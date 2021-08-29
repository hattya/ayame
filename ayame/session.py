#
# ayame.session
#
#   Copyright (c) 2015-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from werkzeug import http
from secure_cookie.session import FilesystemSessionStore as FileSystemSessionStore


__all__ = ['get', 'save', 'FileSystemSessionStore']


def get(app, environ):
    store = app.config['ayame.session.store']
    c = http.parse_cookie(environ.get('HTTP_COOKIE', ''))
    sid = c.get(app.config['ayame.session.name'])
    return store.new() if sid is None else store.get(sid)


def save(app, sess):
    if not sess.should_save:
        return
    app.config['ayame.session.store'].save(sess)
    return ('Set-Cookie', http.dump_cookie(app.config['ayame.session.name'], sess.sid,
                                           app.config['ayame.session.max_age'],
                                           app.config['ayame.session.expires'],
                                           app.config['ayame.session.path'],
                                           app.config['ayame.session.domain'],
                                           app.config['ayame.session.secure'],
                                           app.config['ayame.session.httponly']))
