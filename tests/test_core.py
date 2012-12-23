#
# test_core
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

from contextlib import contextmanager
import io

from nose.tools import assert_raises, eq_, ok_

from ayame import basic, core, http, local, markup, model, uri
from ayame import app as _app
from ayame.exception import AyameError, ComponentError, RenderingError


@contextmanager
def application(environ=None):
    app = _app.Ayame(__name__)
    try:
        ctx = local.push(app, environ)
        if environ is not None:
            ctx.request = app.config['ayame.class.Request'](environ, {})
        yield
    finally:
        local.pop()


def assert_ws(element, i):
    ok_(isinstance(element[i], basestring))
    eq_(element[i].strip(), '')


def test_component():
    assert_raises(ComponentError, core.Component, None)

    c = core.Component('a')
    eq_(c.id, 'a')
    eq_(c.model, None)
    eq_(c.model_object, None)
    assert_raises(ComponentError, setattr, c, 'model_object', '')
    assert_raises(AyameError, lambda: c.app)
    assert_raises(AyameError, lambda: c.config)
    assert_raises(AyameError, lambda: c.environ)
    assert_raises(AyameError, lambda: c.request)
    assert_raises(AyameError, lambda: c.session)
    assert_raises(AyameError, lambda: c.forward(c))
    assert_raises(AyameError, lambda: c.redirect(c))
    assert_raises(AyameError, lambda: c.tr('key'))
    assert_raises(AyameError, lambda: c.uri_for(c))
    assert_raises(ComponentError, c.page)
    eq_(c.path(), 'a')
    eq_(c.render(''), '')


def test_component_with_model():
    assert_raises(ComponentError, core.Component, '1', '')

    m = model.Model(None)
    eq_(m.object, None)
    c = core.Component('a', m)
    eq_(c.id, 'a')
    eq_(c.model, m)
    eq_(c.model.object, None)
    eq_(c.model_object, None)
    c.model.object = True
    eq_(c.model, m)
    eq_(c.model.object, True)
    eq_(c.model_object, True)
    c.model_object = False
    eq_(c.model, m)
    eq_(c.model.object, False)
    eq_(c.model_object, False)
    assert_raises(AyameError, lambda: c.app)
    assert_raises(AyameError, lambda: c.config)
    assert_raises(AyameError, lambda: c.environ)
    assert_raises(AyameError, lambda: c.request)
    assert_raises(AyameError, lambda: c.session)
    assert_raises(AyameError, lambda: c.forward(c))
    assert_raises(AyameError, lambda: c.redirect(c))
    assert_raises(AyameError, lambda: c.tr('key'))
    assert_raises(AyameError, lambda: c.uri_for(c))
    assert_raises(ComponentError, c.page)
    eq_(c.path(), 'a')
    eq_(c.render(''), '')

    m = model.Model('&<>')
    eq_(m.object, '&<>')
    c = core.Component('a', m)
    eq_(c.id, 'a')
    eq_(c.model, m)
    eq_(c.model_object, '&<>')
    eq_(c.model_object_as_string(), '&amp;&lt;&gt;')
    c.escape_model_string = False
    eq_(c.model_object, '&<>')
    eq_(c.model_object_as_string(), '&<>')


