#
# test_uri
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from ayame import uri
from base import AyameTestCase


class URITestCase(AyameTestCase):

    def test_quote(self):
        for s, ev in (
            ('a@example.com', 'a@example.com'),
            ('/~a/cgi-bin/index.cgi', '/~a/cgi-bin/index.cgi'),
            ('/a/=/1', '/a/=/1'),
            ('/\u3044\u308d\u306f', '/%E3%81%84%E3%82%8D%E3%81%AF'), # iroha in hiragana
            (0, '0'),
            (3.14, '3.14'),
        ):
            with self.subTest(s=s):
                v = uri.quote(s)
                self.assertIsInstance(v, str)
                self.assertEqual(v, ev)

    def test_quote_plus(self):
        for s, ev in (
            ('a b c', 'a+b+c'),
            ('abc', 'abc'),
            # iroha in hiragana
            ('\u3044 \u308d \u306f', '%E3%81%84+%E3%82%8D+%E3%81%AF'),
            ('\u3044\u308d\u306f', '%E3%81%84%E3%82%8D%E3%81%AF'),
        ):
            with self.subTest(s=s):
                v = uri.quote_plus(s)
                self.assertIsInstance(v, str)
                self.assertEqual(v, ev)

    def test_parse_qs_empty(self):
        environ = {}
        self.assertEqual(uri.parse_qs(environ), {})

    def test_parse_qs_ascii(self):
        query = '&'.join((
            'a=1',
            'b=1',
            'b=2',
            'c=1',
            'c=2',
            'c=3',
        ))
        environ = {'QUERY_STRING': uri.quote(query)}
        self.assertEqual(uri.parse_qs(environ), {
            'a': ['1'],
            'b': ['1', '2'],
            'c': ['1', '2', '3'],
        })

    def test_parse_qs_utf_8(self):
        query = '&'.join((
            '\u3044=\u58f1',
            '\u308d=\u58f1',
            '\u308d=\u5f10',
            '\u306f=\u58f1',
            '\u306f=\u5f10',
            '\u306f=\u53c2',
        ))
        environ = {'QUERY_STRING': uri.quote(query)}
        self.assertEqual(uri.parse_qs(environ), {
            '\u3044': ['\u58f1'],
            '\u308d': ['\u58f1', '\u5f10'],
            '\u306f': ['\u58f1', '\u5f10', '\u53c2'],
        })

    def test_application_uri_server_name(self):
        for scheme, port, ev in (
            ('http', '80', 'http://localhost/'),
            ('http', '8080', 'http://localhost:8080/'),
            ('https', '443', 'https://localhost/'),
            ('https', '8443', 'https://localhost:8443/'),
        ):
            with self.subTest(scheme=scheme, SERVER_PORT=port):
                environ = {
                    'wsgi.url_scheme': scheme,
                    'SERVER_NAME': 'localhost',
                    'SERVER_PORT': port,
                }
                self.assertEqual(uri.application_uri(environ), ev)

    def test_application_uri_http_host(self):
        for scheme, port, host, ev in (
            ('http', '8080', 'localhost', 'http://localhost/'),
            ('http', '80', 'localhost:8080', 'http://localhost:8080/'),
            ('https', '8443', 'localhost', 'https://localhost/'),
            ('https', '443', 'localhost:8443', 'https://localhost:8443/'),
        ):
            with self.subTest(scheme=scheme, SERVER_PORT=port, HTTP_HOST=host):
                environ = {
                    'wsgi.url_scheme': scheme,
                    'SERVER_NAME': '127.0.0.1',
                    'SERVER_PORT': port,
                    'HTTP_HOST': host,
                }
                self.assertEqual(uri.application_uri(environ), ev)

    def test_application_uri_script_name(self):
        environ = {
            'wsgi.url_scheme': 'https',
            'HTTP_HOST': 'localhost',
        }
        self.assertEqual(uri.application_uri(environ), 'https://localhost/')

        environ = {
            'wsgi.url_scheme': 'https',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '',
        }
        self.assertEqual(uri.application_uri(environ), 'https://localhost/')

        environ = {
            'wsgi.url_scheme': 'https',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '/ayame',
        }
        self.assertEqual(uri.application_uri(environ), 'https://localhost/ayame')

    def test_request_uri(self):
        # SCRIPT_NAME and PATH_INFO are empty
        environ = {
            'wsgi.url_scheme': 'https',
            'HTTP_HOST': 'localhost',
        }
        self.assertEqual(uri.request_uri(environ), 'https://localhost/')

        # SCRIPT_NAME is empty
        environ = {
            'wsgi.url_scheme': 'https',
            'HTTP_HOST': 'localhost',
            'PATH_INFO': '/',
        }
        self.assertEqual(uri.request_uri(environ), 'https://localhost/')

        environ = {
            'wsgi.url_scheme': 'https',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '',
            'PATH_INFO': '/',
        }
        self.assertEqual(uri.request_uri(environ), 'https://localhost/')

    def test_request_uri_script_name(self):
        # PATH_INFO is empty
        environ = {
            'wsgi.url_scheme': 'https',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '/ayame',
        }
        self.assertEqual(uri.request_uri(environ), 'https://localhost/ayame')

        environ = {
            'wsgi.url_scheme': 'https',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '/ayame',
            'PATH_INFO': '',
        }
        self.assertEqual(uri.request_uri(environ), 'https://localhost/ayame')

        # SCRIPT_NAME and PATH_INFO
        environ = {
            'wsgi.url_scheme': 'https',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '/ayame',
            'PATH_INFO': '/',
        }
        self.assertEqual(uri.request_uri(environ), 'https://localhost/ayame/')

    def test_request_uri_query_string(self):
        # QUERY_STRING is empty
        environ = {
            'wsgi.url_scheme': 'https',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '/ayame',
            'PATH_INFO': '/',
        }
        self.assertEqual(uri.request_uri(environ, True), 'https://localhost/ayame/')

        environ = {
            'wsgi.url_scheme': 'https',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '/ayame',
            'PATH_INFO': '/',
            'QUERY_STRING': '',
        }
        self.assertEqual(uri.request_uri(environ, True), 'https://localhost/ayame/')

        # SCRIPT_NAME and QUERY_STRING
        environ = {
            'wsgi.url_scheme': 'https',
            'HTTP_HOST': 'localhost',
            'SCRIPT_NAME': '/ayame',
            'PATH_INFO': '/',
            'QUERY_STRING': 'FrontPage',
        }
        self.assertEqual(uri.request_uri(environ, True), 'https://localhost/ayame/?FrontPage')

    def test_request_path(self):
        # SCRIPT_NAME and PATH_INFO are empty
        environ = {}
        self.assertEqual(uri.request_path(environ), '/')

        # SCRIPT_NAME is empty
        environ = {
            'PATH_INFO': '/',
        }
        self.assertEqual(uri.request_path(environ), '/')

        environ = {
            'SCRIPT_NAME': '',
            'PATH_INFO': '/',
        }
        self.assertEqual(uri.request_path(environ), '/')

        # PATH_INFO is empty
        environ = {
            'SCRIPT_NAME': '/ayame',
        }
        self.assertEqual(uri.request_path(environ), '/ayame')

        environ = {
            'SCRIPT_NAME': '/ayame',
            'PATH_INFO': '',
        }
        self.assertEqual(uri.request_path(environ), '/ayame')

        # SCRIPT_NAME and PATH_INFO
        environ = {
            'SCRIPT_NAME': '/ayame',
            'PATH_INFO': '/',
        }
        self.assertEqual(uri.request_path(environ), '/ayame/')

    def test_is_relative_uri(self):
        self.assertFalse(uri.is_relative_uri(None))
        self.assertFalse(uri.is_relative_uri('/ayame'))
        self.assertFalse(uri.is_relative_uri('#fragment'))
        self.assertFalse(uri.is_relative_uri('http://localhost/ayame'))

        self.assertTrue(uri.is_relative_uri(''))
        self.assertTrue(uri.is_relative_uri('.'))
        self.assertTrue(uri.is_relative_uri('..'))
        self.assertTrue(uri.is_relative_uri('spam.html'))
        self.assertTrue(uri.is_relative_uri('spam/eggs.html'))

    def test_relative_uri(self):
        environ = {}
        self.assertEqual(uri.relative_uri(environ, '/spam.html'), '/spam.html')
        self.assertEqual(uri.relative_uri(environ, 'spam.html'), 'spam.html')

        environ = {'PATH_INFO': ''}
        self.assertEqual(uri.relative_uri(environ, '/spam.html'), '/spam.html')
        self.assertEqual(uri.relative_uri(environ, 'spam.html'), 'spam.html')

        environ = {'PATH_INFO': '/'}
        self.assertEqual(uri.relative_uri(environ, 'spam.html'), 'spam.html')

        environ = {'PATH_INFO': '/spam'}
        self.assertEqual(uri.relative_uri(environ, 'eggs.html'), 'eggs.html')

        environ = {'PATH_INFO': '//spam'}
        self.assertEqual(uri.relative_uri(environ, 'eggs.html'), 'eggs.html')

        environ = {'PATH_INFO': '/spam/'}
        self.assertEqual(uri.relative_uri(environ, 'eggs.html'), '../eggs.html')

        environ = {'PATH_INFO': '/spam/eggs'}
        self.assertEqual(uri.relative_uri(environ, 'ham.html'), '../ham.html')

        environ = {'PATH_INFO': '/spam/eggs/'}
        self.assertEqual(uri.relative_uri(environ, 'ham.html'), '../../ham.html')

        environ = {'PATH_INFO': '/spam/eggs/ham'}
        self.assertEqual(uri.relative_uri(environ, 'toast.html'), '../../toast.html')
