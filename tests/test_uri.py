#
# test_uri
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

from ayame import uri
from base import AyameTestCase


class URITestCase(AyameTestCase):

    def test_quote(self):
        v = uri.quote('a@example.com')
        self.assert_is_instance(v, str)
        self.assert_equal(v, 'a@example.com')

        v = uri.quote('/~a/cgi-bin/index.cgi')
        self.assert_is_instance(v, str)
        self.assert_equal(v, '/~a/cgi-bin/index.cgi')

        v = uri.quote('/a/=/1')
        self.assert_is_instance(v, str)
        self.assert_equal(v, '/a/=/1')

        # iroha in hiragana
        v = uri.quote(u'/\u3044\u308d\u306f')
        self.assert_is_instance(v, str)
        self.assert_equal(v, '/%E3%81%84%E3%82%8D%E3%81%AF')

        v = uri.quote(0)
        self.assert_is_instance(v, str)
        self.assert_equal(v, '0')

        v = uri.quote(3.14)
        self.assert_is_instance(v, str)
        self.assert_equal(v, '3.14')

    def test_quote_plus(self):
        v = uri.quote_plus('a b c')
        self.assert_is_instance(v, str)
        self.assert_equal(v, 'a+b+c')

        v = uri.quote_plus('abc')
        self.assert_is_instance(v, str)
        self.assert_equal(v, 'abc')

        # iroha in hiragana
        v = uri.quote_plus(u'\u3044 \u308d \u306f')
        self.assert_is_instance(v, str)
        self.assert_equal(v, '%E3%81%84+%E3%82%8D+%E3%81%AF')

        v = uri.quote_plus(u'\u3044\u308d\u306f')
        self.assert_is_instance(v, str)
        self.assert_equal(v, '%E3%81%84%E3%82%8D%E3%81%AF')

    def test_parse_qs_empty(self):
        environ = {}
        self.assert_equal(uri.parse_qs(environ), {})

    def test_parse_qs_ascii(self):
        query = ('a=1&'
                 'b=1&'
                 'b=2&'
                 'c=1&'
                 'c=2&'
                 'c=3')
        environ = {'QUERY_STRING': uri.quote(query)}
        self.assert_equal(uri.parse_qs(environ),
                          {'a': ['1'],
                           'b': ['1', '2'],
                           'c': ['1', '2', '3']})

    def test_parse_qs_utf_8(self):
        query = (u'\u3044=\u58f1&'
                 u'\u308d=\u58f1&'
                 u'\u308d=\u5f10&'
                 u'\u306f=\u58f1&'
                 u'\u306f=\u5f10&'
                 u'\u306f=\u53c2')
        environ = {'QUERY_STRING': uri.quote(query)}
        self.assert_equal(uri.parse_qs(environ),
                          {u'\u3044': [u'\u58f1'],
                           u'\u308d': [u'\u58f1', u'\u5f10'],
                           u'\u306f': [u'\u58f1', u'\u5f10', u'\u53c2']})

    def test_application_uri_server_name(self):
        environ = {'wsgi.url_scheme': 'http',
                   'SERVER_NAME': 'localhost',
                   'SERVER_PORT': '80'}
        self.assert_equal(uri.application_uri(environ), 'http://localhost/')

        environ = {'wsgi.url_scheme': 'http',
                   'SERVER_NAME': 'localhost',
                   'SERVER_PORT': '8080'}
        self.assert_equal(uri.application_uri(environ), 'http://localhost:8080/')

        environ = {'wsgi.url_scheme': 'https',
                   'SERVER_NAME': 'localhost',
                   'SERVER_PORT': '443'}
        self.assert_equal(uri.application_uri(environ), 'https://localhost/')

        environ = {'wsgi.url_scheme': 'https',
                   'SERVER_NAME': 'localhost',
                   'SERVER_PORT': '8008'}
        self.assert_equal(uri.application_uri(environ), 'https://localhost:8008/')

    def test_application_uri_http_host(self):
        environ = {'wsgi.url_scheme': 'http',
                   'SERVER_NAME': '127.0.0.1',
                   'SERVER_PORT': '8080',
                   'HTTP_HOST': 'localhost:80'}
        self.assert_equal(uri.application_uri(environ), 'http://localhost/')

        environ = {'wsgi.url_scheme': 'http',
                   'SERVER_NAME': '127.0.0.1',
                   'SERVER_PORT': '80',
                   'HTTP_HOST': 'localhost:8080'}
        self.assert_equal(uri.application_uri(environ), 'http://localhost:8080/')

        environ = {'wsgi.url_scheme': 'https',
                   'SERVER_NAME': '127.0.0.1',
                   'SERVER_PORT': '8008',
                   'HTTP_HOST': 'localhost:443'}
        self.assert_equal(uri.application_uri(environ), 'https://localhost/')

        environ = {'wsgi.url_scheme': 'https',
                   'SERVER_NAME': '127.0.0.1',
                   'SERVER_PORT': '443',
                   'HTTP_HOST': 'localhost:8008'}
        self.assert_equal(uri.application_uri(environ), 'https://localhost:8008/')

    def test_application_uri_script_name(self):
        environ = {'wsgi.url_scheme': 'https',
                   'HTTP_HOST': 'localhost'}
        self.assert_equal(uri.application_uri(environ), 'https://localhost/')

        environ = {'wsgi.url_scheme': 'https',
                   'HTTP_HOST': 'localhost',
                   'SCRIPT_NAME': ''}
        self.assert_equal(uri.application_uri(environ), 'https://localhost/')

        environ = {'wsgi.url_scheme': 'https',
                   'HTTP_HOST': 'localhost',
                   'SCRIPT_NAME': '/ayame'}
        self.assert_equal(uri.application_uri(environ), 'https://localhost/ayame')

    def test_request_uri(self):
        # SCRIPT_NAME and PATH_INFO are empty
        environ = {'wsgi.url_scheme': 'http',
                   'HTTP_HOST': 'localhost'}
        self.assert_equal(uri.request_uri(environ), 'http://localhost/')

        # SCRIPT_NAME is empty
        environ = {'wsgi.url_scheme': 'http',
                   'HTTP_HOST': 'localhost',
                   'PATH_INFO': '/'}
        self.assert_equal(uri.request_uri(environ), 'http://localhost/')

        environ = {'wsgi.url_scheme': 'http',
                   'HTTP_HOST': 'localhost',
                   'SCRIPT_NAME': '',
                   'PATH_INFO': '/'}
        self.assert_equal(uri.request_uri(environ), 'http://localhost/')

    def test_request_uri_script_name(self):
        # PATH_INFO is empty
        environ = {'wsgi.url_scheme': 'http',
                   'HTTP_HOST': 'localhost',
                   'SCRIPT_NAME': '/ayame'}
        self.assert_equal(uri.request_uri(environ), 'http://localhost/ayame')

        environ = {'wsgi.url_scheme': 'http',
                   'HTTP_HOST': 'localhost',
                   'SCRIPT_NAME': '/ayame',
                   'PATH_INFO': ''}
        self.assert_equal(uri.request_uri(environ), 'http://localhost/ayame')

        # SCRIPT_NAME and PATH_INFO
        environ = {'wsgi.url_scheme': 'http',
                   'HTTP_HOST': 'localhost',
                   'SCRIPT_NAME': '/ayame',
                   'PATH_INFO': '/'}
        self.assert_equal(uri.request_uri(environ), 'http://localhost/ayame/')

    def test_request_uri_query_string(self):
        environ = {'wsgi.url_scheme': 'http',
                   'HTTP_HOST': 'localhost',
                   'SCRIPT_NAME': '/ayame',
                   'PATH_INFO': '/'}
        self.assert_equal(uri.request_uri(environ, True), 'http://localhost/ayame/')

        environ = {'wsgi.url_scheme': 'http',
                   'HTTP_HOST': 'localhost',
                   'SCRIPT_NAME': '/ayame',
                   'PATH_INFO': '/',
                   'QUERY_STRING': ''}
        self.assert_equal(uri.request_uri(environ, True), 'http://localhost/ayame/')

        environ = {'wsgi.url_scheme': 'http',
                   'HTTP_HOST': 'localhost',
                   'SCRIPT_NAME': '/ayame',
                   'PATH_INFO': '/',
                   'QUERY_STRING': 'FrontPage'}
        self.assert_equal(uri.request_uri(environ, True), 'http://localhost/ayame/?FrontPage')

    def test_request_path(self):
        # SCRIPT_NAME and PATH_INFO are empty
        environ = {}
        self.assert_equal(uri.request_path(environ), '/')

        # SCRIPT_NAME is empty
        environ = {'PATH_INFO': '/'}
        self.assert_equal(uri.request_path(environ), '/')

        environ = {'SCRIPT_NAME': '',
                   'PATH_INFO': '/'}
        self.assert_equal(uri.request_path(environ), '/')

        # PATH_INFO is empty
        environ = {'SCRIPT_NAME': '/ayame'}
        self.assert_equal(uri.request_path(environ), '/ayame')

        environ = {'SCRIPT_NAME': '/ayame',
                   'PATH_INFO': ''}
        self.assert_equal(uri.request_path(environ), '/ayame')

        # SCRIPT_NAME and PATH_INFO
        environ = {'SCRIPT_NAME': '/ayame',
                   'PATH_INFO': '/'}
        self.assert_equal(uri.request_path(environ), '/ayame/')

    def test_is_relative_uri(self):
        self.assert_false(uri.is_relative_uri(None))
        self.assert_false(uri.is_relative_uri('/ayame'))
        self.assert_false(uri.is_relative_uri('#fragment'))
        self.assert_false(uri.is_relative_uri('http://localhost/ayame'))

        self.assert_true(uri.is_relative_uri(''))
        self.assert_true(uri.is_relative_uri('.'))
        self.assert_true(uri.is_relative_uri('..'))
        self.assert_true(uri.is_relative_uri('spam.html'))
        self.assert_true(uri.is_relative_uri('spam/eggs.html'))

    def test_relative_uri(self):
        environ = {}
        self.assert_equal(uri.relative_uri(environ, '/spam.html'), '/spam.html')
        self.assert_equal(uri.relative_uri(environ, 'spam.html'), 'spam.html')

        environ = {'PATH_INFO': '/'}
        self.assert_equal(uri.relative_uri(environ, 'spam.html'), 'spam.html')

        environ = {'PATH_INFO': '/spam'}
        self.assert_equal(uri.relative_uri(environ, 'eggs.html'), 'eggs.html')

        environ = {'PATH_INFO': '//spam'}
        self.assert_equal(uri.relative_uri(environ, 'eggs.html'), 'eggs.html')

        environ = {'PATH_INFO': '/spam/'}
        self.assert_equal(uri.relative_uri(environ, 'eggs.html'), '../eggs.html')

        environ = {'PATH_INFO': '/spam/eggs'}
        self.assert_equal(uri.relative_uri(environ, 'ham.html'), '../ham.html')

        environ = {'PATH_INFO': '/spam/eggs/'}
        self.assert_equal(uri.relative_uri(environ, 'ham.html'), '../../ham.html')

        environ = {'PATH_INFO': '/spam/eggs/ham'}
        self.assert_equal(uri.relative_uri(environ, 'toast.html'), '../../toast.html')
