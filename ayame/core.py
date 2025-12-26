#
# ayame.core
#
#   Copyright (c) 2011-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import collections
import html
import wsgiref.headers

from . import http, local, markup, model as mm, util
from .exception import AyameError, ComponentError, RenderingError


__all__ = ['AYAME_PATH', 'Component', 'MarkupContainer', 'Page', 'Behavior',
           'AttributeModifier', 'nested']

# marker for firing component
AYAME_PATH = 'ayame:path'


class Component:

    def __init__(self, id, model=None):
        if not (isinstance(self, Page)
                or id):
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

    @property
    def model(self):
        if self.__model is not None:
            return self.__model

        for curr in self.iter_parent():
            if isinstance(curr.model, mm.InheritableModel):
                self.__model = curr.model.wrap(self)
                return self.__model

    @model.setter
    def model(self, model):
        if not (model is None
                or isinstance(model, mm.Model)):
            self.__model = None
            raise ComponentError(self, f'{model!r} is not an instance of Model')
        # update model
        prev = self.__model
        self.__model = model
        # propagate to child models
        if (isinstance(self, MarkupContainer)
            and (prev
                 and isinstance(prev, mm.InheritableModel))):
            queue = collections.deque((self,))
            while queue:
                c = queue.pop()
                # reset model
                if (isinstance(c.model, mm.WrapModel)
                    and c.model.wrapped_model is prev):
                    c.model = None
                # push children
                if isinstance(c, MarkupContainer):
                    queue.extend(reversed(c.children))

    @property
    def model_object(self):
        return self.model.object if self.model is not None else None

    @model_object.setter
    def model_object(self, object):
        if self.model is None:
            raise ComponentError(self, 'model is not set')
        self.model.object = object

    @property
    def app(self):
        return local.app()

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
        for o in args:
            if isinstance(o, Behavior):
                self.behaviors.append(o)
                o.component = self
        return self

    def converter_for(self, value):
        return self.config['ayame.converter.registry'].converter_for(value)

    def element(self):
        # find MarkupContainer which has markup
        path = [self.id]
        for par in self.iter_parent():
            if par.has_markup:
                break
            path.append(par.id)
        else:
            return
        path.reverse()
        # find form element
        m = par.load_markup()
        if m.root is None:
            # markup is empty
            return
        el = m.root
        while path:
            for el, _ in el.walk():
                if el.attrib.get(markup.AYAME_ID) == path[0]:
                    break
            else:
                return
            del path[0]
        return el

    def forward(self, *args, **kwargs):
        self.app.forward(*args, **kwargs)

    def iter_parent(self, cls=None):
        curr = self.parent
        if cls is None:
            while curr is not None:
                yield curr
                curr = curr.parent
        else:
            while curr is not None:
                yield curr
                if isinstance(curr, cls):
                    return
                curr = curr.parent
            raise ComponentError(self, f"component is not attached to '{util.fqon_of(cls)}'")

    def model_object_as_string(self):
        if (o := self.model_object) is not None:
            if not isinstance(o, str):
                o = self.converter_for(o).to_string(o)
            return html.escape(o) if self.escape_model_string else o
        return ''

    def page(self):
        if isinstance(self, Page):
            return self
        for par in self.iter_parent(Page):
            pass
        return par

    def path(self):
        lis = [self]
        lis.extend(self.iter_parent())
        if isinstance(lis[-1], Page):
            del lis[-1]
        return ':'.join(c.id for c in reversed(lis))

    def redirect(self, *args, **kwargs):
        self.app.redirect(*args, **kwargs)

    def fire(self):
        if (self.request.path == self.path()
            and self.visible):
            self.on_fire()

    def on_fire(self):
        pass

    def render(self, element):
        self.on_configure()
        if self.visible:
            self.on_before_render()
            rv = self.on_render(element)
            self.on_after_render()
            return rv

    def on_configure(self):
        for b in self.behaviors:
            b.on_configure(self)

    def on_before_render(self):
        for b in self.behaviors:
            b.on_before_render(self)

    def on_render(self, element):
        for b in self.behaviors:
            b.on_component(self, element)
        return element

    def on_after_render(self):
        for b in self.behaviors:
            b.on_after_render(self)

    def tr(self, key, component=None):
        return self.config['ayame.i18n.localizer'].get(component if component is not None else self, self.request.locale, key)

    def uri_for(self, *args, **kwargs):
        return self.app.uri_for(*args, **kwargs)


