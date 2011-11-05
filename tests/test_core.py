#
# test_core
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

from __future__ import unicode_literals
import io
import os
import wsgiref.util

from nose.tools import assert_raises, eq_, ok_

from ayame import basic, core, http, markup
from ayame.exception import AyameError, ComponentError, RenderingError


def test_simple_app():
    class SimplePage(core.Page):
        pass

    app = core.Ayame(__name__)
    eq_(app._name, __name__)
    eq_(app._root, os.path.dirname(__file__))

    map = app.config['ayame.route.map']
    map.connect('/page', SimplePage)
    map.connect('/int', 0)

    # GET /page -> OK
    xhtml = ('<?xml version="1.0"?>\n'
             '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '
             '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
             '<html xmlns="{xhtml}">\n'
             '  <title>SimplePage</title>\n'
             '  <body>\n'
             '    <p>Hello World!</p>\n'
             '  </body>\n'
             '</html>\n').format(xhtml=markup.XHTML_NS)
    status, headers, exc_info, body = wsgi_call(app.make_app(),
                                                REQUEST_METHOD='GET',
                                                PATH_INFO='/page')
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', '255')])
    eq_(exc_info, None)
    eq_(body, xhtml)

    # GET /page?{query in EUC-JP} -> InternalServerError
    query = '\u3044\u308d\u306f'.encode('euc-jp')
    status, headers, exc_info, body = wsgi_call(app.make_app(),
                                                REQUEST_METHOD='GET',
                                                PATH_INFO='/page',
                                                QUERY_STRING=query)
    eq_(status, http.InternalServerError.status)
    eq_(headers, [])
    ok_(exc_info)
    eq_(body, [])

    # GET /int -> NotFound
    status, headers, exc_info, body = wsgi_call(app.make_app(),
                                                REQUEST_METHOD='GET',
                                                PATH_INFO='/int')
    eq_(status, http.NotFound.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', '263')])
    ok_(exc_info)
    ok_(body)

def wsgi_call(application, **kwargs):
    wsgi = {}

    def start_response(status, headers, exc_info=None):
        wsgi.update(status=status, headers=headers, exc_info=exc_info)

    environ = dict(kwargs)
    wsgiref.util.setup_testing_defaults(environ)
    data = application(environ, start_response)
    return wsgi['status'], wsgi['headers'], wsgi['exc_info'], data

def test_component():
    assert_raises(ComponentError, core.Component, None)

    c = core.Component('a')
    eq_(c.id, 'a')
    eq_(c.model, None)
    eq_(c.model_object, None)
    assert_raises(AyameError, lambda: c.app)
    assert_raises(AyameError, lambda: c.config)
    assert_raises(AyameError, lambda: c.environ)
    assert_raises(ComponentError, c.page)
    eq_(c.path(), 'a')
    eq_(c.render(''), '')

def test_component_with_model():
    assert_raises(ComponentError, core.Component, '1', '')

    m = core.Model(None)
    eq_(m.object, None)
    c = core.Component('a', m)
    eq_(c.id, 'a')
    eq_(c.model, m)
    eq_(c.model_object, None)
    assert_raises(AyameError, lambda: c.app)
    assert_raises(AyameError, lambda: c.config)
    assert_raises(AyameError, lambda: c.environ)
    assert_raises(ComponentError, c.page)
    eq_(c.path(), 'a')
    eq_(c.render(''), '')

    m = core.Model('&<>')
    eq_(m.object, '&<>')
    c = core.Component('a', m)
    eq_(c.id, 'a')
    eq_(c.model, m)
    eq_(c.model_object, '&amp;&lt;&gt;')
    c.escape_model_string = False
    eq_(c.model_object, '&<>')

def test_nested_model():
    inner = core.Model(None)
    outer = core.Model(inner)
    eq_(inner.object, None)
    eq_(outer.object, None)

def test_markup_container():
    mc = core.MarkupContainer('a')
    assert_raises(ComponentError, mc.page)
    eq_(mc.path(), 'a')
    eq_(len(mc.children), 0)
    eq_(mc.find(None), mc)
    eq_(mc.find(''), mc)

    b1 = core.Component('b1')
    mc.add(b1)
    assert_raises(ComponentError, mc.page)
    eq_(b1.path(), 'a:b1')
    eq_(len(mc.children), 1)
    eq_(mc.find('b1'), b1)
    assert_raises(ComponentError, mc.add, b1)

    b2 = core.MarkupContainer('b2')
    mc.add(b2)
    assert_raises(ComponentError, mc.page)
    eq_(b2.path(), 'a:b2')
    eq_(len(mc.children), 2)
    eq_(mc.find('b2'), b2)
    assert_raises(ComponentError, mc.add, b2)

    eq_(mc.render(''), '')

def test_compound_model():
    class Object(object):
        attr = 'attr'
    mc = core.MarkupContainer('a', core.CompoundModel(Object()))
    mc.add(core.Component('attr'))
    eq_(len(mc.children), 1)
    eq_(mc.find('attr').model.object, 'attr')

    class Object(object):
        def get_getter(self):
            return 'getter'
    mc = core.MarkupContainer('a', core.CompoundModel(Object()))
    mc.add(core.Component('getter'))
    eq_(len(mc.children), 1)
    eq_(mc.find('getter').model.object, 'getter')

    class Object(object):
        def __getitem__(self, key):
            if key == 'key':
                return 'key'
            raise KeyError(key)
    mc = core.MarkupContainer('a', core.CompoundModel(Object()))
    mc.add(core.Component('key'))
    eq_(len(mc.children), 1)
    eq_(mc.find('key').model.object, 'key')
    mc.model = core.CompoundModel(object())
    mc.find('key').model = None
    assert_raises(AttributeError, lambda: mc.find('key').model.object)

    mc = core.MarkupContainer('a', core.CompoundModel({'b': 'b', 'c': 'c'}))
    mc.add(core.MarkupContainer('b'))
    eq_(len(mc.children), 1)
    eq_(mc.find('b').model.object, 'b')
    mc.find('b').add(core.Component('c'))
    eq_(len(mc.children), 1)
    eq_(len(mc.find('b').children), 1)
    eq_(mc.find('b:c').model.object, 'c')

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
    root.children.append('')
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.children.append(a)
    root.children.append('')
    mc = core.MarkupContainer('a')
    mc.add(Component('b'))

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(len(root.children), 1)
    eq_(root.children[0], '')

    # replace element by string
    class Component(core.Component):
        def on_render(self, element):
            return ''
    root = markup.Element(markup.QName('', 'root'))
    root.children.append('')
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.children.append(a)
    root.children.append('')
    mc = core.MarkupContainer('a')
    mc.add(Component('b'))

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(len(root.children), 1)
    eq_(root.children[0], '')

    # replace element by list
    class Component(core.Component):
        def on_render(self, element):
            return ['', '', 0, '', '']
    root = markup.Element(markup.QName('', 'root'))
    root.children.append('')
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.children.append(a)
    root.children.append('')
    mc = core.MarkupContainer('a')
    mc.add(Component('b'))

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(len(root.children), 3)
    eq_(root.children[0], '')
    eq_(root.children[1], 0)
    eq_(root.children[2], '')

    # replace element by list
    class Component(core.Component):
        def on_render(self, element):
            return ['', '', 0, '', '']
    root = markup.Element(markup.QName('', 'root'))
    root.children.append('')
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.children.append(a)
    root.children.append(1)
    mc = core.MarkupContainer('a')
    mc.add(Component('b'))

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(len(root.children), 4)
    eq_(root.children[0], '')
    eq_(root.children[1], 0)
    eq_(root.children[2], '')
    eq_(root.children[3], 1)

def test_attribute_modifier():
    am = core.AttributeModifier('a', core.Model(None))
    assert_raises(AyameError, lambda: am.app)
    assert_raises(AyameError, lambda: am.config)
    assert_raises(AyameError, lambda: am.environ)

    # component
    root = markup.Element(markup.QName('', 'root'))
    root.attrib[markup.QName('', 'a')] = ''
    c = core.Component('a')
    c.add(core.AttributeModifier('a', core.Model(None)))
    c.add(core.AttributeModifier(markup.QName('', 'b'), core.Model(None)))
    c.add(core.AttributeModifier('c', core.Model('')))
    eq_(len(c.modifiers), 3)
    eq_(c.modifiers[0].component, c)
    eq_(c.modifiers[1].component, c)
    eq_(c.modifiers[2].component, c)

    root = c.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {markup.QName('', 'c'): ''})
    eq_(len(root.children), 0)

    # markup container
    root = markup.Element(markup.QName('', 'root'))
    root.attrib[markup.QName('', 'a')] = ''
    mc = core.MarkupContainer('a')
    mc.add(core.AttributeModifier('a', core.Model(None)))
    mc.add(core.AttributeModifier(markup.QName('', 'b'), core.Model(None)))
    mc.add(core.AttributeModifier('c', core.Model('')))
    eq_(len(mc.modifiers), 3)
    eq_(mc.modifiers[0].component, mc)
    eq_(mc.modifiers[1].component, mc)
    eq_(mc.modifiers[2].component, mc)

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {markup.QName('', 'c'): ''})
    eq_(len(root.children), 0)

