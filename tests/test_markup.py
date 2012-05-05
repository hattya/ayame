#
# test_markup
#
#   Copyright (c) 2011-2012 Akinori Hattori <hattya@gmail.com>
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
    src = io.StringIO()
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
    php = u'<?php echo "Hello World!"?>'
    src = io.StringIO(php)
    loader = markup.MarkupLoader()
    m = loader.load(test, src, lang='xml')
    eq_(m.xml_decl, {})
    eq_(m.lang, 'xml')
    ok_(m.doctype is None)
    ok_(m.root is None)

    # xhtml1 frameset
    xhtml = (u'<?xml version="1.0"?>'
             u'<!DOCTYPE html PUBLIC "-//W3C/DTD XHTML 1.0 Frameset//EN"'
             u' "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">')
    src = io.StringIO(xhtml)
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
        src = io.StringIO(xml)
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
    assert_xml(u'<?xml standalone="yes"?>', (1, 0))

    # mismatched quotes in xml declaration
    assert_xml(u'<?xml version="1.0\'?>', (1, 0))
    assert_xml(u'<?xml version=\'1.0"?>', (1, 0))

    # no xml declaration
    assert_xml(u'<spam></spam>', (1, 0))

    # multiple root element
    assert_xml(u'<?xml version="1.0"?>'
               u'<spam/>'
               u'<eggs/>',
               (1, 28))
    assert_xml(u'<?xml version="1.0"?>'
               u'<spam></spam>'
               u'<eggs></eggs>',
               (1, 34))

    # omitted end tag for root element
    assert_xml(u'<?xml version="1.0"?>'
               u'<spam>',
               (1, 27))

    # mismatched tag
    assert_xml(u'<?xml version="1.0"?>'
               u'<spam></eggs>',
               (1, 27))

    # attribute duplication
    assert_xml(u'<?xml version="1.0"?>'
               u'<spam a="1" a="2"/>',
               (1, 21))

def test_load_empty_xml():
    test = test_load_empty_xml

    xml = u"<?xml version='1.0'?>"
    src = io.StringIO(xml)
    loader = markup.MarkupLoader()
    m = loader.load(test, src, lang='xml')
    eq_(m.xml_decl, {'version': '1.0'})
    eq_(m.lang, 'xml')
    ok_(m.doctype is None)
    ok_(m.root is None)

def test_load_xml():
    test = test_load_xml

    xml = (u'<?xml version="1.0"?>'
           u'<!DOCTYPE spam SYSTEM "spam.dtd">'
           u'<spam xmlns="spam" id="a">'
           u'&amp;'
           u'<eggs/>'
           u'&#38;'
           u'x'
           u'</spam>')
    src = io.StringIO(xml)
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

    xml = (u'<?xml version="1.0"?>'
           u'<spam xmlns="spam" xmlns:eggs="eggs">'
           u'<eggs:eggs/>'
           u'</spam>')
    src = io.StringIO(xml)
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
    src = io.StringIO(xml)
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
    src = io.StringIO(xml)
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

    xhtml = (u'<?xml version="1.0"?>'
             u'{doctype}'
             u'<html xmlns="{xhtml}">'
             u'<head>'
             u'<title>title</title>'
             u'</head>'
             u'<body>'
             u'<h1>text</h1>'
             u'<p>line1<br />line2</p>'
             u'</body>'
             u'</html>').format(doctype=markup.XHTML1_STRICT,
                                xhtml=markup.XHTML_NS)
    src = io.StringIO(xhtml)
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
        src = io.StringIO(xhtml)
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
    assert_xhtml1(u'{doctype}'
                  u'<html xmlns="http://www.w3.org/1999/xhtml">'
                  u'</html>'
                  .format(doctype=markup.XHTML1_STRICT),
                  (1, 109))

    # multiple root element
    assert_xhtml1(u'<?xml version="1.0"?>'
                  u'{doctype}'
                  u'<html xmlns="http://www.w3.org/1999/xhtml"/>'
                  u'<html xmlns="http://www.w3.org/1999/xhtml"/>'
                  .format(doctype=markup.XHTML1_STRICT),
                  (1, 174))

    # omitted end tag for root element
    assert_xhtml1(u'<?xml version="1.0"?>'
                  u'{doctype}'
                  u'<html xmlns="http://www.w3.org/1999/xhtml">'
                  .format(doctype=markup.XHTML1_STRICT),
                  (1, 173))

