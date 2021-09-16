#
# test_http
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import ayame
from ayame import http
from base import AyameTestCase


class HTTPTestCase(AyameTestCase):

    def assertStatus(self, st, code, reason, superclass=None):
        self.assertEqual(st.code, code)
        self.assertEqual(st.reason, reason)
        self.assertEqual(st.status, '' if code == 0 else f'{code} {reason}')
        if superclass is None:
            self.assertIsInstance(st, object)
            self.assertEqual(str(st), st.status)
        else:
            self.assertIsInstance(st, type)
            self.assertTrue(issubclass(st, superclass))

    def new_environ(self, data=None, form=None):
        return super().new_environ(method='POST',
                                   data=data,
                                   form=form)

    def test_parse_accept(self):
        self.assertEqual(http.parse_accept(''), ())
        self.assertEqual(http.parse_accept('ja, en'), (('ja', 1.0), ('en', 1.0)))
        self.assertEqual(http.parse_accept('en, ja'), (('en', 1.0), ('ja', 1.0)))
        self.assertEqual(http.parse_accept('en; q=0.7, ja'), (('ja', 1.0), ('en', 0.7)))
        # invalid
        self.assertEqual(http.parse_accept('ja, en; q=33.3333'), (('ja', 1.0), ('en', 1.0)))
        self.assertEqual(http.parse_accept('ja, en, q=0.7'), (('ja', 1.0), ('en', 1.0), ('q=0.7', 1.0)))

    def test_parse_form_data_empty(self):
        self.assertEqual(http.parse_form_data(self.new_environ()), {})
        self.assertEqual(http.parse_form_data(self.new_environ(data='')), {})
        self.assertEqual(http.parse_form_data(self.new_environ(form='')), {})

    def test_parse_form_data_ascii(self):
        data = ('x=-1&'
                'y=-1&'
                'y=-2&'
                'z=-1&'
                'z=-2&'
                'z=-3')
        self.assertEqual(http.parse_form_data(self.new_environ(data=data)), {
            'x': ['-1'],
            'y': ['-1', '-2'],
            'z': ['-1', '-2', '-3'],
        })

        data = self.form_data(('x', '-1'),
                              ('y', '-1'),
                              ('y', '-2'),
                              ('z', '-1'),
                              ('z', '-2'),
                              ('z', '-3'))
        self.assertEqual(http.parse_form_data(self.new_environ(form=data)), {
            'x': ['-1'],
            'y': ['-1', '-2'],
            'z': ['-1', '-2', '-3'],
        })

    def test_parse_form_data_utf_8(self):
        data = ('\u3082=\u767e&'
                '\u305b=\u767e&'
                '\u305b=\u5343&'
                '\u3059=\u767e&'
                '\u3059=\u5343&'
                '\u3059=\u4e07')
        self.assertEqual(http.parse_form_data(self.new_environ(data=data)), {
            '\u3082': ['\u767e'],
            '\u305b': ['\u767e', '\u5343'],
            '\u3059': ['\u767e', '\u5343', '\u4e07'],
        })

        data = self.form_data(('\u3082', '\u767e'),
                              ('\u305b', '\u767e'),
                              ('\u305b', '\u5343'),
                              ('\u3059', '\u767e'),
                              ('\u3059', '\u5343'),
                              ('\u3059', '\u4e07'))
        self.assertEqual(http.parse_form_data(self.new_environ(form=data)), {
            '\u3082': ['\u767e'],
            '\u305b': ['\u767e', '\u5343'],
            '\u3059': ['\u767e', '\u5343', '\u4e07'],
        })

    def test_parse_form_data_post(self):
        data = self.form_data(('a', ('\u3044', 'spam\neggs\nham\n', 'text/plain')))
        form_data = http.parse_form_data(self.new_environ(form=data))
        self.assertEqual(list(form_data), ['a'])
        self.assertEqual(len(form_data['a']), 1)
        a = form_data['a'][0]
        self.assertEqual(a.name, 'a')
        self.assertEqual(a.filename, '\u3044')
        self.assertEqual(a.value, b'spam\neggs\nham\n')

    def test_parse_form_data_put(self):
        data = 'spam\neggs\nham\n'
        environ = self.new_environ(data=data)
        environ.update(REQUEST_METHOD='PUT',
                       CONTENT_TYPE='text/plain')
        self.assertEqual(http.parse_form_data(environ), {})

    def test_parse_form_data_http_408(self):
        data = self.form_data(('a', ('a.txt', '', 'text/plain')))
        environ = self.new_environ(form=data[:-20])
        environ.update(CONTENT_LENGTH=str(len(data) * 2))
        with self.assertRaises(http.RequestTimeout):
            http.parse_form_data(environ)

    def test_http_status(self):
        args = (0, '', ayame.AyameError)
        self.assertStatus(http.HTTPStatus, *args)

        st = http.HTTPStatus()
        self.assertStatus(st, *args[:-1])
        self.assertEqual(st.headers, [])
        self.assertEqual(st.description, '')

        class ST(http.HTTPStatus):
            code = -1
            reason = None
            status = None

        self.assertEqual(ST.code, -1)
        self.assertIsNone(ST.reason)
        self.assertIsNone(ST.status)

        st = ST()
        self.assertEqual(st.code, -1)
        self.assertIsNone(st.reason)
        self.assertIsNone(st.status)
        self.assertEqual(st.headers, [])
        self.assertEqual(st.description, '')

    def test_http_200(self):
        args = (200, 'OK', http.HTTPSuccessful)
        self.assertStatus(http.OK, *args)

        st = http.OK()
        self.assertStatus(st, *args[:-1])
        self.assertEqual(st.headers, [])
        self.assertEqual(st.description, '')

    def test_http_201(self):
        args = (201, 'Created', http.HTTPSuccessful)
        self.assertStatus(http.Created, *args)

        st = http.Created()
        self.assertStatus(st, *args[:-1])
        self.assertEqual(st.headers, [])
        self.assertEqual(st.description, '')

    def test_http_202(self):
        args = (202, 'Accepted', http.HTTPSuccessful)
        self.assertStatus(http.Accepted, *args)

        st = http.Accepted()
        self.assertStatus(st, *args[:-1])
        self.assertEqual(st.headers, [])
        self.assertEqual(st.description, '')

    def test_http_204(self):
        args = (204, 'No Content', http.HTTPSuccessful)
        self.assertStatus(http.NoContent, *args)

        st = http.NoContent()
        self.assertStatus(st, *args[:-1])
        self.assertEqual(st.headers, [])
        self.assertEqual(st.description, '')

    def test_http_301(self):
        args = (301, 'Moved Permanently', http.HTTPRedirection)
        self.assertStatus(http.MovedPermanently, *args)

        def assert3xx(st, uri, headers):
            self.assertStatus(st, *args[:-1])
            self.assertEqual(st.headers, headers)
            self.assertIsNot(st.headers, headers)
            self.assertIn(uri, st.description)

        uri = 'http://localhost/'
        headers = [('Server', 'Python')]
        assert3xx(http.MovedPermanently(uri), uri, [
            ('Location', uri),
        ])
        assert3xx(http.MovedPermanently(uri, headers), uri, [
            ('Server', 'Python'),
            ('Location', uri),
        ])
        self.assertEqual(headers, [('Server', 'Python')])

    def test_http_302(self):
        args = (302, 'Found', http.HTTPRedirection)
        self.assertStatus(http.Found, *args)

        def assert3xx(st, uri, headers):
            self.assertStatus(st, *args[:-1])
            self.assertEqual(st.headers, headers)
            self.assertIsNot(st.headers, headers)
            self.assertIn(uri, st.description)

        uri = 'http://localhost/'
        headers = [('Server', 'Python')]
        assert3xx(http.Found(uri), uri, [
            ('Location', uri),
        ])
        assert3xx(http.Found(uri, headers), uri, [
            ('Server', 'Python'),
            ('Location', uri),
        ])
        self.assertEqual(headers, [('Server', 'Python')])

    def test_http_303(self):
        args = (303, 'See Other', http.HTTPRedirection)
        self.assertStatus(http.SeeOther, *args)

        def assert3xx(st, uri, headers):
            self.assertStatus(st, *args[:-1])
            self.assertEqual(st.headers, headers)
            self.assertIsNot(st.headers, headers)
            self.assertIn(uri, st.description)

        uri = 'http://localhost/'
        headers = [('Server', 'Python')]
        assert3xx(http.SeeOther(uri), uri, [
            ('Location', uri),
        ])
        assert3xx(http.SeeOther(uri, headers), uri, [
            ('Server', 'Python'),
            ('Location', uri),
        ])
        self.assertEqual(headers, [('Server', 'Python')])

    def test_http_304(self):
        args = (304, 'Not Modified', http.HTTPRedirection)
        self.assertStatus(http.NotModified, *args)

        st = http.NotModified()
        self.assertStatus(st, *args[:-1])
        self.assertEqual(st.headers, [])
        self.assertEqual(st.description, '')

    def test_http_400(self):
        args = (400, 'Bad Request', http.HTTPClientError)
        self.assertStatus(http.BadRequest, *args)

        st = http.BadRequest()
        self.assertStatus(st, *args[:-1])
        self.assertEqual(st.headers, [])
        self.assertEqual(st.description, '')

    def test_http_401(self):
        args = (401, 'Unauthrized', http.HTTPClientError)
        self.assertStatus(http.Unauthrized, *args)

        def assert4xx(st, headers):
            self.assertStatus(st, *args[:-1])
            self.assertEqual(st.headers, headers)
            self.assertIsNot(st.headers, headers)
            self.assertTrue(st.description)

        headers = []
        assert4xx(http.Unauthrized(), headers)
        assert4xx(http.Unauthrized(headers), headers)
        self.assertEqual(headers, [])

    def test_http_403(self):
        args = (403, 'Forbidden', http.HTTPClientError)
        self.assertStatus(http.Forbidden, *args)

        def assert4xx(st, uri, headers):
            self.assertStatus(st, *args[:-1])
            self.assertEqual(st.headers, headers)
            self.assertIsNot(st.headers, headers)
            self.assertIn(uri, st.description)

        uri = 'http://localhsot/'
        headers = []
        assert4xx(http.Forbidden(uri), uri, headers)
        assert4xx(http.Forbidden(uri, headers), uri, headers)
        self.assertEqual(headers, [])

    def test_http_404(self):
        args = (404, 'Not Found', http.HTTPClientError)
        self.assertStatus(http.NotFound, *args)

        def assert4xx(st, uri, headers):
            self.assertStatus(st, *args[:-1])
            self.assertEqual(st.headers, headers)
            self.assertIsNot(st.headers, headers)
            self.assertIn(uri, st.description)

        uri = 'http://localhsot/'
        headers = []
        assert4xx(http.NotFound(uri), uri, headers)
        assert4xx(http.NotFound(uri, headers), uri, headers)
        self.assertEqual(headers, [])

    def test_http_405(self):
        args = (405, 'Method Not Allowed', http.HTTPClientError)
        self.assertStatus(http.MethodNotAllowed, *args)

        def assert4xx(st, method, uri, headers):
            self.assertStatus(st, *args[:-1])
            self.assertEqual(st.headers, headers)
            self.assertIsNot(st.headers, headers)
            self.assertIn(method, st.description)
            self.assertIn(uri, st.description)

        method = 'PUT'
        uri = 'http://localhost/'
        allow = ['GET', 'POST']
        headers = [('Server', 'Python')]
        assert4xx(http.MethodNotAllowed(method, uri, allow), method, uri, [
            ('Allow', 'GET, POST'),
        ])
        assert4xx(http.MethodNotAllowed(method, uri, allow, headers), method, uri, [
            ('Server', 'Python'),
            ('Allow', 'GET, POST'),
        ])
        self.assertEqual(headers, [('Server', 'Python')])

    def test_http_408(self):
        args = (408, 'Request Timeout', http.HTTPClientError)
        self.assertStatus(http.RequestTimeout, *args)

        def assert4xx(st, headers):
            self.assertStatus(st, *args[:-1])
            self.assertEqual(st.headers, headers)
            self.assertIsNot(st.headers, headers)
            self.assertTrue(st.description)

        headers = []
        assert4xx(http.RequestTimeout(), headers)
        assert4xx(http.RequestTimeout(headers), headers)
        self.assertEqual(headers, [])

    def test_http_500(self):
        args = (500, 'Internal Server Error', http.HTTPServerError)
        self.assertStatus(http.InternalServerError, *args)

        st = http.InternalServerError()
        self.assertStatus(st, *args[:-1])
        self.assertEqual(st.headers, [])
        self.assertEqual(st.description, '')

    def test_http_501(self):
        args = (501, 'Not Implemented', http.HTTPServerError)
        self.assertStatus(http.NotImplemented, *args)

        method = 'PUT'
        uri = 'http://localhsot/'
        st = http.NotImplemented(method, uri)
        self.assertStatus(st, *args[:-1])
        self.assertEqual(st.headers, [])
        self.assertIn(method, st.description)
        self.assertIn(uri, st.description)
