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

import datetime
import cgi
import collections
import os
import sys
import threading
import urlparse
import wsgiref.headers

from beaker.middleware import SessionMiddleware

from ayame import converter, http, markup, route, uri, util
from ayame import model as _model
from ayame.exception import (AyameError, ComponentError, Redirect,
                             RenderingError)


__all__ = ['AYAME_PATH', 'Ayame', 'Component', 'MarkupContainer', 'Page',
           'Request', 'Behavior', 'AttributeModifier', 'IgnitionBehavior']

# marker for firing component
AYAME_PATH = u'ayame:path'

_local = threading.local()
_local.app = None
_local.environ = None
_local._router = None

class Ayame(object):

    @staticmethod
    def instance():
        app = _local.app
        if not isinstance(app, Ayame):
            raise AyameError(u"there is no application attached to '{}'"
                             .format(threading.current_thread().name))
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
                'ayame.converter.locator': converter.Locator(),
                'ayame.markup.encoding': 'utf-8',
                'ayame.markup.pretty': False,
                'ayame.max.redirect': 7,
                'ayame.route.map': route.Map(),
                'ayame.class.MarkupLoader': markup.MarkupLoader,
                'ayame.class.MarkupRenderer': markup.MarkupRenderer,
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
    def session(self):
        return _local.environ['ayame.session']

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
            # dispatch
            object, values = _local._router.match()
            request = self.config['ayame.class.Request'](environ, values)
            for _ in xrange(self.config['ayame.max.redirect']):
                try:
                    status, headers, content = self.handle_request(object,
                                                                   request)
                except Redirect as r:
                    object = r.args[0]
                else:
                    break
            else:
                raise AyameError('reached to the maximum number of internal '
                                 'redirects')
            exc_info = None
        except Exception as e:
            status, headers, content = self.handle_error(e)
            exc_info = sys.exc_info()
        finally:
            _local._router = None
            _local.environ = None
            _local.app = None

        start_response(status, headers, exc_info)
        return content

    def handle_request(self, object, request):
        if isinstance(object, type):
            if issubclass(object, Page):
                page = object(request)
                return page.render()
        raise http.NotFound(uri.request_path(request.environ))

    def handle_error(self, e):
        if isinstance(e, http.HTTPError):
            status = e.status
            content = e.html().encode('utf-8')
            headers = list(e.headers)
            headers.append(('Content-Type', 'text/html; charset=UTF-8'))
            headers.append(('Content-Length', str(len(content))))
        else:
            status = http.InternalServerError.status
            headers = []
            content = []
        return status, headers, content

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
            if self.__model:
                return self.__model
            else:
                current = self.parent
                while current:
                    model = current.model
                    if isinstance(model, _model.InheritableModel):
                        self.__model = model.wrap(self)
                        return self.__model
                    current = current.parent

        def fset(self, model):
            if (model is not None and
                not isinstance(model, _model.Model)):
                self.__model = None
                raise ComponentError(
                        self, '{!r} is not instance of Model'.format(model))
            # update model
            prev = self.__model
            self.__model = model
            # propagate to child models
            if (isinstance(self, MarkupContainer) and
                (prev and
                 isinstance(prev, _model.InheritableModel))):
                queue = collections.deque()
                queue.append(self)
                while queue:
                    component = queue.pop()
                    # reset model
                    if (isinstance(component.model, _model.WrapModel) and
                        component.model.wrapped_model == prev):
                        component.model = None
                    # push children
                    if isinstance(component, MarkupContainer):
                        queue.extend(reversed(component.children))

        return locals()

    model = property(**model())

    def model_object():
        def fget(self):
            return self.model.object if self.model else None

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

