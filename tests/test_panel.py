#
# test_panel
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import textwrap
import unittest.mock

import ayame
from ayame import basic, form, http, markup, panel
from base import AyameTestCase, ElementBuilder


class PanelTestCase(AyameTestCase):

    def test_panel(self):
        class SpamPanel(panel.Panel):
            pass

        with self.application():
            p = SpamPage(SpamPanel)
            m, rv = p.inspect()
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, markup.XHTML1_STRICT)
        self.assertTrue(m.root)

        b = ElementBuilder(markup.XHTML_NS)
        lv = self.lv
        with b.open('html',
                    ns=self.ns):
            b.str(lv[1])
            with b.open('head'):
                b.str(lv[2])
                with b.open('title'):
                    b.str('SpamPage')
                b.str(lv[2])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'SpamPage',
                        })
                b.str(lv[1])
                b.str(lv[3])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'SpamPanel',
                        })
                b.str(lv[2])
            b.str(lv[1])
            with b.open('body'):
                b.str(lv[2])
                with b.open('p'):
                    b.str('before panel (SpamPage)')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('inside ayame:panel (')
                    b.str('SpamPanel')
                    b.str(')')
                b.str(lv[2])
                b.str(lv[2])
                with b.open('p'):
                    b.str('after panel (SpamPage)')
                b.str(lv[1])
            b.str(lv[0])
        self.assertElementEqual(rv, b.root)

    def test_panel_with_markup_inheritance_in_superclass(self):
        class EggsPanel(panel.Panel):
            pass

        class HamPanel(EggsPanel):
            pass

        with self.application():
            p = SpamPage(HamPanel)
            m, rv = p.inspect()
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, markup.XHTML1_STRICT)
        self.assertTrue(m.root)

        b = ElementBuilder(markup.XHTML_NS)
        lv = self.lv
        with b.open('html',
                    ns=self.ns):
            b.str(lv[1])
            with b.open('head'):
                b.str(lv[2])
                with b.open('title'):
                    b.str('SpamPage')
                b.str(lv[2])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'SpamPage',
                        })
                b.str(lv[1])
                b.str(lv[3])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'EggsPanel',
                        })
                b.str(lv[2])
                b.str(lv[3])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'HamPanel',
                        })
                b.str(lv[2])
            b.str(lv[1])
            with b.open('body'):
                b.str(lv[2])
                with b.open('p'):
                    b.str('before panel (SpamPage)')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('before ayame:child (EggsPanel)')
                b.str(lv[3])
                b.str(lv[3])
                with b.open('p'):
                    b.str('inside ayame:extend (')
                    b.str('HamPanel')
                    b.str(')')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('after ayame:child (EggsPanel)')
                b.str(lv[2])
                b.str(lv[2])
                with b.open('p'):
                    b.str('after panel (SpamPage)')
                b.str(lv[1])
            b.str(lv[0])
        self.assertElementEqual(rv, b.root)

    def test_panel_with_markup_inheritance_in_subclass(self):
        class ToastPanel(panel.Panel):
            pass

        class BeansPanel(ToastPanel):
            pass

        with self.application():
            p = SpamPage(BeansPanel)
            m, rv = p.inspect()
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, markup.XHTML1_STRICT)
        self.assertTrue(m.root)

        b = ElementBuilder(markup.XHTML_NS)
        lv = self.lv
        with b.open('html',
                    ns=self.ns):
            b.str(lv[1])
            with b.open('head'):
                b.str(lv[2])
                with b.open('title'):
                    b.str('SpamPage')
                b.str(lv[2])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'SpamPage',
                        })
                b.str(lv[1])
                b.str(lv[3])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'ToastPanel',
                        })
                b.str(lv[2])
                b.str(lv[3])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'BeansPanel',
                        })
                b.str(lv[2])
            b.str(lv[1])
            with b.open('body'):
                b.str(lv[2])
                with b.open('p'):
                    b.str('before panel (SpamPage)')
                b.str(lv[2])
                b.str(lv[4])
                with b.open('p'):
                    b.str('inside ayame:panel (')
                    b.str('BeansPanel')
                    b.str(')')
                b.str(lv[3])
                b.str(lv[2])
                with b.open('p'):
                    b.str('after panel (SpamPage)')
                b.str(lv[1])
            b.str(lv[0])
        self.assertElementEqual(rv, b.root)

    def test_panel_with_empty_markup(self):
        class BaconPanel(panel.Panel):
            pass

        with self.application():
            p = SpamPage(BaconPanel)
            m, rv = p.inspect()
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, markup.XHTML1_STRICT)
        self.assertTrue(m.root)

        b = ElementBuilder(markup.XHTML_NS)
        lv = self.lv
        with b.open('html',
                    ns=self.ns):
            b.str(lv[1])
            with b.open('head'):
                b.str(lv[2])
                with b.open('title'):
                    b.str('SpamPage')
                b.str(lv[2])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'SpamPage',
                        })
                b.str(lv[1])
            b.str(lv[1])
            with b.open('body'):
                b.str(lv[2])
                with b.open('p'):
                    b.str('before panel (SpamPage)')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('inside panel (SpamPage)')
                b.str(lv[2])
                b.str(lv[2])
                with b.open('p'):
                    b.str('after panel (SpamPage)')
                b.str(lv[1])
            b.str(lv[0])
        self.assertElementEqual(rv, b.root)

    def test_panel_with_duplicate_ayame_elements(self):
        class SausagePanel(panel.Panel):
            pass

        with self.application():
            p = SpamPage(SausagePanel)
            m, rv = p.inspect()
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, markup.XHTML1_STRICT)
        self.assertTrue(m.root)

        b = ElementBuilder(markup.XHTML_NS)
        lv = self.lv
        with b.open('html',
                    ns=self.ns):
            b.str(lv[1])
            with b.open('head'):
                b.str(lv[2])
                with b.open('title'):
                    b.str('SpamPage')
                b.str(lv[2])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'SpamPage',
                        })
                b.str(lv[1])
                b.str(lv[3])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'SausagePanel',
                        })
                b.str(lv[2])
            b.str(lv[1])
            with b.open('body'):
                b.str(lv[2])
                with b.open('p'):
                    b.str('before panel (SpamPage)')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('inside ayame:panel (')
                    b.str('SausagePanel')
                    b.str(')')
                b.str(lv[2])
                b.str(lv[2])
                with b.open('p'):
                    b.str('after panel (SpamPage)')
                b.str(lv[1])
            b.str(lv[0])
        self.assertElementEqual(rv, b.root)

    def test_panel_without_ayame_panel(self):
        class TomatoPanel(panel.Panel):
            pass

        with self.application():
            p = SpamPage(TomatoPanel)
            with self.assertRaisesRegex(ayame.RenderingError, r"'ayame:panel' .* not found\b"):
                p.inspect()

    def test_panel_with_ayame_message(self):
        for a, t, m in (
            (
                'en',
                'Title',
                'Hello World!',
            ),
            (
                'ja, en',
                '\u30bf\u30a4\u30c8\u30eb',
                '\u3053\u3093\u306b\u3061\u306f\u4e16\u754c',
            ),
        ):
            with self.subTest(accept_language=a):
                with self.application(self.new_environ(accept=a)):
                    p = LobsterPage()
                    status, headers, content = p()
                html = self.format(type(p), title=t, message=m)
                self.assertEqual(status, http.OK.status)
                self.assertEqual(headers, [
                    ('Content-Type', 'text/html; charset=UTF-8'),
                    ('Content-Length', str(len(html))),
                ])
                self.assertEqual(content, [html])

    def test_feedback_panel(self):
        with unittest.mock.patch.dict(self.app.config):
            self.app.config['ayame.markup.pretty'] = True
            for q, e in (
                # no data
                (
                    None,
                    False,
                ),
                # valid data
                (
                    '&'.join((
                        f'{ayame.AYAME_PATH}=form',
                        'text=text',
                    )),
                    False,
                ),
                # invalid data
                (
                    '&'.join((
                        f'{ayame.AYAME_PATH}=form',
                        'text=',
                    )),
                    True,
                ),
                # nonexistent path
                (
                    f'{ayame.AYAME_PATH}=panel',
                    False,
                ),
            ):
                with self.subTest(query=q):
                    with self.application(self.new_environ(query=q)):
                        p = ShallotsPage()
                        status, headers, content = p()
                    html = self.format(type(p), error=e)
                    self.maxDiff = None
                    self.assertEqual(content[0].decode(), html.decode())
                    self.assertEqual(status, http.OK.status)
                    self.assertEqual(headers, [
                        ('Content-Type', 'text/html; charset=UTF-8'),
                        ('Content-Length', str(len(html))),
                    ])
                    self.assertEqual(content, [html])