def test_ayame_remove():
    test = test_ayame_remove

    # descendant of root element
    xhtml = (u'<?xml version="1.0"?>'
             u'{doctype}'
             u'<html xmlns="{xhtml}" xmlns:ayame="{ayame}">'
             u'<ayame:remove>'
             u'<body>'
             u'<h1>text</h1>'
             u'<hr/>'
             u'</body>'
             u'</ayame:remove>'
             u'</html>').format(doctype=markup.XHTML1_STRICT,
                                xhtml=markup.XHTML_NS,
                                ayame=markup.AYAME_NS)
    src = io.StringIO(xhtml)
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
    xhtml = (u'<?xml version="1.0"?>'
             u'{doctype}'
             u'<ayame:remove xmlns:ayame="{ayame}">'
             u'before html'
             u'</ayame:remove>'
             u'<ayame:remove xmlns:ayame="{ayame}"/>'
             u'<html xmlns="{xhtml}" xmlns:ayame="{ayame}">'
             u'<ayame:remove>'
             u'<body>'
             u'<h1>text</h1>'
             u'<hr/>'
             u'</body>'
             u'</ayame:remove>'
             u'</html>'
             u'<ayame:remove xmlns:ayame="{ayame}"/>'
             u'<ayame:remove xmlns:ayame="{ayame}">'
             u'after html'
             u'</ayame:remove>').format(doctype=markup.XHTML1_STRICT,
                                        xhtml=markup.XHTML_NS,
                                        ayame=markup.AYAME_NS)
    src = io.StringIO(xhtml)
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
    m.xml_decl = {'version': u'1.0',
                  'standalone': u'yes'}
    m.root = markup.Element(markup.QName(u'spam', u'spam'))
    m.root.attrib[markup.QName(u'spam', u'id')] = u'a'
    m.root.type = markup.Element.OPEN
    m.root.ns[u''] = u'spam'
    eggs = markup.Element(markup.QName(u'spam', u'eggs'))
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
    m.root.ns[u''] = u'spam'
    eggs.ns[u''] = u'eggs'
    ham = markup.Element(markup.QName(u'spam', u'ham'))
    ham.type = markup.Element.EMPTY
    eggs.children = [ham]
    assert_raises(RenderingError, renderer.render, test, m, pretty=False)
    assert_raises(RenderingError, renderer.render, test, m, pretty=True)

    # element namespace with default namespace
    m.lang = 'xml'
    eggs = markup.Element(markup.QName(u'eggs', u'eggs'))
    eggs.attrib[markup.QName(u'eggs', u'a')] = u'1'
    eggs.attrib[markup.QName(u'spam', u'a')] = u'2'
    eggs.type = markup.Element.OPEN
    eggs.ns[u'eggs'] = u'eggs'
    m.root.children = [eggs]
    assert_raises(RenderingError, renderer.render, test, m, pretty=False)
    assert_raises(RenderingError, renderer.render, test, m, pretty=True)

    # attribute is None
    m = markup.Markup()
    m.xml_decl = {'version': u'1.0'}
    m.lang = 'xhtml1'
    m.root = markup.Element(markup.QName(markup.XHTML_NS, u'html'))
    m.root.attrib[markup.QName(markup.XML_NS, u'lang')] = None
    m.root.type = markup.Element.EMPTY
    m.root.ns[u''] = markup.XHTML_NS
    assert_raises(RenderingError, renderer.render, test, m, pretty=False)
    assert_raises(RenderingError, renderer.render, test, m, pretty=True)

