#
# test_border
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

from ayame import basic, border, core, http, markup
from ayame.exception import RenderingError


@contextmanager
def application(environ=None):
    local = core._local
    app = core.Ayame(__name__)
    try:
        local.app = app
        if environ is not None:
            local.environ = environ
            local.request = core.Request(environ, {})
        yield
    finally:
        if environ is not None:
            local.request = None
            local.environ = None
        local.app = None


def assert_ws(element, i):
    ok_(isinstance(element[i], basestring))
    eq_(element[i].strip(), '')


def test_border():
    class Spam(core.MarkupContainer):
        def __init__(self, id):
            super(Spam, self).__init__(id)
            self.add(SpamBorder('border'))

    class SpamBorder(border.Border):
        def __init__(self, id):
            super(SpamBorder, self).__init__(id)
            self.add(basic.Label('class', self.__class__.__name__))
            self.body.find('class').render_body_only = True

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
                      markup.QName(markup.XHTML_NS, 'content'): 'SpamBorder'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(meta.children, [])

    body = html[3]
    eq_(body.qname, markup.QName(markup.XHTML_NS, 'body'))
    eq_(body.attrib, {})
    eq_(body.type, markup.Element.OPEN)
    eq_(body.ns, {})
    eq_(len(body), 15)
    assert_ws(body, 0)
    assert_ws(body, 2)
    assert_ws(body, 3)
    assert_ws(body, 5)
    assert_ws(body, 6)
    assert_ws(body, 8)
    assert_ws(body, 9)
    assert_ws(body, 11)
    assert_ws(body, 12)
    assert_ws(body, 14)

    p = body[1]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['before border (Spam)'])

    p = body[4]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['before ayame:body (SpamBorder)'])

    p = body[7]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p), 3)
    p.normalize()
    eq_(p.children, ['inside border (SpamBorder)'])

    p = body[10]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['after ayame:body (SpamBorder)'])

    p = body[13]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['after border (Spam)'])


def test_border_with_markup_inheritance():
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
    eq_(title.children, ['Eggs'])

    meta = head[3]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'Eggs'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(meta.children, [])

    meta = head[6]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'EggsBorder'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(meta.children, [])

    meta = head[9]
    eq_(meta.qname, markup.QName(markup.XHTML_NS, 'meta'))
    eq_(meta.attrib, {markup.QName(markup.XHTML_NS, 'name'): 'class',
                      markup.QName(markup.XHTML_NS, 'content'): 'HamBorder'})
    eq_(meta.type, markup.Element.EMPTY)
    eq_(meta.ns, {})
    eq_(meta.children, [])

    body = html[3]
    eq_(body.qname, markup.QName(markup.XHTML_NS, 'body'))
    eq_(body.attrib, {})
    eq_(body.type, markup.Element.OPEN)
    eq_(body.ns, {})
    eq_(len(body), 15)
    assert_ws(body, 0)
    assert_ws(body, 2)
    assert_ws(body, 3)
    assert_ws(body, 5)
    assert_ws(body, 6)
    assert_ws(body, 8)
    assert_ws(body, 9)
    assert_ws(body, 11)
    assert_ws(body, 12)
    assert_ws(body, 14)

    p = body[1]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['before border (Eggs)'])

    p = body[4]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['before ayame:body (HamBorder)'])

    p = body[7]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p), 3)
    p.normalize()
    eq_(p.children, ['inside border (HamBorder)'])

    p = body[10]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['after ayame:body (HamBorder)'])

    p = body[13]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['after border (Eggs)'])


def test_invalid_markup():
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
    with application():
        mc = Toast('a')
        m = mc.load_markup()
        assert_raises(RenderingError, mc.render, m.root)

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
    with application():
        mc = Beans('a')
        m = mc.load_markup()
        assert_raises(RenderingError, mc.render, m.root)

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
    with application():
        mc = Bacon('a')
        m = mc.load_markup()
        assert_raises(RenderingError, mc.render, m.root)


def test_empty_markup():
    class Sausage(core.MarkupContainer):
        def __init__(self, id):
            super(Sausage, self).__init__(id)
            self.add(SausageBorder('border'))

    class SausageBorder(border.Border):
        pass

    with application():
        mc = Sausage('a')
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
    eq_(len(html), 5)
    assert_ws(html, 0)
    assert_ws(html, 2)
    assert_ws(html, 4)

    head = html[1]
    eq_(head.qname, markup.QName(markup.XHTML_NS, 'head'))
    eq_(head.attrib, {})
    eq_(head.type, markup.Element.OPEN)
    eq_(head.ns, {})
    eq_(len(head), 5)
    assert_ws(head, 0)
    assert_ws(head, 2)
    assert_ws(head, 4)

    title = head[1]
    eq_(title.qname, markup.QName(markup.XHTML_NS, 'title'))
    eq_(title.attrib, {})
    eq_(title.type, markup.Element.OPEN)
    eq_(title.ns, {})
    eq_(title.children, ['Sausage'])

    meta = head[3]
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
    eq_(len(body), 9)
    assert_ws(body, 0)
    assert_ws(body, 2)
    assert_ws(body, 3)
    assert_ws(body, 5)
    assert_ws(body, 6)
    assert_ws(body, 8)

    p = body[1]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['before border (Sausage)'])

    p = body[4]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['inside border (Sausage)'])

    p = body[7]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(p.children, ['after border (Sausage)'])


def test_render_ayame_message():
    class TomatoPage(core.Page):
        def __init__(self):
            super(TomatoPage, self).__init__()
            self.add(TomatoBorder('border'))

    class TomatoBorder(border.Border):
        pass

    xhtml = ('<?xml version="1.0"?>\n'
             '{doctype}\n'
             '<html xmlns="{xhtml}">\n'
             '  <head>\n'
             '    <title>TomatoPage</title>\n'
             '  </head>\n'
             '  <body>\n'
             '    <p>before, body, after</p>\n'
             '  </body>\n'
             '</html>\n').format(doctype=markup.XHTML1_STRICT,
                                 xhtml=markup.XHTML_NS)
    xhtml = xhtml.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(),
               'HTTP_ACCEPT_LANGUAGE': 'en',
               'REQUEST_METHOD': 'GET'}
    with application(environ):
        page = TomatoPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)

    xhtml = (u'<?xml version="1.0"?>\n'
             u'{doctype}\n'
             u'<html xmlns="{xhtml}">\n'
             u'  <head>\n'
             u'    <title>TomatoPage</title>\n'
             u'  </head>\n'
             u'  <body>\n'
             u'    <p>\u524d, \u4e2d, \u5f8c</p>\n'
             u'  </body>\n'
             u'</html>\n').format(doctype=markup.XHTML1_STRICT,
                                  xhtml=markup.XHTML_NS)
    xhtml = xhtml.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(),
               'HTTP_ACCEPT_LANGUAGE': 'ja, en',
               'REQUEST_METHOD': 'GET'}
    with application(environ):
        page = TomatoPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)
