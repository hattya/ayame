#
# test_app
#
#   Copyright (c) 2011-2015 Akinori Hattori <hattya@gmail.com>
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

import locale
import os
import shutil
import tempfile

import ayame
from ayame import basic, http, uri
from base import AyameTestCase


class AppTestCase(AyameTestCase):

    def setup(self):
        super(AppTestCase, self).setup()
        self.locale = locale.getdefaultlocale()[0]
        if self.locale:
            v = self.locale.split('_', 1)
            self.locale = (v[0].lower(), v[1].upper()) if 1 < len(v) else (v[0].lower() if len(v) == 1 else None, None)
        else:
            self.locale = (None,) * 2
        self._getdefaultlocale = locale.getdefaultlocale

    def teardown(self):
        super(AppTestCase, self).teardown()
        locale.getdefaultlocale = self._getdefaultlocale

    def test_ayame(self):
        app = ayame.Ayame(None)
        self.assert_is_none(app._name)
        self.assert_equal(app._root, os.getcwd())

        app = ayame.Ayame(__name__)
        self.assert_equal(app._name, __name__)
        self.assert_equal(app._root, os.path.dirname(__file__))

    def test_request_empty(self):
        environ = self.new_environ(method='POST')
        request = ayame.Request(environ, {})
        self.assert_is(request.environ, environ)
        self.assert_equal(request.method, 'POST')
        self.assert_equal(request.uri, {})
        self.assert_equal(request.query, {})
        self.assert_equal(request.form_data, {})
        self.assert_is_none(request.path)
        with self.assert_raises(ayame.AyameError):
            request.session
        self.assert_equal(request.locale, self.locale)

    def test_request_post_empty(self):
        environ = self.new_environ(method='POST', data='')
        request = ayame.Request(environ, {})
        self.assert_is(request.environ, environ)
        self.assert_equal(request.method, 'POST')
        self.assert_equal(request.uri, {})
        self.assert_equal(request.query, {})
        self.assert_equal(request.form_data, {})
        self.assert_is_none(request.path)
        with self.assert_raises(ayame.AyameError):
            request.session
        self.assert_equal(request.locale, self.locale)

        environ = self.new_environ(method='POST', form='')
        request = ayame.Request(environ, {})
        self.assert_is(request.environ, environ)
        self.assert_equal(request.method, 'POST')
        self.assert_equal(request.uri, {})
        self.assert_equal(request.query, {})
        self.assert_equal(request.form_data, {})
        self.assert_is_none(request.path)
        with self.assert_raises(ayame.AyameError):
            request.session
        self.assert_equal(request.locale, self.locale)

    def test_request_get(self):
        query = '{path}=spam'
        data = '{path}=eggs'
        environ = self.new_environ(method='GET', query=query, data=data)
        request = ayame.Request(environ, {})
        self.assert_is(request.environ, environ)
        self.assert_equal(request.method, 'GET')
        self.assert_equal(request.uri, {})
        self.assert_equal(request.query, {ayame.AYAME_PATH: ['spam']})
        self.assert_equal(request.form_data, {})
        self.assert_equal(request.path, 'spam')
        with self.assert_raises(ayame.AyameError):
            request.session
        self.assert_equal(request.locale, self.locale)

    def test_request_post(self):
        query = '{path}=spam'
        data = '{path}=eggs'
        environ = self.new_environ(method='POST', query=query, data=data)
        request = ayame.Request(environ, {})
        self.assert_is(request.environ, environ)
        self.assert_equal(request.method, 'POST')
        self.assert_equal(request.uri, {})
        self.assert_equal(request.query, {ayame.AYAME_PATH: ['spam']})
        self.assert_equal(request.form_data, {ayame.AYAME_PATH: ['eggs']})
        self.assert_equal(request.path, 'eggs')
        with self.assert_raises(ayame.AyameError):
            request.session
        self.assert_equal(request.locale, self.locale)

        query = '{path}=spam'
        data = self.form_data(('{path}', 'eggs'))
        environ = self.new_environ(method='POST', query=query, form=data)
        request = ayame.Request(environ, {})
        self.assert_is(request.environ, environ)
        self.assert_equal(request.method, 'POST')
        self.assert_equal(request.uri, {})
        self.assert_equal(request.query, {ayame.AYAME_PATH: ['spam']})
        self.assert_equal(request.form_data, {ayame.AYAME_PATH: ['eggs']})
        self.assert_equal(request.path, 'eggs')
        with self.assert_raises(ayame.AyameError):
            request.session
        self.assert_equal(request.locale, self.locale)

    def test_request_put(self):
        data = 'spam\neggs\nham\n'
        environ = self.new_environ(method='PUT', data=data)
        environ['CONTENT_TYPE'] = 'text/plain'
        request = ayame.Request(environ, {})
        self.assert_is(request.environ, environ)
        self.assert_equal(request.method, 'PUT')
        self.assert_equal(request.uri, {})
        self.assert_equal(request.query, {})
        self.assert_equal(request.form_data, {})
        self.assert_is_none(request.path)
        self.assert_equal(request.input.read(), (b'spam\n'
                                                 b'eggs\n'
                                                 b'ham\n'))
        with self.assert_raises(ayame.AyameError):
            request.session
        self.assert_equal(request.locale, self.locale)

    def test_request_posix_locale(self):
        locale.getdefaultlocale = lambda: (None, None)

        environ = self.new_environ(method='GET')
        request = ayame.Request(environ, {})
        self.assert_is(request.environ, environ)
        self.assert_equal(request.method, 'GET')
        self.assert_equal(request.uri, {})
        self.assert_equal(request.query, {})
        self.assert_equal(request.form_data, {})
        self.assert_is_none(request.path)
        with self.assert_raises(ayame.AyameError):
            request.session
        self.assert_equal(request.locale, (None, None))

    def test_request_accept_language_en(self):
        environ = self.new_environ(method='GET', accept='en')
        request = ayame.Request(environ, {})
        self.assert_is(request.environ, environ)
        self.assert_equal(request.method, 'GET')
        self.assert_equal(request.uri, {})
        self.assert_equal(request.query, {})
        self.assert_equal(request.form_data, {})
        self.assert_is_none(request.path)
        with self.assert_raises(ayame.AyameError):
            request.session
        self.assert_equal(request.locale, ('en', None))

    def test_request_accept_language_en_us(self):
        environ = self.new_environ(method='GET', accept='en-us, en')
        request = ayame.Request(environ, {})
        self.assert_is(request.environ, environ)
        self.assert_equal(request.method, 'GET')
        self.assert_equal(request.uri, {})
        self.assert_equal(request.query, {})
        self.assert_equal(request.form_data, {})
        self.assert_is_none(request.path)
        with self.assert_raises(ayame.AyameError):
            request.session
        self.assert_equal(request.locale, ('en', 'US'))


