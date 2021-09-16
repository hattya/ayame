#
# test_markup
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import io
import pickle
import textwrap

import ayame
from ayame import markup
from base import AyameTestCase


class MarkupTestCase(AyameTestCase):

    def assertMarkupEqual(self, a, b):
        self.assertIsNot(a, b)
        self.assertIsNot(a.xml_decl, b.xml_decl)
        self.assertEqual(a.xml_decl, b.xml_decl)
        self.assertEqual(a.lang, b.lang)
        self.assertEqual(a.doctype, b.doctype)
        self.assertIsNot(a.root, b.root)
        # html
        self.assertElementEqual(a.root, b.root)
        # html head
        self.assertElementEqual(a.root[0], b.root[0])
        # html head title
        self.assertElementEqual(a.root[0][0], b.root[0][0])
        # html body
        self.assertElementEqual(a.root[1], b.root[1])

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
                             ns={
                                 '': markup.XHTML_NS,
                                 'xml': markup.XML_NS,
                             })
        head = new_element('head')
        head.append(new_element('title'))
        body = new_element('body')
        m.root[:] = [head, body]
        return m

    def test_markup_copy(self):
        m = self.new_xhtml1()
        self.assertMarkupEqual(m, m.copy())

    def test_markup_pickle(self):
        m = self.new_xhtml1()
        self.assertMarkupEqual(m, pickle.loads(pickle.dumps(m)))

    def test_fragment(self):
        br = markup.Element(self.html_of('br'),
                            type=markup.Element.EMPTY)
        f = markup.Fragment(['before', br, 'after'])
        self.assertEqual(len(f), 3)

        f = f.copy()
        self.assertIsInstance(f, markup.Fragment)
        self.assertEqual(len(f), 3)
        self.assertEqual(f[0], 'before')
        self.assertIsNot(f[1], br)
        self.assertEqual(f[2], 'after')

    def test_space(self):
        self.assertIsInstance(markup.Space, str)
        self.assertEqual(repr(markup.Space), 'Space')

    def test_markup_handler(self):
        class MarkupHandler(markup.MarkupHandler):
            @property
            def xml(self):
                return super().xml

            def is_empty(self, element):
                return super().is_empty(element)

            def start_tag(self):
                super().start_tag()
                self.renderer.write('start_tag\n')

            def end_tag(self):
                super().end_tag()
                self.renderer.write('end_tag\n')

        class MarkupRenderer(io.StringIO):
            def peek(self):
                pass

            def writeln(self, *args):
                for a in args:
                    self.write(a)
                self.write('\n')

        with self.assertRaises(TypeError):
            markup.MarkupHandler(None)

        r = MarkupRenderer()
        h = MarkupHandler(r)
        self.assertIsNone(h.xml)
        self.assertIsNone(h.is_empty(None))
        h.doctype('doctype')
        h.start_tag()
        h.end_tag()
        h.text(0, '')
        h.text(0, 'text\n')
        h.indent(0, 0)
        self.assertEqual(r.getvalue(), 'doctype\nstart_tag\nend_tag\ntext\n')

        elem = markup.Element(None)
        elem[:] = ('',) * 3
        h.compile(elem)
        self.assertEqual(elem.children, [])

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
                self.renderer.write('indent\n')

            def compile(self, element):
                self.renderer.write('compile\n')

        r = io.StringIO()
        h = markup.MarkupPrettifier(MarkupHandler(r))
        h._bol = True
        h.text(0, '')
        self.assertTrue(h._bol)
        h.text(0, 'text\n')
        self.assertFalse(h._bol)
        h.indent(0)
        h.compile(None)
        self.assertEqual(r.getvalue(), 'text\nindent\ncompile\n')


