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

from ayame import http, markup, route, util
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
                'ayame.class.MarkupLoader': markup.MarkupLoader,
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
        self.visible = True
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
        self.markup_type = markup.MarkupType('.html', 'text/html')
        self.children = []
        self._ref = {}
        self._extra_head = None

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
        id, tail = p[0], p[1] if 1 < len(p) else None
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
        push_children = self._push_children
        join_children = self._join_children

        # apply modifiers
        element = super(MarkupContainer, self).on_render(element)

        self._extra_head = []
        queue = self._new_queue(root)
        while queue:
            parent, index, element = queue.pop()
            if element.qname.ns_uri == markup.AYAME_NS:
                # render ayame element
                value = self.render_ayame_element(element)
                if value is not None:
                    if isinstance(value, markup.Element):
                        queue.append((parent, index, value))
                    elif hasattr(value, '__iter__'):
                        children = parent.children[:index]
                        elements = []
                        # save same parent elements
                        while queue:
                            q = queue.pop()
                            if q[0] != parent:
                                queue.append(q)
                                break
                            elements.append(q[2])
                        # append rendered children
                        for v in value:
                            if isinstance(v, markup.Element):
                                elements.append(v)
                            children.append(v)
                        if elements:
                            # replace ayame element (queue)
                            total = len(elements)
                            last = index + total - 1
                            i = 0
                            while i < total:
                                queue.append((parent, last - i, elements[i]))
                                i += 1
                        # replace ayame element (parent)
                        children += parent.children[index + 1:]
                        parent.children = children
                    continue
            elif markup.AYAME_ID in element.attrib:
                # render component
                ayame_id, value = self.render_component(element)
            else:
                # there is no associated component
                push_children(queue, element)
                continue

            if parent is None:
                # replace root element
                root = '' if value is None else value
                push_children(queue, root)
            elif hasattr(value, '__iter__'):
                # replace element
                children = parent.children[:index]
                # check consecutive strings
                text = None
                for v in value:
                    if isinstance(v, basestring):
                        if (text is None and
                            (children and
                             isinstance(children[-1], basestring))):
                            # current and previous children are strings
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
                        push_children(queue, v)
                if text is not None:
                    # flush text buffer
                    children.append(''.join(text))
                    text = None
                join_children(children, parent.children[index + 1:])
                parent.children = children
            else:
                children = parent.children
                if value is None:
                    # remove element
                    del children[index]
                else:
                    # replace element
                    children[index] = value
                    push_children(queue, value)
                # check consecutive strings
                if (0 <= index < len(children) and
                    isinstance(children[index], basestring)):
                    beg = end = index
                    if (0 < index and
                        isinstance(children[index - 1], basestring)):
                        # current and previous children are strings
                        beg = index - 1
                        end = index + 1
                    if (index + 1 < len(children) and
                        isinstance(children[index + 1], basestring)):
                        # current and next children are strings
                        end = index + 2
                    if (beg != index or
                        index != end):
                        # join consecutive strings
                        parent.children = children[:beg]
                        parent.children.append(''.join(children[beg:end]))
                        parent.children += children[end:]
        # merge ayame:head
        self.merge_ayame_head(root)
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
            element.qname = markup.DIV
            return element
        elif element.qname == markup.AYAME_ENCLOSURE:
            component = find(get(element, markup.AYAME_CHILD))
            return element.children if component.visible else None
        raise RenderingError(
                "unknown element 'ayame:{}'".format(element.qname.name))

    def push_ayame_head(self, ayame_head):
        parent = self
        while parent.parent is not None:
            parent = parent.parent
        self._join_children(parent._extra_head, ayame_head.children)

    def merge_ayame_head(self, root):
        if self._extra_head:
            if (isinstance(root, markup.Element) and
                root.qname == markup.HTML):
                for node in root.children:
                    if (isinstance(node, markup.Element) and
                        node.qname == markup.HEAD):
                        node.type = markup.Element.OPEN
                        self._join_children(node.children, self._extra_head)
                        self._extra_head = None
                if self._extra_head is not None:
                    raise RenderingError('head element is not found')
            else:
                raise RenderingError('root element is not html')
        else:
            self._extra_head = None

    def render_component(self, element):
        # retrieve ayame:id
        ayame_id = None
        for attr in tuple(element.attrib):
            if attr.ns_uri != markup.AYAME_NS:
                continue
            elif attr.name == 'id':
                ayame_id = element.attrib.pop(attr)
            else:
                raise RenderingError(
                        "unknown attribute 'ayame:{}'".format(attr.name))
        if ayame_id is None:
            return None, element
        # find component
        component = self.find(ayame_id)
        if component is None:
            raise ComponentError(
                    "component for '{}' is not found".format(ayame_id))
        elif not component.visible:
            return ayame_id, None
        # render component
        element = component.on_render(element)
        return (ayame_id,
                element.children if component.render_body_only else element)

    def on_after_render(self):
        super(MarkupContainer, self).on_after_render()
        for child in self.children:
            child.on_after_render()

    def load_markup(self, cls=None):
        new_queue = self._new_queue
        push_children = self._push_children
        join_children = self._join_children

        def throw(cls, msg):
            raise AyameError('{}: {}'.format(util.fqon_of(cls), msg))

        def walk(root):
            queue = new_queue(root)
            while queue:
                parent, index, element = queue.pop()
                if element.qname == markup.AYAME_EXTEND:
                    yield parent, index, element
                elif element.qname in (markup.AYAME_CHILD, markup.AYAME_HEAD):
                    yield parent, index, element
                    continue # skip children
                push_children(queue, element)

        cls = self.__class__ if cls is None else cls
        loader = self.config['ayame.class.MarkupLoader']()
        ext = self.markup_type.extension
        encoding = self.config['ayame.markup.encoding']
        extra_head = []
        ayame_child = None
        while True:
            m = loader.load(cls, util.load_data(cls, ext, encoding))
            html = 'html' in m.lang
            ayame_extend = ayame_head = None
            for parent, index, element in walk(m.root):
                if element.qname == markup.AYAME_EXTEND:
                    if ayame_extend is None:
                        # resolve superclass
                        supercls = None
                        for c in cls.__bases__:
                            if (not issubclass(c, MarkupContainer) or
                                c is MarkupContainer):
                                continue
                            elif supercls is not None:
                                throw(cls,
                                      'does not support multiple inheritance')
                            supercls = c
                        if supercls is None:
                            throw(cls, 'superclass is not found')
                        cls = supercls
                        ayame_extend = element
                elif element.qname == markup.AYAME_CHILD:
                    if ayame_child is not None:
                        # merge submarkup into supermarkup
                        children = parent.children[:index]
                        if ayame_child:
                            join_children(children, ayame_child)
                        if index + 1 < len(parent.children):
                            join_children(children,
                                          parent.children[index + 1:])
                        parent.children = children
                        ayame_child = None
                elif element.qname == markup.AYAME_HEAD:
                    if (html and
                        ayame_head is None):
                        ayame_head = element
            if ayame_child is not None:
                throw(cls, 'ayame:child element is not found')
            elif ayame_extend is None:
                break # ayame:extend is not found
            # for ayame:child in supermarkup
            ayame_child = ayame_extend.children
            # merge ayame:head
            if ayame_head is not None:
                extra_head = join_children(list(ayame_head.children),
                                           extra_head)
        # merge ayame:head into supermarkup
        if extra_head:
            if ayame_head is None:
                # merge to head
                for node in m.root.children:
                    if (isinstance(node, markup.Element) and
                        node.qname == markup.HEAD):
                        join_children(node.children, extra_head)
                        extra_head = None
            else:
                # merge to ayame:head
                join_children(ayame_head.children, extra_head)
                extra_head = None
            if extra_head is not None:
                throw(cls, 'head element is not found')
        return m

    def _new_queue(self, root):
        queue = deque()
        if isinstance(root, markup.Element):
            queue.append((None, -1, root))
        return queue

    def _push_children(self, queue, node):
        if isinstance(node, markup.Element):
            index = len(node.children) - 1
            while 0 <= index:
                child = node.children[index]
                if isinstance(child, markup.Element):
                    queue.append((node, index, child))
                index -= 1

    def _join_children(self, a, b):
        if ((a and
             isinstance(a[-1], basestring)) and
            (b and
             isinstance(b[0], basestring))):
            a[-1] = ''.join((a[-1], b[0]))
            a += b[1:]
        else:
            a += b
        return a

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