def test_render_unknown_ayame_element():
    root = markup.Element(markup.QName(markup.AYAME_NS, 'spam'))
    mc = core.MarkupContainer('a')
    assert_raises(RenderingError, mc.render, root)

def test_render_ayame_container():
    # ayame:id is not found
    root = markup.Element(markup.QName('', 'root'))
    container = markup.Element(markup.AYAME_CONTAINER)
    root.children.append(container)
    mc = core.MarkupContainer('a')
    assert_raises(RenderingError, mc.render, root)

    # component is not found
    root = markup.Element(markup.QName('', 'root'))
    container = markup.Element(markup.AYAME_CONTAINER)
    container.attrib[markup.AYAME_ID] = 'b'
    root.children.append(container)
    mc = core.MarkupContainer('a')
    assert_raises(ComponentError, mc.render, root)

    # ayame:container
    root = markup.Element(markup.QName('', 'root'))
    container = markup.Element(markup.AYAME_CONTAINER)
    container.attrib[markup.AYAME_ID] = 'b'
    root.children.append(container)
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'c'
    container.children.append(a)
    mc = core.MarkupContainer('a')
    def populate_item(li):
        li.add(basic.Label('c', li.model_object))
    mc.add(basic.ListView('b', [str(i) for i in range(3)], populate_item))

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(len(root.children), 3)

    a = root.children[0]
    eq_(a.qname, markup.QName('', 'a'))
    eq_(a.attrib, {})
    eq_(len(a.children), 1)
    eq_(a.children[0], '0')

    a = root.children[1]
    eq_(a.qname, markup.QName('', 'a'))
    eq_(a.attrib, {})
    eq_(len(a.children), 1)
    eq_(a.children[0], '1')

    a = root.children[2]
    eq_(a.qname, markup.QName('', 'a'))
    eq_(a.attrib, {})
    eq_(len(a.children), 1)
    eq_(a.children[0], '2')

