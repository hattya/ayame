#
# test_http
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

import io

from nose.tools import assert_raises, eq_, ok_

from ayame import exception, http


def test_parse_form_data():
    # empty
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'POST',
               'CONTENT_LENGTH': '0'}
    eq_(http.parse_form_data(environ), {})

    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'POST',
               'CONTENT_TYPE': 'application/x-www-form-urlencoded',
               'CONTENT_LENGTH': '0'}
    eq_(http.parse_form_data(environ), {})

    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'POST',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.http',
               'CONTENT_LENGTH': '0'}
    eq_(http.parse_form_data(environ), {})

    # ASCII
    data = ('x=-1&'
            'y=-1&'
            'y=-2&'
            'z=-1&'
            'z=-2&'
            'z=-3')
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'CONTENT_TYPE': 'application/x-www-form-urlencoded',
               'CONTENT_LENGTH': str(len(data))}
    eq_(http.parse_form_data(environ), {'x': ['-1'],
                                        'y': ['-1', '-2'],
                                        'z': ['-1', '-2', '-3']})

    data = ('--ayame.http\r\n'
            'Content-Disposition: form-data; name="x"\r\n'
            '\r\n'
            '-1\r\n'
            '--ayame.http\r\n'
            'Content-Disposition: form-data; name="y"\r\n'
            '\r\n'
            '-1\r\n'
            '--ayame.http\r\n'
            'Content-Disposition: form-data; name="y"\r\n'
            '\r\n'
            '-2\r\n'
            '--ayame.http\r\n'
            'Content-Disposition: form-data; name="z"\r\n'
            '\r\n'
            '-1\r\n'
            '--ayame.http\r\n'
            'Content-Disposition: form-data; name="z"\r\n'
            '\r\n'
            '-2\r\n'
            '--ayame.http\r\n'
            'Content-Disposition: form-data; name="z"\r\n'
            '\r\n'
            '-3\r\n'
            '--ayame.http--\r\n')
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.http',
               'CONTENT_LENGTH': str(len(data))}
    eq_(http.parse_form_data(environ), {'x': ['-1'],
                                        'y': ['-1', '-2'],
                                        'z': ['-1', '-2', '-3']})

    # UTF-8
    data = (u'\u3082=\u767e&'
            u'\u305b=\u767e&'
            u'\u305b=\u5343&'
            u'\u3059=\u767e&'
            u'\u3059=\u5343&'
            u'\u3059=\u4e07')
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'CONTENT_TYPE': 'application/x-www-form-urlencoded',
               'CONTENT_LENGTH': str(len(data))}
    eq_(http.parse_form_data(environ),
        {u'\u3082': [u'\u767e'],
         u'\u305b': [u'\u767e', u'\u5343'],
         u'\u3059': [u'\u767e', u'\u5343', u'\u4e07']})

    data = (u'--ayame.http\r\n'
            u'Content-Disposition: form-data; name="\u3082"\r\n'
            u'\r\n'
            u'\u767e\r\n'
            u'--ayame.http\r\n'
            u'Content-Disposition: form-data; name="\u305b"\r\n'
            u'\r\n'
            u'\u767e\r\n'
            u'--ayame.http\r\n'
            u'Content-Disposition: form-data; name="\u305b"\r\n'
            u'\r\n'
            u'\u5343\r\n'
            u'--ayame.http\r\n'
            u'Content-Disposition: form-data; name="\u3059"\r\n'
            u'\r\n'
            u'\u767e\r\n'
            u'--ayame.http\r\n'
            u'Content-Disposition: form-data; name="\u3059"\r\n'
            u'\r\n'
            u'\u5343\r\n'
            u'--ayame.http\r\n'
            u'Content-Disposition: form-data; name="\u3059"\r\n'
            u'\r\n'
            u'\u4e07\r\n'
            u'--ayame.http--\r\n')
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.http',
               'CONTENT_LENGTH': str(len(data))}
    eq_(http.parse_form_data(environ),
        {u'\u3082': [u'\u767e'],
         u'\u305b': [u'\u767e', u'\u5343'],
         u'\u3059': [u'\u767e', u'\u5343', u'\u4e07']})

    # filename
    data = (u'--ayame.http\r\n'
            u'Content-Disposition: form-data; name="a"; filename="\u3044"\r\n'
            u'Content-Type: text/plain\r\n'
            u'\r\n'
            u'spam\n'
            u'eggs\n'
            u'ham\n'
            u'\r\n'
            u'--ayame.http--\r\n')
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.http',
               'CONTENT_LENGTH': str(len(data))}
    form_data = http.parse_form_data(environ)
    eq_(tuple(form_data), ('a',))

    fields = form_data['a']
    eq_(len(fields), 1)

    a = fields[0]
    eq_(a.name, 'a')
    eq_(a.filename, u'\u3044')
    eq_(a.value, (b'spam\n'
                  b'eggs\n'
                  b'ham\n'))

    # PUT
    data = ('spam\n'
            'eggs\n'
            'ham\n')
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'PUT',
               'CONTENT_TYPE': 'text/plain',
               'CONTENT_LENGTH': str(len(data))}
    eq_(http.parse_form_data(environ), {})

    # 408 Request Timeout
    data = ('--ayame.http\r\n'
            'Content-Disposition: form-data; name="a"\r\n'
            'Content-Type: text/plain\r\n')
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.http',
               'CONTENT_LENGTH': str(len(data) + 1)}
    assert_raises(http.RequestTimeout, http.parse_form_data, environ)