class MarkupContainer(Component):

    def __init__(self, id, model=None):
        super(MarkupContainer, self).__init__(id, model)
        self.markup_type = markup.MarkupType('.html', 'text/html')
        self.children = []
        self._ref = {}
        self._extra_head = None

    def add(self, *args):
        for object in args:
            if isinstance(object, Component):
                if object.id in self._ref:
                    raise ComponentError(self,
                                         u"component for '{}' already exist"
                                         .format(object.id))
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

    def on_before_render(self):
        super(MarkupContainer, self).on_before_render()
        for child in self.children:
            child.on_before_render()

    def on_render(self, element):
        root = element

        def push(queue, node):
            if isinstance(node, markup.Element):
                for index in xrange(len(node) - 1, -1, -1):
                    child = node[index]
                    if isinstance(child, markup.Element):
                        queue.append((node, index, child))

        # notify behaviors
        element = super(MarkupContainer, self).on_render(element)

        self._extra_head = []
        queue = collections.deque()
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
                                        if isinstance(v, markup.Element))
                        if elements:
                            # replace ayame element (queue)
                            total = len(elements)
                            last = index + total - 1
                            for i in xrange(total):
                                queue.append((parent, last - i, elements[i]))
                        # replace ayame element (parent)
                        parent[index:index + 1] = value
                    continue
            elif markup.AYAME_ID in element.attrib:
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
        def get(e, a):
            v = e.attrib.get(a)
            if v is None:
                raise RenderingError(
                        self,
                        u"'ayame:{}' attribute is required for "
                        u"'ayame:{}' element".format(a.name, e.qname.name))
            return v

        def find(p):
            c = self.find(p)
            if c is None:
                raise ComponentError(
                        self, u"component for '{}' is not found".format(p))
            return c

        if element.qname == markup.AYAME_CONTAINER:
            find(get(element, markup.AYAME_ID)).render_body_only = True
            element.qname = markup.DIV
            return element
        elif element.qname == markup.AYAME_ENCLOSURE:
            component = find(get(element, markup.AYAME_CHILD))
            return element.children if component.visible else None

        if element.qname.ns_uri == markup.AYAME_NS:
            raise RenderingError(
                    self,
                    u"unknown element 'ayame:{}'".format(element.qname.name))
        raise RenderingError(self,
                             u"unknown element '{}'".format(element.qname))

    def push_ayame_head(self, ayame_head):
        current = self
        while current.parent is not None:
            current = current.parent
        current._extra_head += ayame_head.children

    def merge_ayame_head(self, root):
        if self._extra_head:
            if (isinstance(root, markup.Element) and
                root.qname == markup.HTML):
                for node in root:
                    if (isinstance(node, markup.Element) and
                        node.qname == markup.HEAD):
                        node.type = markup.Element.OPEN
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
            if attr.ns_uri != markup.AYAME_NS:
                continue
            elif attr.name == 'id':
                ayame_id = element.attrib.pop(attr)
            else:
                raise RenderingError(self,
                                     u"unknown attribute 'ayame:{}'"
                                     .format(attr.name))
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
            return element.qname not in (markup.AYAME_CHILD, markup.AYAME_HEAD)

        class_ = self.__class__ if class_ is None else class_
        loader = self.config['ayame.class.MarkupLoader']()
        ext = self.markup_type.extension
        encoding = self.config['ayame.markup.encoding']
        extra_head = []
        ayame_child = None
        while True:
            m = loader.load(class_, util.load_data(class_, ext, encoding))
            html = 'html' in m.lang
            ayame_extend = ayame_head = None
            stack = []
            for element, depth in m.root.walk(step=step):
                stack[depth:] = [element]
                if element.qname == markup.AYAME_EXTEND:
                    if ayame_extend is None:
                        # resolve superclass
                        superclass = None
                        for c in class_.__bases__:
                            if (not issubclass(c, MarkupContainer) or
                                c is MarkupContainer):
                                continue
                            elif superclass is not None:
                                raise AyameError('does not support '
                                                 'multiple inheritance')
                            superclass = c
                        if superclass is None:
                            raise AyameError(u"superclass of '{}' is not found"
                                             .format(util.fqon_of(class_)))
                        class_ = superclass
                        ayame_extend = element
                elif element.qname == markup.AYAME_CHILD:
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
                elif element.qname == markup.AYAME_HEAD:
                    if (html and
                        ayame_head is None):
                        ayame_head = element
            if ayame_child is not None:
                raise RenderingError(class_,
                                     "'ayame:child' element is not found")
            elif ayame_extend is None:
                break  # ayame:extend is not found
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
                    if (isinstance(node, markup.Element) and
                        node.qname == markup.HEAD):
                        node.extend(extra_head)
                        extra_head = None
            else:
                # merge to ayame:head
                ayame_head.extend(extra_head)
                extra_head = None
            if extra_head is not None:
                raise RenderingError(class_, "'head' element is not found")
        return m