def test_render_ayame_enclosure():
    # ayame:child is not found
    root = markup.Element(markup.QName('', 'root'))
    enclosure = markup.Element(markup.AYAME_ENCLOSURE)
    root.children.append(enclosure)
    mc = core.MarkupContainer('a')
    assert_raises(RenderingError, mc.render, root)

    # component is not found
    root = markup.Element(markup.QName('', 'root'))
    enclosure = markup.Element(markup.AYAME_ENCLOSURE)
    enclosure.attrib[markup.AYAME_CHILD] = 'b'
    root.children.append(enclosure)
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    enclosure.children.append(a)
    mc = core.MarkupContainer('a')
    assert_raises(ComponentError, mc.render, root)

    # ayame:enclosure with visible component
    root = markup.Element(markup.QName('', 'root'))
    a = markup.Element(markup.QName('', 'a'))
    root.children.append(a)
    enclosure = markup.Element(markup.AYAME_ENCLOSURE)
    enclosure.attrib[markup.AYAME_CHILD] = 'b1'
    a.children.append(enclosure)
    b = markup.Element(markup.QName('', 'b'))
    b.attrib[markup.AYAME_ID] = 'b1'
    enclosure.children.append(b)
    b = markup.Element(markup.QName('', 'b'))
    a.children.append(b)
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b2'
    root.children.append(a)
    mc = core.MarkupContainer('a')
    mc.add(basic.Label('b1', 'spam'))
    mc.add(basic.Label('b2', 'eggs'))

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(len(root.children), 2)

    a = root.children[0]
    eq_(a.qname, markup.QName('', 'a'))
    eq_(a.attrib, {})
    eq_(len(a.children), 2)

    b = a.children[0]
    eq_(b.qname, markup.QName('', 'b'))
    eq_(b.attrib, {})
    eq_(len(b.children), 1)
    eq_(b.children[0], 'spam')

    b = a.children[1]
    eq_(b.qname, markup.QName('', 'b'))
    eq_(b.attrib, {})
    eq_(len(b.children), 0)

    a = root.children[1]
    eq_(a.qname, markup.QName('', 'a'))
    eq_(a.attrib, {})
    eq_(len(a.children), 1)
    eq_(a.children[0], 'eggs')

    # ayame:enclosure with invisible component
    root = markup.Element(markup.QName('', 'root'))
    a = markup.Element(markup.QName('', 'a'))
    root.children.append(a)
    enclosure = markup.Element(markup.AYAME_ENCLOSURE)
    enclosure.attrib[markup.AYAME_CHILD] = 'b1'
    a.children.append(enclosure)
    b = markup.Element(markup.QName('', 'b'))
    b.attrib[markup.AYAME_ID] = 'b1'
    enclosure.children.append(b)
    b = markup.Element(markup.QName('', 'b'))
    a.children.append(b)
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b2'
    root.children.append(a)
    mc = core.MarkupContainer('a')
    mc.add(basic.Label('b1', 'spam'))
    mc.add(basic.Label('b2', 'eggs'))
    mc.find('b1').visible = False
    mc.find('b2').visible = False

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(len(root.children), 1)

    a = root.children[0]
    eq_(a.qname, markup.QName('', 'a'))
    eq_(a.attrib, {})
    eq_(len(a.children), 1)

    b = a.children[0]
    eq_(b.qname, markup.QName('', 'b'))
    eq_(b.attrib, {})
    eq_(len(b.children), 0)

