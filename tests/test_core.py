#
# test_core
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
from ayame import _compat as five
from ayame import basic, http, markup, model
from base import AyameTestCase


class CoreTestCase(AyameTestCase):

    def test_component(self):
        with self.assert_raises_regex(ayame.ComponentError,
                                      r' id .* not set\b'):
            ayame.Component(None)

        c = ayame.Component('a')
        self.assert_equal(c.id, 'a')
        self.assert_is_none(c.model)
        self.assert_is_none(c.model_object)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r'\bmodel .* not set\b'):
            c.model_object = ''
        with self.assert_raises(ayame.AyameError):
            c.app
        with self.assert_raises(ayame.AyameError):
            c.config
        with self.assert_raises(ayame.AyameError):
            c.environ
        with self.assert_raises(ayame.AyameError):
            c.request
        with self.assert_raises(ayame.AyameError):
            c.session
        with self.assert_raises(ayame.AyameError):
            c.forward(c)
        with self.assert_raises(ayame.AyameError):
            c.redirect(c)
        with self.assert_raises(ayame.AyameError):
            c.tr('key')
        with self.assert_raises(ayame.AyameError):
            c.uri_for(c)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r' not attached .*\.Page\b'):
            c.page()
        c.add(None, True, 0, 3.14, '')
        self.assert_equal(c.behaviors, [])
        self.assert_equal(c.path(), 'a')
        self.assert_equal(c.render(''), '')
        c.visible = False
        self.assert_is_none(c.render(''))

    def test_component_with_model(self):
        with self.assert_raises_regex(ayame.ComponentError,
                                      r' not .* instance of Model\b'):
            ayame.Component('1', '')

        m = model.Model(None)
        self.assert_is_none(m.object)
        c = ayame.Component('a', m)
        self.assert_equal(c.id, 'a')
        self.assert_is(c.model, m)
        self.assert_is_none(c.model.object)
        self.assert_is_none(c.model_object)
        c.model.object = True
        self.assert_is(c.model, m)
        self.assert_equal(c.model.object, True)
        self.assert_equal(c.model_object, True)
        c.model_object = False
        self.assert_is(c.model, m)
        self.assert_equal(c.model.object, False)
        self.assert_equal(c.model_object, False)
        with self.assert_raises(ayame.AyameError):
            c.app
        with self.assert_raises(ayame.AyameError):
            c.config
        with self.assert_raises(ayame.AyameError):
            c.environ
        with self.assert_raises(ayame.AyameError):
            c.request
        with self.assert_raises(ayame.AyameError):
            c.session
        with self.assert_raises(ayame.AyameError):
            c.forward(c)
        with self.assert_raises(ayame.AyameError):
            c.redirect(c)
        with self.assert_raises(ayame.AyameError):
            c.tr('key')
        with self.assert_raises(ayame.AyameError):
            c.uri_for(c)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r' not attached .*\.Page\b'):
            c.page()
        c.add(None, True, 0, 3.14, '')
        self.assert_equal(c.behaviors, [])
        self.assert_equal(c.path(), 'a')
        self.assert_equal(c.render(''), '')
        c.visible = False
        self.assert_is_none(c.render(''))

        m = model.Model('&<>')
        self.assert_equal(m.object, '&<>')
        c = ayame.Component('a', m)
        self.assert_equal(c.id, 'a')
        self.assert_is(c.model, m)
        self.assert_equal(c.model_object, '&<>')
        self.assert_equal(c.model_object_as_string(), '&amp;&lt;&gt;')
        c.escape_model_string = False
        self.assert_equal(c.model_object, '&<>')
        self.assert_equal(c.model_object_as_string(), '&<>')

    def test_markup_container(self):
        mc = ayame.MarkupContainer('a')
        with self.assert_raises_regex(ayame.ComponentError,
                                      r' not attached .*\.Page\b'):
            mc.page()
        self.assert_equal(mc.path(), 'a')
        self.assert_equal(mc.children, [])
        self.assert_is(mc.find(None), mc)
        self.assert_is(mc.find(''), mc)
        it = mc.walk()
        self.assert_equal(list(it), [(mc, 0)])

        b1 = ayame.Component('b1')
        mc.add(b1)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r' not attached .*\.Page\b'):
            b1.page()
        self.assert_equal(b1.path(), 'a:b1')
        self.assert_equal(mc.children, [b1])
        self.assert_is(mc.find('b1'), b1)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r"'b1' .* exists\b"):
            mc.add(b1)
        b2 = ayame.MarkupContainer('b2')
        mc.add(b2)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r' not attached .*\.Page\b'):
            b2.page()
        self.assert_equal(b2.path(), 'a:b2')
        self.assert_equal(mc.children, [b1, b2])
        self.assert_is(mc.find('b2'), b2)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r"'b2' .* exists\b"):
            mc.add(b2)
        it = mc.walk()
        self.assert_equal(list(it), [(mc, 0),
                                     (b1, 1), (b2, 1)])

        c1 = ayame.Component('c1')
        b2.add(c1)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r' not attached .*\.Page\b'):
            c1.page()
        self.assert_equal(c1.path(), 'a:b2:c1')
        self.assert_equal(b2.children, [c1])
        self.assert_is(mc.find('b2:c1'), c1)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r"'c1' .* exists\b"):
            b2.add(c1)
        c2 = ayame.MarkupContainer('c2')
        b2.add(c2)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r' not attached .*\.Page\b'):
            c2.page()
        self.assert_equal(c2.path(), 'a:b2:c2')
        self.assert_equal(b2.children, [c1, c2])
        self.assert_is(mc.find('b2:c2'), c2)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r"'c2' .* exists\b"):
            b2.add(c2)
        it = mc.walk()
        self.assert_equal(list(it), [(mc, 0),
                                     (b1, 1),
                                     (b2, 1), (c1, 2), (c2, 2)])
        it = mc.walk(step=lambda component, *args: component != b2)
        self.assert_equal(list(it), [(mc, 0),
                                     (b1, 1),
                                     (b2, 1)])

        self.assert_equal(mc.render(''), '')
        mc.visible = False
        self.assert_is_none(mc.render(''))

    def test_render_no_child_component(self):
        root = markup.Element(self.of('root'))
        mc = ayame.MarkupContainer('a')
        self.assert_equal(mc.render(root), root)

    def test_render_no_ayame_id(self):
        root = markup.Element(self.of('root'))
        mc = ayame.MarkupContainer('a')
        self.assert_equal(mc.render_component(root), (None, root))

    def test_render_unknown_ayame_element(self):
        root = markup.Element(self.ayame_of('spam'))
        mc = ayame.MarkupContainer('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      r"\bunknown element 'ayame:spam'"):
            mc.render(root)

    def test_render_unknown_ayame_attribute(self):
        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'b',
                                      self.ayame_of('spam'): ''})
        mc = ayame.MarkupContainer('a')
        mc.add(ayame.Component('b'))
        with self.assert_raises_regex(ayame.RenderingError,
                                      r"\bunknown attribute 'ayame:spam'"):
            mc.render(root)

    def test_render_no_associated_component(self):
        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'c',
                                      self.of('id'): 'c'})
        mc = ayame.MarkupContainer('a')
        mc.add(ayame.Component('b'))
        with self.assert_raises_regex(ayame.ComponentError,
                                      r"\bcomponent .* 'c' .* not found\b"):
            mc.render(root)

    def test_render_replace_element_itself(self):
        class Component(ayame.Component):
            def on_render(self, element):
                return None

        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'b'})
        mc = ayame.MarkupContainer('a')
        mc.add(Component('b'))
        self.assert_equal(mc.render(root), '')

    def test_render_replace_element_itself_with_string(self):
        class Component(ayame.Component):
            def on_render(self, element):
                return ''

        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'b'})
        mc = ayame.MarkupContainer('a')
        mc.add(Component('b'))
        self.assert_equal(mc.render(root), '')

    def test_render_replace_element_itself_with_list(self):
        class Component(ayame.Component):
            def on_render(self, element):
                return ['>', '!', '<']

        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'b'})
        mc = ayame.MarkupContainer('a')
        mc.add(Component('b'))
        self.assert_equal(mc.render(root), ['>', '!', '<'])

    def test_render_remove_element(self):
        class Component(ayame.Component):
            def on_render(self, element):
                return None if int(self.id) % 2 else self.id

        root = markup.Element(self.of('root'))
        root.append('>')
        for i in five.range(1, 10):
            a = markup.Element(self.of('a'),
                               attrib={markup.AYAME_ID: str(i)})
            root.append(a)
        root.append('<')
        mc = ayame.MarkupContainer('a')
        for i in five.range(1, 10):
            mc.add(Component(str(i)))

        root = mc.render(root)
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(root.children, ['>', '2', '4', '6', '8', '<'])

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
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(root.children, ['>', '', '<'])

    def test_render_replace_element_with_list(self):
        class Component(ayame.Component):
            def on_render(self, element):
                return [self.id, str(int(self.id) + 2)]

        root = markup.Element(self.of('root'))
        root.append('>')
        for i in five.range(2, 10, 4):
            a = markup.Element(self.of('a'),
                               attrib={markup.AYAME_ID: str(i)})
            root.append(a)
        root.append('<')
        mc = ayame.MarkupContainer('a')
        for i in five.range(2, 10, 4):
            mc.add(Component(str(i)))

        root = mc.render(root)
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(root.children, ['>', '2', '4', '6', '8', '<'])

    def test_render_replace_ayame_element_itself(self):
        class MarkupContainer(ayame.MarkupContainer):
            def on_render_element(self, element):
                return None

        root = markup.Element(self.ayame_of('root'))
        mc = MarkupContainer('a')
        self.assert_equal(mc.render(root), '')

    def test_render_replace_ayame_element_itself_with_string(self):
        class MarkupContainer(ayame.MarkupContainer):
            def on_render_element(self, element):
                return ''

        root = markup.Element(self.ayame_of('root'))
        mc = MarkupContainer('a')
        self.assert_equal(mc.render(root), '')

    def test_render_replace_ayame_element_itself_with_list(self):
        class MarkupContainer(ayame.MarkupContainer):
            def on_render_element(self, element):
                return ['>', '!', '<']

        root = markup.Element(self.ayame_of('root'))
        mc = MarkupContainer('a')
        self.assert_equal(mc.render(root), ['>', '!', '<'])

    def test_render_remove_ayame_element(self):
        class MarkupContainer(ayame.MarkupContainer):
            def on_render_element(self, element):
                n = element.qname.name
                return element if n == 'root' else None if n == 'a' else n

        root = markup.Element(self.of('root'))
        root.append('>')
        for i in five.range(1, 10):
            a = markup.Element(self.ayame_of('a' if i % 2 else str(i)))
            root.append(a)
        root.append('<')
        mc = MarkupContainer('a')

        root = mc.render(root)
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(root.children, ['>', '2', '4', '6', '8', '<'])

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
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(root.children, ['>', '', '<'])

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
        for i in five.range(2, 10, 4):
            a = markup.Element(self.ayame_of(str(i)))
            root.append(a)
        root.append('<')
        mc = MarkupContainer('a')

        root = mc.render(root)
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(root.children, ['>', '2', '4', '6', '8', '<'])

    def test_render_ayame_container_no_ayame_id(self):
        root = markup.Element(self.of('root'))
        container = markup.Element(markup.AYAME_CONTAINER)
        root.append(container)
        mc = ayame.MarkupContainer('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      "'ayame:id' .* 'ayame:container'"):
            mc.render(root)

    def test_render_ayame_container_no_associated_component(self):
        root = markup.Element(self.of('root'))
        container = markup.Element(markup.AYAME_CONTAINER,
                                   attrib={markup.AYAME_ID: 'b'})
        root.append(container)
        mc = ayame.MarkupContainer('a')
        with self.assert_raises_regex(ayame.ComponentError,
                                      r"\bcomponent .* 'b' .* not found\b"):
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
        mc.add(basic.ListView('b', [str(i) for i in five.range(3)], populate_item))

        root = mc.render(root)
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(len(root), 3)

        a = root[0]
        self.assert_equal(a.qname, self.of('a'))
        self.assert_equal(a.attrib, {})
        self.assert_equal(a.children, ['0'])

        a = root[1]
        self.assert_equal(a.qname, self.of('a'))
        self.assert_equal(a.attrib, {})
        self.assert_equal(a.children, ['1'])

        a = root[2]
        self.assert_equal(a.qname, self.of('a'))
        self.assert_equal(a.attrib, {})
        self.assert_equal(a.children, ['2'])

    def test_render_ayame_enclosure_no_ayame_child(self):
        root = markup.Element(self.of('root'))
        enclosure = markup.Element(markup.AYAME_ENCLOSURE)
        root.append(enclosure)
        mc = ayame.MarkupContainer('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      "'ayame:child' .* 'ayame:enclosure'"):
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
        with self.assert_raises_regex(ayame.ComponentError,
                                      r"\bcomponent .* 'b' .* not found\b"):
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
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(len(root), 2)

        a = root[0]
        self.assert_equal(a.qname, self.of('a'))
        self.assert_equal(a.attrib, {})
        self.assert_equal(len(a), 2)

        b = a[0]
        self.assert_equal(b.qname, self.of('b'))
        self.assert_equal(b.attrib, {})
        self.assert_equal(b.children, ['spam'])

        b = a[1]
        self.assert_equal(b.qname, self.of('b'))
        self.assert_equal(b.attrib, {})
        self.assert_equal(b.children, [])

        a = root[1]
        self.assert_equal(a.qname, self.of('a'))
        self.assert_equal(a.attrib, {})
        self.assert_equal(a.children, ['eggs'])

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
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(len(root), 1)

        a = root[0]
        self.assert_equal(a.qname, self.of('a'))
        self.assert_equal(a.attrib, {})
        self.assert_equal(len(a), 1)

        b = a[0]
        self.assert_equal(b.qname, self.of('b'))
        self.assert_equal(b.attrib, {})
        self.assert_equal(b.children, [])

    def test_render_ayame_message_element_no_value_for_key(self):
        with self.application(self.new_environ()):
            message = markup.Element(markup.AYAME_MESSAGE,
                                     attrib={markup.AYAME_KEY: 'b'})
            mc = ayame.MarkupContainer('a')
            with self.assert_raises_regex(ayame.RenderingError,
                                          " value .* ayame:message .* 'b'"):
                mc.render(message)

    def test_render_ayame_message_element(self):
        with self.application(self.new_environ(accept='en')):
            p = BeansPage()
            status, headers, content = p()
        html = self.format(BeansPage, message='Hello World!')
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

    def test_render_ayame_message_element_ja(self):
        with self.application(self.new_environ(accept='ja, en')):
            p = BeansPage()
            status, headers, content = p()
        html = self.format(BeansPage, message=u'\u3053\u3093\u306b\u3061\u306f\u4e16\u754c')
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

    def test_render_ayame_message_attribute_invalid_value(self):
        with self.application(self.new_environ()):
            root = markup.Element(self.of('root'),
                                  attrib={markup.AYAME_ID: 'b',
                                          markup.AYAME_MESSAGE: 'id'})
            mc = ayame.MarkupContainer('a')
            mc.add(ayame.Component('b'))
            with self.assert_raises_regex(ayame.RenderingError,
                                          r'\binvalid .* ayame:message '):
                mc.render(root)

    def test_render_ayame_message_attribute(self):
        with self.application(self.new_environ(accept='en')):
            p = BaconPage()
            status, headers, content = p()
        html = self.format(BaconPage, message='Submit')
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

    def test_render_ayame_message_attribute_ja(self):
        with self.application(self.new_environ(accept='ja, en')):
            p = BaconPage()
            status, headers, content = p()
        html = self.format(BaconPage, message=u'\u9001\u4fe1')
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

    def test_render_ayame_head_unknown_root(self):
        root = markup.Element(self.of('root'))
        a = markup.Element(self.of('a'),
                           attrib={markup.AYAME_ID: 'b'})
        root.append(a)
        mc = ayame.MarkupContainer('a')
        mc.add(AyameHeadContainer('b'))
        with self.assert_raises_regex(ayame.RenderingError,
                                      r"\broot element is not 'html'"):
            mc.find_head(root)

    def test_render_ayame_head_no_head(self):
        root = markup.Element(markup.HTML)
        a = markup.Element(self.of('a'),
                           attrib={markup.AYAME_ID: 'b'})
        root.append(a)
        mc = ayame.MarkupContainer('a')
        mc.add(AyameHeadContainer('b'))
        with self.assert_raises_regex(ayame.RenderingError,
                                      r"'head' .* not found\b"):
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
        self.assert_equal(root.qname, markup.HTML)
        self.assert_equal(root.attrib, {})
        self.assert_equal(len(root), 2)

        head = root[0]
        self.assert_equal(head.qname, markup.HEAD)
        self.assert_equal(head.attrib, {})
        self.assert_equal(head.type, markup.Element.OPEN)
        self.assert_equal(len(head), 1)

        h = head[0]
        self.assert_equal(h.qname, self.of('h'))
        self.assert_equal(h.attrib, {})
        self.assert_equal(h.children, [])

        a = root[1]
        self.assert_equal(a.qname, self.of('a'))
        self.assert_equal(a.attrib, {})
        self.assert_equal(a.children, [])

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
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(len(root), 1)

        a = root.children[0]
        self.assert_equal(a.qname, self.of('a'))
        self.assert_equal(a.attrib, {})
        self.assert_equal(len(a), 1)

        b = a.children[0]
        self.assert_equal(b.qname, self.of('b'))
        self.assert_equal(b.attrib, {})
        self.assert_equal(len(b), 1)

        c = b.children[0]
        self.assert_equal(c.qname, self.of('c'))
        self.assert_equal(c.attrib, {})
        self.assert_equal(c.children, [])

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
        self.assert_equal(m.xml_decl, {'version': '1.0'})
        self.assert_equal(m.lang, 'xhtml1')
        self.assert_equal(m.doctype, markup.XHTML1_STRICT)
        self.assert_true(m.root)

        html = m.root
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
                                        self.html_of('content'): 'Eggs'})
        self.assert_equal(meta.type, markup.Element.EMPTY)
        self.assert_equal(meta.ns, {})
        self.assert_equal(meta.children, [])

        meta = head[9]
        self.assert_equal(meta.qname, self.html_of('meta'))
        self.assert_equal(meta.attrib, {self.html_of('name'): 'class',
                                        self.html_of('content'): 'Ham'})
        self.assert_equal(meta.type, markup.Element.EMPTY)
        self.assert_equal(meta.ns, {})
        self.assert_equal(meta.children, [])

        body = html[3]
        self.assert_equal(body.qname, self.html_of('body'))
        self.assert_equal(body.attrib, {})
        self.assert_equal(body.type, markup.Element.OPEN)
        self.assert_equal(body.ns, {})
        self.assert_equal(len(body), 13)
        self.assert_ws(body, 0)
        self.assert_ws(body, 2)
        self.assert_ws(body, 3)
        self.assert_ws(body, 5)
        self.assert_ws(body, 6)
        self.assert_ws(body, 8)
        self.assert_ws(body, 9)
        self.assert_ws(body, 10)
        self.assert_ws(body, 12)

        p = body[1]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['before ayame:child (Spam)'])

        p = body[4]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['inside ayame:extend (Eggs)'])

        p = body[7]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['inside ayame:extend (Ham)'])

        p = body[11]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['after ayame:child (Spam)'])

    def test_markup_inheritance_empty_submarkup(self):
        class Spam(ayame.MarkupContainer):
            pass

        class Sausage(Spam):
            pass

        with self.application():
            mc = Sausage('a')
            m = mc.load_markup()
        self.assert_equal(m.xml_decl, {'version': '1.0'})
        self.assert_equal(m.lang, 'xhtml1')
        self.assert_equal(m.doctype, markup.XHTML1_STRICT)
        self.assert_true(m.root)

        html = m.root
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
                                        self.html_of('content'): 'Sausage'})
        self.assert_equal(meta.type, markup.Element.EMPTY)
        self.assert_equal(meta.ns, {})
        self.assert_equal(meta.children, [])

        body = html[3]
        self.assert_equal(body.qname, self.html_of('body'))
        self.assert_equal(body.attrib, {})
        self.assert_equal(body.type, markup.Element.OPEN)
        self.assert_equal(body.ns, {})
        self.assert_equal(len(body), 6)
        self.assert_ws(body, 0)
        self.assert_ws(body, 2)
        self.assert_ws(body, 3)
        self.assert_ws(body, 5)

        p = body[1]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['before ayame:child (Spam)'])

        p = body[4]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['after ayame:child (Spam)'])

    def test_markup_inheritance_merge_ayame_head(self):
        class Bacon(ayame.MarkupContainer):
            pass

        class Sausage(Bacon):
            pass

        with self.application():
            mc = Sausage('a')
            m = mc.load_markup()
        self.assert_equal(m.xml_decl, {'version': '1.0'})
        self.assert_equal(m.lang, 'xhtml1')
        self.assert_equal(m.doctype, markup.XHTML1_STRICT)
        self.assert_true(m.root)

        html = m.root
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

        ayame_head = html[1]
        self.assert_equal(ayame_head.qname, self.ayame_of('head'))
        self.assert_equal(ayame_head.attrib, {})
        self.assert_equal(ayame_head.type, markup.Element.OPEN)
        self.assert_equal(ayame_head.ns, {})
        self.assert_equal(len(ayame_head), 8)
        self.assert_ws(ayame_head, 0)
        self.assert_ws(ayame_head, 2)
        self.assert_ws(ayame_head, 4)
        self.assert_ws(ayame_head, 5)
        self.assert_ws(ayame_head, 7)

        title = ayame_head[1]
        self.assert_equal(title.qname, self.html_of('title'))
        self.assert_equal(title.attrib, {})
        self.assert_equal(title.type, markup.Element.OPEN)
        self.assert_equal(title.ns, {})
        self.assert_equal(title.children, ['Bacon'])

        meta = ayame_head[3]
        self.assert_equal(meta.qname, self.html_of('meta'))
        self.assert_equal(meta.attrib, {self.html_of('name'): 'class',
                                        self.html_of('content'): 'Bacon'})
        self.assert_equal(meta.type, markup.Element.EMPTY)
        self.assert_equal(meta.ns, {})
        self.assert_equal(meta.children, [])

        meta = ayame_head[6]
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
        self.assert_equal(len(body), 6)
        self.assert_ws(body, 0)
        self.assert_ws(body, 2)
        self.assert_ws(body, 3)
        self.assert_ws(body, 5)

        p = body[1]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['before ayame:child (Bacon)'])

        p = body[4]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['after ayame:child (Bacon)'])

    def test_markup_inheritance_no_superclass(self):
        class Sausage(ayame.MarkupContainer, object):
            pass

        with self.application():
            mc = Sausage('a')
            with self.assert_raises_regex(ayame.AyameError,
                                          '^superclass .* not found$'):
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
            with self.assert_raises_regex(ayame.AyameError,
                                          ' multiple inheritance$'):
                mc.load_markup()

    def test_markup_inheritance_no_ayame_child(self):
        class Toast(ayame.MarkupContainer):
            pass

        class Sausage(Toast):
            pass

        with self.application():
            mc = Sausage('a')
            with self.assert_raises_regex(ayame.RenderingError,
                                          r"'ayame:child' .* not found\b"):
                mc.load_markup()

    def test_markup_inheritance_no_head(self):
        class Beans(ayame.MarkupContainer):
            pass

        class Sausage(Beans):
            pass

        with self.application():
            mc = Sausage('a')
            with self.assert_raises_regex(ayame.RenderingError,
                                          r"'head' .* not found\b"):
                mc.load_markup()

    def test_markup_inheritance_ayame_child_as_root(self):
        class Tomato(ayame.MarkupContainer):
            pass

        class Sausage(Tomato):
            pass

        with self.application():
            mc = Sausage('a')
            with self.assert_raises_regex(ayame.RenderingError,
                                          r"'ayame:child' .* root element\b"):
                mc.load_markup()

    def test_markup_inheritance_empty_markup(self):
        class Lobster(ayame.MarkupContainer):
            pass

        class Sausage(Lobster):
            pass

        with self.application():
            mc = Sausage('a')
            m = mc.load_markup()
        self.assert_equal(m.xml_decl, {})
        self.assert_equal(m.lang, 'xhtml1')
        self.assert_is_none(m.doctype)
        self.assert_is_none(m.root)

        class Lobster(ayame.Page):
            pass

        with self.application(self.new_environ()):
            p = Lobster()
            status, headers, content = p()
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', '0')])
        self.assert_equal(content, [b''])

    def test_markup_inheritance_duplicate_ayame_elements(self):
        class Shallots(ayame.MarkupContainer):
            pass

        class Aubergine(Shallots):
            pass

        with self.application():
            mc = Aubergine('a')
            m = mc.load_markup()
        self.assert_equal(m.xml_decl, {'version': '1.0'})
        self.assert_equal(m.lang, 'xhtml1')
        self.assert_equal(m.doctype, markup.XHTML1_STRICT)
        self.assert_true(m.root)

        html = m.root
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
        self.assert_equal(title.children, ['Shallots'])

        meta = head[3]
        self.assert_equal(meta.qname, self.html_of('meta'))
        self.assert_equal(meta.attrib, {self.html_of('name'): 'class',
                                        self.html_of('content'): 'Shallots'})
        self.assert_equal(meta.type, markup.Element.EMPTY)
        self.assert_equal(meta.ns, {})
        self.assert_equal(meta.children, [])

        meta = head[6]
        self.assert_equal(meta.qname, self.html_of('meta'))
        self.assert_equal(meta.attrib, {self.html_of('name'): 'class',
                                        self.html_of('content'): 'Aubergine'})
        self.assert_equal(meta.type, markup.Element.EMPTY)
        self.assert_equal(meta.ns, {})
        self.assert_equal(meta.children, [])

        body = html[3]
        self.assert_equal(body.qname, self.html_of('body'))
        self.assert_equal(body.attrib, {})
        self.assert_equal(body.type, markup.Element.OPEN)
        self.assert_equal(body.ns, {})
        self.assert_equal(len(body), 8)
        self.assert_ws(body, 0)
        self.assert_ws(body, 2)
        self.assert_ws(body, 3)
        self.assert_ws(body, 5)
        self.assert_ws(body, 7)

        p = body[1]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['before ayame:child (Shallots)'])

        ayame_child = body[4]
        self.assert_equal(ayame_child.qname, self.ayame_of('child'))
        self.assert_equal(ayame_child.attrib, {})
        self.assert_equal(ayame_child.type, markup.Element.EMPTY)
        self.assert_equal(ayame_child.ns, {})
        self.assert_equal(ayame_child.children, [])

        p = body[6]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(p.children, ['after ayame:child (Shallots)'])

    def test_page(self):
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
                super(SpamPage, self).__init__()
                self.add(basic.Label('message', 'Hello World!'))
                self.headers['Content-Type'] = 'text/plain'

        with self.application(self.new_environ()):
            p = SpamPage()
            status, headers, content = p()
        html = self.format(SpamPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        self.assert_equal(p.page(), p)
        self.assert_equal(p.find('message').page(), p)
        self.assert_equal(p.path(), '')
        self.assert_equal(p.find('message').path(), 'message')

    def test_behavior(self):
        b = ayame.Behavior()
        with self.assert_raises(ayame.AyameError):
            b.app
        with self.assert_raises(ayame.AyameError):
            b.config
        with self.assert_raises(ayame.AyameError):
            b.environ
        with self.assert_raises(ayame.AyameError):
            b.request
        with self.assert_raises(ayame.AyameError):
            b.session
        with self.assert_raises(ayame.AyameError):
            b.forward(b)
        with self.assert_raises(ayame.AyameError):
            b.redirect(b)
        with self.assert_raises(ayame.AyameError):
            b.uri_for(b)

    def test_behavior_render(self):
        class Behavior(ayame.Behavior):
            def on_before_render(self, component):
                super(Behavior, self).on_before_render(component)
                component.model_object.append('before-render')

            def on_component(self, component, element):
                super(Behavior, self).on_component(component, element)
                component.model_object.append('component')

            def on_after_render(self, component):
                super(Behavior, self).on_after_render(component)
                component.model_object.append('after-render')

        c = ayame.Component('a', model.Model([]))
        c.add(Behavior())
        self.assert_equal(len(c.behaviors), 1)
        self.assert_equal(c.behaviors[0].component, c)

        self.assert_is_none(c.render(None))
        self.assert_equal(c.model_object,
                          ['before-render', 'component', 'after-render'])

        mc = ayame.MarkupContainer('a', model.Model([]))
        mc.add(Behavior())
        self.assert_equal(len(c.behaviors), 1)
        self.assert_equal(mc.behaviors[0].component, mc)

        self.assert_is_none(mc.render(None))
        self.assert_equal(mc.model_object,
                          ['before-render', 'component', 'after-render'])

    def test_attribute_modifier_on_component(self):
        root = markup.Element(self.of('root'),
                              attrib={self.of('a'): ''})
        c = ayame.Component('a')
        c.add(ayame.AttributeModifier('a', model.Model(None)))
        c.add(ayame.AttributeModifier(self.of('b'),
                                      model.Model(None)))
        c.add(ayame.AttributeModifier('c', model.Model('')))
        self.assert_equal(len(c.behaviors), 3)
        self.assert_equal(c.behaviors[0].component, c)
        self.assert_equal(c.behaviors[1].component, c)
        self.assert_equal(c.behaviors[2].component, c)

        root = c.render(root)
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {self.of('c'): ''})
        self.assert_equal(root.children, [])

    def test_attribute_modifier_on_markup_container(self):
        root = markup.Element(self.of('root'),
                              attrib={self.of('a'): ''})
        mc = ayame.MarkupContainer('a')
        mc.add(ayame.AttributeModifier('a', model.Model(None)))
        mc.add(ayame.AttributeModifier(self.of('b'),
                                       model.Model(None)))
        mc.add(ayame.AttributeModifier('c', model.Model('')))
        self.assert_equal(len(mc.behaviors), 3)
        self.assert_equal(mc.behaviors[0].component, mc)
        self.assert_equal(mc.behaviors[1].component, mc)
        self.assert_equal(mc.behaviors[2].component, mc)

        root = mc.render(root)
        self.assert_equal(root.qname, self.of('root'))
        self.assert_equal(root.attrib, {self.of('c'): ''})
        self.assert_equal(root.children, [])

    def test_fire_get(self):
        query = '{path}=clay1'
        with self.application(self.new_environ(query=query)):
            p = EggsPage()
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        self.assert_equal(p.model_object, {'clay1': 1,
                                           'clay2': 0})

    def test_fire_get_duplicate_ayame_path(self):
        query = ('{path}=clay1&'
                 '{path}=obstacle:clay2')
        with self.application(self.new_environ(query=query)):
            p = EggsPage()
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        self.assert_equal(p.model_object, {'clay1': 1,
                                           'clay2': 0})

    def test_fire_get_nonexistent_path(self):
        query = '{path}=clay2'
        with self.application(self.new_environ(query=query)):
            p = EggsPage()
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        self.assert_equal(p.model_object, {'clay1': 0,
                                           'clay2': 0})

    def test_fire_get_invisible_component(self):
        query = '{path}=clay1'
        with self.application(self.new_environ(query=query)):
            p = EggsPage()
            p.find('clay1').visible = False
            status, headers, content = p()
        html = self.format(EggsPage, clay1=False)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        self.assert_equal(p.model_object, {'clay1': 0,
                                           'clay2': 0})

    def test_fire_post(self):
        data = self.form_data(('{path}', 'obstacle:clay2'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        self.assert_equal(p.model_object, {'clay1': 0,
                                           'clay2': 1})

    def test_fire_post_duplicate_ayame_path(self):
        data = self.form_data(('{path}', 'obstacle:clay2'),
                              ('{path}', 'clay1'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        self.assert_equal(p.model_object, {'clay1': 0,
                                           'clay2': 1})

    def test_fire_post_nonexistent_path(self):
        data = self.form_data(('{path}', 'clay2'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        self.assert_equal(p.model_object, {'clay1': 0,
                                           'clay2': 0})

    def test_fire_post_invisible_component(self):
        data = self.form_data(('{path}', 'clay1'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            p.find('clay1').visible = False
            status, headers, content = p()
        html = self.format(EggsPage, clay1=False)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        self.assert_equal(p.model_object, {'clay1': 0,
                                           'clay2': 0})

    def test_fire_component(self):
        query = '{path}=c'
        with self.application(self.new_environ(query=query)):
            c = Component('c')
            c.fire()
        self.assert_equal(c.model_object, 1)

    def test_fire_component_uknown_path(self):
        query = '{path}=g'
        with self.application(self.new_environ(query=query)):
            c = Component('c')
            c.fire()
        self.assert_equal(c.model_object, 0)

    def test_fire_component_invisible(self):
        query = '{path}=c'
        with self.application(self.new_environ(query=query)):
            c = Component('c')
            c.visible = False
            c.fire()
        self.assert_equal(c.model_object, 0)

    def test_nested(self):
        regex = ' not .* subclass of MarkupContainer$'

        with self.assert_raises_regex(ayame.AyameError,
                                      regex):
            class C(object):
                @ayame.nested
                class C(object):
                    pass

        with self.assert_raises_regex(ayame.AyameError,
                                      regex):
            class C(object):
                @ayame.nested
                def f(self):
                    pass

        class C(object):
            @ayame.nested
            class MarkupContainer(ayame.MarkupContainer):
                pass

        self.assert_is_instance(C.MarkupContainer('a'), ayame.MarkupContainer)

    def test_nested_class_markup(self):
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

        mt = markup.MarkupType('.htm', 'text/html', ())
        self.assert_equal(ToastPage.markup_type, mt)
        mt = markup.MarkupType('.html', 'text/html', (ToastPage,))
        self.assert_equal(ToastPage.NestedPage.markup_type, mt)

        with self.application(self.new_environ()):
            p = ToastPage()
            status, headers, content = p()
        html = self.format(ToastPage, name='ToastPage')
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        with self.application(self.new_environ()):
            p = ToastPage.NestedPage()
            status, headers, content = p()
        html = self.format(ToastPage, name='ToastPage.NestedPage')
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

    def test_element(self):
        class Lobster(ayame.MarkupContainer):
            pass

        with self.application():
            mc = Lobster('a')
            mc.add(ayame.MarkupContainer('b'))
            mc.has_markup = False
            self.assert_is_none(mc.find('b').element())
            mc.has_markup = True
            self.assert_is_none(mc.find('b').element())

        class Toast(ayame.MarkupContainer):
            pass

        with self.application():
            mc = Toast('a')
            mc.add(ayame.MarkupContainer('b'))
            mc.has_markup = True
            mc.find('b').element()

        with self.application():
            p = EggsPage()
            self.assert_is_instance(p.find('clay1').element(), markup.Element)
            self.assert_is_instance(p.find('obstacle:clay2').element(), markup.Element)

    def test_cache(self):
        config = self.app.config.copy()
        try:
            self.app.config['ayame.resource.loader'] = self.new_resource_loader()
            self.app.config['ayame.markup.cache'] = cache = config['ayame.markup.cache'].copy()

            with self.application(self.new_environ()):
                p = EggsPage()
                p()
            self.assert_equal(len(cache), 1)

            with self.application(self.new_environ()):
                p = EggsPage()
                with self.assert_raises(OSError):
                    p()
            self.assert_equal(len(cache), 0)

            with self.application(self.new_environ()):
                p = EggsPage()
                with self.assert_raises(ayame.ResourceError):
                    p()
            self.assert_equal(len(cache), 0)
        finally:
            self.app.config = config


class Component(ayame.Component):

    def __init__(self, id):
        super(Component, self).__init__(id, model.Model(0))

    def on_fire(self):
        self.model_object += 1


class AyameHeadContainer(ayame.MarkupContainer):

    def __init__(self, id, elem=None):
        super(AyameHeadContainer, self).__init__(id)
        self._elem = elem

    def on_render(self, element):
        for par in self.iter_parent():
            pass
        par.head.children.append(self._elem)
        return element


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
        'clay1': lambda v=True: '<p>clay1</p>' if v else ''
    }

    def __init__(self):
        super(EggsPage, self).__init__()
        self.model = model.CompoundModel({
            'clay1': 0,
            'clay2': 0
        })
        self.add(self.Clay('clay1'))
        self.add(ayame.MarkupContainer('obstacle'))
        self.find('obstacle').add(self.Clay('clay2'))

    class Clay(ayame.Component):

        def on_fire(self):
            self.model_object += 1


class BeansPage(ayame.Page):

    html_t = u"""\
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

    html_t = u"""\
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
