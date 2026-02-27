#
# ayame.app
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
from collections.abc import Callable, Iterable
import locale
import os
import sys
from typing import Any, AnyStr

import werkzeug.datastructures

from . import (converter, core, http, i18n, local, markup, page, res, route,
               session, uri, util)
from ._typing import Headers, Locale, OptExcInfo, Self, InputStream, StartResponse, WSGIEnvironment
from .exception import AyameError, _Redirect


__all__ = ['Ayame', 'Request']


class Ayame:

    config: dict[str, Any]

    def __init__(self, name: str) -> None:
        self._name = name
        try:
            self._root = os.path.abspath(os.path.dirname(sys.modules[name].__file__ or ''))
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
            'ayame.session.store': session.FileSystemSessionStore(session_dir),
            'ayame.session.gc': 0.01,
            'ayame.session.sliding': True,
            'ayame.session.name': 'session_id',
            'ayame.session.expires': None,
            'ayame.session.max_age': None,
            'ayame.session.domain': None,
            'ayame.session.path': '/',
            'ayame.session.secure': False,
            'ayame.session.httponly': True,
        }

    @property
    def context(self) -> local.Context:
        return local.context()

    @property
    def environ(self) -> WSGIEnvironment:
        return self.context.environ

    @property
    def request(self) -> Request:
        return self.context.request

    @property
    def session(self) -> session.Session:
        return self.context.session

    @property
    def _router(self) -> route.Router:
        return self.context._router

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> Iterable[bytes]:
        ctx = local.push(self, environ)
        map: route.Map = self.config['ayame.route.map']
        ctx._router = map.bind(environ)
        try:
            o, values = ctx._router.match()
            ctx.request = self.config['ayame.request'](environ, values)
            ctx.session = session.load(self, environ)
            for _ in range(self.config['ayame.max.redirect']):
                try:
                    status, headers, content = self.handle_request(o)
                except _Redirect as r:
                    if r.args[3] == _Redirect.Type.PERMANENT:
                        raise http.MovedPermanently(uri.application_uri(environ)
                                                    + self.uri_for(*r.args[:3], relative=True)[1:])
                    elif r.args[3] != _Redirect.Type.INTERNAL:
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

    def handle_request(self, object: Any) -> tuple[str, Headers, Iterable[bytes]]:
        if isinstance(object, type):
            if issubclass(object, core.Page):
                object = object()
            else:
                # type is callable, so it might cause unexpected error
                object = None
        if callable(object):
            func: Callable[[], tuple[str, Headers, Iterable[bytes]]] = object
            return func()
        raise http.NotFound(uri.request_path(self.environ))

    def handle_error(self, error: Exception) -> tuple[str, Headers, OptExcInfo | None, Iterable[bytes]]:
        if isinstance(error, http.HTTPStatus):
            page: core.Page = self.config['ayame.page.http'](error)
            status, headers, content = page()
            exc_info = None
        else:
            status, headers, content = http.InternalServerError.status, [], []
            exc_info = sys.exc_info()
        return status, headers, exc_info, content

    def forward(self, object: Any, values: dict[AnyStr, Any] | None = None, anchor: AnyStr | None = None) -> None:
        raise _Redirect(object, values, anchor, _Redirect.Type.INTERNAL)

    def redirect(self, object: Any, values: dict[AnyStr, Any] | None = None, anchor: AnyStr | None = None,
                 permanent: bool = False) -> None:
        raise _Redirect(object, values, anchor, _Redirect.Type.PERMANENT if permanent else _Redirect.Type.TEMPORARY)

    def uri_for(self, *args: Any, **kwargs: Any) -> str:
        return self._router.build(*args, **kwargs)


class Request:

    __slots__ = ('environ', 'method', 'uri', 'query', 'form_data', 'path',
                 'locale')

    def __init__(self, environ: WSGIEnvironment, values: dict[str, Any]) -> None:
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

    def _parse_locales(self, environ: WSGIEnvironment) -> Locale:
        loc: str | None
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
    def input(self) -> InputStream:
        input: InputStream = self.environ['wsgi.input']
        return input

    @property
    def session(self) -> session.Session:
        return local.context().session

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        for data in self.form_data.values():
            for v in data:
                if isinstance(v, werkzeug.datastructures.FileStorage):
                    v.close()
