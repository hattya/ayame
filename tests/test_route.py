#
# test_route
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import ayame
from ayame import http, route
from base import AyameTestCase


class RouteTestCase(AyameTestCase):

    def test_static_rules(self):
        map = route.Map()
        map.connect('/', 1)
        map.connect('/news', 2, methods=['GET', 'HEAD'])

        # GET /
        router = map.bind(self.new_environ(path='/'))
        self.assertEqual(router.match(), (1, {}))

        # GET /?a=1
        router = map.bind(self.new_environ(path='/', query='a=1'))
        self.assertEqual(router.match(), (1, {}))

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
        self.assertEqual(router.match(), (2, {}))

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
            router.build(1, method='PUT')
        self.assertEqual(router.build(1),
                         '/')
        self.assertEqual(router.build(1, {'a': ['1']}, query=False),
                         '/')
        self.assertEqual(router.build(1, {'a': ['1']}),
                         '/?a=1')
        self.assertEqual(router.build(1, {'a': ['1']}, 'ch1'),
                         '/?a=1#ch1')
        self.assertEqual(router.build(1, anchor='ch1'),
                         '/#ch1')
        self.assertEqual(router.build(1, {'a': 1}),
                         '/?a=1')
        self.assertEqual(router.build(1, {'a': '1'}),
                         '/?a=1')
        self.assertEqual(router.build(1, {'a': (1,)}),
                         '/?a=1')
        self.assertEqual(router.build(1, {'a': ('1',)}),
                         '/?a=1')
        self.assertEqual(router.build(1, {'a': [1]}),
                         '/?a=1')
        self.assertEqual(router.build(1, {'a': ['1']}),
                         '/?a=1')
        self.assertEqual(router.build(1, {'a': ''}),
                         '/?a=')
        self.assertEqual(router.build(1, {'z': 3, 'm': 2, 'a': 1}),
                         '/?a=1&m=2&z=3')
        self.assertEqual(router.build(1, {'a': [3, 2, 1]}),
                         '/?a=3&a=2&a=1')

        map.sort_key = lambda o: -ord(o[0])
        self.assertEqual(router.build(1, {'a': 1, 'z': [3, 2], 'm': [1, 2]}),
                         '/?z=3&z=2&m=1&m=2&a=1')

        # build URI (without SCRIPT_NAME)
        environ = self.new_environ(path='/')
        environ['SCRIPT_NAME'] = '/ayame'
        router = map.bind(environ)
        self.assertEqual(router.build(1), '/ayame/')
        self.assertEqual(router.build(1, relative=True), '/')

    def test_no_static(self):
        map = route.Map()
        map.connect('<a>', 1)

        router = map.bind(self.new_environ(path='ayame'))
        self.assertEqual(router.match(), (1, {'a': 'ayame'}))

    def test_duplicate_variable(self):
        map = route.Map()
        with self.assertRaisesRegex(ayame.RouteError, r"'a' already in use$"):
            map.connect('/<a>/<b>/<a>/<c>', 1)

    def test_unknown_converter(self):
        map = route.Map()
        with self.assertRaisesRegex(ayame.RouteError, r" 'spam' not found$"):
            map.connect('/<a:spam>', 1)

    def test_custom_converter(self):
        class SpamConverter(route.Converter):
            pass

        map = route.Map(converters={'spam': SpamConverter})
        map.connect('/<a:spam>', 1)

        router = map.bind(self.new_environ(path='/ayame'))
        self.assertEqual(router.match(), (1, {'a': 'ayame'}))

    def test_int_converter(self):
        map = route.Map()
        map.connect('/<y:int>/', 1)
        map.connect('/<y:int>/<m:int(2, min=1, max=12)>/', 2)
        map.connect('/_/<a:int(2)>/', 3)

        # GET /2011 -> MovedPermanently
        router = map.bind(self.new_environ(path='/2011'))
        with self.assertRaises(http.MovedPermanently) as cm:
            router.match()
        self.assertEqual(cm.exception.headers, [
            ('Location', 'http://localhost/2011/'),
        ])

        # GET /<y>/
        for y in (
            1,
            2011,
        ):
            with self.subTest(path=(path := f'/{y}/')):
                router = map.bind(self.new_environ(path=path))
                self.assertEqual(router.match(), (1, {'y': y}))

        # GET /2011/01 -> MovedPermanently
        router = map.bind(self.new_environ(path='/2011/01'))
        with self.assertRaises(http.MovedPermanently) as cm:
            router.match()
        self.assertEqual(cm.exception.headers, [
            ('Location', 'http://localhost/2011/01/'),
        ])

        # GET /<y>/<m>/
        for y, m in (
            (2011, 1),
            (2011, 12),
        ):
            with self.subTest(path=(path := f'/{y}/{m:02}/')):
                router = map.bind(self.new_environ(path=path))
                self.assertEqual(router.match(), (2, {'y': y, 'm': m}))

        # GET /<y>/<m>/ -> NotFound
        for path in (
            '/2011/1/',
            '/2011/100/',
            '/2011/00/',
            '/2011/13/',
        ):
            router = map.bind(self.new_environ(path=path))
            with self.assertRaises(http.NotFound):
                router.match()

        # build URI
        router = map.bind(self.new_environ(path='/'))
        with self.assertRaises(ayame.RouteError):
            router.build(-1)

        with self.assertRaises(ayame.RouteError):
            router.build(1)
        with self.assertRaises(ayame.RouteError):
            router.build(1, {'y': None})
        with self.assertRaises(ayame.RouteError):
            router.build(1, {'y': 'a'})
        self.assertEqual(router.build(1, {'y': [2011]}),
                         '/2011/')
        self.assertEqual(router.build(1, {'y': ['2011']}),
                         '/2011/')
        self.assertEqual(router.build(1, {'y': 2011}),
                         '/2011/')
        self.assertEqual(router.build(1, {'y': '2011'}),
                         '/2011/')
        self.assertEqual(router.build(1, {'y': ['2010', '2011']}),
                         '/2010/?y=2011')
        self.assertEqual(router.build(1, {'y': ['2010', '2011']}, query=False),
                         '/2010/')

        with self.assertRaises(ayame.RouteError):
            router.build(2)
        with self.assertRaises(ayame.RouteError):
            router.build(2, {'y': 2011, 'm': 0})
        with self.assertRaises(ayame.RouteError):
            router.build(2, {'y': 2011, 'm': 13})
        with self.assertRaises(ayame.RouteError):
            router.build(2, {'y': 2011, 'm': 100})
        self.assertEqual(router.build(2, {'y': 2011, 'm': 1}), '/2011/01/')
        self.assertEqual(router.build(2, {'y': 2011, 'm': 12}), '/2011/12/')

        with self.assertRaises(ayame.RouteError):
            router.build(3, {'a': 100})

    def test_string_converter(self):
        map = route.Map()
        map.connect('/<s:string(2)>/', 1)
        map.connect('/<s:string(3, min=3)>/', 2)
        map.connect('/<s:string>/', 3)

        for o, s in (
            (1, 'jp'),
            (2, 'jpy'),
            (3, 'jbgs'),
        ):
            with self.subTest(s=s):
                # GET /<s> -> MovedPermanently
                router = map.bind(self.new_environ(path=f'/{s}'))
                with self.assertRaises(http.MovedPermanently):
                    router.match()

                # GET /<s>/
                router = map.bind(self.new_environ(path=f'/{s}/'))
                self.assertEqual(router.match(), (o, {'s': s}))

        # build URI
        router = map.bind(self.new_environ(path='/'))
        with self.assertRaises(ayame.RouteError):
            router.build(-1)

        with self.assertRaises(ayame.RouteError):
            router.build(1)
        with self.assertRaises(ayame.RouteError):
            router.build(1, {'s': None})
        with self.assertRaises(ayame.RouteError):
            router.build(1, {'s': ''})
        with self.assertRaises(ayame.RouteError):
            router.build(1, {'s': 'abc'})
        self.assertEqual(router.build(1, {'s': 'jp'}), '/jp/')
        self.assertEqual(router.build(1, {'s': 'us'}), '/us/')

        with self.assertRaises(ayame.RouteError):
            router.build(2)
        with self.assertRaises(ayame.RouteError):
            router.build(2, {'s': None})
        with self.assertRaises(ayame.RouteError):
            router.build(2, {'s': ''})
        with self.assertRaises(ayame.RouteError):
            router.build(2, {'s': 'ab'})
        with self.assertRaises(ayame.RouteError):
            router.build(2, {'s': 'abcd'})
        self.assertEqual(router.build(2, {'s': 'jpy'}), '/jpy/')
        self.assertEqual(router.build(2, {'s': 'usd'}), '/usd/')

    def test_path_converter(self):
        map = route.Map()
        map.connect('/<p:path>/<m>', 1)
        map.connect('/<p:path>', 2)

        # GET /WikiPage/edit
        router = map.bind(self.new_environ(path='/WikiPage/edit'))
        self.assertEqual(router.match(), (1, {'p': 'WikiPage', 'm': 'edit'}))

        # GET /WikiPage/edit/
        router = map.bind(self.new_environ(path='/WikiPage/edit/'))
        self.assertEqual(router.match(), (1, {'p': 'WikiPage', 'm': 'edit'}))

        # GET /WikiPage
        router = map.bind(self.new_environ(path='/WikiPage'))
        self.assertEqual(router.match(), (2, {'p': 'WikiPage'}))

        # GET /WikiPage/
        router = map.bind(self.new_environ(path='/WikiPage/'))
        self.assertEqual(router.match(), (2, {'p': 'WikiPage'}))

        # build URI
        router = map.bind(self.new_environ(path='/'))
        with self.assertRaises(ayame.RouteError):
            router.build(-1)

        with self.assertRaises(ayame.RouteError):
            router.build(1)
        with self.assertRaises(ayame.RouteError):
            router.build(1, {'p': None})
        with self.assertRaises(ayame.RouteError):
            router.build(1, {'p': ''})
        self.assertEqual(router.build(1, {'p': 'WikiPage', 'm': 'edit'}),
                         '/WikiPage/edit')
        self.assertEqual(router.build(1, {'p': 'WikiPage', 'm': 'delete'}),
                         '/WikiPage/delete')
        self.assertEqual(router.build(1, {'p': '', 'm': ''}),
                         '//')

        with self.assertRaises(ayame.RouteError):
            router.build(2)
        self.assertEqual(router.build(2, {'p': 'WikiPage'}), '/WikiPage')
        self.assertEqual(router.build(2, {'p': ''}), '/')

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
        submap.connect('/', 1)
        submap.redirect('/old', '/_/new')
        submap.add(route.Rule('/news/', 2))

        # GET /_/
        router = map.bind(self.new_environ(path='/_/'))
        self.assertEqual(router.match(), (1, {}))

        # GET /_/news/
        router = map.bind(self.new_environ(path='/_/news/'))
        self.assertEqual(router.match(), (2, {}))

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

        self.assertEqual(rule._parse_args('1, spam=1'),
                         ((1,), {'spam': 1}))
        self.assertEqual(rule._parse_args('1 , spam = 1'),
                         ((1,), {'spam': 1}))
        self.assertEqual(rule._parse_args('1, 2, spam=1, eggs=2'),
                         ((1, 2), {'spam': 1, 'eggs': 2}))
        self.assertEqual(rule._parse_args('1 , 2 , spam = 1 , eggs = 2'),
                         ((1, 2), {'spam': 1, 'eggs': 2}))

        with self.assertRaisesRegex(SyntaxError, r'^invalid syntax\b'):
            rule._parse_args('0, 1 2, 3')
        with self.assertRaisesRegex(SyntaxError, r'^non-keyword arg\b'):
            rule._parse_args('0, spam=1, 2')
        with self.assertRaisesRegex(SyntaxError, r'\bargument repeated\b'):
            rule._parse_args('0, spam=1, spam=2')
        with self.assertRaisesRegex(SyntaxError, r'^invalid syntax\b'):
            rule._parse_args(r'"spam\\"eggs"')
        with self.assertRaisesRegex(SyntaxError, r'^invalid syntax\b'):
            rule._parse_args(r'"spam\"')
