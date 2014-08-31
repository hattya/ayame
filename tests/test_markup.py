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
try:
    import cPickle as pickle
except ImportError:
    import pickle

import ayame
from ayame import _compat as five
from ayame import markup
from base import AyameTestCase


class MarkupTestCase(AyameTestCase):

    def assert_markup_equal(self, a, b):
        self.assert_is_not(a, b)
        self.assert_is_not(a.xml_decl, b.xml_decl)
        self.assert_equal(a.xml_decl, b.xml_decl)
        self.assert_equal(a.lang, b.lang)
        self.assert_equal(a.doctype, b.doctype)
        self.assert_is_not(a.root, b.root)
        # html
        self.assert_element_equal(a.root, b.root)
        # html head
        self.assert_element_equal(a.root[0], b.root[0])
        # html head title
        self.assert_element_equal(a.root[0][0], b.root[0][0])
        # html body
        self.assert_element_equal(a.root[1], b.root[1])

    def new_xhtml1(self):
        def new_element(name, **kwargs):
            return markup.Element(self.html_of(name),
                                  type=markup.Element.OPEN,
                                  **kwargs)

        m = markup.Markup()
        m.xml_decl = {'version': '1.0'}
        m.lang = 'xhtml1'
        m.doctype = markup.XHTML1_STRICT
        m.root = new_element('html',
                             ns={'': markup.XHTML_NS,
                                 'xml': markup.XML_NS})
        head = new_element('head')
        head.append(new_element('title'))
        body = new_element('body')
        m.root[:] = [head, body]
        return m

    def test_markup_copy(self):
        m = self.new_xhtml1()
        self.assert_markup_equal(m, m.copy())

    def test_markup_pickle(self):
        m = self.new_xhtml1()
        self.assert_markup_equal(m, pickle.loads(pickle.dumps(m)))

    def test_fragment(self):
        br = markup.Element(self.html_of('br'),
                            type=markup.Element.EMPTY)
        f = markup.Fragment(['before', br, 'after'])
        self.assert_equal(len(f), 3)

        f = f.copy()
        self.assert_is_instance(f, markup.Fragment)
        self.assert_equal(len(f), 3)
        self.assert_equal(f[0], 'before')
        self.assert_is_not(f[1], br)
        self.assert_equal(f[2], 'after')

    def test_space(self):
        self.assert_is_instance(markup.Space, five.str)
        self.assert_equal(repr(markup.Space), 'Space')

    def test_markup_handler(self):
        class MarkupHandler(markup.MarkupHandler):
            @property
            def xml(self):
                return super(MarkupHandler, self).xml

            def is_empty(self, element):
                return super(MarkupHandler, self).is_empty(element)

            def start_tag(self):
                super(MarkupHandler, self).start_tag()
                self.renderer.write(u'start_tag\n')

            def end_tag(self):
                super(MarkupHandler, self).end_tag()
                self.renderer.write(u'end_tag\n')

        class MarkupRenderer(io.StringIO):
            def peek(self):
                pass

            def writeln(self, *args):
                for a in args:
                    self.write(a)
                self.write(u'\n')

        with self.assert_raises(TypeError):
            markup.MarkupHandler(None)

        r = MarkupRenderer()
        h = MarkupHandler(r)
        self.assert_is_none(h.xml)
        self.assert_is_none(h.is_empty(None))
        h.doctype(u'doctype')
        h.start_tag()
        h.end_tag()
        h.text(0, u'')
        h.text(0, u'text\n')
        h.indent(0, 0)
        self.assert_equal(r.getvalue(), u'doctype\nstart_tag\nend_tag\ntext\n')

        elem = markup.Element(None)
        elem[:] = ('',) * 3
        h.compile(elem)
        self.assert_equal(elem.children, [])

    def test_markup_prettifier(self):
        class MarkupHandler(markup.MarkupHandler):
            @property
            def xml(self):
                pass

            def is_empty(self, element):
                pass

            def start_tag(self):
                pass

            def end_tag(self):
                pass

            def indent(self, pos):
                self.renderer.write(u'indent\n')

            def compile(self, element):
                self.renderer.write(u'compile\n')

        r = io.StringIO()
        h = markup.MarkupPrettifier(MarkupHandler(r))
        h._bol = True
        h.text(0, u'')
        self.assert_true(h._bol)
        h.text(0, u'text\n')
        self.assert_false(h._bol)
        h.indent(0)
        h.compile(None)
        self.assert_equal(r.getvalue(), u'text\nindent\ncompile\n')