class MarkupLoaderTestCase(AyameTestCase):

    def assertError(self, src, pos, regex, **kwargs):
        loader = kwargs.pop('loader', markup.MarkupLoader)()
        with self.assertRaises(ayame.MarkupError) as cm:
            loader.load(self, src, **kwargs)
        self.assertEqual(len(cm.exception.args), 3)
        self.assertIs(cm.exception.args[0], self)
        self.assertEqual(cm.exception.args[1], pos)
        self.assertRegex(cm.exception.args[2], regex)

    def load(self, src, **kwargs):
        return markup.MarkupLoader().load(self, src, **kwargs)

    def format(self, doc_t, *args, **kwargs):
        kwargs.update(doctype=markup.XHTML1_STRICT,
                      xhtml=markup.XHTML_NS,
                      ayame=markup.AYAME_NS)
        return doc_t.format(*args, **kwargs)

    def test_load(self):
        # unknown processing instruction
        src = io.StringIO('<?php echo "Hello World!"?>')
        m = self.load(src, lang='xml')
        self.assertEqual(m.xml_decl, {})
        self.assertEqual(m.lang, 'xml')
        self.assertIsNone(m.doctype)
        self.assertIsNone(m.root)

        # no root element
        src = io.StringIO('&amp; &#38;')
        m = self.load(src, lang='xml')
        self.assertEqual(m.xml_decl, {})
        self.assertEqual(m.lang, 'xml')
        self.assertIsNone(m.doctype)
        self.assertIsNone(m.root)

    def test_unsupported_html(self):
        # xhtml1 frameset
        src = io.StringIO(textwrap.dedent("""\
            <?xml version="1.0"?>
            <!DOCTYPE html PUBLIC "-//W3C/DTD XHTML 1.0 Frameset//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">
        """))
        self.assertError(src, (2, 0), r'^unsupported HTML version$')

    def test_invalid_xml(self):
        for xml, pos, regex in (
            # malformed xml declaration
            ('<?xml standalone="yes"?>',
             (1, 0), r'^malformed XML declaration$'),
            # unquoted xml attributes
            ('<?xml version=1.0?>',
             (1, 0), r'^malformed XML declaration$'),
            # mismatched quotes in xml declaration
            ('<?xml version="1.0\'?>',
             (1, 0), r'^mismatched quotes$'),
            ('<?xml version=\'1.0"?>',
             (1, 0), r'^mismatched quotes$'),
            # no xml declaration
            ('<spam></spam>',
             (1, 0), r'^XML declaration is not found$'),
            # multiple root elements
            ('<?xml version="1.0"?>\n<spam/>\n<eggs/>',
             (3, 0), r' multiple root elements$'),
            ('<?xml version="1.0"?>\n<spam></spam>\n<eggs></eggs>',
             (3, 0), r' multiple root elements$'),
            # omitted end tag for root element
            ('<?xml version="1.0"?>\n<spam>',
             (2, 6), r"^end tag .* '{}spam' omitted$"),
            # mismatched tag
            ('<?xml version="1.0"?>\n<spam></eggs>',
             (2, 6), r"^end tag .* '{}eggs' .* not open$"),
            # attribute duplication
            ('<?xml version="1.0"?>\n<spam a="1" a="2"/>',
             (2, 0), r"^attribute '{}a' already exists$"),
        ):
            self.assertError(io.StringIO(xml), pos, regex, lang='xml')

    def test_empty_xml(self):
        src = io.StringIO('<?xml version="1.0"?>')
        m = self.load(src, lang='xml')
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xml')
        self.assertIsNone(m.doctype)
        self.assertIsNone(m.root)

    def test_xml(self):
        xml = (
            '<?xml version="1.0"?>'
            '<!DOCTYPE spam SYSTEM "spam.dtd">'
            '<spam xmlns="spam" id="spam">'
            '&amp;'
            '<eggs/>'
            '&#38;'
            'x'
            '</spam>'
        )
        src = io.StringIO(xml)
        m = self.load(src, lang='xml')
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xml')
        self.assertEqual(m.doctype, '<!DOCTYPE spam SYSTEM "spam.dtd">')
        self.assertTrue(m.root)

        spam = m.root
        self.assertEqual(spam.qname, markup.QName('spam', 'spam'))
        self.assertEqual(spam.attrib, {markup.QName('spam', 'id'): 'spam'})
        self.assertEqual(spam.type, markup.Element.OPEN)
        self.assertEqual(spam.ns, {
            '': 'spam',
            'xml': markup.XML_NS,
        })
        self.assertEqual(len(spam), 3)
        self.assertEqual(spam[0], '&amp;')
        self.assertEqual(spam[2], '&#38;x')

        eggs = spam[1]
        self.assertEqual(eggs.qname, markup.QName('spam', 'eggs'))
        self.assertEqual(eggs.attrib, {})
        self.assertEqual(eggs.type, markup.Element.EMPTY)
        self.assertEqual(eggs.ns, {})
        self.assertEqual(eggs.children, [])

    def test_xml_with_prefix(self):
        xml = (
            '<?xml version="1.0"?>'
            '<spam xmlns="spam" xmlns:eggs="eggs">'
            '<eggs:eggs/>'
            '</spam>'
        )
        src = io.StringIO(xml)
        m = self.load(src, lang='xml')
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xml')
        self.assertIsNone(m.doctype)
        self.assertTrue(m.root)

        spam = m.root
        self.assertEqual(spam.qname, markup.QName('spam', 'spam'))
        self.assertEqual(spam.attrib, {})
        self.assertEqual(spam.type, markup.Element.OPEN)
        self.assertEqual(spam.ns, {
            '': 'spam',
            'eggs': 'eggs',
            'xml': markup.XML_NS,
        })
        self.assertEqual(len(spam), 1)

        eggs = spam[0]
        self.assertEqual(eggs.qname, markup.QName('eggs', 'eggs'))
        self.assertEqual(eggs.attrib, {})
        self.assertEqual(eggs.type, markup.Element.EMPTY)
        self.assertEqual(eggs.ns, {})
        self.assertEqual(eggs.children, [])

        # no default namespace
        class Loader(markup.MarkupLoader):
            def _new_element(self, *args, **kwargs):
                elem = super()._new_element(*args, **kwargs)
                elem.ns.pop('', None)
                return elem

        src = io.StringIO(xml)
        self.assertError(src, (1, 70), r' no default namespace$', lang='xml', loader=Loader)

        # no eggs namespace
        class Loader(markup.MarkupLoader):
            def _new_element(self, *args, **kwargs):
                elem = super()._new_element(*args, **kwargs)
                elem.ns.pop('eggs', None)
                return elem

        src = io.StringIO(xml)
        self.assertError(src, (1, 58), r"^unknown .* prefix 'eggs'$", lang='xml', loader=Loader)

    def test_invalid_xhtml1(self):
        for html_t, pos, regex in (
            # no xml declaration
            ("""\
                {doctype}
                <html xmlns="http://www.w3.org/1999/xhtml">
                </html>
             """,
             (2, 0), r'^XML declaration is not found$'),
            # multiple root elements
            ("""\
                <?xml version="1.0"?>
                {doctype}
                <html xmlns="http://www.w3.org/1999/xhtml" />
                <html xmlns="http://www.w3.org/1999/xhtml" />
             """,
             (4, 0), r' multiple root elements$'),
            # omitted end tag for root element
            ("""\
                <?xml version="1.0"?>
                {doctype}
                <html xmlns="http://www.w3.org/1999/xhtml">
             """,
             (4, 0), r"^end tag .* '{.*}html' omitted$"),
        ):
            self.assertError(io.StringIO(self.format(textwrap.dedent(html_t))), pos, regex, lang='xhtml1')

    def test_xhtml1(self):
        html = self.format(
            '<?xml version="1.0"?>'
            '{doctype}'
            '<html xmlns="{xhtml}">'
            '<head>'
            '<title>title</title>'
            '</head>'
            '<body>'
            '<h1>text</h1>'
            '<p>line1<br />line2</p>'
            '</body>'
            '</html>'
        )
        src = io.StringIO(html)
        m = self.load(src, lang='xhtml1')
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
        })
        self.assertEqual(len(html), 2)

        head = html[0]
        self.assertEqual(head.qname, self.html_of('head'))
        self.assertEqual(head.attrib, {})
        self.assertEqual(head.type, markup.Element.OPEN)
        self.assertEqual(head.ns, {})
        self.assertEqual(len(head), 1)

        title = head[0]
        self.assertEqual(title.qname, self.html_of('title'))
        self.assertEqual(title.attrib, {})
        self.assertEqual(title.type, markup.Element.OPEN)
        self.assertEqual(title.ns, {})
        self.assertEqual(title.children, ['title'])

        body = html[1]
        self.assertEqual(body.qname, self.html_of('body'))
        self.assertEqual(body.attrib, {})
        self.assertEqual(body.type, markup.Element.OPEN)
        self.assertEqual(body.ns, {})
        self.assertEqual(len(body), 2)

        h1 = body[0]
        self.assertEqual(h1.qname, self.html_of('h1'))
        self.assertEqual(h1.attrib, {})
        self.assertEqual(h1.type, markup.Element.OPEN)
        self.assertEqual(h1.ns, {})
        self.assertEqual(h1.children, ['text'])

        p = body[1]
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {})
        self.assertEqual(len(p), 3)
        self.assertEqual(p[0], 'line1')
        self.assertEqual(p[2], 'line2')

        br = p[1]
        self.assertEqual(br.qname, self.html_of('br'))
        self.assertEqual(br.attrib, {})
        self.assertEqual(br.type, markup.Element.EMPTY)
        self.assertEqual(br.ns, {})
        self.assertEqual(br.children, [])

    def test_ayame_remove(self):
        # descendant of root element
        html = self.format(textwrap.dedent("""\
            <?xml version="1.0"?>
            {doctype}
            <html xmlns="{xhtml}" xmlns:ayame="{ayame}"><ayame:remove>
              <body>
                <h1>text</h1>
                <hr />
              </body>
            </ayame:remove></html>
        """))
        src = io.StringIO(html)
        m = self.load(src, lang='xhtml1')
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
        self.assertEqual(html.children, [])

        # multiple root elements
        html = self.format(textwrap.dedent("""\
            <?xml version="1.0"?>
            {doctype}
            <ayame:remove xmlns:ayame="{ayame}">
              before html
            </ayame:remove>
            <ayame:remove xmlns:ayame="{ayame}" />
            <html xmlns="{xhtml}" xmlns:ayame="{ayame}"><ayame:remove>
              <body>
                <h1>text</h1>
                <hr />
              </body>
            </ayame:remove></html>
            <ayame:remove xmlns:ayame="{ayame}" />
            <ayame:remove xmlns:ayame="{ayame}">
              after html
            </ayame:remove>
        """))
        src = io.StringIO(html)
        m = self.load(src, lang='xhtml1')
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
        self.assertEqual(html.children, [])