class Page(ayame.Page):

    def __init__(self, cls):
        super().__init__()
        self.add(cls('panel'))
        self.find('panel').add(basic.Label('class', cls.__name__))
        self.find('panel:class').render_body_only = True

    def inspect(self):
        m = self.load_markup()
        self.head = self.find_head(m.root)
        root = super().render(m.root)
        return m, root


class SpamPage(Page):
    pass


class LobsterPage(Page):

    html_t = """\
        <?xml version="1.0"?>
        {doctype}
        <html xmlns="{xhtml}">
          <head>
            <title>LobsterPage</title>
          </head>
          <body>
            <h1>{title}</h1>
            <p>{message}</p>
          </body>
        </html>
    """

    def __init__(self):
        super().__init__(LobsterPanel)


class LobsterPanel(panel.Panel):
    pass


class ShallotsPage(ayame.Page):

    html_t = """\
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
    """
    kwargs = {
        'error': lambda v=False: textwrap.indent(textwrap.dedent("""
            <ul class="feedback-panel">
              <li>&#x27;text&#x27; is required</li>
            </ul>
        """), '  ' * 2).rstrip() if v else '',
    }

    def __init__(self):
        super().__init__()
        self.add(form.Form('form'))
        self.find('form').add(form.TextField('text'))
        self.find('form:text').required = True
        self.add(panel.FeedbackPanel('panel'))
