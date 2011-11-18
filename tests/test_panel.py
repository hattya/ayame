#
# test_panel
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

from contextlib import contextmanager

from nose.tools import assert_raises, eq_, ok_

from ayame import basic, core, panel, markup
from ayame.exception import RenderingError


@contextmanager
def application():
    local = core._local
    app = core.Ayame(__name__)
    try:
        local.app = app
        yield
    finally:
        local.app = None

def test_panel():
    class Spam(core.MarkupContainer):
        def __init__(self, id):
            super(Spam, self).__init__(id)
            self.add(SpamPanel('panel'))

    class SpamPanel(panel.Panel):
        def __init__(self, id):
            super(SpamPanel, self).__init__(id)
            self.add(basic.Label('class', self.__class__.__name__))
            self.find('class').render_body_only = True

    with application():
        mc = Spam('a')
        m = mc.load_markup()
        html = mc.render(m.root)
    eq_(m.xml_decl, {'version': '1.0'})
    eq_(m.lang, 'xhtml1')
    eq_(m.doctype, markup.XHTML1_STRICT)
    ok_(m.root)

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
                      markup.QName(markup.XHTML_NS, 'content'): 'SpamPanel'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(len(meta.children), 0)

    body = html.children[3]
    eq_(body.qname, markup.QName(markup.XHTML_NS, 'body'))
    eq_(body.attrib, {})
    eq_(body.type, markup.Element.OPEN)
    eq_(body.ns, {})
    eq_(len(body.children), 7)
    ok_(isinstance(body.children[0], basestring))
    ok_(isinstance(body.children[2], basestring))
    ok_(isinstance(body.children[4], basestring))
    ok_(isinstance(body.children[6], basestring))

    p = body.children[1]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'before panel (Spam)')

    p = body.children[3]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'inside ayame:panel (SpamPanel)')

    p = body.children[5]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'after panel (Spam)')

def test_panel_with_markup_inheritance():
    class Eggs(core.MarkupContainer):
        def __init__(self, id):
            super(Eggs, self).__init__(id)
            self.add(HamPanel('panel'))

    class EggsPanel(panel.Panel):
        pass
    class HamPanel(EggsPanel):
        def __init__(self, id):
            super(HamPanel, self).__init__(id)
            self.add(basic.Label('class', self.__class__.__name__))
            self.find('class').render_body_only = True

    with application():
        mc = Eggs('a')
        m = mc.load_markup()
        html = mc.render(m.root)
    eq_(m.xml_decl, {'version': '1.0'})
    eq_(m.lang, 'xhtml1')
    eq_(m.doctype, markup.XHTML1_STRICT)
    ok_(m.root)

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
    eq_(title.children[0], 'Eggs')

    meta = head.children[3]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Eggs'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(len(meta.children), 0)

    meta = head.children[5]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'EggsPanel'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(len(meta.children), 0)

    meta = head.children[7]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'HamPanel'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(len(meta.children), 0)

    body = html.children[3]
    eq_(body.qname, markup.QName(markup.XHTML_NS, 'body'))
    eq_(body.attrib, {})
    eq_(body.type, markup.Element.OPEN)
    eq_(body.ns, {})
    eq_(len(body.children), 7)
    ok_(isinstance(body.children[0], basestring))
    ok_(isinstance(body.children[2], basestring))
    ok_(isinstance(body.children[4], basestring))
    ok_(isinstance(body.children[6], basestring))

    p = body.children[1]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'before panel (Eggs)')

    p = body.children[3]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'inside ayame:panel (HamPanel)')

    p = body.children[5]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'after panel (Eggs)')

def test_invalid_markup():
    # ayame:panel element is not found
    class Toast(core.MarkupContainer):
        def __init__(self, id):
            super(Toast, self).__init__(id)
            self.add(ToastPanel('panel'))
    class ToastPanel(panel.Panel):
        def __init__(self, id):
            super(ToastPanel, self).__init__(id)
            self.add(basic.Label('class', self.__class__.__name__))
            self.find('class').render_body_only = True
    with application():
        mc = Toast('a')
        m = mc.load_markup()
        assert_raises(RenderingError, mc.render, m.root)

    # head element is not found
    class Beans(core.MarkupContainer):
        def __init__(self, id):
            super(Beans, self).__init__(id)
            self.add(BeansPanel('panel'))
    class BeansPanel(panel.Panel):
        def __init__(self, id):
            super(BeansPanel, self).__init__(id)
            self.add(basic.Label('class', self.__class__.__name__))
            self.find('class').render_body_only = True
    with application():
        mc = Beans('a')
        m = mc.load_markup()
        assert_raises(RenderingError, mc.render, m.root)

    # unknown ayame element
    class Bacon(core.MarkupContainer):
        def __init__(self, id):
            super(Bacon, self).__init__(id)
            self.add(BaconPanel('panel'))
    class BaconPanel(panel.Panel):
        def __init__(self, id):
            super(BaconPanel, self).__init__(id)
            self.add(basic.Label('class', self.__class__.__name__))
            self.find('class').render_body_only = True
    with application():
        mc = Bacon('a')
        m = mc.load_markup()
        assert_raises(RenderingError, mc.render, m.root)
