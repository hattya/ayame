#
# test_markup
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import collections.abc
import io
import pickle
import textwrap
import unittest.mock

import ayame
from ayame import markup
from base import AyameTestCase, ElementBuilder


class MarkupTestCase(AyameTestCase):

    def test_markup_copy(self):
        def dup(m):
            return m.copy()

        self._test_markup_dup(dup, False)
        self._test_markup_dup(dup, True)

    def test_markup_pickle(self):
        def dup(m):
            return pickle.loads(pickle.dumps(m))

        self._test_markup_dup(dup, False)
        self._test_markup_dup(dup, True)

    def _test_markup_dup(self, dup, root):
        m = markup.Markup()
        m.xml_decl = {'version': '1.0'}
        m.lang = 'xhtml1'
        m.doctype = markup.XHTML1_STRICT
        if root:
            b = ElementBuilder(markup.XHTML_NS)
            with b.open('html',
                        ns={
                            '': markup.XHTML_NS,
                            'xml': markup.XML_NS,
                        }):
                with b.open('head'):
                    with b.open('title'):
                        pass
                with b.open('body'):
                    pass
            m.root = b.root

        c = dup(m)
        self.assertIsNot(m, c)
        self.assertIsNot(m.xml_decl, c.xml_decl)
        self.assertEqual(m.xml_decl, c.xml_decl)
        self.assertEqual(m.lang, c.lang)
        self.assertEqual(m.doctype, c.doctype)
        if root:
            self.assertIsNot(m.root, c.root)
            self.assertElementEqual(m.root, c.root)
        else:
            self.assertIsNone(m.root)
            self.assertIsNone(c.root)

    def test_fragment(self):
        br = markup.Element(self.html_of('br'),
                            type=markup.Element.EMPTY)
        f = markup.Fragment(('before', br, 'after'))
        self.assertEqual(len(f), 3)

        c = f.copy()
        self.assertIsNot(c, f)
        self.assertIsInstance(c, markup.Fragment)
        self.assertEqual(len(c), 3)
        self.assertEqual(c[0], 'before')
        self.assertIsNot(c[1], br)
        self.assertEqual(c[2], 'after')

    def test_space(self):
        self.assertIsInstance(markup.Space, str)
        self.assertEqual(repr(markup.Space), 'Space')

    def test_markup_handler(self):
        class MarkupHandler(markup.MarkupHandler):
            @property
            def xml(self):
                return super().xml

            def is_empty(self, el):
                return super().is_empty(el)

            def start_tag(self):
                super().start_tag()

            def end_tag(self):
                super().end_tag()

        with self.assertRaises(TypeError):
            markup.MarkupHandler(markup.MarkupRenderer())

        r = markup.MarkupRenderer()
        h = MarkupHandler(r)
        with self.assertRaises(NotImplementedError):
            h.xml
        with self.assertRaises(NotImplementedError):
            h.is_empty(self.empty_element())
        with self.assertRaises(NotImplementedError):
            h.start_tag()
        with self.assertRaises(NotImplementedError):
            h.end_tag()

        r._buf = io.StringIO()
        h.doctype('')
        h.text(0, '')
        self.assertEqual(r._buf.getvalue(), '')

        h.doctype('doctype')
        h.text(0, 'text')
        self.assertEqual(r._buf.getvalue(), 'doctype\ntext')

        r.push(0, self.empty_element())
        self.assertFalse(h.indent(0, 1))
        self.assertEqual(h.compile(self.empty_element()), h.INDENT_AROUND)

    def test_markup_prettifier(self):
        class MarkupHandler(markup.MarkupHandler):
            @property
            def xml(self):
                return self._xml

            def is_empty(self, el):
                return self._empty

            def start_tag(self):
                self.renderer.writeln('start_tag')

            def end_tag(self):
                self.renderer.writeln('end_tag')

        r = markup.MarkupRenderer()
        h = markup.MarkupPrettifier(MarkupHandler(r))
        el = self.empty_element()

        h._handler._xml = h._handler._empty = False
        self.assertFalse(h.xml)
        self.assertFalse(h.is_empty(el))

        h._handler._xml = h._handler._empty = True
        self.assertTrue(h.xml)
        self.assertTrue(h.is_empty(el))

        r._buf = io.StringIO()
        r.push(0, el)
        h.doctype('doctype')
        h.start_tag()
        h.end_tag()
        h.text(0, 'text\n')
        self.assertEqual(r._buf.getvalue(), 'doctype\nstart_tag\nend_tag\ntext\n')

        self.assertFalse(h.indent(0))
        self.assertEqual(h.compile(el), h.INDENT_AROUND)


