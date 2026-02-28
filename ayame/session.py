#
# ayame.session
#
#   Copyright (c) 2015-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import abc
from collections.abc import Iterable, Mapping
import datetime
import json
import os
import random
import secrets
import tempfile
import time
from typing import TYPE_CHECKING, Any

import itsdangerous
import werkzeug.datastructures
import werkzeug.http

from ._typing import Self, WSGIEnvironment

if TYPE_CHECKING:
    from . import app as am


__all__ = ['load', 'save', 'max_age', 'Session', 'SessionStore',
           'CookieSessionStore', 'FileSystemSessionStore']

MAX_AGE = 60 * 60 * 24 * 400


def load(app: am.Ayame, environ: WSGIEnvironment) -> Session:
    store: SessionStore = app.config['ayame.session.store']
    if random.random() < app.config['ayame.session.gc']:
        store.gc()
    c = werkzeug.http.parse_cookie(environ.get('HTTP_COOKIE', ''))
    return store.load(c.get(app.config['ayame.session.name']))


def save(app: am.Ayame, sess: Session) -> tuple[str, str] | None:
    store: SessionStore
    max_age: datetime.timedelta | int | None
    expires: str | datetime.datetime | int | float | None
    if (sess.modified
        and not sess):
        store = app.config['ayame.session.store']
        store.drop(sess)
        v = ''
        max_age = expires = 0
    elif (sess.modified
          or app.config['ayame.session.sliding']):
        store = app.config['ayame.session.store']
        v = store.save(sess)
        max_age = app.config['ayame.session.max_age']
        expires = app.config['ayame.session.expires']
    else:
        return None
    return 'Set-Cookie', werkzeug.http.dump_cookie(app.config['ayame.session.name'],
                                                   v,
                                                   max_age,
                                                   expires,
                                                   app.config['ayame.session.path'],
                                                   app.config['ayame.session.domain'],
                                                   app.config['ayame.session.secure'],
                                                   app.config['ayame.session.httponly'])


def max_age(app: am.Ayame) -> int | None:
    rv = 0.0
    if v := app.config['ayame.session.max_age']:
        rv = v if isinstance(v, (int, float)) else v.total_seconds()
    elif v := app.config['ayame.session.expires']:
        if isinstance(v, (int, float)):
            ts = v
        else:
            dt: datetime.datetime | None = werkzeug.http.parse_date(v) if isinstance(v, str) else v
            if dt:
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                elif dt.tzinfo != datetime.timezone.utc:
                    dt = dt.astimezone(datetime.timezone.utc)
                ts = dt.timestamp()
            else:
                ts = 0.0
        if ts:
            rv = ts - time.time()
    return int(rv) if rv > 0.0 else None


class Session(werkzeug.datastructures.CallbackDict[str, Any]):

    __slots__ = ('sid', 'modified')

    def __init__(self, data: Mapping[str, Any] | None = None, sid: str = ''):
        def on_update(self: Self) -> None:
            self.modified = True

        super().__init__(data, on_update)
        self.sid = sid
        self.modified = False

    def __repr__(self) -> str:
        return f'<{type(self).__name__}{"*" if self.modified else ""} {dict.__repr__(self)}>'

    def __copy__(self) -> Self:
        sess = type(self)(self)
        sess.sid = self.sid
        sess.modified = self.modified
        return sess

    copy = __copy__


class SessionStore(metaclass=abc.ABCMeta):

    def __init__(self, max_age: int | None = None) -> None:
        self.max_age = max_age if max_age and max_age > 0 else MAX_AGE

    @abc.abstractmethod
    def load(self, value: str | None) -> Session:
        raise NotImplementedError

    @abc.abstractmethod
    def save(self, sess: Session) -> str:
        raise NotImplementedError

    def drop(self, sess: Session) -> None:
        pass

    def gc(self) -> None:
        pass


class CookieSessionStore(SessionStore):

    def __init__(self, secret_key: str | bytes | Iterable[str] | Iterable[bytes],
                 salt: str | bytes | None = 'session', max_age: int | None = None) -> None:
        super().__init__(max_age)
        self.serializer = itsdangerous.URLSafeTimedSerializer(secret_key, salt)

    def load(self, value: str | None) -> Session:
        m = False
        if value:
            try:
                return Session(self.serializer.loads(value, max_age=self.max_age))
            except Exception:
                m = True
        sess = Session()
        sess.modified = m
        return sess

    def save(self, sess: Session) -> str:
        return self.serializer.dumps(sess)


class FileSystemSessionStore(SessionStore):

    _prefix = '__session__'

    def __init__(self, path: str, name: str = 'ayame_{sid}.sess', mode: int = 0o644, max_age: int | None = None) -> None:
        super().__init__(max_age)
        self.path = path
        self.name = name
        self.mode = mode

    def load(self, value: str | None) -> Session:
        m = False
        if value:
            try:
                with open(self._path_for(value)) as fp:
                    return Session(json.load(fp), sid=value)
            except Exception:
                m = True
        sess = Session(sid=secrets.token_urlsafe())
        sess.modified = m
        return sess

    def save(self, sess: Session) -> str:
        if sess.modified:
            dst = self._path_for(sess.sid)
            fd, tmp = tempfile.mkstemp(prefix=self._prefix, dir=self.path, text=True)
            try:
                with os.fdopen(fd, 'w') as fp:
                    json.dump(sess, fp)
                    fp.flush()
                os.replace(tmp, dst)
                os.chmod(dst, self.mode)
            except Exception:
                os.unlink(tmp)
                raise
        return sess.sid

    def drop(self, sess: Session) -> None:
        try:
            os.remove(self._path_for(sess.sid))
        except OSError:
            pass

    def _path_for(self, sid: str) -> str:
        return os.path.join(self.path, self.name.format(sid=sid))

    def gc(self) -> None:
        now = time.time()
        try:
            with os.scandir(self.path) as it:
                for e in it:
                    try:
                        if (e.is_file()
                            and not e.name.startswith(self._prefix)
                            and now - e.stat().st_mtime > self.max_age):
                            os.remove(e.path)
                    except OSError:
                        pass
        except OSError:
            pass
