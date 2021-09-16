#
# test_app
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import locale
import os
import tempfile
import textwrap

import ayame
from ayame import basic, http, uri
from base import AyameTestCase


class AppTestCase(AyameTestCase):

    def setUp(self):
        self.locale = locale.getdefaultlocale()[0]
        if self.locale:
            v = self.locale.split('_', 1)
            self.locale = (v[0].lower(), v[1].upper()) if len(v) > 1 else (v[0].lower() if len(v) == 1 else None, None)
        else:
            self.locale = (None,) * 2
        self._getdefaultlocale = locale.getdefaultlocale

    def tearDown(self):
        locale.getdefaultlocale = self._getdefaultlocale

    def test_ayame(self):
        app = ayame.Ayame(None)
        self.assertIsNone(app._name)
        self.assertEqual(app._root, os.getcwd())

        app = ayame.Ayame(__name__)
        self.assertEqual(app._name, __name__)
        self.assertEqual(app._root, os.path.dirname(__file__))

    def test_request_empty(self):
        environ = self.new_environ(method='POST')
        request = ayame.Request(environ, {})
        self.assertIs(request.environ, environ)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.uri, {})
        self.assertEqual(request.query, {})
        self.assertEqual(request.form_data, {})
        self.assertIsNone(request.path)
        with self.assertRaises(ayame.AyameError):
            request.session
        self.assertEqual(request.locale, self.locale)

    def test_request_post_empty(self):
        environ = self.new_environ(method='POST', data='')
        request = ayame.Request(environ, {})
        self.assertIs(request.environ, environ)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.uri, {})
        self.assertEqual(request.query, {})
        self.assertEqual(request.form_data, {})
        self.assertIsNone(request.path)
        with self.assertRaises(ayame.AyameError):
            request.session
        self.assertEqual(request.locale, self.locale)

        environ = self.new_environ(method='POST', form='')
        request = ayame.Request(environ, {})
        self.assertIs(request.environ, environ)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.uri, {})
        self.assertEqual(request.query, {})
        self.assertEqual(request.form_data, {})
        self.assertIsNone(request.path)
        with self.assertRaises(ayame.AyameError):
            request.session
        self.assertEqual(request.locale, self.locale)

    def test_request_get(self):
        query = '{path}=spam'
        data = '{path}=eggs'
        environ = self.new_environ(method='GET', query=query, data=data)
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
        query = '{path}=spam'
        data = '{path}=eggs'
        environ = self.new_environ(method='POST', query=query, data=data)
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

        query = '{path}=spam'
        data = self.form_data(('{path}', 'eggs'))
        environ = self.new_environ(method='POST', query=query, form=data)
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

    def test_request_posix_locale(self):
        locale.getdefaultlocale = lambda: (None, None)

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

    def test_request_accept_language_en(self):
        environ = self.new_environ(method='GET', accept='en')
        request = ayame.Request(environ, {})
        self.assertIs(request.environ, environ)
        self.assertEqual(request.method, 'GET')
        self.assertEqual(request.uri, {})
        self.assertEqual(request.query, {})
        self.assertEqual(request.form_data, {})
        self.assertIsNone(request.path)
        with self.assertRaises(ayame.AyameError):
            request.session
        self.assertEqual(request.locale, ('en', None))

    def test_request_accept_language_en_us(self):
        environ = self.new_environ(method='GET', accept='en-us, en')
        request = ayame.Request(environ, {})
        self.assertIs(request.environ, environ)
        self.assertEqual(request.method, 'GET')
        self.assertEqual(request.uri, {})
        self.assertEqual(request.query, {})
        self.assertEqual(request.form_data, {})
        self.assertIsNone(request.path)
        with self.assertRaises(ayame.AyameError):
            request.session
        self.assertEqual(request.locale, ('en', 'US'))


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
        map = self.app.config['ayame.route.map']
        map.connect('/page', SimplePage)
        map.connect('/int', 0)
        map.connect('/class', object)
        map.connect('/redir', RedirectPage)

    def new_environ(self, method='GET', path='', query=''):
        return super().new_environ(method=method,
                                   path=path,
                                   query=query)

    def wsgi_call(self, environ):
        def start_response(status, headers, exc_info=None):
            wsgi.update(status=status, headers=headers, exc_info=exc_info)

        wsgi = {}
        content = self.app(environ, start_response)
        return wsgi['status'], wsgi['headers'], wsgi['exc_info'], list(content)

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

        # GET /page?{query in EUC-JP} -> OK
        query = uri.quote('\u3044\u308d\u306f', encoding='euc-jp')
        environ = self.new_environ('GET', '/page', query=query)
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
        # GET /redir?message=Salve+Munde! -> OK
        query = 'message=Salve Munde!'
        environ = self.new_environ('GET', '/redir', query=query)
        status, headers, exc_info, content = self.wsgi_call(environ)
        html = self.format(SimplePage, message='Salve Munde!')
        self.assertEqual(status, http.OK.status)
        self.assertEqual(len(headers), 3)
        self.assertIn(('Content-Type', 'text/html; charset=UTF-8'), headers)
        self.assertIn(('Content-Length', str(len(html))), headers)
        self.assertIsNone(exc_info)
        self.assertEqual(content, [html])


class SimplePage(ayame.Page):

    html_t = textwrap.dedent("""\
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
    """)
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