class ElementTestCase(AyameTestCase):

    def new_element(self, name, attrib=None, empty=False):
        _ = self.html_of
        return markup.Element(_(name),
                              attrib={_(n): v for n, v in attrib.items()} if attrib else None,
                              type=markup.Element.EMPTY if empty else markup.Element.OPEN,
                              ns={
                                  '': markup.XHTML_NS,
                                  'xml': markup.XML_NS
                              })

    def test_element(self):
        el = self.empty_element()
        self.assertEqual(el.qname, markup.QName('', ''))
        self.assertEqual(el.attrib, {})
        self.assertIsNone(el.type)
        self.assertEqual(el.ns, {})
        self.assertEqual(el.children, [])
        self.assertEqual(repr(el.qname), '{}')
        self.assertRegex(repr(el), r' {} ')
        self.assertEqual(len(el), 0)
        self.assertTrue(el)
        self.assertIsInstance(el, collections.abc.Iterable)
        self.assertEqual(list(el), [])

        p = self.new_element('p', {'id': 'spam'})
        self.assertEqual(p.qname, self.html_of('p'))
        self.assertEqual(p.attrib, {self.html_of('id'): 'spam'})
        self.assertEqual(p.type, markup.Element.OPEN)
        self.assertEqual(p.ns, {
            '': markup.XHTML_NS,
            'xml': markup.XML_NS,
        })
        self.assertEqual(p.children, [])
        self.assertEqual(repr(p.qname), f'{{{markup.XHTML_NS}}}p')
        self.assertRegex(repr(p), fr' {{{markup.XHTML_NS}}}p ')
        self.assertEqual(len(p), 0)
        self.assertTrue(p)
        self.assertIsInstance(el, collections.abc.Iterable)
        self.assertEqual(list(el), [])

    def test_attrib(self):
        p = self.new_element('p', {'ID': 'spam'})
        p.attrib['CLASS'] = 'eggs'
        self.assertEqual(sorted(p.attrib.items(), key=lambda t: t[1]), [
            ('class', 'eggs'),
            (self.html_of('id'), 'spam'),
        ])

    def test_get(self):
        p = self.new_element('p')
        br = self.new_element('br', empty=True)
        p.children[:] = ['a', 'b', 'c', br, 'd', 'e', 'f']
        self.assertEqual(p[:3], ['a', 'b', 'c'])
        self.assertEqual(p[3], br)
        self.assertEqual(p[4:], ['d', 'e', 'f'])
        self.assertEqual(p[:], ['a', 'b', 'c', br, 'd', 'e', 'f'])

    def test_set(self):
        p = self.new_element('p')
        br = self.new_element('br', empty=True)
        p[:1] = ['a', 'b', 'c']
        p[3:] = [br]
        p[4:] = ['d', 'e', 'f']
        self.assertEqual(p.children, ['a', 'b', 'c', br, 'd', 'e', 'f'])

    def test_del(self):
        p = self.new_element('p')
        br = self.new_element('br', empty=True)
        p.children[:] = ['a', 'b', 'c', br, 'd', 'e', 'f']
        del p[:3]
        self.assertEqual(p.children, [br, 'd', 'e', 'f'])
        del p[0]
        self.assertEqual(p.children, ['d', 'e', 'f'])
        del p[0:]
        self.assertEqual(p.children, [])

    def test_iter(self):
        p = self.new_element('p')
        br = self.new_element('br', empty=True)
        p.children[:] = ['a', 'b', 'c', br, 'd', 'e', 'f']
        self.assertEqual(list(p), ['a', 'b', 'c', br, 'd', 'e', 'f'])

    def test_copy(self):
        self._test_dup(lambda el: el.copy())

    def test_pickle(self):
        self._test_dup(lambda el: pickle.loads(pickle.dumps(el)))

    def _test_dup(self, dup):
        spam = self.new_element('p', {'id': 'spam'})
        eggs = self.new_element('p', {'id': 'eggs'})
        br = self.new_element('br', empty=True)
        eggs[:] = ['ham', br]
        spam[:] = ['toast', eggs, 'beans', br]
        self.assertElementEqual(spam, dup(spam))

    def test_append(self):
        p = self.new_element('p')
        br = self.new_element('br', empty=True)
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
        br = self.new_element('br', empty=True)
        p.extend(('a', 'b', 'c', br, 'd', 'e', 'f'))
        self.assertEqual(p.children, ['a', 'b', 'c', br, 'd', 'e', 'f'])

    def test_insert(self):
        p = self.new_element('p')
        br = self.new_element('br', empty=True)
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
        br = self.new_element('br', empty=True)
        p[:] = ['a', 'b', 'c', br, 'd', 'e', 'f']
        p.remove('a')
        p.remove('b')
        p.remove('c')
        p.remove(br)
        p.remove('d')
        p.remove('e')
        p.remove('f')
        self.assertEqual(p.children, [])

    def test_walk(self):
        spam = self.new_element('p', {'id': 'spam'})
        self.assertEqual(list(spam.walk()), [
            (spam, 0),
        ])

        eggs = self.new_element('p', {'id': 'eggs'})
        ham = self.new_element('p', {'id': 'ham'})
        spam.extend([eggs, ham])
        self.assertEqual(list(spam.walk()), [
            (spam, 0),
            (eggs, 1), (ham, 1),
        ])

        beans = self.new_element('p', {'id': 'beans'})
        bacon = self.new_element('p', {'id': 'bacon'})
        eggs.extend([beans, bacon])
        sausage = self.new_element('p', {'id': 'sausage'})
        tomato = self.new_element('p', {'id': 'tomato'})
        ham.extend([sausage, tomato])
        self.assertEqual(list(spam.walk()), [
            (spam, 0),
            (eggs, 1),
            (beans, 2), (bacon, 2),
            (ham, 1),
            (sausage, 2), (tomato, 2),
        ])

        self.assertEqual(list(spam.walk(step=lambda el, *a: el is not eggs)), [
            (spam, 0),
            (eggs, 1),
            (ham, 1),
            (sausage, 2), (tomato, 2),
        ])

    def test_normalize(self):
        p = self.new_element('p')
        br = self.new_element('br', empty=True)

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