def test_render_xml():
    test = test_render_xml
    renderer = markup.MarkupRenderer()

    # pretty output
    xml = (u'<?xml version="1.0" encoding="ISO-8859-1"?>\n'
           u'<!DOCTYPE spam SYSTEM "spam.dtd">\n'
           u'<spam xmlns="spam" a="a">\n'
           u'  a\n'
           u'  <eggs/>\n'
           u'  b\n'
           u'  c\n'
           u'  <eggs:eggs xmlns:eggs="eggs" xmlns:ham="ham" a="1" ham:a="2">\n'
           u'    <ham>\n'
           u'      1\n'
           u'      2\n'
           u'    </ham>\n'
           u'  </eggs:eggs>\n'
           u'</spam>\n')
    xml = xml.encode('iso-8859-1')

    m = markup.Markup()
    m.xml_decl = {'version': u'1.0',
                  'encoding': u'iso-8859-1'}
    m.lang = 'xml'
    m.doctype = u'<!DOCTYPE spam SYSTEM "spam.dtd">'
    m.root = markup.Element(markup.QName(u'spam', u'spam'))
    m.root.attrib[markup.QName(u'spam', u'a')] = u'a'
    m.root.type = markup.Element.OPEN
    m.root.ns[u''] = u'spam'
    m.root.children.append(u'\n'
                           u'    a\n'
                           u'    \n')
    eggs = markup.Element(markup.QName(u'spam', u'eggs'))
    eggs.type = markup.Element.EMPTY
    m.root.children.append(eggs)
    m.root.children.append(u'\n'
                           u'    b\n'
                           u'    c\n')
    eggs = markup.Element(markup.QName(u'eggs', u'eggs'))
    eggs.attrib[markup.QName(u'eggs', u'a')] = u'1'
    eggs.attrib[markup.QName(u'ham', u'a')] = u'2'
    eggs.type = markup.Element.OPEN
    eggs.ns[u'eggs'] = u'eggs'
    eggs.ns[u'ham'] = u'ham'
    ham = markup.Element(markup.QName(u'spam', u'ham'))
    ham.type = markup.Element.OPEN
    ham.children.append(u'\n'
                        u'    1\n'
                        u'    2\n')
    eggs.children.append(ham)
    m.root.children.append(eggs)
    eq_(renderer.render(test, m, pretty=True), xml)

    # raw output
    m = markup.Markup()
    m.xml_decl = {'version': u'1.0',
                  'encoding': u'iso-8859-1'}
    m.lang = 'xml'
    m.doctype = u'<!DOCTYPE spam SYSTEM "spam.dtd">'
    m.root = markup.Element(markup.QName(u'spam', u'spam'))
    m.root.attrib[markup.QName(u'spam', u'a')] = u'a'
    m.root.type = markup.Element.OPEN
    m.root.ns[u''] = u'spam'
    m.root.children.append(u'\n'
                           u'  a\n'
                           u'  ')
    eggs = markup.Element(markup.QName(u'spam', u'eggs'))
    eggs.type = markup.Element.EMPTY
    m.root.children.append(eggs)
    m.root.children.append(u'\n'
                           u'  b\n'
                           u'  c\n'
                           u'  ')
    eggs = markup.Element(markup.QName(u'eggs', u'eggs'))
    eggs.attrib[markup.QName(u'eggs', u'a')] = u'1'
    eggs.attrib[markup.QName(u'ham', u'a')] = u'2'
    eggs.type = markup.Element.OPEN
    eggs.ns[u'eggs'] = u'eggs'
    eggs.ns[u'ham'] = u'ham'
    eggs.children.append(u'\n'
                         u'    ')
    ham = markup.Element(markup.QName(u'spam', u'ham'))
    ham.type = markup.Element.OPEN
    ham.children.append(u'\n'
                        u'      1\n'
                        u'      2\n'
                        u'    ')
    eggs.children.append(ham)
    eggs.children.append(u'\n'
                         u'  ')
    m.root.children.append(eggs)
    m.root.children.append(u'\n')
    eq_(renderer.render(test, m, pretty=False), xml)

