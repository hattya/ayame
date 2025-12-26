#
# ayame.app
#
#   Copyright (c) 2011-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import locale
import os
import sys

import werkzeug.datastructures

from . import (converter, core, http, i18n, local, markup, page, res, route,
               session, uri, util)
from .exception import AyameError, _Redirect


__all__ = ['Ayame', 'Request']


class Ayame:

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
            'ayame.session.store': session.FileSystemSessionStore(session_dir, 'ayame_%s.sess'),
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
        return self.context.session

    @property
    def _router(self):
        return self.context._router

    def __call__(self, environ, start_response):
        ctx = local.push(self, environ)
        ctx._router = self.config['ayame.route.map'].bind(environ)
        try:
            o, values = ctx._router.match()
            ctx.request = self.config['ayame.request'](environ, values)
            ctx.session = session.get(self, environ)
            for _ in range(self.config['ayame.max.redirect']):
                try:
                    status, headers, content = self.handle_request(o)
                except _Redirect as r:
                    if r.args[3] == _Redirect.PERMANENT:
                        raise http.MovedPermanently(uri.application_uri(environ)
                                                    + self.uri_for(*r.args[:3], relative=True)[1:])
                    elif r.args[3] != _Redirect.INTERNAL:
                        raise http.Found(uri.application_uri(environ)
                                         + self.uri_for(*r.args[:3], relative=True)[1:])
                    o = r.args[0]
                    ctx.request.path = None
                    continue
                break
            else:
                raise AyameError('reached to the maximum number of internal redirects')
            exc_info = None
            if set_cookie := session.save(self, ctx.session):
                headers.append(set_cookie)
        except Exception as e:
            ctx.request = self.config['ayame.request'](environ, {})
            status, headers, exc_info, content = self.handle_error(e)
        finally:
            ctx.request.close()
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


class Request:

    __slots__ = ('environ', 'method', 'uri', 'query', 'form_data', 'path',
                 'locale')

    def __init__(self, environ, values):
        self.environ = environ
        self.method = environ['REQUEST_METHOD']
        self.uri = values
        self.query = uri.parse_qs(environ)
        self.form_data = http.parse_form_data(environ)
        # retrieve ayame:path
        self.path = None
        if self.method == 'GET':
            if query := self.query.get(core.AYAME_PATH):
                self.path = query[0]
        elif self.method == 'POST':
            if ((data := self.form_data.get(core.AYAME_PATH))
                and isinstance(data[0], str)):
                self.path = data[0]
        self.locale = self._parse_locales(environ)

    def _parse_locales(self, environ):
        if values := http.parse_accept(environ.get('HTTP_ACCEPT_LANGUAGE')):
            loc = values[0][0]
            sep = '-'
        else:
            loc = locale.getlocale()[0]
            sep = '_'
        if loc:
            v = loc.split(sep, 1)
            return v[0].lower(), v[1].upper() if len(v) > 1 else None
        return (None, None)

    @property
    def input(self):
        return self.environ['wsgi.input']

    @property
    def session(self):
        return local.context().session

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def close(self):
        for data in self.form_data.values():
            for v in data:
                if isinstance(v, werkzeug.datastructures.FileStorage):
                    v.close()
