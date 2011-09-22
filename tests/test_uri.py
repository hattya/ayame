#
# test_uri
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

from nose.tools import eq_, ok_

from ayame import uri


def test_quote():
    v = uri.quote('a@example.com')
    eq_(v, b'a@example.com')
    ok_(isinstance(v, bytes))

    v = uri.quote('/~a/cgi-bin/index.cgi')
    eq_(v, b'/~a/cgi-bin/index.cgi')
    ok_(isinstance(v, bytes))

    v = uri.quote('/a/=/1')
    eq_(v, b'/a/=/1')
    ok_(isinstance(v, bytes))

    # iroha in hiragana
    v = uri.quote('/\u3044\u308d\u306f')
    eq_(v, b'/%E3%81%84%E3%82%8D%E3%81%AF')
    ok_(isinstance(v, bytes))

    v = uri.quote(0)
    eq_(v, b'0')
    ok_(isinstance(v, bytes))

    v = uri.quote(3.14)
    eq_(v, b'3.14')
    ok_(isinstance(v, bytes))

def test_quote_plus():
    v = uri.quote_plus('a b c')
    eq_(v, b'a+b+c')
    ok_(isinstance(v, bytes))

    v = uri.quote_plus('abc')
    eq_(v, b'abc')
    ok_(isinstance(v, bytes))

    # iroha in hiragana
    v = uri.quote_plus('\u3044 \u308d \u306f')
    eq_(v, b'%E3%81%84+%E3%82%8D+%E3%81%AF')
    ok_(isinstance(v, bytes))

    v = uri.quote_plus('\u3044\u308d\u306f')
    eq_(v, b'%E3%81%84%E3%82%8D%E3%81%AF')
    ok_(isinstance(v, bytes))

def test_application_uri():
    # SERVER_NAME and SERVER_PORT
    environ = {'wsgi.url_scheme': 'http',
               'SERVER_NAME': 'localhost',
               'SERVER_PORT': '80'}
    eq_(uri.application_uri(environ), 'http://localhost/')

    environ = {'wsgi.url_scheme': 'http',
               'SERVER_NAME': 'localhost',
               'SERVER_PORT': '8080'}
    eq_(uri.application_uri(environ), 'http://localhost:8080/')

    environ = {'wsgi.url_scheme': 'https',
               'SERVER_NAME': 'localhost',
               'SERVER_PORT': '443'}
    eq_(uri.application_uri(environ), 'https://localhost/')

    environ = {'wsgi.url_scheme': 'https',
               'SERVER_NAME': 'localhost',
               'SERVER_PORT': '8008'}
    eq_(uri.application_uri(environ), 'https://localhost:8008/')

    # HTTP_HOST
    environ = {'wsgi.url_scheme': 'http',
               'SERVER_NAME': '127.0.0.1',
               'SERVER_PORT': '8080',
               'HTTP_HOST': 'localhost:80'}
    eq_(uri.application_uri(environ), 'http://localhost/')

    environ = {'wsgi.url_scheme': 'http',
               'SERVER_NAME': '127.0.0.1',
               'SERVER_PORT': '80',
               'HTTP_HOST': 'localhost:8080'}
    eq_(uri.application_uri(environ), 'http://localhost:8080/')

    environ = {'wsgi.url_scheme': 'https',
               'SERVER_NAME': '127.0.0.1',
               'SERVER_PORT': '8008',
               'HTTP_HOST': 'localhost:443'}
    eq_(uri.application_uri(environ), 'https://localhost/')

    environ = {'wsgi.url_scheme': 'https',
               'SERVER_NAME': '127.0.0.1',
               'SERVER_PORT': '443',
               'HTTP_HOST': 'localhost:8008'}
    eq_(uri.application_uri(environ), 'https://localhost:8008/')

    # SCRIPT_NAME
    environ = {'wsgi.url_scheme': 'https',
               'HTTP_HOST': 'localhost'}
    eq_(uri.application_uri(environ), 'https://localhost/')

    environ = {'wsgi.url_scheme': 'https',
               'HTTP_HOST': 'localhost',
               'SCRIPT_NAME': ''}
    eq_(uri.application_uri(environ), 'https://localhost/')

    environ = {'wsgi.url_scheme': 'https',
               'HTTP_HOST': 'localhost',
               'SCRIPT_NAME': '/ayame'}
    eq_(uri.application_uri(environ), 'https://localhost/ayame')

