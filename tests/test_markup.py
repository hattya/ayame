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

import io
import os
import tempfile

from nose.tools import assert_raises, eq_, ok_

from ayame import markup
from ayame.exception import MarkupError


def test_element():
    foo = markup.Element(markup.QName('foo', 'foo'),
                         attrib={'id': 'a'},
                         type=markup.Element.EMPTY,
                         ns={'': 'foo'})
    eq_(foo.qname, markup.QName('foo', 'foo'))
    eq_(foo.attrib, {'id': 'a'})
    eq_(foo.type, markup.Element.EMPTY)
    eq_(foo.ns, {'': 'foo'})
    eq_(repr(foo.qname), '{foo}foo')

    bar = foo.copy()
    foo.attrib[0] = 'a'
    eq_(foo.attrib, {'id': 'a', 0: 'a'})

    eq_(bar.qname, markup.QName('foo', 'foo'))
    eq_(bar.attrib, {'id': 'a'})
    eq_(bar.type, markup.Element.EMPTY)
    eq_(bar.ns, {'': 'foo'})
    eq_(repr(bar.qname), '{foo}foo')

def test_load_error():
    test = test_load_error

    # src is None
    loader = markup.MarkupLoader()
    assert_raises(MarkupError, loader.load, test, None)
    try:
        loader.load(test, None)
        ok_(False)
    except MarkupError as e:
        eq_(e.args[0], __name__ + '.test_load_error')
        eq_(e.args[1], (0, 0))

    # cannot open src
    src = ''
    loader = markup.MarkupLoader()
    assert_raises(MarkupError, loader.load, test, src, lang='')
    try:
        loader.load(test, src, lang='')
        ok_(False)
    except MarkupError as e:
        eq_(e.args[0], __name__ + '.test_load_error')
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
        eq_(e.args[0], __name__ + '.test_load_error')
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
        eq_(e.args[0], __name__ + '.test_load')
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
            eq_(e.args[0], __name__ + '.test_invalid_xml')
            eq_(e.args[1], pos)

    # malformed xml declaration
    assert_xml('<?xml standalone="yes"?>', (1, 0))

    # mismatched quotes in xml declaration
    assert_xml('<?xml version="1.0\'?>', (1, 0))
    assert_xml('<?xml version=\'1.0"?>', (1, 0))

    # no xml declaration
    assert_xml('<foo></foo>', (1, 0))

    # multiple root element
    assert_xml('<?xml version="1.0"?>'
               '<foo/>'
               '<bar/>',
               (1, 27))
    assert_xml('<?xml version="1.0"?>'
               '<foo></foo>'
               '<bar></bar>',
               (1, 32))

    # omitted end tag for root element
    assert_xml('<?xml version="1.0"?>'
               '<foo>',
               (1, 26))

    # mismatched tag
    assert_xml('<?xml version="1.0"?>'
               '<foo></bar>',
               (1, 26))

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
           '<!DOCTYPE test SYSTEM "foo.dtd">'
           '<foo xmlns="foo" id="a">'
           '&amp;'
           '<bar/>'
           '&#38;'
           'x'
           '</foo>')
    src = io.StringIO(xml.decode())
    loader = markup.MarkupLoader()
    m = loader.load(test, src, lang='xml')
    eq_(m.xml_decl, {'version': '1.0'})
    eq_(m.lang, 'xml')
    eq_(m.doctype, '<!DOCTYPE test SYSTEM "foo.dtd">')
    ok_(m.root)

    foo = m.root
    eq_(foo.qname, markup.QName('foo', 'foo'))
    eq_(foo.attrib, {markup.QName('foo', 'id'): 'a'})
    eq_(foo.type, markup.Element.OPEN)
    eq_(foo.ns, {'': 'foo', 'xml': markup.XML_NS})
    eq_(len(foo.children), 3)
    eq_(foo.children[0], '&amp;')
    eq_(foo.children[2], '&#38;x')

    bar = foo.children[1]
    eq_(bar.qname, markup.QName('foo', 'bar'))
    eq_(bar.attrib, {})
    eq_(bar.type, markup.Element.EMPTY)
    eq_(bar.ns, {})
    eq_(len(bar.children), 0)

def test_load_xml_with_prefix():
    test = test_load_xml_with_prefix

    xml = ('<?xml version="1.0"?>'
           '<foo xmlns="foo" xmlns:bar="bar">'
           '<bar:bar/>'
           '</foo>')
    src = io.StringIO(xml.decode())
    loader = markup.MarkupLoader()
    m = loader.load(test, src, lang='xml')
    eq_(m.xml_decl, {'version': '1.0'})
    eq_(m.lang, 'xml')
    ok_(m.doctype is None)
    ok_(m.root)

    foo = m.root
    eq_(foo.qname, markup.QName('foo', 'foo'))
    eq_(foo.attrib, {})
    eq_(foo.type, markup.Element.OPEN)
    eq_(foo.ns, {'': 'foo', 'bar': 'bar', 'xml': markup.XML_NS})
    eq_(len(foo.children), 1)

    bar = foo.children[0]
    eq_(bar.qname, markup.QName('bar', 'bar'))
    eq_(bar.attrib, {})
    eq_(bar.type, markup.Element.EMPTY)
    eq_(bar.ns, {})
    eq_(len(bar.children), 0)

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
        eq_(e.args[0], __name__ + '.test_load_xml_with_prefix')
        eq_(e.args[1], (1, 64))

    # no bar namespace
    class Loader(markup.MarkupLoader):
        def new_xml_element(self, *args, **kwargs):
            element = super(Loader, self).new_xml_element(*args, **kwargs)
            element.ns.pop('bar', None)
            return element
    src = io.StringIO(xml.decode())
    loader = Loader()
    assert_raises(MarkupError, loader.load, test, src, lang='xml')
    try:
        src.seek(0)
        loader.load(test, src, lang='xml')
        ok_(False)
    except MarkupError as e:
        eq_(e.args[0], __name__ + '.test_load_xml_with_prefix')
        eq_(e.args[1], (1, 54))

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
            eq_(e.args[0], __name__ + '.test_invalid_xhtml1')
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