class MarkupContainer(Component):

    markup_type = markup.MarkupType('.html', 'text/html', ())

    def __init__(self, id, model=None):
        super().__init__(id, model)
        self.children = []
        self.has_markup = False
        self._ref = {}
        self.__head = None

    @property
    def head(self):
        if self.__head is None:
            raise RenderingError(self, "'head' element is not found")
        return self.__head

    @head.setter
    def head(self, head):
        self.__head = head

    def add(self, *args):
        for o in args:
            if isinstance(o, Component):
                if o.id in self._ref:
                    raise ComponentError(self, f"component for '{o.id}' already exists")
                self.children.append(o)
                self._ref[o.id] = o
                o.parent = self
            else:
                super().add(o)
        return self

    def find(self, path):
        if not path:
            return self
        p = path.split(':', 1)
        id, tail = p[0], p[1] if len(p) > 1 else None
        if (c := self._ref.get(id)) is not None:
            return c.find(tail) if isinstance(c, MarkupContainer) else c
        raise ComponentError(self, f"component for '{path}' is not found")

    def walk(self, step=None):
        queue = collections.deque(((self, 0),))
        while queue:
            component, depth = queue.pop()
            yield component, depth
            # push child components
            if (isinstance(component, MarkupContainer)
                and (step is None
                     or step(component, depth))):
                queue.extend((c, depth + 1)
                             for c in reversed(component.children))

    def fire(self):
        if self.request.path:
            # fire component
            try:
                if (c := self.find(self.request.path)).visible:
                    c.on_fire()
            except ComponentError:
                pass

    def on_configure(self):
        super().on_configure()
        for c in self.children:
            c.on_configure()

    def on_before_render(self):
        super().on_before_render()
        for c in self.children:
            if c.visible:
                c.on_before_render()

    def on_render(self, element):
        def push(queue, node):
            if isinstance(node, markup.Element):
                for i in range(len(node) - 1, -1, -1):
                    if isinstance((n := node[i]), markup.Element):
                        queue.append((node, i, n))

        def pop_while(queue, parent):
            while queue:
                v = queue.pop()
                if v[0] != parent:
                    queue.append(v)
                    break
                yield v

        # notify behaviors
        rv = super().on_render(element)

        queue = collections.deque()
        if isinstance(rv, markup.Element):
            queue.append((None, -1, rv))
        while queue:
            parent, i, el = queue.pop()
            iv = self.on_render_element(el)
            if isinstance(iv, markup.Element):
                ayame_id, iv = self.on_render_attrib(iv)
            else:
                ayame_id = None
            if ayame_id is None:
                if isinstance(iv, markup.Element):
                    # there is no associated component
                    push(queue, el)
                    continue
                elif (isinstance(iv, collections.abc.Iterable)
                      and not isinstance(iv, str)):
                    # replace ayame element (parent)
                    if parent is None:
                        rv = iv
                    else:
                        parent.children[i:i+1] = iv
                    # assign indices to rendered elements
                    data = [(parent, i + j, v)
                            for j, v in enumerate(iv)
                            if isinstance(v, markup.Element)]
                    # update indices (increase)
                    amt = len(iv) - 1
                    data.extend((v[0], v[1] + amt, v[2])
                                for v in pop_while(queue, parent))
                    # replace ayame element (queue)
                    queue.extend(reversed(data))
                    continue

            if parent is None:
                # replace element itself
                if iv is None:
                    rv = ''
                else:
                    rv = iv
                    push(queue, rv)
            elif iv is None:
                # remove element
                del parent.children[i]
                # update indices (decrease)
                queue.extend(reversed([(v[0], v[1] - 1, v[2])
                                       for v in pop_while(queue, parent)]))
            elif (isinstance(iv, (markup.Element, str))
                  or not isinstance(iv, collections.abc.Iterable)):
                # replace element
                parent.children[i] = iv
                push(queue, iv)
            else:
                # replace element
                parent.children[i:i+1] = iv
                # update indices (increase)
                amt = len(iv) - 1
                queue.extend(reversed([(v[0], v[1] + amt, v[2])
                                       for v in pop_while(queue, parent)]))
                for v in iv:
                    push(queue, v)
        return rv

    def on_render_element(self, element):
        def get(e, a, keep=True):
            if a in e.attrib:
                return e.attrib[a] if keep else e.attrib.pop(a)
            raise RenderingError(self, f"'ayame:{a.name}' attribute is required for 'ayame:{e.qname.name}' element")

        if element.qname.ns_uri != markup.AYAME_NS:
            return element
        elif element.qname == markup.AYAME_CONTAINER:
            self.find(get(element, markup.AYAME_ID)).render_body_only = True
            return element
        elif element.qname == markup.AYAME_ENCLOSURE:
            c = self.find(get(element, markup.AYAME_CHILD))
            return element.children if c.visible else None
        elif element.qname == markup.AYAME_MESSAGE:
            mc = _MessageContainer(util.new_token()[:7], get(element, markup.AYAME_KEY, False))
            self.add(mc)
            element.attrib[markup.AYAME_ID] = mc.id
            return element
        raise RenderingError(self, f"unknown element 'ayame:{element.qname.name}'")

    def on_render_attrib(self, element):
        ayame_id = element.attrib.get(markup.AYAME_ID)
        if markup.AYAME_MESSAGE in element.attrib:
            # prepare AttributeModifier
            if ayame_id is not None:
                self.find(ayame_id).add(_AttributeLocalizer())
            else:
                ayame_id = util.new_token()[:7]
                self.add(_MessageContainer(ayame_id))
                element.attrib[markup.AYAME_ID] = ayame_id
        # render component
        if ayame_id is not None:
            return self.render_component(element)
        return None, element

    def render_component(self, element):
        # retrieve ayame:id attribute
        ayame_id = None
        for a in tuple(element.attrib):
            if not (isinstance(a, markup.QName)
                    and a.ns_uri == markup.AYAME_NS):
                continue
            elif a.name == 'id':
                ayame_id = element.attrib.pop(a)
            elif a.name != 'message':
                raise RenderingError(self, f"unknown attribute 'ayame:{a.name}'")
        if ayame_id is None:
            return None, element
        # find component
        c = self.find(ayame_id)
        if not c.visible:
            return ayame_id, None
        # render component
        rv = c.on_render(element)
        return ayame_id, rv.children if c.render_body_only and isinstance(rv, markup.Element) else rv

    def on_after_render(self):
        super().on_after_render()
        for c in self.children:
            if c.visible:
                c.on_after_render()

    def load_markup(self):
        def step(el, _):
            return el.qname not in (markup.AYAME_CHILD, markup.AYAME_HEAD)

        rl = self.config['ayame.resource.loader']
        ml = self.config['ayame.markup.loader']()
        enc = self.config['ayame.markup.encoding']
        sep = self.config['ayame.markup.separator']
        cache = self.config['ayame.markup.cache']
        cls = type(self)
        extra_head = []
        ayame_head = ayame_child = None
        while True:
            if cls.markup_type.scope:
                path = f'{sep.join(c.__name__ for c in cls.markup_type.scope + (cls,))}{cls.markup_type.extension}'
            else:
                path = cls.markup_type.extension
            key = f'{cls.__name__}:{path}'
            try:
                mtime, m = cache[key]
            except KeyError:
                mtime = -1
            try:
                if (r := rl.load(cls, path)).mtime > mtime:
                    with r.open(enc) as fp:
                        m = ml.load(cls, fp)
                    cache[key] = (r.mtime, m)
            except Exception:
                try:
                    del cache[key]
                except KeyError:
                    pass
                raise
            # m will be modified, so it should be copied
            m = m.copy()
            if m.root is None:
                # markup is empty
                break

            stack = []
            ayame_head = ayame_extend = None
            for el, depth in m.root.walk(step=step):
                stack[depth:] = (el,)
                if el.qname == markup.AYAME_EXTEND:
                    if ayame_extend is None:
                        # resolve superclass
                        supercls = None
                        for c in cls.__bases__:
                            if (not issubclass(c, MarkupContainer)
                                or c is MarkupContainer):
                                continue
                            elif supercls is not None:
                                raise AyameError('does not support multiple inheritance')
                            supercls = c
                        if supercls is None:
                            raise AyameError(f"superclass of '{util.fqon_of(cls)}' is not found")
                        cls = supercls
                        ayame_extend = el
                elif el.qname == markup.AYAME_CHILD:
                    if ayame_child is not None:
                        # merge submarkup into supermarkup
                        if len(stack) < 2:
                            raise RenderingError(cls, "'ayame:child' element cannot be the root element")
                        parent = stack[-2]
                        i = parent.children.index(el)
                        parent.children[i:i+1] = ayame_child
                        ayame_child = None
                elif el.qname == markup.AYAME_HEAD:
                    if ('html' in m.lang
                        and ayame_head is None):
                        ayame_head = el
            if ayame_child is not None:
                raise RenderingError(cls, "'ayame:child' element is not found")
            elif ayame_extend is None:
                # ayame:extend element is not found
                break
            # for ayame:child element in supermarkup
            ayame_child = ayame_extend.children
            # merge ayame:head element
            if ayame_head is not None:
                extra_head = ayame_head.children + extra_head
        # merge ayame:head element into supermarkup
        if extra_head:
            if ayame_head is None:
                # merge to head element
                for node in m.root.children:
                    if (isinstance(node, markup.Element)
                        and node.qname == markup.HEAD):
                        node.type = markup.Element.OPEN
                        node.extend(extra_head)
                        break
                else:
                    raise RenderingError(cls, "'head' element is not found")
            else:
                # merge to ayame:head element
                ayame_head.extend(extra_head)
        return m

    def find_head(self, root):
        if not (isinstance(root, markup.Element)
                and root.qname == markup.HTML):
            raise RenderingError(self, "root element is not 'html'")

        for node in root.children:
            if (isinstance(node, markup.Element)
                and node.qname == markup.HEAD):
                node.type = markup.Element.OPEN
                return node