class MarkupLoaderTestCase(AyameTestCase):

    def assert_error(self, pos, regex, src, **kwargs):
        loader = kwargs.pop('loader', markup.MarkupLoader)()
        with self.assert_raises(ayame.MarkupError) as cm:
            loader.load(self, src, **kwargs)
        self.assert_equal(len(cm.exception.args), 3)
        self.assert_is(cm.exception.args[0], self)
        self.assert_equal(cm.exception.args[1], pos)
        self.assert_regex(cm.exception.args[2], regex)

    def load(self, src, **kwargs):
        return markup.MarkupLoader().load(self, src, **kwargs)

    def format(self, doc_t, *args, **kwargs):
        kwargs.update(doctype=markup.XHTML1_STRICT,
                      xhtml=markup.XHTML_NS,
                      ayame=markup.AYAME_NS)
        return doc_t.format(*args, **kwargs)

    def test_load(self):
        # unknown processing instruction
        src = io.StringIO(u'<?php echo "Hello World!"?>')
        m = self.load(src, lang='xml')
        self.assert_equal(m.xml_decl, {})
        self.assert_equal(m.lang, 'xml')
        self.assert_is_none(m.doctype)
        self.assert_is_none(m.root)

        # no root element
        src = io.StringIO(u'&amp; &#38;')
        m = self.load(src, lang='xml')
        self.assert_equal(m.xml_decl, {})
        self.assert_equal(m.lang, 'xml')
        self.assert_is_none(m.doctype)
        self.assert_is_none(m.root)

    def test_unsupported_html(self):
        # xhtml1 frameset
        html = u"""\
<?xml version="1.0"?>
<!DOCTYPE html PUBLIC "-//W3C/DTD XHTML 1.0 Frameset//EN"\
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">
"""
        self.assert_error((2, 0), '^unsupported HTML version$',
                          io.StringIO(html))

    def test_invalid_xml(self):
        def assert_xml(pos, regex, xml):
            self.assert_error(pos, regex,
                              io.StringIO(xml), lang='xml')

        # malformed xml declaration
        xml = u'<?xml standalone="yes"?>'
        assert_xml((1, 0), '^malformed XML declaration$',
                   xml)

        # unquoted xml attributes
        xml = u'<?xml version=1.0?>'
        assert_xml((1, 0), '^malformed XML declaration$',
                   xml)

        # mismatched quotes in xml declaration
        for xml in (u'<?xml version="1.0\'?>',
                    u'<?xml version=\'1.0"?>'):
            assert_xml((1, 0), '^mismatched quotes$',
                       xml)

        # no xml declaration
        xml = u'<spam></spam>'
        assert_xml((1, 0), '^XML declaration is not found$',
                   xml)

        # multiple root elements
        for xml in (u'<?xml version="1.0"?>\n<spam/>\n<eggs/>',
                    u'<?xml version="1.0"?>\n<spam></spam>\n<eggs></eggs>'):
            assert_xml((3, 0), ' multiple root elements$',
                       xml)

        # omitted end tag for root element
        xml = u'<?xml version="1.0"?>\n<spam>'
        assert_xml((2, 6), "^end tag .* '{}spam' omitted$",
                   xml)

        # mismatched tag
        xml = u'<?xml version="1.0"?>\n<spam></eggs>'
        assert_xml((2, 6), "^end tag .* '{}eggs' .* not open$",
                   xml)

        # attribute duplication
        xml = u'<?xml version="1.0"?>\n<spam a="1" a="2"/>'
        assert_xml((2, 0), "^attribute '{}a' already exists$",
                   xml)

    def test_empty_xml(self):
        src = io.StringIO(u'<?xml version="1.0"?>')
        m = self.load(src, lang='xml')
        self.assert_equal(m.xml_decl, {'version': '1.0'})
        self.assert_equal(m.lang, 'xml')
        self.assert_is_none(m.doctype)
        self.assert_is_none(m.root)

    def test_xml(self):
        xml = u"""\
<?xml version="1.0"?>\
<!DOCTYPE spam SYSTEM "spam.dtd">\
<spam xmlns="spam" id="spam">\
&amp;\
<eggs/>\
&#38;\
x\
</spam>\
"""
        src = io.StringIO(xml)
        m = self.load(src, lang='xml')
        self.assert_equal(m.xml_decl, {'version': '1.0'})
        self.assert_equal(m.lang, 'xml')
        self.assert_equal(m.doctype, '<!DOCTYPE spam SYSTEM "spam.dtd">')
        self.assert_true(m.root)

        spam = m.root
        self.assert_equal(spam.qname, markup.QName('spam', 'spam'))
        self.assert_equal(spam.attrib, {markup.QName('spam', 'id'): 'spam'})
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

    def test_xml_with_prefix(self):
        xml = u"""\
<?xml version="1.0"?>\
<spam xmlns="spam" xmlns:eggs="eggs">\
<eggs:eggs/>\
</spam>\
"""
        src = io.StringIO(xml)
        m = self.load(src, lang='xml')
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
            def _new_element(self, *args, **kwargs):
                elem = super(Loader, self)._new_element(*args, **kwargs)
                elem.ns.pop('', None)
                return elem

        src = io.StringIO(xml)
        self.assert_error((1, 70), ' no default namespace$',
                          src, lang='xml',
                          loader=Loader)

        # no eggs namespace
        class Loader(markup.MarkupLoader):
            def _new_element(self, *args, **kwargs):
                elem = super(Loader, self)._new_element(*args, **kwargs)
                elem.ns.pop('eggs', None)
                return elem

        src = io.StringIO(xml)
        self.assert_error((1, 58), "^unknown .* prefix 'eggs'$",
                          src, lang='xml',
                          loader=Loader)

    def test_invalid_xhtml1(self):
        def assert_xhtml1(pos, regex, html_t):
            self.assert_error(pos, regex,
                              io.StringIO(self.format(html_t)), lang='xhtml1')

        # no xml declaration
        html_t = u"""\
{doctype}
<html xmlns="http://www.w3.org/1999/xhtml">
</html>
"""
        assert_xhtml1((2, 0), '^XML declaration is not found$',
                      html_t)

        # multiple root elements
        html_t = u"""\
<?xml version="1.0"?>
{doctype}
<html xmlns="http://www.w3.org/1999/xhtml" />
<html xmlns="http://www.w3.org/1999/xhtml" />
"""
        assert_xhtml1((4, 0), ' multiple root elements$',
                      html_t)

        # omitted end tag for root element
        html_t = u"""\
<?xml version="1.0"?>
{doctype}
<html xmlns="http://www.w3.org/1999/xhtml">
"""
        assert_xhtml1((4, 0), "^end tag .* '{.*}html' omitted$",
                      html_t)

    def test_xhtml1(self):
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
        m = self.load(src, lang='xhtml1')
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
<?xml version="1.0"?>
{doctype}
<html xmlns="{xhtml}" xmlns:ayame="{ayame}">\
<ayame:remove>
  <body>
    <h1>text</h1>
    <hr />
  </body>