def test_render_xhtml1():
    test = test_render_xhtml1
    renderer = markup.MarkupRenderer()

    def new_qname(name, ns=markup.XHTML_NS):
        return markup.QName(ns, name)

    def new_element(name, ns=markup.XHTML_NS, type=markup.Element.OPEN):
        return markup.Element(new_qname(name, ns=ns), type=type)

    xhtml = (u'<?xml version="1.0" encoding="ISO-8859-1"?>\n'
             u'{doctype}\n'
             u'<html xmlns="{xhtml}" xmlns:ayame="{ayame}" xml:lang="en">\n'
             u'  <head>\n'
             u'    <meta content="" name="keywords"/>\n'
             u'    <title>title</title>\n'
             u'    <style type="text/css">\n'
             u'      h1 {{\n'
             u'        font-size: 120%;\n'
             u'      }}\n'
             u'      p {{\n'
             u'        font-size: 90%;\n'
             u'      }}\n'
             u'    </style>\n'
             u'    <script type="text/javascript">\n'
             u'      <!--\n'
             u'      var x = 0;\n'
             u'      var y = 0;\n'
             u'      // -->\n'
             u'    </script>\n'
             u'  </head>\n'
             u'  <body>\n'
             u'    <ayame:remove>\n'
             u'      <p>Hello World!</p>\n'
             u'    </ayame:remove>\n'
             u'    <h1> spam <span class="yellow"> eggs </span> ham </h1>\n'
             u'    <blockquote cite="http://example.com/">\n'
             u'      <p>citation</p>\n'
             u'    </blockquote>\n'
             u'    <div class="text"> spam <i>eggs</i> ham</div>\n'
             u'    <div class="ayame">\n'
             u'      <ins>\n'
             u'        <ayame:remove>\n'
             u'          spam<br/>\n'
             u'          eggs\n'
             u'        </ayame:remove>\n'
             u'      </ins>\n'
             u'      <p>\n'
             u'        <ayame:remove>\n'
             u'          ham\n'
             u'        </ayame:remove>\n'
             u'        toast\n'
             u'      </p>\n'
             u'      <ul>\n'
             u'        <ayame:container id="a">\n'
             u'          <li>spam</li>\n'
             u'          <li>eggs</li>\n'
             u'        </ayame:container>\n'
             u'      </ul>\n'
             u'    </div>\n'
             u'    <div class="block">\n'
             u'      Planets\n'
             u'      <ul>\n'
             u'        <li> Mercury </li>\n'
             u'        <li> Venus </li>\n'
             u'        <li>Earth</li>\n'
             u'      </ul>\n'
             u'    </div>\n'
             u'    <div class="inline-ins-del">\n'
             u'      <p><del>old</del><ins>new</ins></p>\n'
             u'    </div>\n'
             u'    <div class="block-ins-del">\n'
             u'      <del>\n'
             u'        <pre>old</pre>\n'
             u'      </del>\n'
             u'      <ins>\n'
             u'        <pre>new</pre>\n'
             u'      </ins>\n'
             u'    </div>\n'
             u'    <pre>\n'
             u'  * 1\n'
             u'    * 2\n'
             u'      * 3\n'
             u'    * 4\n'
             u'  * 5\n'
             u'</pre>\n'
             u'    <div class="br">\n'
             u'      <h2>The Solar System</h2>\n'
             u'      <p>\n'
             u'        <em>Mercury</em> is the first planet.<br/>\n'
             u'        <em>Venus</em> is the second planet.\n'
             u'      </p>\n'
             u'      <p><em>Earth</em> is the third planet.</p>\n'
             u'      <ayame:remove>\n'
             u'        <p>\n'
             u'          <em>Mars</em> is the fourth planet.<br/>\n'
             u'          <em>Jupiter</em> is the fifth planet.\n'
             u'        </p>\n'
             u'      </ayame:remove>\n'
             u'      <ul>\n'
             u'        <li>\n'
             u'          1<br/>\n'
             u'          2<br/>\n'
             u'          3\n'
             u'        </li>\n'
             u'      </ul>\n'
             u'    </div>\n'
             u'    <form action="/" method="post">\n'
             u'      <fieldset>\n'
             u'        <legend>form</legend>\n'
             u'        <textarea>\n'
             u'          Sun\n'
             u'        </textarea>\n'
             u'      </fieldset>\n'
             u'    </form>\n'
             u'  </body>\n'
             u'</html>\n').format(doctype=markup.XHTML1_STRICT,
                                  xhtml=markup.XHTML_NS,
                                  ayame=markup.AYAME_NS)
    xhtml = xhtml.encode('iso-8859-1')

    m = markup.Markup()
    m.xml_decl = {'version': u'1.0',
                  'encoding': u'iso-8859-1'}
    m.lang = 'xhtml1'
    m.doctype = markup.XHTML1_STRICT
    m.root = new_element(u'html')
    m.root.attrib[new_qname(u'lang', ns=markup.XML_NS)] = u'en'
    m.root.ns[u'a'] = markup.XML_NS
    m.root.ns[u'b'] = markup.XHTML_NS
    m.root.ns[u'ayame'] = markup.AYAME_NS

    head = new_element(u'head')
    meta = new_element(u'meta')
    meta.attrib[new_qname(u'name')] = u'keywords'
    meta.attrib[new_qname(u'content')] = u''
    meta.children.append(u'a')
    head.children.append(meta)

    title = new_element(u'title')
    title.children.append(u'title')
    span = new_element(u'span')
    title.children.append(span)
    head.children.append(title)

    style = new_element(u'style')
    style.attrib[new_qname(u'type')] = u'text/css'
    style.children.append(u'\n'
                          u'      h1 {\n'
                          u'        font-size: 120%;\n'
                          u'      }\n'
                          u'\n'
                          u'      p {\n'
                          u'        font-size: 90%;\n'
                          u'      }\n'
                          u'\n')
    head.children.append(style)

    script = new_element(u'script')
    script.attrib[new_qname(u'type')] = u'text/javascript'
    script.children.append(u'\n'
                           u'     <!--\n'
                           u'     var x = 0;\n'
                           u'     var y = 0;\n'
                           u'     // -->\n'
                           u'\n')
    head.children.append(script)
    m.root.children.append(head)

    body = new_element(u'body')
    remove = new_element(u'remove', ns=markup.AYAME_NS)
    p = new_element(u'p')
    p.children.append(u'Hello World!')
    remove.children.append(p)
    body.children.append(remove)

    h1 = new_element(u'h1')
    h1.children.append(u'\n'
                       u'  spam\n')
    span = new_element(u'span')
    span.attrib[new_qname(u'class')] = u'yellow'
    span.children.append(u'\n'
                         u'  eggs  \n')
    h1.children.append(span)
    h1.children.append(u'\n'
                       u'  ham  \n')
    body.children.append(h1)

    blockquote = new_element(u'blockquote')
    blockquote.attrib[new_qname(u'cite')] = u'http://example.com/'
    blockquote.children.append(u'before')
    p = new_element(u'p')
    p.children.append(u'citation')
    blockquote.children.append(p)
    blockquote.children.append(u'after')
    body.children.append(blockquote)

    div = new_element(u'div')
    div.attrib[new_qname(u'class')] = u'text'
    div.children.append(u'\n'
                        u'spam   \n'
                        u'\n')
    i = new_element(u'i')
    i.children.append(u'eggs')
    div.children.append(i)
    div.children.append(u'  ham')
    body.children.append(div)

    div = new_element(u'div')
    div.attrib[new_qname(u'class')] = u'ayame'
    ins = new_element(u'ins')
    remove = new_element(u'remove', ns=markup.AYAME_NS)
    remove.children.append(u'spam')
    br = new_element(u'br', type=markup.Element.EMPTY)
    remove.children.append(br)
    remove.children.append(u'eggs')
    ins.children.append(remove)
    div.children.append(ins)
    p = new_element(u'p')
    remove = new_element(u'remove', ns=markup.AYAME_NS)
    remove.children.append(u'ham')
    p.children.append(remove)
    p.children.append(u'toast')
    div.children.append(p)
    ul = new_element(u'ul')
    container = new_element(u'container', ns=markup.AYAME_NS)
    container.attrib[markup.AYAME_ID] = u'a'
    li = new_element(u'li')
    li.children.append(u'spam')
    container.children.append(li)
    li = new_element(u'li')
    li.children.append(u'eggs')
    container.children.append(li)
    ul.children.append(container)
    div.children.append(ul)
    body.children.append(div)

    div = new_element(u'div')
    div.attrib[new_qname(u'class')] = u'block'
    div.children.append(u'Planets')
    ul = new_element(u'ul')
    li = new_element(u'li')
    li.children.append(u'\n'
                       u' Mercury '
                       u'\n')
    ul.children.append(li)
    li = new_element(u'li')
    li.children.append(u'  Venus  ')
    ul.children.append(li)
    li = new_element(u'li')
    li.children.append(u'Earth')
    ul.children.append(li)
    div.children.append(ul)
    div.children.append(u'\n')
    body.children.append(div)

    div = new_element(u'div')
    div.attrib[new_qname(u'class')] = u'inline-ins-del'
    p = new_element(u'p')
    del_ = new_element(u'del')
    del_.children.append(u'old')
    p.children.append(del_)
    ins = new_element(u'ins')
    ins.children.append(u'new')
    p.children.append(ins)
    div.children.append(p)
    body.children.append(div)

    div = new_element(u'div')
    div.attrib[new_qname(u'class')] = u'block-ins-del'
    del_ = new_element(u'del')
    pre = new_element(u'pre')
    pre.children.append(u'old')
    del_.children.append(pre)
    div.children.append(del_)
    ins = new_element(u'ins')
    pre = new_element(u'pre')
    pre.children.append(u'new')
    ins.children.append(pre)
    div.children.append(ins)
    body.children.append(div)

    pre = new_element(u'pre')
    pre.children.append(u'\n'
                        u'  * 1\n'
                        u'    * 2\n'
                        u'      * 3\n'
                        u'    * 4\n'
                        u'  * 5\n')
    body.children.append(pre)

    div = new_element(u'div')
    div.attrib[new_qname(u'class')] = u'br'
    h2 = new_element(u'h2')
    h2.children.append(u'The Solar System')
    div.children.append(h2)
    p = new_element(u'p')
    em = new_element(u'em')
    em.children.append(u'Mercury')
    p.children.append(em)
    p.children.append(u' is the first planet.')
    br = new_element(u'br', type=markup.Element.EMPTY)
    p.children.append(br)
    p.children.append(u'\n')
    em = new_element(u'em')
    em.children.append(u'Venus')
    p.children.append(em)
    p.children.append(u' is the second planet.')
    p.children.append(u'\n')
    div.children.append(p)
    div.children.append(u'\n')
    p = new_element(u'p')
    em = new_element(u'em')
    em.children.append(u'Earth')
    p.children.append(em)
    p.children.append(u' is the third planet.')
    div.children.append(p)
    remove = new_element(u'remove', ns=markup.AYAME_NS)
    p = new_element(u'p')
    em = new_element(u'em')
    em.children.append(u'Mars')
    p.children.append(em)
    p.children.append(u' is the fourth planet.')
    br = new_element(u'br', type=markup.Element.EMPTY)
    p.children.append(br)
    em = new_element(u'em')
    em.children.append(u'Jupiter')
    p.children.append(em)
    p.children.append(u' is the fifth planet.')
    remove.children.append(p)
    div.children.append(remove)
    ul = new_element(u'ul')
    li = new_element(u'li')
    li.children.append(u'1')
    br = new_element(u'br', type=markup.Element.EMPTY)
    li.children.append(br)
    li.children.append(u'2')
    br = new_element(u'br', type=markup.Element.EMPTY)
    li.children.append(br)
    li.children.append(u'3')
    ul.children.append(li)
    div.children.append(ul)
    div.children.append(u'\n')
    body.children.append(div)

    form = new_element(u'form')
    form.attrib[new_qname(u'action')] = u'/'
    form.attrib[new_qname(u'method')] = u'post'
    fieldset = new_element(u'fieldset')
    legend = new_element(u'legend')
    legend.children.append(u'form')
    fieldset.children.append(legend)
    textarea = new_element(u'textarea')
    textarea.children.append(u'Sun')
    fieldset.children.append(textarea)
    form.children.append(fieldset)
    body.children.append(form)
    m.root.children.append(body)

    eq_(renderer.render(test, m, pretty=True), xhtml)
