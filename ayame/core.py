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
from collections import deque
import os
import sys
import threading

from beaker.middleware import SessionMiddleware

from ayame import http, markup, route
from ayame.exception import AyameError, ComponentError, RenderingError


__all__ = ['Ayame', 'Component', 'MarkupContainer', 'AttributeModifier',
           'Model', 'CompoundModel']

_local = threading.local()
_local.app = None
_local.environ = None
_local._router = None

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

    @property
    def environ(self):
        return _local.environ

    @property
    def _router(self):
        return _local._router

    def make_app(self):
        beaker = dict((k, self.config[k]) for k in self.config
                      if k.startswith('beaker.'))
        app = SessionMiddleware(self, beaker, 'ayame.session')
        return app

    def __call__(self, environ, start_response):
        try:
            _local.app = self
            _local.environ = environ
            _local._router = self.config['ayame.route.map'].bind(environ)
            obj, values = _local._router.match()

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
            _local._router = None
            _local.environ = None
            _local.app = None

class Component(object):

    def __init__(self, id, model=None):
        if id is None:
            raise ComponentError('component id is not set')
        self.__id = id
        self.model = model
        self.parent = None
        self.escape_model_string = True
        self.render_body_only = False
        self.modifiers = []

    @property
    def id(self):
        return self.__id

    def model():
        def fget(self):
            if self.__model:
                return self.__model
            else:
                current = self.parent
                while current:
                    model = current.model
                    if isinstance(model, CompoundModel):
                        self.__model = model.wrap(self)
                        return self.__model
                    current = current.parent

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

    def add(self, *args):
        for obj in args:
            if isinstance(obj, AttributeModifier):
                self.modifiers.append(obj)
        return self

    def render(self, element):
        self.on_before_render()
        element = self.on_render(element)
        self.on_after_render()
        return element

    def on_before_render(self):
        pass

    def on_render(self, element):
        for modifier in self.modifiers:
            modifier.on_component(self, element)
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
            else:
                super(MarkupContainer, self).add(obj)
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

    def on_render(self, element):
        root = element
        queue = deque()

        def push_children(element):
            if isinstance(element, markup.Element):
                index = len(element.children) - 1
                while 0 <= index:
                    child = element.children[index]
                    if isinstance(child, markup.Element):
                        queue.append((element, index, child))
                    index -= 1

        # apply modifiers
        element = super(MarkupContainer, self).on_render(element)
        # push root element
        if isinstance(root, markup.Element):
            queue.append((None, -1, root))
        while queue:
            parent, index, element = queue.pop()
            if element.qname.ns_uri == markup.AYAME_NS:
                # render ayame element
                value = self.render_ayame_element(element)
                if value is not None:
                    if isinstance(value, markup.Element):
                        queue.append((parent, index, value))
                    continue
            elif markup.AYAME_ID in element.attrib:
                # render component
                ayame_id, value = self.render_component(element)
            else:
                # there is no associated component
                push_children(element)
                continue

            if parent is None:
                # replace root element
                root = '' if value is None else value
                push_children(root)
            elif hasattr(value, '__iter__'):
                # replace element
                children = parent.children[:index]
                tail = parent.children[index + 1:]
                # check consecutive strings
                text = None
                for v in value:
                    if isinstance(v, basestring):
                        if (text is None and
                            (children and
                             isinstance(children[-1], basestring))):
                            # current and previous children are a string
                            text = [children[-1], v]
                            children = children[:-1]
                        elif text is not None:
                            # text buffer exists
                            text.append(v)
                        else:
                            children.append(v)
                    else:
                        if text is not None:
                            # flush text buffer
                            children.append(''.join(text))
                            text = None
                        children.append(v)
                        push_children(v)
                if text is not None:
                    # flush text buffer
                    children.append(''.join(text))
                    text = None
                if ((children and
                     isinstance(children[-1], basestring)) and
                    (tail and
                     isinstance(tail[0], basestring))):
                    # current and next children are a string
                    children[-1] = ''.join((children[-1], tail[0]))
                    children += tail[1:]
                else:
                    children += tail
                parent.children = children
            else:
                children = parent.children
                if value is None:
                    # remove element
                    del children[index]
                else:
                    # replace element
                    children[index] = value
                    push_children(value)
                # check consecutive strings
                if (0 <= index < len(children) and
                    isinstance(children[index], basestring)):
                    beg = end = index
                    if (0 < index and
                        isinstance(children[index - 1], basestring)):
                        # current and previous children are a string
                        beg = index - 1
                        end = index + 1
                    if (index + 1 < len(children) and
                        isinstance(children[index + 1], basestring)):
                        # current and next children are a string
                        end = index + 2
                    if (beg != index or
                        index != end):
                        # join consecutive strings
                        parent.children = children[:beg]
                        parent.children.append(''.join(children[beg:end]))
                        parent.children += children[end:]
        return root

    def render_ayame_element(self, element):
        def get(e, a):
            v = e.attrib.get(a)
            if v is None:
                raise RenderingError("'ayame:{}' attribute is required for "
                                     "'ayame:{}' element".format(a.name,
                                                                 e.qname.name))
            return v

        def find(p):
            c = self.find(p)
            if c is None:
                raise ComponentError(
                        "component for '{}' is not found".format(p))
            return c

        if element.qname == markup.AYAME_CONTAINER:
            find(get(element, markup.AYAME_ID)).render_body_only = True
            element.qname = markup.QName(markup.XHTML_NS, 'div')
            return element
        raise RenderingError(
                "unknown element 'ayame:{}'".format(element.qname.name))

    def render_component(self, element):
        # retrieve ayame:id
        ayame_id = None
        for attr in list(element.attrib):
            if attr.ns_uri != markup.AYAME_NS:
                continue
            elif attr.name == 'id':
                ayame_id = element.attrib.pop(attr)
            else:
                raise RenderingError(
                        "unknown attribute 'ayame:{}'".format(attr.name))
        if ayame_id is None:
            return None, element
        # render component
        component = self.find(ayame_id)
        if component is None:
            raise ComponentError(
                    "component for '{}' is not found".format(ayame_id))
        element = component.on_render(element)
        return (ayame_id,
                element.children if component.render_body_only else element)

    def on_after_render(self):
        super(MarkupContainer, self).on_after_render()
        for child in self.children:
            child.on_after_render()