</ayame:remove>\
</html>
""")
        src = io.StringIO(html)
        m = self.load(src, lang='xhtml1')
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
        html = self.format(u"""\
<?xml version="1.0"?>
{doctype}
<ayame:remove xmlns:ayame="{ayame}">
  before html
</ayame:remove>
<ayame:remove xmlns:ayame="{ayame}" />
<html xmlns="{xhtml}" xmlns:ayame="{ayame}">\
<ayame:remove>
  <body>
    <h1>text</h1>
    <hr />
  </body>
</ayame:remove>\
</html>
<ayame:remove xmlns:ayame="{ayame}" />
<ayame:remove xmlns:ayame="{ayame}">
  after html
</ayame:remove>
""")
        src = io.StringIO(html)
        m = self.load(src, lang='xhtml1')
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


class MarkupRendererTestCase(AyameTestCase):

    def assert_error(self, regex, m):
        for pretty in (False, True):
            renderer = markup.MarkupRenderer()
            with self.assert_raises(ayame.RenderingError) as cm:
                renderer.render(self, m, pretty=pretty)
            self.assert_equal(len(cm.exception.args), 2)
            self.assert_is(cm.exception.args[0], self)
            self.assert_regex(cm.exception.args[1], regex)

    def new_markup(self, lang):
        m = markup.Markup()
        m.xml_decl = {
            u'version': u'1.0',
            u'standalone': u'yes'
        }
        m.lang = lang
        spam = markup.Element(markup.QName(u'spam', u'spam'),
                              attrib={markup.QName(u'spam', u'id'): u'a'},
                              ns={u'': u'spam'})
        eggs = markup.Element(markup.QName(u'spam', u'eggs'))
        eggs.append(0)
        spam.append(eggs)
        m.root = spam
        return m

    def format(self, doc_t, *args, **kwargs):
        kwargs.update(doctype=markup.XHTML1_STRICT,
                      xhtml=markup.XHTML_NS,
                      ayame=markup.AYAME_NS)
        return doc_t.format(*args, **kwargs)

    def test_invalid_type(self):
        m = self.new_markup('xml')
        self.assert_error("^invalid type .* 'int'",
                          m)

    def test_svg(self):
        m = self.new_markup('svg')
        self.assert_error("^unknown .* 'svg'",
                          m)

    def test_unknown_ns_uri(self):
        # unknown namespace URI
        m = self.new_markup('xml')
        m.root.ns.clear()
        del m.root[0][:]
        self.assert_error("^unknown namespace URI 'spam'$",
                          m)

    def test_overwrite_ns_uri(self):
        m = self.new_markup('xml')
        m.root[0].ns[u''] = u'eggs'
        ham = markup.Element(markup.QName(u'spam', u'ham'))
        m.root[0][:] = [ham]
        self.assert_error("namespace URI .*''.* overwritten$",
                          m)

    def test_default_ns_attr(self):
        m = self.new_markup('xml')
        eggs = markup.Element(markup.QName(u'eggs', u'eggs'),
                              attrib={markup.QName(u'eggs', u'a'): u'1',
                                      markup.QName(u'spam', u'a'): u'2'},
                              ns={u'eggs': u'eggs'})
        m.root[:] = [eggs]
        self.assert_error(' default namespace$',
                          m)

    def test_render_xml(self):
        renderer = markup.MarkupRenderer()
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

        # pretty output
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
        self.assert_equal(renderer.render(self, m), xml)

    def test_render_xhtml1(self):
        renderer = markup.MarkupRenderer()
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
    <h1>spam <span class="yellow">eggs</span> ham</h1>
    <blockquote cite="http://example.com/">
      <p>citation</p>
    </blockquote>
    <div class="text">spam <i>eggs</i> ham</div>
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
        <li>Mercury</li>
        <li>Venus</li>
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

        def new_element(name, type=markup.Element.OPEN, **kwargs):
            return markup.Element(self.html_of(name), type=type, **kwargs)

        def new_ayame_element(name, **kwargs):
            kwargs['type'] = markup.Element.OPEN
            return markup.Element(self.ayame_of(name), **kwargs)

        br = new_element(u'br',
                         type=markup.Element.EMPTY)

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

        script = new_element(u'script',
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

        blockquote = new_element(u'blockquote',
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
        remove.append(br.copy())
        remove.append(u'eggs')
        ins.append(remove)
        div.append(ins)
        p = new_element(u'p')
        remove = new_ayame_element(u'remove')
        remove.append(u'ham\n')
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
        p.append(br.copy())
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
        p.append(br.copy())
        em = new_element(u'em')
        em.append(u'Jupiter')
        p.append(em)
        p.append(u' is the fifth planet.')
        remove.append(p)
        div.append(remove)
        ul = new_element(u'ul')
        li = new_element(u'li')
        li.append(u'1')
        li.append(br.copy())
        li.append(u'2')
        li.append(br.copy())
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
        textarea.append(u'Sun\n')
        fieldset.append(textarea)
        form.append(fieldset)
        body.append(form)
        m.root.append(body)

        self.assert_equal(renderer.render(self, m, pretty=True), html)


class ElementTestCase(AyameTestCase):

    def new_element(self, name, attrib=None):
        elem = markup.Element(self.html_of(name),
                              type=markup.Element.OPEN,
                              ns={'': markup.XHTML_NS})
        if attrib:
            for n, v in five.items(attrib):
                elem.attrib[self.html_of(n)] = v
        return elem

    def test_element(self):
        div = self.new_element('div', {'id': 'spam'})
        self.assert_equal(div.qname, self.html_of('div'))
        self.assert_equal(div.attrib, {self.html_of('id'): 'spam'})
        self.assert_equal(div.type, markup.Element.OPEN)
        self.assert_equal(div.ns, {'': markup.XHTML_NS})
        self.assert_equal(div.children, [])
        self.assert_equal(repr(div.qname), '{{{}}}div'.format(markup.XHTML_NS))
        self.assert_regex(repr(div), ' {{{}}}div '.format(markup.XHTML_NS))
        self.assert_equal(len(div), 0)
        self.assert_true(div)

    def test_attrib(self):
        o = object()
        div = self.new_element('div', {'ID': 'spam'})
        div.attrib['CLASS'] = 'eggs'
        div.attrib[o] = 'ham'
        self.assert_equal(list(sorted(five.items(div.attrib), key=lambda t: t[1])),
                          [('class', 'eggs'), (o, 'ham'), (self.html_of('id'), 'spam')])

    def test_set(self):
        p = self.new_element('p')
        br = self.new_element('br')
        p[:1] = ['a', 'b', 'c']
        p[3:] = [br]
        p[4:] = ['d', 'e', 'f']
        self.assert_equal(p.children, ['a', 'b', 'c', br, 'd', 'e', 'f'])

    def test_get(self):
        p = self.new_element('p')
        br = self.new_element('br')
        p[:] = ['a', 'b', 'c', br, 'd', 'e', 'f']
        self.assert_equal(p[:3], ['a', 'b', 'c'])
        self.assert_equal(p[3], br)
        self.assert_equal(p[4:], ['d', 'e', 'f'])
        self.assert_equal(p[:], ['a', 'b', 'c', br, 'd', 'e', 'f'])

    def test_del(self):
        p = self.new_element('p')
        br = self.new_element('br')
        p[:] = ['a', 'b', 'c', br, 'd', 'e', 'f']
        del p[:3]
        self.assert_equal(p.children, [br, 'd', 'e', 'f'])
        del p[0]
        self.assert_equal(p.children, ['d', 'e', 'f'])
        del p[0:]
        self.assert_equal(p.children, [])

    def test_append(self):
        p = self.new_element('p')
        br = self.new_element('br')
        p.append('a')
        p.append('b')
        p.append('c')
        p.append(br)
        p.append('d')
        p.append('e')
        p.append('f')
        self.assert_equal(p.children, ['a', 'b', 'c', br, 'd', 'e', 'f'])

    def test_extend(self):
        p = self.new_element('p')
        br = self.new_element('br')
        p.extend(('a', 'b', 'c', br, 'd', 'e', 'f'))
        self.assert_equal(p.children, ['a', 'b', 'c', br, 'd', 'e', 'f'])

    def test_insert(self):
        p = self.new_element('p')
        br = self.new_element('br')
        p.insert(0, 'f')
        p.insert(0, 'c')
        p.insert(0, 'b')
        p.insert(-1, 'd')
        p.insert(-1, 'e')
        p.insert(0, 'a')
        p.insert(3, br)
        self.assert_equal(p.children, ['a', 'b', 'c', br, 'd', 'e', 'f'])

    def test_remove(self):
        p = self.new_element('p')
        br = self.new_element('br')
        p[:] = ['a', 'b', 'c', br, 'd', 'e', 'f']
        p.remove('a')
        p.remove('b')
        p.remove('c')
        p.remove(br)
        p.remove('d')
        p.remove('e')
        p.remove('f')
        self.assert_equal(p.children, [])

    def test_copy(self):
        div = self._test_dup(lambda div: div.copy())
        self.assert_is_not(div[1][1], div[3])

    def test_pickle(self):
        div = self._test_dup(lambda div: pickle.loads(pickle.dumps(div)))
        self.assert_is(div[1][1], div[3])

    def _test_dup(self, dup):
        div = self.new_element('div', {'id': 'spam'})
        p = self.new_element('p', {'id': 'eggs'})
        br = self.new_element('br')
        br.type = markup.Element.EMPTY
        p[:] = ['ham', br]
        div[:] = ['toast', p, 'beans', br]

        elem = dup(div)
        # div#spam
        self.assert_element_equal(elem, div)
        self.assert_equal(elem[0], 'toast')
        self.assert_equal(elem[2], 'beans')
        # div#spam p#eggs
        self.assert_element_equal(elem[1], p)
        self.assert_equal(elem[1][0], 'ham')
        # div#spam p#eggs br
        self.assert_element_equal(elem[1][1], br)
        # div#spam br
        self.assert_element_equal(elem[3], br)
        return elem

    def test_walk(self):
        root = self.new_element('div', {'id': 'root'})
        it = root.walk()
        self.assert_equal(list(it), [(root, 0)])

        spam = self.new_element('div', {'id': 'spam'})
        eggs = self.new_element('div', {'id': 'eggs'})
        root.extend([spam, eggs])
        it = root.walk()
        self.assert_equal(list(it), [(root, 0),
                                     (spam, 1), (eggs, 1)])

        toast = self.new_element('div', {'id': 'toast'})
        beans = self.new_element('div', {'id': 'beans'})
        spam.extend([toast, beans])
        bacon = self.new_element('div', {'id': 'bacon'})
        sausage = self.new_element('div', {'id': 'sausage'})
        eggs.extend([bacon, sausage])
        it = root.walk()
        self.assert_equal(list(it), [(root, 0),
                                     (spam, 1),
                                     (toast, 2), (beans, 2),
                                     (eggs, 1),
                                     (bacon, 2), (sausage, 2)])

        it = root.walk(step=lambda element, *args: element is not spam)
        self.assert_equal(list(it), [(root, 0),
                                     (spam, 1),
                                     (eggs, 1),
                                     (bacon, 2), (sausage, 2)])

    def test_normalize(self):
        p = self.new_element('p')
        br = self.new_element('br')

        p[:] = ['a', br, 'b', 'c', br, 'd', 'e', 'f']
        p.normalize()
        self.assert_equal(p.children, ['a', br, 'bc', br, 'def'])

        p[:] = ['a', br, 'b', 'c', br, 'd', 'e', 'f', br]
        p.normalize()
        self.assert_equal(p.children, ['a', br, 'bc', br, 'def', br])

        p[:] = [br, 'a', br, 'b', 'c', br, 'd', 'e', 'f']
        p.normalize()
        self.assert_equal(p.children, [br, 'a', br, 'bc', br, 'def'])

        p[:] = [br, 'a', br, 'b', 'c', br, 'd', 'e', 'f', br]
        p.normalize()
        self.assert_equal(p.children, [br, 'a', br, 'bc', br, 'def', br])
