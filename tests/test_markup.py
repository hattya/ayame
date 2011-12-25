#
# test_markup
#
#   Copyright (c) 2011 Akinori Hattori <hattya@gmail.com>
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

from __future__ import unicode_literals
import io
import os
import tempfile

from nose.tools import assert_raises, eq_, ok_

from ayame import markup
from ayame.exception import MarkupError, RenderingError


def test_element():
    spam = markup.Element(markup.QName('spam', 'spam'),
                          attrib={'id': 'a'},
                          type=markup.Element.EMPTY,
                          ns={'': 'spam'})
    eq_(spam.qname, markup.QName('spam', 'spam'))
    eq_(spam.attrib, {'id': 'a'})
    eq_(spam.type, markup.Element.EMPTY)
    eq_(spam.ns, {'': 'spam'})
    eq_(repr(spam.qname), '{spam}spam')

    eggs = spam.copy()
    eggs.qname = markup.QName('spam', 'eggs')
    spam.attrib[0] = 'a'
    eq_(spam.qname, markup.QName('spam', 'spam'))
    eq_(spam.attrib, {'id': 'a', 0: 'a'})

    eq_(eggs.qname, markup.QName('spam', 'eggs'))
    eq_(eggs.attrib, {'id': 'a'})
    eq_(eggs.type, markup.Element.EMPTY)
    eq_(eggs.ns, {'': 'spam'})
    eq_(repr(eggs.qname), '{spam}eggs')

def test_load_error():
    test = test_load_error

    # src is None
    loader = markup.MarkupLoader()
    assert_raises(MarkupError, loader.load, test, None)
    try:
        loader.load(test, None)
        ok_(False)
    except MarkupError as e:
        eq_(e.args[0], test)
        eq_(e.args[1], (0, 0))

    # cannot open src
    src = ''
    loader = markup.MarkupLoader()
    assert_raises(MarkupError, loader.load, test, src, lang='')
    try:
        loader.load(test, src, lang='')
        ok_(False)
    except MarkupError as e:
        eq_(e.args[0], test)
        eq_(e.args[1], (0, 0))

    # src is empty string
    src = io.StringIO(''.decode())
    loader = markup.MarkupLoader()
    assert_raises(MarkupError, loader.load, test, src, lang='')
    try:
        src.seek(0)
        loader.load(test, src, lang='')
        ok_(False)
    except MarkupError as e:
        eq_(e.args[0], test)
        eq_(e.args[1], (1, 0))

def test_load():
    test = test_load

    # load from file
    fd, src = tempfile.mkstemp()
    loader = markup.MarkupLoader()
    m = loader.load(test, src, lang='xml')
    eq_(m.xml_decl, {})
    eq_(m.lang, 'xml')
    ok_(m.doctype is None)
    ok_(m.root is None)
    os.close(fd)
    os.remove(src)

    # php
    php = '<?php echo "Hello World!"?>'
    src = io.StringIO(php.decode())
    loader = markup.MarkupLoader()
    m = loader.load(test, src, lang='xml')
    eq_(m.xml_decl, {})
    eq_(m.lang, 'xml')
    ok_(m.doctype is None)
    ok_(m.root is None)

    # xhtml1 frameset
    xhtml = ('<?xml version="1.0"?>'
             '<!DOCTYPE html PUBLIC "-//W3C/DTD XHTML 1.0 Frameset//EN" '
             '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">')
    src = io.StringIO(xhtml.decode())
    loader = markup.MarkupLoader()
    assert_raises(MarkupError, loader.load, test, src, lang='xml')
    try:
        src.seek(0)
        loader.load(test, src, lang='xml')
        ok_(False)
    except MarkupError as e:
        eq_(e.args[0], test)
        eq_(e.args[1], (1, 21))

