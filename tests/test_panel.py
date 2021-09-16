#
# test_panel
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import textwrap

import ayame
from ayame import basic, form, http, markup, panel
from base import AyameTestCase


class PanelTestCase(AyameTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.app.config['ayame.markup.pretty'] = True

    def test_panel(self):
        class Spam(MarkupContainer):
            def __init__(self, id):
                super().__init__(id)
                self.add(SpamPanel('panel'))

        class SpamPanel(Panel):
            pass

        with self.application():
            mc = Spam('a')
            self.assertTrue(mc.find('panel').render_body_only)
            self.assertTrue(mc.find('panel').has_markup)
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
            self.html_of('content'): 'SpamPanel',
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
        self.assertEqual(p.children, ['before panel (Spam)'])

        p = body[4]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(len(p), 3)
        p.normalize()
        self.assertEqual(p.children, ['inside ayame:panel (SpamPanel)'])

        p = body[7]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['after panel (Spam)'])

    def test_panel_with_markup_inheritance(self):
        class Eggs(MarkupContainer):
            def __init__(self, id):
                super().__init__(id)
                self.add(HamPanel('panel'))

        class EggsPanel(Panel):
            pass

        class HamPanel(EggsPanel):
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
            self.html_of('content'): 'EggsPanel',
        })
        self.assertEqual(meta.type, markup.Element.EMPTY)
        self.assertEqual(meta.ns, {})
        self.assertEqual(meta.children, [])

        meta = head[9]
        self.assertEqual(meta.qname, self.html_of('meta'))
        self.assertEqual(meta.attrib, {
            self.html_of('name'): 'class',
            self.html_of('content'): 'HamPanel',
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
        self.assertEqual(p.children, ['before panel (Eggs)'])

        p = body[4]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(len(p), 3)
        p.normalize()
        self.assertEqual(p.children, ['inside ayame:panel (HamPanel)'])

        p = body[7]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['after panel (Eggs)'])

    def test_invalid_markup_no_ayame_panel(self):
        class Toast(MarkupContainer):
            def __init__(self, id):
                super().__init__(id)
                self.add(ToastPanel('panel'))

        class ToastPanel(Panel):
            pass

        with self.application():
            mc = Toast('a')
            with self.assertRaisesRegex(ayame.RenderingError, r"'ayame:panel' .* not found\b"):
                mc.render()

    def test_invalid_markup_no_head(self):
        class Beans(MarkupContainer):
            def __init__(self, id):
                super().__init__(id)
                self.add(BeansPanel('panel'))

        class BeansPanel(Panel):
            pass

        with self.application():
            mc = Beans('a')
            with self.assertRaisesRegex(ayame.RenderingError, r"'head' .* not found\b"):
                mc.render()

    def test_invalid_markup_unknown_ayame_element(self):
        class Bacon(MarkupContainer):
            def __init__(self, id):
                super().__init__(id)
                self.add(BaconPanel('panel'))

        class BaconPanel(Panel):
            pass

        with self.application():
            mc = Bacon('a')
            with self.assertRaisesRegex(ayame.RenderingError, r"\bunknown .* 'ayame:bacon'"):
                mc.render()

    def test_empty_markup(self):
        class Sausage(MarkupContainer):
            def __init__(self, id):
                super().__init__(id)
                self.add(SausagePanel('panel'))

        class SausagePanel(Panel):
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
        self.assertEqual(p.children, ['before panel (Sausage)'])

        p = body[4]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['inside panel (Sausage)'])

        p = body[7]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['after panel (Sausage)'])

    def test_duplicate_ayame_elements(self):
        class Lobster(MarkupContainer):
            def __init__(self, id):
                super().__init__(id)
                self.add(LobsterPanel('panel'))

        class LobsterPanel(Panel):
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
            self.html_of('content'): 'LobsterPanel',
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
        self.assertEqual(p.children, ['before panel (Lobster)'])

        p = body[4]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(len(p), 3)
        p.normalize()
        self.assertEqual(p.children, ['inside ayame:panel (LobsterPanel)'])

        p = body[7]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['after panel (Lobster)'])

    def test_feedback_panel(self):
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

    def test_feedback_panel_valid(self):
        query = ('{path}=form&'
                 'text=text')
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

    def test_feedback_panel_invalid(self):
        query = ('{path}=form&'
                 'text=')
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

    def test_feedback_panel_nonexistent_path(self):
        query = '{path}=panel'
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
        html = self.format(TomatoPage, message='Hello World!')
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
        html = self.format(TomatoPage, message='\u3053\u3093\u306b\u3061\u306f\u4e16\u754c')
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


class Panel(panel.Panel):

    def __init__(self, id, model=None):
        super().__init__(id, model)
        self.add(basic.Label('class', self.__class__.__name__))
        self.find('class').render_body_only = True

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
        self.add(TomatoPanel('panel'))


class TomatoPanel(Panel):
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
                <input name="text" type="text" value="" /><br />
              </fieldset>
            </form>{error}
          </body>
        </html>
    """)
    kwargs = {
        'error': lambda v=False: textwrap.indent(textwrap.dedent("""
            <ul class="feedback-panel">
              <li>&#x27;text&#x27; is required</li>
            </ul>
        """), ' ' * 4).rstrip() if v else '',
    }

    def __init__(self):
        super().__init__()
        self.add(form.Form('form'))
        self.find('form').add(form.TextField('text'))
        self.find('form:text').required = True
        self.add(panel.FeedbackPanel('panel'))
