#
# test_app
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
import locale
import os
import wsgiref.util

from nose.tools import eq_, ok_

from ayame import basic, core, http, markup, uri
from ayame import app as _app


def wsgi_call(application, **kwargs):
    def start_response(status, headers, exc_info=None):
        wsgi.update(status=status, headers=headers, exc_info=exc_info)

    environ = dict(kwargs)
    wsgiref.util.setup_testing_defaults(environ)
    wsgi = {}
    content = application(environ, start_response)
    return wsgi['status'], wsgi['headers'], wsgi['exc_info'], content


def test_simple_app():
    class SimplePage(core.Page):
        def __init__(self):
            super(SimplePage, self).__init__()
            self.add(SessionLabel('message', u'Hello World!'))

    class SessionLabel(basic.Label):
        def __init__(self, id, default):
            super(SessionLabel, self).__init__(id,
                                               self.session.get(id, default))

    class RedirectPage(core.Page):
        def on_render(self, element):
            if 'message' in self.request.query:
                self.session['message'] = self.request.query['message'][0]
                self.forward(SimplePage)
            elif 'permanent' in self.request.query.get('type', []):
                self.redirect(RedirectPage, {'p': 1}, permanent=True)
            elif 'temporary' in self.request.query.get('type', []):
                self.redirect(RedirectPage, {'t': 1})
            self.forward(RedirectPage)

    app = _app.Ayame(__name__)
    eq_(app._name, __name__)
    eq_(app._root, os.path.dirname(__file__))

    map = app.config['ayame.route.map']
    map.connect('/page', SimplePage)
    map.connect('/int', 0)
    map.connect('/redir', RedirectPage)

    app = app.new()

    # GET /page -> OK
    xhtml = ('<?xml version="1.0"?>\n'
             '{doctype}\n'
             '<html xmlns="{xhtml}">\n'
             '  <head>\n'
             '    <title>SimplePage</title>\n'
             '  </head>\n'
             '  <body>\n'
             '    <p>Hello World!</p>\n'
             '  </body>\n'
             '</html>\n').format(doctype=markup.XHTML1_STRICT,
                                 xhtml=markup.XHTML_NS)
    xhtml = xhtml.encode('utf-8')
    status, headers, exc_info, content = wsgi_call(app,
                                                   REQUEST_METHOD='GET',
                                                   PATH_INFO='/page')
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(exc_info, None)
    eq_(content, xhtml)

    # GET /page?{query in EUC-JP} -> OK
    query = uri.quote('\u3044\u308d\u306f', encoding='euc-jp')
    status, headers, exc_info, content = wsgi_call(app,
                                                   REQUEST_METHOD='GET',
                                                   PATH_INFO='/page',
                                                   QUERY_STRING=query)
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(exc_info, None)
    eq_(content, xhtml)

    # GET /int -> NotFound
    status, headers, exc_info, content = wsgi_call(app,
                                                   REQUEST_METHOD='GET',
                                                   PATH_INFO='/int')
    eq_(status, http.NotFound.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', '916')])
    eq_(exc_info, None)
    ok_(content)

    # GET /redir -> InternalServerError
    status, headers, exc_info, content = wsgi_call(app,
                                                   REQUEST_METHOD='GET',
                                                   PATH_INFO='/redir')
    eq_(status, http.InternalServerError.status)
    eq_(headers, [])
    ok_(exc_info)
    eq_(content, [])

    # GET /redir?type=permanent -> MovedPermanently
    query = uri.quote_plus('type=permanent')
    status, headers, exc_info, content = wsgi_call(app,
                                                   REQUEST_METHOD='GET',
                                                   PATH_INFO='/redir',
                                                   QUERY_STRING=query)
    eq_(status, http.MovedPermanently.status)
    ok_(('Location', 'http://127.0.0.1/redir?p=1') in headers)
    eq_(exc_info, None)
    ok_(content)

    # GET /redir?type=temporary -> Found
    query = uri.quote_plus('type=temporary')
    status, headers, exc_info, content = wsgi_call(app,
                                                   REQUEST_METHOD='GET',
                                                   PATH_INFO='/redir',
                                                   QUERY_STRING=query)
    eq_(status, http.Found.status)
    ok_(('Location', 'http://127.0.0.1/redir?t=1') in headers)
    eq_(exc_info, None)
    ok_(content)

    # GET /redir?message=Hallo+Welt! -> OK
    xhtml = xhtml.replace(b'Hello World!', b'Hallo Welt!')
    query = uri.quote_plus('message=Hallo Welt!')
    status, headers, exc_info, content = wsgi_call(app,
                                                   REQUEST_METHOD='GET',
                                                   PATH_INFO='/redir',
                                                   QUERY_STRING=query)
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(exc_info, None)
    eq_(content, xhtml)


def test_failsafe():
    app = _app.Ayame(None)
    eq_(app._root, os.getcwd())


def test_request():
    default_locale = locale.getdefaultlocale()[0]
    if default_locale:
        v = default_locale.split('_', 1)
        if 1 < len(v):
            default_locale = (v[0].lower(), v[1].upper())
        else:
            default_locale = (v[0].lower() if len(v) == 1 else None, None)
    else:
        default_locale = (None,) * 2

    # QUERY_STRING and CONTENT_TYPE are empty
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'POST',
               'CONTENT_LENGTH': '0',
               'ayame.session': {}}
    request = _app.Request(environ, {})
    eq_(request.environ, environ)
    eq_(request.method, 'POST')
    eq_(request.uri, {})
    eq_(request.query, {})
    eq_(request.form_data, {})
    eq_(request.path, None)
    eq_(request.session, {})
    eq_(request.locale, default_locale)

    # form data is empty
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'POST',
               'CONTENT_TYPE': 'application/x-www-form-urlencoded',
               'CONTENT_LENGTH': '0',
               'ayame.session': {}}
    request = _app.Request(environ, {})
    eq_(request.environ, environ)
    eq_(request.method, 'POST')
    eq_(request.uri, {})
    eq_(request.query, {})
    eq_(request.form_data, {})
    eq_(request.path, None)
    eq_(request.session, {})
    eq_(request.locale, default_locale)

    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'POST',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.core',
               'CONTENT_LENGTH': '0',
               'ayame.session': {}}
    request = _app.Request(environ, {})
    eq_(request.environ, environ)
    eq_(request.method, 'POST')
    eq_(request.uri, {})
    eq_(request.query, {})
    eq_(request.form_data, {})
    eq_(request.path, None)
    eq_(request.session, {})
    eq_(request.locale, default_locale)

    # GET
    query = '{}=spam'.format(core.AYAME_PATH)
    data = '{}=eggs'.format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'GET',
               'QUERY_STRING': uri.quote(query),
               'CONTENT_TYPE': 'application/x-www-form-urlencoded',
               'CONTENT_LENGTH': str(len(data)),
               'ayame.session': {}}
    request = _app.Request(environ, {})
    eq_(request.environ, environ)
    eq_(request.method, 'GET')
    eq_(request.uri, {})
    eq_(request.query, {core.AYAME_PATH: ['spam']})
    eq_(request.form_data, {})
    eq_(request.path, 'spam')
    eq_(request.session, {})
    eq_(request.locale, default_locale)

    # POST
    query = '{}=spam'.format(core.AYAME_PATH)
    data = '{}=eggs'.format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'QUERY_STRING': uri.quote(query),
               'CONTENT_TYPE': 'application/x-www-form-urlencoded',
               'CONTENT_LENGTH': str(len(data)),
               'ayame.session': {}}
    request = _app.Request(environ, {})
    eq_(request.environ, environ)
    eq_(request.method, 'POST')
    eq_(request.uri, {})
    eq_(request.query, {core.AYAME_PATH: ['spam']})
    eq_(request.form_data, {core.AYAME_PATH: ['eggs']})
    eq_(request.path, 'eggs')
    eq_(request.session, {})
    eq_(request.locale, default_locale)

    query = '{}=spam'.format(core.AYAME_PATH)
    data = ('--ayame.core\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'eggs\r\n'
            '--ayame.core--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'QUERY_STRING': uri.quote(query),
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.core',
               'CONTENT_LENGTH': str(len(data)),
               'ayame.session': {}}
    request = _app.Request(environ, {})
    eq_(request.environ, environ)
    eq_(request.method, 'POST')
    eq_(request.uri, {})
    eq_(request.query, {core.AYAME_PATH: ['spam']})
    eq_(request.form_data, {core.AYAME_PATH: ['eggs']})
    eq_(request.path, 'eggs')
    eq_(request.session, {})
    eq_(request.locale, default_locale)

    # PUT
    data = ('spam\n'
            'eggs\n'
            'ham\n')
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'PUT',
               'QUERY_STRING': '',
               'CONTENT_TYPE': 'text/plain',
               'CONTENT_LENGTH': str(len(data)),
               'ayame.session': {}}
    request = _app.Request(environ, {})
    eq_(request.environ, environ)
    eq_(request.method, 'PUT')
    eq_(request.uri, {})
    eq_(request.query, {})
    eq_(request.form_data, {})
    eq_(request.path, None)
    eq_(request.input.read(), (b'spam\n'
                               b'eggs\n'
                               b'ham\n'))
    eq_(request.session, {})
    eq_(request.locale, default_locale)

    # Accept-Language
    environ = {'wsgi.input': io.BytesIO(),
               'HTTP_ACCEPT_LANGUAGE': 'en-us, en',
               'REQUEST_METHOD': 'GET',
               'QUERY_STRING': '',
               'ayame.session': {}}
    request = _app.Request(environ, {})
    eq_(request.environ, environ)
    eq_(request.method, 'GET')
    eq_(request.uri, {})
    eq_(request.query, {})
    eq_(request.form_data, {})
    eq_(request.path, None)
    eq_(request.session, {})
    eq_(request.locale, ('en', 'US'))

    environ = {'wsgi.input': io.BytesIO(),
               'HTTP_ACCEPT_LANGUAGE': 'en',
               'REQUEST_METHOD': 'GET',
               'QUERY_STRING': '',
               'ayame.session': {}}
    request = _app.Request(environ, {})
    eq_(request.environ, environ)
    eq_(request.method, 'GET')
    eq_(request.uri, {})
    eq_(request.query, {})
    eq_(request.form_data, {})
    eq_(request.path, None)
    eq_(request.session, {})
    eq_(request.locale, ('en', None))

    getdefaultlocale = locale.getdefaultlocale
    locale.getdefaultlocale = lambda: (None, None)
    try:
        environ = {'wsgi.input': io.BytesIO(),
                   'REQUEST_METHOD': 'GET',
                   'QUERY_STRING': '',
                   'ayame.session': {}}
        request = _app.Request(environ, {})
        eq_(request.environ, environ)
        eq_(request.method, 'GET')
        eq_(request.uri, {})
        eq_(request.query, {})
        eq_(request.form_data, {})
        eq_(request.path, None)
        eq_(request.session, {})
        eq_(request.locale, (None, None))
    finally:
        locale.getdefaultlocale = getdefaultlocale
