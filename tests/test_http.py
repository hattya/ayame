#
# test_http
#
#   Copyright (c) 2011-2014 Akinori Hattori <hattya@gmail.com>
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

import ayame
from ayame import http
from base import AyameTestCase


class HTTPTestCase(AyameTestCase):

    def assert_status_class(self, st, code, reason, superclass=None):
        self.assert_equal(st.code, code)
        self.assert_equal(st.reason, reason)
        self.assert_equal(st.status, '' if code == 0 else '{} {}'.format(code, reason))
        if superclass is None:
            self.assert_is_instance(st, object)
            self.assert_equal(str(st), st.status)
        else:
            self.assert_is_instance(st, type)
            self.assert_true(issubclass(st, superclass))

    def new_environ(self, data=None, form=None):
        return super(HTTPTestCase, self).new_environ(method='POST',
                                                     data=data,
                                                     form=form)

    def test_parse_accept(self):
        self.assert_equal(http.parse_accept(''),
                          ())
        self.assert_equal(http.parse_accept('ja, en'),
                          (('ja', 1.0), ('en', 1.0)))
        self.assert_equal(http.parse_accept('en, ja'),
                          (('en', 1.0), ('ja', 1.0)))
        self.assert_equal(http.parse_accept('en; q=0.7, ja'),
                          (('ja', 1.0), ('en', 0.7)))
        # invalid
        self.assert_equal(http.parse_accept('ja, en; q=33.3333'),
                          (('ja', 1.0), ('en', 1.0)))
        self.assert_equal(http.parse_accept('ja, en, q=0.7'),
                          (('ja', 1.0), ('en', 1.0), ('q=0.7', 1.0)))

    def test_parse_form_data_empty(self):
        self.assert_equal(http.parse_form_data(self.new_environ()), {})
        self.assert_equal(http.parse_form_data(self.new_environ(data='')), {})
        self.assert_equal(http.parse_form_data(self.new_environ(form='')), {})

    def test_parse_form_data_ascii(self):
        data = ('x=-1&'
                'y=-1&'
                'y=-2&'
                'z=-1&'
                'z=-2&'
                'z=-3')
        self.assert_equal(http.parse_form_data(self.new_environ(data=data)),
                          {'x': ['-1'],
                           'y': ['-1', '-2'],
                           'z': ['-1', '-2', '-3']})

        data = self.form_data(('x', '-1'),
                              ('y', '-1'),
                              ('y', '-2'),
                              ('z', '-1'),
                              ('z', '-2'),
                              ('z', '-3'))
        self.assert_equal(http.parse_form_data(self.new_environ(form=data)),
                          {'x': ['-1'],
                           'y': ['-1', '-2'],
                           'z': ['-1', '-2', '-3']})

    def test_parse_form_data_utf_8(self):
        data = (u'\u3082=\u767e&'
                u'\u305b=\u767e&'
                u'\u305b=\u5343&'
                u'\u3059=\u767e&'
                u'\u3059=\u5343&'
                u'\u3059=\u4e07')
        self.assert_equal(http.parse_form_data(self.new_environ(data=data)),
                          {u'\u3082': [u'\u767e'],
                           u'\u305b': [u'\u767e', u'\u5343'],
                           u'\u3059': [u'\u767e', u'\u5343', u'\u4e07']})

        data = self.form_data((u'\u3082', u'\u767e'),
                              (u'\u305b', u'\u767e'),
                              (u'\u305b', u'\u5343'),
                              (u'\u3059', u'\u767e'),
                              (u'\u3059', u'\u5343'),
                              (u'\u3059', u'\u4e07'),
                              )
        self.assert_equal(http.parse_form_data(self.new_environ(form=data)),
                          {u'\u3082': [u'\u767e'],
                           u'\u305b': [u'\u767e', u'\u5343'],
                           u'\u3059': [u'\u767e', u'\u5343', u'\u4e07']})

    def test_parse_form_data_post(self):
        data = self.form_data(('a', (u'\u3044', 'spam\neggs\nham\n', 'text/plain')))
        form_data = http.parse_form_data(self.new_environ(form=data))
        self.assert_equal(list(form_data), ['a'])
        self.assert_equal(len(form_data['a']), 1)
        a = form_data['a'][0]
        self.assert_equal(a.name, 'a')
        self.assert_equal(a.filename, u'\u3044')
        self.assert_equal(a.value, (b'spam\n'
                                    b'eggs\n'
                                    b'ham\n'))

    def test_parse_form_data_put(self):
        data = 'spam\neggs\nham\n'
        environ = self.new_environ(data=data)
        environ.update(REQUEST_METHOD='PUT',
                       CONTENT_TYPE='text/plain')
        self.assert_equal(http.parse_form_data(environ), {})

    def test_parse_form_data_http_408(self):
        data = self.form_data(('a', ('a.txt', '', 'text/plain')))
        environ = self.new_environ(form=data[:-20])
        environ.update(CONTENT_LENGTH=str(len(data) * 2))
        with self.assert_raises(http.RequestTimeout):
            http.parse_form_data(environ)

    def test_http_status(self):
        args = (0, '', ayame.AyameError)
        self.assert_status_class(http.HTTPStatus, *args)

        st = http.HTTPStatus()
        self.assert_status_class(st, *args[:-1])
        self.assert_equal(st.headers, [])
        self.assert_equal(st.description, '')

        class ST(http.HTTPStatus):
            code = -1
            reason = None
            status = None

        self.assert_equal(ST.code, -1)
        self.assert_is_none(ST.reason)
        self.assert_is_none(ST.status)

        st = ST()
        self.assert_equal(st.code, -1)
        self.assert_is_none(st.reason)
        self.assert_is_none(st.status)
        self.assert_equal(st.headers, [])
        self.assert_equal(st.description, '')

    def test_http_200(self):
        args = (200, 'OK', http.HTTPSuccessful)
        self.assert_status_class(http.OK, *args)

        st = http.OK()
        self.assert_status_class(st, *args[:-1])
        self.assert_equal(st.headers, [])
        self.assert_equal(st.description, '')

    def test_http_201(self):
        args = (201, 'Created', http.HTTPSuccessful)
        self.assert_status_class(http.Created, *args)

        st = http.Created()
        self.assert_status_class(st, *args[:-1])
        self.assert_equal(st.headers, [])
        self.assert_equal(st.description, '')

    def test_http_202(self):
        args = (202, 'Accepted', http.HTTPSuccessful)
        self.assert_status_class(http.Accepted, *args)

        st = http.Accepted()
        self.assert_status_class(st, *args[:-1])
        self.assert_equal(st.headers, [])
        self.assert_equal(st.description, '')

    def test_http_204(self):
        args = (204, 'No Content', http.HTTPSuccessful)
        self.assert_status_class(http.NoContent, *args)

        st = http.NoContent()
        self.assert_status_class(st, *args[:-1])
        self.assert_equal(st.headers, [])
        self.assert_equal(st.description, '')

    def test_http_301(self):
        args = (301, 'Moved Permanently', http.HTTPRedirection)
        self.assert_status_class(http.MovedPermanently, *args)

        def assert_3xx(st, uri, headers):
            self.assert_status_class(st, *args[:-1])
            self.assert_equal(st.headers, headers)
            self.assert_is_not(st.headers, headers)
            self.assert_in(uri, st.description)

        uri = 'http://localhost/'
        headers = [('Server', 'Python')]

        st = http.MovedPermanently(uri)
        assert_3xx(st, uri, [('Location', uri)])

        st = http.MovedPermanently(uri, headers)
        assert_3xx(st, uri, [('Server', 'Python'),
                             ('Location', uri)])

        self.assert_equal(headers, [('Server', 'Python')])

    def test_http_302(self):
        args = (302, 'Found', http.HTTPRedirection)
        self.assert_status_class(http.Found, *args)

        def assert_3xx(st, uri, headers):
            self.assert_status_class(st, *args[:-1])
            self.assert_equal(st.headers, headers)
            self.assert_is_not(st.headers, headers)
            self.assert_in(uri, st.description)

        uri = 'http://localhost/'
        headers = [('Server', 'Python')]
        assert_3xx(http.Found(uri), uri, [('Location', uri)])
        assert_3xx(http.Found(uri, headers), uri, [('Server', 'Python'),
                                                   ('Location', uri)])
        self.assert_equal(headers, [('Server', 'Python')])

    def test_http_303(self):
        args = (303, 'See Other', http.HTTPRedirection)
        self.assert_status_class(http.SeeOther, *args)

        def assert_3xx(st, uri, headers):
            self.assert_status_class(st, *args[:-1])
            self.assert_equal(st.headers, headers)
            self.assert_is_not(st.headers, headers)
            self.assert_in(uri, st.description)

        uri = 'http://localhost/'
        headers = [('Server', 'Python')]
        assert_3xx(http.SeeOther(uri), uri, [('Location', uri)])
        assert_3xx(http.SeeOther(uri, headers), uri, [('Server', 'Python'),
                                                      ('Location', uri)])
        self.assert_equal(headers, [('Server', 'Python')])

    def test_http_304(self):
        args = (304, 'Not Modified', http.HTTPRedirection)
        self.assert_status_class(http.NotModified, *args)

        st = http.NotModified()
        self.assert_status_class(st, *args[:-1])
        self.assert_equal(st.headers, [])
        self.assert_equal(st.description, '')

    def test_http_400(self):
        args = (400, 'Bad Request', http.HTTPClientError)
        self.assert_status_class(http.BadRequest, *args)

        st = http.BadRequest()
        self.assert_status_class(st, *args[:-1])
        self.assert_equal(st.headers, [])
        self.assert_equal(st.description, '')

    def test_http_401(self):
        args = (401, 'Unauthrized', http.HTTPClientError)
        self.assert_status_class(http.Unauthrized, *args)

        def assert_4xx(st, headers):
            self.assert_status_class(st, *args[:-1])
            self.assert_equal(st.headers, headers)
            self.assert_is_not(st.headers, headers)
            self.assert_true(st.description)

        headers = []
        assert_4xx(http.Unauthrized(), headers)
        assert_4xx(http.Unauthrized(headers), headers)
        self.assert_equal(headers, [])

    def test_http_403(self):
        args = (403, 'Forbidden', http.HTTPClientError)
        self.assert_status_class(http.Forbidden, *args)

        def assert_4xx(st, uri, headers):
            self.assert_status_class(st, *args[:-1])
            self.assert_equal(st.headers, headers)
            self.assert_is_not(st.headers, headers)
            self.assert_in(uri, st.description)

        uri = 'http://localhsot/'
        headers = []
        assert_4xx(http.Forbidden(uri), uri, headers)
        assert_4xx(http.Forbidden(uri, headers), uri, headers)
        self.assert_equal(headers, [])

    def test_http_404(self):
        args = (404, 'Not Found', http.HTTPClientError)
        self.assert_status_class(http.NotFound, *args)

        def assert_4xx(st, uri, headers):
            self.assert_status_class(st, *args[:-1])
            self.assert_equal(st.headers, headers)
            self.assert_is_not(st.headers, headers)
            self.assert_in(uri, st.description)

        uri = 'http://localhsot/'
        headers = []
        assert_4xx(http.NotFound(uri), uri, headers)
        assert_4xx(http.NotFound(uri, headers), uri, headers)
        self.assert_equal(headers, [])

    def test_http_405(self):
        args = (405, 'Method Not Allowed', http.HTTPClientError)
        self.assert_status_class(http.MethodNotAllowed, *args)

        def assert_4xx(st, method, uri, headers):
            self.assert_status_class(st, *args[:-1])
            self.assert_equal(st.headers, headers)
            self.assert_is_not(st.headers, headers)
            self.assert_in(method, st.description)
            self.assert_in(uri, st.description)

        method = 'PUT'
        uri = 'http://localhost/'
        allow = ['GET', 'POST']
        headers = [('Server', 'Python')]
        assert_4xx(http.MethodNotAllowed(method, uri, allow), method, uri, [('Allow', 'GET, POST')])
        assert_4xx(http.MethodNotAllowed(method, uri, allow, headers), method, uri, [('Server', 'Python'),
                                                                                     ('Allow', 'GET, POST')])
        self.assert_equal(headers, [('Server', 'Python')])

    def test_http_408(self):
        args = (408, 'Request Timeout', http.HTTPClientError)
        self.assert_status_class(http.RequestTimeout, *args)

        def assert_4xx(st, headers):
            self.assert_status_class(st, *args[:-1])
            self.assert_equal(st.headers, headers)
            self.assert_is_not(st.headers, headers)
            self.assert_true(st.description)

        headers = []
        assert_4xx(http.RequestTimeout(), headers)
        assert_4xx(http.RequestTimeout(headers), headers)
        self.assert_equal(headers, [])

    def test_http_500(self):
        args = (500, 'Internal Server Error', http.HTTPServerError)
        self.assert_status_class(http.InternalServerError, *args)

        st = http.InternalServerError()
        self.assert_status_class(st, *args[:-1])
        self.assert_equal(st.headers, [])
        self.assert_equal(st.description, '')

    def test_http_501(self):
        args = (501, 'Not Implemented', http.HTTPServerError)
        self.assert_status_class(http.NotImplemented, *args)

        method = 'PUT'
        uri = 'http://localhsot/'
        st = http.NotImplemented(method, uri)
        self.assert_status_class(st, *args[:-1])
        self.assert_equal(st.headers, [])
        self.assert_in(method, st.description)
        self.assert_in(uri, st.description)
