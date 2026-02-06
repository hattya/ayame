#
# test_basic
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import ayame
from ayame import basic, markup, model
from base import AyameTestCase, ElementBuilder


class BasicTestCase(AyameTestCase):

    def test_label(self):
        el = self.empty_element()
        c = basic.Label('a')
        self.assertIsNone(c.model)

        rv = c.render(el)
        self.assertIs(rv, el)
        self.assertEqual(rv.attrib, {})
        self.assertEqual(rv.children, [''])

    def test_label_with_model(self):
        el = self.empty_element()
        m = model.Model('&<>')
        c = basic.Label('a', m)
        self.assertIs(c.model, m)
        self.assertEqual(c.model.object, '&<>')
        with self.application():
            rv = c.render(el)
            self.assertIs(rv, el)
            self.assertEqual(rv.attrib, {})
            self.assertEqual(rv.children, ['&amp;&lt;&gt;'])

    def test_label_with_string(self):
        el = self.empty_element()
        c = basic.Label('a', '&<>')
        self.assertEqual(c.model.object, '&<>')
        with self.application():
            rv = c.render(el)
            self.assertIs(rv, el)
            self.assertEqual(rv.attrib, {})
            self.assertEqual(rv.children, ['&amp;&lt;&gt;'])

    def test_list_view_with_empty_model(self):
        el = self.empty_element(attrib={
            markup.AYAME_ID: 'b',
        })
        el.append(self.empty_element(attrib={
            markup.AYAME_ID: 'c',
        }))
        mc = ayame.MarkupContainer('a')
        m = model.Model(None)
        mc.add(basic.ListView('b', m, lambda li: None))
        self.assertIs(mc.find('b').model, m)

        rv = mc.render(el)
        self.assertIs(rv, el)
        self.assertEqual(rv.attrib, {})
        self.assertEqual(rv.children, [])

    def test_list_view_without_populate_item(self):
        el = self.empty_element(attrib={
            markup.AYAME_ID: 'b',
        })
        el.append(self.empty_element(attrib={
            markup.AYAME_ID: 'c',
        }))
        mc = ayame.MarkupContainer('a')
        m = model.Model([1, 2, 3])
        mc.add(basic.ListView('b', m, None))

        with self.assertRaisesRegex(ayame.ComponentError, r"\bcomponent .* 'c' .* not found\b"):
            mc.render(el)

    def test_list_view(self):
        def populate_item(li):
            li.add(basic.Label('c', li.model_object))

        b = ElementBuilder(markup.XHTML_NS)
        with b.open('ul',
                    {
                        'ayame:id': 'b',
                    },
                    ns=self.ns):
            with b.open('li',
                        {
                            'ayame:id': 'c',
                        }):
                pass
        el = b.root
        o = list('123')
        m = model.Model(o)
        mc = ayame.MarkupContainer('a')
        mc.add(basic.ListView('b', m, populate_item))
        self.assertIs(mc.find('b').model, m)

        rv = mc.render(el)
        self.assertIs(rv, el)
        with b.open('ul',
                    ns=self.ns):
            with b.open('li'):
                b.str('1')
            with b.open('li'):
                b.str('2')
            with b.open('li'):
                b.str('3')
        self.assertElementEqual(rv, b.root)

        lv = mc.find('b')
        self.assertEqual(len(lv.children), 3)
        self.assertEqual(lv.children[0].index, 0)
        self.assertEqual(lv.children[0].model_object, '1')
        self.assertEqual(lv.children[1].index, 1)
        self.assertEqual(lv.children[1].model_object, '2')
        self.assertEqual(lv.children[2].index, 2)
        self.assertEqual(lv.children[2].model_object, '3')

        lv.children[0].model_object = '7'
        lv.children[1].model_object = '8'
        lv.children[2].model_object = '9'
        self.assertEqual(lv.children[0].model_object, '7')
        self.assertEqual(lv.children[1].model_object, '8')
        self.assertEqual(lv.children[2].model_object, '9')
        self.assertEqual(o, list('789'))

    def test_list_view_with_render_body_only(self):
        def populate_item(li):
            li.add(basic.Label('c', li.model.object))
            li.find('c').render_body_only = True

        el = self.empty_element(attrib={
            markup.AYAME_ID: 'b',
        })
        el.append('[')
        el.append(self.empty_element(attrib={
            markup.AYAME_ID: 'c',
        }))
        el.append(']')
        mc = ayame.MarkupContainer('a')
        mc.add(basic.ListView('b', list('123'), populate_item))

        rv = mc.render(el)
        self.assertIs(rv, el)
        self.assertEqual(rv.attrib, {})
        self.assertEqual(rv.children, list('[1][2][3]'))

    def test_property_list_view(self):
        def populate_item(li):
            li.add(basic.Label('c'))

        b = ElementBuilder(markup.XHTML_NS)
        with b.open('ul',
                    {
                        'ayame:id': 'b',
                    },
                    ns=self.ns):
            with b.open('li',
                        {
                            'ayame:id': 'c',
                        }):
                pass
        el = b.root
        o = {'b': [{'c': v} for v in '123']}
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer('a', m)
        mc.add(basic.PropertyListView('b', None, populate_item))
        self.assertIs(mc.model, m)

        rv = mc.render(el)
        self.assertIs(rv, el)
        with b.open('ul',
                    ns=self.ns):
            with b.open('li'):
                b.str('1')
            with b.open('li'):
                b.str('2')
            with b.open('li'):
                b.str('3')
        self.assertElementEqual(rv, b.root)

        lv = mc.find('b')
        self.assertEqual(len(lv.children), 3)
        self.assertEqual(lv.children[0].index, 0)
        self.assertEqual(lv.children[0].model_object, {'c': '1'})
        self.assertEqual(lv.children[1].index, 1)
        self.assertEqual(lv.children[1].model_object, {'c': '2'})
        self.assertEqual(lv.children[2].index, 2)
        self.assertEqual(lv.children[2].model_object, {'c': '3'})

        lv.children[0].find('c').model_object = '7'
        lv.children[1].find('c').model_object = '8'
        lv.children[2].find('c').model_object = '9'
        self.assertEqual(lv.children[0].model_object, {'c': '7'})
        self.assertEqual(lv.children[1].model_object, {'c': '8'})
        self.assertEqual(lv.children[2].model_object, {'c': '9'})
        self.assertEqual(o, {'b': [{'c': v} for v in '789']})

    def test_property_list_view_render_body_only(self):
        def populate_item(li):
            li.add(basic.Label('c'))
            li.find('c').render_body_only = True

        el = self.empty_element(attrib={
            markup.AYAME_ID: 'b',
        })
        el.append('[')
        el.append(self.empty_element(attrib={
            markup.AYAME_ID: 'c',
        }))
        el.append(']')
        m = model.CompoundModel({'b': [{'c': v} for v in '123']})
        mc = ayame.MarkupContainer('a', m)
        mc.add(basic.PropertyListView('b', None, populate_item))

        rv = mc.render(el)
        self.assertIs(rv, el)
        self.assertEqual(rv.attrib, {})
        self.assertEqual(rv.children, list('[1][2][3]'))

    def test_context_path_generator(self):
        for p, v in (
            ('/spam', 'eggs.html'),
            ('/spam/', '../eggs.html'),
        ):
            with self.subTest(path=p):
                href = self.html_of('href')
                a = markup.Element(self.html_of('a'),
                                   {
                                       href: '',
                                   })
                c = ayame.Component(__name__)
                with self.application(self.new_environ(path=p)):
                    am = basic.ContextPathGenerator(href, 'eggs.html')
                    am.on_component(c, a)
                self.assertEqual(a.attrib, {href: v})

    def test_context_image(self):
        for p, v in (
            ('/spam', 'eggs.gif'),
            ('/spam/', '../eggs.gif'),
        ):
            with self.subTest(path=p):
                src = self.html_of('src')
                img = markup.Element(self.html_of('img'),
                                     {
                                         src: '',
                                     })
                c = basic.ContextImage(src, 'eggs.gif')
                with self.application(self.new_environ(path=p)):
                    img = c.render(img)
                self.assertEqual(img.attrib, {src: v})

    def test_context_link(self):
        for p, v in (
            ('/spam', 'eggs.css'),
            ('/spam/', '../eggs.css'),
        ):
            with self.subTest(path=p):
                href = self.html_of('href')
                link = markup.Element(self.html_of('link'),
                                      {
                                          href: '',
                                      })
                c = basic.ContextLink(href, 'eggs.css')
                with self.application(self.new_environ(path=p)):
                    link = c.render(link)
                self.assertEqual(link.attrib, {href: v})
