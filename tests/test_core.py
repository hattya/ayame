#
# test_core
#
#   Copyright (c) 2011-2013 Akinori Hattori <hattya@gmail.com>
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
from ayame import basic, http, markup, model
from base import AyameTestCase


class CoreTestCase(AyameTestCase):

    def setup(self):
        super(CoreTestCase, self).setup()
        self.boundary = 'ayame.core'

    def test_component(self):
        with self.assert_raises_regex(ayame.ComponentError,
                                      r'\bid .* not set\b'):
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
                                      r" is not attached .*\.Page\b"):
            c.page()
        self.assert_equal(c.path(), 'a')
        self.assert_equal(c.render(''), '')

    def test_component_with_model(self):
        with self.assert_raises_regex(ayame.ComponentError,
                                      r'\bis not an instance of Model\b'):
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
                                      r" is not attached .*\.Page\b"):
            c.page()
        self.assert_equal(c.path(), 'a')
        self.assert_equal(c.render(''), '')

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
                                      r" is not attached .*\.Page\b"):
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
                                      r" is not attached .*\.Page\b"):
            b1.page()
        self.assert_equal(b1.path(), 'a:b1')
        self.assert_equal(mc.children, [b1])
        self.assert_is(mc.find('b1'), b1)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r"'b1' already exists\b"):
            mc.add(b1)
        b2 = ayame.MarkupContainer('b2')
        mc.add(b2)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r" is not attached .*\.Page\b"):
            b2.page()
        self.assert_equal(b2.path(), 'a:b2')
        self.assert_equal(mc.children, [b1, b2])
        self.assert_is(mc.find('b2'), b2)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r"'b2' already exists\b"):
            mc.add(b2)
        it = mc.walk()
        self.assert_equal(list(it), [(mc, 0),
                                     (b1, 1), (b2, 1)])

        c1 = ayame.Component('c1')
        b2.add(c1)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r" is not attached .*\.Page\b"):
            c1.page()
        self.assert_equal(c1.path(), 'a:b2:c1')
        self.assert_equal(b2.children, [c1])
        self.assert_is(mc.find('b2:c1'), c1)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r"'c1' already exists\b"):
            b2.add(c1)
        c2 = ayame.MarkupContainer('c2')
        b2.add(c2)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r" is not attached .*\.Page\b"):
            c2.page()
        self.assert_equal(c2.path(), 'a:b2:c2')
        self.assert_equal(b2.children, [c1, c2])
        self.assert_is(mc.find('b2:c2'), c2)
        with self.assert_raises_regex(ayame.ComponentError,
                                      r"'c2' already exists\b"):
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

    def test_render_no_child_component(self):
        root = markup.Element(markup.QName('', 'root'))
        mc = ayame.MarkupContainer('a')
        self.assert_equal(mc.render(root), root)

    def test_render_no_ayame_id(self):
        root = markup.Element(markup.QName('', 'root'))
        mc = ayame.MarkupContainer('a')
        self.assert_equal(mc.render_component(root), (None, root))

    def test_render_unknown_ayame_element(self):
        root = markup.Element(self.ayame_of('spam'))
        mc = ayame.MarkupContainer('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      r"\bunknown element 'ayame:spam'"):
            mc.render(root)

    def test_render_unknown_element(self):
        root = markup.Element(markup.QName('', 'root'))
        mc = ayame.MarkupContainer('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      r"\bunknown element '{}root'"):
            mc.render_ayame_element(root)

    def test_render_unknown_ayame_attribute(self):
        root = markup.Element(markup.QName('', 'root'),
                              attrib={markup.AYAME_ID: 'b',
                                      self.ayame_of('spam'): ''})
        mc = ayame.MarkupContainer('a')
        mc.add(ayame.Component('b'))
        with self.assert_raises_regex(ayame.RenderingError,
                                      r"\bunknown attribute 'ayame:spam'"):
            mc.render(root)

    def test_render_no_associated_component(self):
        root = markup.Element(markup.QName('', 'root'),
                              attrib={markup.AYAME_ID: 'c',
                                      markup.QName('', 'id'): 'c'})
        mc = ayame.MarkupContainer('a')
        mc.add(ayame.Component('b'))
        with self.assert_raises_regex(ayame.ComponentError,
                                      r"\bcomponent .* 'c' .* not found\b"):
            mc.render(root)

    def test_render_replace_root_element(self):
        class Component(ayame.Component):
            def on_render(self, element):
                return None

        root = markup.Element(markup.QName('', 'root'),
                              attrib={markup.AYAME_ID: 'b'})
        mc = ayame.MarkupContainer('a')
        mc.add(Component('b'))
        self.assert_equal(mc.render(root), '')

    def test_render_remove_element(self):
        class Component(ayame.Component):
            def on_render(self, element):
                return None

        root = markup.Element(markup.QName('', 'root'))
        root.append('>')
        a = markup.Element(markup.QName('', 'a'),
                           attrib={markup.AYAME_ID: 'b'})
        root.append(a)
        root.append('<')
        mc = ayame.MarkupContainer('a')
        mc.add(Component('b'))

        root = mc.render(root)
        self.assert_equal(root.qname, markup.QName('', 'root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(root.children, ['>', '<'])

    def test_render_replace_element_by_string(self):
        class Component(ayame.Component):
            def on_render(self, element):
                return ''

        root = markup.Element(markup.QName('', 'root'))
        root.append('>')
        a = markup.Element(markup.QName('', 'a'),
                           attrib={markup.AYAME_ID: 'b'})
        root.append(a)
        root.append('<')
        mc = ayame.MarkupContainer('a')
        mc.add(Component('b'))

        root = mc.render(root)
        self.assert_equal(root.qname, markup.QName('', 'root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(root.children, ['>', '<'])

    def test_render_replace_element_by_list(self):
        class Component(ayame.Component):
            def on_render(self, element):
                return ['>>', '!', '<<']

        root = markup.Element(markup.QName('', 'root'))
        root.append('>')
        a = markup.Element(markup.QName('', 'a'),
                           attrib={markup.AYAME_ID: 'b'})
        root.append(a)
        root.append('<')
        mc = ayame.MarkupContainer('a')
        mc.add(Component('b'))

        root = mc.render(root)
        self.assert_equal(root.qname, markup.QName('', 'root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(root.children, ['>', '>>', '!', '<<', '<'])

    def test_render_ayame_container_no_ayame_id(self):
        root = markup.Element(markup.QName('', 'root'))
        container = markup.Element(markup.AYAME_CONTAINER)
        root.append(container)
        mc = ayame.MarkupContainer('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      r"'ayame:id' .* 'ayame:container'"):
            mc.render(root)

    def test_render_ayame_container_no_associated_component(self):
        root = markup.Element(markup.QName('', 'root'))
        container = markup.Element(markup.AYAME_CONTAINER,
                                   attrib={markup.AYAME_ID: 'b'})
        root.append(container)
        mc = ayame.MarkupContainer('a')
        with self.assert_raises_regex(ayame.ComponentError,
                                      r"\bcomponent .* 'b' .* not found\b"):
            mc.render(root)

    def test_render_ayame_container(self):
        root = markup.Element(markup.QName('', 'root'))
        container = markup.Element(markup.AYAME_CONTAINER,
                                   attrib={markup.AYAME_ID: 'b'})
        root.append(container)
        a = markup.Element(markup.QName('', 'a'),
                           attrib={markup.AYAME_ID: 'c'})
        container.append(a)
        mc = ayame.MarkupContainer('a')
        def populate_item(li):
            li.add(basic.Label('c', li.model_object))
        mc.add(basic.ListView('b', [str(i) for i in xrange(3)], populate_item))

        root = mc.render(root)
        self.assert_equal(root.qname, markup.QName('', 'root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(len(root), 3)

        a = root[0]
        self.assert_equal(a.qname, markup.QName('', 'a'))
        self.assert_equal(a.attrib, {})
        self.assert_equal(a.children, ['0'])

        a = root[1]
        self.assert_equal(a.qname, markup.QName('', 'a'))
        self.assert_equal(a.attrib, {})
        self.assert_equal(a.children, ['1'])

        a = root[2]
        self.assert_equal(a.qname, markup.QName('', 'a'))
        self.assert_equal(a.attrib, {})
        self.assert_equal(a.children, ['2'])

    def test_render_ayame_enclosure_no_ayame_child(self):
        root = markup.Element(markup.QName('', 'root'))
        enclosure = markup.Element(markup.AYAME_ENCLOSURE)
        root.append(enclosure)
        mc = ayame.MarkupContainer('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      r"'ayame:child' .* 'ayame:enclosure'"):
            mc.render(root)

    def test_render_ayame_enclosure_no_associated_component(self):
        root = markup.Element(markup.QName('', 'root'))
        enclosure = markup.Element(markup.AYAME_ENCLOSURE,
                                   attrib={markup.AYAME_CHILD: 'b'})
        root.append(enclosure)
        a = markup.Element(markup.QName('', 'a'),
                           attrib={markup.AYAME_ID: 'b'})
        enclosure.append(a)
        mc = ayame.MarkupContainer('a')
        with self.assert_raises_regex(ayame.ComponentError,
                                      r"\bcomponent .* 'b' .* not found\b"):
            mc.render(root)

    def test_render_ayame_enclosure_with_visible_component(self):
        root = markup.Element(markup.QName('', 'root'))
        a = markup.Element(markup.QName('', 'a'))
        root.append(a)
        enclosure = markup.Element(markup.AYAME_ENCLOSURE,
                                   attrib={markup.AYAME_CHILD: 'b1'})
        a.append(enclosure)
        b = markup.Element(markup.QName('', 'b'),
                           attrib={markup.AYAME_ID: 'b1'})
        enclosure.append(b)
        b = markup.Element(markup.QName('', 'b'))
        a.append(b)
        a = markup.Element(markup.QName('', 'a'),
                           attrib={markup.AYAME_ID: 'b2'})
        root.append(a)
        mc = ayame.MarkupContainer('a')
        mc.add(basic.Label('b1', 'spam'))
        mc.add(basic.Label('b2', 'eggs'))

        root = mc.render(root)
        self.assert_equal(root.qname, markup.QName('', 'root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(len(root), 2)

        a = root[0]
        self.assert_equal(a.qname, markup.QName('', 'a'))
        self.assert_equal(a.attrib, {})
        self.assert_equal(len(a), 2)

        b = a[0]
        self.assert_equal(b.qname, markup.QName('', 'b'))
        self.assert_equal(b.attrib, {})
        self.assert_equal(b.children, ['spam'])

        b = a[1]
        self.assert_equal(b.qname, markup.QName('', 'b'))
        self.assert_equal(b.attrib, {})
        self.assert_equal(b.children, [])

        a = root[1]
        self.assert_equal(a.qname, markup.QName('', 'a'))
        self.assert_equal(a.attrib, {})
        self.assert_equal(a.children, ['eggs'])

    def test_render_ayame_enclosure_with_invisible_component(self):
        root = markup.Element(markup.QName('', 'root'))
        a = markup.Element(markup.QName('', 'a'))
        root.append(a)
        enclosure = markup.Element(markup.AYAME_ENCLOSURE,
                                   attrib={markup.AYAME_CHILD: 'b1'})
        a.append(enclosure)
        b = markup.Element(markup.QName('', 'b'),
                           attrib={markup.AYAME_ID: 'b1'})
        enclosure.append(b)
        b = markup.Element(markup.QName('', 'b'))
        a.append(b)
        a = markup.Element(markup.QName('', 'a'),
                           attrib={markup.AYAME_ID: 'b2'})
        root.append(a)
        mc = ayame.MarkupContainer('a')
        mc.add(basic.Label('b1', 'spam'))
        mc.add(basic.Label('b2', 'eggs'))
        mc.find('b1').visible = False
        mc.find('b2').visible = False

        root = mc.render(root)
        self.assert_equal(root.qname, markup.QName('', 'root'))
        self.assert_equal(root.attrib, {})
        self.assert_equal(len(root), 1)

        a = root[0]
        self.assert_equal(a.qname, markup.QName('', 'a'))
        self.assert_equal(a.attrib, {})
        self.assert_equal(len(a), 1)

        b = a[0]
        self.assert_equal(b.qname, markup.QName('', 'b'))
        self.assert_equal(b.attrib, {})
        self.assert_equal(b.children, [])

    def test_render_ayame_message_element_no_value_for_key(self):
        with self.application(self.new_environ()):
            message = markup.Element(markup.AYAME_MESSAGE,
                                     attrib={markup.AYAME_KEY: 'b'})
            mc = ayame.MarkupContainer('a')
            with self.assert_raises_regex(ayame.RenderingError,
                                          r"\bvalue .* ayame:message .* 'b'"):
                mc.render(message)

    def test_render_ayame_message_element(self):
        with self.application(self.new_environ(accept='en')):
            p = BeansPage()
            status, headers, content = p.render()
        html = self.format(BeansPage, message='Hello World!')
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

    def test_render_ayame_message_element_ja(self):
        with self.application(self.new_environ(accept='ja, en')):
            p = BeansPage()
            status, headers, content = p.render()
        html = self.format(
            BeansPage, message=u'\u3053\u3093\u306b\u3061\u306f\u4e16\u754c')
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

    def test_render_ayame_message_attribute_invalid_value(self):
        with self.application(self.new_environ()):
            root = markup.Element(markup.QName('', 'root'),
                                  attrib={markup.AYAME_ID: 'b',
                                          markup.AYAME_MESSAGE: 'id'})
            mc = ayame.MarkupContainer('a')
            mc.add(ayame.Component('b'))
            with self.assert_raises_regex(ayame.RenderingError,
                                          r"\binvalid .* ayame:message\b"):
                mc.render(root)

    def test_render_ayame_message_attribute(self):
        with self.application(self.new_environ(accept='en')):
            p = BaconPage()
            status, headers, content = p.render()
        html = self.format(BaconPage, message='Submit')
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

    def test_render_ayame_message_attribute_ja(self):
        with self.application(self.new_environ(accept='ja, en')):
            p = BaconPage()
            status, headers, content = p.render()
        html = self.format(BaconPage, message=u'\u9001\u4fe1')
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

    def test_render_ayame_head_unknown_root(self):
        root = markup.Element(markup.QName('', 'root'))
        a = markup.Element(markup.QName('', 'a'),
                           attrib={markup.AYAME_ID: 'b'})
        root.append(a)
        mc = ayame.MarkupContainer('a')
        mc.add(AyameHeadContainer('b'))
        with self.assert_raises_regex(ayame.RenderingError,
                                      r"\broot element is not 'html'"):
            mc.render(root)

    def test_render_ayame_head_no_head(self):
        root = markup.Element(markup.HTML)
        a = markup.Element(markup.QName('', 'a'),
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
        a = markup.Element(markup.QName('', 'a'),
                           attrib={markup.AYAME_ID: 'b'})
        root.append(a)
        h = markup.Element(markup.QName('', 'h'))
        mc = ayame.MarkupContainer('a')
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
        self.assert_equal(h.qname, markup.QName('', 'h'))
        self.assert_equal(h.attrib, {})
        self.assert_equal(h.children, [])

        a = root[1]
        self.assert_equal(a.qname, markup.QName('', 'a'))
        self.assert_equal(a.attrib, {})
        self.assert_equal(a.children, [])

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
        class Sausage(ayame.MarkupContainer):
            pass

        with self.application():
            mc = Sausage('a')
            with self.assert_raises_regex(ayame.AyameError,
                                          r"\bsuperclass .* not found\b"):
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
                                          r"\bmultiple inheritance\b"):
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
            status, headers, content = p.render()
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', '0')])
        self.assert_equal(content, b'')

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
            status, headers, content = p.render()
        html = self.format(SpamPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

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
        root = markup.Element(markup.QName('', 'root'),
                              attrib={markup.QName('', 'a'): ''})
        c = ayame.Component('a')
        c.add(ayame.AttributeModifier('a', model.Model(None)))
        c.add(ayame.AttributeModifier(markup.QName('', 'b'),
                                      model.Model(None)))
        c.add(ayame.AttributeModifier('c', model.Model('')))
        self.assert_equal(len(c.behaviors), 3)
        self.assert_equal(c.behaviors[0].component, c)
        self.assert_equal(c.behaviors[1].component, c)
        self.assert_equal(c.behaviors[2].component, c)

        root = c.render(root)
        self.assert_equal(root.qname, markup.QName('', 'root'))
        self.assert_equal(root.attrib, {markup.QName('', 'c'): ''})
        self.assert_equal(root.children, [])

    def test_attribute_modifier_on_markup_container(self):
        root = markup.Element(markup.QName('', 'root'),
                              attrib={markup.QName('', 'a'): ''})
        mc = ayame.MarkupContainer('a')
        mc.add(ayame.AttributeModifier('a', model.Model(None)))
        mc.add(ayame.AttributeModifier(markup.QName('', 'b'),
                                       model.Model(None)))
        mc.add(ayame.AttributeModifier('c', model.Model('')))
        self.assert_equal(len(mc.behaviors), 3)
        self.assert_equal(mc.behaviors[0].component, mc)
        self.assert_equal(mc.behaviors[1].component, mc)
        self.assert_equal(mc.behaviors[2].component, mc)

        root = mc.render(root)
        self.assert_equal(root.qname, markup.QName('', 'root'))
        self.assert_equal(root.attrib, {markup.QName('', 'c'): ''})
        self.assert_equal(root.children, [])

    def test_ignition_behavior_get(self):
        query = '{path}=clay1'
        with self.application(self.new_environ(query=query)):
            p = EggsPage()
            status, headers, content = p.render()
        html = self.format(EggsPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

        self.assert_equal(p.model_object, {'clay1': 1,
                                           'clay2': 0})

    def test_ignition_behavior_get_duplicate_ayame_path(self):
        query = ('{path}=clay1&'
                 '{path}=obstacle:clay2')
        with self.application(self.new_environ(query=query)):
            p = EggsPage()
            status, headers, content = p.render()
        html = self.format(EggsPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

        self.assert_equal(p.model_object, {'clay1': 1,
                                           'clay2': 0})

    def test_ignition_behavior_post(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

obstacle:clay2
{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = EggsPage()
            status, headers, content = p.render()
        html = self.format(EggsPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

        self.assert_equal(p.model_object, {'clay1': 0,
                                           'clay2': 1})

    def test_ignition_behavior_post_duplicate_ayame_path(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

obstacle:clay2
{__}
Content-Disposition: form-data; name="{path}"

clay1
{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = EggsPage()
            status, headers, content = p.render()
        html = self.format(EggsPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

        self.assert_equal(p.model_object, {'clay1': 0,
                                           'clay2': 1})

    def test_nested(self):
        regex = r" is not a subclass of MarkupContainer\b"
        with self.assert_raises_regex(ayame.AyameError, regex):
            class C(object):
                @ayame.nested
                class C(object):
                    pass
        with self.assert_raises_regex(ayame.AyameError, regex):
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

        with self.application(self.new_environ()):
            p = ToastPage()
            status, headers, content = p.render()
        html = self.format(ToastPage, name='ToastPage')
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

        with self.application(self.new_environ()):
            p = ToastPage.NestedPage()
            status, headers, content = p.render()
        html = self.format(ToastPage, name='ToastPage.NestedPage')
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)


class AyameHeadContainer(ayame.MarkupContainer):

    def __init__(self, id, element=None):
        super(AyameHeadContainer, self).__init__(id)
        self._element = element

    def on_render(self, element):
        ayame_head = markup.Element(markup.AYAME_HEAD)
        ayame_head.append(self._element)
        self.push_ayame_head(ayame_head)
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
    <p>clay1</p>
    <div>
      <p>clay2</p>
    </div>
  </body>
</html>
"""

    def __init__(self):
        super(EggsPage, self).__init__()
        self.model = model.CompoundModel({'clay1': 0,
                                          'clay2': 0})
        class Clay(ayame.Component):
            def __init__(self, id, model=None):
                super(self.__class__, self).__init__(id, model)
                class Counter(ayame.IgnitionBehavior):
                    def on_component(self, component, element):
                        self.fire()
                    def on_fire(self, component):
                        super(self.__class__, self).on_fire(component)
                        component.model_object += 1
                self.add(Counter())
        self.add(Clay('clay1'))
        self.add(ayame.MarkupContainer('obstacle'))
        self.find('obstacle').add(Clay('clay2'))


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