def test_markup_container():
    mc = core.MarkupContainer('a')
    assert_raises(ComponentError, mc.page)
    eq_(mc.path(), 'a')
    eq_(mc.children, [])
    eq_(mc.find(None), mc)
    eq_(mc.find(''), mc)
    it = mc.walk()
    eq_(next(it), (mc, 0))
    assert_raises(StopIteration, next, it)

    b1 = core.Component('b1')
    mc.add(b1)
    assert_raises(ComponentError, b1.page)
    eq_(b1.path(), 'a:b1')
    eq_(mc.children, [b1])
    eq_(mc.find('b1'), b1)
    assert_raises(ComponentError, mc.add, b1)
    b2 = core.MarkupContainer('b2')
    mc.add(b2)
    assert_raises(ComponentError, b2.page)
    eq_(b2.path(), 'a:b2')
    eq_(mc.children, [b1, b2])
    eq_(mc.find('b2'), b2)
    assert_raises(ComponentError, mc.add, b2)
    it = mc.walk()
    eq_(next(it), (mc, 0))
    eq_(next(it), (b1, 1))
    eq_(next(it), (b2, 1))
    assert_raises(StopIteration, next, it)

    c1 = core.Component('c1')
    b2.add(c1)
    assert_raises(ComponentError, c1.page)
    eq_(c1.path(), 'a:b2:c1')
    eq_(b2.children, [c1])
    eq_(mc.find('b2:c1'), c1)
    assert_raises(ComponentError, b2.add, c1)
    c2 = core.MarkupContainer('c2')
    b2.add(c2)
    assert_raises(ComponentError, c2.page)
    eq_(c2.path(), 'a:b2:c2')
    eq_(b2.children, [c1, c2])
    eq_(mc.find('b2:c2'), c2)
    assert_raises(ComponentError, b2.add, c2)
    it = mc.walk()
    eq_(next(it), (mc, 0))
    eq_(next(it), (b1, 1))
    eq_(next(it), (b2, 1))
    eq_(next(it), (c1, 2))
    eq_(next(it), (c2, 2))
    assert_raises(StopIteration, next, it)
    it = mc.walk(step=lambda component, *args: component != b2)
    eq_(next(it), (mc, 0))
    eq_(next(it), (b1, 1))
    eq_(next(it), (b2, 1))
    assert_raises(StopIteration, next, it)

    eq_(mc.render(''), '')


def test_render_children():
    # no child component
    root = markup.Element(markup.QName('', 'root'))
    mc = core.MarkupContainer('a')
    eq_(mc.render(root), root)

    # unknown ayame attribute
    root = markup.Element(markup.QName('', 'root'))
    root.attrib[markup.AYAME_ID] = 'b'
    root.attrib[markup.QName(markup.AYAME_NS, 'spam')] = ''
    mc = core.MarkupContainer('a')
    mc.add(core.Component('b'))
    assert_raises(RenderingError, mc.render, root)

    # component is not found
    root = markup.Element(markup.QName('', 'root'))
    root.attrib[markup.AYAME_ID] = 'c'
    root.attrib[markup.QName('', 'id')] = 'c'
    mc = core.MarkupContainer('a')
    mc.add(core.Component('b'))
    assert_raises(ComponentError, mc.render, root)

    # replace root element
    class Component(core.Component):
        def on_render(self, element):
            return None
    root = markup.Element(markup.QName('', 'root'))
    root.attrib[markup.AYAME_ID] = 'b'
    mc = core.MarkupContainer('a')
    mc.add(Component('b'))
    eq_(mc.render(root), '')

    # remove element
    class Component(core.Component):
        def on_render(self, element):
            return None
    root = markup.Element(markup.QName('', 'root'))
    root.append('>')
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.append(a)
    root.append('<')
    mc = core.MarkupContainer('a')
    mc.add(Component('b'))

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(root.children, ['>', '<'])

    # replace element by string
    class Component(core.Component):
        def on_render(self, element):
            return ''
    root = markup.Element(markup.QName('', 'root'))
    root.append('>')
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.append(a)
    root.append('<')
    mc = core.MarkupContainer('a')
    mc.add(Component('b'))

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(root.children, ['>', '<'])

    # replace element by list
    class Component(core.Component):
        def on_render(self, element):
            return ['>>', '!', '<<']
    root = markup.Element(markup.QName('', 'root'))
    root.append('>')
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.append(a)
    root.append('<')
    mc = core.MarkupContainer('a')
    mc.add(Component('b'))

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(root.children, ['>', '>>', '!', '<<', '<'])


def test_behavior():
    b = core.Behavior()
    assert_raises(AyameError, lambda: b.app)
    assert_raises(AyameError, lambda: b.config)
    assert_raises(AyameError, lambda: b.environ)
    assert_raises(AyameError, lambda: b.request)
    assert_raises(AyameError, lambda: b.session)
    assert_raises(AyameError, lambda: b.forward(b))
    assert_raises(AyameError, lambda: b.redirect(b))
    assert_raises(AyameError, lambda: b.uri_for(b))

    class Behavior(core.Behavior):
        def on_before_render(self, component):
            super(Behavior, self).on_before_render(component)
            component.model_object.append('before-render')
        def on_component(self, component, element):
            super(Behavior, self).on_component(component, element)
            component.model_object.append('component')
        def on_after_render(self, component):
            super(Behavior, self).on_after_render(component)
            component.model_object.append('after-render')

    # component
    c = core.Component('a', model.Model([]))
    c.add(Behavior())
    eq_(len(c.behaviors), 1)
    eq_(c.behaviors[0].component, c)

    eq_(c.render(None), None)
    eq_(c.model_object, ['before-render', 'component', 'after-render'])

    # markup container
    mc = core.MarkupContainer('a', model.Model([]))
    mc.add(Behavior())
    eq_(len(c.behaviors), 1)
    eq_(mc.behaviors[0].component, mc)

    eq_(mc.render(None), None)
    eq_(mc.model_object, ['before-render', 'component', 'after-render'])