def test_invalid_xml():
    test = test_invalid_xml

    def assert_xml(xml, pos):
        src = io.StringIO(xml.decode())
        loader = markup.MarkupLoader()
        assert_raises(MarkupError, loader.load, test, src, lang='xml')
        try:
            src.seek(0)
            loader.load(test, src, lang='xml')
            ok_(False)
        except MarkupError as e:
            eq_(e.args[0], test)
            eq_(e.args[1], pos)

    # malformed xml declaration
    assert_xml('<?xml standalone="yes"?>', (1, 0))

    # mismatched quotes in xml declaration
    assert_xml('<?xml version="1.0\'?>', (1, 0))
    assert_xml('<?xml version=\'1.0"?>', (1, 0))

    # no xml declaration
    assert_xml('<spam></spam>', (1, 0))

    # multiple root element
    assert_xml('<?xml version="1.0"?>'
               '<spam/>'
               '<eggs/>',
               (1, 28))
    assert_xml('<?xml version="1.0"?>'
               '<spam></spam>'
               '<eggs></eggs>',
               (1, 34))

    # omitted end tag for root element
    assert_xml('<?xml version="1.0"?>'
               '<spam>',
               (1, 27))

    # mismatched tag
    assert_xml('<?xml version="1.0"?>'
               '<spam></eggs>',
               (1, 27))

    # attribute duplication
    assert_xml('<?xml version="1.0"?>'
               '<spam a="1" a="2"/>',
               (1, 21))

def test_load_empty_xml():
    test = test_load_empty_xml

    xml = "<?xml version='1.0'?>"
    src = io.StringIO(xml.decode())
    loader = markup.MarkupLoader()
    m = loader.load(test, src, lang='xml')
    eq_(m.xml_decl, {'version': '1.0'})
    eq_(m.lang, 'xml')
    ok_(m.doctype is None)
    ok_(m.root is None)

def test_load_xml():
    test = test_load_xml

    xml = ('<?xml version="1.0"?>'
           '<!DOCTYPE spam SYSTEM "spam.dtd">'
           '<spam xmlns="spam" id="a">'
           '&amp;'
           '<eggs/>'
           '&#38;'
           'x'
           '</spam>')
    src = io.StringIO(xml.decode())
    loader = markup.MarkupLoader()
    m = loader.load(test, src, lang='xml')
    eq_(m.xml_decl, {'version': '1.0'})
    eq_(m.lang, 'xml')
    eq_(m.doctype, '<!DOCTYPE spam SYSTEM "spam.dtd">')
    ok_(m.root)

    spam = m.root
    eq_(spam.qname, markup.QName('spam', 'spam'))
    eq_(spam.attrib, {markup.QName('spam', 'id'): 'a'})
    eq_(spam.type, markup.Element.OPEN)
    eq_(spam.ns, {'': 'spam', 'xml': markup.XML_NS})
    eq_(len(spam.children), 3)
    eq_(spam.children[0], '&amp;')
    eq_(spam.children[2], '&#38;x')

    eggs = spam.children[1]
    eq_(eggs.qname, markup.QName('spam', 'eggs'))
    eq_(eggs.attrib, {})
    eq_(eggs.type, markup.Element.EMPTY)
    eq_(eggs.ns, {})
    eq_(len(eggs.children), 0)

def test_load_xml_with_prefix():
    test = test_load_xml_with_prefix

    xml = ('<?xml version="1.0"?>'
           '<spam xmlns="spam" xmlns:eggs="eggs">'
           '<eggs:eggs/>'
           '</spam>')
    src = io.StringIO(xml.decode())
    loader = markup.MarkupLoader()
    m = loader.load(test, src, lang='xml')
    eq_(m.xml_decl, {'version': '1.0'})
    eq_(m.lang, 'xml')
    ok_(m.doctype is None)
    ok_(m.root)

    spam = m.root
    eq_(spam.qname, markup.QName('spam', 'spam'))
    eq_(spam.attrib, {})
    eq_(spam.type, markup.Element.OPEN)
    eq_(spam.ns, {'': 'spam', 'eggs': 'eggs', 'xml': markup.XML_NS})
    eq_(len(spam.children), 1)

    eggs = spam.children[0]
    eq_(eggs.qname, markup.QName('eggs', 'eggs'))
    eq_(eggs.attrib, {})
    eq_(eggs.type, markup.Element.EMPTY)
    eq_(eggs.ns, {})
    eq_(len(eggs.children), 0)

    # no default namespace
    class Loader(markup.MarkupLoader):
        def new_xml_element(self, *args, **kwargs):
            element = super(Loader, self).new_xml_element(*args, **kwargs)
            element.ns.pop('', None)
            return element
    src = io.StringIO(xml.decode())
    loader = Loader()
    assert_raises(MarkupError, loader.load, test, src, lang='xml')
    try:
        src.seek(0)
        loader.load(test, src, lang='xml')
        ok_(False)
    except MarkupError as e:
        eq_(e.args[0], test)
        eq_(e.args[1], (1, 70))

    # no eggs namespace
    class Loader(markup.MarkupLoader):
        def new_xml_element(self, *args, **kwargs):
            element = super(Loader, self).new_xml_element(*args, **kwargs)
            element.ns.pop('eggs', None)
            return element
    src = io.StringIO(xml.decode())
    loader = Loader()
    assert_raises(MarkupError, loader.load, test, src, lang='xml')
    try:
        src.seek(0)
        loader.load(test, src, lang='xml')
        ok_(False)
    except MarkupError as e:
        eq_(e.args[0], test)
        eq_(e.args[1], (1, 58))

