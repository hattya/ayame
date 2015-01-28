#
# ayame.session
#
#   Copyright (c) 2015 Akinori Hattori <hattya@gmail.com>
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

from werkzeug import http
from werkzeug.contrib.sessions import FilesystemSessionStore as FileSystemSessionStore


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