def test_attribute_modifier():
    # component
    root = markup.Element(markup.QName('', 'root'))
    root.attrib[markup.QName('', 'a')] = ''
    c = core.Component('a')
    c.add(core.AttributeModifier('a', model.Model(None)))
    c.add(core.AttributeModifier(markup.QName('', 'b'), model.Model(None)))
    c.add(core.AttributeModifier('c', model.Model('')))
    eq_(len(c.behaviors), 3)
    eq_(c.behaviors[0].component, c)
    eq_(c.behaviors[1].component, c)
    eq_(c.behaviors[2].component, c)

    root = c.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {markup.QName('', 'c'): ''})
    eq_(root.children, [])

    # markup container
    root = markup.Element(markup.QName('', 'root'))
    root.attrib[markup.QName('', 'a')] = ''
    mc = core.MarkupContainer('a')
    mc.add(core.AttributeModifier('a', model.Model(None)))
    mc.add(core.AttributeModifier(markup.QName('', 'b'), model.Model(None)))
    mc.add(core.AttributeModifier('c', model.Model('')))
    eq_(len(mc.behaviors), 3)
    eq_(mc.behaviors[0].component, mc)
    eq_(mc.behaviors[1].component, mc)
    eq_(mc.behaviors[2].component, mc)

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {markup.QName('', 'c'): ''})
    eq_(root.children, [])


def test_render_unknown_ayame_element():
    root = markup.Element(markup.QName(markup.AYAME_NS, 'spam'))
    mc = core.MarkupContainer('a')
    assert_raises(RenderingError, mc.render, root)


def test_render_ayame_container():
    # ayame:id is not found
    root = markup.Element(markup.QName('', 'root'))
    container = markup.Element(markup.AYAME_CONTAINER)
    root.append(container)
    mc = core.MarkupContainer('a')
    assert_raises(RenderingError, mc.render, root)

    # component is not found
    root = markup.Element(markup.QName('', 'root'))
    container = markup.Element(markup.AYAME_CONTAINER)
    container.attrib[markup.AYAME_ID] = 'b'
    root.append(container)
    mc = core.MarkupContainer('a')
    assert_raises(ComponentError, mc.render, root)

    # ayame:container
    root = markup.Element(markup.QName('', 'root'))
    container = markup.Element(markup.AYAME_CONTAINER)
    container.attrib[markup.AYAME_ID] = 'b'
    root.append(container)
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'c'
    container.append(a)
    mc = core.MarkupContainer('a')
    def populate_item(li):
        li.add(basic.Label('c', li.model_object))
    mc.add(basic.ListView('b', [str(i) for i in range(3)], populate_item))

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(len(root), 3)

    a = root[0]
    eq_(a.qname, markup.QName('', 'a'))
    eq_(a.attrib, {})
    eq_(a.children, ['0'])

    a = root[1]
    eq_(a.qname, markup.QName('', 'a'))
    eq_(a.attrib, {})
    eq_(a.children, ['1'])

    a = root[2]
    eq_(a.qname, markup.QName('', 'a'))
    eq_(a.attrib, {})
    eq_(a.children, ['2'])