def test_load_xhtml1():
    test = test_load_xhtml1

    xhtml = ('<?xml version="1.0"?>'
             '{doctype}'
             '<html xmlns="{xhtml}">'
             '<head>'
             '<title>title</title>'
             '</head>'
             '<body>'
             '<h1>text</h1>'
             '<p>line1<br />line2</p>'
             '</body>'
             '</html>').format(doctype=markup.XHTML1_STRICT,
                               xhtml=markup.XHTML_NS)
    src = io.StringIO(xhtml.decode())
    loader = markup.MarkupLoader()
    m = loader.load(test, src, lang='xhtml1')
    eq_(m.xml_decl, {'version': '1.0'})
    eq_(m.lang, 'xhtml1')
    eq_(m.doctype, markup.XHTML1_STRICT)
    ok_(m.root)

    html = m.root
    eq_(html.qname, markup.QName(markup.XHTML_NS, 'html'))
    eq_(html.attrib, {})
    eq_(html.type, markup.Element.OPEN)
    eq_(html.ns, {'': markup.XHTML_NS, 'xml': markup.XML_NS})
    eq_(len(html.children), 2)

    head = html.children[0]
    eq_(head.qname, markup.QName(markup.XHTML_NS, 'head'))
    eq_(head.attrib, {})
    eq_(head.type, markup.Element.OPEN)
    eq_(head.ns, {})
    eq_(len(head.children), 1)

    title = head.children[0]
    eq_(title.qname, markup.QName(markup.XHTML_NS, 'title'))
    eq_(title.attrib, {})
    eq_(title.type, markup.Element.OPEN)
    eq_(title.ns, {})
    eq_(len(title.children), 1)
    eq_(title.children[0], 'title')

    body = html.children[1]
    eq_(body.qname, markup.QName(markup.XHTML_NS, 'body'))
    eq_(body.attrib, {})
    eq_(body.type, markup.Element.OPEN)
    eq_(body.ns, {})
    eq_(len(body.children), 2)

    h1 = body.children[0]
    eq_(h1.qname, markup.QName(markup.XHTML_NS, 'h1'))
    eq_(h1.attrib, {})
    eq_(h1.type, markup.Element.OPEN)
    eq_(h1.ns, {})
    eq_(len(h1.children), 1)
    eq_(h1.children[0], 'text')

    p = body.children[1]
    eq_(p.qname, markup.QName(markup.XHTML_NS, 'p'))
    eq_(p.attrib, {})
    eq_(p.type, markup.Element.OPEN)
    eq_(p.ns, {})
    eq_(len(p.children), 3)
    eq_(p.children[0], 'line1')
    eq_(p.children[2], 'line2')

    br = p.children[1]
    eq_(br.qname, markup.QName(markup.XHTML_NS, 'br'))
    eq_(br.attrib, {})
    eq_(br.type, markup.Element.EMPTY)
    eq_(br.ns, {})
    eq_(len(br.children), 0)

def test_invalid_xhtml1():
    test = test_invalid_xhtml1

    def assert_xhtml1(xhtml, pos):
        src = io.StringIO(xhtml.decode())
        loader = markup.MarkupLoader()
        assert_raises(MarkupError, loader.load, test, src, lang='xhtml1')
        try:
            src.seek(0)
            loader.load(test, src, lang='xhtml1')
            ok_(False)
        except MarkupError as e:
            eq_(e.args[0], test)
            eq_(e.args[1], pos)

    # no xml declaration
    assert_xhtml1(markup.XHTML1_STRICT +
                  ('<html xmlns="http://www.w3.org/1999/xhtml">'
                   '</html>'),
                  (1, 109))

    # multiple root element
    assert_xhtml1('<?xml version="1.0"?>' +
                  markup.XHTML1_STRICT +
                  ('<html xmlns="http://www.w3.org/1999/xhtml"/>'
                   '<html xmlns="http://www.w3.org/1999/xhtml"/>'),
                  (1, 174))

    # omitted end tag for root element
    assert_xhtml1('<?xml version="1.0"?>' +
                  markup.XHTML1_STRICT +
                  '<html xmlns="http://www.w3.org/1999/xhtml">',
                  (1, 173))

