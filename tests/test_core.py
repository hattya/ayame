#
# test_core
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import unittest.mock

import ayame
from ayame import http, markup, model
from base import AyameTestCase, ElementBuilder


class CoreTestCase(AyameTestCase):

    def test_component(self):
        with self.assertRaisesRegex(ayame.ComponentError, r' id .* not set\b'):
            ayame.Component('')

        c = ayame.Component('a')
        self.assertEqual(c.id, 'a')
        self.assertIsNone(c.model)
        self.assertIsNone(c.model_object)
        self.assertEqual(c.model_object_as_string(), '')
        with self.assertRaisesRegex(ayame.ComponentError, r'\bmodel .* not set\b'):
            c.model_object = ''
        with self.assertRaises(ayame.AyameError):
            c.app
        with self.assertRaises(ayame.AyameError):
            c.config
        with self.assertRaises(ayame.AyameError):
            c.environ
        with self.assertRaises(ayame.AyameError):
            c.request
        with self.assertRaises(ayame.AyameError):
            c.session
        with self.assertRaises(ayame.AyameError):
            c.forward(c)
        with self.assertRaises(ayame.AyameError):
            c.redirect(c)
        with self.assertRaises(ayame.AyameError):
            c.tr('key')
        with self.assertRaises(ayame.AyameError):
            c.uri_for(c)
        with self.assertRaisesRegex(ayame.ComponentError, r' not attached .*\.Page\b'):
            c.page()
        self.assertEqual(c.path(), 'a')

        c.add(None, True, 0, 3.14, '')
        self.assertEqual(c.behaviors, [])

        el = self.empty_element()
        self.assertIs(c.render(el), el)
        self.assertIsNone(c.render(None))
        c.visible = False
        self.assertIsNone(c.render(el))

    def test_component_with_model(self):
        with self.assertRaisesRegex(ayame.ComponentError, r' not .* instance of Model\b'):
            ayame.Component('a', '')

        m = model.Model(None)
        c = ayame.Component('a', m)
        self.assertEqual(c.id, 'a')
        self.assertIs(c.model, m)
        self.assertIsNone(c.model_object)
        self.assertEqual(c.model_object_as_string(), '')

        for o, esc, raw in (
            (True, 'True', 'True'),
            (0, '0', '0'),
            (3.14, '3.14', '3.14'),
            ('&<>', '&amp;&lt;&gt;', '&<>'),
        ):
            with self.subTest(object=o):
                c.model_object = o
                self.assertIs(c.model, m)
                self.assertEqual(c.model_object, o)
                with self.application():
                    c.escape_model_string = True
                    self.assertEqual(c.model_object_as_string(), esc)
                    c.escape_model_string = False
                    self.assertEqual(c.model_object_as_string(), raw)

    def test_markup_container(self):
        mc = ayame.MarkupContainer('a')
        with self.assertRaisesRegex(ayame.ComponentError, r' not attached .*\.Page\b'):
            mc.page()
        self.assertEqual(mc.path(), 'a')
        self.assertEqual(mc.children, [])
        self.assertIs(mc.find(None), mc)
        self.assertIs(mc.find(''), mc)
        with self.assertRaisesRegex(ayame.ComponentError, fr"\bcomponent .* '{__name__}' .* not found\b"):
            mc.find(__name__)
        self.assertEqual(list(mc.walk()), [
            (mc, 0),
        ])

        mc.add(None, True, 0, 3.14, '')
        self.assertEqual(mc.behaviors, [])
        self.assertEqual(mc.children, [])

        b1 = ayame.Component('b1')
        mc.add(b1)
        with self.assertRaisesRegex(ayame.ComponentError, r' not attached .*\.Page\b'):
            b1.page()
        self.assertEqual(b1.path(), 'a:b1')
        self.assertEqual(mc.behaviors, [])
        self.assertEqual(mc.children, [b1])
        self.assertIs(mc.find('b1'), b1)
        with self.assertRaisesRegex(ayame.ComponentError, r"'b1' .* exists\b"):
            mc.add(b1)
        b2 = ayame.MarkupContainer('b2')
        mc.add(b2)
        with self.assertRaisesRegex(ayame.ComponentError, r' not attached .*\.Page\b'):
            b2.page()
        self.assertEqual(b2.path(), 'a:b2')
        self.assertEqual(mc.behaviors, [])
        self.assertEqual(mc.children, [b1, b2])
        self.assertIs(mc.find('b2'), b2)
        with self.assertRaisesRegex(ayame.ComponentError, r"'b2' .* exists\b"):
            mc.add(b2)
        self.assertEqual(list(mc.walk()), [
            (mc, 0),
            (b1, 1), (b2, 1),
        ])

        c1 = ayame.Component('c1')
        b2.add(c1)
        with self.assertRaisesRegex(ayame.ComponentError, r' not attached .*\.Page\b'):
            c1.page()
        self.assertEqual(c1.path(), 'a:b2:c1')
        self.assertEqual(b2.behaviors, [])
        self.assertEqual(b2.children, [c1])
        self.assertIs(mc.find('b2:c1'), c1)
        with self.assertRaisesRegex(ayame.ComponentError, r"'c1' .* exists\b"):
            b2.add(c1)
        c2 = ayame.MarkupContainer('c2')
        b2.add(c2)
        with self.assertRaisesRegex(ayame.ComponentError, r' not attached .*\.Page\b'):
            c2.page()
        self.assertEqual(c2.path(), 'a:b2:c2')
        self.assertEqual(b2.behaviors, [])
        self.assertEqual(b2.children, [c1, c2])
        self.assertIs(mc.find('b2:c2'), c2)
        with self.assertRaisesRegex(ayame.ComponentError, r"'c2' .* exists\b"):
            b2.add(c2)
        self.assertEqual(list(mc.walk()), [
            (mc, 0),
            (b1, 1), (b2, 1),
            (c1, 2), (c2, 2),
        ])
        self.assertEqual(list(mc.walk(step=lambda c, _: c != b2)), [
            (mc, 0),
            (b1, 1), (b2, 1),
        ])

        el = self.empty_element()
        self.assertIs(mc.render(el), el)
        self.assertIsNone(mc.render(None))
        mc.visible = False
        self.assertIsNone(mc.render(el))

    def test_markup_container_with_model(self):
        mc = ayame.MarkupContainer('a')
        c = ayame.Component('b')
        mc.add(c)

        o = {'b': 'b'}
        m = model.CompoundModel(o)
        mc.model = m
        self.assertIs(mc.model, m)
        self.assertIs(mc.model_object, o)
        self.assertIsInstance(c.model, model.WrapModel)
        self.assertEqual(c.model_object, c.id)
        c.model_object = []
        self.assertEqual(c.model_object, [])

        o = {'b': 'a:b'}
        m = model.CompoundModel(o)
        mc.model = m
        self.assertIs(mc.model, m)
        self.assertIs(mc.model_object, o)
        self.assertIsInstance(c.model, model.WrapModel)
        self.assertEqual(c.model_object, c.path())
        c.model_object = []
        self.assertEqual(c.model_object, [])

        o = {'b': ''}
        m = model.Model(o)
        mc.model = m
        self.assertIs(mc.model, m)
        self.assertIs(mc.model_object, o)
        self.assertIsNone(c.model)
        self.assertIsNone(c.model_object)
        with self.assertRaisesRegex(ayame.ComponentError, r'\bmodel .* not set\b'):
            c.model_object = []

    def test_render_no_ayame_id(self):
        el = self.empty_element()
        mc = ayame.MarkupContainer('a')
        self.assertEqual(mc.render_component(el), (None, el))

    def test_render_unknown_ayame_element(self):
        el = markup.Element(self.ayame_of(__name__))
        mc = ayame.MarkupContainer('a')
        with self.assertRaisesRegex(ayame.RenderingError, fr"\bunknown element 'ayame:{__name__}'"):
            mc.render(el)

    def test_render_unknown_ayame_attribute(self):
        el = self.empty_element(attrib={
            markup.AYAME_ID: 'b',
            self.ayame_of(__name__): 'b',
        })
        mc = ayame.MarkupContainer('a')
        mc.add(ayame.Component('b'))
        with self.assertRaisesRegex(ayame.RenderingError, fr"\bunknown attribute 'ayame:{__name__}'"):
            mc.render(el)

    def test_render_no_associated_component(self):
        el = self.empty_element(attrib={
            self.html_of('id'): __name__,
            markup.AYAME_ID: __name__,
        })
        mc = ayame.MarkupContainer('a')
        mc.add(ayame.Component('b'))
        with self.assertRaisesRegex(ayame.ComponentError, fr"\bcomponent .* '{__name__}' .* not found\b"):
            mc.render(el)

    def test_render_replace_element_itself(self):
        class Component(ayame.Component):
            def on_render(self, _):
                return self.model_object

        el = self.empty_element()
        for t, o, rv in (
            (
                markup.Element,
                el,
                el,
            ),
            (
                str,
                '',
                '',
            ),
            (
                list[markup.Node],
                [el, ''],
                [el, ''],
            ),
            (
                None,
                None,
                '',
            ),
        ):
            with self.subTest(type=t):
                el = self.empty_element(attrib={
                    markup.AYAME_ID: 'b',
                })
                mc = ayame.MarkupContainer('a')
                mc.add(Component('b', model.Model(o)))

                self.assertEqual(mc.render(el), rv)

    def test_render_remove_element(self):
        class Component(ayame.Component):
            def on_render(self, _):
                return None

        el = self.empty_element()
        for i in range(1, 10):
            if i % 2:
                el.append(str(i))
            else:
                el.append(self.empty_element(attrib={
                    markup.AYAME_ID: str(i),
                }))
        mc = ayame.MarkupContainer('a')
        for i in range(2, 10, 2):
            mc.add(Component(str(i)))

        rv = mc.render(el)
        self.assertIs(rv, el)
        self.assertEqual(rv.attrib, {})
        self.assertEqual(rv.children, ['1', '3', '5', '7', '9'])

    def test_render_replace_element(self):
        class Component(ayame.Component):
            def on_render(self, _):
                return self.model_object

        el = self.empty_element()
        for t, o, children in (
            (
                markup.Element,
                el,
                ['>', el, '<'],
            ),
            (
                str,
                '',
                ['>', '', '<'],
            ),
            (
                list[markup.Node],
                [el, ''],
                ['>', el, '', '<'],
            ),
            (
                None,
                None,
                ['>', '<'],
            ),
        ):
            with self.subTest(type=t):
                el = self.empty_element()
                el.append('>')
                el.append(self.empty_element(attrib={
                    markup.AYAME_ID: 'b',
                }))
                el.append('<')
                mc = ayame.MarkupContainer('a')
                mc.add(Component('b', model.Model(o)))

                rv = mc.render(el)
                self.assertIs(rv, el)
                self.assertEqual(rv.attrib, {})
                self.assertEqual(rv.children, children)

    def test_render_replace_ayame_element_itself(self):
        class MarkupContainer(ayame.MarkupContainer):
            def on_render_element(self, el):
                return self.model_object if el.qname.ns_uri == markup.AYAME_NS else el

        el = self.empty_element()
        for t, o, rv in (
            (
                str,
                '',
                '',
            ),
            (
                list[markup.Node],
                [el, ''],
                [el, ''],
            ),
            (
                None,
                None,
                '',
            ),
        ):
            with self.subTest(type=t):
                el = markup.Element(self.ayame_of(__name__))
                mc = MarkupContainer('a', model.Model(o))
                self.assertEqual(mc.render(el), rv)

    def test_render_remove_ayame_element(self):
        class MarkupContainer(ayame.MarkupContainer):
            def on_render_element(self, el):
                return None if el.qname.ns_uri == markup.AYAME_NS else el

        el = self.empty_element()
        for i in range(1, 10):
            if i % 2:
                el.append(str(i))
            else:
                el.append(markup.Element(self.ayame_of(str(i))))
        mc = MarkupContainer('a')

        rv = mc.render(el)
        self.assertIs(rv, el)
        self.assertEqual(rv.attrib, {})
        self.assertEqual(rv.children, ['1', '3', '5', '7', '9'])

    def test_render_replace_ayame_element(self):
        class MarkupContainer(ayame.MarkupContainer):
            def on_render_element(self, el):
                return self.model_object if el.qname.ns_uri == markup.AYAME_NS else el

        el = self.empty_element()
        for t, o, children in (
            (
                str,
                '',
                ['>', '', '<'],
            ),
            (
                list[markup.Node],
                [el, ''],
                ['>', el, '', '<'],
            ),
            (
                None,
                None,
                ['>', '<'],
            ),
        ):
            with self.subTest(type=t):
                el = self.empty_element()
                el.append('>')
                el.append(markup.Element(self.ayame_of(__name__)))
                el.append('<')
                mc = MarkupContainer('a', model.Model(o))

                rv = mc.render(el)
                self.assertIs(rv, el)
                self.assertEqual(rv.attrib, {})
                self.assertEqual(rv.children, children)

    def test_render_ayame_container_no_ayame_id(self):
        el = markup.Element(markup.AYAME_CONTAINER)
        mc = ayame.MarkupContainer('a')
        with self.assertRaisesRegex(ayame.RenderingError, r"'ayame:id' .* 'ayame:container'"):
            mc.render(el)

    def test_render_ayame_container_no_associated_component(self):
        el = markup.Element(markup.AYAME_CONTAINER,
                            {
                                markup.AYAME_ID: 'b',
                            })
        mc = ayame.MarkupContainer('a')
        with self.assertRaisesRegex(ayame.ComponentError, r"\bcomponent .* 'b' .* not found\b"):
            mc.render(el)

    def test_render_ayame_container(self):
        class Container(ayame.MarkupContainer):
            def on_render(self, el):
                return el

        b = ElementBuilder(markup.XHTML_NS)
        with b.open('ul',
                    ns=self.ns):
            with b.open('li'):
                b.str('spam')
                b.empty('br')
                with b.open('ayame:container',
                            {
                                'ayame:id': 'b',
                            }):
                    b.str('eggs')
                    b.empty('br')
                    b.str('ham')
                    b.empty('br')
                b.str('toast')
            with b.open('li'):
                b.str('beans')
        el = b.root
        mc = ayame.MarkupContainer('a')
        mc.add(Container('b'))

        rv = mc.render(el)
        self.assertIs(rv, el)
        with b.open('ul',
                    ns=self.ns):
            with b.open('li'):
                b.str('spam')
                b.empty('br')
                b.str('eggs')
                b.empty('br')
                b.str('ham')
                b.empty('br')
                b.str('toast')
            with b.open('li'):
                b.str('beans')
        self.assertElementEqual(rv, b.root)

    def test_render_ayame_enclosure_no_ayame_child(self):
        el = markup.Element(markup.AYAME_ENCLOSURE)
        mc = ayame.MarkupContainer('a')
        with self.assertRaisesRegex(ayame.RenderingError, r"'ayame:child' .* 'ayame:enclosure'"):
            mc.render(el)

    def test_render_ayame_enclosure_no_associated_component(self):
        el = markup.Element(markup.AYAME_ENCLOSURE,
                            {
                                markup.AYAME_CHILD: 'b',
                            })
        el.append(self.empty_element(attrib={
            markup.AYAME_ID: 'b',
        }))
        mc = ayame.MarkupContainer('a')
        with self.assertRaisesRegex(ayame.ComponentError, r"\bcomponent .* 'b' .* not found\b"):
            mc.render(el)

    def test_render_ayame_enclosure(self):
        for v in (True, False):
            with self.subTest(visible=v):
                b = ElementBuilder(markup.XHTML_NS)
                with b.open('ul',
                            ns=self.ns):
                    with b.open('li'):
                        b.str('spam')
                        b.empty('br')
                        with b.open('ayame:enclosure',
                                    {
                                        'ayame:child': 'b',
                                    }):
                            b.str('eggs')
                            b.empty('br',
                                    {
                                        'ayame:id': 'b',
                                    })
                            b.str('ham')
                            b.empty('br')
                        b.str('toast')
                    with b.open('li'):
                        b.str('beans')
                el = b.root
                mc = ayame.MarkupContainer('a')
                mc.add(ayame.Component('b'))
                mc.find('b').visible = v

                rv = mc.render(el)
                self.assertIs(rv, el)
                with b.open('ul',
                            ns=self.ns):
                    with b.open('li'):
                        b.str('spam')
                        b.empty('br')
                        if v:
                            b.str('eggs')
                            b.empty('br')
                            b.str('ham')
                            b.empty('br')
                        b.str('toast')
                    with b.open('li'):
                        b.str('beans')
                self.assertElementEqual(rv, b.root)

    def test_render_ayame_message_element_no_value_for_key(self):
        with self.application(self.new_environ()):
            el = markup.Element(markup.AYAME_MESSAGE,
                                {
                                    markup.AYAME_KEY: 'key',
                                })
            mc = ayame.MarkupContainer('a')
            with self.assertRaisesRegex(ayame.RenderingError, r" value .* ayame:message .* 'key'"):
                mc.render(el)

    def test_render_ayame_message_element(self):
        for a, m in (
            (
                'en',
                'Hello World!',
            ),
            (
                'ja, en',
                '\u3053\u3093\u306b\u3061\u306f\u4e16\u754c',
            ),
        ):
            with self.subTest(accept_language=a):
                with self.application(self.new_environ(accept=a)):
                    p = BeansPage()
                    status, headers, content = p()
                html = self.format(type(p), message=m)
                self.assertEqual(status, http.OK.status)
                self.assertEqual(headers, [
                    ('Content-Type', 'text/html; charset=UTF-8'),
                    ('Content-Length', str(len(html))),
                ])
                self.assertEqual(content, [html])

    def test_render_ayame_message_attribute_invalid_value(self):
        for a in (
            {
                markup.AYAME_ID: 'b',
                markup.AYAME_MESSAGE: 'key',
            },
            {
                markup.AYAME_MESSAGE: 'key',
            },
        ):
            with (self.subTest(attrib=a),
                  self.application(self.new_environ())):
                el = self.empty_element(attrib=a)
                mc = ayame.MarkupContainer('a')
                mc.add(ayame.Component('b'))
                with self.assertRaisesRegex(ayame.RenderingError, r'\binvalid .* ayame:message '):
                    mc.render(el)

    def test_render_ayame_message_attribute(self):
        for a, m in (
            (
                'en',
                'Submit',
            ),
            (
                'ja, en',
                '\u9001\u4fe1',
            ),
        ):
            with self.subTest(accept_language=a):
                with self.application(self.new_environ(accept=a)):
                    p = BaconPage()
                    status, headers, content = p()
                html = self.format(type(p), message=m)
                self.assertEqual(status, http.OK.status)
                self.assertEqual(headers, [
                    ('Content-Type', 'text/html; charset=UTF-8'),
                    ('Content-Length', str(len(html))),
                ])
                self.assertEqual(content, [html])

    def test_render_invisible_child(self):
        b = ElementBuilder(markup.XHTML_NS)
        with b.open('ul',
                    ns=self.ns):
            with b.open('li',
                        {
                            'ayame:id': 'b1',
                        }):
                b.str('spam')
                with b.open('span',
                            {
                                'ayame:id': 'c1',
                            }):
                    b.str('eggs')
                b.str('ham')
            with b.open('li',
                        {
                            'ayame:id': 'b2',
                        }):
                b.str('toast')
                with b.open('span',
                            {
                                'ayame:id': 'c2',
                            }):
                    b.str('beans')
                b.str('bacon')
        el = b.root
        mc = ayame.MarkupContainer('a')
        mc.add(ayame.MarkupContainer('b1'))
        mc.find('b1').add(ayame.Component('c1'))
        mc.find('b1:c1').visible = False
        mc.add(ayame.MarkupContainer('b2'))
        mc.find('b2').add(ayame.Component('c2'))
        mc.find('b2').visible = False

        rv = mc.render(el)
        self.assertIs(rv, el)
        with b.open('ul',
                    ns=self.ns):
            with b.open('li'):
                b.str('spam')
                b.str('ham')
        self.assertElementEqual(rv, b.root)

    def test_markup_inheritance(self):
        class Spam(ayame.MarkupContainer):
            pass

        class Eggs(Spam):
            pass

        class Ham(Spam):
            pass

        for supercls in (Eggs, Ham):
            for name in ('Toast', 'Beans'):
                cls = type(name, (supercls,), {})
                with (self.subTest(inheritance=f'Spam > {supercls.__name__} > {name}'),
                      self.application()):
                    mc = cls('a')
                    m = mc.load_markup()
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
                                b.str('Spam')
                            b.str(lv[2])
                            b.empty('meta',
                                    {
                                        'name': 'class',
                                        'content': 'Spam',
                                    })
                            b.str(lv[1])
                            if supercls is Ham:
                                b.str(lv[3])
                                b.empty('meta',
                                        {
                                            'name': 'class',
                                            'content': 'Ham',
                                        })
                                b.str(lv[2])
                            if name == 'Beans':
                                b.str(lv[3])
                                b.empty('meta',
                                        {
                                            'name': 'class',
                                            'content': 'Beans',
                                        })
                                b.str(lv[2])
                        b.str(lv[1])
                        with b.open('body'):
                            b.str(lv[2])
                            with b.open('p'):
                                b.str('before ayame:child (Spam)')
                            b.str(lv[2])
                            b.str(lv[3])
                            with b.open('p'):
                                b.str(f'inside ayame:extend ({supercls.__name__})')
                            b.str(lv[3])
                            b.str(lv[3])
                            with b.open('p'):
                                b.str(f'inside ayame:extend ({name})')
                            b.str(lv[2])
                            b.str(lv[2])
                            b.str(lv[2])
                            with b.open('p'):
                                b.str('after ayame:child (Spam)')
                            b.str(lv[1])
                        b.str(lv[0])
                    self.assertElementEqual(m.root, b.root)

    def test_markup_inheritance_with_empty_superclass(self):
        class Bacon(ayame.MarkupContainer):
            pass

        class Toast(Bacon):
            pass

        with self.application():
            mc = Toast('a')
            m = mc.load_markup()
        self.assertEqual(m.xml_decl, {})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, '')
        self.assertIsNone(m.root)

    def test_markup_inheritance_with_empty_subclass(self):
        class Spam(ayame.MarkupContainer):
            pass

        class Sausage(Spam):
            pass

        with self.application():
            mc = Sausage('a')
            m = mc.load_markup()
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
                    b.str('Spam')
                b.str(lv[2])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'Spam',
                        })
                b.str(lv[1])
                b.str(lv[3])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'Sausage',
                        })
                b.str(lv[2])
            b.str(lv[1])
            with b.open('body'):
                b.str(lv[2])
                with b.open('p'):
                    b.str('before ayame:child (Spam)')
                b.str(lv[2])
                b.str(lv[2])
                with b.open('p'):
                    b.str('after ayame:child (Spam)')
                b.str(lv[1])
            b.str(lv[0])
        self.assertElementEqual(m.root, b.root)

    def test_markup_inheritance_with_duplicate_ayame_elements(self):
        class Tomato(ayame.MarkupContainer):
            pass

        class Lobster(Tomato):
            pass

        with self.application():
            mc = Lobster('a')
            m = mc.load_markup()
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
                    b.str('Tomato')
                b.str(lv[2])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'Tomato',
                        })
                b.str(lv[1])
                b.str(lv[3])
                b.empty('meta',
                        {
                            'name': 'class',
                            'content': 'Lobster',
                        })
                b.str(lv[2])
            b.str(lv[1])
            with b.open('body'):
                b.str(lv[2])
                with b.open('p'):
                    b.str('before ayame:child (Tomato)')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('inside ayame:extend (Lobster)')
                b.str(lv[2])
                b.str(lv[2])
                b.empty('ayame:child')
                b.str(lv[2])
                with b.open('p'):
                    b.str('after ayame:child (Tomato)')
                b.str(lv[1])
            b.str(lv[0])
        self.assertElementEqual(m.root, b.root)

    def test_markup_inheritance_with_superclass_ayame_head(self):
        class Shallots(ayame.MarkupContainer):
            pass

        class Beans(Shallots):
            pass

        with self.application():
            mc = Beans('a')
            m = mc.load_markup()
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
                    b.str('Shallots')
                b.str(lv[2])
                with b.open('ayame:head'):
                    b.str(lv[3])
                    b.empty('meta',
                            {
                                'name': 'class',
                                'content': 'Shallots',
                            })
                    b.str(lv[2])
                    b.str(lv[3])
                    b.empty('meta',
                            {
                                'name': 'class',
                                'content': 'Beans',
                            })
                    b.str(lv[2])
                b.str(lv[1])
            b.str(lv[1])
            with b.open('body'):
                b.str(lv[2])
                with b.open('p'):
                    b.str('before ayame:child (Shallots)')
                b.str(lv[2])
                b.str(lv[3])
                with b.open('p'):
                    b.str('inside ayame:extend (Beans)')
                b.str(lv[2])
                b.str(lv[2])
                with b.open('p'):
                    b.str('after ayame:child (Shallots)')
                b.str(lv[1])
            b.str(lv[0])
        self.assertElementEqual(m.root, b.root)

    def test_markup_inheritance_with_multiple_inheritance(self):
        class Spam(ayame.MarkupContainer):
            pass

        class Eggs(ayame.MarkupContainer):
            pass

        class Toast(Spam, Eggs):
            pass

        with self.application():
            mc = Toast('a')
            with self.assertRaisesRegex(ayame.AyameError, r' multiple inheritance$'):
                mc.load_markup()

    def test_markup_inheritance_without_superclass(self):
        class Toast(ayame.MarkupContainer):
            pass

        class Beans(ayame.MarkupContainer):
            pass

        for cls in (Toast, Beans):
            with (self.subTest(cls=cls.__name__),
                  self.application()):
                mc = cls('a')
                with self.assertRaisesRegex(ayame.AyameError, r'^superclass .* not found$'):
                    mc.load_markup()

    def test_markup_inheritance_without_ayame_child(self):
        class Aubergine(ayame.MarkupContainer):
            pass

        class Toast(Aubergine):
            pass

        class Beans(Aubergine):
            pass

        for cls in (Toast, Beans):
            with (self.subTest(cls=cls.__name__),
                  self.application()):
                mc = cls('a')
                with self.assertRaisesRegex(ayame.RenderingError, r"'ayame:child' .* not found\b"):
                    mc.load_markup()

    def test_markup_inheritance_with_ayame_child_as_root(self):
        class Truffle(ayame.MarkupContainer):
            pass

        class Toast(Truffle):
            pass

        class Beans(Truffle):
            pass

        for cls in (Toast, Beans):
            with (self.subTest(cls=cls.__name__),
                  self.application()):
                mc = cls('a')
                with self.assertRaisesRegex(ayame.RenderingError, r"'ayame:child' .* root element\b"):
                    mc.load_markup()

    def test_markup_inheritance_without_head(self):
        class Bacon(ayame.MarkupContainer):
            pass

        class Pate(ayame.MarkupContainer):
            pass

        for cls in (Bacon, Pate):
            with self.application():
                mc = type('Beans', (cls,), {})('a')
                with self.assertRaisesRegex(ayame.RenderingError, r"'head' .* not found\b"):
                    mc.load_markup()

    def test_markup_cache(self):
        with unittest.mock.patch.dict(self.app.config):
            self.app.config['ayame.markup.cache'] = cache = self.app.config['ayame.markup.cache'].copy()
            self.app.config['ayame.resource.loader'] = self.new_resource_loader()
            cache.clear()

            with self.application(self.new_environ()):
                p = SpamPage()
                p()
            self.assertEqual(len(cache), 1)

            with self.application(self.new_environ()):
                p = SpamPage()
                with self.assertRaises(OSError):
                    p()
            self.assertEqual(len(cache), 0)

            with self.application(self.new_environ()):
                p = SpamPage()
                with self.assertRaises(ayame.ResourceError):
                    p()
            self.assertEqual(len(cache), 0)

    def test_page(self):
        with self.application(self.new_environ()):
            p = SpamPage()
            status, headers, content = p()
        html = self.format(type(p))
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        self.assertIs(p.page(), p)
        self.assertIs(p.find('message').page(), p)
        self.assertEqual(p.path(), '')
        self.assertEqual(p.find('message').path(), 'message')

    def test_behavior(self):
        b = ayame.Behavior()
        with self.assertRaises(ayame.AyameError):
            b.app
        with self.assertRaises(ayame.AyameError):
            b.config
        with self.assertRaises(ayame.AyameError):
            b.environ
        with self.assertRaises(ayame.AyameError):
            b.request
        with self.assertRaises(ayame.AyameError):
            b.session
        with self.assertRaises(ayame.AyameError):
            b.forward(b)
        with self.assertRaises(ayame.AyameError):
            b.redirect(b)
        with self.assertRaises(ayame.AyameError):
            b.uri_for(b)

    def test_behavior_render(self):
        class Behavior(ayame.Behavior):
            def on_before_render(self, c):
                super().on_before_render(c)
                c.model_object.append('before-render')

            def on_component(self, c, el):
                super().on_component(c, el)
                c.model_object.append('component')

            def on_after_render(self, c):
                super().on_after_render(c)
                c.model_object.append('after-render')

        for cls in (ayame.Component, ayame.MarkupContainer):
            with self.subTest(cls=cls):
                c = cls('a', model.Model([]))
                c.add(Behavior())
                self.assertEqual(len(c.behaviors), 1)
                self.assertEqual(c.behaviors[0].component, c)

                el = self.empty_element()
                self.assertIs(c.render(el), el)
                self.assertEqual(c.model_object, ['before-render', 'component', 'after-render'])

    def test_attribute_modifier(self):
        for cls in (ayame.Component, ayame.MarkupContainer):
            with self.subTest(cls=cls):
                el = self.empty_element(attrib={
                    self.html_of('data-spam'): '',
                    self.html_of('data-ham'): '',
                })
                c = cls('a')
                c.add(ayame.AttributeModifier(self.html_of('data-spam'), model.Model('spam')))
                c.add(ayame.AttributeModifier(self.html_of('data-eggs'), model.Model('eggs')))
                c.add(ayame.AttributeModifier(self.html_of('data-ham'), model.Model(None)))
                c.add(ayame.AttributeModifier(self.html_of('data-toast'), model.Model(None)))
                self.assertEqual([b.component for b in c.behaviors], [c] * 4)

                rv = c.render(el)
                self.assertIs(rv, el)
                self.assertEqual(rv.attrib, {
                    self.html_of('data-spam'): 'spam',
                    self.html_of('data-eggs'): 'eggs',
                })

    def test_fire_get(self):
        for visible, query, o in (
            # fire path
            (
                True,
                f'{ayame.AYAME_PATH}=clay1',
                {
                    'clay1': 1,
                    'clay2': 0,
                },
            ),
            # duplicate path
            (
                True,
                '&'.join((
                    f'{ayame.AYAME_PATH}=clay1',
                    f'{ayame.AYAME_PATH}=obstacle:clay2',
                )),
                {
                    'clay1': 1,
                    'clay2': 0,
                },
            ),
            # nonexistent path
            (
                True,
                f'{ayame.AYAME_PATH}=clay2',
                {
                    'clay1': 0,
                    'clay2': 0,
                },
            ),
            # invisible component
            (
                False,
                f'{ayame.AYAME_PATH}=clay1',
                {
                    'clay1': 0,
                    'clay2': 0,
                },
            ),
        ):
            with self.subTest(query=query):
                with self.application(self.new_environ(query=query)):
                    p = EggsPage()
                    p.find('clay1').visible = visible
                    status, headers, content = p()
                html = self.format(type(p), clay1=visible)
                self.assertEqual(status, http.OK.status)
                self.assertEqual(headers, [
                    ('Content-Type', 'text/html; charset=UTF-8'),
                    ('Content-Length', str(len(html))),
                ])
                self.assertEqual(content, [html])

                self.assertEqual(p.model_object, o)

    def test_fire_post(self):
        for visible, data, o in (
            # fire path
            (
                True,
                self.form_data(
                    (ayame.AYAME_PATH, 'obstacle:clay2'),
                ),
                {
                    'clay1': 0,
                    'clay2': 1,
                },
            ),
            # duplicate path
            (
                True,
                self.form_data(
                    (ayame.AYAME_PATH, 'obstacle:clay2'),
                    (ayame.AYAME_PATH, 'clay1'),
                ),
                {
                    'clay1': 0,
                    'clay2': 1,
                },
            ),
            # nonexistent path
            (
                True,
                self.form_data(
                    (ayame.AYAME_PATH, 'clay2'),
                ),
                {
                    'clay1': 0,
                    'clay2': 0,
                },
            ),
            # invisible component
            (
                False,
                self.form_data(
                    (ayame.AYAME_PATH, 'clay1'),
                ),
                {
                    'clay1': 0,
                    'clay2': 0,
                },
            ),
        ):
            with self.subTest(form_data=data):
                with self.application(self.new_environ(method='POST', form=data)):
                    p = EggsPage()
                    p.find('clay1').visible = visible
                    status, headers, content = p()
                html = self.format(type(p), clay1=visible)
                self.assertEqual(status, http.OK.status)
                self.assertEqual(headers, [
                    ('Content-Type', 'text/html; charset=UTF-8'),
                    ('Content-Length', str(len(html))),
                ])
                self.assertEqual(content, [html])

                self.assertEqual(p.model_object, o)

    def test_fire_component(self):
        class Component(ayame.Component):
            def __init__(self, id):
                super().__init__(id, model.Model(0))

            def on_fire(self):
                super().on_fire()
                self.model_object += 1

        for visible, query, o in (
            # fire path
            (
                True,
                f'{ayame.AYAME_PATH}=c',
                1,
            ),
            # nonexistent path
            (
                True,
                f'{ayame.AYAME_PATH}=_',
                0,
            ),
            # invisible component
            (
                False,
                f'{ayame.AYAME_PATH}=c',
                0,
            ),
        ):
            with self.subTest(query=query):
                with self.application(self.new_environ(query=query)):
                    c = Component('c')
                    c.visible = visible
                    c.fire()
                self.assertEqual(c.model_object, o)

    def test_page_with_empty_markup(self):
        class Bacon(ayame.Page):
            pass

        with self.application(self.new_environ()):
            p = Bacon()
            status, headers, content = p()
        html = b''
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        self.assertIs(p.page(), p)
        self.assertEqual(p.path(), '')

    def test_nested(self):
        regex = r' not .* subclass of MarkupContainer$'

        with self.assertRaisesRegex(ayame.AyameError, regex):
            class Spam:
                @ayame.nested
                def f(self):
                    pass

        with self.assertRaisesRegex(ayame.AyameError, regex):
            class Eggs:
                @ayame.nested
                class C:
                    pass

        with self.assertRaisesRegex(ayame.AyameError, regex):
            class Ham:
                C = ayame.nested(ayame.MarkupContainer)

        class Toast:
            @ayame.nested
            class C(ayame.MarkupContainer):
                pass

        self.assertIsInstance(Toast.C('a'), ayame.MarkupContainer)

    def test_nested_class_markup(self):
        for cls, mt in (
            (
                ToastPage,
                markup.MarkupType('.htm', 'text/html', ()),
            ),
            (
                ToastPage.NestedPage,
                markup.MarkupType('.html', 'text/html', (ToastPage,)),
            ),
        ):
            with self.subTest(cls=cls):
                with self.application(self.new_environ()):
                    p = cls()
                    status, headers, content = p()
                html = self.format(cls, name=cls.__qualname__)
                self.assertEqual(status, http.OK.status)
                self.assertEqual(headers, [
                    ('Content-Type', 'text/html; charset=UTF-8'),
                    ('Content-Length', str(len(html))),
                ])
                self.assertEqual(content, [html])

                self.assertEqual(cls.markup_type, mt)

    def test_ayame_head_for_component_markup(self):
        el = self.empty_element()
        mc = ayame.MarkupContainer('a')
        with self.assertRaisesRegex(ayame.RenderingError, r"'head' .* not found\b"):
            mc.head
        with self.assertRaisesRegex(ayame.RenderingError, r"\broot element is not 'html'"):
            mc.find_head(el)

        b = ElementBuilder(markup.XHTML_NS)
        with b.open('html',
                    ns=self.ns):
            with b.open('body'):
                pass
        el = b.root
        self.assertIsNone(mc.find_head(el))

        with b.open('html',
                    ns=self.ns):
            with b.open('head'):
                pass
        el = b.root
        mc.head = mc.find_head(el)
        mc.head.append(markup.Element(self.html_of('title'),
                                      type=markup.Element.OPEN))
        mc.head[-1].append('title')
        with b.open('html',
                    ns=self.ns):
            with b.open('head'):
                with b.open('title'):
                    b.str('title')
        self.assertElementEqual(el, b.root)

    def test_element(self):
        class Bacon(ayame.MarkupContainer):
            pass

        class Aubergine(ayame.MarkupContainer):
            pass

        for cls in (Bacon, Aubergine):
            with (self.subTest(cls=cls),
                  self.application()):
                mc = cls('a')
                mc.add(ayame.MarkupContainer('b'))

                mc.has_markup = False
                self.assertIsNone(mc.find('b').element())
                mc.has_markup = True
                self.assertIsNone(mc.find('b').element())

        with self.application():
            p = EggsPage()
            clay1 = p.find('clay1').element()
            clay2 = p.find('obstacle:clay2').element()
            self.assertIsInstance(clay1, markup.Element)
            self.assertIsInstance(clay2, markup.Element)
            self.assertIsNot(clay1, clay2)


