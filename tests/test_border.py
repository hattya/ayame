#
# test_border
#
#   Copyright (c) 2011-2015 Akinori Hattori <hattya@gmail.com>
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

import ayame
from ayame import basic, border, form, http, markup
from base import AyameTestCase


class BorderTestCase(AyameTestCase):

    @classmethod
    def setup_class(cls):
        super(BorderTestCase, cls).setup_class()
        cls.app.config['ayame.markup.pretty'] = True

    def test_border(self):
        class Spam(MarkupContainer):
            def __init__(self, id):
                super(Spam, self).__init__(id)
                self.add(SpamBorder('border'))

        class SpamBorder(Border):
            pass

        with self.application():
            mc = Spam('a')
            self.assert_true(mc.find('border').render_body_only)
            self.assert_true(mc.find('border').has_markup)
            m, html = mc.render()
        self.assert_equal(m.xml_decl, {'version': '1.0'})
        self.assert_equal(m.lang, 'xhtml1')
        self.assert_equal(m.doctype, markup.XHTML1_STRICT)
        self.assert_true(m.root)

        self.assert_equal(html.qname, self.html_of('html'))
        self.assert_equal(html.attrib, {})
        self.assert_equal(html.type, markup.Element.OPEN)
        self.assert_equal(html.ns, {'': markup.XHTML_NS,
                                    'xml': markup.XML_NS,
                                    'ayame': markup.AYAME_NS})
        self.assert_equal(len(html), 5)
        self.assert_ws(html, 0)
        self.assert_ws(html, 2)
        self.assert_ws(html, 4)

        head = html[1]
        self.assert_equal(head.qname, self.html_of('head'))
        self.assert_equal(head.attrib, {})
        self.assert_equal(head.type, markup.Element.OPEN)
        self.assert_equal(head.ns, {})
        self.assert_equal(len(head), 8)
        self.assert_ws(head, 0)
        self.assert_ws(head, 2)
        self.assert_ws(head, 4)
        self.assert_ws(head, 5)
        self.assert_ws(head, 7)

        title = head[1]
        self.assert_equal(title.qname, self.html_of('title'))
        self.assert_equal(title.attrib, {})
        self.assert_equal(title.type, markup.Element.OPEN)
        self.assert_equal(title.ns, {})
        self.assert_equal(title.children, ['Spam'])

        meta = head[3]
        self.assert_equal(meta.qname, self.html_of('meta'))
        self.assert_equal(meta.attrib, {self.html_of('name'): 'class',
                                        self.html_of('content'): 'Spam'})
        self.assert_equal(meta.type, markup.Element.EMPTY)
        self.assert_equal(meta.ns, {})
        self.assert_equal(meta.children, [])

        meta = head[6]
        self.assert_equal(meta.qname, self.html_of('meta'))
        self.assert_equal(meta.attrib, {self.html_of('name'): 'class',
                                        self.html_of('content'): 'SpamBorder'})
        self.assert_equal(meta.type, markup.Element.EMPTY)
        self.assert_equal(meta.ns, {})
        self.assert_equal(meta.children, [])

        body = html[3]
        self.assert_equal(body.qname, self.html_of('body'))
        self.assert_equal(body.attrib, {})
        self.assert_equal(body.type, markup.Element.OPEN)
        self.assert_equal(body.ns, {})
        self.assert_equal(len(body), 15)
        self.assert_ws(body, 0)
        self.assert_ws(body, 2)
        self.assert_ws(body, 3)
        self.assert_ws(body, 5)
        self.assert_ws(body, 6)
        self.assert_ws(body, 8)
        self.assert_ws(body, 9)
        self.assert_ws(body, 11)
        self.assert_ws(body, 12)
        self.assert_ws(body, 14)

        p = body[1]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['before border (Spam)'])

        p = body[4]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['before ayame:body (SpamBorder)'])

        p = body[7]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(len(p), 3)
        p.normalize()
        self.assert_equal(p.children, ['inside border (SpamBorder)'])

        p = body[10]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['after ayame:body (SpamBorder)'])

        p = body[13]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['after border (Spam)'])

    def test_border_with_markup_inheritance(self):
        class Eggs(MarkupContainer):
            def __init__(self, id):
                super(Eggs, self).__init__(id)
                self.add(HamBorder('border'))

        class EggsBorder(Border):
            pass

        class HamBorder(EggsBorder):
            pass

        with self.application():
            mc = Eggs('a')
            m, html = mc.render()
        self.assert_equal(m.xml_decl, {'version': '1.0'})
        self.assert_equal(m.lang, 'xhtml1')
        self.assert_equal(m.doctype, markup.XHTML1_STRICT)
        self.assert_true(m.root)

        self.assert_equal(html.qname, self.html_of('html'))
        self.assert_equal(html.attrib, {})
        self.assert_equal(html.type, markup.Element.OPEN)
        self.assert_equal(html.ns, {'': markup.XHTML_NS,
                                    'xml': markup.XML_NS,
                                    'ayame': markup.AYAME_NS})
        self.assert_equal(len(html), 5)
        self.assert_ws(html, 0)
        self.assert_ws(html, 2)
        self.assert_ws(html, 4)

        head = html[1]
        self.assert_equal(head.qname, self.html_of('head'))
        self.assert_equal(head.attrib, {})
        self.assert_equal(head.type, markup.Element.OPEN)
        self.assert_equal(head.ns, {})
        self.assert_equal(len(head), 11)
        self.assert_ws(head, 0)
        self.assert_ws(head, 2)
        self.assert_ws(head, 4)
        self.assert_ws(head, 5)
        self.assert_ws(head, 7)
        self.assert_ws(head, 8)
        self.assert_ws(head, 10)

        title = head[1]
        self.assert_equal(title.qname, self.html_of('title'))
        self.assert_equal(title.attrib, {})
        self.assert_equal(title.type, markup.Element.OPEN)
        self.assert_equal(title.ns, {})
        self.assert_equal(title.children, ['Eggs'])

        meta = head[3]
        self.assert_equal(meta.qname, self.html_of('meta'))
        self.assert_equal(meta.attrib, {self.html_of('name'): 'class',
                                        self.html_of('content'): 'Eggs'})
        self.assert_equal(meta.type, markup.Element.EMPTY)
        self.assert_equal(meta.ns, {})
        self.assert_equal(meta.children, [])

        meta = head[6]
        self.assert_equal(meta.qname, self.html_of('meta'))
        self.assert_equal(meta.attrib, {self.html_of('name'): 'class',
                                        self.html_of('content'): 'EggsBorder'})
        self.assert_equal(meta.type, markup.Element.EMPTY)
        self.assert_equal(meta.ns, {})
        self.assert_equal(meta.children, [])

        meta = head[9]
        self.assert_equal(meta.qname, self.html_of('meta'))
        self.assert_equal(meta.attrib, {self.html_of('name'): 'class',
                                        self.html_of('content'): 'HamBorder'})
        self.assert_equal(meta.type, markup.Element.EMPTY)
        self.assert_equal(meta.ns, {})
        self.assert_equal(meta.children, [])

        body = html[3]
        self.assert_equal(body.qname, self.html_of('body'))
        self.assert_equal(body.attrib, {})
        self.assert_equal(body.type, markup.Element.OPEN)
        self.assert_equal(body.ns, {})
        self.assert_equal(len(body), 15)
        self.assert_ws(body, 0)
        self.assert_ws(body, 2)
        self.assert_ws(body, 3)
        self.assert_ws(body, 5)
        self.assert_ws(body, 6)
        self.assert_ws(body, 8)
        self.assert_ws(body, 9)
        self.assert_ws(body, 11)
        self.assert_ws(body, 12)
        self.assert_ws(body, 14)

        p = body[1]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['before border (Eggs)'])

        p = body[4]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['before ayame:body (HamBorder)'])

        p = body[7]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(len(p), 3)
        p.normalize()
        self.assert_equal(p.children, ['inside border (HamBorder)'])

        p = body[10]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['after ayame:body (HamBorder)'])

        p = body[13]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['after border (Eggs)'])

    def test_invalid_markup_no_ayame_border(self):
        class Toast(MarkupContainer):
            def __init__(self, id):
                super(Toast, self).__init__(id)
                self.add(ToastBorder('border'))

        class ToastBorder(Border):
            pass

        with self.application():
            mc = Toast('a')
            with self.assert_raises_regex(ayame.RenderingError,
                                          r"'ayame:border' .* not found\b"):
                mc.render()

    def test_invalid_markup_no_ayame_body(self):
        class Beans(MarkupContainer):
            def __init__(self, id):
                super(Beans, self).__init__(id)
                self.add(BeansBorder('border'))

        class BeansBorder(Border):
            pass

        with self.application():
            mc = Beans('a')
            with self.assert_raises_regex(ayame.RenderingError,
                                          r"'ayame:body' .* not found\b"):
                mc.render()

    def test_invalid_markup_unknown_ayame_element(self):
        class Bacon(MarkupContainer):
            def __init__(self, id):
                super(Bacon, self).__init__(id)
                self.add(BaconBorder('border'))

        class BaconBorder(Border):
            pass

        with self.application():
            mc = Bacon('a')
            with self.assert_raises_regex(ayame.RenderingError,
                                          r"\bunknown .* 'ayame:bacon'"):
                mc.render()

    def test_empty_markup(self):
        class Sausage(MarkupContainer):
            def __init__(self, id):
                super(Sausage, self).__init__(id)
                self.add(SausageBorder('border'))

        class SausageBorder(Border):
            pass

        with self.application():
            mc = Sausage('a')
            m, html = mc.render()
        self.assert_equal(m.xml_decl, {'version': '1.0'})
        self.assert_equal(m.lang, 'xhtml1')
        self.assert_equal(m.doctype, markup.XHTML1_STRICT)
        self.assert_true(m.root)

        self.assert_equal(html.qname, self.html_of('html'))
        self.assert_equal(html.attrib, {})
        self.assert_equal(html.type, markup.Element.OPEN)
        self.assert_equal(html.ns, {'': markup.XHTML_NS,
                                    'xml': markup.XML_NS,
                                    'ayame': markup.AYAME_NS})
        self.assert_equal(len(html), 5)
        self.assert_ws(html, 0)
        self.assert_ws(html, 2)
        self.assert_ws(html, 4)

        head = html[1]
        self.assert_equal(head.qname, self.html_of('head'))
        self.assert_equal(head.attrib, {})
        self.assert_equal(head.type, markup.Element.OPEN)
        self.assert_equal(head.ns, {})
        self.assert_equal(len(head), 5)
        self.assert_ws(head, 0)
        self.assert_ws(head, 2)
        self.assert_ws(head, 4)

        title = head[1]
        self.assert_equal(title.qname, self.html_of('title'))
        self.assert_equal(title.attrib, {})
        self.assert_equal(title.type, markup.Element.OPEN)
        self.assert_equal(title.ns, {})
        self.assert_equal(title.children, ['Sausage'])

        meta = head[3]
        self.assert_equal(meta.qname, self.html_of('meta'))
        self.assert_equal(meta.attrib, {self.html_of('name'): 'class',
                                        self.html_of('content'): 'Sausage'})
        self.assert_equal(meta.type, markup.Element.EMPTY)
        self.assert_equal(meta.ns, {})
        self.assert_equal(meta.children, [])

        body = html[3]
        self.assert_equal(body.qname, self.html_of('body'))
        self.assert_equal(body.attrib, {})
        self.assert_equal(body.type, markup.Element.OPEN)
        self.assert_equal(body.ns, {})
        self.assert_equal(len(body), 9)
        self.assert_ws(body, 0)
        self.assert_ws(body, 2)
        self.assert_ws(body, 3)
        self.assert_ws(body, 5)
        self.assert_ws(body, 6)
        self.assert_ws(body, 8)

        p = body[1]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['before border (Sausage)'])

        p = body[4]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['inside border (Sausage)'])

        p = body[7]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['after border (Sausage)'])

    def test_duplicate_ayame_elements(self):
        class Lobster(MarkupContainer):
            def __init__(self, id):
                super(Lobster, self).__init__(id)
                self.add(LobsterBorder('border'))

        class LobsterBorder(Border):
            pass

        with self.application():
            mc = Lobster('a')
            m, html = mc.render()
        self.assert_equal(m.xml_decl, {'version': '1.0'})
        self.assert_equal(m.lang, 'xhtml1')
        self.assert_equal(m.doctype, markup.XHTML1_STRICT)
        self.assert_true(m.root)

        self.assert_equal(html.qname, self.html_of('html'))
        self.assert_equal(html.attrib, {})
        self.assert_equal(html.type, markup.Element.OPEN)
        self.assert_equal(html.ns, {'': markup.XHTML_NS,
                                    'xml': markup.XML_NS,
                                    'ayame': markup.AYAME_NS})
        self.assert_equal(len(html), 5)
        self.assert_ws(html, 0)
        self.assert_ws(html, 2)
        self.assert_ws(html, 4)

        head = html[1]
        self.assert_equal(head.qname, self.html_of('head'))
        self.assert_equal(head.attrib, {})
        self.assert_equal(head.type, markup.Element.OPEN)
        self.assert_equal(head.ns, {})
        self.assert_equal(len(head), 8)
        self.assert_ws(head, 0)
        self.assert_ws(head, 2)
        self.assert_ws(head, 4)
        self.assert_ws(head, 5)
        self.assert_ws(head, 7)

        title = head[1]
        self.assert_equal(title.qname, self.html_of('title'))
        self.assert_equal(title.attrib, {})
        self.assert_equal(title.type, markup.Element.OPEN)
        self.assert_equal(title.ns, {})
        self.assert_equal(title.children, ['Lobster'])

        meta = head[3]
        self.assert_equal(meta.qname, self.html_of('meta'))
        self.assert_equal(meta.attrib, {self.html_of('name'): 'class',
                                        self.html_of('content'): 'Lobster'})
        self.assert_equal(meta.type, markup.Element.EMPTY)
        self.assert_equal(meta.ns, {})
        self.assert_equal(meta.children, [])

        meta = head[6]
        self.assert_equal(meta.qname, self.html_of('meta'))
        self.assert_equal(meta.attrib, {self.html_of('name'): 'class',
                                        self.html_of('content'): 'LobsterBorder'})
        self.assert_equal(meta.type, markup.Element.EMPTY)
        self.assert_equal(meta.ns, {})
        self.assert_equal(meta.children, [])

        body = html[3]
        self.assert_equal(body.qname, self.html_of('body'))
        self.assert_equal(body.attrib, {})
        self.assert_equal(body.type, markup.Element.OPEN)
        self.assert_equal(body.ns, {})
        self.assert_equal(len(body), 17)
        self.assert_ws(body, 0)
        self.assert_ws(body, 2)
        self.assert_ws(body, 3)
        self.assert_ws(body, 5)
        self.assert_ws(body, 6)
        self.assert_ws(body, 8)
        self.assert_ws(body, 9)
        self.assert_ws(body, 11)
        self.assert_ws(body, 13)
        self.assert_ws(body, 14)
        self.assert_ws(body, 16)

        p = body[1]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['before border (Lobster)'])

        p = body[4]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['before ayame:body (LobsterBorder)'])

        p = body[7]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(len(p), 3)
        p.normalize()
        self.assert_equal(p.children, ['inside border (LobsterBorder)'])

        ayame_body = body[10]
        self.assert_equal(ayame_body.qname, self.ayame_of('body'))
        self.assert_equal(ayame_body.attrib, {})
        self.assert_equal(ayame_body.type, markup.Element.EMPTY)
        self.assert_equal(ayame_body.ns, {})
        self.assert_equal(ayame_body.children, [])

        p = body[12]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['after ayame:body (LobsterBorder)'])

        p = body[15]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['after border (Lobster)'])

    def test_feedback_field_border(self):
        with self.application(self.new_environ()):
            p = ShallotsPage()
            status, headers, content = p()
        html = self.format(ShallotsPage, error=False)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

    def test_feedback_field_border_valid(self):
        query = ('{path}=form&'
                 'field:field_body:text=text')
        with self.application(self.new_environ(query=query)):
            p = ShallotsPage()
            status, headers, content = p()
        html = self.format(ShallotsPage, error=False)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

    def test_feedback_field_border_invalid(self):
        query = ('{path}=form&'
                 'field:field_body:text=')
        with self.application(self.new_environ(query=query)):
            p = ShallotsPage()
            status, headers, content = p()
        html = self.format(ShallotsPage, error=True)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

    def test_feedback_field_border_nonexistent_path(self):
        query = '{path}=border'
        with self.application(self.new_environ(query=query)):
            p = ShallotsPage()
            status, headers, content = p()
        html = self.format(ShallotsPage, error=False)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

    def test_render_ayame_message(self):
        with self.application(self.new_environ(accept='en')):
            p = TomatoPage()
            status, headers, content = p()
        html = self.format(TomatoPage, message='before, body, after')
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

    def test_render_ayame_message_ja(self):
        with self.application(self.new_environ(accept='ja, en')):
            p = TomatoPage()
            status, headers, content = p()
        html = self.format(TomatoPage, message=u'\u524d, \u4e2d, \u5f8c')
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])