def test_render_ayame_enclosure():
    # ayame:child is not found
    root = markup.Element(markup.QName('', 'root'))
    enclosure = markup.Element(markup.AYAME_ENCLOSURE)
    root.append(enclosure)
    mc = core.MarkupContainer('a')
    assert_raises(RenderingError, mc.render, root)

    # component is not found
    root = markup.Element(markup.QName('', 'root'))
    enclosure = markup.Element(markup.AYAME_ENCLOSURE)
    enclosure.attrib[markup.AYAME_CHILD] = 'b'
    root.append(enclosure)
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    enclosure.append(a)
    mc = core.MarkupContainer('a')
    assert_raises(ComponentError, mc.render, root)

    # ayame:enclosure with visible component
    root = markup.Element(markup.QName('', 'root'))
    a = markup.Element(markup.QName('', 'a'))
    root.append(a)
    enclosure = markup.Element(markup.AYAME_ENCLOSURE)
    enclosure.attrib[markup.AYAME_CHILD] = 'b1'
    a.append(enclosure)
    b = markup.Element(markup.QName('', 'b'))
    b.attrib[markup.AYAME_ID] = 'b1'
    enclosure.append(b)
    b = markup.Element(markup.QName('', 'b'))
    a.append(b)
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b2'
    root.append(a)
    mc = core.MarkupContainer('a')
    mc.add(basic.Label('b1', 'spam'))
    mc.add(basic.Label('b2', 'eggs'))

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(len(root), 2)

    a = root[0]
    eq_(a.qname, markup.QName('', 'a'))
    eq_(a.attrib, {})
    eq_(len(a), 2)

    b = a[0]
    eq_(b.qname, markup.QName('', 'b'))
    eq_(b.attrib, {})
    eq_(b.children, ['spam'])

    b = a[1]
    eq_(b.qname, markup.QName('', 'b'))
    eq_(b.attrib, {})
    eq_(b.children, [])

    a = root[1]
    eq_(a.qname, markup.QName('', 'a'))
    eq_(a.attrib, {})
    eq_(a.children, ['eggs'])

    # ayame:enclosure with invisible component
    root = markup.Element(markup.QName('', 'root'))
    a = markup.Element(markup.QName('', 'a'))
    root.append(a)
    enclosure = markup.Element(markup.AYAME_ENCLOSURE)
    enclosure.attrib[markup.AYAME_CHILD] = 'b1'
    a.append(enclosure)
    b = markup.Element(markup.QName('', 'b'))
    b.attrib[markup.AYAME_ID] = 'b1'
    enclosure.append(b)
    b = markup.Element(markup.QName('', 'b'))
    a.append(b)
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b2'
    root.append(a)
    mc = core.MarkupContainer('a')
    mc.add(basic.Label('b1', 'spam'))
    mc.add(basic.Label('b2', 'eggs'))
    mc.find('b1').visible = False
    mc.find('b2').visible = False

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(len(root), 1)

    a = root[0]
    eq_(a.qname, markup.QName('', 'a'))
    eq_(a.attrib, {})
    eq_(len(a), 1)

    b = a[0]
    eq_(b.qname, markup.QName('', 'b'))
    eq_(b.attrib, {})
    eq_(b.children, [])