def test_ayame_remove():
    test = test_ayame_remove

    # descendant of root element
    xhtml = ('<?xml version="1.0"?>'
             '{doctype}'
             '<html xmlns="{xhtml}" xmlns:ayame="{ayame}">'
             '<ayame:remove>'
             '<body>'
             '<h1>text</h1>'
             '<hr/>'
             '</body>'
             '</ayame:remove>'
             '</html>').format(doctype=markup.XHTML1_STRICT,
                               xhtml=markup.XHTML_NS,
                               ayame=markup.AYAME_NS)
    src = io.StringIO(xhtml.decode())
    loader = markup.MarkupLoader()
    m = loader.load(test, src, lang='xhtml1')
    eq_(m.xml_decl, {'version': '1.0'})
    eq_(m.lang, 'xhtml1')
    eq_(m.doctype, markup.XHTML1_STRICT)
    ok_(m.root)

    html = m.root
    eq_(html.qname, markup.QName(markup.XHTML_NS, 'html'))
    eq_(html.attrib, {})
    eq_(html.type, markup.Element.OPEN)
    eq_(html.ns, {'': markup.XHTML_NS,
                  'xml': markup.XML_NS,
                  'ayame': markup.AYAME_NS})
    eq_(len(html.children), 0)

    # multiple root element
    xhtml = ('<?xml version="1.0"?>'
             '{doctype}'
             '<ayame:remove xmlns:ayame="{ayame}">'
             'before html'
             '</ayame:remove>'
             '<ayame:remove xmlns:ayame="{ayame}"/>'
             '<html xmlns="{xhtml}" xmlns:ayame="{ayame}">'
             '<ayame:remove>'
             '<body>'
             '<h1>text</h1>'
             '<hr/>'
             '</body>'
             '</ayame:remove>'
             '</html>'
             '<ayame:remove xmlns:ayame="{ayame}"/>'
             '<ayame:remove xmlns:ayame="{ayame}">'
             'after html'
             '</ayame:remove>').format(doctype=markup.XHTML1_STRICT,
                                       xhtml=markup.XHTML_NS,
                                       ayame=markup.AYAME_NS)
    src = io.StringIO(xhtml.decode())
    loader = markup.MarkupLoader()
    m = loader.load(test, src, lang='xhtml1')
    eq_(m.xml_decl, {'version': '1.0'})
    eq_(m.lang, 'xhtml1')
    eq_(m.doctype, markup.XHTML1_STRICT)
    ok_(m.root)

    html = m.root
    eq_(html.qname, markup.QName(markup.XHTML_NS, 'html'))
    eq_(html.attrib, {})
    eq_(html.type, markup.Element.OPEN)
    eq_(html.ns, {'': markup.XHTML_NS,
                  'xml': markup.XML_NS,
                  'ayame': markup.AYAME_NS})
    eq_(len(html.children), 0)