class MarkupRendererTestCase(AyameTestCase):

    def assertError(self, m, regex):
        for pretty in (False, True):
            renderer = markup.MarkupRenderer()
            with self.assertRaises(ayame.RenderingError) as cm:
                renderer.render(self, m, pretty=pretty)
            self.assertEqual(len(cm.exception.args), 2)
            self.assertIs(cm.exception.args[0], self)
            self.assertRegex(cm.exception.args[1], regex)

    def new_markup(self, lang):
        m = markup.Markup()
        m.xml_decl = {
            'version': '1.0',
            'standalone': 'yes',
        }
        m.lang = lang
        spam = markup.Element(markup.QName('spam', 'spam'),
                              attrib={markup.QName('spam', 'id'): 'a'},
                              ns={'': 'spam'})
        eggs = markup.Element(markup.QName('spam', 'eggs'))
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
        self.assertError(m, r"^invalid type .* 'int'")

    def test_svg(self):
        m = self.new_markup('svg')
        self.assertError(m, r"^unknown .* 'svg'")

    def test_unknown_ns_uri(self):
        # unknown namespace URI
        m = self.new_markup('xml')
        m.root.ns.clear()
        del m.root[0][:]
        self.assertError(m, r"^unknown namespace URI 'spam'$")

    def test_overwrite_ns_uri(self):
        m = self.new_markup('xml')
        m.root[0].ns[''] = 'eggs'
        ham = markup.Element(markup.QName('spam', 'ham'))
        m.root[0][:] = [ham]
        self.assertError(m, r"namespace URI .*''.* overwritten$")

    def test_default_ns_attr(self):
        m = self.new_markup('xml')
        eggs = markup.Element(markup.QName('eggs', 'eggs'),
                              attrib={
                                  markup.QName('eggs', 'a'): '1',
                                  markup.QName('spam', 'a'): '2',
                              },
                              ns={'eggs': 'eggs'})
        m.root[:] = [eggs]
        self.assertError(m, r' default namespace$')

    def test_render_xml(self):
        renderer = markup.MarkupRenderer()
        xml = textwrap.dedent("""\
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
        """).encode('iso-8859-1')

        # pretty output
        m = markup.Markup()
        m.xml_decl = {
            'version': '1.0',
            'encoding': 'iso-8859-1',
        }
        m.lang = 'xml'
        m.doctype = '<!DOCTYPE spam SYSTEM "spam.dtd">'
        m.root = markup.Element(markup.QName('spam', 'spam'),
                                attrib={markup.QName('spam', 'a'): 'a'},
                                type=markup.Element.OPEN,
                                ns={'': 'spam'})
        m.root.append('\n'
                      '    a\n'
                      '    \n')
        eggs = markup.Element(markup.QName('spam', 'eggs'),
                              type=markup.Element.EMPTY)
        m.root.append(eggs)
        m.root.append('\n'
                      '    b\n'
                      '    c\n')
        eggs = markup.Element(markup.QName('eggs', 'eggs'),
                              attrib={
                                  markup.QName('eggs', 'a'): '1',
                                  markup.QName('ham', 'a'): '2',
                              },
                              type=markup.Element.OPEN,
                              ns={
                                  'eggs': 'eggs',
                                  'ham': 'ham',
                              })
        ham = markup.Element(markup.QName('spam', 'ham'),
                             type=markup.Element.OPEN)
        ham.append('\n'
                   '    1\n'
                   '    2\n')
        eggs.append(ham)
        m.root.append(eggs)
        self.assertEqual(renderer.render(self, m, pretty=True), xml)

        # raw output
        m = markup.Markup()
        m.xml_decl = {
            'version': '1.0',
            'encoding': 'iso-8859-1',
        }
        m.lang = 'xml'
        m.doctype = '<!DOCTYPE spam SYSTEM "spam.dtd">'
        m.root = markup.Element(markup.QName('spam', 'spam'),
                                attrib={markup.QName('spam', 'a'): 'a'},
                                type=markup.Element.OPEN,
                                ns={'': 'spam'})
        m.root.append('\n'
                      '  a\n'
                      '  ')
        eggs = markup.Element(markup.QName('spam', 'eggs'))
        eggs.type = markup.Element.EMPTY
        m.root.append(eggs)
        m.root.append('\n'
                      '  b\n'
                      '  c\n'
                      '  ')
        eggs = markup.Element(markup.QName('eggs', 'eggs'),
                              attrib={
                                  markup.QName('eggs', 'a'): '1',
                                  markup.QName('ham', 'a'): '2',
                              },
                              type=markup.Element.OPEN,
                              ns={
                                  'eggs': 'eggs',
                                  'ham': 'ham',
                              })
        eggs.append('\n'
                    '    ')
        ham = markup.Element(markup.QName('spam', 'ham'),
                             type=markup.Element.OPEN)
        ham.append('\n'
                   '      1\n'
                   '      2\n'
                   '    ')
        eggs.append(ham)
        eggs.append('\n'
                    '  ')
        m.root.append(eggs)
        m.root.append('\n')
        self.assertEqual(renderer.render(self, m), xml)

    def test_render_xhtml1(self):
        renderer = markup.MarkupRenderer()
        html = self.format(textwrap.dedent("""\
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
        """)).encode('iso-8859-1')

        def new_element(name, type=markup.Element.OPEN, **kwargs):
            return markup.Element(self.html_of(name), type=type, **kwargs)

        def new_ayame_element(name, **kwargs):
            kwargs['type'] = markup.Element.OPEN
            return markup.Element(self.ayame_of(name), **kwargs)

        br = new_element('br',
                         type=markup.Element.EMPTY)

        m = markup.Markup()
        m.xml_decl = {
            'version': '1.0',
            'encoding': 'iso-8859-1',
        }
        m.lang = 'xhtml1'
        m.doctype = markup.XHTML1_STRICT
        m.root = new_element('html',
                             attrib={self.xml_of('lang'): 'en'},
                             ns={
                                 'a': markup.XML_NS,
                                 'b': markup.XHTML_NS,
                                 'ayame': markup.AYAME_NS,
                             })

        head = new_element('head')
        meta = new_element('meta',
                           attrib={
                               self.html_of('name'): 'keywords',
                               self.html_of('content'): '',
                           })
        meta.append('a')
        head.append(meta)

        title = new_element('title')
        title.append('title')
        span = new_element('span')
        title.append(span)
        head.append(title)

        style = new_element('style',
                            attrib={self.html_of('type'): 'text/css'})
        style.append('\n'
                     '      h1 {\n'
                     '        font-size: 120%;\n'
                     '      }\n'
                     '\n'
                     '      p {\n'
                     '        font-size: 90%;\n'
                     '      }\n'
                     '\n')
        head.append(style)

        script = new_element('script',
                             attrib={self.html_of('type'): 'text/javascript'})
        script.append('\n'
                      '     <!--\n'
                      '     var x = 0;\n'
                      '     var y = 0;\n'
                      '     // -->\n'
                      '\n')
        head.append(script)
        m.root.append(head)

        body = new_element('body')
        remove = new_ayame_element('remove')
        p = new_element('p')
        p.append('Hello World!')
        remove.append(p)
        body.append(remove)

        h1 = new_element('h1')
        h1.append('\n'
                  '  spam\n')
        span = new_element('span',
                           attrib={self.html_of('class'): 'yellow'})
        span.append('\n'
                    '  eggs  \n')
        h1.append(span)
        h1.append('\n'
                  '  ham  \n')
        body.append(h1)

        blockquote = new_element('blockquote',
                                 attrib={self.html_of('cite'): 'http://example.com/'})
        blockquote.append('before')
        p = new_element('p')
        p.append('citation')
        blockquote.append(p)
        blockquote.append('after')
        body.append(blockquote)

        div = new_element('div',
                          attrib={self.html_of('class'): 'text'})
        div.append('\n'
                   'spam   \n'
                   '\n')
        i = new_element('i')
        i.append('eggs')
        div.append(i)
        div.append('  ham')
        body.append(div)

        div = new_element('div',
                          attrib={self.html_of('class'): 'ayame'})
        ins = new_element('ins')
        remove = new_ayame_element('remove')
        remove.append('spam')
        remove.append(br.copy())
        remove.append('eggs')
        ins.append(remove)
        div.append(ins)
        p = new_element('p')
        remove = new_ayame_element('remove')
        remove.append('ham\n')
        p.append(remove)
        p.append('toast')
        div.append(p)
        ul = new_element('ul')
        container = new_ayame_element('container',
                                      attrib={markup.AYAME_ID: 'a'})
        li = new_element('li')
        li.append('spam')
        container.append(li)
        li = new_element('li')
        li.append('eggs')
        container.append(li)
        ul.append(container)
        div.append(ul)
        body.append(div)

        div = new_element('div',
                          attrib={self.html_of('class'): 'block'})
        div.append('Planets')
        ul = new_element('ul')
        li = new_element('li')
        li.append('\n'
                  ' Mercury '
                  '\n')
        ul.append(li)
        li = new_element('li')
        li.append('  Venus  ')
        ul.append(li)
        li = new_element('li')
        li.append('Earth')
        ul.append(li)
        div.append(ul)
        div.append('\n')
        body.append(div)

        div = new_element('div',
                          attrib={self.html_of('class'): 'inline-ins-del'})
        p = new_element('p')
        del_ = new_element('del')
        del_.append('old')
        p.append(del_)
        ins = new_element('ins')
        ins.append('new')
        p.append(ins)
        div.append(p)
        body.append(div)

        div = new_element('div',
                          attrib={self.html_of('class'): 'block-ins-del'})
        del_ = new_element('del')
        pre = new_element('pre')
        pre.append('old')
        del_.append(pre)
        div.append(del_)
        ins = new_element('ins')
        pre = new_element('pre')
        pre.append('new')
        ins.append(pre)
        div.append(ins)
        body.append(div)

        pre = new_element('pre')
        pre.append('\n'
                   '  * 1\n'
                   '    * 2\n'
                   '      * 3\n'
                   '    * 4\n'
                   '  * 5\n')
        body.append(pre)

        div = new_element('div',
                          attrib={self.html_of('class'): 'br'})
        h2 = new_element('h2')
        h2.append('The Solar System')
        div.append(h2)
        p = new_element('p')
        em = new_element('em')
        em.append('Mercury')
        p.append(em)
        p.append(' is the first planet.')
        p.append(br.copy())
        p.append('\n')
        em = new_element('em')
        em.append('Venus')
        p.append(em)
        p.append(' is the second planet.')
        p.append('\n')
        div.append(p)
        div.append('\n')
        p = new_element('p')
        em = new_element('em')
        em.append('Earth')
        p.append(em)
        p.append(' is the third planet.')
        div.append(p)
        remove = new_ayame_element('remove')
        p = new_element('p')
        em = new_element('em')
        em.append('Mars')
        p.append(em)
        p.append(' is the fourth planet.')
        p.append(br.copy())
        em = new_element('em')
        em.append('Jupiter')
        p.append(em)
        p.append(' is the fifth planet.')
        remove.append(p)
        div.append(remove)
        ul = new_element('ul')
        li = new_element('li')
        li.append('1')
        li.append(br.copy())
        li.append('2')
        li.append(br.copy())
        li.append('3')
        ul.append(li)
        div.append(ul)
        div.append('\n')
        body.append(div)

        form = new_element('form',
                           attrib={
                               self.html_of('action'): '/',
                               self.html_of('method'): 'post',
                           })
        fieldset = new_element('fieldset')
        legend = new_element('legend')
        legend.append('form')
        fieldset.append(legend)
        textarea = new_element('textarea')
        textarea.append('Sun\n')
        fieldset.append(textarea)
        form.append(fieldset)
        body.append(form)
        m.root.append(body)

        self.assertEqual(renderer.render(self, m, pretty=True), html)


