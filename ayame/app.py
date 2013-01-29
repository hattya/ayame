#
# ayame.app
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

import datetime
import locale
import os
import sys

import beaker.middleware

import ayame.converter
import ayame.core
from ayame.exception import AyameError, _Redirect
import ayame.http
import ayame.i18n
import ayame.local
import ayame.markup
import ayame.page
import ayame.route
import ayame.uri


__all__ = ['Ayame', 'Request']


class Ayame(object):

    def __init__(self, name):
        self._name = name
        try:
            module = sys.modules[name]
            self._root = os.path.abspath(os.path.dirname(module.__file__))
        except (AttributeError, KeyError):
            self._root = os.getcwd()
        session_dir = os.path.join(self._root, 'session')
        self.config = {
            'ayame.converter.registry': ayame.converter.ConverterRegistry(),
            'ayame.i18n.localizer': ayame.i18n.Localizer(),
            'ayame.markup.encoding': 'utf-8',
            'ayame.markup.loader': ayame.markup.MarkupLoader,
            'ayame.markup.pretty': False,
            'ayame.markup.renderer': ayame.markup.MarkupRenderer,
            'ayame.markup.separator': '.',
            'ayame.max.redirect': 7,
            'ayame.page.http': ayame.page.HTTPStatusPage,
            'ayame.request': Request,
            'ayame.route.map': ayame.route.Map(),
            'beaker.session.type': 'file',
            'beaker.session.data_dir': os.path.join(session_dir, 'data'),
            'beaker.session.lock_dir': os.path.join(session_dir, 'lock'),
            'beaker.session.cookie_expires': datetime.timedelta(31),
            'beaker.session.key': None,
            'beaker.session.secret': None}

    @property
    def context(self):
        return ayame.local.context()

    @property
    def environ(self):
        return self.context.environ

    @property
    def request(self):
        return self.context.request

    @property
    def session(self):
        return self.context.environ['ayame.session']

    @property
    def _router(self):
        return self.context._router

    def new(self):
        app = beaker.middleware.SessionMiddleware(self, self.config,
                                                  'ayame.session')
        return app

    def __call__(self, environ, start_response):
        try:
            context = ayame.local.push(self, environ)
            context._router = self.config['ayame.route.map'].bind(environ)
            # dispatch
            object, values = context._router.match()
            context.request = self.config['ayame.request'](environ, values)
            for _ in xrange(self.config['ayame.max.redirect']):
                try:
                    status, headers, content = self.handle_request(object)
                except _Redirect as r:
                    if r.args[3] == _Redirect.PERMANENT:
                        raise ayame.http.MovedPermanently(
                            ayame.uri.application_uri(environ) +
                            self.uri_for(*r.args[:3], relative=True)[1:])
                    elif r.args[3] != _Redirect.INTERNAL:
                        raise ayame.http.Found(
                            ayame.uri.application_uri(environ) +
                            self.uri_for(*r.args[:3], relative=True)[1:])
                    object = r.args[0]
                    context.request.path = None
                    continue
                break
            else:
                raise AyameError('reached to the maximum number of internal '
                                 'redirects')
            exc_info = None
        except Exception as e:
            status, headers, exc_info, content = self.handle_error(e)
        finally:
            ayame.local.pop()

        start_response(status, headers, exc_info)
        return content

    def handle_request(self, object):
        if isinstance(object, type):
            if issubclass(object, ayame.core.Page):
                return object().render()
        raise ayame.http.NotFound(ayame.uri.request_path(self.environ))

    def handle_error(self, error):
        if isinstance(error, ayame.http.HTTPStatus):
            page = self.config['ayame.page.http'](error)
            status, headers, content = page.render()
            exc_info = None
        else:
            status = ayame.http.InternalServerError.status
            headers = []
            content = []
            exc_info = sys.exc_info()
        return status, headers, exc_info, content

    def forward(self, object, values=None, anchor=None):
        raise _Redirect(object, values, anchor, _Redirect.INTERNAL)

    def redirect(self, object, values=None, anchor=None, permanent=False):
        raise _Redirect(
            object, values, anchor,
            _Redirect.PERMANENT if permanent else _Redirect.TEMPORARY)

    def uri_for(self, *args, **kwargs):
        return self._router.build(*args, **kwargs)


class Request(object):

    __slots__ = ('environ', 'method', 'uri', 'query', 'form_data', 'path',
                 'locale')

    def __init__(self, environ, values):
        self.environ = environ
        self.method = environ['REQUEST_METHOD']
        self.uri = values
        self.query = ayame.uri.parse_qs(environ)
        self.form_data = ayame.http.parse_form_data(environ)
        # retrieve ayame:path
        if self.method == 'GET':
            self.path = self.query.get(ayame.core.AYAME_PATH)
        elif self.method == 'POST':
            self.path = self.form_data.get(ayame.core.AYAME_PATH)
        else:
            self.path = None
        if self.path:
            self.path = self.path[0]
        self.locale = self._parse_locales(environ)

    def _parse_locales(self, environ):
        values = ayame.http.parse_accept(environ.get('HTTP_ACCEPT_LANGUAGE'))
        if values:
            value = values[0][0]
            sep = '-'
        else:
            value = locale.getdefaultlocale()[0]
            sep = '_'
        if value:
            v = value.split(sep, 1)
            if 1 < len(v):
                return (v[0].lower(), v[1].upper())
            return (v[0].lower(), None)
        return (None,) * 2

    @property
    def input(self):
        return self.environ['wsgi.input']

    @property
    def session(self):
        return self.environ['ayame.session']
