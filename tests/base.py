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
import io
import os
import sys
import unittest
import wsgiref.util

import ayame
from ayame import _compat as five
from ayame import local, markup, res, uri, util


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

    @classmethod
    def setUpClass(cls):
        cls.setup_class()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_class()

    @classmethod
    def setup_class(cls):
        cls.app = ayame.Ayame(cls.__module__)
        cls.boundary = 'ayame.' + cls.__module__[5:]

    @classmethod
    def teardown_class(cls):
        pass

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def setup(self):
        pass

    def teardown(self):
        pass

    def assert_element_equal(self, a, b):
        self.assert_is_not(a, b)
        # qname
        self.assert_is_instance(a.qname, markup.QName)
        self.assert_is_instance(b.qname, markup.QName)
        self.assert_equal(a.qname, b.qname)
        # attrib
        self.assert_is_instance(a.attrib, markup._AttributeDict)
        self.assert_is_instance(b.attrib, markup._AttributeDict)
        self.assert_is_not(a.attrib, b.attrib)
        self.assert_equal(a.attrib, b.attrib)
        # type
        self.assert_equal(a.type, b.type)
        # ns
        self.assert_is_instance(a.ns, dict)
        self.assert_is_instance(b.ns, dict)
        self.assert_is_not(a.ns, b.ns)
        self.assert_equal(a.ns, b.ns)
        # children
        self.assert_is_instance(a.children, list)
        self.assert_is_instance(b.children, list)
        self.assert_is_not(a.children, b.children)
        self.assert_equal(len(a.children), len(b.children))
        for i in five.range(len(a.children)):
            if isinstance(a[i], markup.Element):
                self.assert_is_instance(b[i], markup.Element)
                self.assert_element_equal(a[i], b[i])
            else:
                self.assert_is_instance(a[i], five.string_type)
                self.assert_is_instance(b[i], five.string_type)
                self.assert_equal(a[i], b[i])

    def assert_ws(self, seq, i):
        self.assert_is_instance(seq[i], five.string_type)
        self.assert_regex(seq[i], '^\s*$')

    def path_for(self, path):
        return os.path.join(os.path.splitext(sys.modules[self.__class__.__module__].__file__)[0], path)

    def new_resource_loader(self):
        ref = {}

        class ResourceLoader(res.ResourceLoader):
            def load_from(self, loader, parent, path):
                return Resource(os.path.join(parent, path))

        class Resource(res.FileResource):
            @property
            def mtime(self):
                if self._path not in ref:
                    ref[self._path] = 0
                ref[self._path] += 1
                return self._mtime + ref[self._path]

            def open(self, encoding='utf-8'):
                if 3 < ref[self._path]:
                    raise ayame.ResourceError
                return StringIO(self._path, encoding)

        class StringIO(io.StringIO):
            def __init__(self, path, encoding):
                self._path = path
                with io.open(self._path, encoding=encoding) as fp:
                    super(StringIO, self).__init__(fp.read())

            def read(self, *args, **kwargs):
                return self._wrap(super(StringIO, self).read, args, kwargs)

            def readline(self, *args, **kwargs):
                return self._wrap(super(StringIO, self).readline, args, kwargs)

            def _wrap(self, func, args, kwargs):
                if 2 < ref[self._path]:
                    raise OSError
                return func(*args, **kwargs)

        return ResourceLoader()

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
                    form=None, accept=None):
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
        elif form is not None:
            environ['CONTENT_TYPE'] = ('multipart/form-data; '
                                       'boundary={}').format(self.boundary)
            data = form
        else:
            data = ''
        data = data.format(path=ayame.AYAME_PATH).encode('utf-8')
        environ['wsgi.input'].write(data)
        environ['wsgi.input'].seek(0)
        environ['CONTENT_LENGTH'] = str(len(data))
        if accept is not None:
            environ['HTTP_ACCEPT_LANGUAGE'] = accept
        return environ

    def form_data(self, *args):
        self.assert_is_instance(self.boundary, five.string_type)
        self.assert_true(self.boundary)
        buf = []
        for n, v in args:
            buf.append('--' + self.boundary)
            if isinstance(v, tuple):
                buf.append(u'Content-Disposition: form-data; name="{}"; filename="{}"'.format(n, v[0]))
                buf.append('Content-Type: ' + v[2])
                v = v[1]
            else:
                buf.append(u'Content-Disposition: form-data; name="{}"'.format(n))
            buf.append('')
            buf.append(v)
        buf.append('--' + self.boundary + '--')
        return '\r\n'.join(buf)

    def xml_of(self, name):
        return markup.QName(markup.XML_NS, name)

    def html_of(self, name):
        return markup.QName(markup.XHTML_NS, name)

    def ayame_of(self, name):
        return markup.QName(markup.AYAME_NS, name)

    def of(self, name):
        return markup.QName('', name)

    def format(self, class_, *args, **kwargs):
        kwargs.update(doctype=markup.XHTML1_STRICT,
                      xhtml=markup.XHTML_NS,
                      xml=markup.XML_NS,
                      ayame=markup.AYAME_NS,
                      path=ayame.AYAME_PATH)
        for k, v in five.items(getattr(class_, 'kwargs', {})):
            if callable(v):
                v = v(*[kwargs[k]] if k in kwargs else [])
            elif k in kwargs:
                continue
            kwargs[k] = v
        return class_.html_t.format(*args, **kwargs).encode(kwargs.pop('encoding', 'utf-8'))
