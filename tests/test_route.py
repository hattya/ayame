#
# test_route
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import ayame
from ayame import http, route
from base import AyameTestCase


class RouteTestCase(AyameTestCase):

    def test_static_rules(self):
        map = route.Map()
        map.connect('/', 0)
        map.connect('/news', 1, methods=['GET', 'HEAD'])

        # GET /
        router = map.bind(self.new_environ(path='/'))
        self.assertEqual(router.match(), (0, {}))

        # GET /?a=1
        router = map.bind(self.new_environ(path='/', query='a=1'))
        self.assertEqual(router.match(), (0, {}))

        # GET (empty path info) -> MovedPermanently
        router = map.bind(self.new_environ(path=''))
        with self.assertRaises(http.MovedPermanently) as cm:
            router.match()
        self.assertEqual(cm.exception.headers, [
            ('Location', 'http://localhost/'),
        ])

        # HEAD / -> NotImplemented
        router = map.bind(self.new_environ(method='HEAD', path='/'))
        with self.assertRaises(http.NotImplemented) as cm:
            router.match()
        self.assertEqual(cm.exception.headers, [])

        # GET /news
        router = map.bind(self.new_environ(path='/news'))
        self.assertEqual(router.match(), (1, {}))

        # PUT /news -> NotImplemented
        router = map.bind(self.new_environ(method='PUT', path='/news'))
        with self.assertRaises(http.NotImplemented):
            router.match()

        # GET /404 -> NotFound
        router = map.bind(self.new_environ(path='/404'))
        with self.assertRaises(http.NotFound):
            router.match()

        # build URI
        router = map.bind(self.new_environ(path='/'))
        with self.assertRaises(ayame.RouteError):
            router.build(-1)

        with self.assertRaises(ayame.RouteError):
            router.build(0, method='PUT')
        self.assertEqual(router.build(0),
                         '/')
        self.assertEqual(router.build(0, {'a': ['1']}, query=False),
                         '/')
        self.assertEqual(router.build(0, {'a': ['1']}),
                         '/?a=1')
        self.assertEqual(router.build(0, {'a': ['1']}, 'ch1'),
                         '/?a=1#ch1')
        self.assertEqual(router.build(0, anchor='ch1'),
                         '/#ch1')
        self.assertEqual(router.build(0, {'a': 1}),
                         '/?a=1')
        self.assertEqual(router.build(0, {'a': '1'}),
                         '/?a=1')
        self.assertEqual(router.build(0, {'a': [1]}),
                         '/?a=1')
        self.assertEqual(router.build(0, {'a': (1,)}),
                         '/?a=1')
        self.assertEqual(router.build(0, {'a': ['1']}),
                         '/?a=1')
        self.assertEqual(router.build(0, {'a': ('1',)}),
                         '/?a=1')
        self.assertEqual(router.build(0, {'a': ''}),
                         '/?a=')
        self.assertEqual(router.build(0, {'a': 1, 'z': 3, 'm': 2}),
                         '/?a=1&m=2&z=3')
        self.assertEqual(router.build(0, {'a': [3, 2, 1]}),
                         '/?a=3&a=2&a=1')

        map.sort_key = lambda o: -ord(o[0])
        self.assertEqual(router.build(0, {'a': 1, 'z': [3, 2], 'm': [1, 2]}),
                         '/?z=3&z=2&m=1&m=2&a=1')

        # build URI (without SCRIPT_NAME)
        environ = self.new_environ(path='/')
        environ['SCRIPT_NAME'] = '/ayame'
        router = map.bind(environ)
        self.assertEqual(router.build(0), '/ayame/')
        self.assertEqual(router.build(0, relative=True), '/')

    def test_no_static(self):
        map = route.Map()
        map.connect('<a>', 0)

        router = map.bind(self.new_environ(path='app'))
        self.assertEqual(router.match(), (0, {'a': 'app'}))

    def test_duplicate_variable(self):
        map = route.Map()
        with self.assertRaisesRegex(ayame.RouteError, r"'a' already in use$"):
            map.connect('/<a>/<b>/<a>/<c>', 0)

    def test_unknown_converter(self):
        map = route.Map()
        with self.assertRaisesRegex(ayame.RouteError, r" 'spam' not found$"):
            map.connect('/<a:spam>', 0)

    def test_custom_converter(self):
        class SpamConverter(route.Converter):
            pass

        map = route.Map(converters={'spam': SpamConverter})
        map.connect('/<a:spam>', 0)

        router = map.bind(self.new_environ(path='/app'))
        self.assertEqual(router.match(), (0, {'a': 'app'}))

    def test_int_converter(self):
        map = route.Map()
        map.connect('/<y:int>/', 0)
        map.connect('/<y:int>/<m:int(2, min=1, max=12)>/', 1)
        map.connect('/_/<a:int(2)>/', 2)

        # GET /2011 -> MovedPermanently
        router = map.bind(self.new_environ(path='/2011'))
        with self.assertRaises(http.MovedPermanently) as cm:
            router.match()
        self.assertEqual(cm.exception.headers, [
            ('Location', 'http://localhost/2011/'),
        ])

        # GET /2011/
        router = map.bind(self.new_environ(path='/2011/'))
        self.assertEqual(router.match(), (0, {'y': 2011}))

        # GET /0/
        router = map.bind(self.new_environ(path='/0/'))
        self.assertEqual(router.match(), (0, {'y': 0}))

        # GET /2011/01 -> MovedPermanently
        router = map.bind(self.new_environ(path='/2011/01'))
        with self.assertRaises(http.MovedPermanently) as cm:
            router.match()
        self.assertEqual(cm.exception.headers, [
            ('Location', 'http://localhost/2011/01/'),
        ])

        # GET /2011/01/
        router = map.bind(self.new_environ(path='/2011/01/'))
        self.assertEqual(router.match(), (1, {'y': 2011, 'm': 1}))

        # GET /2011/12/
        router = map.bind(self.new_environ(path='/2011/12/'))
        self.assertEqual(router.match(), (1, {'y': 2011, 'm': 12}))

        # GET /2011/1/ -> NotFound
        router = map.bind(self.new_environ(path='/2011/1/'))
        with self.assertRaises(http.NotFound):
            router.match()

        # GET /2011/100/ -> NotFound
        router = map.bind(self.new_environ(path='/2011/100/'))
        with self.assertRaises(http.NotFound):
            router.match()

        # GET /2011/00/ -> NotFound
        router = map.bind(self.new_environ(path='/2011/00/'))
        with self.assertRaises(http.NotFound):
            router.match()

        # GET /2011/13/ -> NotFound
        router = map.bind(self.new_environ(path='/2011/13/'))
        with self.assertRaises(http.NotFound):
            router.match()

        # build URI
        router = map.bind(self.new_environ(path='/'))
        with self.assertRaises(ayame.RouteError):
            router.build(-1)

        with self.assertRaises(ayame.RouteError):
            router.build(0)
        with self.assertRaises(ayame.RouteError):
            router.build(0, {'y': None})
        with self.assertRaises(ayame.RouteError):
            router.build(0, {'y': 'a'})
        self.assertEqual(router.build(0, {'y': [2011]}),
                         '/2011/')
        self.assertEqual(router.build(0, {'y': ['2011']}),
                         '/2011/')
        self.assertEqual(router.build(0, {'y': 2011}),
                         '/2011/')
        self.assertEqual(router.build(0, {'y': '2011'}),
                         '/2011/')
        self.assertEqual(router.build(0, {'y': ['2010', '2011']}),
                         '/2010/?y=2011')
        self.assertEqual(router.build(0, {'y': ['2010', '2011']}, query=False),
                         '/2010/')

        with self.assertRaises(ayame.RouteError):
            router.build(1)
        with self.assertRaises(ayame.RouteError):
            router.build(1, {'y': 2011, 'm': 0})
        with self.assertRaises(ayame.RouteError):
            router.build(1, {'y': 2011, 'm': 13})
        with self.assertRaises(ayame.RouteError):
            router.build(1, {'y': 2011, 'm': 100})
        self.assertEqual(router.build(1, {'y': 2011, 'm': 1}), '/2011/01/')
        self.assertEqual(router.build(1, {'y': 2011, 'm': 12}), '/2011/12/')

        with self.assertRaises(ayame.RouteError):
            router.build(2, {'a': 100})

    def test_string_converter(self):
        map = route.Map()
        map.connect('/<s:string(2)>/', 0)
        map.connect('/<s:string(3, min=3)>/', 1)
        map.connect('/<s:string>/', 2)

        # GET /jp -> MovedPermanently
        router = map.bind(self.new_environ(path='/jp'))
        with self.assertRaises(http.MovedPermanently):
            router.match()

        # GET /jp/
        router = map.bind(self.new_environ(path='/jp/'))
        self.assertEqual(router.match(), (0, {'s': 'jp'}))

        # GET /jpy -> MovedPermanently
        router = map.bind(self.new_environ(path='/jpy'))
        with self.assertRaises(http.MovedPermanently):
            router.match()

        # GET /jpy/
        router = map.bind(self.new_environ(path='/jpy/'))
        self.assertEqual(router.match(), (1, {'s': 'jpy'}))

        # GET /news -> MovedPermanently
        router = map.bind(self.new_environ(path='/news'))
        with self.assertRaises(http.MovedPermanently):
            router.match()

        # GET /news/
        router = map.bind(self.new_environ(path='/news/'))
        self.assertEqual(router.match(), (2, {'s': 'news'}))

        # build URI
        router = map.bind(self.new_environ(path='/'))
        with self.assertRaises(ayame.RouteError):
            router.build(-1)

        with self.assertRaises(ayame.RouteError):
            router.build(0)
        with self.assertRaises(ayame.RouteError):
            router.build(0, {'s': None})
        with self.assertRaises(ayame.RouteError):
            router.build(0, {'s': ''})
        with self.assertRaises(ayame.RouteError):
            router.build(0, {'s': 'abc'})
        self.assertEqual(router.build(0, {'s': 'jp'}), '/jp/')
        self.assertEqual(router.build(0, {'s': 'us'}), '/us/')

        with self.assertRaises(ayame.RouteError):
            router.build(1)
        with self.assertRaises(ayame.RouteError):
            router.build(1, {'s': None})
        with self.assertRaises(ayame.RouteError):
            router.build(1, {'s': ''})
        with self.assertRaises(ayame.RouteError):
            router.build(1, {'s': 'ab'})
        with self.assertRaises(ayame.RouteError):
            router.build(1, {'s': 'abcd'})
        self.assertEqual(router.build(1, {'s': 'jpy'}), '/jpy/')
        self.assertEqual(router.build(1, {'s': 'usd'}), '/usd/')

    def test_path_converter(self):
        map = route.Map()
        map.connect('/<p:path>/<m>', 0)
        map.connect('/<p:path>', 1)

        # GET /WikiPage/edit
        router = map.bind(self.new_environ(path='/WikiPage/edit'))
        self.assertEqual(router.match(), (0, {'p': 'WikiPage', 'm': 'edit'}))

        # GET /WikiPage/edit/
        router = map.bind(self.new_environ(path='/WikiPage/edit/'))
        self.assertEqual(router.match(), (0, {'p': 'WikiPage', 'm': 'edit'}))

        # GET /WikiPage
        router = map.bind(self.new_environ(path='/WikiPage'))
        self.assertEqual(router.match(), (1, {'p': 'WikiPage'}))

        # GET /WikiPage/
        router = map.bind(self.new_environ(path='/WikiPage/'))
        self.assertEqual(router.match(), (1, {'p': 'WikiPage'}))

        # build URI
        router = map.bind(self.new_environ(path='/'))
        with self.assertRaises(ayame.RouteError):
            router.build(-1)

        with self.assertRaises(ayame.RouteError):
            router.build(0)
        with self.assertRaises(ayame.RouteError):
            router.build(0, {'p': None})
        with self.assertRaises(ayame.RouteError):
            router.build(0, {'p': ''})
        self.assertEqual(router.build(0, {'p': 'WikiPage', 'm': 'edit'}),
                         '/WikiPage/edit')
        self.assertEqual(router.build(0, {'p': 'WikiPage', 'm': 'delete'}),
                         '/WikiPage/delete')
        self.assertEqual(router.build(0, {'p': '', 'm': ''}),
                         '//')

        with self.assertRaises(ayame.RouteError):
            router.build(1)
        self.assertEqual(router.build(1, {'p': 'WikiPage'}), '/WikiPage')
        self.assertEqual(router.build(1, {'p': ''}), '/')

    def test_redirect(self):
        map = route.Map()
        map.redirect('/<y:int>/<m:int(2, min=1, max=12)>/', '/_/<y>/<m>/')
        map.redirect('/<s:string(2)>/', lambda s: f'/_/{s}/')

        # GET /2011/01/ -> MovedPermanently
        router = map.bind(self.new_environ(path='/2011/01/'))
        with self.assertRaises(http.MovedPermanently) as cm:
            router.match()
        self.assertEqual(cm.exception.headers, [
            ('Location', 'http://localhost/_/2011/01/'),
        ])

        # GET /jp/ -> MovedPermanently
        router = map.bind(self.new_environ(path='/jp/'))
        with self.assertRaises(http.MovedPermanently) as cm:
            router.match()
        self.assertEqual(cm.exception.headers, [
            ('Location', 'http://localhost/_/jp/'),
        ])

    def test_add_rule(self):
        rule = route.Rule('/', 0)
        map = route.Map()
        map.add(rule)
        with self.assertRaises(ayame.RouteError):
            map.add(rule)

    def test_mount(self):
        map = route.Map()
        submap = map.mount('/_')
        submap.connect('/', 0)
        submap.redirect('/old', '/_/new')
        submap.add(route.Rule('/news/', 1))

        # GET /_/
        router = map.bind(self.new_environ(path='/_/'))
        self.assertEqual(router.match(), (0, {}))

        # GET /_/news/
        router = map.bind(self.new_environ(path='/_/news/'))
        self.assertEqual(router.match(), (1, {}))

        # GET /_/old -> MovedPermanently
        router = map.bind(self.new_environ(path='/_/old'))
        with self.assertRaises(http.MovedPermanently) as cm:
            router.match()
        self.assertEqual(cm.exception.headers, [
            ('Location', 'http://localhost/_/new'),
        ])

    def test_parse_args(self):
        rule = route.Rule('/', 1)
        self.assertEqual(rule._parse_args(''), ((), {}))
        self.assertEqual(rule._parse_args(' '), ((), {}))
        self.assertEqual(rule._parse_args(' , '), ((), {}))

        self.assertEqual(rule._parse_args('None, True, False'),
                         ((None, True, False), {}))
        self.assertEqual(rule._parse_args('0, 1, 0b10, 0o10, 0x10'),
                         ((0, 1, 2, 8, 16), {}))
        self.assertEqual(rule._parse_args('0, -1, -0b10, -0o10, -0x10'),
                         ((0, -1, -2, -8, -16), {}))
        self.assertEqual(rule._parse_args('3.14, 10., .001, 1e100, 3.14e-10, 0e0'),
                         ((3.14, 10.0, 0.001, 1e+100, 3.14e-10, 0.0), {}))
        self.assertEqual(rule._parse_args(r'"spam", "eggs\"ham", "toast\\"'),
                         (('spam', 'eggs"ham', r'toast\\'), {}))

        self.assertEqual(rule._parse_args('0, spam=1'), ((0,), {'spam': 1}))
        self.assertEqual(rule._parse_args('0, spam = 1'), ((0,), {'spam': 1}))

        with self.assertRaises(SyntaxError):
            rule._parse_args('0, 1 2, 3')
        with self.assertRaises(SyntaxError):
            rule._parse_args('0, spam=1, 2')
        with self.assertRaises(SyntaxError):
            rule._parse_args('0, spam=1, spam=2')
        with self.assertRaises(SyntaxError):
            rule._parse_args(r'"spam\\"eggs"')
        with self.assertRaises(SyntaxError):
            rule._parse_args(r'"spam\"')