class AttributeModifier(object):

    def __init__(self, attr, model):
        self._attr = attr
        self._model = model

    @property
    def app(self):
        return Ayame.instance()

    @property
    def config(self):
        return self.app.config

    def on_component(self, component, element):
        if isinstance(self._attr, markup.QName):
            attr = self._attr
        else:
            attr = markup.QName(element.qname.ns_uri, self._attr)
        value = self._model.object if self._model else None
        new_value = self.new_value(element.attrib.get(attr), value)
        if new_value is None:
            if attr in element.attrib:
                del element.attrib[attr]
        else:
            element.attrib[attr] = new_value

    def new_value(self, value, new_value):
        return new_value

class Model(object):

    def __init__(self, object):
        self.__object = object

    @property
    def object(self):
        if isinstance(self.__object, Model):
            return self.__object.object
        return self.__object

class CompoundModel(Model):

    def wrap(self, component):
        class InheritedModel(Model):

            def __init__(self, model):
                super(InheritedModel, self).__init__(None)
                self._component = component
                self._object = model.object

            @property
            def object(self):
                object = self._object
                name = self._component.id
                # instance variable
                try:
                    return getattr(object, name)
                except AttributeError:
                    pass
                # getter method
                try:
                    getter = getattr(object, 'get_' + name)
                    if callable(getter):
                        return getter()
                except AttributeError:
                    pass
                # __getitem__
                try:
                    return object.__getitem__(name)
                except (AttributeError, LookupError):
                    pass
                raise AttributeError(name)

        return InheritedModel(self)
