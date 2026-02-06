#
# test_border
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import textwrap
import unittest.mock

import ayame
from ayame import basic, border, form, http, markup
from base import AyameTestCase, ElementBuilder


class BorderTestCase(AyameTestCase):

    def test_border(self):
        class SpamBorder(border.Border):
            pass

        with self.application():
            p = SpamPage(SpamBorder)
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
                            'content': 'SpamBorder',
                        })
                b.str(lv[2])
            b.str(lv[1])
            with b.open('body'):
                b.str(lv[2])
                with b.open('p'):
                    b.str('before border (SpamPage)')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('before ayame:body (SpamBorder)')
                b.str(lv[3])
                b.str(lv[3])
                with b.open('p'):
                    b.str('inside border (')
                    b.str('SpamBorder')
                    b.str(')')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('after ayame:body (SpamBorder)')
                b.str(lv[2])
                b.str(lv[2])
                with b.open('p'):
                    b.str('after border (SpamPage)')
                b.str(lv[1])
            b.str(lv[0])
        self.assertElementEqual(rv, b.root)

    def test_border_with_markup_inheritance_in_superclass(self):
        class EggsBorder(border.Border):
            pass

        class HamBorder(EggsBorder):
            pass

        with self.application():
            p = SpamPage(HamBorder)
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
                            'content': 'EggsBorder',
                        })
                b.str(lv[2])
                b.str(lv[3])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'HamBorder',
                        })
                b.str(lv[2])
            b.str(lv[1])
            with b.open('body'):
                b.str(lv[2])
                with b.open('p'):
                    b.str('before border (SpamPage)')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('before ayame:child (EggsBorder)')
                b.str(lv[3])
                b.str(lv[3])
                with b.open('p'):
                    b.str('before ayame:body (HamBorder)')
                b.str(lv[3])
                b.str(lv[3])
                with b.open('p'):
                    b.str('inside border (')
                    b.str('HamBorder')
                    b.str(')')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('after ayame:body (HamBorder)')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('after ayame:child (EggsBorder)')
                b.str(lv[2])
                b.str(lv[2])
                with b.open('p'):
                    b.str('after border (SpamPage)')
                b.str(lv[1])
            b.str(lv[0])
        self.assertElementEqual(rv, b.root)

    def test_border_with_markup_inheritance_in_subclass(self):
        class ToastBorder(border.Border):
            pass

        class BeansBorder(ToastBorder):
            pass

        with self.application():
            p = SpamPage(BeansBorder)
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
                            'content': 'ToastBorder',
                        })
                b.str(lv[2])
                b.str(lv[3])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'BeansBorder',
                        })
                b.str(lv[2])
            b.str(lv[1])
            with b.open('body'):
                b.str(lv[2])
                with b.open('p'):
                    b.str('before border (SpamPage)')
                b.str(lv[2])
                b.str(lv[4])
                with b.open('p'):
                    b.str('before ayame:body (BeansBorder)')
                b.str(lv[4])
                b.str(lv[3])
                with b.open('p'):
                    b.str('inside border (')
                    b.str('BeansBorder')
                    b.str(')')
                b.str(lv[2])
                b.str(lv[4])
                with b.open('p'):
                    b.str('after ayame:body (BeansBorder)')
                b.str(lv[3])
                b.str(lv[2])
                with b.open('p'):
                    b.str('after border (SpamPage)')
                b.str(lv[1])
            b.str(lv[0])
        self.assertElementEqual(rv, b.root)

    def test_border_without_ayame_head(self):
        class BaconBorder(border.Border):
            pass

        with self.application():
            p = SpamPage(BaconBorder)
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
                    b.str('before border (SpamPage)')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('before ayame:body (BaconBorder)')
                b.str(lv[3])
                b.str(lv[3])
                with b.open('p'):
                    b.str('inside border (')
                    b.str('BaconBorder')
                    b.str(')')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('after ayame:body (BaconBorder)')
                b.str(lv[2])
                b.str(lv[2])
                with b.open('p'):
                    b.str('after border (SpamPage)')
                b.str(lv[1])
            b.str(lv[0])
        self.assertElementEqual(rv, b.root)

    def test_border_with_empty_markup(self):
        class SausageBorder(border.Border):
            pass

        with self.application():
            p = SausagePage(SausageBorder)
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
                    b.str('SausagePage')
                b.str(lv[2])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'SausagePage',
                        })
                b.str(lv[1])
            b.str(lv[1])
            with b.open('body'):
                b.str(lv[2])
                with b.open('p'):
                    b.str('before border (SausagePage)')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('inside border (SausagePage)')
                b.str(lv[2])
                b.str(lv[2])
                with b.open('p'):
                    b.str('after border (SausagePage)')
                b.str(lv[1])
            b.str(lv[0])
        self.assertElementEqual(rv, b.root)

    def test_border_with_duplicate_ayame_elements(self):
        class TomatoBorder(border.Border):
            pass

        with self.application():
            p = SpamPage(TomatoBorder)
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
                            'content': 'TomatoBorder',
                        })
                b.str(lv[2])
            b.str(lv[1])
            with b.open('body'):
                b.str(lv[2])
                with b.open('p'):
                    b.str('before border (SpamPage)')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('before ayame:body (TomatoBorder)')
                b.str(lv[3])
                b.str(lv[3])
                with b.open('p'):
                    b.str('inside border (')
                    b.str('TomatoBorder')
                    b.str(')')
                b.str(lv[2])
                b.str(lv[3])
                b.empty('ayame:body')
                b.str(lv[3])
                with b.open('p'):
                    b.str('after ayame:body (TomatoBorder)')
                b.str(lv[2])
                b.str(lv[2])
                with b.open('p'):
                    b.str('after border (SpamPage)')
                b.str(lv[1])
            b.str(lv[0])
        self.assertElementEqual(rv, b.root)

    def test_border_without_ayame_border(self):
        class LobsterBorder(border.Border):
            pass

        with self.application():
            p = SpamPage(LobsterBorder)
            with self.assertRaisesRegex(ayame.RenderingError, r"'ayame:border' .* not found\b"):
                p.inspect()

    def test_border_without_ayame_body(self):
        class ShallotsBorder(border.Border):
            pass

        with self.application():
            p = SpamPage(ShallotsBorder)
            with self.assertRaisesRegex(ayame.RenderingError, r"'ayame:body' .* not found\b"):
                p.inspect()

    def test_border_with_ayame_message(self):
        for a, t, m in (
            (
                'en',
                'Title',
                'Hop - Step - Jump',
            ),
            (
                'ja, en',
                '\u30bf\u30a4\u30c8\u30eb',
                '\u30db\u30c3\u30d7 - \u30b9\u30c6\u30c3\u30d7 - \u30b8\u30e3\u30f3\u30d7',
            ),
        ):
            with self.subTest(accept_language=a):
                with self.application(self.new_environ(accept=a)):
                    p = AuberginePage()
                    status, headers, content = p()
                html = self.format(type(p), title=t, message=m)
                self.assertEqual(status, http.OK.status)
                self.assertEqual(headers, [
                    ('Content-Type', 'text/html; charset=UTF-8'),
                    ('Content-Length', str(len(html))),
                ])
                self.assertEqual(content, [html])

    def test_feedback_field_border(self):
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
                    '&'.join ((
                        f'{ayame.AYAME_PATH}=form',
                        'field:field_body:text=text',
                    )),
                    False,
                ),
                # invalid data
                (
                    '&'.join((
                        f'{ayame.AYAME_PATH}=form',
                        'field:field_body:text=',
                    )),
                    True,
                ),
                # nonexistent path
                (
                    f'{ayame.AYAME_PATH}=border',
                    False,
                ),
            ):
                with self.subTest(query=q):
                    with self.application(self.new_environ(query=q)):
                        p = TrufflePage()
                        status, headers, content = p()
                    html = self.format(type(p), error=e)
                    self.assertEqual(status, http.OK.status)
                    self.assertEqual(headers, [
                        ('Content-Type', 'text/html; charset=UTF-8'),
                        ('Content-Length', str(len(html))),
                    ])
                    self.assertEqual(content, [html])


