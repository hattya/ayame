#
# test_http
#
#   Copyright (c) 2011-2013 Akinori Hattori <hattya@gmail.com>
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

    def setup(self):
        super(HTTPTestCase, self).setup()
        self.boundary = 'ayame.http'

    def new_environ(self, data=None, body=None):
        return super(HTTPTestCase, self).new_environ(method='POST',
                                                     data=data,
                                                     body=body)

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
        self.assert_equal(http.parse_form_data(self.new_environ(body='')), {})

    def test_parse_form_data_ascii(self):
        data = """\
x=-1&\
y=-1&\
y=-2&\
z=-1&\
z=-2&\
z=-3\
"""
        self.assert_equal(http.parse_form_data(self.new_environ(data=data)),
                          {'x': ['-1'],
                           'y': ['-1', '-2'],
                           'z': ['-1', '-2', '-3']})

        data = """\
{__}
Content-Disposition: form-data; name="x"

-1
{__}
Content-Disposition: form-data; name="y"

-1
{__}
Content-Disposition: form-data; name="y"

-2
{__}
Content-Disposition: form-data; name="z"

-1
{__}
Content-Disposition: form-data; name="z"

-2
{__}
Content-Disposition: form-data; name="z"

-3
{____}
"""
        self.assert_equal(http.parse_form_data(self.new_environ(body=data)),
                          {'x': ['-1'],
                           'y': ['-1', '-2'],
                           'z': ['-1', '-2', '-3']})

    def test_parse_form_data_utf_8(self):
        data = u"""\
\u3082=\u767e&\
\u305b=\u767e&\
\u305b=\u5343&\
\u3059=\u767e&\
\u3059=\u5343&\
\u3059=\u4e07\
"""
        self.assert_equal(http.parse_form_data(self.new_environ(data=data)),
                          {u'\u3082': [u'\u767e'],
                           u'\u305b': [u'\u767e', u'\u5343'],
                           u'\u3059': [u'\u767e', u'\u5343', u'\u4e07']})

        data = u"""\
{__}
Content-Disposition: form-data; name="\u3082"

\u767e
{__}
Content-Disposition: form-data; name="\u305b"

\u767e
{__}
Content-Disposition: form-data; name="\u305b"

\u5343
{__}
Content-Disposition: form-data; name="\u3059"

\u767e
{__}
Content-Disposition: form-data; name="\u3059"

\u5343
{__}
Content-Disposition: form-data; name="\u3059"

\u4e07
{____}
"""
        self.assert_equal(http.parse_form_data(self.new_environ(body=data)),
                          {u'\u3082': [u'\u767e'],
                           u'\u305b': [u'\u767e', u'\u5343'],
                           u'\u3059': [u'\u767e', u'\u5343', u'\u4e07']})

    def test_parse_form_data_post(self):
        data = u"""\
{__}
Content-Disposition: form-data; name="a"; filename="\u3044"
Content-Type: text/plain

spam
eggs
ham

{____}
"""
        form_data = http.parse_form_data(self.new_environ(body=data))
        self.assert_equal(tuple(form_data), ('a',))
        self.assert_equal(len(form_data['a']), 1)
        a = form_data['a'][0]
        self.assert_equal(a.name, 'a')
        self.assert_equal(a.filename, u'\u3044')
        self.assert_equal(a.value, (b'spam\n'
                                    b'eggs\n'
                                    b'ham\n'))

    def test_parse_form_data_put(self):
        data = """\
spam
eggs
ham
"""
        environ = self.new_environ(data=data)
        environ.update(REQUEST_METHOD='PUT',
                       CONTENT_TYPE='text/plain')
        self.assert_equal(http.parse_form_data(environ), {})

    def test_parse_form_data_http_408(self):
        data = """\
{__}
Content-Disposition: form-data; name="a"
Content-Type: text/plain
"""
        environ = self.new_environ(body=data)
        environ['CONTENT_LENGTH'] = str(len(data) * 2)
        with self.assert_raises(http.RequestTimeout):
            http.parse_form_data(environ)

    def test_http_status(self):
        e = http.HTTPStatus()
        self.assert_true(issubclass(e.__class__, ayame.AyameError))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 0)
        self.assert_equal(e.reason, '')
        self.assert_equal(e.status, '')
        self.assert_equal(e.headers, [])
        self.assert_equal(e.description, '')

    def test_http_200(self):
        e = http.OK()
        self.assert_true(issubclass(e.__class__, http.HTTPSuccessful))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 200)
        self.assert_equal(e.reason, 'OK')
        self.assert_equal(e.status, '200 OK')
        self.assert_equal(e.headers, [])
        self.assert_equal(e.description, '')

    def test_http_201(self):
        e = http.Created()
        self.assert_true(issubclass(e.__class__, http.HTTPSuccessful))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 201)
        self.assert_equal(e.reason, 'Created')
        self.assert_equal(e.status, '201 Created')
        self.assert_equal(e.headers, [])
        self.assert_equal(e.description, '')

    def test_http_202(self):
        e = http.Accepted()
        self.assert_true(issubclass(e.__class__, http.HTTPSuccessful))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 202)
        self.assert_equal(e.reason, 'Accepted')
        self.assert_equal(e.status, '202 Accepted')
        self.assert_equal(e.headers, [])
        self.assert_equal(e.description, '')

    def test_http_204(self):
        e = http.NoContent()
        self.assert_true(issubclass(e.__class__, http.HTTPSuccessful))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 204)
        self.assert_equal(e.reason, 'No Content')
        self.assert_equal(e.status, '204 No Content')
        self.assert_equal(e.headers, [])
        self.assert_equal(e.description, '')

    def test_http_301(self):
        uri = 'http://localhost/'
        e = http.MovedPermanently(uri)
        self.assert_true(issubclass(e.__class__, http.HTTPRedirection))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 301)
        self.assert_equal(e.reason, 'Moved Permanently')
        self.assert_equal(e.status, '301 Moved Permanently')
        self.assert_equal(e.headers, [('Location', uri)])
        self.assert_in(uri, e.description)

    def test_http_302(self):
        uri = 'http://localhost/'
        e = http.Found(uri)
        self.assert_true(issubclass(e.__class__, http.HTTPRedirection))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 302)
        self.assert_equal(e.reason, 'Found')
        self.assert_equal(e.status, '302 Found')
        self.assert_equal(e.headers, [('Location', uri)])
        self.assert_in(uri, e.description)

    def test_http_303(self):
        uri = 'http://localhost/'
        e = http.SeeOther(uri)
        self.assert_true(issubclass(e.__class__, http.HTTPRedirection))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 303)
        self.assert_equal(e.reason, 'See Other')
        self.assert_equal(e.status, '303 See Other')
        self.assert_equal(e.headers, [('Location', uri)])
        self.assert_in(uri, e.description)

    def test_http_304(self):
        e = http.NotModified()
        self.assert_true(issubclass(e.__class__, http.HTTPRedirection))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 304)
        self.assert_equal(e.reason, 'Not Modified')
        self.assert_equal(e.status, '304 Not Modified')
        self.assert_equal(e.headers, [])
        self.assert_equal(e.description, '')

    def test_http_400(self):
        e = http.BadRequest()
        self.assert_true(issubclass(e.__class__, http.ClientError))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 400)
        self.assert_equal(e.reason, 'Bad Request')
        self.assert_equal(e.status, '400 Bad Request')
        self.assert_equal(e.headers, [])
        self.assert_equal(e.description, '')

    def test_http_401(self):
        e = http.Unauthrized()
        self.assert_true(issubclass(e.__class__, http.ClientError))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 401)
        self.assert_equal(e.reason, 'Unauthrized')
        self.assert_equal(e.status, '401 Unauthrized')
        self.assert_equal(e.headers, [])
        self.assert_true(e.description)

    def test_http_403(self):
        uri = 'http://localhsot/'
        e = http.Forbidden(uri)
        self.assert_true(issubclass(e.__class__, http.ClientError))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 403)
        self.assert_equal(e.reason, 'Forbidden')
        self.assert_equal(e.status, '403 Forbidden')
        self.assert_equal(e.headers, [])
        self.assert_in(uri, e.description)

    def test_http_404(self):
        uri = 'http://localhsot/'
        e = http.NotFound(uri)
        self.assert_true(issubclass(e.__class__, http.ClientError))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 404)
        self.assert_equal(e.reason, 'Not Found')
        self.assert_equal(e.status, '404 Not Found')
        self.assert_equal(e.headers, [])
        self.assert_in(uri, e.description)

    def test_http_405(self):
        uri = 'http://localhsot/'
        e = http.MethodNotAllowed('PUT', uri, ['GET', 'POST'])
        self.assert_true(issubclass(e.__class__, http.ClientError))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 405)
        self.assert_equal(e.reason, 'Method Not Allowed')
        self.assert_equal(e.status, '405 Method Not Allowed')
        self.assert_equal(e.headers, [('Allow', 'GET, POST')])
        self.assert_in(uri, e.description)

    def test_http_408(self):
        e = http.RequestTimeout()
        self.assert_true(issubclass(e.__class__, http.ClientError))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 408)
        self.assert_equal(e.reason, 'Request Timeout')
        self.assert_equal(e.status, '408 Request Timeout')
        self.assert_equal(e.headers, [])
        self.assert_true(e.description)

    def test_http_500(self):
        e = http.InternalServerError()
        self.assert_true(issubclass(e.__class__, http.ServerError))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 500)
        self.assert_equal(e.reason, 'Internal Server Error')
        self.assert_equal(e.status, '500 Internal Server Error')
        self.assert_equal(e.headers, [])
        self.assert_equal(e.description, '')

    def test_http_501(self):
        method = 'PUT'
        uri = 'http://localhsot/'
        e = http.NotImplemented(method, uri)
        self.assert_true(issubclass(e.__class__, http.ServerError))
        self.assert_equal(str(e), e.status)
        self.assert_equal(e.code, 501)
        self.assert_equal(e.reason, 'Not Implemented')
        self.assert_equal(e.status, '501 Not Implemented')
        self.assert_equal(e.headers, [])
        self.assert_in(method, e.description)
        self.assert_in(uri, e.description)
