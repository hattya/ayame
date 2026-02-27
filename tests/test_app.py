#
# test_app
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import locale
import os
import tempfile
import unittest.mock

import ayame
from ayame import basic, http
from base import AyameTestCase


class AppTestCase(AyameTestCase):

    def setUp(self):
        loc = locale.getlocale()[0]
        if loc:
            v = loc.split('_', 1)
            self.locale = (v[0].lower(), v[1].upper()) if len(v) > 1 else (v[0].lower() if len(v) == 1 else None, None)
        else:
            self.locale = (None,) * 2

    def test_ayame(self):
        app = ayame.Ayame('')
        self.assertEqual(app._name, '')
        self.assertEqual(app._root, os.getcwd())

        app = ayame.Ayame(__name__)
        self.assertEqual(app._name, __name__)
        self.assertEqual(app._root, os.path.dirname(__file__))

    def test_request_empty(self):
        for m in ('GET', 'POST'):
            with self.subTest(method=m):
                environ = self.new_environ(method=m)
                request = ayame.Request(environ, {})
                self.assertIs(request.environ, environ)
                self.assertEqual(request.method, m)
                self.assertEqual(request.uri, {})
                self.assertEqual(request.query, {})
                self.assertEqual(request.form_data, {})
                self.assertIsNone(request.path)
                with self.assertRaises(ayame.AyameError):
                    request.session
                self.assertEqual(request.locale, self.locale)

    def test_request_get(self):
        query = f'{ayame.AYAME_PATH}=spam'
        for data, form in (
            (
                f'{ayame.AYAME_PATH}=eggs',
                None,
            ),
            (
                None,
                self.form_data((ayame.AYAME_PATH, 'eggs')),
            ),
        ):
            with self.subTest(data=bool(data), form=bool(form)):
                environ = self.new_environ(method='GET', query=query, data=data, form=form)
                request = ayame.Request(environ, {})
                self.assertIs(request.environ, environ)
                self.assertEqual(request.method, 'GET')
                self.assertEqual(request.uri, {})
                self.assertEqual(request.query, {ayame.AYAME_PATH: ['spam']})
                self.assertEqual(request.form_data, {})
                self.assertEqual(request.path, 'spam')
                with self.assertRaises(ayame.AyameError):
                    request.session
                self.assertEqual(request.locale, self.locale)

    def test_request_post(self):
        query = f'{ayame.AYAME_PATH}=spam'
        for data, form in (
            (
                f'{ayame.AYAME_PATH}=eggs',
                None,
            ),
            (
                None,
                self.form_data((ayame.AYAME_PATH, 'eggs'))
            ),
        ):
            with self.subTest(data=bool(data), form=bool(form)):
                environ = self.new_environ(method='POST', query=query, data=data, form=form)
                request = ayame.Request(environ, {})
                self.assertIs(request.environ, environ)
                self.assertEqual(request.method, 'POST')
                self.assertEqual(request.uri, {})
                self.assertEqual(request.query, {ayame.AYAME_PATH: ['spam']})
                self.assertEqual(request.form_data, {ayame.AYAME_PATH: ['eggs']})
                self.assertEqual(request.path, 'eggs')
                with self.assertRaises(ayame.AyameError):
                    request.session
                self.assertEqual(request.locale, self.locale)

    def test_request_post_file(self):
        data = self.form_data(
            ('text', 'spam'),
            ('file', ('a.txt', 'eggs\nham\ntoast\n', 'text/plain')),
        )
        environ = self.new_environ(method='POST', form=data)
        request = ayame.Request(environ, {})
        self.assertIs(request.environ, environ)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.uri, {})
        self.assertEqual(request.query, {})
        self.assertEqual(list(request.form_data), ['text', 'file'])
        self.assertIsNone(request.path)
        with self.assertRaises(ayame.AyameError):
            request.session
        self.assertEqual(request.locale, self.locale)

        with request:
            self.assertEqual(request.form_data['text'][0], 'spam')
            v = request.form_data['file'][0]
            self.assertEqual(v.name, 'file')
            self.assertEqual(v.filename, 'a.txt')
            self.assertEqual(v.read(), b'eggs\nham\ntoast\n')
            self.assertEqual(v.mimetype, 'text/plain')
            self.assertEqual(v.mimetype_params, {})
            self.assertFalse(v.closed)
        self.assertTrue(v.closed)

    def test_request_put(self):
        data = 'spam\neggs\nham\n'
        environ = self.new_environ(method='PUT', data=data)
        environ['CONTENT_TYPE'] = 'text/plain'
        request = ayame.Request(environ, {})
        self.assertIs(request.environ, environ)
        self.assertEqual(request.method, 'PUT')
        self.assertEqual(request.uri, {})
        self.assertEqual(request.query, {})
        self.assertEqual(request.form_data, {})
        self.assertIsNone(request.path)
        self.assertEqual(request.input.read(), b'spam\neggs\nham\n')
        with self.assertRaises(ayame.AyameError):
            request.session
        self.assertEqual(request.locale, self.locale)

    @unittest.mock.patch('locale.getlocale')
    def test_request_with_posix_locale(self, getlocale):
        getlocale.return_value = (None, None)

        environ = self.new_environ(method='GET')
        request = ayame.Request(environ, {})
        self.assertIs(request.environ, environ)
        self.assertEqual(request.method, 'GET')
        self.assertEqual(request.uri, {})
        self.assertEqual(request.query, {})
        self.assertEqual(request.form_data, {})
        self.assertIsNone(request.path)
        with self.assertRaises(ayame.AyameError):
            request.session
        self.assertEqual(request.locale, (None, None))

    def test_request_accept_language(self):
        for a, v in (
            (
                'en',
                ('en', None),
            ),
            (
                'en-us, en',
                ('en', 'US'),
            ),
        ):
            with self.subTest(accept_language=a):
                environ = self.new_environ(method='GET', accept=a)
                request = ayame.Request(environ, {})
                self.assertIs(request.environ, environ)
                self.assertEqual(request.method, 'GET')
                self.assertEqual(request.uri, {})
                self.assertEqual(request.query, {})
                self.assertEqual(request.form_data, {})
                self.assertIsNone(request.path)
                with self.assertRaises(ayame.AyameError):
                    request.session
                self.assertEqual(request.locale, v)


