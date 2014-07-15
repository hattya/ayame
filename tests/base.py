#
# base
#
#   Copyright (c) 2013-2014 Akinori Hattori <hattya@gmail.com>
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

import contextlib
import sys
import unittest
import wsgiref.util

import ayame
from ayame import _compat as five
from ayame import local, markup, uri, util


__all__ = ['AyameTestCase']


def _method_of(name):
    return ''.join(s.title() if 0 < i else s
                   for i, s in enumerate(name.split('_')))


_ASSERT_MAP = {a: _method_of(a)
               for a in ('assert_equal', 'assert_not_equal',
                         'assert_true', 'assert_false',
                         'assert_is', 'assert_is_not',
                         'assert_is_none', 'assert_is_not_none',
                         'assert_in', 'assert_not_in',
                         'assert_is_instance', 'assert_not_is_instance',
                         'assert_raises', 'assert_raises_regex',
                         'assert_almost_equal', 'assert_not_almost_equal',
                         'assert_greater', 'assert_greater_equal',
                         'assert_less', 'assert_less_equal',
                         'assert_regex', 'assert_not_regex',
                         'assert_items_equal')}

if sys.version_info < (3, 2):
    _ASSERT_MAP.update(assert_raises_regex='assertRaisesRegexp',
                       assert_regex='assertRegexpMatches',
                       assert_not_regex='assertNotRegexpMatches')


class AyameTestCase(unittest.TestCase):

    def __getattr__(self, name):
        try:
            return getattr(self, _ASSERT_MAP[name])
        except KeyError:
            raise AttributeError("'{}' object has no attribute {!r}".format(util.fqon_of(self.__class__), name))

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def setup(self):
        self.app = ayame.Ayame(__name__)
        self.boundary = self.__class__.__module__

    def teardown(self):
        pass

    def assert_ws(self, sequence, index):
        self.assert_is_instance(sequence[index], five.string_type)
        self.assert_regex(sequence[index], '^\s*$')

    @contextlib.contextmanager
    def application(self, environ=None):
        app = self.app
        ctx = local.push(app, environ)
        try:
            if environ is not None:
                ctx.request = app.config['ayame.request'](environ, {})
                ctx._router = app.config['ayame.route.map'].bind(environ)
            yield
        finally:
            local.pop()

    def new_environ(self, method='GET', path='', query='', data=None,
                    body=None, accept=None):
        query = uri.quote(query.format(path=ayame.AYAME_PATH))
        environ = {
            'SERVER_NAME': 'localhost',
            'REQUEST_METHOD': method,
            'PATH_INFO': path,
            'QUERY_STRING': query,
            'ayame.session': {}
        }
        wsgiref.util.setup_testing_defaults(environ)

        if data is not None:
            environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
            data = data.format(path=ayame.AYAME_PATH)
        elif body is not None:
            self.assert_is_instance(self.boundary, five.string_type)
            self.assert_true(self.boundary)
            environ['CONTENT_TYPE'] = ('multipart/form-data; '
                                       'boundary={}').format(self.boundary)
            data = body.format(path=ayame.AYAME_PATH,
                               __='--{}'.format(self.boundary),
                               ____='--{}--'.format(self.boundary))
        else:
            data = ''
        data = data.encode('utf-8')
        environ['wsgi.input'].write(data)
        environ['wsgi.input'].seek(0)
        environ['CONTENT_LENGTH'] = str(len(data))
        if accept is not None:
            environ['HTTP_ACCEPT_LANGUAGE'] = accept
        return environ

    def xml_of(self, name):
        return markup.QName(markup.XML_NS, name)

    def html_of(self, name):
        return markup.QName(markup.XHTML_NS, name)

    def ayame_of(self, name):
        return markup.QName(markup.AYAME_NS, name)

    def format(self, class_, *args, **kwargs):
        kwargs.update(doctype=markup.XHTML1_STRICT,
                      xhtml=markup.XHTML_NS,
                      xml=markup.XML_NS,
                      ayame=markup.AYAME_NS,
                      path=ayame.AYAME_PATH)
        for k, v in five.items(getattr(class_, 'kwargs', {})):
            if callable(v):
                kwargs[k] = v(*[kwargs[k]] if k in kwargs else [])
            else:
                kwargs.setdefault(k, v)
        return class_.html_t.format(*args, **kwargs).encode(kwargs.pop('encoding', 'utf-8'))