def test_render_error():
    test = test_render_error

    m = markup.Markup()
    m.xml_decl = {'version': '1.0',
                  'standalone': 'yes'}
    m.root = markup.Element(markup.QName('spam', 'spam'))
    m.root.attrib[markup.QName('spam', 'id')] = 'a'
    m.root.type = markup.Element.OPEN
    m.root.ns[''] = 'spam'
    eggs = markup.Element(markup.QName('spam', 'eggs'))
    eggs.type = markup.Element.OPEN
    eggs.children.append(0)
    m.root.children.append(eggs)
    renderer = markup.MarkupRenderer()

    # invalid type
    m.lang = 'xml'
    assert_raises(RenderingError, renderer.render, test, m, pretty=False)
    assert_raises(RenderingError, renderer.render, test, m, pretty=True)

    # svg
    m.lang = 'svg'
    assert_raises(RenderingError, renderer.render, test, m, pretty=False)
    assert_raises(RenderingError, renderer.render, test, m, pretty=True)

    # unknown namespace URI
    m.lang = 'xml'
    m.root.ns.clear()
    eggs.children = []
    assert_raises(RenderingError, renderer.render, test, m, pretty=False)
    assert_raises(RenderingError, renderer.render, test, m, pretty=True)

    # overwrite namespace URI
    m.lang = 'xml'
    m.root.ns[''] = 'spam'
    eggs.ns[''] = 'eggs'
    ham = markup.Element(markup.QName('spam', 'ham'))
    ham.type = markup.Element.EMPTY
    eggs.children = [ham]
    assert_raises(RenderingError, renderer.render, test, m, pretty=False)
    assert_raises(RenderingError, renderer.render, test, m, pretty=True)

    # element namespace with default namespace
    m.lang = 'xml'
    eggs = markup.Element(markup.QName('eggs', 'eggs'))
    eggs.attrib[markup.QName('eggs', 'a')] = '1'
    eggs.attrib[markup.QName('spam', 'a')] = '2'
    eggs.type = markup.Element.OPEN
    eggs.ns['eggs'] = 'eggs'
    m.root.children = [eggs]
    assert_raises(RenderingError, renderer.render, test, m, pretty=False)
    assert_raises(RenderingError, renderer.render, test, m, pretty=True)

    # attribute is None
    m = markup.Markup()
    m.xml_decl = {'version': '1.0'}
    m.lang = 'xhtml1'
    m.root = markup.Element(markup.QName(markup.XHTML_NS, 'html'))
    m.root.attrib[markup.QName(markup.XML_NS, 'lang')] = None
    m.root.type = markup.Element.EMPTY
    m.root.ns[''] = markup.XHTML_NS
    assert_raises(RenderingError, renderer.render, test, m, pretty=False)
    assert_raises(RenderingError, renderer.render, test, m, pretty=True)

def test_render_xml():
    test = test_render_xml
    renderer = markup.MarkupRenderer()

    # pretty output
    xml = ('<?xml version="1.0" encoding="ISO-8859-1"?>\n'
           '<!DOCTYPE spam SYSTEM "spam.dtd">\n'
           '<spam xmlns="spam" a="a">\n'
           '  a\n'
           '  <eggs/>\n'
           '  b\n'
           '  c\n'
           '  <eggs:eggs xmlns:eggs="eggs" xmlns:ham="ham" a="1" ham:a="2">\n'
           '    <ham>\n'
           '      1\n'
           '      2\n'
           '    </ham>\n'
           '  </eggs:eggs>\n'
           '</spam>\n')

    m = markup.Markup()
    m.xml_decl = {'version': '1.0',
                  'encoding': 'iso-8859-1'}
    m.lang = 'xml'
    m.doctype = '<!DOCTYPE spam SYSTEM "spam.dtd">'
    m.root = markup.Element(markup.QName('spam', 'spam'))
    m.root.attrib[markup.QName('spam', 'a')] = 'a'
    m.root.type = markup.Element.OPEN
    m.root.ns[''] = 'spam'
    m.root.children.append('\n'
                           '    a\n'
                           '    \n')
    eggs = markup.Element(markup.QName('spam', 'eggs'))
    eggs.type = markup.Element.EMPTY
    m.root.children.append(eggs)
    m.root.children.append('\n'
                           '    b\n'
                           '    c\n')
    eggs = markup.Element(markup.QName('eggs', 'eggs'))
    eggs.attrib[markup.QName('eggs', 'a')] = '1'
    eggs.attrib[markup.QName('ham', 'a')] = '2'
    eggs.type = markup.Element.OPEN
    eggs.ns['eggs'] = 'eggs'
    eggs.ns['ham'] = 'ham'
    ham = markup.Element(markup.QName('spam', 'ham'))
    ham.type = markup.Element.OPEN
    ham.children.append('\n'
                        '    1\n'
                        '    2\n')
    eggs.children.append(ham)
    m.root.children.append(eggs)
    eq_(renderer.render(test, m, pretty=True), xml)

    # raw output
    m = markup.Markup()
    m.xml_decl = {'version': '1.0',
                  'encoding': 'iso-8859-1'}
    m.lang = 'xml'
    m.doctype = '<!DOCTYPE spam SYSTEM "spam.dtd">'
    m.root = markup.Element(markup.QName('spam', 'spam'))
    m.root.attrib[markup.QName('spam', 'a')] = 'a'
    m.root.type = markup.Element.OPEN
    m.root.ns[''] = 'spam'
    m.root.children.append('\n'
                           '  a\n'
                           '  ')
    eggs = markup.Element(markup.QName('spam', 'eggs'))
    eggs.type = markup.Element.EMPTY
    m.root.children.append(eggs)
    m.root.children.append('\n'
                           '  b\n'
                           '  c\n'
                           '  ')
    eggs = markup.Element(markup.QName('eggs', 'eggs'))
    eggs.attrib[markup.QName('eggs', 'a')] = '1'
    eggs.attrib[markup.QName('ham', 'a')] = '2'
    eggs.type = markup.Element.OPEN
    eggs.ns['eggs'] = 'eggs'
    eggs.ns['ham'] = 'ham'
    eggs.children.append('\n'
                         '    ')
    ham = markup.Element(markup.QName('spam', 'ham'))
    ham.type = markup.Element.OPEN
    ham.children.append('\n'
                        '      1\n'
                        '      2\n'
                        '    ')
    eggs.children.append(ham)
    eggs.children.append('\n'
                         '  ')
    m.root.children.append(eggs)
    m.root.children.append('\n')
    eq_(renderer.render(test, m, pretty=False), xml)

