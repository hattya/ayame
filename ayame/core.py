#
# ayame.core
#
#   Copyright (c) 2011-2012 Akinori Hattori <hattya@gmail.com>
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

import cgi
import collections
import datetime
import locale
import os
import sys
import threading
import wsgiref.headers

import beaker.middleware

import ayame.converter
from ayame.exception import (AyameError, ComponentError, Redirect,
                             RenderingError)
import ayame.http
import ayame.i18n
import ayame.markup
import ayame.model
import ayame.route
import ayame.uri
import ayame.util


__all__ = ['AYAME_PATH', 'Ayame', 'Component', 'MarkupContainer', 'Page',
           'Request', 'Behavior', 'AttributeModifier', 'IgnitionBehavior',
           'nested']

# marker for firing component
AYAME_PATH = u'ayame:path'

_local = threading.local()
_local.app = None
_local.environ = None
_local.request = None
_local._router = None


class Ayame(object):

    @staticmethod
    def instance():
        app = _local.app
        if not isinstance(app, Ayame):
            raise AyameError(u"there is no application attached to "
                             u"'{}'".format(threading.current_thread().name))
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
            'ayame.converter.locator': ayame.converter.Locator(),
            'ayame.i18n.localizer': ayame.i18n.Localizer(),
            'ayame.markup.encoding': 'utf-8',
            'ayame.markup.separator': '.',
            'ayame.markup.pretty': False,
            'ayame.max.redirect': 7,
            'ayame.route.map': ayame.route.Map(),
            'ayame.class.MarkupLoader': ayame.markup.MarkupLoader,
            'ayame.class.MarkupRenderer': ayame.markup.MarkupRenderer,
            'ayame.class.Request': Request,
            'beaker.session.type': 'file',
            'beaker.session.data_dir': os.path.join(session_dir, 'data'),
            'beaker.session.lock_dir': os.path.join(session_dir, 'lock'),
            'beaker.session.cookie_expires': datetime.timedelta(31),
            'beaker.session.key': None,
            'beaker.session.secret': None}

    @property
    def environ(self):
        return _local.environ

    @property
    def request(self):
        return _local.request

    @property
    def session(self):
        return _local.environ['ayame.session']

    @property
    def _router(self):
        return _local._router

    def new(self):
        app = beaker.middleware.SessionMiddleware(self, self.config,
                                                  'ayame.session')
        return app

    def __call__(self, environ, start_response):
        try:
            _local.app = self
            _local.environ = environ
            _local._router = self.config['ayame.route.map'].bind(environ)
            # dispatch
            object, values = _local._router.match()
            _local.request = self.config['ayame.class.Request'](environ,
                                                                values)
            for _ in xrange(self.config['ayame.max.redirect']):
                try:
                    status, headers, content = self.handle_request(object)
                except Redirect as r:
                    if r.args[3] == Redirect.PERMANENT:
                        raise ayame.http.MovedPermanently(
                            ayame.uri.application_uri(self.environ) +
                            self.uri_for(*r.args[:3], relative=True)[1:])
                    elif r.args[3] != Redirect.INTERNAL:
                        raise ayame.http.Found(
                            ayame.uri.application_uri(self.environ) +
                            self.uri_for(*r.args[:3], relative=True)[1:])
                    object = r.args[0]
                    _local.request.path = None
                else:
                    break
            else:
                raise AyameError('reached to the maximum number of internal '
                                 'redirects')
            exc_info = None
        except Exception as e:
            status, headers, content, exc_info = self.handle_error(e)
        finally:
            _local._router = None
            _local.environ = None
            _local.app = None

        start_response(status, headers, exc_info)
        return content

    def handle_request(self, object):
        if isinstance(object, type):
            if issubclass(object, Page):
                return object().render()
        raise ayame.http.NotFound(ayame.uri.request_path(self.environ))

    def handle_error(self, e):
        if isinstance(e, ayame.http.HTTPError):
            status = e.status
            content = e.html().encode('utf-8')
            headers = list(e.headers)
            headers.append(('Content-Type', 'text/html; charset=UTF-8'))
            headers.append(('Content-Length', str(len(content))))
            exc_info = None
        else:
            status = ayame.http.InternalServerError.status
            headers = []
            content = []
            exc_info = sys.exc_info()
        return status, headers, content, exc_info

    def forward(self, object, values=None, anchor=None):
        raise Redirect(object, values, anchor, Redirect.INTERNAL)

    def redirect(self, object, values=None, anchor=None, permanent=False):
        raise Redirect(object, values, anchor,
                       Redirect.PERMANENT if permanent else Redirect.TEMPORARY)

    def uri_for(self, *args, **kwargs):
        return self._router.build(*args, **kwargs)