class _MessageContainer(MarkupContainer):

    def __init__(self, id, key=None):
        if key is not None:
            # ayame:message element
            super().__init__(id, mm.Model(key))
            self.render_body_only = True
        else:
            # ayame:message attribute
            super().__init__(id)
            self.add(_AttributeLocalizer())

    def on_render(self, element):
        if (k := self.model_object) is not None:
            if (v := self.parent.tr(k)) is not None:
                element.children[:] = (v,)
                return element
            raise RenderingError(self.parent, f"no value found for ayame:message with key '{k}'")
        # notify behaviors and render components
        return super().on_render(element)


class Page(MarkupContainer):

    def __init__(self):
        super().__init__('')
        self.has_markup = True
        self.status = http.OK.status
        self.__headers = []
        self.headers = wsgiref.headers.Headers(self.__headers)

    def __call__(self):
        self.fire()
        # load markup and render components
        if (m := self.load_markup()).root is not None:
            # find head element for ayame:head element
            self.head = self.find_head(m.root)
            m.root = super().render(m.root)
            # remove ayame namespace from root element
            for pfx in tuple(m.root.ns):
                if m.root.ns[pfx] == markup.AYAME_NS:
                    del m.root.ns[pfx]
            # render markup
            mr = self.config['ayame.markup.renderer']()
            pretty = self.config['ayame.markup.pretty']
            content = mr.render(self, m, pretty=pretty)
        else:
            # markup is empty
            content = b''
        # HTTP headers
        self.headers['Content-Type'] = f'{self.markup_type.mime_type}; charset=UTF-8'
        self.headers['Content-Length'] = str(len(content))
        return self.status, self.__headers, [content]


