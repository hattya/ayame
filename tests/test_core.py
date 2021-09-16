#
# test_core
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import textwrap

import ayame
from ayame import basic, http, markup, model
from base import AyameTestCase


class CoreTestCase(AyameTestCase):

    def test_component(self):
        with self.assertRaisesRegex(ayame.ComponentError, r' id .* not set\b'):
            ayame.Component(None)

        c = ayame.Component('a')
        self.assertEqual(c.id, 'a')
        self.assertIsNone(c.model)
        self.assertIsNone(c.model_object)
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
        c.add(None, True, 0, 3.14, '')
        self.assertEqual(c.behaviors, [])
        self.assertEqual(c.path(), 'a')
        self.assertEqual(c.render(''), '')
        c.visible = False
        self.assertIsNone(c.render(''))

    def test_component_with_model(self):
        with self.assertRaisesRegex(ayame.ComponentError, r' not .* instance of Model\b'):
            ayame.Component('1', '')

        m = model.Model(None)
        self.assertIsNone(m.object)
        c = ayame.Component('a', m)
        self.assertEqual(c.id, 'a')
        self.assertIs(c.model, m)
        self.assertIsNone(c.model.object)
        self.assertIsNone(c.model_object)
        c.model.object = True
        self.assertIs(c.model, m)
        self.assertEqual(c.model.object, True)
        self.assertEqual(c.model_object, True)
        c.model_object = False
        self.assertIs(c.model, m)
        self.assertEqual(c.model.object, False)
        self.assertEqual(c.model_object, False)
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
        c.add(None, True, 0, 3.14, '')
        self.assertEqual(c.behaviors, [])
        self.assertEqual(c.path(), 'a')
        self.assertEqual(c.render(''), '')
        c.visible = False
        self.assertIsNone(c.render(''))

        m = model.Model('&<>')
        self.assertEqual(m.object, '&<>')
        c = ayame.Component('a', m)
        self.assertEqual(c.id, 'a')
        self.assertIs(c.model, m)
        self.assertEqual(c.model_object, '&<>')
        self.assertEqual(c.model_object_as_string(), '&amp;&lt;&gt;')
        c.escape_model_string = False
        self.assertEqual(c.model_object, '&<>')
        self.assertEqual(c.model_object_as_string(), '&<>')

    def test_markup_container(self):
        mc = ayame.MarkupContainer('a')
        with self.assertRaisesRegex(ayame.ComponentError, r' not attached .*\.Page\b'):
            mc.page()
        self.assertEqual(mc.path(), 'a')
        self.assertEqual(mc.children, [])
        self.assertIs(mc.find(None), mc)
        self.assertIs(mc.find(''), mc)
        it = mc.walk()
        self.assertEqual(list(it), [(mc, 0)])

        b1 = ayame.Component('b1')
        mc.add(b1)
        with self.assertRaisesRegex(ayame.ComponentError, r' not attached .*\.Page\b'):
            b1.page()
        self.assertEqual(b1.path(), 'a:b1')
        self.assertEqual(mc.children, [b1])
        self.assertIs(mc.find('b1'), b1)
        with self.assertRaisesRegex(ayame.ComponentError, r"'b1' .* exists\b"):
            mc.add(b1)
        b2 = ayame.MarkupContainer('b2')
        mc.add(b2)
        with self.assertRaisesRegex(ayame.ComponentError, r' not attached .*\.Page\b'):
            b2.page()
        self.assertEqual(b2.path(), 'a:b2')
        self.assertEqual(mc.children, [b1, b2])
        self.assertIs(mc.find('b2'), b2)
        with self.assertRaisesRegex(ayame.ComponentError, r"'b2' .* exists\b"):
            mc.add(b2)
        it = mc.walk()
        self.assertEqual(list(it), [(mc, 0), (b1, 1), (b2, 1)])

        c1 = ayame.Component('c1')
        b2.add(c1)
        with self.assertRaisesRegex(ayame.ComponentError, r' not attached .*\.Page\b'):
            c1.page()
        self.assertEqual(c1.path(), 'a:b2:c1')
        self.assertEqual(b2.children, [c1])
        self.assertIs(mc.find('b2:c1'), c1)
        with self.assertRaisesRegex(ayame.ComponentError, r"'c1' .* exists\b"):
            b2.add(c1)
        c2 = ayame.MarkupContainer('c2')
        b2.add(c2)
        with self.assertRaisesRegex(ayame.ComponentError, r' not attached .*\.Page\b'):
            c2.page()
        self.assertEqual(c2.path(), 'a:b2:c2')
        self.assertEqual(b2.children, [c1, c2])
        self.assertIs(mc.find('b2:c2'), c2)
        with self.assertRaisesRegex(ayame.ComponentError, r"'c2' .* exists\b"):
            b2.add(c2)
        it = mc.walk()
        self.assertEqual(list(it), [
            (mc, 0),
            (b1, 1),
            (b2, 1), (c1, 2), (c2, 2),
        ])
        it = mc.walk(step=lambda component, *args: component != b2)
        self.assertEqual(list(it), [
            (mc, 0),
            (b1, 1),
            (b2, 1),
        ])

        self.assertEqual(mc.render(''), '')
        mc.visible = False
        self.assertIsNone(mc.render(''))

    def test_render_no_child_component(self):
        root = markup.Element(self.of('root'))
        mc = ayame.MarkupContainer('a')
        self.assertEqual(mc.render(root), root)

    def test_render_no_ayame_id(self):
        root = markup.Element(self.of('root'))
        mc = ayame.MarkupContainer('a')
        self.assertEqual(mc.render_component(root), (None, root))

    def test_render_unknown_ayame_element(self):
        root = markup.Element(self.ayame_of('spam'))
        mc = ayame.MarkupContainer('a')
        with self.assertRaisesRegex(ayame.RenderingError, r"\bunknown element 'ayame:spam'"):
            mc.render(root)

    def test_render_unknown_ayame_attribute(self):
        root = markup.Element(self.of('root'),
                              attrib={
                                  markup.AYAME_ID: 'b',
                                  self.ayame_of('spam'): '',
                              })
        mc = ayame.MarkupContainer('a')
        mc.add(ayame.Component('b'))
        with self.assertRaisesRegex(ayame.RenderingError, r"\bunknown attribute 'ayame:spam'"):
            mc.render(root)

    def test_render_no_associated_component(self):
        root = markup.Element(self.of('root'),
                              attrib={
                                  markup.AYAME_ID: 'c',
                                  self.of('id'): 'c',
                              })
        mc = ayame.MarkupContainer('a')
        mc.add(ayame.Component('b'))
        with self.assertRaisesRegex(ayame.ComponentError, r"\bcomponent .* 'c' .* not found\b"):
            mc.render(root)

    def test_render_replace_element_itself(self):
        class Component(ayame.Component):
            def on_render(self, element):
                return None

        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'b'})
        mc = ayame.MarkupContainer('a')
        mc.add(Component('b'))
        self.assertEqual(mc.render(root), '')

    def test_render_replace_element_itself_with_string(self):
        class Component(ayame.Component):
            def on_render(self, element):
                return ''

        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'b'})
        mc = ayame.MarkupContainer('a')
        mc.add(Component('b'))
        self.assertEqual(mc.render(root), '')

    def test_render_replace_element_itself_with_list(self):
        class Component(ayame.Component):
            def on_render(self, element):
                return ['>', '!', '<']

        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'b'})
        mc = ayame.MarkupContainer('a')
        mc.add(Component('b'))
        self.assertEqual(mc.render(root), ['>', '!', '<'])

    def test_render_remove_element(self):
        class Component(ayame.Component):
            def on_render(self, element):
                return None if int(self.id) % 2 else self.id

        root = markup.Element(self.of('root'))
        root.append('>')
        for i in range(1, 10):
            a = markup.Element(self.of('a'),
                               attrib={markup.AYAME_ID: str(i)})
            root.append(a)
        root.append('<')
        mc = ayame.MarkupContainer('a')
        for i in range(1, 10):
            mc.add(Component(str(i)))

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {})
        self.assertEqual(root.children, ['>', '2', '4', '6', '8', '<'])

    def test_render_replace_element_with_string(self):
        class Component(ayame.Component):
            def on_render(self, element):
                return ''

        root = markup.Element(self.of('root'))
        root.append('>')
        a = markup.Element(self.of('a'),
                           attrib={markup.AYAME_ID: 'b'})
        root.append(a)
        root.append('<')
        mc = ayame.MarkupContainer('a')
        mc.add(Component('b'))

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {})
        self.assertEqual(root.children, ['>', '', '<'])

    def test_render_replace_element_with_list(self):
        class Component(ayame.Component):
            def on_render(self, element):
                return [self.id, str(int(self.id) + 2)]

        root = markup.Element(self.of('root'))
        root.append('>')
        for i in range(2, 10, 4):
            a = markup.Element(self.of('a'),
                               attrib={markup.AYAME_ID: str(i)})
            root.append(a)
        root.append('<')
        mc = ayame.MarkupContainer('a')
        for i in range(2, 10, 4):
            mc.add(Component(str(i)))

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {})
        self.assertEqual(root.children, ['>', '2', '4', '6', '8', '<'])

    def test_render_replace_ayame_element_itself(self):
        class MarkupContainer(ayame.MarkupContainer):
            def on_render_element(self, element):
                return None

        root = markup.Element(self.ayame_of('root'))
        mc = MarkupContainer('a')
        self.assertEqual(mc.render(root), '')

    def test_render_replace_ayame_element_itself_with_string(self):
        class MarkupContainer(ayame.MarkupContainer):
            def on_render_element(self, element):
                return ''

        root = markup.Element(self.ayame_of('root'))
        mc = MarkupContainer('a')
        self.assertEqual(mc.render(root), '')

    def test_render_replace_ayame_element_itself_with_list(self):
        class MarkupContainer(ayame.MarkupContainer):
            def on_render_element(self, element):
                return ['>', '!', '<']

        root = markup.Element(self.ayame_of('root'))
        mc = MarkupContainer('a')
        self.assertEqual(mc.render(root), ['>', '!', '<'])

    def test_render_remove_ayame_element(self):
        class MarkupContainer(ayame.MarkupContainer):
            def on_render_element(self, element):
                n = element.qname.name
                return element if n == 'root' else None if n == 'a' else n

        root = markup.Element(self.of('root'))
        root.append('>')
        for i in range(1, 10):
            a = markup.Element(self.ayame_of('a' if i % 2 else str(i)))
            root.append(a)
        root.append('<')
        mc = MarkupContainer('a')

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {})
        self.assertEqual(root.children, ['>', '2', '4', '6', '8', '<'])

    def test_render_replace_ayame_element_with_string(self):
        class MarkupContainer(ayame.MarkupContainer):
            def on_render_element(self, element):
                return '' if element is a else element

        root = markup.Element(self.of('root'))
        root.append('>')
        a = markup.Element(self.ayame_of('a'))
        root.append(a)
        root.append('<')
        mc = MarkupContainer('a')

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {})
        self.assertEqual(root.children, ['>', '', '<'])

    def test_render_replace_ayame_element_with_list(self):
        class MarkupContainer(ayame.MarkupContainer):
            def on_render_element(self, element):
                n = element.qname.name
                if n == 'root':
                    return element
                elif element.qname.ns_uri == '':
                    return n
                return [n, markup.Element(markup.QName('', str(int(n) + 2)))]

        root = markup.Element(self.of('root'))
        root.append('>')
        for i in range(2, 10, 4):
            a = markup.Element(self.ayame_of(str(i)))
            root.append(a)
        root.append('<')
        mc = MarkupContainer('a')

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {})
        self.assertEqual(root.children, ['>', '2', '4', '6', '8', '<'])

    def test_render_ayame_container_no_ayame_id(self):
        root = markup.Element(self.of('root'))
        container = markup.Element(markup.AYAME_CONTAINER)
        root.append(container)
        mc = ayame.MarkupContainer('a')
        with self.assertRaisesRegex(ayame.RenderingError, r"'ayame:id' .* 'ayame:container'"):
            mc.render(root)

    def test_render_ayame_container_no_associated_component(self):
        root = markup.Element(self.of('root'))
        container = markup.Element(markup.AYAME_CONTAINER,
                                   attrib={markup.AYAME_ID: 'b'})
        root.append(container)
        mc = ayame.MarkupContainer('a')
        with self.assertRaisesRegex(ayame.ComponentError, r"\bcomponent .* 'b' .* not found\b"):
            mc.render(root)

    def test_render_ayame_container(self):
        def populate_item(li):
            li.add(basic.Label('c', li.model_object))

        root = markup.Element(self.of('root'))
        container = markup.Element(markup.AYAME_CONTAINER,
                                   attrib={markup.AYAME_ID: 'b'})
        root.append(container)
        a = markup.Element(self.of('a'),
                           attrib={markup.AYAME_ID: 'c'})
        container.append(a)
        mc = ayame.MarkupContainer('a')
        mc.add(basic.ListView('b', [str(i) for i in range(3)], populate_item))

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {})
        self.assertEqual(len(root), 3)

        a = root[0]
        self.assertEqual(a.qname, self.of('a'))
        self.assertEqual(a.attrib, {})
        self.assertEqual(a.children, ['0'])

        a = root[1]
        self.assertEqual(a.qname, self.of('a'))
        self.assertEqual(a.attrib, {})
        self.assertEqual(a.children, ['1'])

        a = root[2]
        self.assertEqual(a.qname, self.of('a'))
        self.assertEqual(a.attrib, {})
        self.assertEqual(a.children, ['2'])

    def test_render_ayame_enclosure_no_ayame_child(self):
        root = markup.Element(self.of('root'))
        enclosure = markup.Element(markup.AYAME_ENCLOSURE)
        root.append(enclosure)
        mc = ayame.MarkupContainer('a')
        with self.assertRaisesRegex(ayame.RenderingError, r"'ayame:child' .* 'ayame:enclosure'"):
            mc.render(root)

    def test_render_ayame_enclosure_no_associated_component(self):
        root = markup.Element(self.of('root'))
        enclosure = markup.Element(markup.AYAME_ENCLOSURE,
                                   attrib={markup.AYAME_CHILD: 'b'})
        root.append(enclosure)
        a = markup.Element(self.of('a'),
                           attrib={markup.AYAME_ID: 'b'})
        enclosure.append(a)
        mc = ayame.MarkupContainer('a')
        with self.assertRaisesRegex(ayame.ComponentError, r"\bcomponent .* 'b' .* not found\b"):
            mc.render(root)

    def test_render_ayame_enclosure_with_visible_component(self):
        root = markup.Element(self.of('root'))
        a = markup.Element(self.of('a'))
        root.append(a)
        enclosure = markup.Element(markup.AYAME_ENCLOSURE,
                                   attrib={markup.AYAME_CHILD: 'b1'})
        a.append(enclosure)
        b = markup.Element(self.of('b'),
                           attrib={markup.AYAME_ID: 'b1'})
        enclosure.append(b)
        b = markup.Element(self.of('b'))
        a.append(b)
        a = markup.Element(self.of('a'),
                           attrib={markup.AYAME_ID: 'b2'})
        root.append(a)
        mc = ayame.MarkupContainer('a')
        mc.add(basic.Label('b1', 'spam'))
        mc.add(basic.Label('b2', 'eggs'))

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {})
        self.assertEqual(len(root), 2)

        a = root[0]
        self.assertEqual(a.qname, self.of('a'))
        self.assertEqual(a.attrib, {})
        self.assertEqual(len(a), 2)

        b = a[0]
        self.assertEqual(b.qname, self.of('b'))
        self.assertEqual(b.attrib, {})
        self.assertEqual(b.children, ['spam'])

        b = a[1]
        self.assertEqual(b.qname, self.of('b'))
        self.assertEqual(b.attrib, {})
        self.assertEqual(b.children, [])

        a = root[1]
        self.assertEqual(a.qname, self.of('a'))
        self.assertEqual(a.attrib, {})
        self.assertEqual(a.children, ['eggs'])

    def test_render_ayame_enclosure_with_invisible_component(self):
        root = markup.Element(self.of('root'))
        a = markup.Element(self.of('a'))
        root.append(a)
        enclosure = markup.Element(markup.AYAME_ENCLOSURE,
                                   attrib={markup.AYAME_CHILD: 'b1'})
        a.append(enclosure)
        b = markup.Element(self.of('b'),
                           attrib={markup.AYAME_ID: 'b1'})
        enclosure.append(b)
        b = markup.Element(self.of('b'))
        a.append(b)
        a = markup.Element(self.of('a'),
                           attrib={markup.AYAME_ID: 'b2'})
        root.append(a)
        mc = ayame.MarkupContainer('a')
        mc.add(basic.Label('b1', 'spam'))
        mc.add(basic.Label('b2', 'eggs'))
        mc.find('b1').visible = False
        mc.find('b2').visible = False

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {})
        self.assertEqual(len(root), 1)

        a = root[0]
        self.assertEqual(a.qname, self.of('a'))
        self.assertEqual(a.attrib, {})
        self.assertEqual(len(a), 1)

        b = a[0]
        self.assertEqual(b.qname, self.of('b'))
        self.assertEqual(b.attrib, {})
        self.assertEqual(b.children, [])

    def test_render_ayame_message_element_no_value_for_key(self):
        with self.application(self.new_environ()):
            message = markup.Element(markup.AYAME_MESSAGE,
                                     attrib={markup.AYAME_KEY: 'b'})
            mc = ayame.MarkupContainer('a')
            with self.assertRaisesRegex(ayame.RenderingError, r" value .* ayame:message .* 'b'"):
                mc.render(message)

    def test_render_ayame_message_element(self):
        with self.application(self.new_environ(accept='en')):
            p = BeansPage()
            status, headers, content = p()
        html = self.format(BeansPage, message='Hello World!')
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

    def test_render_ayame_message_element_ja(self):
        with self.application(self.new_environ(accept='ja, en')):
            p = BeansPage()
            status, headers, content = p()
        html = self.format(BeansPage, message='\u3053\u3093\u306b\u3061\u306f\u4e16\u754c')
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

    def test_render_ayame_message_attribute_invalid_value(self):
        with self.application(self.new_environ()):
            root = markup.Element(self.of('root'),
                                  attrib={
                                      markup.AYAME_ID: 'b',
                                      markup.AYAME_MESSAGE: 'id',
                                  })
            mc = ayame.MarkupContainer('a')
            mc.add(ayame.Component('b'))
            with self.assertRaisesRegex(ayame.RenderingError, r'\binvalid .* ayame:message '):
                mc.render(root)

    def test_render_ayame_message_attribute(self):
        with self.application(self.new_environ(accept='en')):
            p = BaconPage()
            status, headers, content = p()
        html = self.format(BaconPage, message='Submit')
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

    def test_render_ayame_message_attribute_ja(self):
        with self.application(self.new_environ(accept='ja, en')):
            p = BaconPage()
            status, headers, content = p()
        html = self.format(BaconPage, message='\u9001\u4fe1')
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

    def test_render_ayame_head_unknown_root(self):
        root = markup.Element(self.of('root'))
        a = markup.Element(self.of('a'),
                           attrib={markup.AYAME_ID: 'b'})
        root.append(a)
        mc = ayame.MarkupContainer('a')
        mc.add(AyameHeadContainer('b'))
        with self.assertRaisesRegex(ayame.RenderingError, r"\broot element is not 'html'"):
            mc.find_head(root)

    def test_render_ayame_head_no_head(self):
        root = markup.Element(markup.HTML)
        a = markup.Element(self.of('a'),
                           attrib={markup.AYAME_ID: 'b'})
        root.append(a)
        mc = ayame.MarkupContainer('a')
        mc.add(AyameHeadContainer('b'))
        with self.assertRaisesRegex(ayame.RenderingError, r"'head' .* not found\b"):
            mc.render(root)

    def test_render_ayame_head(self):
        root = markup.Element(markup.HTML)
        head = markup.Element(markup.HEAD)
        root.append(head)
        a = markup.Element(self.of('a'),
                           attrib={markup.AYAME_ID: 'b'})
        root.append(a)
        h = markup.Element(self.of('h'))
        mc = ayame.MarkupContainer('a')
        mc.head = mc.find_head(root)
        mc.add(AyameHeadContainer('b', h))

        root = mc.render(root)
        self.assertEqual(root.qname, markup.HTML)
        self.assertEqual(root.attrib, {})
        self.assertEqual(len(root), 2)

        head = root[0]
        self.assertEqual(head.qname, markup.HEAD)
        self.assertEqual(head.attrib, {})
        self.assertEqual(head.type, markup.Element.OPEN)
        self.assertEqual(len(head), 1)

        h = head[0]
        self.assertEqual(h.qname, self.of('h'))
        self.assertEqual(h.attrib, {})
        self.assertEqual(h.children, [])

        a = root[1]
        self.assertEqual(a.qname, self.of('a'))
        self.assertEqual(a.attrib, {})
        self.assertEqual(a.children, [])

    def test_render_invisible_child(self):
        root = markup.Element(self.of('root'))
        a = markup.Element(self.of('a'))
        root.append(a)
        b = markup.Element(self.of('b'),
                           attrib={markup.AYAME_ID: 'b1'})
        a.append(b)
        c = markup.Element(self.of('c'),
                           attrib={markup.AYAME_ID: 'c1'})
        b.append(c)
        b = markup.Element(self.of('b'),
                           attrib={markup.AYAME_ID: 'b2'})
        a.append(b)
        c = markup.Element(self.of('c'),
                           attrib={markup.AYAME_ID: 'c2'})
        b.append(c)
        mc = ayame.MarkupContainer('a')
        mc.add(ayame.MarkupContainer('b1'))
        mc.find('b1').add(ayame.Component('c1'))
        mc.find('b1').visible = False
        mc.add(ayame.MarkupContainer('b2'))
        mc.find('b2').add(ayame.Component('c2'))

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {})
        self.assertEqual(len(root), 1)

        a = root.children[0]
        self.assertEqual(a.qname, self.of('a'))
        self.assertEqual(a.attrib, {})
        self.assertEqual(len(a), 1)

        b = a.children[0]
        self.assertEqual(b.qname, self.of('b'))
        self.assertEqual(b.attrib, {})
        self.assertEqual(len(b), 1)

        c = b.children[0]
        self.assertEqual(c.qname, self.of('c'))
        self.assertEqual(c.attrib, {})
        self.assertEqual(c.children, [])

    def test_markup_inheritance(self):
        class Spam(ayame.MarkupContainer):
            pass

        class Eggs(Spam):
            pass

        class Ham(Eggs):
            pass

        with self.application():
            mc = Ham('a')
            m = mc.load_markup()
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, markup.XHTML1_STRICT)
        self.assertTrue(m.root)

        html = m.root
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
            self.html_of('content'): 'Eggs',
        })
        self.assertEqual(meta.type, markup.Element.EMPTY)
        self.assertEqual(meta.ns, {})
        self.assertEqual(meta.children, [])

        meta = head[9]
        self.assertEqual(meta.qname, self.html_of('meta'))
        self.assertEqual(meta.attrib, {
            self.html_of('name'): 'class',
            self.html_of('content'): 'Ham',
        })
        self.assertEqual(meta.type, markup.Element.EMPTY)
        self.assertEqual(meta.ns, {})
        self.assertEqual(meta.children, [])

        body = html[3]
        self.assertEqual(body.qname, self.html_of('body'))
        self.assertEqual(body.attrib, {})
        self.assertEqual(body.type, markup.Element.OPEN)
        self.assertEqual(body.ns, {})
        self.assertEqual(len(body), 13)
        self.assertWS(body, 0)
        self.assertWS(body, 2)
        self.assertWS(body, 3)
        self.assertWS(body, 5)
        self.assertWS(body, 6)
        self.assertWS(body, 8)
        self.assertWS(body, 9)
        self.assertWS(body, 10)
        self.assertWS(body, 12)

        p = body[1]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['before ayame:child (Spam)'])

        p = body[4]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['inside ayame:extend (Eggs)'])

        p = body[7]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['inside ayame:extend (Ham)'])

        p = body[11]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['after ayame:child (Spam)'])

    def test_markup_inheritance_empty_submarkup(self):
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

        html = m.root
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
        self.assertEqual(len(body), 6)
        self.assertWS(body, 0)
        self.assertWS(body, 2)
        self.assertWS(body, 3)
        self.assertWS(body, 5)

        p = body[1]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['before ayame:child (Spam)'])

        p = body[4]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['after ayame:child (Spam)'])

    def test_markup_inheritance_merge_ayame_head(self):
        class Bacon(ayame.MarkupContainer):
            pass

        class Sausage(Bacon):
            pass

        with self.application():
            mc = Sausage('a')
            m = mc.load_markup()
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, markup.XHTML1_STRICT)
        self.assertTrue(m.root)

        html = m.root
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

        ayame_head = html[1]
        self.assertEqual(ayame_head.qname, self.ayame_of('head'))
        self.assertEqual(ayame_head.attrib, {})
        self.assertEqual(ayame_head.type, markup.Element.OPEN)
        self.assertEqual(ayame_head.ns, {})
        self.assertEqual(len(ayame_head), 8)
        self.assertWS(ayame_head, 0)
        self.assertWS(ayame_head, 2)
        self.assertWS(ayame_head, 4)
        self.assertWS(ayame_head, 5)
        self.assertWS(ayame_head, 7)

        title = ayame_head[1]
        self.assertEqual(title.qname, self.html_of('title'))
        self.assertEqual(title.attrib, {})
        self.assertEqual(title.type, markup.Element.OPEN)
        self.assertEqual(title.ns, {})
        self.assertEqual(title.children, ['Bacon'])

        meta = ayame_head[3]
        self.assertEqual(meta.qname, self.html_of('meta'))
        self.assertEqual(meta.attrib, {
            self.html_of('name'): 'class',
            self.html_of('content'): 'Bacon',
        })
        self.assertEqual(meta.type, markup.Element.EMPTY)
        self.assertEqual(meta.ns, {})
        self.assertEqual(meta.children, [])

        meta = ayame_head[6]
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
        self.assertEqual(len(body), 6)
        self.assertWS(body, 0)
        self.assertWS(body, 2)
        self.assertWS(body, 3)
        self.assertWS(body, 5)

        p = body[1]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['before ayame:child (Bacon)'])

        p = body[4]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['after ayame:child (Bacon)'])

    def test_markup_inheritance_no_superclass(self):
        class Sausage(ayame.MarkupContainer):
            pass

        with self.application():
            mc = Sausage('a')
            with self.assertRaisesRegex(ayame.AyameError, r'^superclass .* not found$'):
                mc.load_markup()

    def test_markup_inheritance_multiple_inheritance(self):
        class Spam(ayame.MarkupContainer):
            pass

        class Toast(ayame.MarkupContainer):
            pass

        class Beans(ayame.MarkupContainer):
            pass

        class Bacon(ayame.MarkupContainer):
            pass

        class Sausage(Spam, Toast, Beans, Bacon):
            pass

        with self.application():
            mc = Sausage('a')
            with self.assertRaisesRegex(ayame.AyameError, r' multiple inheritance$'):
                mc.load_markup()

    def test_markup_inheritance_no_ayame_child(self):
        class Toast(ayame.MarkupContainer):
            pass

        class Sausage(Toast):
            pass

        with self.application():
            mc = Sausage('a')
            with self.assertRaisesRegex(ayame.RenderingError, r"'ayame:child' .* not found\b"):
                mc.load_markup()

    def test_markup_inheritance_no_head(self):
        class Beans(ayame.MarkupContainer):
            pass

        class Sausage(Beans):
            pass

        with self.application():
            mc = Sausage('a')
            with self.assertRaisesRegex(ayame.RenderingError, r"'head' .* not found\b"):
                mc.load_markup()

    def test_markup_inheritance_ayame_child_as_root(self):
        class Tomato(ayame.MarkupContainer):
            pass

        class Sausage(Tomato):
            pass

        with self.application():
            mc = Sausage('a')
            with self.assertRaisesRegex(ayame.RenderingError, r"'ayame:child' .* root element\b"):
                mc.load_markup()

    def test_markup_inheritance_empty_markup(self):
        class Lobster(ayame.MarkupContainer):
            pass

        class Sausage(Lobster):
            pass

        with self.application():
            mc = Sausage('a')
            m = mc.load_markup()
        self.assertEqual(m.xml_decl, {})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertIsNone(m.doctype)
        self.assertIsNone(m.root)

        class Lobster(ayame.Page):
            pass

        with self.application(self.new_environ()):
            p = Lobster()
            status, headers, content = p()
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', '0'),
        ])
        self.assertEqual(content, [b''])

    def test_markup_inheritance_duplicate_ayame_elements(self):
        class Shallots(ayame.MarkupContainer):
            pass

        class Aubergine(Shallots):
            pass

        with self.application():
            mc = Aubergine('a')
            m = mc.load_markup()
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, markup.XHTML1_STRICT)
        self.assertTrue(m.root)

        html = m.root
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
        self.assertEqual(title.children, ['Shallots'])

        meta = head[3]
        self.assertEqual(meta.qname, self.html_of('meta'))
        self.assertEqual(meta.attrib, {
            self.html_of('name'): 'class',
            self.html_of('content'): 'Shallots',
        })
        self.assertEqual(meta.type, markup.Element.EMPTY)
        self.assertEqual(meta.ns, {})
        self.assertEqual(meta.children, [])

        meta = head[6]
        self.assertEqual(meta.qname, self.html_of('meta'))
        self.assertEqual(meta.attrib, {
            self.html_of('name'): 'class',
            self.html_of('content'): 'Aubergine',
        })
        self.assertEqual(meta.type, markup.Element.EMPTY)
        self.assertEqual(meta.ns, {})
        self.assertEqual(meta.children, [])

        body = html[3]
        self.assertEqual(body.qname, self.html_of('body'))
        self.assertEqual(body.attrib, {})
        self.assertEqual(body.type, markup.Element.OPEN)
        self.assertEqual(body.ns, {})
        self.assertEqual(len(body), 8)
        self.assertWS(body, 0)
        self.assertWS(body, 2)
        self.assertWS(body, 3)
        self.assertWS(body, 5)
        self.assertWS(body, 7)

        p = body[1]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['before ayame:child (Shallots)'])

        ayame_child = body[4]
        self.assertEqual(ayame_child.qname, self.ayame_of('child'))
        self.assertEqual(ayame_child.attrib, {})
        self.assertEqual(ayame_child.type, markup.Element.EMPTY)
        self.assertEqual(ayame_child.ns, {})
        self.assertEqual(ayame_child.children, [])

        p = body[6]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(p.children, ['after ayame:child (Shallots)'])

    def test_page(self):
        class SpamPage(ayame.Page):
            html_t = textwrap.dedent("""\
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
            """)

            def __init__(self):
                super().__init__()
                self.add(basic.Label('message', 'Hello World!'))
                self.headers['Content-Type'] = 'text/plain'

        with self.application(self.new_environ()):
            p = SpamPage()
            status, headers, content = p()
        html = self.format(SpamPage)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        self.assertEqual(p.page(), p)
        self.assertEqual(p.find('message').page(), p)
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
            def on_before_render(self, component):
                super().on_before_render(component)
                component.model_object.append('before-render')

            def on_component(self, component, element):
                super().on_component(component, element)
                component.model_object.append('component')

            def on_after_render(self, component):
                super().on_after_render(component)
                component.model_object.append('after-render')

        c = ayame.Component('a', model.Model([]))
        c.add(Behavior())
        self.assertEqual(len(c.behaviors), 1)
        self.assertEqual(c.behaviors[0].component, c)

        self.assertIsNone(c.render(None))
        self.assertEqual(c.model_object, ['before-render', 'component', 'after-render'])

        mc = ayame.MarkupContainer('a', model.Model([]))
        mc.add(Behavior())
        self.assertEqual(len(c.behaviors), 1)
        self.assertEqual(mc.behaviors[0].component, mc)

        self.assertIsNone(mc.render(None))
        self.assertEqual(mc.model_object, ['before-render', 'component', 'after-render'])

    def test_attribute_modifier_on_component(self):
        root = markup.Element(self.of('root'),
                              attrib={self.of('a'): ''})
        c = ayame.Component('a')
        c.add(ayame.AttributeModifier('a', model.Model(None)))
        c.add(ayame.AttributeModifier(self.of('b'),
                                      model.Model(None)))
        c.add(ayame.AttributeModifier('c', model.Model('')))
        self.assertEqual(len(c.behaviors), 3)
        self.assertEqual(c.behaviors[0].component, c)
        self.assertEqual(c.behaviors[1].component, c)
        self.assertEqual(c.behaviors[2].component, c)

        root = c.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {self.of('c'): ''})
        self.assertEqual(root.children, [])

    def test_attribute_modifier_on_markup_container(self):
        root = markup.Element(self.of('root'),
                              attrib={self.of('a'): ''})
        mc = ayame.MarkupContainer('a')
        mc.add(ayame.AttributeModifier('a', model.Model(None)))
        mc.add(ayame.AttributeModifier(self.of('b'),
                                       model.Model(None)))
        mc.add(ayame.AttributeModifier('c', model.Model('')))
        self.assertEqual(len(mc.behaviors), 3)
        self.assertEqual(mc.behaviors[0].component, mc)
        self.assertEqual(mc.behaviors[1].component, mc)
        self.assertEqual(mc.behaviors[2].component, mc)

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {self.of('c'): ''})
        self.assertEqual(root.children, [])

    def test_fire_get(self):
        query = '{path}=clay1'
        with self.application(self.new_environ(query=query)):
            p = EggsPage()
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        self.assertEqual(p.model_object, {
            'clay1': 1,
            'clay2': 0,
        })

    def test_fire_get_duplicate_ayame_path(self):
        query = ('{path}=clay1&'
                 '{path}=obstacle:clay2')
        with self.application(self.new_environ(query=query)):
            p = EggsPage()
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        self.assertEqual(p.model_object, {
            'clay1': 1,
            'clay2': 0,
        })

    def test_fire_get_nonexistent_path(self):
        query = '{path}=clay2'
        with self.application(self.new_environ(query=query)):
            p = EggsPage()
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        self.assertEqual(p.model_object, {
            'clay1': 0,
            'clay2': 0,
        })

    def test_fire_get_invisible_component(self):
        query = '{path}=clay1'
        with self.application(self.new_environ(query=query)):
            p = EggsPage()
            p.find('clay1').visible = False
            status, headers, content = p()
        html = self.format(EggsPage, clay1=False)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        self.assertEqual(p.model_object, {
            'clay1': 0,
            'clay2': 0,
        })

    def test_fire_post(self):
        data = self.form_data(('{path}', 'obstacle:clay2'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        self.assertEqual(p.model_object, {
            'clay1': 0,
            'clay2': 1,
        })

    def test_fire_post_duplicate_ayame_path(self):
        data = self.form_data(('{path}', 'obstacle:clay2'),
                              ('{path}', 'clay1'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        self.assertEqual(p.model_object, {
            'clay1': 0,
            'clay2': 1,
        })

    def test_fire_post_nonexistent_path(self):
        data = self.form_data(('{path}', 'clay2'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        self.assertEqual(p.model_object, {
            'clay1': 0,
            'clay2': 0,
        })

    def test_fire_post_invisible_component(self):
        data = self.form_data(('{path}', 'clay1'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            p.find('clay1').visible = False
            status, headers, content = p()
        html = self.format(EggsPage, clay1=False)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        self.assertEqual(p.model_object, {
            'clay1': 0,
            'clay2': 0,
        })

    def test_fire_component(self):
        query = '{path}=c'
        with self.application(self.new_environ(query=query)):
            c = Component('c')
            c.fire()
        self.assertEqual(c.model_object, 1)

    def test_fire_component_uknown_path(self):
        query = '{path}=g'
        with self.application(self.new_environ(query=query)):
            c = Component('c')
            c.fire()
        self.assertEqual(c.model_object, 0)

    def test_fire_component_invisible(self):
        query = '{path}=c'
        with self.application(self.new_environ(query=query)):
            c = Component('c')
            c.visible = False
            c.fire()
        self.assertEqual(c.model_object, 0)

    def test_nested(self):
        regex = r' not .* subclass of MarkupContainer$'

        with self.assertRaisesRegex(ayame.AyameError, regex):
            class C:
                @ayame.nested
                class C:
                    pass

        with self.assertRaisesRegex(ayame.AyameError, regex):
            class C:
                @ayame.nested
                def f(self):
                    pass

        class C:
            @ayame.nested
            class MarkupContainer(ayame.MarkupContainer):
                pass

        self.assertIsInstance(C.MarkupContainer('a'), ayame.MarkupContainer)

    def test_nested_class_markup(self):
        class HamPage(ayame.Page):
            html_t = textwrap.dedent("""\
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
            """)

        class ToastPage(HamPage):
            markup_type = markup.MarkupType('.htm', 'text/html', ())

            @ayame.nested
            class NestedPage(HamPage):
                pass

        mt = markup.MarkupType('.htm', 'text/html', ())
        self.assertEqual(ToastPage.markup_type, mt)
        mt = markup.MarkupType('.html', 'text/html', (ToastPage,))
        self.assertEqual(ToastPage.NestedPage.markup_type, mt)

        with self.application(self.new_environ()):
            p = ToastPage()
            status, headers, content = p()
        html = self.format(ToastPage, name='ToastPage')
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        with self.application(self.new_environ()):
            p = ToastPage.NestedPage()
            status, headers, content = p()
        html = self.format(ToastPage, name='ToastPage.NestedPage')
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

    def test_element(self):
        class Lobster(ayame.MarkupContainer):
            pass

        with self.application():
            mc = Lobster('a')
            mc.add(ayame.MarkupContainer('b'))
            mc.has_markup = False
            self.assertIsNone(mc.find('b').element())
            mc.has_markup = True
            self.assertIsNone(mc.find('b').element())

        class Toast(ayame.MarkupContainer):
            pass

        with self.application():
            mc = Toast('a')
            mc.add(ayame.MarkupContainer('b'))
            mc.has_markup = True
            mc.find('b').element()

        with self.application():
            p = EggsPage()
            self.assertIsInstance(p.find('clay1').element(), markup.Element)
            self.assertIsInstance(p.find('obstacle:clay2').element(), markup.Element)

    def test_cache(self):
        config = self.app.config.copy()
        try:
            self.app.config['ayame.resource.loader'] = self.new_resource_loader()
            self.app.config['ayame.markup.cache'] = cache = config['ayame.markup.cache'].copy()

            with self.application(self.new_environ()):
                p = EggsPage()
                p()
            self.assertEqual(len(cache), 1)

            with self.application(self.new_environ()):
                p = EggsPage()
                with self.assertRaises(OSError):
                    p()
            self.assertEqual(len(cache), 0)

            with self.application(self.new_environ()):
                p = EggsPage()
                with self.assertRaises(ayame.ResourceError):
                    p()
            self.assertEqual(len(cache), 0)
        finally:
            self.app.config = config


class Component(ayame.Component):

    def __init__(self, id):
        super().__init__(id, model.Model(0))

    def on_fire(self):
        self.model_object += 1


class AyameHeadContainer(ayame.MarkupContainer):

    def __init__(self, id, elem=None):
        super().__init__(id)
        self._elem = elem

    def on_render(self, element):
        for par in self.iter_parent():
            pass
        par.head.children.append(self._elem)
        return element


class EggsPage(ayame.Page):

    html_t = textwrap.dedent("""\
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
    """)
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


class BeansPage(ayame.Page):

    html_t = textwrap.dedent("""\
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
    """)


class BaconPage(ayame.Page):

    html_t = textwrap.dedent("""\
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
    """)