class Component(object):

    def __init__(self, id, model=None):
        if (not isinstance(self, Page) and
            id is None):
            raise ComponentError(self, 'component id is not set')
        self.__id = id
        self.__model = None
        self.model = model
        self.parent = None
        self.escape_model_string = True
        self.render_body_only = False
        self.visible = True
        self.behaviors = []

    @property
    def id(self):
        return self.__id

    def model():
        def fget(self):
            if self.__model is not None:
                return self.__model
            else:
                current = self.parent
                while current:
                    model = current.model
                    if isinstance(model, ayame.model.InheritableModel):
                        self.__model = model.wrap(self)
                        return self.__model
                    current = current.parent

        def fset(self, model):
            if (model is not None and
                not isinstance(model, ayame.model.Model)):
                self.__model = None
                raise ComponentError(
                    self, '{!r} is not instance of Model'.format(model))
            # update model
            prev = self.__model
            self.__model = model
            # propagate to child models
            if (isinstance(self, MarkupContainer) and
                (prev and
                 isinstance(prev, ayame.model.InheritableModel))):
                queue = collections.deque((self,))
                while queue:
                    component = queue.pop()
                    # reset model
                    if (isinstance(component.model, ayame.model.WrapModel) and
                        component.model.wrapped_model == prev):
                        component.model = None
                    # push children
                    if isinstance(component, MarkupContainer):
                        queue.extend(reversed(component.children))

        return locals()

    model = property(**model())

    def model_object():
        def fget(self):
            return self.model.object if self.model is not None else None

        def fset(self, object):
            if self.model is None:
                raise ComponentError(self, 'model is not set')
            self.model.object = object

        return locals()

    model_object = property(**model_object())

    @property
    def app(self):
        return Ayame.instance()

    @property
    def config(self):
        return self.app.config

    @property
    def environ(self):
        return self.app.environ

    @property
    def request(self):
        return self.app.request

    @property
    def session(self):
        return self.app.session

    def add(self, *args):
        for object in args:
            if isinstance(object, Behavior):
                self.behaviors.append(object)
                object.component = self
        return self

    def converter_for(self, value):
        return self.config['ayame.converter.locator'].converter_for(value)

    def forward(self, *args, **kwargs):
        return self.app.forward(*args, **kwargs)

    def model_object_as_string(self):
        object = self.model_object
        if object is not None:
            if not isinstance(object, basestring):
                converter = self.converter_for(object)
                object = converter.to_string(object)
            if self.escape_model_string:
                return cgi.escape(object, True)
            return object
        return u''

    def page(self):
        current = self
        while current.parent is not None:
            current = current.parent
        if isinstance(current, Page):
            return current
        raise ComponentError(self, 'component is not attached to Page')

    def path(self):
        current = self
        buf = [current.id]
        while current.parent is not None:
            current = current.parent
            buf.append(current.id)
        if (isinstance(current, Page) and
            buf[-1] is None):
            buf = buf[:-1]
        return u':'.join(reversed(buf))

    def redirect(self, *args, **kwargs):
        return self.app.redirect(*args, **kwargs)

    def render(self, element):
        self.on_before_render()
        element = self.on_render(element)
        self.on_after_render()
        return element

    def on_before_render(self):
        for behavior in self.behaviors:
            behavior.on_before_render(self)

    def on_render(self, element):
        for behavior in self.behaviors:
            behavior.on_component(self, element)
        return element

    def on_after_render(self):
        for behavior in self.behaviors:
            behavior.on_after_render(self)

    def tr(self, key, component=None):
        component = component if component is not None else self
        return self.config['ayame.i18n.localizer'].get(component,
                                                       self.request.locale,
                                                       key)

    def uri_for(self, *args, **kwargs):
        return self.app.uri_for(*args, **kwargs)