class ElementTestCase(AyameTestCase):

    def new_element(self, name, attrib=None):
        elem = markup.Element(self.html_of(name),
                              type=markup.Element.OPEN,
                              ns={'': markup.XHTML_NS})
        if attrib:
            for n, v in attrib.items():
                elem.attrib[self.html_of(n)] = v
        return elem

    def test_element(self):
        div = self.new_element('div', {'id': 'spam'})
        self.assertEqual(div.qname, self.html_of('div'))
        self.assertEqual(div.attrib, {self.html_of('id'): 'spam'})
        self.assertEqual(div.type, markup.Element.OPEN)
        self.assertEqual(div.ns, {'': markup.XHTML_NS})
        self.assertEqual(div.children, [])
        self.assertEqual(repr(div.qname), f'{{{markup.XHTML_NS}}}div')
        self.assertRegex(repr(div), fr' {{{markup.XHTML_NS}}}div ')
        self.assertEqual(len(div), 0)
        self.assertTrue(div)

    def test_attrib(self):
        o = object()
        div = self.new_element('div', {'ID': 'spam'})
        div.attrib['CLASS'] = 'eggs'
        div.attrib[o] = 'ham'
        self.assertEqual(list(sorted(div.attrib.items(), key=lambda t: t[1])), [
            ('class', 'eggs'),
            (o, 'ham'),
            (self.html_of('id'), 'spam'),
        ])

    def test_set(self):
        p = self.new_element('p')
        br = self.new_element('br')
        p[:1] = ['a', 'b', 'c']
        p[3:] = [br]
        p[4:] = ['d', 'e', 'f']
        self.assertEqual(p.children, ['a', 'b', 'c', br, 'd', 'e', 'f'])

    def test_get(self):
        p = self.new_element('p')
        br = self.new_element('br')
        p[:] = ['a', 'b', 'c', br, 'd', 'e', 'f']
        self.assertEqual(p[:3], ['a', 'b', 'c'])
        self.assertEqual(p[3], br)
        self.assertEqual(p[4:], ['d', 'e', 'f'])
        self.assertEqual(p[:], ['a', 'b', 'c', br, 'd', 'e', 'f'])

    def test_del(self):
        p = self.new_element('p')
        br = self.new_element('br')
        p[:] = ['a', 'b', 'c', br, 'd', 'e', 'f']
        del p[:3]
        self.assertEqual(p.children, [br, 'd', 'e', 'f'])
        del p[0]
        self.assertEqual(p.children, ['d', 'e', 'f'])
        del p[0:]
        self.assertEqual(p.children, [])

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
        self.assertEqual(p.children, ['a', 'b', 'c', br, 'd', 'e', 'f'])

    def test_extend(self):
        p = self.new_element('p')
        br = self.new_element('br')
        p.extend(('a', 'b', 'c', br, 'd', 'e', 'f'))
        self.assertEqual(p.children, ['a', 'b', 'c', br, 'd', 'e', 'f'])

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
        self.assertEqual(p.children, ['a', 'b', 'c', br, 'd', 'e', 'f'])

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
        self.assertEqual(p.children, [])

    def test_copy(self):
        div = self._test_dup(lambda div: div.copy())
        self.assertIsNot(div[1][1], div[3])

    def test_pickle(self):
        div = self._test_dup(lambda div: pickle.loads(pickle.dumps(div)))
        self.assertIs(div[1][1], div[3])

    def _test_dup(self, dup):
        div = self.new_element('div', {'id': 'spam'})
        p = self.new_element('p', {'id': 'eggs'})
        br = self.new_element('br')
        br.type = markup.Element.EMPTY
        p[:] = ['ham', br]
        div[:] = ['toast', p, 'beans', br]

        elem = dup(div)
        # div#spam
        self.assertElementEqual(elem, div)
        self.assertEqual(elem[0], 'toast')
        self.assertEqual(elem[2], 'beans')
        # div#spam p#eggs
        self.assertElementEqual(elem[1], p)
        self.assertEqual(elem[1][0], 'ham')
        # div#spam p#eggs br
        self.assertElementEqual(elem[1][1], br)
        # div#spam br
        self.assertElementEqual(elem[3], br)
        return elem

    def test_walk(self):
        root = self.new_element('div', {'id': 'root'})
        it = root.walk()
        self.assertEqual(list(it), [(root, 0)])

        spam = self.new_element('div', {'id': 'spam'})
        eggs = self.new_element('div', {'id': 'eggs'})
        root.extend([spam, eggs])
        it = root.walk()
        self.assertEqual(list(it), [
            (root, 0),
            (spam, 1), (eggs, 1),
        ])

        toast = self.new_element('div', {'id': 'toast'})
        beans = self.new_element('div', {'id': 'beans'})
        spam.extend([toast, beans])
        bacon = self.new_element('div', {'id': 'bacon'})
        sausage = self.new_element('div', {'id': 'sausage'})
        eggs.extend([bacon, sausage])
        it = root.walk()
        self.assertEqual(list(it), [
            (root, 0),
            (spam, 1),
            (toast, 2), (beans, 2),
            (eggs, 1),
            (bacon, 2), (sausage, 2),
        ])

        it = root.walk(step=lambda element, *args: element is not spam)
        self.assertEqual(list(it), [
            (root, 0),
            (spam, 1),
            (eggs, 1),
            (bacon, 2), (sausage, 2),
        ])

    def test_normalize(self):
        p = self.new_element('p')
        br = self.new_element('br')

        p[:] = ['a', br, 'b', 'c', br, 'd', 'e', 'f']
        p.normalize()
        self.assertEqual(p.children, ['a', br, 'bc', br, 'def'])

        p[:] = ['a', br, 'b', 'c', br, 'd', 'e', 'f', br]
        p.normalize()
        self.assertEqual(p.children, ['a', br, 'bc', br, 'def', br])

        p[:] = [br, 'a', br, 'b', 'c', br, 'd', 'e', 'f']
        p.normalize()
        self.assertEqual(p.children, [br, 'a', br, 'bc', br, 'def'])

        p[:] = [br, 'a', br, 'b', 'c', br, 'd', 'e', 'f', br]
        p.normalize()
        self.assertEqual(p.children, [br, 'a', br, 'bc', br, 'def', br])
