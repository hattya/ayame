#
# test_markup
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

import io
import tempfile

import ayame
from ayame import markup
from base import AyameTestCase


class MarkupTestCase(AyameTestCase):

    def assert_markup_error(self, pos, regex, src, **kwargs):
        loader = kwargs.pop('loader', markup.MarkupLoader)()
        with self.assert_raises(ayame.MarkupError) as a:
            loader.load(self, src, **kwargs)
        self.assert_equal(len(a.exception.args), 3)
        self.assert_is(a.exception.args[0], self)
        self.assert_equal(a.exception.args[1], pos)
        self.assert_regex(a.exception.args[2], regex)

    def assert_rendering_error(self, regex, m, **kwargs):
        renderer = markup.MarkupRenderer()
        with self.assert_raises(ayame.RenderingError) as a:
            renderer.render(self, m, **kwargs)
        self.assert_is(a.exception.args[0], self)
        self.assert_regex(a.exception.args[1], regex)

    def format(self, doc_t, *args, **kwargs):
        kwargs.update(doctype=markup.XHTML1_STRICT,
                      xhtml=markup.XHTML_NS,
                      ayame=markup.AYAME_NS)
        return doc_t.format(*args, **kwargs)

    def test_element(self):
        spam = markup.Element(markup.QName('spam', 'spam'),
                              attrib={'id': 'a'},
                              type=markup.Element.EMPTY,
                              ns={'': 'spam'})
        self.assert_equal(spam.qname, markup.QName('spam', 'spam'))
        self.assert_equal(spam.attrib, {'id': 'a'})
        self.assert_equal(spam.type, markup.Element.EMPTY)
        self.assert_equal(spam.ns, {'': 'spam'})
        self.assert_equal(spam.children, [])
        self.assert_equal(repr(spam.qname), '{spam}spam')
        self.assert_regex(repr(spam), ' {spam}spam ')
        self.assert_equal(len(spam), 0)
        self.assert_true(spam)

        eggs = spam.copy()
        eggs.qname = markup.QName('spam', 'eggs')
        spam.attrib[0] = 'a'
        self.assert_equal(spam.qname, markup.QName('spam', 'spam'))
        self.assert_equal(spam.attrib, {'id': 'a',
                                        0: 'a'})

        self.assert_equal(eggs.qname, markup.QName('spam', 'eggs'))
        self.assert_equal(eggs.attrib, {'id': 'a'})
        self.assert_equal(eggs.type, markup.Element.EMPTY)
        self.assert_equal(eggs.ns, {'': 'spam'})
        self.assert_equal(eggs.children, [])
        self.assert_equal(repr(eggs.qname), '{spam}eggs')
        self.assert_regex(repr(eggs), ' {spam}eggs ')
        self.assert_equal(len(eggs), 0)
        self.assert_true(eggs)

    def test_element___getitem_____setitem_____delitem__(self):
        spam = markup.Element(self.of('spam'),
                              attrib={markup.AYAME_ID: 'spam'})
        eggs = markup.Element(self.of('eggs'))
        spam[:1] = ['a', 'b', 'c']
        spam[3:] = [eggs]
        spam[4:] = ['d', 'e', 'f']
        self.assert_equal(spam.children, ['a', 'b', 'c', eggs, 'd', 'e', 'f'])
        self.assert_equal(eggs.children, [])
        self.assert_equal(spam[:3], ['a', 'b', 'c'])
        self.assert_equal(spam[3], eggs)
        self.assert_equal(spam[4:], ['d', 'e', 'f'])
        del spam[:]
        self.assert_equal(spam.children, [])

    def test_element_append(self):
        spam = markup.Element(self.of('spam'),
                              attrib={markup.AYAME_ID: 'spam'})
        eggs = markup.Element(self.of('eggs'))
        spam.append('a')
        spam.append('b')
        spam.append('c')
        spam.append(eggs)
        spam.append('d')
        spam.append('e')
        spam.append('f')
        self.assert_equal(spam.children, ['a', 'b', 'c', eggs, 'd', 'e', 'f'])
        self.assert_equal(eggs.children, [])

    def test_element_extend(self):
        spam = markup.Element(self.of('spam'),
                              attrib={markup.AYAME_ID: 'spam'})
        eggs = markup.Element(self.of('eggs'))
        spam.extend(('a', 'b', 'c', eggs, 'd', 'e', 'f'))
        self.assert_equal(spam.children, ['a', 'b', 'c', eggs, 'd', 'e', 'f'])
        self.assert_equal(eggs.children, [])

    def test_element_insert(self):
        spam = markup.Element(self.of('spam'),
                              attrib={markup.AYAME_ID: 'spam'})
        eggs = markup.Element(self.of('eggs'))
        spam.insert(0, 'f')
        spam.insert(0, 'c')
        spam.insert(0, 'b')
        spam.insert(-1, 'd')
        spam.insert(-1, 'e')
        spam.insert(0, 'a')
        spam.insert(3, eggs)
        self.assert_equal(spam.children, ['a', 'b', 'c', eggs, 'd', 'e', 'f'])
        self.assert_equal(eggs.children, [])

    def test_element_remove(self):
        spam = markup.Element(self.of('spam'),
                              attrib={markup.AYAME_ID: 'spam'})
        eggs = markup.Element(self.of('eggs'))
        spam.extend(['a', 'b', 'c', eggs, 'd', 'e', 'f'])
        spam.remove('a')
        spam.remove('b')
        spam.remove('c')
        spam.remove(eggs)
        spam.remove('d')
        spam.remove('e')
        spam.remove('f')
        self.assert_equal(spam.children, [])
        self.assert_equal(eggs.children, [])

    def test_element_normalize(self):
        def new_elements(i=None):
            for n in ('spam', 'eggs', 'ham', 'toast', 'beans', 'bacon',
                      'sausage')[:i]:
                yield markup.Element(self.of(n))

        spam, eggs, ham, toast = new_elements(4)
        spam.extend(('a', eggs,
                     'b', 'c', ham, toast,
                     'd', 'e', 'f'))
        spam.normalize()
        self.assert_equal(spam.children, ['a', eggs,
                                          'bc', ham, toast,
                                          'def'])

        spam, eggs, ham, toast, beans, bacon, sausage = new_elements()
        spam.extend(('a', eggs,
                     'b', 'c', ham, toast,
                     'd', 'e', 'f', beans, bacon, sausage))
        spam.normalize()
        self.assert_equal(spam.children, ['a', eggs,
                                          'bc', ham, toast,
                                          'def', beans, bacon, sausage])

        spam, eggs, ham, toast, beans, bacon, sausage = new_elements()
        spam.extend((eggs, 'a',
                     ham, toast, 'b', 'c',
                     beans, bacon, sausage))
        spam.normalize()
        self.assert_equal(spam.children, [eggs, 'a',
                                          ham, toast, 'bc',
                                          beans, bacon, sausage])

        spam, eggs, ham, toast, beans, bacon, sausage = new_elements()
        spam.extend((eggs, 'a',
                     ham, toast, 'b', 'c',
                     beans, bacon, sausage, 'd', 'e', 'f'))
        spam.normalize()
        self.assert_equal(spam.children, [eggs, 'a',
                                          ham, toast, 'bc',
                                          beans, bacon, sausage, 'def'])

    def test_element_walk(self):
        root = markup.Element(self.of('root'),
                              attrib={markup.AYAME_ID: 'root'})
        it = root.walk()
        self.assert_equal(list(it), [(root, 0)])

        a1 = markup.Element(self.of('a1'))
        root.append(a1)
        a2 = markup.Element(self.of('a2'),
                            attrib={markup.AYAME_ID: 'a2'})
        root.append(a2)
        it = root.walk()
        self.assert_equal(list(it), [(root, 0),
                                     (a1, 1), (a2, 1)])

        a1_b1 = markup.Element(self.of('b1'))
        a1.append(a1_b1)
        a1_b2 = markup.Element(self.of('b2'),
                               attrib={markup.AYAME_ID: 'b2'})
        a1.append(a1_b2)
        a2_b1 = markup.Element(self.of('b1'))
        a2.append(a2_b1)
        a2_b2 = markup.Element(self.of('b2'),
                               attrib={markup.AYAME_ID: 'b2'})
        a2.append(a2_b2)
        it = root.walk()
        self.assert_equal(list(it),
                          [(root, 0),
                           (a1, 1), (a1_b1, 2), (a1_b2, 2),
                           (a2, 1), (a2_b1, 2), (a2_b2, 2)])
        it = root.walk(step=lambda element, *args: element != a1)
        self.assert_equal(list(it),
                          [(root, 0),
                           (a1, 1),
                           (a2, 1), (a2_b1, 2), (a2_b2, 2)])

    def test_fragment(self):
        spam = markup.Element(markup.QName('spam', 'spam'),
                              type=markup.Element.EMPTY,
                              ns={'': 'spam'})
        f1 = markup.Fragment(['before', spam, 'after'])
        self.assert_equal(len(f1), 3)

        f2 = f1.copy()
        self.assert_is_instance(f2, markup.Fragment)
        self.assert_equal(len(f2), 3)
        self.assert_equal(f1[0], f2[0])
        self.assert_not_equal(f1[1], f2[1])
        self.assert_equal(f1[2], f2[2])

    def test_load_error(self):
        # src is None
        src = None
        self.assert_markup_error((0, 0), r'\bload markup\b',
                                 src)

        # cannot open src
        src = ''
        self.assert_markup_error((0, 0), r'\bload markup\b',
                                 src)

    def test_load(self):
        # unknown lang
        src = io.StringIO()
        self.assert_markup_error((1, 0), " '' .* not implemented$",
                                 src, lang='')

        # unknown processing instruction
        php = u'<?php echo "Hello World!"?>'
        src = io.StringIO(php)
        loader = markup.MarkupLoader()
        m = loader.load(self, src, lang='xml')
        self.assert_equal(m.xml_decl, {})
        self.assert_equal(m.lang, 'xml')
        self.assert_is_none(m.doctype)
        self.assert_is_none(m.root)

        # no root element
        text = u'&amp; &#38;'
        src = io.StringIO(text)
        loader = markup.MarkupLoader()
        m = loader.load(self, src, lang='xml')
        self.assert_equal(m.xml_decl, {})
        self.assert_equal(m.lang, 'xml')
        self.assert_is_none(m.doctype)
        self.assert_is_none(m.root)

        # load from file
        with tempfile.NamedTemporaryFile('w+') as fp:
            loader = markup.MarkupLoader()
            m = loader.load(self, fp)
            self.assert_equal(m.xml_decl, {})
            self.assert_equal(m.lang, 'xhtml1')
            self.assert_is_none(m.doctype)
            self.assert_is_none(m.root)

    def test_load_unsupported_html(self):
        # xhtml1 frameset
        html = u"""\
<?xml version="1.0"?>\
<!DOCTYPE html PUBLIC "-//W3C/DTD XHTML 1.0 Frameset//EN"\
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">\
"""
        src = io.StringIO(html)
        self.assert_markup_error((1, 21), r'^unsupported HTML version$',
                                 src)

    def test_invalid_xml(self):
        def assert_xml(xml, pos, regex):
            src = io.StringIO(xml)
            self.assert_markup_error(pos, regex,
                                     src, lang='xml')

        # malformed xml declaration
        xml = u'<?xml standalone="yes"?>'
        assert_xml(xml, (1, 0), '^malformed XML declaration$')

        # unquoted xml attributes
        xml = u'<?xml version=1.0?>'
        assert_xml(xml, (1, 0), '^malformed XML declaration$')

        # mismatched quotes in xml declaration
        xml = u'<?xml version="1.0\'?>'
        assert_xml(xml, (1, 0), '^mismatched quotes$')
        xml = u'<?xml version=\'1.0"?>'
        assert_xml(xml, (1, 0), '^mismatched quotes$')

        # no xml declaration
        xml = u'<spam></spam>'
        assert_xml(xml, (1, 0), '^XML declaration is not found$')

        # multiple root elements
        xml = u"""\
<?xml version="1.0"?>\
<spam/>\
<eggs/>\
"""
        assert_xml(xml, (1, 28), ' multiple root elements$')
        xml = u"""\
<?xml version="1.0"?>\
<spam></spam>\
<eggs></eggs>\
"""
        assert_xml(xml, (1, 34), ' multiple root elements$')

        # omitted end tag for root element
        xml = u"""\
<?xml version="1.0"?>\
<spam>\
"""
        assert_xml(xml, (1, 27), "^end tag .* '{}spam' omitted$")

        # mismatched tag
        xml = u"""\
<?xml version="1.0"?>\
<spam></eggs>\
"""
        assert_xml(xml, (1, 27), "^end tag .* '{}eggs' .* not open$")

        # attribute duplication
        xml = u"""\
<?xml version="1.0"?>\
<spam a="1" a="2"/>\
"""
        assert_xml(xml, (1, 21), "^attribute '{}a' already exists$")

    def test_load_empty_xml(self):
        xml = u"<?xml version='1.0'?>"
        src = io.StringIO(xml)
        loader = markup.MarkupLoader()
        m = loader.load(self, src, lang='xml')
        self.assert_equal(m.xml_decl, {'version': '1.0'})
        self.assert_equal(m.lang, 'xml')
        self.assert_is_none(m.doctype)
        self.assert_is_none(m.root)

    def test_load_xml(self):
        xml = u"""\
<?xml version="1.0"?>\
<!DOCTYPE spam SYSTEM "spam.dtd">\
<spam xmlns="spam" id="a">\
&amp;\
<eggs/>\
&#38;\
x\
</spam>\
"""
        src = io.StringIO(xml)
        loader = markup.MarkupLoader()
        m = loader.load(self, src, lang='xml')
        self.assert_equal(m.xml_decl, {'version': '1.0'})
        self.assert_equal(m.lang, 'xml')
        self.assert_equal(m.doctype, '<!DOCTYPE spam SYSTEM "spam.dtd">')
        self.assert_true(m.root)

        spam = m.root
        self.assert_equal(spam.qname, markup.QName('spam', 'spam'))
        self.assert_equal(spam.attrib, {markup.QName('spam', 'id'): 'a'})
        self.assert_equal(spam.type, markup.Element.OPEN)
        self.assert_equal(spam.ns, {'': 'spam',
                                    'xml': markup.XML_NS})
        self.assert_equal(len(spam), 3)
        self.assert_equal(spam[0], '&amp;')
        self.assert_equal(spam[2], '&#38;x')

        eggs = spam[1]
        self.assert_equal(eggs.qname, markup.QName('spam', 'eggs'))
        self.assert_equal(eggs.attrib, {})
        self.assert_equal(eggs.type, markup.Element.EMPTY)
        self.assert_equal(eggs.ns, {})
        self.assert_equal(eggs.children, [])

    def test_load_xml_with_prefix(self):
        xml = u"""\
<?xml version="1.0"?>\
<spam xmlns="spam" xmlns:eggs="eggs">\
<eggs:eggs/>\
</spam>\
"""
        src = io.StringIO(xml)
        loader = markup.MarkupLoader()
        m = loader.load(self, src, lang='xml')
        self.assert_equal(m.xml_decl, {'version': '1.0'})
        self.assert_equal(m.lang, 'xml')
        self.assert_is_none(m.doctype)
        self.assert_true(m.root)

        spam = m.root
        self.assert_equal(spam.qname, markup.QName('spam', 'spam'))
        self.assert_equal(spam.attrib, {})
        self.assert_equal(spam.type, markup.Element.OPEN)
        self.assert_equal(spam.ns, {'': 'spam',
                                    'eggs': 'eggs',
                                    'xml': markup.XML_NS})
        self.assert_equal(len(spam), 1)

        eggs = spam[0]
        self.assert_equal(eggs.qname, markup.QName('eggs', 'eggs'))
        self.assert_equal(eggs.attrib, {})
        self.assert_equal(eggs.type, markup.Element.EMPTY)
        self.assert_equal(eggs.ns, {})
        self.assert_equal(eggs.children, [])

        # no default namespace
        class Loader(markup.MarkupLoader):
            def new_xml_element(self, *args, **kwargs):
                elem = super(Loader, self).new_xml_element(*args, **kwargs)
                elem.ns.pop('', None)
                return elem

        src = io.StringIO(xml)
        self.assert_markup_error((1, 70), ' no default namespace$',
                                 src, lang='xml',
                                 loader=Loader)

        # no eggs namespace
        class Loader(markup.MarkupLoader):
            def new_xml_element(self, *args, **kwargs):
                elem = super(Loader, self).new_xml_element(*args, **kwargs)
                elem.ns.pop('eggs', None)
                return elem

        src = io.StringIO(xml)
        self.assert_markup_error((1, 58), "^unknown .* prefix 'eggs'$",
                                 src, lang='xml',
                                 loader=Loader)

    def test_invalid_xhtml1(self):
        def assert_xhtml1(html_t, pos, regex):
            src = io.StringIO(self.format(html_t))
            self.assert_markup_error(pos, regex,
                                     src, lang='xhtml1')

        # no xml declaration
        html_t = u"""\
{doctype}\
<html xmlns="http://www.w3.org/1999/xhtml">\
</html>\
"""
        assert_xhtml1(html_t, (1, 109), '^XML declaration is not found$')

        # multiple root elements
        html_t = u"""\
<?xml version="1.0"?>\
{doctype}\
<html xmlns="http://www.w3.org/1999/xhtml" />\
<html xmlns="http://www.w3.org/1999/xhtml" />\
"""
        assert_xhtml1(html_t, (1, 175), ' multiple root elements$')

        # omitted end tag for root element
        html_t = u"""\
<?xml version="1.0"?>\
{doctype}\
<html xmlns="http://www.w3.org/1999/xhtml">\
"""
        assert_xhtml1(html_t, (1, 173), "^end tag .* '{.*}html' omitted$")

    def test_load_xhtml1(self):
        html = self.format(u"""\
<?xml version="1.0"?>\
{doctype}\
<html xmlns="{xhtml}">\
<head>\
<title>title</title>\
</head>\
<body>\
<h1>text</h1>\
<p>line1<br />line2</p>\
</body>\
</html>\
""")
        src = io.StringIO(html)
        loader = markup.MarkupLoader()
        m = loader.load(self, src, lang='xhtml1')
        self.assert_equal(m.xml_decl, {'version': '1.0'})
        self.assert_equal(m.lang, 'xhtml1')
        self.assert_equal(m.doctype, markup.XHTML1_STRICT)
        self.assert_true(m.root)

        html = m.root
        self.assert_equal(html.qname, self.html_of('html'))
        self.assert_equal(html.attrib, {})
        self.assert_equal(html.type, markup.Element.OPEN)
        self.assert_equal(html.ns, {'': markup.XHTML_NS,
                                    'xml': markup.XML_NS})
        self.assert_equal(len(html), 2)

        head = html[0]
        self.assert_equal(head.qname, self.html_of('head'))
        self.assert_equal(head.attrib, {})
        self.assert_equal(head.type, markup.Element.OPEN)
        self.assert_equal(head.ns, {})
        self.assert_equal(len(head), 1)

        title = head[0]
        self.assert_equal(title.qname, self.html_of('title'))
        self.assert_equal(title.attrib, {})
        self.assert_equal(title.type, markup.Element.OPEN)
        self.assert_equal(title.ns, {})
        self.assert_equal(title.children, ['title'])

        body = html[1]
        self.assert_equal(body.qname, self.html_of('body'))
        self.assert_equal(body.attrib, {})
        self.assert_equal(body.type, markup.Element.OPEN)
        self.assert_equal(body.ns, {})
        self.assert_equal(len(body), 2)

        h1 = body[0]
        self.assert_equal(h1.qname, self.html_of('h1'))
        self.assert_equal(h1.attrib, {})
        self.assert_equal(h1.type, markup.Element.OPEN)
        self.assert_equal(h1.ns, {})
        self.assert_equal(h1.children, ['text'])

        p = body[1]
        self.assert_equal(p.qname, self.html_of('p'))
        self.assert_equal(p.attrib, {})
        self.assert_equal(p.type, markup.Element.OPEN)
        self.assert_equal(p.ns, {})
        self.assert_equal(len(p), 3)
        self.assert_equal(p[0], 'line1')
        self.assert_equal(p[2], 'line2')

        br = p[1]
        self.assert_equal(br.qname, self.html_of('br'))
        self.assert_equal(br.attrib, {})
        self.assert_equal(br.type, markup.Element.EMPTY)
        self.assert_equal(br.ns, {})
        self.assert_equal(br.children, [])

    def test_ayame_remove(self):
        # descendant of root element
        html = self.format(u"""\
<?xml version="1.0"?>\
{doctype}\
<html xmlns="{xhtml}" xmlns:ayame="{ayame}">\
<ayame:remove>\
<body>\
<h1>text</h1>\
<hr />\
</body>\
</ayame:remove>\
</html>\
""")
        src = io.StringIO(html)
        loader = markup.MarkupLoader()
        m = loader.load(self, src, lang='xhtml1')
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
        self.assert_equal(html.children, [])

        # multiple root elements
        html_t = self.format(u"""\
<?xml version="1.0"?>\
{doctype}\
<ayame:remove xmlns:ayame="{ayame}">\
before html\
</ayame:remove>\
<ayame:remove xmlns:ayame="{ayame}" />\
<html xmlns="{xhtml}" xmlns:ayame="{ayame}">\
<ayame:remove>\
<body>\
<h1>text</h1>\
<hr />\
</body>\
</ayame:remove>\
</html>\
<ayame:remove xmlns:ayame="{ayame}" />\
<ayame:remove xmlns:ayame="{ayame}">\
after html\
</ayame:remove>\
""")
        src = io.StringIO(html_t)
        loader = markup.MarkupLoader()
        m = loader.load(self, src, lang='xhtml1')
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
        self.assert_equal(html.children, [])

    def test_render_error(self):
        def new_markup(lang):
            m = markup.Markup()
            m.xml_decl = {
                'version': u'1.0',
                'standalone': u'yes'
            }
            m.lang = lang
            spam = markup.Element(markup.QName(u'spam', u'spam'),
                                  attrib={markup.QName(u'spam', u'id'): u'a'},
                                  type=markup.Element.OPEN,
                                  ns={u'': u'spam'})
            eggs = markup.Element(markup.QName(u'spam', u'eggs'),
                                  type=markup.Element.OPEN)
            eggs.append(0)
            spam.append(eggs)
            m.root = spam
            return m

        # invalid type
        m = new_markup('xml')
        self.assert_rendering_error("^invalid type .* 'int'",
                                    m, pretty=False)
        self.assert_rendering_error("^invalid type .* 'int'",
                                    m, pretty=True)

        # svg
        m = new_markup('svg')
        self.assert_rendering_error(" 'svg' .* not implemented$",
                                    m, pretty=False)
        self.assert_rendering_error(" 'svg' .* not implemented$",
                                    m, pretty=True)

        # unknown namespace URI
        m = new_markup('xml')
        m.root.ns.clear()
        del m.root[0][:]
        self.assert_rendering_error("^unknown namespace URI 'spam'$",
                                    m, pretty=False)
        self.assert_rendering_error("^unknown namespace URI 'spam'$",
                                    m, pretty=True)

        # overwrite namespace URI
        m = new_markup('xml')
        m.root[0].ns[u''] = u'eggs'
        ham = markup.Element(markup.QName(u'spam', u'ham'),
                             type=markup.Element.EMPTY)
        m.root[0][:] = [ham]
        self.assert_rendering_error("namespace URI .*''.* overwritten$",
                                    m, pretty=False)
        self.assert_rendering_error("namespace URI .*''.* overwritten$",
                                    m, pretty=True)

        # element namespace with default namespace
        m = new_markup('xml')
        eggs = markup.Element(markup.QName(u'eggs', u'eggs'),
                              attrib={markup.QName(u'eggs', u'a'): u'1',
                                      markup.QName(u'spam', u'a'): u'2'},
                              type=markup.Element.OPEN,
                              ns={u'eggs': u'eggs'})
        m.root[:] = [eggs]
        self.assert_rendering_error(' default namespace$',
                                    m, pretty=False)
        self.assert_rendering_error(' default namespace$',
                                    m, pretty=True)

        # attribute is None
        m = new_markup('xhtml1')
        m.root = markup.Element(self.html_of(u'html'),
                                attrib={self.html_of(u'lang'): None},
                                type=markup.Element.EMPTY,
                                ns={u'': markup.XHTML_NS})
        self.assert_rendering_error("^'{.*}lang' attribute is None$",
                                    m, pretty=False)
        self.assert_rendering_error("^'{.*}lang' attribute is None$",
                                    m, pretty=True)

    def test_render_xml(self):
        renderer = markup.MarkupRenderer()

        # pretty output
        xml = u"""\
<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE spam SYSTEM "spam.dtd">
<spam xmlns="spam" a="a">
  a
  <eggs/>
  b
  c
  <eggs:eggs xmlns:eggs="eggs" xmlns:ham="ham" a="1" ham:a="2">
    <ham>
      1
      2
    </ham>
  </eggs:eggs>
</spam>
""".encode('iso-8859-1')

        m = markup.Markup()
        m.xml_decl = {
            'version': u'1.0',
            'encoding': u'iso-8859-1'
        }
        m.lang = 'xml'
        m.doctype = u'<!DOCTYPE spam SYSTEM "spam.dtd">'
        m.root = markup.Element(markup.QName(u'spam', u'spam'),
                                attrib={markup.QName(u'spam', u'a'): u'a'},
                                type=markup.Element.OPEN,
                                ns={u'': u'spam'})
        m.root.append(u'\n'
                      u'    a\n'
                      u'    \n')
        eggs = markup.Element(markup.QName(u'spam', u'eggs'),
                              type=markup.Element.EMPTY)
        m.root.append(eggs)
        m.root.append(u'\n'
                      u'    b\n'
                      u'    c\n')
        eggs = markup.Element(markup.QName(u'eggs', u'eggs'),
                              attrib={markup.QName(u'eggs', u'a'): u'1',
                                      markup.QName(u'ham', u'a'): u'2'},
                              type=markup.Element.OPEN,
                              ns={u'eggs': u'eggs',
                                  u'ham': u'ham'})
        ham = markup.Element(markup.QName(u'spam', u'ham'),
                             type=markup.Element.OPEN)
        ham.append(u'\n'
                   u'    1\n'
                   u'    2\n')
        eggs.append(ham)
        m.root.append(eggs)
        self.assert_equal(renderer.render(self, m, pretty=True), xml)

        # raw output
        m = markup.Markup()
        m.xml_decl = {
            'version': u'1.0',
            'encoding': u'iso-8859-1'
        }
        m.lang = 'xml'
        m.doctype = u'<!DOCTYPE spam SYSTEM "spam.dtd">'
        m.root = markup.Element(markup.QName(u'spam', u'spam'),
                                attrib={markup.QName(u'spam', u'a'): u'a'},
                                type=markup.Element.OPEN,
                                ns={u'': u'spam'})
        m.root.append(u'\n'
                      u'  a\n'
                      u'  ')
        eggs = markup.Element(markup.QName(u'spam', u'eggs'))
        eggs.type = markup.Element.EMPTY
        m.root.append(eggs)
        m.root.append(u'\n'
                      u'  b\n'
                      u'  c\n'
                      u'  ')
        eggs = markup.Element(markup.QName(u'eggs', u'eggs'),
                              attrib={markup.QName(u'eggs', u'a'): u'1',
                                      markup.QName(u'ham', u'a'): u'2'},
                              type=markup.Element.OPEN,
                              ns={u'eggs': u'eggs',
                                  u'ham': u'ham'})
        eggs.append(u'\n'
                    u'    ')
        ham = markup.Element(markup.QName(u'spam', u'ham'),
                             type=markup.Element.OPEN)
        ham.append(u'\n'
                   u'      1\n'
                   u'      2\n'
                   u'    ')
        eggs.append(ham)
        eggs.append(u'\n'
                    u'  ')
        m.root.append(eggs)
        m.root.append(u'\n')
        self.assert_equal(renderer.render(self, m, pretty=False), xml)

    def test_render_xhtml1(self):
        renderer = markup.MarkupRenderer()

        def new_element(name, type=markup.Element.OPEN, **kwargs):
            return markup.Element(self.html_of(name), type=type, **kwargs)

        def new_ayame_element(name, **kwargs):
            kwargs['type'] = markup.Element.OPEN
            return markup.Element(self.ayame_of(name), **kwargs)

        html = self.format(u"""\
<?xml version="1.0" encoding="ISO-8859-1"?>
{doctype}
<html xmlns="{xhtml}" xmlns:ayame="{ayame}" xml:lang="en">
  <head>
    <meta content="" name="keywords" />
    <title>title</title>
    <style type="text/css">
      h1 {{
        font-size: 120%;
      }}
      p {{
        font-size: 90%;
      }}
    </style>
    <script type="text/javascript">
      <!--
      var x = 0;
      var y = 0;
      // -->
    </script>
  </head>
  <body>
    <ayame:remove>
      <p>Hello World!</p>
    </ayame:remove>
    <h1> spam <span class="yellow"> eggs </span> ham </h1>
    <blockquote cite="http://example.com/">
      <p>citation</p>
    </blockquote>
    <div class="text"> spam <i>eggs</i> ham</div>
    <div class="ayame">
      <ins>
        <ayame:remove>
          spam<br />
          eggs
        </ayame:remove>
      </ins>
      <p>
        <ayame:remove>
          ham
        </ayame:remove>
        toast
      </p>
      <ul>
        <ayame:container id="a">
          <li>spam</li>
          <li>eggs</li>
        </ayame:container>
      </ul>
    </div>
    <div class="block">
      Planets
      <ul>
        <li> Mercury </li>
        <li> Venus </li>
        <li>Earth</li>
      </ul>
    </div>
    <div class="inline-ins-del">
      <p><del>old</del><ins>new</ins></p>
    </div>
    <div class="block-ins-del">
      <del>
        <pre>old</pre>
      </del>
      <ins>
        <pre>new</pre>
      </ins>
    </div>
    <pre>
  * 1
    * 2
      * 3
    * 4
  * 5
</pre>
    <div class="br">
      <h2>The Solar System</h2>
      <p>
        <em>Mercury</em> is the first planet.<br />
        <em>Venus</em> is the second planet.
      </p>
      <p><em>Earth</em> is the third planet.</p>
      <ayame:remove>
        <p>
          <em>Mars</em> is the fourth planet.<br />
          <em>Jupiter</em> is the fifth planet.
        </p>
      </ayame:remove>
      <ul>
        <li>
          1<br />
          2<br />
          3
        </li>
      </ul>
    </div>
    <form action="/" method="post">
      <fieldset>
        <legend>form</legend>
        <textarea>
          Sun
        </textarea>
      </fieldset>
    </form>
  </body>
</html>
""").encode('iso-8859-1')

        m = markup.Markup()
        m.xml_decl = {
            'version': u'1.0',
            'encoding': u'iso-8859-1'
        }
        m.lang = 'xhtml1'
        m.doctype = markup.XHTML1_STRICT
        m.root = new_element(u'html',
                             attrib={self.xml_of(u'lang'): u'en'},
                             ns={u'a': markup.XML_NS,
                                 u'b': markup.XHTML_NS,
                                 u'ayame': markup.AYAME_NS})

        head = new_element(u'head')
        meta = new_element(u'meta',
                           attrib={self.html_of(u'name'): u'keywords',
                                   self.html_of(u'content'): u''})
        meta.append(u'a')
        head.append(meta)

        title = new_element(u'title')
        title.append(u'title')
        span = new_element(u'span')
        title.append(span)
        head.append(title)

        style = new_element(u'style',
                            attrib={self.html_of(u'type'): u'text/css'})
        style.append(u'\n'
                     u'      h1 {\n'
                     u'        font-size: 120%;\n'
                     u'      }\n'
                     u'\n'
                     u'      p {\n'
                     u'        font-size: 90%;\n'
                     u'      }\n'
                     u'\n')
        head.append(style)

        script = new_element(
            u'script',
            attrib={self.html_of(u'type'): u'text/javascript'})
        script.append(u'\n'
                      u'     <!--\n'
                      u'     var x = 0;\n'
                      u'     var y = 0;\n'
                      u'     // -->\n'
                      u'\n')
        head.append(script)
        m.root.append(head)

        body = new_element(u'body')
        remove = new_ayame_element(u'remove')
        p = new_element(u'p')
        p.append(u'Hello World!')
        remove.append(p)
        body.append(remove)

        h1 = new_element(u'h1')
        h1.append(u'\n'
                  u'  spam\n')
        span = new_element(u'span',
                           attrib={self.html_of(u'class'): u'yellow'})
        span.append(u'\n'
                    u'  eggs  \n')
        h1.append(span)
        h1.append(u'\n'
                  u'  ham  \n')
        body.append(h1)

        blockquote = new_element(
            u'blockquote',
            attrib={self.html_of(u'cite'): u'http://example.com/'})
        blockquote.append(u'before')
        p = new_element(u'p')
        p.append(u'citation')
        blockquote.append(p)
        blockquote.append(u'after')
        body.append(blockquote)

        div = new_element(u'div',
                          attrib={self.html_of(u'class'): u'text'})
        div.append(u'\n'
                   u'spam   \n'
                   u'\n')
        i = new_element(u'i')
        i.append(u'eggs')
        div.append(i)
        div.append(u'  ham')
        body.append(div)

        div = new_element(u'div',
                          attrib={self.html_of(u'class'): u'ayame'})
        ins = new_element(u'ins')
        remove = new_ayame_element(u'remove')
        remove.append(u'spam')
        br = new_element(u'br', type=markup.Element.EMPTY)
        remove.append(br)
        remove.append(u'eggs')
        ins.append(remove)
        div.append(ins)
        p = new_element(u'p')
        remove = new_ayame_element(u'remove')
        remove.append(u'ham')
        p.append(remove)
        p.append(u'toast')
        div.append(p)
        ul = new_element(u'ul')
        container = new_ayame_element(u'container',
                                      attrib={markup.AYAME_ID: u'a'})
        li = new_element(u'li')
        li.append(u'spam')
        container.append(li)
        li = new_element(u'li')
        li.append(u'eggs')
        container.append(li)
        ul.append(container)
        div.append(ul)
        body.append(div)

        div = new_element(u'div',
                          attrib={self.html_of(u'class'): u'block'})
        div.append(u'Planets')
        ul = new_element(u'ul')
        li = new_element(u'li')
        li.append(u'\n'
                  u' Mercury '
                  u'\n')
        ul.append(li)
        li = new_element(u'li')
        li.append(u'  Venus  ')
        ul.append(li)
        li = new_element(u'li')
        li.append(u'Earth')
        ul.append(li)
        div.append(ul)
        div.append(u'\n')
        body.append(div)

        div = new_element(u'div',
                          attrib={self.html_of(u'class'): u'inline-ins-del'})
        p = new_element(u'p')
        del_ = new_element(u'del')
        del_.append(u'old')
        p.append(del_)
        ins = new_element(u'ins')
        ins.append(u'new')
        p.append(ins)
        div.append(p)
        body.append(div)

        div = new_element(u'div',
                          attrib={self.html_of(u'class'): u'block-ins-del'})
        del_ = new_element(u'del')
        pre = new_element(u'pre')
        pre.append(u'old')
        del_.append(pre)
        div.append(del_)
        ins = new_element(u'ins')
        pre = new_element(u'pre')
        pre.append(u'new')
        ins.append(pre)
        div.append(ins)
        body.append(div)

        pre = new_element(u'pre')
        pre.append(u'\n'
                   u'  * 1\n'
                   u'    * 2\n'
                   u'      * 3\n'
                   u'    * 4\n'
                   u'  * 5\n')
        body.append(pre)

        div = new_element(u'div',
                          attrib={self.html_of(u'class'): u'br'})
        h2 = new_element(u'h2')
        h2.append(u'The Solar System')
        div.append(h2)
        p = new_element(u'p')
        em = new_element(u'em')
        em.append(u'Mercury')
        p.append(em)
        p.append(u' is the first planet.')
        br = new_element(u'br', type=markup.Element.EMPTY)
        p.append(br)
        p.append(u'\n')
        em = new_element(u'em')
        em.append(u'Venus')
        p.append(em)
        p.append(u' is the second planet.')
        p.append(u'\n')
        div.append(p)
        div.append(u'\n')
        p = new_element(u'p')
        em = new_element(u'em')
        em.append(u'Earth')
        p.append(em)
        p.append(u' is the third planet.')
        div.append(p)
        remove = new_ayame_element(u'remove')
        p = new_element(u'p')
        em = new_element(u'em')
        em.append(u'Mars')
        p.append(em)
        p.append(u' is the fourth planet.')
        br = new_element(u'br', type=markup.Element.EMPTY)
        p.append(br)
        em = new_element(u'em')
        em.append(u'Jupiter')
        p.append(em)
        p.append(u' is the fifth planet.')
        remove.append(p)
        div.append(remove)
        ul = new_element(u'ul')
        li = new_element(u'li')
        li.append(u'1')
        br = new_element(u'br', type=markup.Element.EMPTY)
        li.append(br)
        li.append(u'2')
        br = new_element(u'br', type=markup.Element.EMPTY)
        li.append(br)
        li.append(u'3')
        ul.append(li)
        div.append(ul)
        div.append(u'\n')
        body.append(div)

        form = new_element(u'form',
                           attrib={self.html_of(u'action'): u'/',
                                   self.html_of(u'method'): u'post'})
        fieldset = new_element(u'fieldset')
        legend = new_element(u'legend')
        legend.append(u'form')
        fieldset.append(legend)
        textarea = new_element(u'textarea')
        textarea.append(u'Sun')
        fieldset.append(textarea)
        form.append(fieldset)
        body.append(form)
        m.root.append(body)

        self.assert_equal(renderer.render(self, m, pretty=True), html)