def test_http_status():
    e = http.HTTPStatus()
    eq_(e.__class__.__bases__, (exception.AyameError,))
    eq_(str(e), e.status)
    eq_(e.code, 0)
    eq_(e.reason, '')
    eq_(e.status, '')
    eq_(e.headers, [])
    ok_(e.html())

def test_http_200():
    e = http.OK()
    eq_(e.__class__.__bases__, (http.HTTPSuccessful,))
    eq_(str(e), e.status)
    eq_(e.code, 200)
    eq_(e.reason, 'OK')
    eq_(e.status, '200 OK')
    eq_(e.headers, [])
    ok_(not e.html())

def test_http_201():
    e = http.Created()
    eq_(e.__class__.__bases__, (http.HTTPSuccessful,))
    eq_(str(e), e.status)
    eq_(e.code, 201)
    eq_(e.reason, 'Created')
    eq_(e.status, '201 Created')
    eq_(e.headers, [])
    ok_(not e.html())

def test_http_202():
    e = http.Accepted()
    eq_(e.__class__.__bases__, (http.HTTPSuccessful,))
    eq_(str(e), e.status)
    eq_(e.code, 202)
    eq_(e.reason, 'Accepted')
    eq_(e.status, '202 Accepted')
    eq_(e.headers, [])
    ok_(not e.html())

def test_http_204():
    e = http.NoContent()
    eq_(e.__class__.__bases__, (http.HTTPSuccessful,))
    eq_(str(e), e.status)
    eq_(e.code, 204)
    eq_(e.reason, 'No Content')
    eq_(e.status, '204 No Content')
    eq_(e.headers, [])
    ok_(not e.html())

def test_http_301():
    uri = 'http://localhost/'
    e = http.MovedPermanently(uri)
    eq_(e.__class__.__bases__, (http.Redirection,))
    eq_(str(e), e.status)
    eq_(e.code, 301)
    eq_(e.reason, 'Moved Permanently')
    eq_(e.status, '301 Moved Permanently')
    eq_(e.headers, [('Location', uri)])
    ok_(e.html())

def test_http_302():
    uri = 'http://localhost/'
    e = http.Found(uri)
    eq_(e.__class__.__bases__, (http.Redirection,))
    eq_(str(e), e.status)
    eq_(e.code, 302)
    eq_(e.reason, 'Found')
    eq_(e.status, '302 Found')
    eq_(e.headers, [('Location', uri)])
    ok_(e.html())