class Page(MarkupContainer):

    def __init__(self, request):
        super(Page, self).__init__(None)
        self.request = request
        self.__headers = []
        self.headers = wsgiref.headers.Headers(self.__headers)

    def render(self):
        # load markup and render components
        m = self.load_markup()
        m.root = super(Page, self).render(m.root)
        # remove ayame namespace from root element
        for prefix in tuple(m.root.ns):
            if m.root.ns[prefix] == markup.AYAME_NS:
                del m.root.ns[prefix]
        # render markup
        renderer = self.config['ayame.class.MarkupRenderer']()
        content = renderer.render(self, m,
                                  pretty=self.config['ayame.markup.pretty'])
        # HTTP headers
        mime_type = self.markup_type.mime_type
        self.headers['Content-Type'] = '{}; charset=UTF-8'.format(mime_type)
        self.headers['Content-Length'] = str(len(content))
        return http.OK.status, self.__headers, content

class Request(object):

    __slots__ = ('environ', 'method', 'uri', 'query', 'form_data')

    def __init__(self, environ, values):
        self.environ = environ
        self.method = environ['REQUEST_METHOD']
        self.uri = values
        self.query = self._parse_qs(environ)
        self.form_data = self._parse_form_data(environ)

    def _parse_qs(self, environ):
        qs = environ.get('QUERY_STRING')
        if not qs:
            return {}

        qs = urlparse.parse_qs(qs, keep_blank_values=True)
        if sys.hexversion < 0x03000000:
            return dict((self._decode(k), [self._decode(s) for s in v])
                        for k, v in qs.iteritems())
        else:
            return qs

    def _parse_form_data(self, environ):
        ct = cgi.parse_header(environ.get('CONTENT_TYPE', ''))[0]
        if ct not in ('application/x-www-form-urlencoded',
                      'multipart/form-data'):
            return {}

        # isolate QUERY_STRING
        fs_environ = environ.copy()
        fs_environ['QUERY_STRING'] = ''
        fs = cgi.FieldStorage(fp=environ['wsgi.input'],
                              environ=fs_environ,
                              keep_blank_values=True)

        form_data = {}
        if fs.list:
            for field in fs.list:
                if field.done == -1:
                    raise http.RequestTimeout()
                field.name = self._decode(field.name)
                if field.filename:
                    field.filename = self._decode(field.filename)
                    value = field
                else:
                    value = self._decode(field.value)
                if field.name in form_data:
                    form_data[field.name].append(value)
                else:
                    form_data[field.name] = [value]
        return form_data

    if sys.hexversion < 0x03000000:
        def _decode(self, s):
            return unicode(s, 'utf-8', 'replace')
    else:
        def _decode(self, s):
            return s

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
    def session(self):
        return self.app.session

    def on_before_render(self, component):
        pass

    def on_component(self, component, element):
        pass

    def on_after_render(self, component):
        pass

class AttributeModifier(Behavior):

    def __init__(self, attr, model):
        super(AttributeModifier, self).__init__()
        self._attr = attr
        self._model = model

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

class IgnitionBehavior(Behavior):

    def fire(self):
        component = self.component
        page = component.page()
        # retrieve ayame:path
        path = None
        if page.request.method == 'GET':
            path = page.request.query.get(AYAME_PATH)
        elif page.request.method == 'POST':
            path = page.request.form_data.get(AYAME_PATH)
        if path:
            if 1 < len(path):
                raise RenderingError(page, 'duplicate ayame:path')
            # fire component
            if path[0] == component.path():
                self.on_fire(component, page.request)

    def on_fire(self, component, request):
        pass