def test_markup_inheritance():
    class Spam(core.MarkupContainer):
        pass
    class Eggs(Spam):
        pass
    class Ham(Eggs):
        pass

    class Toast(core.MarkupContainer):
        pass

    class Beans(core.MarkupContainer):
        pass

    class Bacon(core.MarkupContainer):
        pass

    # markup inheritance
    with application():
        mc = Ham('a')
        m = mc.load_markup()
    eq_(m.xml_decl, {'version': '1.0'})
    eq_(m.lang, 'xhtml1')
    eq_(m.doctype, markup.XHTML1_STRICT)
    ok_(m.root)

    html = m.root
    eq_(html.qname, markup.QName(markup.XHTML_NS, 'html'))
    eq_(html.attrib, {})
    eq_(html.type, markup.Element.OPEN)
    eq_(html.ns, {'': markup.XHTML_NS,
                  'xml': markup.XML_NS,
                  'ayame': markup.AYAME_NS})
    eq_(len(html), 5)
    assert_ws(html, 0)
    assert_ws(html, 2)
    assert_ws(html, 4)

    head = html[1]
    eq_(head.qname, markup.QName(markup.XHTML_NS, 'head'))
    eq_(head.attrib, {})
    eq_(head.type, markup.Element.OPEN)
    eq_(head.ns, {})
    eq_(len(head), 11)
    assert_ws(head, 0)
    assert_ws(head, 2)
    assert_ws(head, 4)
    assert_ws(head, 5)
    assert_ws(head, 7)
    assert_ws(head, 8)
    assert_ws(head, 10)

    title = head[1]
    eq_(title.qname, markup.QName(markup.XHTML_NS, 'title'))
    eq_(title.attrib, {})
    eq_(title.type, markup.Element.OPEN)
    eq_(title.ns, {})
    eq_(len(title), 1)
    eq_(title.children, ['Spam'])

    meta = head[3]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Spam'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(meta.children, [])

    meta = head[6]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Eggs'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(meta.children, [])

    meta = head[9]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Ham'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(meta.children, [])

    body = html[3]
    eq_(body.qname, markup.QName(markup.XHTML_NS, 'body'))
    eq_(body.attrib, {})
    eq_(body.type, markup.Element.OPEN)
    eq_(body.ns, {})
    eq_(len(body), 13)
    assert_ws(body, 0)
    assert_ws(body, 2)
    assert_ws(body, 3)
    assert_ws(body, 5)
    assert_ws(body, 6)
    assert_ws(body, 8)
    assert_ws(body, 9)
    assert_ws(body, 10)
    assert_ws(body, 12)

    p = body[1]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['before ayame:child (Spam)'])

    p = body[4]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['inside ayame:extend (Eggs)'])

    p = body[7]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['inside ayame:extend (Ham)'])

    p = body[11]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['after ayame:child (Spam)'])

    # submarkup is empty
    class Sausage(Spam):
        pass
    with application():
        mc = Sausage('a')
        m = mc.load_markup()
    eq_(m.xml_decl, {'version': '1.0'})
    eq_(m.lang, 'xhtml1')
    eq_(m.doctype, markup.XHTML1_STRICT)
    ok_(m.root)

    html = m.root
    eq_(html.qname, markup.QName(markup.XHTML_NS, 'html'))
    eq_(html.attrib, {})
    eq_(html.type, markup.Element.OPEN)
    eq_(html.ns, {'': markup.XHTML_NS,
                  'xml': markup.XML_NS,
                  'ayame': markup.AYAME_NS})
    eq_(len(html), 5)
    assert_ws(html, 0)
    assert_ws(html, 2)
    assert_ws(html, 4)

    head = html[1]
    eq_(head.qname, markup.QName(markup.XHTML_NS, 'head'))
    eq_(head.attrib, {})
    eq_(head.type, markup.Element.OPEN)
    eq_(head.ns, {})
    eq_(len(head), 8)
    assert_ws(head, 0)
    assert_ws(head, 2)
    assert_ws(head, 4)
    assert_ws(head, 5)
    assert_ws(head, 7)

    title = head[1]
    eq_(title.qname, markup.QName(markup.XHTML_NS, 'title'))
    eq_(title.attrib, {})
    eq_(title.type, markup.Element.OPEN)
    eq_(title.ns, {})
    eq_(title.children, ['Spam'])

    meta = head[3]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Spam'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(meta.children, [])

    meta = head[6]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Sausage'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(meta.children, [])

    body = html[3]
    eq_(body.qname, markup.QName(markup.XHTML_NS, 'body'))
    eq_(body.attrib, {})
    eq_(body.type, markup.Element.OPEN)
    eq_(body.ns, {})
    eq_(len(body), 6)
    assert_ws(body, 0)
    assert_ws(body, 2)
    assert_ws(body, 3)
    assert_ws(body, 5)

    p = body[1]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['before ayame:child (Spam)'])

    p = body[4]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['after ayame:child (Spam)'])

    # merge ayame:head into ayame:head in supermarkup
    class Sausage(Bacon):
        pass
    with application():
        mc = Sausage('a')
        m = mc.load_markup()
    eq_(m.xml_decl, {'version': '1.0'})
    eq_(m.lang, 'xhtml1')
    eq_(m.doctype, markup.XHTML1_STRICT)
    ok_(m.root)

    html = m.root
    eq_(html.qname, markup.QName(markup.XHTML_NS, 'html'))
    eq_(html.attrib, {})
    eq_(html.type, markup.Element.OPEN)
    eq_(html.ns, {'': markup.XHTML_NS,
                  'xml': markup.XML_NS,
                  'ayame': markup.AYAME_NS})
    eq_(len(html), 5)
    assert_ws(html, 0)
    assert_ws(html, 2)
    assert_ws(html, 4)

    ayame_head = html[1]
    eq_(ayame_head.qname, markup.QName(markup.AYAME_NS, 'head'))
    eq_(ayame_head.attrib, {})
    eq_(ayame_head.type, markup.Element.OPEN)
    eq_(ayame_head.ns, {})
    eq_(len(ayame_head), 8)
    assert_ws(ayame_head, 0)
    assert_ws(ayame_head, 2)
    assert_ws(ayame_head, 4)
    assert_ws(ayame_head, 5)
    assert_ws(ayame_head, 7)

    title = ayame_head[1]
    eq_(title.qname, markup.QName(markup.XHTML_NS, 'title'))
    eq_(title.attrib, {})
    eq_(title.type, markup.Element.OPEN)
    eq_(title.ns, {})
    eq_(title.children, ['Bacon'])

    meta = ayame_head[3]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Bacon'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(meta.children, [])

    meta = ayame_head[6]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Sausage'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(meta.children, [])

    body = html[3]
    eq_(body.qname, markup.QName(markup.XHTML_NS, 'body'))
    eq_(body.attrib, {})
    eq_(body.type, markup.Element.OPEN)
    eq_(body.ns, {})
    eq_(len(body), 6)
    assert_ws(body, 0)
    assert_ws(body, 2)
    assert_ws(body, 3)
    assert_ws(body, 5)

    p = body[1]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['before ayame:child (Bacon)'])

    p = body[4]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['after ayame:child (Bacon)'])

    # superclass is not found
    class Sausage(core.MarkupContainer):
        pass
    with application():
        mc = Sausage('a')
        assert_raises(AyameError, mc.load_markup)

    # multiple inheritance
    class Sausage(Spam, Toast, Beans, Bacon):
        pass
    with application():
        mc = Sausage('a')
        assert_raises(AyameError, mc.load_markup)

    # ayame:child element is not found
    class Sausage(Toast):
        pass
    with application():
        mc = Sausage('a')
        assert_raises(RenderingError, mc.load_markup)

    # head element is not found
    class Sausage(Beans):
        pass
    with application():
        mc = Sausage('a')
        assert_raises(RenderingError, mc.load_markup)

    # ayame:child element is root element
    class Tomato(core.MarkupContainer):
        pass
    class Sausage(Tomato):
        pass
    with application():
        mc = Sausage('a')
        assert_raises(RenderingError, mc.load_markup)

    # empty markup
    class Lobster(core.MarkupContainer):
        pass
    class Sausage(Lobster):
        pass
    with application():
        mc = Sausage('a')
        m = mc.load_markup()
    eq_(m.xml_decl, {})
    eq_(m.lang, 'xhtml1')
    eq_(m.doctype, None)
    eq_(m.root, None)

    class Lobster(core.Page):
        pass
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET'}
    with application(environ):
        page = Lobster()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', '0')])
    eq_(content, b'')


