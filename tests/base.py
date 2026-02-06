#
# base
#
#   Copyright (c) 2013-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import collections
import contextlib
import io
import os
import sys
import textwrap
import unittest
import wsgiref.util

import ayame
from ayame import local, markup, res, uri


__all__ = ['AyameTestCase']


class AyameTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = ayame.Ayame(cls.__module__)
        cls.boundary = f'ayame.{cls.__module__[5:]}'
        cls.lv = (
            '\n',
            '\n  ',
            '\n    ',
            '\n      ',
            '\n        ',
        )
        cls.ns = {
            '': markup.XHTML_NS,
            'xml': markup.XML_NS,
            'ayame': markup.AYAME_NS,
        }

    def assertElementEqual(self, a, b, msg=None):
        def assertElementEqual(a, b, xpath):
            self.assertIsInstance(a, markup.Element, xpath)
            self.assertIsInstance(b, markup.Element, xpath)
            self.assertIsNot(a, b, xpath)
            # qname
            self.assertIsInstance(a.qname, markup.QName, xpath)
            self.assertIsInstance(b.qname, markup.QName, xpath)
            self.assertEqual(a.qname, b.qname, xpath)
            # attrib
            self.assertIsInstance(a.attrib, markup._AttributeDict, xpath)
            self.assertIsInstance(b.attrib, markup._AttributeDict, xpath)
            self.assertIsNot(a.attrib, b.attrib, xpath)
            self.assertEqual(a.attrib, b.attrib, xpath)
            # type
            self.assertEqual(a.type, b.type, xpath)
            # ns
            self.assertIsInstance(a.ns, dict, xpath)
            self.assertIsInstance(b.ns, dict, xpath)
            self.assertIsNot(a.ns, b.ns, xpath)
            self.assertEqual(a.ns, b.ns, xpath)
            # children
            self.assertIsInstance(a.children, list, xpath)
            self.assertIsInstance(b.children, list, xpath)
            self.assertIsNot(a.children, b.children, xpath)
            self.assertEqual(len(a.children), len(b.children), xpath)

        def name_of(qname, stack):
            for el in reversed(stack):
                for k, v in el.ns.items():
                    if v == qname.ns_uri:
                        return f'{k}:{qname.name}' if k else qname.name
            return str(qname)

        def xpath_of(stack, count):
            rv = ['']
            for i, el in enumerate(stack):
                rv.append(f'{name_of(el.qname, stack[:i+1])}[{count[i][el.qname]}]')
            return '/'.join(rv)

        stack = []
        count = [collections.defaultdict(int)]
        a_q = collections.deque((a,))
        b_q = collections.deque((b,))
        end = object()
        while a_q:
            a_v = a_q.popleft()
            b_v = b_q.popleft()
            if isinstance(a_v, markup.Element):
                stack.append(a_v)
                count[-1][a_v.qname] += 1

                xpath = xpath_of(stack, count)
                assertElementEqual(a_v, b_v, xpath)

                count.append(collections.defaultdict(int))
                a_q.appendleft(end)
                a_q.extendleft(reversed(a_v.children))
                b_q.appendleft(end)
                b_q.extendleft(reversed(b_v.children))
            elif a_v is not end:
                count[-1]['text()'] += 1

                xpath = f'{xpath_of(stack, count)}/text()[{count[-1]["text()"]}]'
                self.assertEqual(a_v, b_v, xpath)
            else:
                stack.pop()
                count.pop()

    def path_for(self, path):
        return os.path.join(os.path.splitext(sys.modules[type(self).__module__].__file__)[0], path)

    def new_resource_loader(self):
        ref = collections.defaultdict(int)

        class ResourceLoader(res.ResourceLoader):
            def load_from(self, loader, parent, path):
                return Resource(os.path.join(parent, path))

        class Resource(res.FileResource):
            @property
            def mtime(self):
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
                if ref[self._path] > 2:
                    raise OSError
                return super().read(*args, **kwargs)

            def readline(self, *args, **kwargs):
                if ref[self._path] > 2:
                    raise OSError
                return super().readline(*args, **kwargs)

        return ResourceLoader()

    @contextlib.contextmanager
    def application(self, environ=None):
        app = self.app
        try:
            ctx = local.push(app, environ)
            if environ is not None:
                ctx.request = app.config['ayame.request'](environ, {})
                ctx._router = app.config['ayame.route.map'].bind(environ)
                with ctx.request:
                    yield
            else:
                yield
        finally:
            local.pop()

    def new_environ(self, method='GET', path='', query='', data=None,
                    form=None, accept=None):
        query = uri.quote(query)
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
            environ['CONTENT_TYPE'] = f'multipart/form-data; boundary={self.boundary}'
            data = form
        else:
            data = ''
        data = data.encode('utf-8')
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
            buf.append(f'--{self.boundary}')
            if isinstance(v, tuple):
                buf.append(f'Content-Disposition: form-data; name="{n}"; filename="{v[0]}"')
                buf.append(f'Content-Type: {v[2]}')
                v = v[1]
            else:
                buf.append(f'Content-Disposition: form-data; name="{n}"')
            buf.append('')
            buf.append(v)
        buf.append(f'--{self.boundary}--')
        return '\r\n'.join(buf)

    def empty_element(self, attrib=None):
        return markup.Element(markup.QName('', ''), attrib)

    def html_of(self, name):
        return markup.QName(markup.XHTML_NS, name)

    def ayame_of(self, name):
        return markup.QName(markup.AYAME_NS, name)

    def format(self, cls, *args, **kwargs):
        kwargs.update(doctype=markup.XHTML1_STRICT,
                      xhtml=markup.XHTML_NS,
                      xml=markup.XML_NS,
                      ayame=markup.AYAME_NS,
                      path=ayame.AYAME_PATH)
        for k, v in getattr(cls, 'kwargs', {}).items():
            if callable(v):
                v = v(*[kwargs[k]] if k in kwargs else [])
            elif k in kwargs:
                continue
            kwargs[k] = v
        return textwrap.dedent(cls.html_t).format(*args, **kwargs).encode(kwargs.pop('encoding', 'utf-8'))


class ElementBuilder:

    def __init__(self, default, **prefix):
        self.__root = None
        self.__active = None
        self.__prefix = {
            '': default,
            'xml': markup.XML_NS,
            'ayame': markup.AYAME_NS,
        }
        self.__prefix.update(prefix)

    @property
    def root(self):
        return self.__root

    def open(self, name, attrib=None, ns=None):
        return self.element(name, attrib, markup.Element.OPEN, ns)

    def empty(self, name, attrib=None, ns=None):
        with self.element(name, attrib, markup.Element.EMPTY, ns):
            pass

    @contextlib.contextmanager
    def element(self, name, attrib=None, type=None, ns=None):
        def q(name):
            v = name.split(':') if ':' in name else ['', name]
            return markup.QName(self.__prefix[v[0]], v[1])

        a = self.__active
        try:
            el = markup.Element(q(name), {q(a): v for a, v in attrib.items()} if attrib else None, type, ns)
            if self.__active is None:
                self.__root = self.__active = el
            else:
                self.__active.append(el)
                self.__active = el
            yield el
        finally:
            self.__active = a

    def str(self, s):
        self.__active.append(s)