class SimpleAppTestCase(AyameTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.session_dir = tempfile.TemporaryDirectory(prefix='ayame-')

    @classmethod
    def tearDownClass(cls):
        cls.session_dir.cleanup()

    def setUp(self):
        self.app = ayame.Ayame(__name__)
        self.app.config['ayame.session.store'].path = self.session_dir.name
        self.app.config['ayame.session.sliding'] = False
        map = self.app.config['ayame.route.map']
        map.connect('/page', SimplePage)
        map.connect('/int', 0)
        map.connect('/class', object)
        map.connect('/redir', RedirectPage)

    def wsgi_call(self, environ):
        def start_response(status, headers, exc_info=None):
            wsgi.update(status=status, headers=headers, exc_info=exc_info)

        wsgi = {}
        content = self.app(environ, start_response)
        return wsgi['status'], wsgi['headers'], wsgi['exc_info'], list(content)

    def test_get_not_found(self):
        # GET / -> NotFound
        environ = self.new_environ('GET', '/')
        status, headers, exc_info, content = self.wsgi_call(environ)
        self.assertEqual(status, http.NotFound.status)
        self.assertIn(('Content-Type', 'text/html; charset=UTF-8'), headers)
        self.assertIsNone(exc_info)
        self.assertTrue(content)

    def test_get_page(self):
        # GET /page -> OK
        environ = self.new_environ('GET', '/page')
        status, headers, exc_info, content = self.wsgi_call(environ)
        html = self.format(SimplePage)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertIsNone(exc_info)
        self.assertEqual(content, [html])

    def test_get_int(self):
        # GET /int -> NotFound
        environ = self.new_environ('GET', '/int')
        status, headers, exc_info, content = self.wsgi_call(environ)
        self.assertEqual(status, http.NotFound.status)
        self.assertIn(('Content-Type', 'text/html; charset=UTF-8'), headers)
        self.assertIsNone(exc_info)
        self.assertTrue(content)

    def test_get_class(self):
        # GET /class -> NotFound
        environ = self.new_environ('GET', '/class')
        status, headers, exc_info, content = self.wsgi_call(environ)
        self.assertEqual(status, http.NotFound.status)
        self.assertIn(('Content-Type', 'text/html; charset=UTF-8'), headers)
        self.assertIsNone(exc_info)
        self.assertTrue(content)

    def test_get_redir_http_500(self):
        # GET /redir -> InternalServerError
        environ = self.new_environ('GET', '/redir')
        status, headers, exc_info, content = self.wsgi_call(environ)
        self.assertEqual(status, http.InternalServerError.status)
        self.assertEqual(headers, [])
        self.assertIsNotNone(exc_info)
        self.assertEqual(content, [])

    def test_get_redir_http_301(self):
        # GET /redir?type=permanent -> MovedPermanently
        query = 'type=permanent'
        environ = self.new_environ('GET', '/redir', query=query)
        status, headers, exc_info, content = self.wsgi_call(environ)
        self.assertEqual(status, http.MovedPermanently.status)
        self.assertIn(('Location', 'http://localhost/redir?p=1'), headers)
        self.assertIsNone(exc_info)
        self.assertTrue(content)

    def test_get_redir_http_302(self):
        # GET /redir?type=temporary -> Found
        query = 'type=temporary'
        environ = self.new_environ('GET', '/redir', query=query)
        status, headers, exc_info, content = self.wsgi_call(environ)
        self.assertEqual(status, http.Found.status)
        self.assertIn(('Location', 'http://localhost/redir?t=1'), headers)
        self.assertIsNone(exc_info)
        self.assertTrue(content)

    def test_get_redir(self):
        for m in (
            # in Latin
            'Salve Munde!',
            # in Japanese
            '\u3053\u3093\u306b\u3061\u306f\u4e16\u754c',
        ):
            with self.subTest(message=m):
                # GET /redir?message=... -> OK
                query = f'message={m}'
                environ = self.new_environ('GET', '/redir', query=query)
                status, headers, exc_info, content = self.wsgi_call(environ)
                html = self.format(SimplePage, message=m)
                self.assertEqual(status, http.OK.status)
                self.assertEqual(len(headers), 3)
                self.assertIn(('Content-Type', 'text/html; charset=UTF-8'), headers)
                self.assertIn(('Content-Length', str(len(html))), headers)
                self.assertIsNone(exc_info)
                self.assertEqual(content, [html])


class SimplePage(ayame.Page):

    html_t = """\
        <?xml version="1.0"?>
        {doctype}
        <html xmlns="{xhtml}">
          <head>
            <title>SimplePage</title>
          </head>
          <body>
            <p>{message}</p>
          </body>
        </html>
    """
    kwargs = {
        'message': 'Hello World!',
    }

    def __init__(self):
        super().__init__()
        self.add(SessionLabel('message', self.kwargs['message']))


class SessionLabel(basic.Label):

    def __init__(self, id, default):
        super().__init__(id, self.session.get(id, default))


class RedirectPage(ayame.Page):

    def on_render(self, element):
        if 'message' in self.request.query:
            self.session['message'] = self.request.query['message'][0]
            self.forward(SimplePage)
        elif 'permanent' in self.request.query.get('type', []):
            self.redirect(RedirectPage, {'p': 1}, permanent=True)
        elif 'temporary' in self.request.query.get('type', []):
            self.redirect(RedirectPage, {'t': 1})
        else:
            self.forward(RedirectPage)
