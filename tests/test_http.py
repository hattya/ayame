#
# test_http
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

from nose.tools import assert_raises, eq_, ok_

from ayame import exception, http


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
