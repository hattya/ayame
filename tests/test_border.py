#
# test_border
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

from nose.tools import assert_raises, eq_, ok_

from ayame import basic, core, border, markup
from ayame.exception import RenderingError


def test_border():
    local = core._local
    app = core.Ayame(__name__)

    class Spam(core.MarkupContainer):
        def __init__(self, id):
            super(Spam, self).__init__(id)
            self.add(SpamBorder('border'))
    class SpamBorder(border.Border):
        def __init__(self, id):
            super(SpamBorder, self).__init__(id)
            self.add(basic.Label('class', self.__class__.__name__))
            self.body.find('class').render_body_only = True
    try:
        local.app = app
        mc = Spam('a')
        m = mc.load_markup()
        html = mc.render(m.root)
    finally:
        local.app = None
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
                      markup.QName(markup.XHTML_NS, 'content'): 'SpamBorder'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(len(meta.children), 0)

    body = html.children[3]
    eq_(body.qname, markup.QName(markup.XHTML_NS, 'body'))
    eq_(body.attrib, {})
    eq_(body.type, markup.Element.OPEN)
    eq_(body.ns, {})
    eq_(len(body.children), 11)
    ok_(isinstance(body.children[0], basestring))
    ok_(isinstance(body.children[2], basestring))
    ok_(isinstance(body.children[4], basestring))
    ok_(isinstance(body.children[6], basestring))
    ok_(isinstance(body.children[8], basestring))
    ok_(isinstance(body.children[10], basestring))

    p = body.children[1]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'before border (Spam)')

    p = body.children[3]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'before ayame:body (SpamBorder)')

    p = body.children[5]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'inside border (SpamBorder)')

    p = body.children[7]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'after ayame:body (SpamBorder)')

    p = body.children[9]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'after border (Spam)')

def test_border_with_markup_inheritance():
    local = core._local
    app = core.Ayame(__name__)

    class Eggs(core.MarkupContainer):
        def __init__(self, id):
            super(Eggs, self).__init__(id)
            self.add(HamBorder('border'))
    class EggsBorder(border.Border):
        pass
    class HamBorder(EggsBorder):
        def __init__(self, id):
            super(HamBorder, self).__init__(id)
            self.add(basic.Label('class', self.__class__.__name__))
            self.body.find('class').render_body_only = True
    try:
        local.app = app
        mc = Eggs('a')
        m = mc.load_markup()
        html = mc.render(m.root)
    finally:
        local.app = None
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
                      markup.QName(markup.XHTML_NS, 'content'): 'EggsBorder'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(len(meta.children), 0)

    meta = head.children[7]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'HamBorder'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(len(meta.children), 0)

    body = html.children[3]
    eq_(body.qname, markup.QName(markup.XHTML_NS, 'body'))
    eq_(body.attrib, {})
    eq_(body.type, markup.Element.OPEN)
    eq_(body.ns, {})
    eq_(len(body.children), 11)
    ok_(isinstance(body.children[0], basestring))
    ok_(isinstance(body.children[2], basestring))
    ok_(isinstance(body.children[4], basestring))
    ok_(isinstance(body.children[6], basestring))
    ok_(isinstance(body.children[8], basestring))
    ok_(isinstance(body.children[10], basestring))

    p = body.children[1]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'before border (Eggs)')

    p = body.children[3]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'before ayame:body (HamBorder)')

    p = body.children[5]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'inside border (HamBorder)')

    p = body.children[7]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'after ayame:body (HamBorder)')

    p = body.children[9]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 1)
    eq_(p.children[0], 'after border (Eggs)')

def test_invalid_markup():
    local = core._local
    app = core.Ayame(__name__)

    # ayame:border element is not found
    class Toast(core.MarkupContainer):
        def __init__(self, id):
            super(Toast, self).__init__(id)
            self.add(ToastBorder('border'))
    class ToastBorder(border.Border):
        def __init__(self, id):
            super(ToastBorder, self).__init__(id)
            self.add(basic.Label('class', self.__class__.__name__))
            self.body.find('class').render_body_only = True
    try:
        local.app = app
        mc = Toast('a')
        m = mc.load_markup()
        assert_raises(RenderingError, mc.render, m.root)
    finally:
        local.app = None

    # ayame:body element is not found
    class Beans(core.MarkupContainer):
        def __init__(self, id):
            super(Beans, self).__init__(id)
            self.add(BeansBorder('border'))
    class BeansBorder(border.Border):
        def __init__(self, id):
            super(BeansBorder, self).__init__(id)
            self.add(basic.Label('class', self.__class__.__name__))
            self.body.find('class').render_body_only = True
    try:
        local.app = app
        mc = Beans('a')
        m = mc.load_markup()
        assert_raises(RenderingError, mc.render, m.root)
    finally:
        local.app = None

    # unknown ayame element
    class Bacon(core.MarkupContainer):
        def __init__(self, id):
            super(Bacon, self).__init__(id)
            self.add(BaconBorder('border'))
    class BaconBorder(border.Border):
        def __init__(self, id):
            super(BaconBorder, self).__init__(id)
            self.add(basic.Label('class', self.__class__.__name__))
            self.body.find('class').render_body_only = True
    try:
        local.app = app
        mc = Bacon('a')
        m = mc.load_markup()
        assert_raises(RenderingError, mc.render, m.root)
    finally:
        local.app = None