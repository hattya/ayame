#
# test_border
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import textwrap

import ayame
from ayame import basic, border, form, http, markup
from base import AyameTestCase


class BorderTestCase(AyameTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.app.config['ayame.markup.pretty'] = True

    def test_border(self):
        class Spam(MarkupContainer):
            def __init__(self, id):
                super().__init__(id)
                self.add(SpamBorder('border'))

        class SpamBorder(Border):
            pass

        with self.application():
            mc = Spam('a')
            self.assertTrue(mc.find('border').render_body_only)
            self.assertTrue(mc.find('border').has_markup)
            m, html = mc.render()
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, markup.XHTML1_STRICT)
        self.assertTrue(m.root)

        self.assertEqual(html.qname, self.html_of('html'))
        self.assertEqual(html.attrib, {})
        self.assertEqual(html.type, markup.Element.OPEN)
        self.assertEqual(html.ns, {
            '': markup.XHTML_NS,
            'xml': markup.XML_NS,
            'ayame': markup.AYAME_NS,
        })
        self.assertEqual(len(html), 5)
        self.assertWS(html, 0)
        self.assertWS(html, 2)
        self.assertWS(html, 4)

        head = html[1]
        self.assertEqual(head.qname, self.html_of('head'))
        self.assertEqual(head.attrib, {})
        self.assertEqual(head.type, markup.Element.OPEN)
        self.assertEqual(head.ns, {})
        self.assertEqual(len(head), 8)
        self.assertWS(head, 0)
        self.assertWS(head, 2)
        self.assertWS(head, 4)
        self.assertWS(head, 5)
        self.assertWS(head, 7)

        title = head[1]
        self.assertEqual(title.qname, self.html_of('title'))
        self.assertEqual(title.attrib, {})
        self.assertEqual(title.type, markup.Element.OPEN)
        self.assertEqual(title.ns, {})
        self.assertEqual(title.children, ['Spam'])

        meta = head[3]
        self.assertEqual(meta.qname, self.html_of('meta'))
        self.assertEqual(meta.attrib, {
            self.html_of('name'): 'class',
            self.html_of('content'): 'Spam',
        })
        self.assertEqual(meta.type, markup.Element.EMPTY)
        self.assertEqual(meta.ns, {})
        self.assertEqual(meta.children, [])

        meta = head[6]
        self.assertEqual(meta.qname, self.html_of('meta'))
        self.assertEqual(meta.attrib, {
            self.html_of('name'): 'class',
            self.html_of('content'): 'SpamBorder',
        })
        self.assertEqual(meta.type, markup.Element.EMPTY)
        self.assertEqual(meta.ns, {})
        self.assertEqual(meta.children, [])

        body = html[3]
        self.assertEqual(body.qname, self.html_of('body'))
        self.assertEqual(body.attrib, {})
        self.assertEqual(body.type, markup.Element.OPEN)
        self.assertEqual(body.ns, {})
        self.assertEqual(len(body), 15)
        self.assertWS(body, 0)
        self.assertWS(body, 2)
        self.assertWS(body, 3)
        self.assertWS(body, 5)
        self.assertWS(body, 6)
        self.assertWS(body, 8)
        self.assertWS(body, 9)
        self.assertWS(body, 11)
        self.assertWS(body, 12)
        self.assertWS(body, 14)

        p = body[1]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['before border (Spam)'])

        p = body[4]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['before ayame:body (SpamBorder)'])

        p = body[7]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(len(p), 3)
        p.normalize()
        self.assertEqual(p.children, ['inside border (SpamBorder)'])

        p = body[10]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['after ayame:body (SpamBorder)'])

        p = body[13]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['after border (Spam)'])

    def test_border_with_markup_inheritance(self):
        class Eggs(MarkupContainer):
            def __init__(self, id):
                super().__init__(id)
                self.add(HamBorder('border'))

        class EggsBorder(Border):
            pass

        class HamBorder(EggsBorder):
            pass

        with self.application():
            mc = Eggs('a')
            m, html = mc.render()
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, markup.XHTML1_STRICT)
        self.assertTrue(m.root)

        self.assertEqual(html.qname, self.html_of('html'))
        self.assertEqual(html.attrib, {})
        self.assertEqual(html.type, markup.Element.OPEN)
        self.assertEqual(html.ns, {
            '': markup.XHTML_NS,
            'xml': markup.XML_NS,
            'ayame': markup.AYAME_NS,
        })
        self.assertEqual(len(html), 5)
        self.assertWS(html, 0)
        self.assertWS(html, 2)
        self.assertWS(html, 4)

        head = html[1]
        self.assertEqual(head.qname, self.html_of('head'))
        self.assertEqual(head.attrib, {})
        self.assertEqual(head.type, markup.Element.OPEN)
        self.assertEqual(head.ns, {})
        self.assertEqual(len(head), 11)
        self.assertWS(head, 0)
        self.assertWS(head, 2)
        self.assertWS(head, 4)
        self.assertWS(head, 5)
        self.assertWS(head, 7)
        self.assertWS(head, 8)
        self.assertWS(head, 10)

        title = head[1]
        self.assertEqual(title.qname, self.html_of('title'))
        self.assertEqual(title.attrib, {})
        self.assertEqual(title.type, markup.Element.OPEN)
        self.assertEqual(title.ns, {})
        self.assertEqual(title.children, ['Eggs'])

        meta = head[3]
        self.assertEqual(meta.qname, self.html_of('meta'))
        self.assertEqual(meta.attrib, {
            self.html_of('name'): 'class',
            self.html_of('content'): 'Eggs',
        })
        self.assertEqual(meta.type, markup.Element.EMPTY)
        self.assertEqual(meta.ns, {})
        self.assertEqual(meta.children, [])

        meta = head[6]
        self.assertEqual(meta.qname, self.html_of('meta'))
        self.assertEqual(meta.attrib, {
            self.html_of('name'): 'class',
            self.html_of('content'): 'EggsBorder',
        })
        self.assertEqual(meta.type, markup.Element.EMPTY)
        self.assertEqual(meta.ns, {})
        self.assertEqual(meta.children, [])

        meta = head[9]
        self.assertEqual(meta.qname, self.html_of('meta'))
        self.assertEqual(meta.attrib, {
            self.html_of('name'): 'class',
            self.html_of('content'): 'HamBorder',
        })
        self.assertEqual(meta.type, markup.Element.EMPTY)
        self.assertEqual(meta.ns, {})
        self.assertEqual(meta.children, [])

        body = html[3]
        self.assertEqual(body.qname, self.html_of('body'))
        self.assertEqual(body.attrib, {})
        self.assertEqual(body.type, markup.Element.OPEN)
        self.assertEqual(body.ns, {})
        self.assertEqual(len(body), 15)
        self.assertWS(body, 0)
        self.assertWS(body, 2)
        self.assertWS(body, 3)
        self.assertWS(body, 5)
        self.assertWS(body, 6)
        self.assertWS(body, 8)
        self.assertWS(body, 9)
        self.assertWS(body, 11)
        self.assertWS(body, 12)
        self.assertWS(body, 14)

        p = body[1]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['before border (Eggs)'])

        p = body[4]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['before ayame:body (HamBorder)'])

        p = body[7]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(len(p), 3)
        p.normalize()
        self.assertEqual(p.children, ['inside border (HamBorder)'])

        p = body[10]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['after ayame:body (HamBorder)'])

        p = body[13]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['after border (Eggs)'])

    def test_invalid_markup_no_ayame_border(self):
        class Toast(MarkupContainer):
            def __init__(self, id):
                super().__init__(id)
                self.add(ToastBorder('border'))

        class ToastBorder(Border):
            pass

        with self.application():
            mc = Toast('a')
            with self.assertRaisesRegex(ayame.RenderingError, r"'ayame:border' .* not found\b"):
                mc.render()

    def test_invalid_markup_no_ayame_body(self):
        class Beans(MarkupContainer):
            def __init__(self, id):
                super().__init__(id)
                self.add(BeansBorder('border'))

        class BeansBorder(Border):
            pass

        with self.application():
            mc = Beans('a')
            with self.assertRaisesRegex(ayame.RenderingError, r"'ayame:body' .* not found\b"):
                mc.render()

    def test_invalid_markup_unknown_ayame_element(self):
        class Bacon(MarkupContainer):
            def __init__(self, id):
                super().__init__(id)
                self.add(BaconBorder('border'))

        class BaconBorder(Border):
            pass

        with self.application():
            mc = Bacon('a')
            with self.assertRaisesRegex(ayame.RenderingError, r"\bunknown .* 'ayame:bacon'"):
                mc.render()

    def test_empty_markup(self):
        class Sausage(MarkupContainer):
            def __init__(self, id):
                super().__init__(id)
                self.add(SausageBorder('border'))

        class SausageBorder(Border):
            pass

        with self.application():
            mc = Sausage('a')
            m, html = mc.render()
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, markup.XHTML1_STRICT)
        self.assertTrue(m.root)

        self.assertEqual(html.qname, self.html_of('html'))
        self.assertEqual(html.attrib, {})
        self.assertEqual(html.type, markup.Element.OPEN)
        self.assertEqual(html.ns, {
            '': markup.XHTML_NS,
            'xml': markup.XML_NS,
            'ayame': markup.AYAME_NS,
        })
        self.assertEqual(len(html), 5)
        self.assertWS(html, 0)
        self.assertWS(html, 2)
        self.assertWS(html, 4)

        head = html[1]
        self.assertEqual(head.qname, self.html_of('head'))
        self.assertEqual(head.attrib, {})
        self.assertEqual(head.type, markup.Element.OPEN)
        self.assertEqual(head.ns, {})
        self.assertEqual(len(head), 5)
        self.assertWS(head, 0)
        self.assertWS(head, 2)
        self.assertWS(head, 4)

        title = head[1]
        self.assertEqual(title.qname, self.html_of('title'))
        self.assertEqual(title.attrib, {})
        self.assertEqual(title.type, markup.Element.OPEN)
        self.assertEqual(title.ns, {})
        self.assertEqual(title.children, ['Sausage'])

        meta = head[3]
        self.assertEqual(meta.qname, self.html_of('meta'))
        self.assertEqual(meta.attrib, {
            self.html_of('name'): 'class',
            self.html_of('content'): 'Sausage',
        })
        self.assertEqual(meta.type, markup.Element.EMPTY)
        self.assertEqual(meta.ns, {})
        self.assertEqual(meta.children, [])

        body = html[3]
        self.assertEqual(body.qname, self.html_of('body'))
        self.assertEqual(body.attrib, {})
        self.assertEqual(body.type, markup.Element.OPEN)
        self.assertEqual(body.ns, {})
        self.assertEqual(len(body), 9)
        self.assertWS(body, 0)
        self.assertWS(body, 2)
        self.assertWS(body, 3)
        self.assertWS(body, 5)
        self.assertWS(body, 6)
        self.assertWS(body, 8)

        p = body[1]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['before border (Sausage)'])

        p = body[4]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['inside border (Sausage)'])

        p = body[7]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['after border (Sausage)'])

    def test_duplicate_ayame_elements(self):
        class Lobster(MarkupContainer):
            def __init__(self, id):
                super().__init__(id)
                self.add(LobsterBorder('border'))

        class LobsterBorder(Border):
            pass

        with self.application():
            mc = Lobster('a')
            m, html = mc.render()
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, markup.XHTML1_STRICT)
        self.assertTrue(m.root)

        self.assertEqual(html.qname, self.html_of('html'))
        self.assertEqual(html.attrib, {})
        self.assertEqual(html.type, markup.Element.OPEN)
        self.assertEqual(html.ns, {
            '': markup.XHTML_NS,
            'xml': markup.XML_NS,
            'ayame': markup.AYAME_NS,
        })
        self.assertEqual(len(html), 5)
        self.assertWS(html, 0)
        self.assertWS(html, 2)
        self.assertWS(html, 4)

        head = html[1]
        self.assertEqual(head.qname, self.html_of('head'))
        self.assertEqual(head.attrib, {})
        self.assertEqual(head.type, markup.Element.OPEN)
        self.assertEqual(head.ns, {})
        self.assertEqual(len(head), 8)
        self.assertWS(head, 0)
        self.assertWS(head, 2)
        self.assertWS(head, 4)
        self.assertWS(head, 5)
        self.assertWS(head, 7)

        title = head[1]
        self.assertEqual(title.qname, self.html_of('title'))
        self.assertEqual(title.attrib, {})
        self.assertEqual(title.type, markup.Element.OPEN)
        self.assertEqual(title.ns, {})
        self.assertEqual(title.children, ['Lobster'])

        meta = head[3]
        self.assertEqual(meta.qname, self.html_of('meta'))
        self.assertEqual(meta.attrib, {
            self.html_of('name'): 'class',
            self.html_of('content'): 'Lobster',
        })
        self.assertEqual(meta.type, markup.Element.EMPTY)
        self.assertEqual(meta.ns, {})
        self.assertEqual(meta.children, [])

        meta = head[6]
        self.assertEqual(meta.qname, self.html_of('meta'))
        self.assertEqual(meta.attrib, {
            self.html_of('name'): 'class',
            self.html_of('content'): 'LobsterBorder',
        })
        self.assertEqual(meta.type, markup.Element.EMPTY)
        self.assertEqual(meta.ns, {})
        self.assertEqual(meta.children, [])

        body = html[3]
        self.assertEqual(body.qname, self.html_of('body'))
        self.assertEqual(body.attrib, {})
        self.assertEqual(body.type, markup.Element.OPEN)
        self.assertEqual(body.ns, {})
        self.assertEqual(len(body), 17)
        self.assertWS(body, 0)
        self.assertWS(body, 2)
        self.assertWS(body, 3)
        self.assertWS(body, 5)
        self.assertWS(body, 6)
        self.assertWS(body, 8)
        self.assertWS(body, 9)
        self.assertWS(body, 11)
        self.assertWS(body, 13)
        self.assertWS(body, 14)
        self.assertWS(body, 16)

        p = body[1]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['before border (Lobster)'])

        p = body[4]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['before ayame:body (LobsterBorder)'])

        p = body[7]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(len(p), 3)
        p.normalize()
        self.assertEqual(p.children, ['inside border (LobsterBorder)'])

        ayame_body = body[10]
        self.assertEqual(ayame_body.qname, self.ayame_of('body'))
        self.assertEqual(ayame_body.attrib, {})
        self.assertEqual(ayame_body.type, markup.Element.EMPTY)
        self.assertEqual(ayame_body.ns, {})
        self.assertEqual(ayame_body.children, [])

        p = body[12]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['after ayame:body (LobsterBorder)'])

        p = body[15]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['after border (Lobster)'])

    def test_feedback_field_border(self):
        with self.application(self.new_environ()):
            p = ShallotsPage()
            status, headers, content = p()
        html = self.format(ShallotsPage, error=False)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

    def test_feedback_field_border_valid(self):
        query = ('{path}=form&'
                 'field:field_body:text=text')
        with self.application(self.new_environ(query=query)):
            p = ShallotsPage()
            status, headers, content = p()
        html = self.format(ShallotsPage, error=False)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

    def test_feedback_field_border_invalid(self):
        query = ('{path}=form&'
                 'field:field_body:text=')
        with self.application(self.new_environ(query=query)):
            p = ShallotsPage()
            status, headers, content = p()
        html = self.format(ShallotsPage, error=True)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

    def test_feedback_field_border_nonexistent_path(self):
        query = '{path}=border'
        with self.application(self.new_environ(query=query)):
            p = ShallotsPage()
            status, headers, content = p()
        html = self.format(ShallotsPage, error=False)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

    def test_render_ayame_message(self):
        with self.application(self.new_environ(accept='en')):
            p = TomatoPage()
            status, headers, content = p()
        html = self.format(TomatoPage, message='before, body, after')
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

    def test_render_ayame_message_ja(self):
        with self.application(self.new_environ(accept='ja, en')):
            p = TomatoPage()
            status, headers, content = p()
        html = self.format(TomatoPage, message='\u524d, \u4e2d, \u5f8c')
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])