def test_http_303():
    uri = 'http://localhost/'
    e = http.SeeOther(uri)
    eq_(e.__class__.__bases__, (http.Redirection,))
    eq_(str(e), e.status)
    eq_(e.code, 303)
    eq_(e.reason, 'See Other')
    eq_(e.status, '303 See Other')
    eq_(e.headers, [('Location', uri)])
    ok_(e.html())

def test_http_304():
    e = http.NotModified()
    eq_(e.__class__.__bases__, (http.Redirection,))
    eq_(str(e), e.status)
    eq_(e.code, 304)
    eq_(e.reason, 'Not Modified')
    eq_(e.status, '304 Not Modified')
    eq_(e.headers, [])
    ok_(not e.html())

def test_http_400():
    e = http.BadRequest()
    eq_(e.__class__.__bases__, (http.ClientError,))
    eq_(str(e), e.status)
    eq_(e.code, 400)
    eq_(e.reason, 'Bad Request')
    eq_(e.status, '400 Bad Request')
    eq_(e.headers, [])
    ok_(e.html())

def test_http_401():
    e = http.Unauthrized()
    eq_(e.__class__.__bases__, (http.ClientError,))
    eq_(str(e), e.status)
    eq_(e.code, 401)
    eq_(e.reason, 'Unauthrized')
    eq_(e.status, '401 Unauthrized')
    eq_(e.headers, [])
    ok_(e.html())

def test_http_403():
    uri = 'http://localhsot/'
    e = http.Forbidden(uri)
    eq_(e.__class__.__bases__, (http.ClientError,))
    eq_(str(e), e.status)
    eq_(e.code, 403)
    eq_(e.reason, 'Forbidden')
    eq_(e.status, '403 Forbidden')
    eq_(e.headers, [])
    ok_(e.html())

def test_http_404():
    uri = 'http://localhsot/'
    e = http.NotFound(uri)
    eq_(e.__class__.__bases__, (http.ClientError,))
    eq_(str(e), e.status)
    eq_(e.code, 404)
    eq_(e.reason, 'Not Found')
    eq_(e.status, '404 Not Found')
    eq_(e.headers, [])
    ok_(e.html())

def test_http_405():
    uri = 'http://localhsot/'
    e = http.MethodNotAllowed('PUT', uri, ['GET', 'POST'])
    eq_(e.__class__.__bases__, (http.ClientError,))
    eq_(str(e), e.status)
    eq_(e.code, 405)
    eq_(e.reason, 'Method Not Allowed')
    eq_(e.status, '405 Method Not Allowed')
    eq_(e.headers, [('Allow', 'GET,POST')])
    ok_(e.html())

def test_http_408():
    e = http.RequestTimeout()
    eq_(e.__class__.__bases__, (http.ClientError,))
    eq_(str(e), e.status)
    eq_(e.code, 408)
    eq_(e.reason, 'Request Timeout')
    eq_(e.status, '408 Request Timeout')
    eq_(e.headers, [])
    ok_(e.html())

def test_http_500():
    e = http.InternalServerError()
    eq_(e.__class__.__bases__, (http.ServerError,))
    eq_(str(e), e.status)
    eq_(e.code, 500)
    eq_(e.reason, 'Internal Server Error')
    eq_(e.status, '500 Internal Server Error')
    eq_(e.headers, [])
    ok_(e.html())

def test_http_501():
    method = 'PUT'
    uri = 'http://localhsot/'
    e = http.NotImplemented(method, uri)
    eq_(e.__class__.__bases__, (http.ServerError,))
    eq_(str(e), e.status)
    eq_(e.code, 501)
    eq_(e.reason, 'Not Implemented')
    eq_(e.status, '501 Not Implemented')
    eq_(e.headers, [])
    ok_(e.html())
