#
# ayame.core
#
#   Copyright (c) 2011 Akinori Hattori <hattya@gmail.com>
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

from datetime import timedelta
import os
import sys
import threading

from beaker.middleware import SessionMiddleware

from ayame import http, route
from ayame.exception import AyameError


__all__ = ['Ayame']

_local = threading.local()
_local.app = None

class Ayame(object):

    @staticmethod
    def instance():
        app = _local.app
        if not isinstance(app, Ayame):
            raise AyameError('there is no application attached '
                             "to '{}'".format(threading.current_thread().name))
        return app

    def __init__(self, name):
        self._name = name
        try:
            module = sys.modules[name]
            self._root = os.path.abspath(os.path.dirname(module.__file__))
        except (KeyError, AttributeError):
            self._root = os.getcwd()
        session_dir = os.path.join(self._root, 'session')
        self.config = {
                'ayame.markup.encoding': 'utf-8',
                'ayame.route.map': route.Map(),
                'beaker.session.type': 'file',
                'beaker.session.data_dir': os.path.join(session_dir, 'data'),
                'beaker.session.lock_dir': os.path.join(session_dir, 'lock'),
                'beaker.session.cookie_expires': timedelta(31),
                'beaker.session.key': None,
                'beaker.session.secret': None}

    def make_app(self):
        beaker = dict((k, self.config[k]) for k in self.config
                      if k.startswith('beaker.'))
        app = SessionMiddleware(self, beaker, 'ayame.session')
        return app

    def __call__(self, environ, start_response):
        try:
            _local.app = self
            self.environ = environ
            self._router = self.config['ayame.route.map'].bind(environ)
            obj, values = self._router.match()

            start_response(http.OK.status,
                           [('Content-Type', 'text/plain;charset=UTF-8')])
            return []
        except http.HTTPError as e:
            data = e.html()
            headers = list(e.headers)
            headers.append(('Content-Type', 'text/html;charset=UTF-8'))
            headers.append(('Content-Length', str(len(data))))
            start_response(e.status, headers)
            return data
        finally:
            self.environ = None
            _local.app = None