class MarkupContainer(Component):

    markup_type = ayame.markup.MarkupType('.html', 'text/html', ())

    def __init__(self, id, model=None):
        super(MarkupContainer, self).__init__(id, model)
        self.children = []
        self._ref = {}
        self._extra_head = None

    def add(self, *args):
        for object in args:
            if isinstance(object, Component):
                if object.id in self._ref:
                    raise ComponentError(
                        self,
                        u"component for '{}' already exist".format(object.id))
                self.children.append(object)
                self._ref[object.id] = object
                object.parent = self
            else:
                super(MarkupContainer, self).add(object)
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

    def walk(self, step=None):
        step = step if callable(step) else lambda *args: True

        queue = collections.deque(((self, 0),))
        while queue:
            component, depth = queue.pop()
            yield component, depth
            # push child components
            if (isinstance(component, MarkupContainer) and
                step(component, depth)):
                queue.extend((c, depth + 1)
                             for c in reversed(component.children))

    def on_before_render(self):
        super(MarkupContainer, self).on_before_render()
        for child in self.children:
            child.on_before_render()

    def on_render(self, element):
        def push(queue, node):
            if isinstance(node, ayame.markup.Element):
                for index in xrange(len(node) - 1, -1, -1):
                    child = node[index]
                    if isinstance(child, ayame.markup.Element):
                        queue.append((node, index, child))

        root = element
        # notify behaviors
        element = super(MarkupContainer, self).on_render(element)

        self._extra_head = []
        queue = collections.deque()
        if isinstance(root, ayame.markup.Element):
            queue.append((None, -1, root))
        while queue:
            parent, index, element = queue.pop()
            if element.qname.ns_uri == ayame.markup.AYAME_NS:
                # render ayame element
                value = self.render_ayame_element(element)
                if value is not None:
                    if isinstance(value, ayame.markup.Element):
                        queue.append((parent, index, value))
                    elif isinstance(value, collections.Sequence):
                        # save same parent elements
                        elements = []
                        while queue:
                            q = queue.pop()
                            if q[0] != parent:
                                queue.append(q)
                                break
                            elements.append(q[2])
                        # append rendered children
                        elements.extend(v for v in value
                                        if isinstance(v, ayame.markup.Element))
                        if elements:
                            # replace ayame element (queue)
                            total = len(elements)
                            last = index + total - 1
                            for i in xrange(total):
                                queue.append((parent, last - i, elements[i]))
                        # replace ayame element (parent)
                        parent[index:index + 1] = value
                    continue
            elif ayame.markup.AYAME_ID in element.attrib:
                # render component
                ayame_id, value = self.render_component(element)
            else:
                # there is no associated component
                push(queue, element)
                continue

            if parent is None:
                # replace root element
                if value is None:
                    root = u''
                else:
                    root = value
                    push(queue, root)
            elif isinstance(value, collections.Sequence):
                # replace element
                parent[index:index + 1] = value
                for v in value:
                    push(queue, v)
            elif value is None:
                # remove element
                del parent[index]
            else:
                # replace element
                parent[index] = value
                push(queue, value)
        # merge ayame:head
        self.merge_ayame_head(root)
        return root

    def render_ayame_element(self, element):
        def get(element, attr, keep=True):
            if attr in element.attrib:
                if keep:
                    return element.attrib[attr]
                return element.attrib.pop(attr)
            raise RenderingError(
                self,
                u"'ayame:{}' attribute is required for "
                u"'ayame:{}' element".format(attr.name, element.qname.name))

        def find(path):
            component = self.find(path)
            if component is not None:
                return component
            raise ComponentError(
                self, u"component for '{}' is not found".format(path))

        if element.qname == ayame.markup.AYAME_CONTAINER:
            find(get(element, ayame.markup.AYAME_ID)).render_body_only = True
            element.qname = ayame.markup.DIV
            return element
        elif element.qname == ayame.markup.AYAME_ENCLOSURE:
            component = find(get(element, ayame.markup.AYAME_CHILD))
            return element.children if component.visible else None
        elif element.qname == ayame.markup.AYAME_MESSAGE:
            key = get(element, ayame.markup.AYAME_KEY, False)
            message = _MessageContainer(ayame.util.new_token()[:7], key)
            self.add(message)
            element.qname = ayame.markup.DIV
            element.attrib[ayame.markup.AYAME_ID] = message.id
            return element

        if element.qname.ns_uri == ayame.markup.AYAME_NS:
            raise RenderingError(
                self, u"unknown element 'ayame:{}'".format(element.qname.name))
        raise RenderingError(self,
                             u"unknown element '{}'".format(element.qname))

    def push_ayame_head(self, ayame_head):
        current = self
        while current.parent is not None:
            current = current.parent
        current._extra_head += ayame_head.children

    def merge_ayame_head(self, root):
        if self._extra_head:
            if (isinstance(root, ayame.markup.Element) and
                root.qname == ayame.markup.HTML):
                for node in root:
                    if (isinstance(node, ayame.markup.Element) and
                        node.qname == ayame.markup.HEAD):
                        node.type = ayame.markup.Element.OPEN
                        node.extend(self._extra_head)
                        self._extra_head = None
                if self._extra_head is not None:
                    raise RenderingError(self, "'head' element is not found")
            else:
                raise RenderingError(self, "root element is not 'html'")
        else:
            self._extra_head = None

    def render_component(self, element):
        # retrieve ayame:id
        ayame_id = None
        for attr in tuple(element.attrib):
            if attr.ns_uri != ayame.markup.AYAME_NS:
                continue
            elif attr.name == 'id':
                ayame_id = element.attrib.pop(attr)
            else:
                raise RenderingError(
                    self, u"unknown attribute 'ayame:{}'".format(attr.name))
        if ayame_id is None:
            return None, element
        # find component
        component = self.find(ayame_id)
        if component is None:
            raise ComponentError(
                self, u"component for '{}' is not found".format(ayame_id))
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

    def load_markup(self, class_=None):
        def step(element, depth):
            return element.qname not in (ayame.markup.AYAME_CHILD,
                                         ayame.markup.AYAME_HEAD)

        def path_of(class_):
            if self.__class__ == class_:
                markup_type = self.markup_type
            else:
                markup_type = super(class_, self).markup_type
            if markup_type.scope:
                return (sep.join(c.__name__
                                 for c in markup_type.scope + (class_,)) +
                        markup_type.extension)
            return markup_type.extension

        class_ = class_ if class_ is not None else self.__class__
        loader = self.config['ayame.class.MarkupLoader']()
        encoding = self.config['ayame.markup.encoding']
        sep = self.config['ayame.markup.separator']
        extra_head = []
        ayame_child = None
        while True:
            m = loader.load(class_, ayame.util.load_data(class_,
                                                         path_of(class_),
                                                         encoding))
            if m.root is None:
                # markup is empty
                break

            html = 'html' in m.lang
            ayame_extend = ayame_head = None
            stack = []
            for element, depth in m.root.walk(step=step):
                stack[depth:] = [element]
                if element.qname == ayame.markup.AYAME_EXTEND:
                    if ayame_extend is None:
                        # resolve superclass
                        superclass = None
                        for c in class_.__bases__:
                            if (not issubclass(c, MarkupContainer) or
                                c is MarkupContainer):
                                continue
                            elif superclass is not None:
                                raise AyameError(
                                    'does not support multiple inheritance')
                            superclass = c
                        if superclass is None:
                            raise AyameError(
                                u"superclass of '{}' is not found".format(
                                    ayame.util.fqon_of(class_)))
                        class_ = superclass
                        ayame_extend = element
                elif element.qname == ayame.markup.AYAME_CHILD:
                    if ayame_child is not None:
                        # merge submarkup into supermarkup
                        if len(stack) < 2:
                            raise RenderingError(self,
                                                 "'ayame:child' element "
                                                 "cannot be the root element")
                        parent = stack[-2]
                        index = parent.children.index(element)
                        parent[index:index + 1] = ayame_child
                        ayame_child = None
                elif element.qname == ayame.markup.AYAME_HEAD:
                    if (html and
                        ayame_head is None):
                        ayame_head = element
            if ayame_child is not None:
                raise RenderingError(class_,
                                     "'ayame:child' element is not found")
            elif ayame_extend is None:
                # ayame:extend is not found
                break
            # for ayame:child in supermarkup
            ayame_child = ayame_extend.children
            # merge ayame:head
            if ayame_head is not None:
                extra_head = ayame_head.children + extra_head
        # merge ayame:head into supermarkup
        if extra_head:
            if ayame_head is None:
                # merge to head
                for node in m.root:
                    if (isinstance(node, ayame.markup.Element) and
                        node.qname == ayame.markup.HEAD):
                        node.extend(extra_head)
                        extra_head = None
            else:
                # merge to ayame:head
                ayame_head.extend(extra_head)
                extra_head = None
            if extra_head is not None:
                raise RenderingError(class_, "'head' element is not found")
        return m