class SpamPage(ayame.Page):

    html_t = """\
        <?xml version="1.0"?>
        {doctype}
        <html xmlns="{xhtml}">
          <head>
            <title>SpamPage</title>
          </head>
          <body>
            <p>Hello World!</p>
          </body>
        </html>
    """

    def __init__(self):
        super().__init__()
        self.add(self.Label('message', model.Model('Hello World!')))
        self.headers['Content-Type'] = 'text/plain'

    class Label(ayame.Component):
        def on_render(self, el):
            el[:] = self.model_object
            return el


class EggsPage(ayame.Page):

    html_t = """\
        <?xml version="1.0"?>
        {doctype}
        <html xmlns="{xhtml}">
          <head>
            <title>EggsPage</title>
          </head>
          <body>
            {clay1}
            <div>
              <p>clay2</p>
            </div>
          </body>
        </html>
    """
    kwargs = {
        'clay1': lambda v=True: '<p>clay1</p>' if v else '',
    }

    def __init__(self):
        super().__init__()
        self.model = model.CompoundModel({
            'clay1': 0,
            'clay2': 0,
        })
        self.add(self.Clay('clay1'))
        self.add(ayame.MarkupContainer('obstacle'))
        self.find('obstacle').add(self.Clay('clay2'))

    class Clay(ayame.Component):

        def on_fire(self):
            self.model_object += 1


class HamPage(ayame.Page):

    html_t = """\
        <?xml version="1.0"?>
        {doctype}
        <html xmlns="{xhtml}">
          <head>
            <title>HamPage</title>
          </head>
          <body>
            <p>{name}</p>
          </body>
        </html>
    """


class ToastPage(HamPage):

    markup_type = markup.MarkupType('.htm', 'text/html', ())

    @ayame.nested
    class NestedPage(HamPage):
        pass


class BeansPage(ayame.Page):

    html_t = """\
        <?xml version="1.0"?>
        {doctype}
        <html xmlns="{xhtml}">
          <head>
            <title>BeansPage</title>
          </head>
          <body>
            <p>{message}</p>
          </body>
        </html>
    """


class BaconPage(ayame.Page):

    html_t = """\
        <?xml version="1.0"?>
        {doctype}
        <html xmlns="{xhtml}">
          <head>
            <title>BaconPage</title>
          </head>
          <body>
            <form action="#">
              <div>
                <input type="submit" value="{message}" />
              </div>
            </form>
          </body>
        </html>
    """