class SimpleAppTestCase(AyameTestCase):

    @classmethod
    def setup_class(cls):
        cls.session_dir = tempfile.mkdtemp()

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.session_dir)

    def setup(self):
        super(SimpleAppTestCase, self).setup()
        self.app = ayame.Ayame(__name__)
        self.app.config['ayame.session.store'].path = self.session_dir
        map = self.app.config['ayame.route.map']
        map.connect('/page', SimplePage)
        map.connect('/int', 0)
        map.connect('/class', object)
        map.connect('/redir', RedirectPage)

    def new_environ(self, method='GET', path='', query=''):
        return super(SimpleAppTestCase, self).new_environ(method=method,
                                                          path=path,
                                                          query=query)

    def wsgi_call(self, environ):
        def start_response(status, headers, exc_info=None):
            wsgi.update(status=status, headers=headers, exc_info=exc_info)

        wsgi = {}
        content = self.app(environ, start_response)
        content = list(content)
        if hasattr(content, 'close'):
            content.close()
        return wsgi['status'], wsgi['headers'], wsgi['exc_info'], content

    def test_get_page(self):
        # GET /page -> OK
        environ = self.new_environ('GET', '/page')
        status, headers, exc_info, content = self.wsgi_call(environ)
        html = self.format(SimplePage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_is_none(exc_info)
        self.assert_equal(content, [html])

        # GET /page?{query in EUC-JP} -> OK
        query = uri.quote('\u3044\u308d\u306f', encoding='euc-jp')
        environ = self.new_environ('GET', '/page', query=query)
        status, headers, exc_info, content = self.wsgi_call(environ)
        html = self.format(SimplePage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_is_none(exc_info)
        self.assert_equal(content, [html])

    def test_get_int(self):
        # GET /int -> NotFound
        environ = self.new_environ('GET', '/int')
        status, headers, exc_info, content = self.wsgi_call(environ)
        self.assert_equal(status, http.NotFound.status)
        self.assert_in(('Content-Type', 'text/html; charset=UTF-8'), headers)
        self.assert_is_none(exc_info)
        self.assert_true(content)

    def test_get_class(self):
        # GET /class -> NotFound
        environ = self.new_environ('GET', '/class')
        status, headers, exc_info, content = self.wsgi_call(environ)
        self.assert_equal(status, http.NotFound.status)
        self.assert_in(('Content-Type', 'text/html; charset=UTF-8'), headers)
        self.assert_is_none(exc_info)
        self.assert_true(content)

    def test_get_redir_http_500(self):
        # GET /redir -> InternalServerError
        environ = self.new_environ('GET', '/redir')
        status, headers, exc_info, content = self.wsgi_call(environ)
        self.assert_equal(status, http.InternalServerError.status)
        self.assert_equal(headers, [])
        self.assert_is_not_none(exc_info)
        self.assert_equal(content, [])

    def test_get_redir_http_301(self):
        # GET /redir?type=permanent -> MovedPermanently
        query = 'type=permanent'
        environ = self.new_environ('GET', '/redir', query=query)
        status, headers, exc_info, content = self.wsgi_call(environ)
        self.assert_equal(status, http.MovedPermanently.status)
        self.assert_in(('Location', 'http://localhost/redir?p=1'), headers)
        self.assert_is_none(exc_info)
        self.assert_true(content)

    def test_get_redir_http_302(self):
        # GET /redir?type=temporary -> Found
        query = 'type=temporary'
        environ = self.new_environ('GET', '/redir', query=query)
        status, headers, exc_info, content = self.wsgi_call(environ)
        self.assert_equal(status, http.Found.status)
        self.assert_in(('Location', 'http://localhost/redir?t=1'), headers)
        self.assert_is_none(exc_info)
        self.assert_true(content)

    def test_get_redir(self):
        # GET /redir?message=Salve+Munde! -> OK
        query = 'message=Salve Munde!'
        environ = self.new_environ('GET', '/redir', query=query)
        status, headers, exc_info, content = self.wsgi_call(environ)
        html = self.format(SimplePage, message='Salve Munde!')
        self.assert_equal(status, http.OK.status)
        self.assert_equal(len(headers), 3)
        self.assert_in(('Content-Type', 'text/html; charset=UTF-8'), headers)
        self.assert_in(('Content-Length', str(len(html))), headers)
        self.assert_is_none(exc_info)
        self.assert_equal(content, [html])


class SimplePage(ayame.Page):

    html_t = u"""\
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
        'message': 'Hello World!'
    }

    def __init__(self):
        super(SimplePage, self).__init__()
        self.add(SessionLabel('message', self.kwargs['message']))


class SessionLabel(basic.Label):

    def __init__(self, id, default):
        super(SessionLabel, self).__init__(id, self.session.get(id, default))


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