class Behavior:

    def __init__(self):
        self.component = None

    @property
    def app(self):
        return local.app()

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

    def on_configure(self, component):
        pass

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
        super().__init__()
        self._attr = attr
        self._model = model

    def on_component(self, component, element):
        a = self._attr if isinstance(self._attr, markup.QName) else markup.QName(element.qname.ns_uri, self._attr)
        v = self._model.object if self._model is not None else None

        if (v := self.new_value(element.attrib.get(a), v)) is not None:
            element.attrib[a] = v
        elif a in element.attrib:
            del element.attrib[a]

    def new_value(self, value, new_value):
        return new_value


class _AttributeLocalizer(Behavior):

    def on_component(self, component, element):
        for s in v.split(',') if (v := element.attrib.pop(markup.AYAME_MESSAGE)) else []:
            try:
                name, key = s.rsplit(':', 1)
            except ValueError:
                raise RenderingError(component, 'invalid value is found in ayame:message attribute')
            if (v := component.tr(key)) is not None:
                element.attrib[markup.QName(element.qname.ns_uri, name)] = v


class nested:

    def __init__(self, attr):
        if (not isinstance(attr, type)
            or not issubclass(attr, MarkupContainer)
            or attr is MarkupContainer):
            raise AyameError(f"'{util.fqon_of(attr)}' is not a subclass of MarkupContainer")
        self._attr = attr
        self._arranged = False

    def __get__(self, instance, owner):
        attr = self._attr
        if (not self._arranged
            and issubclass(owner, MarkupContainer)):
            attr.markup_type = markup.MarkupType(attr.markup_type.extension,
                                                 attr.markup_type.mime_type,
                                                 owner.markup_type.scope + (owner,))
            self._arranged = True
        return attr