class Page(ayame.Page):

    def __init__(self, cls):
        super().__init__()
        self.add(cls('border'))
        self.find('border').add(basic.Label('class', cls.__name__))
        self.find('border').body.find('class').render_body_only = True

    def inspect(self):
        m = self.load_markup()
        self.head = self.find_head(m.root)
        root = super().render(m.root)
        return m, root


class SpamPage(Page):
    pass


class SausagePage(Page):
    pass


class AuberginePage(ayame.Page):

    html_t = """\
        <?xml version="1.0"?>
        {doctype}
        <html xmlns="{xhtml}">
          <head>
            <title>AuberginePage</title>
          </head>
          <body>
            <h1>{title}</h1>
            <p>{message}</p>
          </body>
        </html>
    """

    def __init__(self):
        super().__init__()
        self.add(AubergineBorder('border'))


class AubergineBorder(border.Border):
    pass


class TrufflePage(ayame.Page):

    html_t = textwrap.dedent("""\
        <?xml version="1.0"?>
        {doctype}
        <html xmlns="{xhtml}">
          <head>
            <title>TrufflePage</title>
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
        """), '  ' * 4).rstrip(),
    }

    def __init__(self):
        super().__init__()
        self.add(form.Form('form'))
        self.find('form').add(border.FeedbackFieldBorder('field'))
        self.find('form:field').add(form.TextField('text'))
        self.find('form:field:field_body:text').required = True
