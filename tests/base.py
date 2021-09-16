#
# base
#
#   Copyright (c) 2013-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import contextlib
import io
import os
import sys
import unittest
import wsgiref.util

import ayame
from ayame import local, markup, res, uri


__all__ = ['AyameTestCase']


class AyameTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = ayame.Ayame(cls.__module__)
        cls.boundary = 'ayame.' + cls.__module__[5:]

    def assertElementEqual(self, a, b):
        self.assertIsNot(a, b)
        # qname
        self.assertIsInstance(a.qname, markup.QName)
        self.assertIsInstance(b.qname, markup.QName)
        self.assertEqual(a.qname, b.qname)
        # attrib
        self.assertIsInstance(a.attrib, markup._AttributeDict)
        self.assertIsInstance(b.attrib, markup._AttributeDict)
        self.assertIsNot(a.attrib, b.attrib)
        self.assertEqual(a.attrib, b.attrib)
        # type
        self.assertEqual(a.type, b.type)
        # ns
        self.assertIsInstance(a.ns, dict)
        self.assertIsInstance(b.ns, dict)
        self.assertIsNot(a.ns, b.ns)
        self.assertEqual(a.ns, b.ns)
        # children
        self.assertIsInstance(a.children, list)
        self.assertIsInstance(b.children, list)
        self.assertIsNot(a.children, b.children)
        self.assertEqual(len(a.children), len(b.children))
        for i in range(len(a.children)):
            if isinstance(a[i], markup.Element):
                self.assertIsInstance(b[i], markup.Element)
                self.assertElementEqual(a[i], b[i])
            else:
                self.assertIsInstance(a[i], str)
                self.assertIsInstance(b[i], str)
                self.assertEqual(a[i], b[i])

    def assertWS(self, seq, i):
        self.assertIsInstance(seq[i], str)
        self.assertRegex(seq[i], r'^\s*$')

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
                if ref[self._path] > 3:
                    raise ayame.ResourceError
                return StringIO(self._path, encoding)

        class StringIO(io.StringIO):
            def __init__(self, path, encoding):
                self._path = path
                with open(self._path, encoding=encoding) as fp:
                    super().__init__(fp.read())

            def read(self, *args, **kwargs):
                return self._wrap(super().read, args, kwargs)

            def readline(self, *args, **kwargs):
                return self._wrap(super().readline, args, kwargs)

            def _wrap(self, func, args, kwargs):
                if ref[self._path] > 2:
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
            'ayame.session': {},
        }
        wsgiref.util.setup_testing_defaults(environ)

        if data is not None:
            environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
        elif form is not None:
            environ['CONTENT_TYPE'] = 'multipart/form-data; boundary=' + self.boundary
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
        self.assertIsInstance(self.boundary, str)
        self.assertTrue(self.boundary)
        buf = []
        for n, v in args:
            buf.append('--' + self.boundary)
            if isinstance(v, tuple):
                buf.append(f'Content-Disposition: form-data; name="{n}"; filename="{v[0]}"')
                buf.append('Content-Type: ' + v[2])
                v = v[1]
            else:
                buf.append(f'Content-Disposition: form-data; name="{n}"')
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
        for k, v in getattr(class_, 'kwargs', {}).items():
            if callable(v):
                v = v(*[kwargs[k]] if k in kwargs else [])
            elif k in kwargs:
                continue
            kwargs[k] = v
        return class_.html_t.format(*args, **kwargs).encode(kwargs.pop('encoding', 'utf-8'))