def test_ayame_head():
    ayame_head = markup.Element(markup.AYAME_HEAD)
    h = markup.Element(markup.QName('', 'h'))
    ayame_head.append(h)

    class MarkupContainer(core.MarkupContainer):
        def on_render(self, element):
            self.push_ayame_head(ayame_head)
            return element

    # root element is not html
    root = markup.Element(markup.QName('', 'root'))
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.append(a)
    mc = core.MarkupContainer('a')
    mc.add(MarkupContainer('b'))
    assert_raises(RenderingError, mc.render, root)

    # head element is not found
    root = markup.Element(markup.HTML)
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.append(a)
    mc = core.MarkupContainer('a')
    mc.add(MarkupContainer('b'))
    assert_raises(RenderingError, mc.render, root)

    # push ayame:head
    root = markup.Element(markup.HTML)
    head = markup.Element(markup.HEAD)
    root.append(head)
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.append(a)
    mc = core.MarkupContainer('a')
    mc.add(MarkupContainer('b'))

    root = mc.render(root)
    eq_(root.qname, markup.HTML)
    eq_(root.attrib, {})
    eq_(len(root), 2)

    head = root[0]
    eq_(head.qname, markup.HEAD)
    eq_(head.attrib, {})
    eq_(head.type, markup.Element.OPEN)
    eq_(len(head), 1)

    h = head[0]
    eq_(h.qname, markup.QName('', 'h'))
    eq_(h.attrib, {})
    eq_(h.children, [])

    a = root[1]
    eq_(a.qname, markup.QName('', 'a'))
    eq_(a.attrib, {})
    eq_(a.children, [])


def test_failsafe():
    # MarkupContainer
    mc = core.MarkupContainer('a')
    a = markup.Element(markup.QName('', 'a'))
    assert_raises(RenderingError, mc.render_ayame_element, a)
    eq_(mc.render_component(a), (None, a))


