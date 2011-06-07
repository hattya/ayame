#
# test_route
#
#   Copyright (c) 2011 Akinori Hattori <hattya@gmail.com>
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

from __future__ import unicode_literals
from wsgiref import util

from nose.tools import assert_raises, eq_, ok_

from ayame import http, route
from ayame.exception import RouteError


def new_environ(path_info, method='GET', query=None):
    environ = {'SERVER_NAME': 'localhost',
               'PATH_INFO': path_info,
               'REQUEST_METHOD': method}
    if query:
        environ['QUERY_STRING'] = query
    util.setup_testing_defaults(environ)
    return environ

def test_static_rules():
    map = route.Map()
    map.connect('/', 0)
    map.connect('/news', 1, methods=['GET', 'HEAD'])

    # case: GET /
    router = map.bind(new_environ('/'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {})

    # case: GET /?a=1
    router = map.bind(new_environ('/', query='a=1'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {})

    # case: GET (empty path info) -> MovedPermanently
    router = map.bind(new_environ(''))
    assert_raises(http.MovedPermanently, router.match)
    try:
        router.match()
    except http.MovedPermanently as e:
        eq_(e.headers, [('Location', 'http://localhost/')])

    # case: HEAD / -> NotImplemented
    router = map.bind(new_environ('/', method='HEAD'))
    assert_raises(http.NotImplemented, router.match)
    try:
        router.match()
    except http.NotImplemented as e:
        eq_(e.headers, [('Allow', 'GET,POST')])

    # case: GET /news
    router = map.bind(new_environ('/news'))
    obj, values = router.match()
    eq_(obj, 1)
    eq_(values, {})

    # case: PUT /news -> NotImplemented
    router = map.bind(new_environ('/news', method='PUT'))
    assert_raises(http.NotImplemented, router.match)

    # case: GET /404 -> NotFound
    router = map.bind(new_environ('/404'))
    assert_raises(http.NotFound, router.match)

    # case: build URI
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

def test_duplicate_variable():
    map = route.Map()
    assert_raises(RouteError, map.connect, '/<a>/<b>/<a>/<c>', 0)

def test_unknown_converter():
    map = route.Map()
    assert_raises(RouteError, map.connect, '/<foo:a>', 0)

def test_custom_converter():
    class FooConverter(route.Converter):
        pass
    map = route.Map(converters={'foo': FooConverter})
    map.connect('/<foo:a>', 0)

    # case: GET /app
    router = map.bind(new_environ('/app'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {'a': 'app'})

def test_int_converter():
    map = route.Map()
    map.connect('/<int:y>/', 0)
    map.connect('/<int:y>/<int(2, min=1, max=12):m>/', 1)
    map.connect('/_/<int(2):a>/', 2)

    # case: GET /2011 -> MovedPermanently
    router = map.bind(new_environ('/2011'))
    assert_raises(http.MovedPermanently, router.match)
    try:
        router.match()
    except http.MovedPermanently as e:
        eq_(e.headers, [('Location', 'http://localhost/2011/')])

    # case: GET /2011/
    router = map.bind(new_environ('/2011/'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {'y': 2011})

    # case: GET /0/
    router = map.bind(new_environ('/0/'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {'y': 0})

    # case: GET /2011/01 -> MovedPermanently
    router = map.bind(new_environ('/2011/01'))
    assert_raises(http.MovedPermanently, router.match)
    try:
        router.match()
    except http.MovedPermanently as e:
        eq_(e.headers, [('Location', 'http://localhost/2011/01/')])

    # case: GET /2011/01/
    router = map.bind(new_environ('/2011/01/'))
    obj, values = router.match()
    eq_(obj, 1)
    eq_(values, {'y': 2011, 'm': 1})

    # case: GET /2011/12/
    router = map.bind(new_environ('/2011/12/'))
    obj, values = router.match()
    eq_(obj, 1)
    eq_(values, {'y': 2011, 'm': 12})

    # case: GET /2011/1/ -> NotFound
    router = map.bind(new_environ('/2011/1/'))
    assert_raises(http.NotFound, router.match)

    # case: GET /2011/100/ -> NotFound
    router = map.bind(new_environ('/2011/100/'))
    assert_raises(http.NotFound, router.match)

    # case: GET /2011/00/ -> NotFound
    router = map.bind(new_environ('/2011/00/'))
    assert_raises(http.NotFound, router.match)

    # case: GET /2011/13/ -> NotFound
    router = map.bind(new_environ('/2011/13/'))
    assert_raises(http.NotFound, router.match)

    # case: build URI
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
    map.connect('/<string(2):s>/', 0)
    map.connect('/<string(3, min=3):s>/', 1)
    map.connect('/<string:s>/', 2)

    # case: GET /jp -> MovedPermanently
    router = map.bind(new_environ('/jp'))
    assert_raises(http.MovedPermanently, router.match)

    # case: GET /jp/
    router = map.bind(new_environ('/jp/'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {'s': 'jp'})

    # case: GET /jpy -> MovedPermanently
    router = map.bind(new_environ('/jpy'))
    assert_raises(http.MovedPermanently, router.match)

    # case: GET /jpy/
    router = map.bind(new_environ('/jpy/'))
    obj, values = router.match()
    eq_(obj, 1)
    eq_(values, {'s': 'jpy'})

    # case: GET /news -> MovedPermanently
    router = map.bind(new_environ('/news'))
    assert_raises(http.MovedPermanently, router.match)

    # case: GET /news/
    router = map.bind(new_environ('/news/'))
    obj, values = router.match()
    eq_(obj, 2)
    eq_(values, {'s': 'news'})

    # case: build URI
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
    map.connect('/<path:p>/<m>', 0)
    map.connect('/<path:p>', 1)

    # case: GET /WikiPage/edit
    router = map.bind(new_environ('/WikiPage/edit'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {'p': 'WikiPage', 'm': 'edit'})

    # case: GET /WikiPage/edit/
    router = map.bind(new_environ('/WikiPage/edit/'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {'p': 'WikiPage', 'm': 'edit'})

    # case: GET /WikiPage
    router = map.bind(new_environ('/WikiPage'))
    obj, values = router.match()
    eq_(obj, 1)
    eq_(values, {'p': 'WikiPage'})

    # case: GET /WikiPage/
    router = map.bind(new_environ('/WikiPage/'))
    obj, values = router.match()
    eq_(obj, 1)
    eq_(values, {'p': 'WikiPage'})

    # case: build URI
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
    map.redirect('/<int:y>/<int(2, min=1, max=12):m>/', '/_/<y>/<m>/')
    map.redirect('/<string(2):s>/', redirect)

    # case: GET /2011/01/ -> MovedPermanently
    router = map.bind(new_environ('/2011/01/'))
    assert_raises(http.MovedPermanently, router.match)
    try:
        router.match()
    except http.MovedPermanently as e:
        eq_(e.headers, [('Location', 'http://localhost/_/2011/01/')])

    # case: GET /jp/ -> MovedPermanently
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

    # case: GET /_/
    router = map.bind(new_environ('/_/'))
    obj, values = router.match()
    eq_(obj, 0)
    eq_(values, {})

    # case: GET /_/news/
    router = map.bind(new_environ('/_/news/'))
    obj, values = router.match()
    eq_(obj, 1)
    eq_(values, {})

    # case: GET /_/old -> MovedPermanently
    router = map.bind(new_environ('/_/old'))
    assert_raises(http.MovedPermanently, router.match)
    try:
        router.match()
    except http.MovedPermanently as e:
        eq_(e.headers, [('Location', 'http://localhost/_/new')])