def test_request_uri():
    # SCRIPT_NAME and PATH_INFO are empty
    environ = {'wsgi.url_scheme': 'http',
               'HTTP_HOST': 'localhost'}
    eq_(uri.request_uri(environ), 'http://localhost/')

    # SCRIPT_NAME is empty
    environ = {'wsgi.url_scheme': 'http',
               'HTTP_HOST': 'localhost',
               'PATH_INFO': '/'}
    eq_(uri.request_uri(environ), 'http://localhost/')

    environ = {'wsgi.url_scheme': 'http',
               'HTTP_HOST': 'localhost',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/'}
    eq_(uri.request_uri(environ), 'http://localhost/')

    # PATH_INFO is empty
    environ = {'wsgi.url_scheme': 'http',
               'HTTP_HOST': 'localhost',
               'SCRIPT_NAME': '/ayame'}
    eq_(uri.request_uri(environ), 'http://localhost/ayame')

    environ = {'wsgi.url_scheme': 'http',
               'HTTP_HOST': 'localhost',
               'SCRIPT_NAME': '/ayame',
               'PATH_INFO': ''}
    eq_(uri.request_uri(environ), 'http://localhost/ayame')

    # SCRIPT_NAME and PATH_INFO
    environ = {'wsgi.url_scheme': 'http',
               'HTTP_HOST': 'localhost',
               'SCRIPT_NAME': '/ayame',
               'PATH_INFO': '/'}
    eq_(uri.request_uri(environ), 'http://localhost/ayame/')

    # QUERY_STRING
    environ = {'wsgi.url_scheme': 'http',
               'HTTP_HOST': 'localhost',
               'SCRIPT_NAME': '/ayame',
               'PATH_INFO': '/'}
    eq_(uri.request_uri(environ, True), 'http://localhost/ayame/')

    environ = {'wsgi.url_scheme': 'http',
               'HTTP_HOST': 'localhost',
               'SCRIPT_NAME': '/ayame',
               'PATH_INFO': '/',
               'QUERY_STRING': ''}
    eq_(uri.request_uri(environ, True), 'http://localhost/ayame/')

    environ = {'wsgi.url_scheme': 'http',
               'HTTP_HOST': 'localhost',
               'SCRIPT_NAME': '/ayame',
               'PATH_INFO': '/',
               'QUERY_STRING': 'FrontPage'}
    eq_(uri.request_uri(environ, True), 'http://localhost/ayame/?FrontPage')

def test_request_path():
    # SCRIPT_NAME and PATH_INFO are empty
    environ = {}
    eq_(uri.request_path(environ), '/')

    # SCRIPT_NAME is empty
    environ = {'PATH_INFO': '/'}
    eq_(uri.request_path(environ), '/')

    environ = {'SCRIPT_NAME': '',
               'PATH_INFO': '/'}
    eq_(uri.request_path(environ), '/')

    # PATH_INFO is empty
    environ = {'SCRIPT_NAME': '/ayame'}
    eq_(uri.request_path(environ), '/ayame')

    environ = {'SCRIPT_NAME': '/ayame',
               'PATH_INFO': ''}
    eq_(uri.request_path(environ), '/ayame')

    # SCRIPT_NAME and PATH_INFO
    environ = {'SCRIPT_NAME': '/ayame',
               'PATH_INFO': '/'}
    eq_(uri.request_path(environ), '/ayame/')

def test_is_relative_uri():
    ok_(not uri.is_relative_uri(None))
    ok_(not uri.is_relative_uri('/ayame'))
    ok_(not uri.is_relative_uri('#fragment'))
    ok_(not uri.is_relative_uri('http://localhost/ayame'))

    ok_(uri.is_relative_uri(''))
    ok_(uri.is_relative_uri('.'))
    ok_(uri.is_relative_uri('..'))
    ok_(uri.is_relative_uri('foo.html'))
    ok_(uri.is_relative_uri('foo/bar.html'))