def test_page():
    class SpamPage(core.Page):
        def __init__(self):
            super(SpamPage, self).__init__()
            self.add(basic.Label('message', u'Hello World!'))
            self.headers['Content-Type'] = 'text/plain'

    xhtml = ('<?xml version="1.0"?>\n'
             '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '
             '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
             '<html xmlns="{xhtml}">\n'
             '  <head>\n'
             '    <title>SpamPage</title>\n'
             '  </head>\n'
             '  <body>\n'
             '    <p>Hello World!</p>\n'
             '  </body>\n'
             '</html>\n').format(xhtml=markup.XHTML_NS)
    xhtml = xhtml.encode('utf-8')

    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET'}
    with application(environ):
        page = SpamPage()
        status, headers, content = page.render()
    eq_(page.page(), page)
    eq_(page.find('message').page(), page)
    eq_(page.path(), '')
    eq_(page.find('message').path(), 'message')
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)


def test_ignition_behavior():
    class EggsPage(core.Page):
        def __init__(self):
            super(EggsPage, self).__init__()
            self.model = model.CompoundModel({'clay1': 0,
                                              'clay2': 0})
            self.add(Clay('clay1'))
            self.add(core.MarkupContainer('obstacle'))
            self.find('obstacle').add(Clay('clay2'))

    class Clay(core.Component):
        def __init__(self, id, model=None):
            super(Clay, self).__init__(id, model)
            self.add(IgnitionBehavior())

    class IgnitionBehavior(core.IgnitionBehavior):
        def on_component(self, component, element):
            self.fire()
        def on_fire(self, component):
            super(IgnitionBehavior, self).on_fire(component)
            component.model_object += 1

    xhtml = ('<?xml version="1.0"?>\n'
             '{doctype}\n'
             '<html xmlns="{xhtml}">\n'
             '  <head>\n'
             '    <title>EggsPage</title>\n'
             '  </head>\n'
             '  <body>\n'
             '    <p>clay1</p>\n'
             '    <div>\n'
             '      <p>clay2</p>\n'
             '    </div>\n'
             '  </body>\n'
             '</html>\n').format(doctype=markup.XHTML1_STRICT,
                                 xhtml=markup.XHTML_NS)
    xhtml = xhtml.encode('utf-8')

    # GET
    query = '{}=clay1'.format(core.AYAME_PATH)
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET',
               'QUERY_STRING': uri.quote(query)}
    with application(environ):
        page = EggsPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)
    eq_(page.model_object, {'clay1': 1,
                            'clay2': 0})

    # duplicate ayame:path
    query = ('{0}=clay1&'
             '{0}=obstacle:clay2').format(core.AYAME_PATH)
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET',
               'QUERY_STRING': uri.quote(query)}
    with application(environ):
        page = EggsPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)
    eq_(page.model_object, {'clay1': 1,
                            'clay2': 0})

    # POST
    data = ('--ayame.core\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'obstacle:clay2\r\n'
            '--ayame.core--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.core',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = EggsPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)
    eq_(page.model_object, {'clay1': 0,
                            'clay2': 1})

    # duplicate ayame:path
    data = ('--ayame.core\r\n'
            'Content-Disposition: form-data; name="{0}"\r\n'
            '\r\n'
            'obstacle:clay2\r\n'
            '--ayame.core\r\n'
            'Content-Disposition: form-data; name="{0}"\r\n'
            '\r\n'
            'clay1\r\n'
            '--ayame.core--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.core',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = EggsPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)
    eq_(page.model_object, {'clay1': 0,
                            'clay2': 1})


def test_nested_class_markup():
    class HamPage(core.Page):
        pass
    class ToastPage(HamPage):
        markup_type = markup.MarkupType('.htm', 'text/html', ())
        @core.nested
        class NestedPage(HamPage):
            pass

    xhtml = ('<?xml version="1.0"?>\n'
             '{doctype}\n'
             '<html xmlns="{xhtml}">\n'
             '  <head>\n'
             '    <title>HamPage</title>\n'
             '  </head>\n'
             '  <body>\n'
             '    <p>ToastPage</p>\n'
             '  </body>\n'
             '</html>\n').format(doctype=markup.XHTML1_STRICT,
                                 xhtml=markup.XHTML_NS)
    xhtml = xhtml.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET'}
    with application(environ):
        page = ToastPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)

    xhtml = ('<?xml version="1.0"?>\n'
             '{doctype}\n'
             '<html xmlns="{xhtml}">\n'
             '  <head>\n'
             '    <title>HamPage</title>\n'
             '  </head>\n'
             '  <body>\n'
             '    <p>ToastPage.NestedPage</p>\n'
             '  </body>\n'
             '</html>\n').format(doctype=markup.XHTML1_STRICT,
                                 xhtml=markup.XHTML_NS)
    xhtml = xhtml.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET'}
    with application(environ):
        page = ToastPage.NestedPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)


