#
# test_route
#
#   Copyright (c) 2011-2012 Akinori Hattori <hattya@gmail.com>
#
#   Permission is hereby granted, free of charge, to any person
#   obtaining a copy of this software and associated documentation files
#   (the "Software"), to deal in the Software without restriction,
#   including without limitation the rights to use, copy, modify, merge,
#   publish, distribute, sublicense, and/or sell copies of the Software,
#   and to permit persons to whom the Software is furnished to do so,
#   subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be
#   included in all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
#   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#   ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#   CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
#

import wsgiref.util

from nose.tools import assert_raises, eq_

from ayame import http, route
from ayame.exception import RouteError


def new_environ(path_info, method='GET', query=None):
    environ = {'SERVER_NAME': 'localhost',
               'PATH_INFO': path_info,
               'REQUEST_METHOD': method}
    if query:
        environ['QUERY_STRING'] = query
    wsgiref.util.setup_testing_defaults(environ)
    return environ


def test_static_rules():
    map = route.Map()
    map.connect('/', 0)
    map.connect('/news', 1, methods=['GET', 'HEAD'])

    # GET /
    router = map.bind(new_environ('/'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {})

    # GET /?a=1
    router = map.bind(new_environ('/', query='a=1'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {})

    # GET (empty path info) -> MovedPermanently
    router = map.bind(new_environ(''))
    assert_raises(http.MovedPermanently, router.match)
    try:
        router.match()
    except http.MovedPermanently as e:
        eq_(e.headers, [('Location', 'http://localhost/')])

    # HEAD / -> NotImplemented
    router = map.bind(new_environ('/', method='HEAD'))
    assert_raises(http.NotImplemented, router.match)
    try:
        router.match()
    except http.NotImplemented as e:
        eq_(e.headers, [('Allow', 'GET,POST')])

    # GET /news
    router = map.bind(new_environ('/news'))
    obj, values = router.match()
    eq_(obj, 1)
    eq_(values, {})

    # PUT /news -> NotImplemented
    router = map.bind(new_environ('/news', method='PUT'))
    assert_raises(http.NotImplemented, router.match)

    # GET /404 -> NotFound
    router = map.bind(new_environ('/404'))
    assert_raises(http.NotFound, router.match)

    # build URI
    router = map.bind(new_environ('/'))
    assert_raises(RouteError, router.build, -1)

    assert_raises(RouteError, router.build, 0, method='PUT')
    eq_(router.build(0), '/')
    eq_(router.build(0, {'a': ['1']}, append_query=False), '/')
    eq_(router.build(0, {'a': ['1']}), '/?a=1')
    eq_(router.build(0, {'a': ['1']}, 'ch1'), '/?a=1#ch1')
    eq_(router.build(0, anchor='ch1'), '/#ch1')
    eq_(router.build(0, {'a': 1}), '/?a=1')
    eq_(router.build(0, {'a': '1'}), '/?a=1')
    eq_(router.build(0, {'a': [1]}), '/?a=1')
    eq_(router.build(0, {'a': (1,)}), '/?a=1')
    eq_(router.build(0, {'a': ['1']}), '/?a=1')
    eq_(router.build(0, {'a': ('1',)}), '/?a=1')
    eq_(router.build(0, {'a': ''}), '/?a=')
    eq_(router.build(0, {'a': 1, 'z': 3, 'm': 2}), '/?a=1&m=2&z=3')
    eq_(router.build(0, {'a': [3, 2, 1]}), '/?a=1&a=2&a=3')

    def key(o):
        return o[0]
    map.sort_key = key
    eq_(router.build(0, {'a': [3, 2, 1]}), '/?a=3&a=2&a=1')

    # build URI (without SCRIPT_NAME)
    router = map.bind(new_environ('/'))
    router.environ['SCRIPT_NAME'] = '/ayame'
    eq_(router.build(0), '/ayame/')
    eq_(router.build(0, relative=True), '/')


def test_duplicate_variable():
    map = route.Map()
    assert_raises(RouteError, map.connect, '/<a>/<b>/<a>/<c>', 0)


def test_unknown_converter():
    map = route.Map()
    assert_raises(RouteError, map.connect, '/<a:spam>', 0)


def test_custom_converter():
    class SpamConverter(route.Converter):
        pass
    map = route.Map(converters={'spam': SpamConverter})
    map.connect('/<a:spam>', 0)

    # GET /app
    router = map.bind(new_environ('/app'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {'a': 'app'})


def test_int_converter():
    map = route.Map()
    map.connect('/<y:int>/', 0)
    map.connect('/<y:int>/<m:int(2, min=1, max=12)>/', 1)
    map.connect('/_/<a:int(2)>/', 2)

    # GET /2011 -> MovedPermanently
    router = map.bind(new_environ('/2011'))
    assert_raises(http.MovedPermanently, router.match)
    try:
        router.match()
    except http.MovedPermanently as e:
        eq_(e.headers, [('Location', 'http://localhost/2011/')])

    # GET /2011/
    router = map.bind(new_environ('/2011/'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {'y': 2011})

    # GET /0/
    router = map.bind(new_environ('/0/'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {'y': 0})

    # GET /2011/01 -> MovedPermanently
    router = map.bind(new_environ('/2011/01'))
    assert_raises(http.MovedPermanently, router.match)
    try:
        router.match()
    except http.MovedPermanently as e:
        eq_(e.headers, [('Location', 'http://localhost/2011/01/')])

    # GET /2011/01/
    router = map.bind(new_environ('/2011/01/'))
    obj, values = router.match()
    eq_(obj, 1)
    eq_(values, {'y': 2011, 'm': 1})

    # GET /2011/12/
    router = map.bind(new_environ('/2011/12/'))
    obj, values = router.match()
    eq_(obj, 1)
    eq_(values, {'y': 2011, 'm': 12})

    # GET /2011/1/ -> NotFound
    router = map.bind(new_environ('/2011/1/'))
    assert_raises(http.NotFound, router.match)

    # GET /2011/100/ -> NotFound
    router = map.bind(new_environ('/2011/100/'))
    assert_raises(http.NotFound, router.match)

    # GET /2011/00/ -> NotFound
    router = map.bind(new_environ('/2011/00/'))
    assert_raises(http.NotFound, router.match)

    # GET /2011/13/ -> NotFound
    router = map.bind(new_environ('/2011/13/'))
    assert_raises(http.NotFound, router.match)

    # build URI
    router = map.bind(new_environ('/'))
    assert_raises(RouteError, router.build, -1)

    assert_raises(RouteError, router.build, 0)
    assert_raises(RouteError, router.build, 0, {'y': None})
    assert_raises(RouteError, router.build, 0, {'y': 'a'})
    eq_(router.build(0, {'y': [2011]}), '/2011/')
    eq_(router.build(0, {'y': ['2011']}), '/2011/')
    eq_(router.build(0, {'y': 2011}), '/2011/')
    eq_(router.build(0, {'y': '2011'}), '/2011/')
    eq_(router.build(0, {'y': ['2010', '2011']}), '/2010/?y=2011')
    eq_(router.build(0, {'y': ['2010', '2011']}, append_query=False), '/2010/')

    assert_raises(RouteError, router.build, 1)
    assert_raises(RouteError, router.build, 1, {'y': 2011, 'm': 0})
    assert_raises(RouteError, router.build, 1, {'y': 2011, 'm': 13})
    assert_raises(RouteError, router.build, 1, {'y': 2011, 'm': 100})
    eq_(router.build(1, {'y': 2011, 'm': 1}), '/2011/01/')
    eq_(router.build(1, {'y': 2011, 'm': 12}), '/2011/12/')

    assert_raises(RouteError, router.build, 2, {'a': 100})


def test_string_converter():
    map = route.Map()
    map.connect('/<s:string(2)>/', 0)
    map.connect('/<s:string(3, min=3)>/', 1)
    map.connect('/<s:string>/', 2)

    # GET /jp -> MovedPermanently
    router = map.bind(new_environ('/jp'))
    assert_raises(http.MovedPermanently, router.match)

    # GET /jp/
    router = map.bind(new_environ('/jp/'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {'s': 'jp'})

    # GET /jpy -> MovedPermanently
    router = map.bind(new_environ('/jpy'))
    assert_raises(http.MovedPermanently, router.match)

    # GET /jpy/
    router = map.bind(new_environ('/jpy/'))
    obj, values = router.match()
    eq_(obj, 1)
    eq_(values, {'s': 'jpy'})

    # GET /news -> MovedPermanently
    router = map.bind(new_environ('/news'))
    assert_raises(http.MovedPermanently, router.match)

    # GET /news/
    router = map.bind(new_environ('/news/'))
    obj, values = router.match()
    eq_(obj, 2)
    eq_(values, {'s': 'news'})

    # build URI
    router = map.bind(new_environ('/'))
    assert_raises(RouteError, router.build, -1)

    assert_raises(RouteError, router.build, 0)
    assert_raises(RouteError, router.build, 0, {'s': None})
    assert_raises(RouteError, router.build, 0, {'s': ''})
    assert_raises(RouteError, router.build, 0, {'s': 'abc'})
    eq_(router.build(0, {'s': 'jp'}), '/jp/')
    eq_(router.build(0, {'s': 'us'}), '/us/')

    assert_raises(RouteError, router.build, 1)
    assert_raises(RouteError, router.build, 1, {'s': None})
    assert_raises(RouteError, router.build, 1, {'s': ''})
    assert_raises(RouteError, router.build, 1, {'s': 'ab'})
    assert_raises(RouteError, router.build, 1, {'s': 'abcd'})
    eq_(router.build(1, {'s': 'jpy'}), '/jpy/')
    eq_(router.build(1, {'s': 'usd'}), '/usd/')


def test_path_converter():
    map = route.Map()
    map.connect('/<p:path>/<m>', 0)
    map.connect('/<p:path>', 1)

    # GET /WikiPage/edit
    router = map.bind(new_environ('/WikiPage/edit'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {'p': 'WikiPage', 'm': 'edit'})

    # GET /WikiPage/edit/
    router = map.bind(new_environ('/WikiPage/edit/'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {'p': 'WikiPage', 'm': 'edit'})

    # GET /WikiPage
    router = map.bind(new_environ('/WikiPage'))
    obj, values = router.match()
    eq_(obj, 1)
    eq_(values, {'p': 'WikiPage'})

    # GET /WikiPage/
    router = map.bind(new_environ('/WikiPage/'))
    obj, values = router.match()
    eq_(obj, 1)
    eq_(values, {'p': 'WikiPage'})

    # build URI
    router = map.bind(new_environ('/'))
    assert_raises(RouteError, router.build, -1)

    assert_raises(RouteError, router.build, 0)
    assert_raises(RouteError, router.build, 0, {'p': None})
    assert_raises(RouteError, router.build, 0, {'p': ''})
    eq_(router.build(0, {'p': 'WikiPage', 'm': 'edit'}), '/WikiPage/edit')
    eq_(router.build(0, {'p': 'WikiPage', 'm': 'delete'}), '/WikiPage/delete')
    eq_(router.build(0, {'p': '', 'm': ''}), '//')

    assert_raises(RouteError, router.build, 1)
    eq_(router.build(1, {'p': 'WikiPage'}), '/WikiPage')
    eq_(router.build(1, {'p': ''}), '/')


def test_redirect():
    def redirect(s):
        return '/_/{}/'.format(s)
    map = route.Map()
    map.redirect('/<y:int>/<m:int(2, min=1, max=12)>/', '/_/<y>/<m>/')
    map.redirect('/<s:string(2)>/', redirect)

    # GET /2011/01/ -> MovedPermanently
    router = map.bind(new_environ('/2011/01/'))
    assert_raises(http.MovedPermanently, router.match)
    try:
        router.match()
    except http.MovedPermanently as e:
        eq_(e.headers, [('Location', 'http://localhost/_/2011/01/')])

    # GET /jp/ -> MovedPermanently
    router = map.bind(new_environ('/jp/'))
    assert_raises(http.MovedPermanently, router.match)
    try:
        router.match()
    except http.MovedPermanently as e:
        eq_(e.headers, [('Location', 'http://localhost/_/jp/')])


def test_add_rule():
    rule = route.Rule('/', 0)
    map = route.Map()
    map.add(rule)
    assert_raises(RouteError, map.add, rule)


def test_mount():
    rule = route.Rule('/news/', 1)
    map = route.Map()
    submap = map.mount('/_')
    submap.connect('/', 0)
    submap.redirect('/old', '/_/new')
    submap.add(rule)

    # GET /_/
    router = map.bind(new_environ('/_/'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {})

    # GET /_/news/
    router = map.bind(new_environ('/_/news/'))
    obj, values = router.match()
    eq_(obj, 1)
    eq_(values, {})

    # GET /_/old -> MovedPermanently
    router = map.bind(new_environ('/_/old'))
    assert_raises(http.MovedPermanently, router.match)
    try:
        router.match()
    except http.MovedPermanently as e:
        eq_(e.headers, [('Location', 'http://localhost/_/new')])