def test_markup_inheritance():
    local = core._local
    app = core.Ayame(__name__)

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
    try:
        local.app = app
        mc = Ham('a')
        m = mc.load_markup()
    finally:
        local.app = None
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
    eq_(len(html.children), 5)
    ok_(isinstance(html.children[0], basestring))
    ok_(isinstance(html.children[2], basestring))
    ok_(isinstance(html.children[4], basestring))

    head = html.children[1]
    eq_(head.qname, markup.QName(markup.XHTML_NS, 'head'))
    eq_(head.attrib, {})
    eq_(head.type, markup.Element.OPEN)
    eq_(head.ns, {})
    eq_(len(head.children), 9)
    ok_(isinstance(head.children[0], basestring))
    ok_(isinstance(head.children[2], basestring))
    ok_(isinstance(head.children[4], basestring))
    ok_(isinstance(head.children[6], basestring))
    ok_(isinstance(head.children[8], basestring))

    title = head.children[1]
    eq_(title.qname, markup.QName(markup.XHTML_NS, 'title'))
    eq_(title.attrib, {})
    eq_(title.type, markup.Element.OPEN)
    eq_(title.ns, {})
    eq_(len(title.children), 1)
    eq_(title.children[0], 'Spam')

    meta = head.children[3]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Spam'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(len(meta.children), 0)

    meta = head.children[5]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Eggs'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(len(meta.children), 0)

    meta = head.children[7]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Ham'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(len(meta.children), 0)

    body = html.children[3]
    eq_(body.qname, markup.QName(markup.XHTML_NS, 'body'))
    eq_(body.attrib, {})
    eq_(body.type, markup.Element.OPEN)
    eq_(body.ns, {})
    eq_(len(body.children), 9)
    ok_(isinstance(body.children[0], basestring))
    ok_(isinstance(body.children[2], basestring))
    ok_(isinstance(body.children[4], basestring))
    ok_(isinstance(body.children[6], basestring))
    ok_(isinstance(body.children[8], basestring))

    p = body.children[1]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'before ayame:child (Spam)')

    p = body.children[3]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'inside ayame:extend (Eggs)')

    p = body.children[5]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'inside ayame:extend (Ham)')

    p = body.children[7]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'after ayame:child (Spam)')

    # submarkup is empty
    class Sausage(Spam):
        pass
    try:
        local.app = app
        mc = Sausage('a')
        m = mc.load_markup()
    finally:
        local.app = None
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
    eq_(len(html.children), 5)
    ok_(isinstance(html.children[0], basestring))
    ok_(isinstance(html.children[2], basestring))
    ok_(isinstance(html.children[4], basestring))

    head = html.children[1]
    eq_(head.qname, markup.QName(markup.XHTML_NS, 'head'))
    eq_(head.attrib, {})
    eq_(head.type, markup.Element.OPEN)
    eq_(head.ns, {})
    eq_(len(head.children), 7)
    ok_(isinstance(head.children[0], basestring))
    ok_(isinstance(head.children[2], basestring))
    ok_(isinstance(head.children[4], basestring))
    ok_(isinstance(head.children[6], basestring))

    title = head.children[1]
    eq_(title.qname, markup.QName(markup.XHTML_NS, 'title'))
    eq_(title.attrib, {})
    eq_(title.type, markup.Element.OPEN)
    eq_(title.ns, {})
    eq_(len(title.children), 1)
    eq_(title.children[0], 'Spam')

    meta = head.children[3]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Spam'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(len(meta.children), 0)

    meta = head.children[5]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Sausage'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(len(meta.children), 0)

    body = html.children[3]
    eq_(body.qname, markup.QName(markup.XHTML_NS, 'body'))
    eq_(body.attrib, {})
    eq_(body.type, markup.Element.OPEN)
    eq_(body.ns, {})
    eq_(len(body.children), 5)
    ok_(isinstance(body.children[0], basestring))
    ok_(isinstance(body.children[2], basestring))
    ok_(isinstance(body.children[4], basestring))

    p = body.children[1]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'before ayame:child (Spam)')

    p = body.children[3]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'after ayame:child (Spam)')

    # merge ayame:head into ayame:head in supermarkup
    class Sausage(Bacon):
        pass
    try:
        local.app = app
        mc = Sausage('a')
        m = mc.load_markup()
    finally:
        local.app = None
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
    eq_(len(html.children), 5)
    ok_(isinstance(html.children[0], basestring))
    ok_(isinstance(html.children[2], basestring))
    ok_(isinstance(html.children[4], basestring))

    ayame_head = html.children[1]
    eq_(ayame_head.qname, markup.QName(markup.AYAME_NS, 'head'))
    eq_(ayame_head.attrib, {})
    eq_(ayame_head.type, markup.Element.OPEN)
    eq_(ayame_head.ns, {})
    eq_(len(ayame_head.children), 7)
    ok_(isinstance(ayame_head.children[0], basestring))
    ok_(isinstance(ayame_head.children[2], basestring))
    ok_(isinstance(ayame_head.children[4], basestring))
    ok_(isinstance(ayame_head.children[6], basestring))

    title = ayame_head.children[1]
    eq_(title.qname, markup.QName(markup.XHTML_NS, 'title'))
    eq_(title.attrib, {})
    eq_(title.type, markup.Element.OPEN)
    eq_(title.ns, {})
    eq_(len(title.children), 1)
    eq_(title.children[0], 'Bacon')

    meta = ayame_head.children[3]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Bacon'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(len(meta.children), 0)

    meta = ayame_head.children[5]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Sausage'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(len(meta.children), 0)

    body = html.children[3]
    eq_(body.qname, markup.QName(markup.XHTML_NS, 'body'))
    eq_(body.attrib, {})
    eq_(body.type, markup.Element.OPEN)
    eq_(body.ns, {})
    eq_(len(body.children), 5)
    ok_(isinstance(body.children[0], basestring))
    ok_(isinstance(body.children[2], basestring))
    ok_(isinstance(body.children[4], basestring))

    p = body.children[1]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'before ayame:child (Bacon)')

    p = body.children[3]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'after ayame:child (Bacon)')

    # superclass is not found
    class Sausage(core.MarkupContainer):
        pass
    try:
        local.app = app
        mc = Sausage('a')
        assert_raises(AyameError, mc.load_markup)
    finally:
        local.app = None

    # multiple inheritance
    class Sausage(Spam, Toast, Beans, Bacon):
        pass
    try:
        local.app = app
        mc = Sausage('a')
        assert_raises(AyameError, mc.load_markup)
    finally:
        local.app = None

    # ayame:child element is not found
    class Sausage(Toast):
        pass
    try:
        local.app = app
        mc = Sausage('a')
        assert_raises(RenderingError, mc.load_markup)
    finally:
        local.app = None

    # head element is not found
    class Sausage(Beans):
        pass
    try:
        local.app = app
        mc = Sausage('a')
        assert_raises(RenderingError, mc.load_markup)
    finally:
        local.app = None