class _MessageContainer(MarkupContainer):

    def __init__(self, id, key):
        super(_MessageContainer, self).__init__(id, ayame.model.Model(key))
        self.escape_model_string = False
        self.render_body_only = True

    def on_render(self, element):
        key = self.model_object_as_string()
        value = self.parent.tr(key)
        if value is None:
            raise RenderingError(
                self.parent,
                "no value found for ayame:message with key '{}'".format(key))
        element[:] = (value,)
        return element


class Page(MarkupContainer):

    def __init__(self):
        super(Page, self).__init__(None)
        self.__headers = []
        self.headers = wsgiref.headers.Headers(self.__headers)

    def render(self):
        # load markup and render components
        m = self.load_markup()
        if m.root is None:
            # markup is empty
            content = b''
        else:
            m.root = super(Page, self).render(m.root)
            # remove ayame namespace from root element
            for prefix in tuple(m.root.ns):
                if m.root.ns[prefix] == ayame.markup.AYAME_NS:
                    del m.root.ns[prefix]
            # render markup
            renderer = self.config['ayame.class.MarkupRenderer']()
            pretty = self.config['ayame.markup.pretty']
            content = renderer.render(self, m, pretty=pretty)
        # HTTP headers
        mime_type = self.markup_type.mime_type
        self.headers['Content-Type'] = '{}; charset=UTF-8'.format(mime_type)
        self.headers['Content-Length'] = str(len(content))
        return ayame.http.OK.status, self.__headers, content