def test_render_xhtml1():
    test = test_render_xhtml1
    renderer = markup.MarkupRenderer()

    def new_qname(name, ns=markup.XHTML_NS):
        return markup.QName(ns, name)

    def new_element(name, ns=markup.XHTML_NS):
        return markup.Element(new_qname(name, ns=ns), type=markup.Element.OPEN)

    xhtml = ('<?xml version="1.0" encoding="ISO-8859-1"?>\n'
             '{doctype}\n'
             '<html xmlns="{xhtml}" xmlns:ayame="{ayame}" xml:lang="en">\n'
             '  <head>\n'
             '    <meta content="" name="keywords"/>\n'
             '    <title>title</title>\n'
             '    <style type="text/css">\n'
             '      h1 {{\n'
             '        font-size: 120%;\n'
             '      }}\n'
             '      p {{\n'
             '        font-size: 90%;\n'
             '      }}\n'
             '    </style>\n'
             '    <script type="text/javascript">\n'
             '      <!--\n'
             '      var x = 0;\n'
             '      var y = 0;\n'
             '      // -->\n'
             '    </script>\n'
             '  </head>\n'
             '  <body>\n'
             '    <ayame:remove>\n'
             '      <p>Hello World!</p>\n'
             '    </ayame:remove>\n'
             '    <h1>spam <span class="yellow">eggs</span> ham</h1>\n'
             '    <blockquote cite="http://example.com/">\n'
             '      <p>citation</p>\n'
             '    </blockquote>\n'
             '    <div class="text">spam <i>eggs</i> ham</div>\n'
             '    <div class="ayame">\n'
             '      <ayame:remove>\n'
             '        Hello World!\n'
             '      </ayame:remove>\n'
             '    </div>\n'
             '    <div class="block">\n'
             '      <ul>\n'
             '        <li>Mercury</li>\n'
             '        <li>Venus</li>\n'
             '        <li>Earth</li>\n'
             '      </ul>\n'
             '    </div>\n'
             '    <div class="inline-ins-del">\n'
             '      <p><del>old</del><ins>new</ins></p>\n'
             '    </div>\n'
             '    <div class="block-ins-del">\n'
             '      <del>\n'
             '        <pre>old</pre>\n'
             '      </del>\n'
             '      <ins>\n'
             '        <pre>new</pre>\n'
             '      </ins>\n'
             '    </div>\n'
             '    <pre>\n'
             '  * 1\n'
             '    * 2\n'
             '      * 3\n'
             '    * 4\n'
             '  * 5\n'
             '</pre>\n'
             '  </body>\n'
             '</html>\n').format(doctype=markup.XHTML1_STRICT,
                                 xhtml=markup.XHTML_NS,
                                 ayame=markup.AYAME_NS)

    m = markup.Markup()
    m.xml_decl = {'version': '1.0',
                  'encoding': 'iso-8859-1'}
    m.lang = 'xhtml1'
    m.doctype = markup.XHTML1_STRICT
    m.root = new_element('html')
    m.root.attrib[new_qname('lang', ns=markup.XML_NS)] = 'en'
    m.root.ns['a'] = markup.XML_NS
    m.root.ns['b'] = markup.XHTML_NS
    m.root.ns['ayame'] = markup.AYAME_NS

    head = new_element('head')
    meta = new_element('meta')
    meta.attrib[new_qname('name')] = 'keywords'
    meta.attrib[new_qname('content')] = ''
    meta.children.append('a')
    head.children.append(meta)

    title = new_element('title')
    title.children.append('title')
    span = new_element('span')
    title.children.append(span)
    head.children.append(title)

    style = new_element('style')
    style.attrib[new_qname('type')] = 'text/css'
    style.children.append('\n'
                          '      h1 {\n'
                          '        font-size: 120%;\n'
                          '      }\n'
                          '\n'
                          '      p {\n'
                          '        font-size: 90%;\n'
                          '      }\n'
                          '\n')
    head.children.append(style)

    script = new_element('script')
    script.attrib[new_qname('type')] = 'text/javascript'
    script.children.append('\n'
                           '     <!--\n'
                           '     var x = 0;\n'
                           '     var y = 0;\n'
                           '     // -->\n'
                           '\n')
    head.children.append(script)
    m.root.children.append(head)

    body = new_element('body')
    ayame_remove = new_element('remove', ns=markup.AYAME_NS)
    p = new_element('p')
    p.children.append('Hello World!')
    ayame_remove.children.append(p)
    body.children.append(ayame_remove)

    h1 = new_element('h1')
    h1.children.append('\n'
                       '  spam\n')
    span = new_element('span')
    span.attrib[new_qname('class')] = 'yellow'
    span.children.append('\n'
                         '  eggs  \n')
    h1.children.append(span)
    h1.children.append('\n'
                       '  ham  \n')
    body.children.append(h1)

    blockquote = new_element('blockquote')
    blockquote.attrib[new_qname('cite')] = 'http://example.com/'
    blockquote.children.append('before')
    p = new_element('p')
    p.children.append('citation')
    blockquote.children.append(p)
    blockquote.children.append('after')
    body.children.append(blockquote)

    div = new_element('div')
    div.attrib[new_qname('class')] = 'text'
    div.children.append(' \n'
                        '  spam\n'
                        ' \n')
    i = new_element('i')
    i.children.append('eggs')
    div.children.append(i)
    div.children.append('  ham')
    body.children.append(div)

    div = new_element('div')
    div.attrib[new_qname('class')] = 'ayame'
    ayame_remove = new_element('remove', ns=markup.AYAME_NS)
    ayame_remove.children.append('Hello World!')
    div.children.append(ayame_remove)
    body.children.append(div)

    div = new_element('div')
    div.attrib[new_qname('class')] = 'block'
    ul = new_element('ul')
    li = new_element('li')
    li.children.append('\n'
                       ' Mercury '
                       '\n')
    ul.children.append(li)
    li = new_element('li')
    li.children.append('  Venus  ')
    ul.children.append(li)
    li = new_element('li')
    li.children.append('Earth')
    ul.children.append(li)
    div.children.append(ul)
    div.children.append('\n')
    body.children.append(div)

    div = new_element('div')
    div.attrib[new_qname('class')] = 'inline-ins-del'
    p = new_element('p')
    del_ = new_element('del')
    del_.children.append('old')
    p.children.append(del_)
    ins = new_element('ins')
    ins.children.append('new')
    p.children.append(ins)
    div.children.append(p)
    body.children.append(div)

    div = new_element('div')
    div.attrib[new_qname('class')] = 'block-ins-del'
    del_ = new_element('del')
    pre = new_element('pre')
    pre.children.append('old')
    del_.children.append(pre)
    div.children.append(del_)
    ins = new_element('ins')
    pre = new_element('pre')
    pre.children.append('new')
    ins.children.append(pre)
    div.children.append(ins)
    body.children.append(div)

    pre = new_element('pre')
    pre.children.append('\n'
                        '  * 1\n'
                        '    * 2\n'
                        '      * 3\n'
                        '    * 4\n'
                        '  * 5\n')
    body.children.append(pre)
    m.root.children.append(body)

    eq_(renderer.render(test, m, pretty=True), xhtml)