def test_ayame_head():
    ayame_head = markup.Element(markup.AYAME_HEAD)
    h = markup.Element(markup.QName('', 'h'))
    ayame_head.children.append(h)

    class MarkupContainer(core.MarkupContainer):
        def on_render(self, element):
            self.push_ayame_head(ayame_head)
            return element

    # root element is not html
    root = markup.Element(markup.QName('', 'root'))
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.children.append(a)
    mc = core.MarkupContainer('a')
    mc.add(MarkupContainer('b'))
    assert_raises(RenderingError, mc.render, root)

    # head element is not found
    root = markup.Element(markup.HTML)
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.children.append(a)
    mc = core.MarkupContainer('a')
    mc.add(MarkupContainer('b'))
    assert_raises(RenderingError, mc.render, root)

    # push ayame:head
    root = markup.Element(markup.HTML)
    head = markup.Element(markup.HEAD)
    root.children.append(head)
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.children.append(a)
    mc = core.MarkupContainer('a')
    mc.add(MarkupContainer('b'))

    root = mc.render(root)
    eq_(root.qname, markup.HTML)
    eq_(root.attrib, {})
    eq_(len(root.children), 2)

    head = root.children[0]
    eq_(head.qname, markup.HEAD)
    eq_(head.attrib, {})
    eq_(head.type, markup.Element.OPEN)
    eq_(len(head.children), 1)

    h = head.children[0]
    eq_(h.qname, markup.QName('', 'h'))
    eq_(h.attrib, {})
    eq_(len(h.children), 0)

    a = root.children[1]
    eq_(a.qname, markup.QName('', 'a'))
    eq_(a.attrib, {})
    eq_(len(a.children), 0)

