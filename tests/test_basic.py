#
# test_basic
#
#   Copyright (c) 2011-2014 Akinori Hattori <hattya@gmail.com>
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
from ayame import _compat as five
from ayame import basic, markup, model
from base import AyameTestCase


class BasicTestCase(AyameTestCase):

    def test_label(self):
        c = basic.Label('a')
        self.assert_is_none(c.model)

        elem = c.render(markup.Element(None))
        self.assert_equal(elem.attrib, {})
        self.assert_equal(elem.children, [''])

    def test_label_with_object_model(self):
        with self.application():
            m = model.Model([])
            c = basic.Label('a', m)
            self.assert_is(c.model, m)

            elem = c.render(markup.Element(None))
            self.assert_equal(elem.attrib, {})
            self.assert_equal(elem.children, ['[]'])

    def test_label_with_string_model(self):
        with self.application():
            m = model.Model('<tag>')
            c = basic.Label('a', m)
            self.assert_is(c.model, m)

            elem = c.render(markup.Element(None))
            self.assert_equal(elem.attrib, {})
            self.assert_equal(elem.children, ['&lt;tag&gt;'])

    def test_label_with_string(self):
        with self.application():
            c = basic.Label('a', '<tag>')
            self.assert_equal(c.model.object, '<tag>')

            elem = c.render(markup.Element(None))
            self.assert_equal(elem.attrib, {})
            self.assert_equal(elem.children, ['&lt;tag&gt;'])

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
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(root.children, [])

    def test_list_view_error(self):
        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'b'})
        label = markup.Element(self.of('label'),
                               attrib={markup.AYAME_ID: 'c'})
        root.append(label)
        mc = ayame.MarkupContainer('a')
        m = model.Model([str(i) for i in five.range(3)])
        mc.add(basic.ListView('b', m, None))

        with self.assert_raises_regex(ayame.ComponentError,
                                      r"\bcomponent .* 'c' .* not found\b"):
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
        m = model.Model([str(i) for i in five.range(3)])
        mc.add(basic.ListView('b', m, populate_item))

        root = mc.render(root)
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(len(root), 3)

        label = root[0]
        self.assert_equal(label.qname, self.of('label'))
        self.assert_equal(label.attrib, {})
        self.assert_equal(label.children, ['0'])

        label = root[1]
        self.assert_equal(label.qname, self.of('label'))
        self.assert_equal(label.attrib, {})
        self.assert_equal(label.children, ['1'])

        label = root[2]
        self.assert_equal(label.qname, self.of('label'))
        self.assert_equal(label.attrib, {})
        self.assert_equal(label.children, ['2'])

        self.assert_equal(len(mc.children), 1)
        lv = mc.children[0]
        self.assert_equal(len(lv.children), 3)
        self.assert_equal(lv.children[0].index, 0)
        self.assert_equal(lv.children[1].index, 1)
        self.assert_equal(lv.children[2].index, 2)

        self.assert_is_instance(lv.children[0].model, basic._ListItemModel)
        self.assert_is_instance(lv.children[1].model, basic._ListItemModel)
        self.assert_is_instance(lv.children[2].model, basic._ListItemModel)
        lv.children[0].model.object = 10
        lv.children[1].model.object = 11
        lv.children[2].model.object = 12
        self.assert_equal(lv.children[0].model.object, 10)
        self.assert_equal(lv.children[1].model.object, 11)
        self.assert_equal(lv.children[2].model.object, 12)

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
        mc.add(basic.ListView('b', [str(i) for i in five.range(3)], populate_item))

        root = mc.render(root)
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(len(root), 9)
        root.normalize()
        self.assert_equal(root.children, ['[0][1][2]'])

    def test_property_list_view(self):
        def populate_item(li):
            li.add(basic.Label('c', li.model.object))

        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'b'})
        label = markup.Element(self.of('label'),
                               attrib={markup.AYAME_ID: 'c'})
        root.append(label)
        m = model.CompoundModel({'b': [str(i) for i in five.range(3)]})
        mc = ayame.MarkupContainer('a', m)
        mc.add(basic.PropertyListView('b', None, populate_item))

        root = mc.render(root)
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(len(root), 3)

        label = root[0]
        self.assert_equal(label.qname, self.of('label'))
        self.assert_equal(label.attrib, {})
        self.assert_equal(label.children, ['0'])

        label = root[1]
        self.assert_equal(label.qname, self.of('label'))
        self.assert_equal(label.attrib, {})
        self.assert_equal(label.children, ['1'])

        label = root[2]
        self.assert_equal(label.qname, self.of('label'))
        self.assert_equal(label.attrib, {})
        self.assert_equal(label.children, ['2'])

        self.assert_equal(len(mc.children), 1)
        lv = mc.children[0]
        self.assert_equal(len(lv.children), 3)
        self.assert_equal(lv.children[0].index, 0)
        self.assert_equal(lv.children[1].index, 1)
        self.assert_equal(lv.children[2].index, 2)

        self.assert_is_instance(lv.children[0].model, model.CompoundModel)
        self.assert_is_instance(lv.children[1].model, model.CompoundModel)
        self.assert_is_instance(lv.children[2].model, model.CompoundModel)
        lv.children[0].model.object = 10
        lv.children[1].model.object = 11
        lv.children[2].model.object = 12
        self.assert_equal(lv.children[0].model.object, 10)
        self.assert_equal(lv.children[1].model.object, 11)
        self.assert_equal(lv.children[2].model.object, 12)

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
        m = model.CompoundModel({'b': [str(i) for i in five.range(3)]})
        mc = ayame.MarkupContainer('a', m)
        mc.add(basic.PropertyListView('b', None, populate_item))

        root = mc.render(root)
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(len(root), 9)
        root.normalize()
        self.assert_equal(root.children, ['[0][1][2]'])

    def test_context_path_generator(self):
        def assert_a(path, value):
            a = markup.Element(self.html_of('a'))
            href = self.html_of('href')
            with self.application(self.new_environ(path=path)):
                am = basic.ContextPathGenerator(href, 'eggs.html')
                am.on_component(None, a)
            self.assert_equal(a.attrib, {href: value})

        assert_a('/spam', 'eggs.html')
        assert_a('/spam/', '../eggs.html')

    def test_context_image(self):
        def assert_img(path, value):
            img = markup.Element(self.html_of('img'))
            src = self.html_of('src')
            with self.application(self.new_environ(path=path)):
                c = basic.ContextImage(src, 'eggs.gif')
                img = c.render(img)
            self.assert_equal(img.attrib, {src: value})

        assert_img('/spam', 'eggs.gif')
        assert_img('/spam/', '../eggs.gif')

    def test_context_link(self):
        def assert_meta(path, value):
            meta = markup.Element(self.html_of('meta'))
            href = self.html_of('href')
            with self.application(self.new_environ(path=path)):
                c = basic.ContextLink(href, 'eggs.css')
                meta = c.render(meta)
            self.assert_equal(meta.attrib, {href: value})

        assert_meta('/spam', 'eggs.css')
        assert_meta('/spam/', '../eggs.css')