class MarkupLoaderTestCase(AyameTestCase):

    def assertError(self, src, pos, regex, **kwargs):
        ml = kwargs.pop('loader', markup.MarkupLoader)()
        with self.assertRaises(ayame.MarkupError) as cm:
            ml.load(self, src, **kwargs)
        self.assertEqual(len(cm.exception.args), 3)
        self.assertIs(cm.exception.args[0], self)
        self.assertEqual(cm.exception.args[1], pos)
        self.assertRegex(cm.exception.args[2], regex)

    def load(self, src, **kwargs):
        return markup.MarkupLoader().load(self, src, **kwargs)

    def minify(self, doc):
        return ''.join(l.strip() for l in textwrap.dedent(doc).splitlines())

    def test_load(self):
        # unknown processing instruction
        src = io.StringIO('<?php echo "Hello World!"?>')
        m = self.load(src, lang='xml')
        self.assertEqual(m.xml_decl, {})
        self.assertEqual(m.lang, 'xml')
        self.assertEqual(m.doctype, '')
        self.assertIsNone(m.root)

        # no root element
        src = io.StringIO('&amp; &#38;')
        m = self.load(src, lang='xml')
        self.assertEqual(m.xml_decl, {})
        self.assertEqual(m.lang, 'xml')
        self.assertEqual(m.doctype, '')
        self.assertIsNone(m.root)

    def test_unsupported_html(self):
        # xhtml1 frameset
        src = io.StringIO(textwrap.dedent("""\
            <?xml version="1.0"?>
            <!DOCTYPE html PUBLIC "-//W3C/DTD XHTML 1.0 Frameset//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">
        """))
        self.assertError(src, (2, 0), r'^unsupported HTML version$')

    def test_invalid_xml(self):
        for doc, pos, regex in (
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
            self.assertError(io.StringIO(doc), pos, regex, lang='xml')

    def test_empty_xml(self):
        src = io.StringIO('<?xml version="1.0"?>')
        m = self.load(src, lang='xml')
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xml')
        self.assertEqual(m.doctype, '')
        self.assertIsNone(m.root)

    def test_xml(self):
        doc = self.minify("""\
            <?xml version="1.0"?>
            <!DOCTYPE spam SYSTEM "spam.dtd">
            <spam xmlns="spam" id="spam">
              &amp;
              <eggs/>
              &#38;
              x
            </spam>
        """)
        src = io.StringIO(doc)
        m = self.load(src, lang='xml')
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xml')
        self.assertEqual(m.doctype, '<!DOCTYPE spam SYSTEM "spam.dtd">')
        self.assertTrue(m.root)

        b = ElementBuilder('spam')
        with b.open('spam',
                    attrib={
                        'id': 'spam',
                    },
                    ns={
                        '': 'spam',
                        'xml': markup.XML_NS,
                    }):
            b.str('&amp;')
            b.empty('eggs')
            b.str('&#38;x')
        self.assertElementEqual(m.root, b.root)

    def test_xml_with_prefix(self):
        doc = self.minify("""\
            <?xml version="1.0"?>
            <spam xmlns="spam" xmlns:eggs="eggs">
              <eggs:eggs/>
            </spam>
        """)
        src = io.StringIO(doc)
        m = self.load(src, lang='xml')
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xml')
        self.assertEqual(m.doctype, '')
        self.assertTrue(m.root)

        b = ElementBuilder('spam',
                           eggs='eggs')
        with b.open('spam',
                    ns={
                        '': 'spam',
                        'eggs': 'eggs',
                        'xml': markup.XML_NS,
                    }):
            b.empty('eggs:eggs')
        self.assertElementEqual(m.root, b.root)

        # no default namespace
        class Loader(markup.MarkupLoader):
            def _new_element(self, *args, **kwargs):
                el = super()._new_element(*args, **kwargs)
                el.ns.pop('', None)
                return el

        src = io.StringIO(doc)
        self.assertError(src, (1, 70), r' no default namespace$', lang='xml', loader=Loader)

        # no eggs namespace
        class Loader(markup.MarkupLoader):
            def _new_element(self, *args, **kwargs):
                el = super()._new_element(*args, **kwargs)
                el.ns.pop('eggs', None)
                return el

        src = io.StringIO(doc)
        self.assertError(src, (1, 58), r"^unknown .* prefix 'eggs'$", lang='xml', loader=Loader)

    def test_invalid_xhtml1(self):
        for doc, pos, regex in (
            # no xml declaration
            (f"""\
                {markup.XHTML1_STRICT}
                <html xmlns="{markup.XHTML_NS}">
                </html>
             """,
             (2, 0), r'^XML declaration is not found$'),
            # multiple root elements
            (f"""\
                <?xml version="1.0"?>
                {markup.XHTML1_STRICT}
                <html xmlns="{markup.XHTML_NS}" />
                <html xmlns="{markup.XHTML_NS}" />
             """,
             (4, 0), r' multiple root elements$'),
            # omitted end tag for root element
            (f"""\
                <?xml version="1.0"?>
                {markup.XHTML1_STRICT}
                <html xmlns="{markup.XHTML_NS}">
             """,
             (4, 0), r"^end tag .* '{.*}html' omitted$"),
        ):
            self.assertError(io.StringIO(textwrap.dedent(doc)), pos, regex, lang='xhtml1')

    def test_xhtml1(self):
        doc = self.minify(f"""\
            <?xml version="1.0"?>
            {markup.XHTML1_STRICT}
            <html xmlns="{markup.XHTML_NS}">
              <head>
                <title>title</title>
              </head>
              <body>
                <h1>text</h1>
                <p>line1<br />line2</p>
              </body>
            </html>
        """)
        src = io.StringIO(doc)
        m = self.load(src, lang='xhtml1')
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, markup.XHTML1_STRICT)
        self.assertTrue(m.root)

        b = ElementBuilder(markup.XHTML_NS)
        with b.open('html',
                    ns={
                        '': markup.XHTML_NS,
                        'xml': markup.XML_NS,
                    }):
            with b.open('head'):
                with b.open('title'):
                    b.str('title')
            with b.open('body'):
                with b.open('h1'):
                    b.str('text')
                with b.open('p'):
                    b.str('line1')
                    b.empty('br')
                    b.str('line2')
        self.assertElementEqual(m.root, b.root)

    def test_ayame_remove(self):
        # descendant of root element
        doc = textwrap.dedent(f"""\
            <?xml version="1.0"?>
            {markup.XHTML1_STRICT}
            <html xmlns="{markup.XHTML_NS}" xmlns:ayame="{markup.AYAME_NS}"><ayame:remove>
              <body>
                <h1>text</h1>
                <hr />
              </body>
            </ayame:remove></html>
        """)
        src = io.StringIO(doc)
        m = self.load(src, lang='xhtml1')
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, markup.XHTML1_STRICT)
        self.assertTrue(m.root)

        b = ElementBuilder(markup.XHTML_NS)
        with b.open('html',
                    ns={
                        '': markup.XHTML_NS,
                        'xml': markup.XML_NS,
                        'ayame': markup.AYAME_NS,
                    }):
            pass
        self.assertElementEqual(m.root, b.root)

        # multiple root elements
        doc = textwrap.dedent(f"""\
            <?xml version="1.0"?>
            {markup.XHTML1_STRICT}
            <ayame:remove xmlns:ayame="{markup.AYAME_NS}">
              before html
            </ayame:remove>
            <ayame:remove xmlns:ayame="{markup.AYAME_NS}" />
            <html xmlns="{markup.XHTML_NS}" xmlns:ayame="{markup.AYAME_NS}"><ayame:remove>
              <body>
                <h1>text</h1>
                <hr />
              </body>
            </ayame:remove></html>
            <ayame:remove xmlns:ayame="{markup.AYAME_NS}" />
            <ayame:remove xmlns:ayame="{markup.AYAME_NS}">
              after html
            </ayame:remove>
        """)
        src = io.StringIO(doc)
        m = self.load(src, lang='xhtml1')
        self.assertEqual(m.xml_decl, {'version': '1.0'})
        self.assertEqual(m.lang, 'xhtml1')
        self.assertEqual(m.doctype, markup.XHTML1_STRICT)
        self.assertTrue(m.root)

        with b.open('html',
                    ns={
                        '': markup.XHTML_NS,
                        'xml': markup.XML_NS,
                        'ayame': markup.AYAME_NS,
                    }):
            pass
        self.assertElementEqual(m.root, b.root)