def test_failsafe():
    # Ayame
    app = core.Ayame(None)
    eq_(app._root, os.getcwd())

    # MarkupContainer
    mc = core.MarkupContainer('a')
    a = markup.Element(markup.QName('', 'a'))
    assert_raises(RenderingError, mc.render_ayame_element, a)
    eq_(mc.render_component(a), (None, a))

def test_request():
    # QUERY_STRING and CONTENT_TYPE are empty
    environ = {'REQUEST_METHOD': 'POST'}
    request = core.Request(environ, {})
    eq_(request.environ, environ)
    eq_(request.method, 'POST')
    eq_(request.uri, {})
    eq_(request.query, {})
    eq_(request.body, {})

    # message body is empty
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'POST',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.core'}
    request = core.Request(environ, {})
    eq_(request.environ, environ)
    eq_(request.method, 'POST')
    eq_(request.uri, {})
    eq_(request.query, {})
    eq_(request.body, {})

    # ASCII
    query = ('a=1&'
             'b=1&'
             'b=2&'
             'c=1&'
             'c=2&'
             'c=3')
    body = ('--ayame.core\r\n'
            'Content-Disposition: form-data; name="x"\r\n'
            '\r\n'
            '-1\r\n'
            '--ayame.core\r\n'
            'Content-Disposition: form-data; name="y"\r\n'
            '\r\n'
            '-1\r\n'
            '--ayame.core\r\n'
            'Content-Disposition: form-data; name="y"\r\n'
            '\r\n'
            '-2\r\n'
            '--ayame.core\r\n'
            'Content-Disposition: form-data; name="z"\r\n'
            '\r\n'
            '-1\r\n'
            '--ayame.core\r\n'
            'Content-Disposition: form-data; name="z"\r\n'
            '\r\n'
            '-2\r\n'
            '--ayame.core\r\n'
            'Content-Disposition: form-data; name="z"\r\n'
            '\r\n'
            '-3\r\n'
            '--ayame.core--\r\n'
            '\r\n')
    environ = {'wsgi.input': io.BytesIO(body.encode('utf-8')),
               'REQUEST_METHOD': 'POST',
               'QUERY_STRING': query.encode('utf-8'),
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.core'}
    request = core.Request(environ, {})
    eq_(request.environ, environ)
    eq_(request.method, 'POST')
    eq_(request.uri, {})
    eq_(request.query, {'a': ['1'],
                        'b': ['1', '2'],
                        'c': ['1', '2', '3']})
    eq_(request.body, {'x': ['-1'],
                       'y': ['-1', '-2'],
                       'z': ['-1', '-2', '-3']})

    # UTF-8
    query = ('\u3044=\u58f1&'
             '\u308d=\u58f1&'
             '\u308d=\u5f10&'
             '\u306f=\u58f1&'
             '\u306f=\u5f10&'
             '\u306f=\u53c2')
    body = ('--ayame.core\r\n'
            'Content-Disposition: form-data; name="\u3082"\r\n'
            '\r\n'
            '\u767e\r\n'
            '--ayame.core\r\n'
            'Content-Disposition: form-data; name="\u305b"\r\n'
            '\r\n'
            '\u767e\r\n'
            '--ayame.core\r\n'
            'Content-Disposition: form-data; name="\u305b"\r\n'
            '\r\n'
            '\u5343\r\n'
            '--ayame.core\r\n'
            'Content-Disposition: form-data; name="\u3059"\r\n'
            '\r\n'
            '\u767e\r\n'
            '--ayame.core\r\n'
            'Content-Disposition: form-data; name="\u3059"\r\n'
            '\r\n'
            '\u5343\r\n'
            '--ayame.core\r\n'
            'Content-Disposition: form-data; name="\u3059"\r\n'
            '\r\n'
            '\u4e07\r\n'
            '--ayame.core--\r\n'
            '\r\n')
    environ = {'wsgi.input': io.BytesIO(body.encode('utf-8')),
               'REQUEST_METHOD': 'POST',
               'QUERY_STRING': query.encode('utf-8'),
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.core'}
    request = core.Request(environ, {})
    eq_(request.environ, environ)
    eq_(request.method, 'POST')
    eq_(request.uri, {})
    eq_(request.query, {'\u3044': ['\u58f1'],
                        '\u308d': ['\u58f1', '\u5f10'],
                        '\u306f': ['\u58f1', '\u5f10', '\u53c2']})
    eq_(request.body, {'\u3082': ['\u767e'],
                       '\u305b': ['\u767e', '\u5343'],
                       '\u3059': ['\u767e', '\u5343', '\u4e07']})

    # filename
    body = ('--ayame.core\r\n'
            'Content-Disposition: form-data; name="a"; filename="\u3044"\r\n'
            'Content-Type: text/plain\r\n'
            '\r\n'
            'spam\n'
            'eggs\n'
            'ham\n'
            '\r\n'
            '--ayame.core--\r\n'
            '\r\n')
    environ = {'wsgi.input': io.BytesIO(body.encode('utf-8')),
               'REQUEST_METHOD': 'POST',
               'QUERY_STRING': '',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.core'}
    request = core.Request(environ, {})
    eq_(request.environ, environ)
    eq_(request.method, 'POST')
    eq_(request.uri, {})
    eq_(request.query, {})
    eq_(tuple(request.body), ('a',))

    fields = request.body['a']
    eq_(len(fields), 1)

    a = fields[0]
    eq_(a.name, 'a')
    eq_(a.filename, '\u3044')
    eq_(a.value, ('spam\n'
                  'eggs\n'
                  'ham\n'))

    # PUT
    body = ('spam\n'
            'eggs\n'
            'ham\n')
    environ = {'wsgi.input': io.BytesIO(body.encode('utf-8')),
               'REQUEST_METHOD': 'PUT',
               'QUERY_STRING': '',
               'CONTENT_TYPE': 'text/plain',
               'CONTENT_LENGTH': str(len(body))}
    request = core.Request(environ, {})
    eq_(request.environ, environ)
    eq_(request.method, 'PUT')
    eq_(request.uri, {})
    eq_(request.query, {})
    eq_(request.body.value, ('spam\n'
                             'eggs\n'
                             'ham\n'))

    # 408 Request Timeout
    body = ('--ayame.core\r\n'
            'Content-Disposition: form-data; name="a"\r\n'
            'Content-Type: text/plain\r\n')
    environ = {'wsgi.input': io.BytesIO(body.encode('utf-8')),
               'REQUEST_METHOD': 'POST',
               'QUERY_STRING': '',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.core'}
    assert_raises(http.RequestTimeout, core.Request, environ, {})

    environ = {'wsgi.input': io.BytesIO(b''),
               'REQUEST_METHOD': 'PUT',
               'QUERY_STRING': '',
               'CONTENT_TYPE': 'text/plain',
               'CONTENT_LENGTH': '-1'}
    assert_raises(http.RequestTimeout, core.Request, environ, {})

def test_page():
    local = core._local
    app = core.Ayame(__name__)

    class SpamPage(core.Page):
        def __init__(self, request):
            super(SpamPage, self).__init__(request)
            self.add(basic.Label('greeting', 'Hello World!'))
            self.headers['Content-Type'] = 'text/plain'
    xhtml = ('<?xml version="1.0"?>\n'
             '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '
             '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
             '<html xmlns="{xhtml}">\n'
             '  <title>SpamPage</title>\n'
             '  <body>\n'
             '    <p>Hello World!</p>\n'
             '  </body>\n'
             '</html>\n').format(xhtml=markup.XHTML_NS)
    environ = {'REQUEST_METHOD': 'GET'}
    try:
        local.app = app
        request = core.Request(environ, {})
        page = SpamPage(request)
        status, headers, body = page.render()
    finally:
        local.app = None
    eq_(page.page(), page)
    eq_(page.find('greeting').page(), page)
    eq_(page.path(), '')
    eq_(page.find('greeting').path(), 'greeting')
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', '253')])
    eq_(body, xhtml)