class MarkupContainer(ayame.MarkupContainer):

    def render(self):
        m = self.load_markup()
        self.head = self.find_head(m.root)
        html = super().render(m.root)
        return m, html


class Border(border.Border):

    def __init__(self, id, model=None):
        super().__init__(id, model)
        self.add(basic.Label('class', self.__class__.__name__))
        self.body.find('class').render_body_only = True

    def page(self):
        for parent in self.iter_parent():
            pass
        return parent


class TomatoPage(ayame.Page):

    html_t = textwrap.dedent("""\
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
    """)

    def __init__(self):
        super().__init__()
        self.add(TomatoBorder('border'))


class TomatoBorder(Border):
    pass


class ShallotsPage(ayame.Page):

    html_t = textwrap.dedent("""\
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
    """)
    kwargs = {
        'error': lambda v=False: textwrap.indent(textwrap.dedent("""\
            <div class="field-error">
              <input name="field:field_body:text" type="text" value="" /><br />
              <p class="feedback">&#x27;text&#x27; is required</p>
            </div>
        """ if v else """\
            <div class="field">
              <input name="field:field_body:text" type="text" value="" /><br />
            </div>
        """), ' ' * 8).rstrip(),
    }

    def __init__(self):
        super().__init__()
        self.add(form.Form('form'))
        self.find('form').add(border.FeedbackFieldBorder('field'))
        self.find('form:field').add(form.TextField('text'))
        self.find('form:field:field_body:text').required = True
