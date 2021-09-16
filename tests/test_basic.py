#
# test_basic
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import ayame
from ayame import basic, markup, model
from base import AyameTestCase


class BasicTestCase(AyameTestCase):

    def test_label(self):
        c = basic.Label('a')
        self.assertIsNone(c.model)

        elem = c.render(markup.Element(None))
        self.assertEqual(elem.attrib, {})
        self.assertEqual(elem.children, [''])

    def test_label_with_object_model(self):
        with self.application():
            m = model.Model([])
            c = basic.Label('a', m)
            self.assertIs(c.model, m)

            elem = c.render(markup.Element(None))
            self.assertEqual(elem.attrib, {})
            self.assertEqual(elem.children, ['[]'])

    def test_label_with_string_model(self):
        with self.application():
            m = model.Model('<tag>')
            c = basic.Label('a', m)
            self.assertIs(c.model, m)

            elem = c.render(markup.Element(None))
            self.assertEqual(elem.attrib, {})
            self.assertEqual(elem.children, ['&lt;tag&gt;'])

    def test_label_with_string(self):
        with self.application():
            c = basic.Label('a', '<tag>')
            self.assertEqual(c.model.object, '<tag>')

            elem = c.render(markup.Element(None))
            self.assertEqual(elem.attrib, {})
            self.assertEqual(elem.children, ['&lt;tag&gt;'])

    def test_list_view_empty_model(self):
        def populate_item(li):
            li.add(basic.Label('c', li.model.object))

        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'b'})
        label = markup.Element(self.of('label'),
                               attrib={markup.AYAME_ID: 'c'})
        root.append(label)
        mc = ayame.MarkupContainer('a')
        m = model.Model(None)
        mc.add(basic.ListView('b', m, populate_item))

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {})
        self.assertEqual(root.children, [])

    def test_list_view_error(self):
        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'b'})
        label = markup.Element(self.of('label'),
                               attrib={markup.AYAME_ID: 'c'})
        root.append(label)
        mc = ayame.MarkupContainer('a')
        m = model.Model([str(i) for i in range(3)])
        mc.add(basic.ListView('b', m, None))

        with self.assertRaisesRegex(ayame.ComponentError, r"\bcomponent .* 'c' .* not found\b"):
            mc.render(root)

    def test_list_view(self):
        def populate_item(li):
            li.add(basic.Label('c', li.model.object))

        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'b'})
        label = markup.Element(self.of('label'),
                               attrib={markup.AYAME_ID: 'c'})
        root.append(label)
        mc = ayame.MarkupContainer('a')
        m = model.Model([str(i) for i in range(3)])
        mc.add(basic.ListView('b', m, populate_item))

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {})
        self.assertEqual(len(root), 3)

        label = root[0]
        self.assertEqual(label.qname, self.of('label'))
        self.assertEqual(label.attrib, {})
        self.assertEqual(label.children, ['0'])

        label = root[1]
        self.assertEqual(label.qname, self.of('label'))
        self.assertEqual(label.attrib, {})
        self.assertEqual(label.children, ['1'])

        label = root[2]
        self.assertEqual(label.qname, self.of('label'))
        self.assertEqual(label.attrib, {})
        self.assertEqual(label.children, ['2'])

        self.assertEqual(len(mc.children), 1)
        lv = mc.children[0]
        self.assertEqual(len(lv.children), 3)
        self.assertEqual(lv.children[0].index, 0)
        self.assertEqual(lv.children[1].index, 1)
        self.assertEqual(lv.children[2].index, 2)

        self.assertIsInstance(lv.children[0].model, basic._ListItemModel)
        self.assertIsInstance(lv.children[1].model, basic._ListItemModel)
        self.assertIsInstance(lv.children[2].model, basic._ListItemModel)
        lv.children[0].model.object = 10
        lv.children[1].model.object = 11
        lv.children[2].model.object = 12
        self.assertEqual(lv.children[0].model.object, 10)
        self.assertEqual(lv.children[1].model.object, 11)
        self.assertEqual(lv.children[2].model.object, 12)

    def test_list_view_render_body_only(self):
        def populate_item(li):
            li.add(basic.Label('c', li.model.object))
            li.find('c').render_body_only = True

        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'b'})
        root.append('[')
        label = markup.Element(self.of('label'),
                               attrib={markup.AYAME_ID: 'c'})
        root.append(label)
        root.append(']')
        mc = ayame.MarkupContainer('a')
        mc.add(basic.ListView('b', [str(i) for i in range(3)], populate_item))

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {})
        self.assertEqual(len(root), 9)
        root.normalize()
        self.assertEqual(root.children, ['[0][1][2]'])

    def test_property_list_view(self):
        def populate_item(li):
            li.add(basic.Label('c', li.model.object))

        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'b'})
        label = markup.Element(self.of('label'),
                               attrib={markup.AYAME_ID: 'c'})
        root.append(label)
        m = model.CompoundModel({'b': [str(i) for i in range(3)]})
        mc = ayame.MarkupContainer('a', m)
        mc.add(basic.PropertyListView('b', None, populate_item))

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {})
        self.assertEqual(len(root), 3)

        label = root[0]
        self.assertEqual(label.qname, self.of('label'))
        self.assertEqual(label.attrib, {})
        self.assertEqual(label.children, ['0'])

        label = root[1]
        self.assertEqual(label.qname, self.of('label'))
        self.assertEqual(label.attrib, {})
        self.assertEqual(label.children, ['1'])

        label = root[2]
        self.assertEqual(label.qname, self.of('label'))
        self.assertEqual(label.attrib, {})
        self.assertEqual(label.children, ['2'])

        self.assertEqual(len(mc.children), 1)
        lv = mc.children[0]
        self.assertEqual(len(lv.children), 3)
        self.assertEqual(lv.children[0].index, 0)
        self.assertEqual(lv.children[1].index, 1)
        self.assertEqual(lv.children[2].index, 2)

        self.assertIsInstance(lv.children[0].model, model.CompoundModel)
        self.assertIsInstance(lv.children[1].model, model.CompoundModel)
        self.assertIsInstance(lv.children[2].model, model.CompoundModel)
        lv.children[0].model.object = 10
        lv.children[1].model.object = 11
        lv.children[2].model.object = 12
        self.assertEqual(lv.children[0].model.object, 10)
        self.assertEqual(lv.children[1].model.object, 11)
        self.assertEqual(lv.children[2].model.object, 12)

    def test_property_list_view_render_body_only(self):
        def populate_item(li):
            li.add(basic.Label('c', li.model.object))
            li.find('c').render_body_only = True

        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'b'})
        root.append('[')
        label = markup.Element(self.of('label'),
                               attrib={markup.AYAME_ID: 'c'})
        root.append(label)
        root.append(']')
        m = model.CompoundModel({'b': [str(i) for i in range(3)]})
        mc = ayame.MarkupContainer('a', m)
        mc.add(basic.PropertyListView('b', None, populate_item))

        root = mc.render(root)
        self.assertEqual(root.qname, self.of('root'))
        self.assertEqual(root.attrib, {})
        self.assertEqual(len(root), 9)
        root.normalize()
        self.assertEqual(root.children, ['[0][1][2]'])

    def test_context_path_generator(self):
        for path, value in (
            ('/spam', 'eggs.html'),
            ('/spam/', '../eggs.html'),
        ):
            with self.subTest(path=path, value=value):
                a = markup.Element(self.html_of('a'))
                href = self.html_of('href')
                with self.application(self.new_environ(path=path)):
                    am = basic.ContextPathGenerator(href, 'eggs.html')
                    am.on_component(None, a)
                self.assertEqual(a.attrib, {href: value})

    def test_context_image(self):
        for path, value in (
            ('/spam', 'eggs.gif'),
            ('/spam/', '../eggs.gif'),
        ):
            with self.subTest(path=path, value=value):
                img = markup.Element(self.html_of('img'))
                src = self.html_of('src')
                with self.application(self.new_environ(path=path)):
                    c = basic.ContextImage(src, 'eggs.gif')
                    img = c.render(img)
                self.assertEqual(img.attrib, {src: value})

    def test_context_link(self):
        for path, value in (
            ('/spam', 'eggs.css'),
            ('/spam/', '../eggs.css'),
        ):
            with self.subTest(path=path, value=value):
                meta = markup.Element(self.html_of('meta'))
                href = self.html_of('href')
                with self.application(self.new_environ(path=path)):
                    c = basic.ContextLink(href, 'eggs.css')
                    meta = c.render(meta)
                self.assertEqual(meta.attrib, {href: value})