class Request(object):

    __slots__ = ('environ', 'method', 'uri', 'query', 'form_data', 'path',
                 'locale')

    def __init__(self, environ, values):
        self.environ = environ
        self.method = environ['REQUEST_METHOD']
        self.uri = values
        self.query = ayame.uri.parse_qs(environ)
        self.form_data = ayame.http.parse_form_data(environ)
        # retrieve ayame:path
        if self.method == 'GET':
            self.path = self.query.get(AYAME_PATH)
        elif self.method == 'POST':
            self.path = self.form_data.get(AYAME_PATH)
        else:
            self.path = None
        if self.path:
            self.path = self.path[0]
        self.locale = self._parse_locales(environ)

    def _parse_locales(self, environ):
        values = ayame.http.parse_accept(environ.get('HTTP_ACCEPT_LANGUAGE'))
        if values:
            value = values[0][0]
            sep = '-'
        else:
            value = locale.getdefaultlocale()[0]
            sep = '_'
        if value:
            v = value.split(sep, 1)
            if 1 < len(v):
                return (v[0].lower(), v[1].upper())
            elif len(v) == 1:
                return (v[0].lower(), None)
        return (None,) * 2

    @property
    def input(self):
        return self.environ['wsgi.input']

    @property
    def session(self):
        return self.environ['ayame.session']


class Behavior(object):

    def __init__(self):
        self.component = None

    @property
    def app(self):
        return Ayame.instance()

    @property
    def config(self):
        return self.app.config

    @property
    def environ(self):
        return self.app.environ

    @property
    def request(self):
        return self.app.request

    @property
    def session(self):
        return self.app.session

    def forward(self, *args, **kwargs):
        return self.app.forward(*args, **kwargs)

    def on_before_render(self, component):
        pass

    def on_component(self, component, element):
        pass

    def on_after_render(self, component):
        pass

    def redirect(self, *args, **kwargs):
        return self.app.redirect(*args, **kwargs)

    def uri_for(self, *args, **kwargs):
        return self.app.uri_for(*args, **kwargs)


class AttributeModifier(Behavior):

    def __init__(self, attr, model):
        super(AttributeModifier, self).__init__()
        self._attr = attr
        self._model = model

    def on_component(self, component, element):
        if isinstance(self._attr, ayame.markup.QName):
            attr = self._attr
        else:
            attr = ayame.markup.QName(element.qname.ns_uri, self._attr)
        value = self._model.object if self._model is not None else None
        new_value = self.new_value(element.attrib.get(attr), value)
        if new_value is None:
            if attr in element.attrib:
                del element.attrib[attr]
        else:
            element.attrib[attr] = new_value

    def new_value(self, value, new_value):
        return new_value


class IgnitionBehavior(Behavior):

    def fire(self):
        # fire component
        if self.component.path() == self.request.path:
            self.on_fire(self.component)

    def on_fire(self, component):
        pass


class nested(object):

    def __init__(self, class_):
        self.__class = class_

    def __get__(self, instance, owner):
        class_ = self.__class
        if (issubclass(class_, MarkupContainer) and
            issubclass(owner, MarkupContainer)):
            class_.markup_type = ayame.markup.MarkupType(
                class_.markup_type.extension, class_.markup_type.mime_type,
                owner.markup_type.scope + (owner,))
        return class_