class MarkupRendererTestCase(AyameTestCase):

    def assertError(self, m, regex):
        r = markup.MarkupRenderer()
        for pretty in (False, True):
            with self.assertRaises(ayame.RenderingError) as cm:
                r.render(self, m, pretty=pretty)
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

        b = ElementBuilder('spam')
        with b.open('spam',
                    attrib={
                        'id': 'a',
                    },
                    ns={
                        '': 'spam',
                    }):
            with b.open('eggs') as el:
                el.append(0)
        m.root = b.root
        return m

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
        m.root[0][:] = [
            markup.Element(markup.QName('spam', 'ham')),
        ]
        self.assertError(m, r"namespace URI .*''.* overwritten$")

    def test_default_ns_attr(self):
        m = self.new_markup('xml')
        m.root[:] = [
            markup.Element(markup.QName('eggs', 'eggs'),
                           attrib={
                               markup.QName('eggs', 'a'): '1',
                               markup.QName('spam', 'a'): '2',
                           },
                           ns={
                               'eggs': 'eggs',
                           }),
        ]
        self.assertError(m, r' default namespace$')

    @unittest.mock.patch.dict(markup.MarkupRenderer._registry)
    def test_render_non_xml(self):
        class MarkupHandler(markup.MarkupHandler):
            @property
            def xml(self):
                return False

            def is_empty(self, _):
                return False

            def start_tag(self):
                pass

            def end_tag(self):
                pass

        markup.MarkupRenderer.register(__name__, MarkupHandler)

        m = markup.Markup()
        m.lang = __name__
        m.root = self.empty_element()
        r = markup.MarkupRenderer()
        self.assertEqual(r.render(self, m), b'\n')

    def test_render_xml(self):
        r = markup.MarkupRenderer()
        doc = textwrap.dedent("""\
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

        b = ElementBuilder('spam',
                           eggs='eggs',
                           ham='ham')
        with b.open('spam',
                    attrib={
                        'a': 'a',
                    },
                    ns={
                        '': 'spam',
                    }):
            b.str('\n'
                  '    a\n'
                  '    \n')
            b.empty('eggs')
            b.str('\n'
                  '    b\n'
                  '    c\n')
            with b.open('eggs:eggs',
                        attrib={
                            'eggs:a': '1',
                            'ham:a': '2',
                        },
                        ns={
                            'eggs': 'eggs',
                            'ham': 'ham',
                        }):
                with b.open('ham'):
                    b.str('\n'
                          '    1\n'
                          '    2\n')
        m.root = b.root
        self.assertEqual(r.render(self, m, pretty=True), doc)

        # raw output
        m = markup.Markup()
        m.xml_decl = {
            'version': '1.0',
            'encoding': 'iso-8859-1',
        }
        m.lang = 'xml'
        m.doctype = '<!DOCTYPE spam SYSTEM "spam.dtd">'

        with b.open('spam',
                    attrib={
                        'a': 'a',
                    },
                    ns={
                        '': 'spam',
                    }):
            b.str('\n'
                  '  a\n'
                  '  ')
            b.empty('eggs')
            b.str('\n'
                  '  b\n'
                  '  c\n'
                  '  ')
            with b.open('eggs:eggs',
                        attrib={
                            'eggs:a': '1',
                            'ham:a': '2',
                        },
                        ns={
                            'eggs': 'eggs',
                            'ham': 'ham',
                        }):
                b.str('\n'
                      '    ')
                with b.open('ham'):
                    b.str('\n'
                          '      1\n'
                          '      2\n'
                          '    ')
                b.str('\n'
                      '  ')
            b.str('\n')
        m.root = b.root
        self.assertEqual(r.render(self, m), doc)

    def test_render_xhtml1(self):
        r = markup.MarkupRenderer()
        doc = textwrap.dedent(f"""\
            <?xml version="1.0" encoding="ISO-8859-1"?>
            {markup.XHTML1_STRICT}
            <html xmlns="{markup.XHTML_NS}" xmlns:ayame="{markup.AYAME_NS}" xml:lang="en">
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
                    <input type="text" />
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
            'version': '1.0',
            'encoding': 'iso-8859-1',
        }
        m.lang = 'xhtml1'
        m.doctype = markup.XHTML1_STRICT

        b = ElementBuilder(markup.XHTML_NS)
        with b.open('html',
                    attrib={
                        'xml:lang': 'en',
                    },
                    ns={
                        'xml': markup.XML_NS,
                        'html': markup.XHTML_NS,
                        'ayame': markup.AYAME_NS,
                    }):
            with b.open('head'):
                with b.open('meta',
                            attrib={
                                'name': 'keywords',
                                'content': '',
                            }):
                    b.str('a')
                with b.open('title'):
                    b.str('title')
                    with b.open('span'):
                        pass
                with b.open('style',
                            attrib={
                                'type': 'text/css',
                            }):
                    b.str('\n'
                          '      h1 {\n'
                          '        font-size: 120%;\n'
                          '      }\n'
                          '\n'
                          '      p {\n'
                          '        font-size: 90%;\n'
                          '      }\n'
                          '\n')
                with b.open('script',
                            attrib={
                                'type': 'text/javascript',
                            }):
                    b.str('\n'
                          '     <!--\n'
                          '     var x = 0;\n'
                          '     var y = 0;\n'
                          '     // -->\n'
                          '\n')
            with b.open('body'):
                with b.open('ayame:remove'):
                    with b.open('p'):
                        b.str('')
                        b.str('Hello World!')
                        b.str('')
                with b.open('h1'):
                    b.str('\n'
                          '  spam\n')
                    with b.open('span',
                                attrib={
                                    'class': 'yellow'
                                }):
                        b.str('\n'
                              '  eggs  \n')
                    b.str('\n'
                          '  ham  \n')
                with b.open('blockquote',
                            attrib={
                                'cite': 'http://example.com/',
                            }):
                    b.str('before')
                    with b.open('p'):
                        b.str('citation')
                    b.str('after')
                with b.open('div',
                            attrib={
                                'class': 'text',
                            }):
                    b.str('\n'
                          'spam   \n'
                          '\n')
                    with b.open('i'):
                        b.str('eggs')
                    b.str('  ham')
                with b.open('div',
                            attrib={
                                'class': 'ayame'
                            }):
                    with b.open('ins'):
                        with b.open('ayame:remove'):
                            b.str('spam')
                            b.empty('br')
                            b.str('eggs')
                    with b.open('p'):
                        with b.open('ayame:remove'):
                            b.str('ham\n')
                        b.str('toast')
                    with b.open('ul'):
                        with b.open('ayame:container',
                                    attrib={
                                        'ayame:id': 'a',
                                    }):
                            with b.open('li'):
                                b.str('spam')
                            with b.open('li'):
                                b.str('eggs')
                with b.open('div',
                            attrib={
                                'class': 'block',
                            }):
                    b.str('Planets')
                    with b.open('ul'):
                        with b.open('li'):
                            b.str('\n'
                                  ' Mercury '
                                  '\n')
                        with b.open('li'):
                            b.str('  Venus  ')
                        with b.open('li'):
                            b.str('Earth')
                    b.str('\n')
                with b.open('div',
                            attrib={
                                'class': 'inline-ins-del',
                            }):
                    with b.open('p'):
                        with b.open('del'):
                            b.str('old')
                        with b.open('ins'):
                            b.str('new')
                with b.open('div',
                            attrib={
                                'class': 'block-ins-del',
                            }):
                    with b.open('del'):
                        with b.open('pre'):
                            b.str('old')
                    with b.open('ins'):
                        with b.open('pre'):
                            b.str('new')
                with b.open('pre'):
                    b.str('\n'
                          '  * 1\n'
                          '    * 2\n'
                          '      * 3\n'
                          '    * 4\n'
                          '  * 5\n')
                with b.open('div',
                            attrib={
                                'class': 'br',
                            }):
                    with b.open('h2'):
                        b.str('The Solar System')
                    with b.open('p'):
                        with b.open('em'):
                            b.str('Mercury')
                        b.str(' is the first planet.')
                        b.empty('br')
                        b.str('\n')
                        with b.open('em'):
                            b.str('Venus')
                        b.str(' is the second planet.')
                        b.str('\n')
                    b.str('\n')
                    with b.open('p'):
                        with b.open('em'):
                            b.str('Earth')
                        b.str(' is the third planet.')
                    with b.open('ayame:remove'):
                        with b.open('p'):
                            with b.open('em'):
                                b.str('Mars')
                            b.str(' is the fourth planet.')
                            b.empty('br')
                            with b.open('em'):
                                b.str('Jupiter')
                            b.str(' is the fifth planet.')
                    with b.open('ul'):
                        with b.open('li'):
                            b.str('1')
                            b.empty('br')
                            b.str('2')
                            b.empty('br')
                            b.str('3')
                    b.str('\n')
                with b.open('form',
                            attrib={
                                'action': '/',
                                'method': 'post',
                            }):
                    with b.open('fieldset'):
                        with b.open('legend'):
                            b.str('form')
                        b.empty('input',
                                attrib={
                                    'type': 'text',
                                })
                        with b.open('textarea'):
                            b.str('Sun\n')
        m.root = b.root
        self.assertEqual(r.render(self, m, pretty=True), doc)
