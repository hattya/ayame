#
# ayame.app
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
import sys

from werkzeug.contrib.sessions import FilesystemSessionStore, SessionMiddleware

from . import _compat as five
from . import (converter, core, http, i18n, local, markup, page, res, route,
               uri, util)
from .exception import AyameError, _Redirect


__all__ = ['Ayame', 'Request']


class Ayame(object):

    def __init__(self, name):
        self._name = name
        try:
            self._root = os.path.abspath(os.path.dirname(sys.modules[name].__file__))
        except (AttributeError, KeyError):
            self._root = os.getcwd()
        session_dir = os.path.join(self._root, 'session')
        self.config = {
            'ayame.converter.registry': converter.ConverterRegistry(),
            'ayame.i18n.cache': util.LRUCache(64),
            'ayame.i18n.localizer': i18n.Localizer(),
            'ayame.markup.cache': util.LRUCache(64),
            'ayame.markup.encoding': 'utf-8',
            'ayame.markup.loader': markup.MarkupLoader,
            'ayame.markup.pretty': False,
            'ayame.markup.renderer': markup.MarkupRenderer,
            'ayame.markup.separator': '.',
            'ayame.max.redirect': 7,
            'ayame.page.http': page.HTTPStatusPage,
            'ayame.request': Request,
            'ayame.resource.loader': res.ResourceLoader(),
            'ayame.route.map': route.Map(),
            'ayame.session.store': FilesystemSessionStore(session_dir, 'ayame_%s.sess'),
            'ayame.session.name': 'session_id',
            'ayame.session.expires': None,
            'ayame.session.max_age': None,
            'ayame.session.domain': None,
            'ayame.session.path': '/',
            'ayame.session.secure': False,
            'ayame.session.httponly': True,
        }

    @property
    def context(self):
        return local.context()

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
        app = SessionMiddleware(self, self.config['ayame.session.store'],
                                self.config['ayame.session.name'],
                                self.config['ayame.session.max_age'],
                                self.config['ayame.session.expires'],
                                self.config['ayame.session.path'],
                                self.config['ayame.session.domain'],
                                self.config['ayame.session.secure'],
                                self.config['ayame.session.httponly'],
                                'ayame.session')
        return app

    def __call__(self, environ, start_response):
        try:
            ctx = local.push(self, environ)
            ctx._router = self.config['ayame.route.map'].bind(environ)
            # dispatch
            o, values = ctx._router.match()
            ctx.request = self.config['ayame.request'](environ, values)
            for _ in five.range(self.config['ayame.max.redirect']):
                try:
                    status, headers, content = self.handle_request(o)
                except _Redirect as r:
                    if r.args[3] == _Redirect.PERMANENT:
                        raise http.MovedPermanently(uri.application_uri(environ) +
                                                    self.uri_for(*r.args[:3], relative=True)[1:])
                    elif r.args[3] != _Redirect.INTERNAL:
                        raise http.Found(uri.application_uri(environ) +
                                         self.uri_for(*r.args[:3], relative=True)[1:])
                    o = r.args[0]
                    ctx.request.path = None
                    continue
                break
            else:
                raise AyameError('reached to the maximum number of internal redirects')
            exc_info = None
        except Exception as e:
            status, headers, exc_info, content = self.handle_error(e)
        finally:
            local.pop()

        start_response(status, headers, exc_info)
        return content

    def handle_request(self, object):
        if isinstance(object, type):
            if issubclass(object, core.Page):
                object = object()
            else:
                # type is callable, so it might cause unexpected error
                object = None
        if callable(object):
            return object()
        raise http.NotFound(uri.request_path(self.environ))

    def handle_error(self, error):
        if isinstance(error, http.HTTPStatus):
            page = self.config['ayame.page.http'](error)
            status, headers, content = page()
            exc_info = None
        else:
            status, headers, content = http.InternalServerError.status, [], []
            exc_info = sys.exc_info()
        return status, headers, exc_info, content

    def forward(self, object, values=None, anchor=None):
        raise _Redirect(object, values, anchor, _Redirect.INTERNAL)

    def redirect(self, object, values=None, anchor=None, permanent=False):
        raise _Redirect(object, values, anchor, _Redirect.PERMANENT if permanent else _Redirect.TEMPORARY)

    def uri_for(self, *args, **kwargs):
        return self._router.build(*args, **kwargs)


class Request(object):

    __slots__ = ('environ', 'method', 'uri', 'query', 'form_data', 'path',
                 'locale')

    def __init__(self, environ, values):
        self.environ = environ
        self.method = environ['REQUEST_METHOD']
        self.uri = values
        self.query = uri.parse_qs(environ)
        self.form_data = http.parse_form_data(environ)
        # retrieve ayame:path
        if self.method == 'GET':
            self.path = self.query.get(core.AYAME_PATH)
        elif self.method == 'POST':
            self.path = self.form_data.get(core.AYAME_PATH)
        else:
            self.path = None
        if self.path:
            self.path = self.path[0]
        self.locale = self._parse_locales(environ)

    def _parse_locales(self, environ):
        values = http.parse_accept(environ.get('HTTP_ACCEPT_LANGUAGE'))
        if values:
            v = values[0][0]
            sep = '-'
        else:
            v = locale.getdefaultlocale()[0]
            sep = '_'
        if v:
            v = v.split(sep, 1)
            return (v[0].lower(), v[1].upper() if 1 < len(v) else None)
        return (None,) * 2

    @property
    def input(self):
        return self.environ['wsgi.input']

    @property
    def session(self):
        return self.environ['ayame.session']
