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
import cgi
import os
import sys
import threading

from beaker.middleware import SessionMiddleware

from ayame import http, route
from ayame.exception import AyameError, ComponentError


__all__ = ['Ayame', 'Component', 'MarkupContainer', 'Model']

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
        except (AttributeError, KeyError):
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

class Component(object):

    def __init__(self, id, model=None):
        if id is None:
            raise ComponentError('component id is not set')
        self.__id = id
        self.model = model
        self.parent = None
        self.escape_model_string = True

    @property
    def id(self):
        return self.__id

    def model():
        def fget(self):
            return self.__model
        def fset(self, model):
            if (model is not None and
                not isinstance(model, Model)):
                self.__model = None
                raise ComponentError(
                        '{!r} is not an instance of Model'.format(model))
            self.__model = model
        return locals()

    model = property(**model())

    @property
    def model_object(self):
        object = self.model.object if self.model else None
        if (isinstance(object, basestring) and
            self.escape_model_string):
            return cgi.escape(object)
        return object

    @property
    def app(self):
        return Ayame.instance()

    @property
    def config(self):
        return self.app.config

    def render(self, element):
        self.on_before_render()
        element = self.on_render(element)
        self.on_after_render()
        return element

    def on_before_render(self):
        pass

    def on_render(self, element):
        return element

    def on_after_render(self):
        pass

class MarkupContainer(Component):

    def __init__(self, id, model=None):
        super(MarkupContainer, self).__init__(id, model)
        self.children = []
        self._ref = {}

    def add(self, *args):
        for obj in args:
            if isinstance(obj, Component):
                if obj.id in self._ref:
                    raise ComponentError(
                            "component for '{}' already exist".format(obj.id))
                self.children.append(obj)
                self._ref[obj.id] = obj
                obj.parent = self
        return self

    def find(self, path):
        if not path:
            return self
        p = path.split(':', 1)
        id, tail = p[0], p[1] if len(p) > 1 else None
        child = self._ref.get(id)
        if isinstance(child, MarkupContainer):
            return child.find(tail)
        return child

    def on_before_render(self):
        super(MarkupContainer, self).on_before_render()
        for child in self.children:
            child.on_before_render()

    def on_after_render(self):
        super(MarkupContainer, self).on_after_render()
        for child in self.children:
            child.on_after_render()

class Model(object):

    def __init__(self, object):
        self.__object = object

    @property
    def object(self):
        if isinstance(self.__object, Model):
            return self.__object.object
        return self.__object