def test_render_ayame_message_element():
    class BeansPage(core.Page):
        pass

    xhtml = ('<?xml version="1.0"?>\n'
             '{doctype}\n'
             '<html xmlns="{xhtml}">\n'
             '  <head>\n'
             '    <title>BeansPage</title>\n'
             '  </head>\n'
             '  <body>\n'
             '    <p>Hello World!</p>\n'
             '  </body>\n'
             '</html>\n').format(doctype=markup.XHTML1_STRICT,
                                 xhtml=markup.XHTML_NS)
    xhtml = xhtml.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(),
               'HTTP_ACCEPT_LANGUAGE': 'en',
               'REQUEST_METHOD': 'GET'}
    with application(environ):
        page = BeansPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)

    xhtml = (u'<?xml version="1.0"?>\n'
             u'{doctype}\n'
             u'<html xmlns="{xhtml}">\n'
             u'  <head>\n'
             u'    <title>BeansPage</title>\n'
             u'  </head>\n'
             u'  <body>\n'
             u'    <p>\u3053\u3093\u306b\u3061\u306f\u4e16\u754c</p>\n'
             u'  </body>\n'
             u'</html>\n').format(doctype=markup.XHTML1_STRICT,
                                  xhtml=markup.XHTML_NS)
    xhtml = xhtml.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(),
               'HTTP_ACCEPT_LANGUAGE': 'ja, en',
               'REQUEST_METHOD': 'GET'}
    with application(environ):
        page = BeansPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)

    # no value found for key
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET'}
    with application(environ):
        message = markup.Element(markup.AYAME_MESSAGE)
        message.attrib[markup.AYAME_KEY] = 'b'
        mc = core.MarkupContainer('a')
        assert_raises(RenderingError, mc.render, message)


def test_render_ayame_message_attribute():
    class BaconPage(core.Page):
        pass

    xhtml = ('<?xml version="1.0"?>\n'
             '{doctype}\n'
             '<html xmlns="{xhtml}">\n'
             '  <head>\n'
             '    <title>BaconPage</title>\n'
             '  </head>\n'
             '  <body>\n'
             '    <form action="#">\n'
             '      <div>\n'
             '        <input type="submit" value="Submit"/>\n'
             '      </div>\n'
             '    </form>\n'
             '  </body>\n'
             '</html>\n').format(doctype=markup.XHTML1_STRICT,
                                 xhtml=markup.XHTML_NS)
    xhtml = xhtml.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(),
               'HTTP_ACCEPT_LANGUAGE': 'en',
               'REQUEST_METHOD': 'GET'}
    with application(environ):
        page = BaconPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)

    xhtml = (u'<?xml version="1.0"?>\n'
             u'{doctype}\n'
             u'<html xmlns="{xhtml}">\n'
             u'  <head>\n'
             u'    <title>BaconPage</title>\n'
             u'  </head>\n'
             u'  <body>\n'
             u'    <form action="#">\n'
             u'      <div>\n'
             u'        <input type="submit" value="\u9001\u4fe1"/>\n'
             u'      </div>\n'
             u'    </form>\n'
             u'  </body>\n'
             u'</html>\n').format(doctype=markup.XHTML1_STRICT,
                                  xhtml=markup.XHTML_NS)
    xhtml = xhtml.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(),
               'HTTP_ACCEPT_LANGUAGE': 'ja, en',
               'REQUEST_METHOD': 'GET'}
    with application(environ):
        page = BaconPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)

    # invalid value for ayame:message attribute
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET'}
    with application(environ):
        root = markup.Element(markup.QName('', 'root'))
        root.attrib[markup.AYAME_ID] = 'b'
        root.attrib[markup.AYAME_MESSAGE] = 'id'
        mc = core.MarkupContainer('a')
        mc.add(core.Component('b'))
        assert_raises(RenderingError, mc.render, root)