class MarkupContainer(ayame.MarkupContainer):

    def render(self):
        m = self.load_markup()
        self.head = self.find_head(m.root)
        html = super(MarkupContainer, self).render(m.root)
        return m, html


class Border(border.Border):

    def __init__(self, id, model=None):
        super(Border, self).__init__(id, model)
        self.add(basic.Label('class', self.__class__.__name__))
        self.body.find('class').render_body_only = True

    def page(self):
        for parent in self.iter_parent():
            pass
        return parent


class TomatoPage(ayame.Page):

    html_t = u"""\
<?xml version="1.0"?>
{doctype}
<html xmlns="{xhtml}">
  <head>
    <title>TomatoPage</title>
  </head>
  <body>
    <p>{message}</p>
  </body>
</html>
"""

    def __init__(self):
        super(TomatoPage, self).__init__()
        self.add(TomatoBorder('border'))


class TomatoBorder(Border):
    pass


class ShallotsPage(ayame.Page):

    html_t = u"""\
<?xml version="1.0"?>
{doctype}
<html xmlns="{xhtml}">
  <head>
    <title>ShallotsPage</title>
  </head>
  <body>
    <form action="/" method="post">
      <div class="ayame-hidden"><input name="{path}" type="hidden" value="form" /></div>
      <fieldset>
        <legend>form</legend>
{error}
      </fieldset>
    </form>
  </body>
</html>
"""
    kwargs = {
        'error': lambda v=False: """\
        <div class="field-error">
          <input name="field:field_body:text" type="text" value="" /><br />
          <p class="feedback">&#x27;text&#x27; is required</p>
        </div>\
""" if v else """\
        <div class="field">
          <input name="field:field_body:text" type="text" value="" /><br />
        </div>\
"""
    }

    def __init__(self):
        super(ShallotsPage, self).__init__()
        self.add(form.Form('form'))
        self.find('form').add(border.FeedbackFieldBorder('field'))
        self.find('form:field').add(form.TextField('text'))
        self.find('form:field:field_body:text').required = True
