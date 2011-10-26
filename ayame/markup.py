#
# ayame.markup
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

from HTMLParser import HTMLParser
from collections import deque, namedtuple
import io
import re

from ayame import util
from ayame.exception import MarkupError


__all__ = ['XML_NS', 'XHTML_NS', 'AYAME_NS', 'XHTML1_STRICT', 'QName',
           'HTML', 'HEAD', 'DIV', 'AYAME_CONTAINER', 'AYAME_ENCLOSURE',
           'AYAME_EXTEND', 'AYAME_CHILD', 'AYAME_PANEL', 'AYAME_BORDER',
           'AYAME_BODY', 'AYAME_HEAD', 'AYAME_REMOVE', 'AYAME_ID',
           'MarkupType', 'Markup', 'Element', 'MarkupLoader']

# namespace URI
XML_NS = 'http://www.w3.org/XML/1998/namespace'
XHTML_NS = 'http://www.w3.org/1999/xhtml'
AYAME_NS = 'http://hattya.github.com/ayame'

# XML declaration
_xml_decl_re = re.compile(r'''
    xml
    # VersionInfo
    \s*
    version\s*=\s*(?P<version>["']1.\d+["'])
    # EncodingDecl
    (?:
        \s*
        encoding\s*=\s*(?P<encoding>["'][a-zA-Z][a-zA-Z0-9._-]*["'])
    )?
    # SDDecl
    (?:
        \s*
        standalone\s*=\s*(?P<standalone>["'](?:yes|no)["'])
    )?
    \s*
    \?
    \Z
''', re.VERBOSE)

# DOCTYPE of (X)HTML
XHTML1_STRICT = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '
                 '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')
_xhtml1_strict_re = re.compile(
        'DOCTYPE\s+html\s+'
        'PUBLIC\s+"-//W3C//DTD XHTML 1.0 Strict//EN"\s+'
        '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"'
        '\Z')
_html_re = re.compile(
        'DOCTYPE\s+'
        '(?:HTML|html)\s+'
        'PUBLIC\s+')

class QName(namedtuple('QName', 'ns_uri, name')):

    __slots__ = ()

    def __repr__(self):
        return '{{{}}}{}'.format(*self)

# HTML elements
HTML = QName(XHTML_NS, 'html')
HEAD = QName(XHTML_NS, 'head')
DIV = QName(XHTML_NS, 'div')

# ayame elements
AYAME_CONTAINER = QName(AYAME_NS, 'container')
AYAME_ENCLOSURE = QName(AYAME_NS, 'enclosure')
AYAME_EXTEND = QName(AYAME_NS, 'extend')
AYAME_CHILD = QName(AYAME_NS, 'child')
AYAME_PANEL = QName(AYAME_NS, 'panel')
AYAME_BORDER = QName(AYAME_NS, 'border')
AYAME_BODY = QName(AYAME_NS, 'body')
AYAME_HEAD = QName(AYAME_NS, 'head')
AYAME_REMOVE = QName(AYAME_NS, 'remove')

# ayame attributes
AYAME_ID = QName(AYAME_NS, 'id')
#AYAME_CHILD = QName(AYAME_NS, 'child')

MarkupType = namedtuple('MarkupType', 'extension, mime_type')

class Markup(object):

    __slots__ = ('xml_decl', 'lang', 'doctype', 'root')

    def __init__(self):
        self.xml_decl = {}
        self.lang = None
        self.doctype = None
        self.root = None

class Element(object):

    __slots__ = ('qname', 'attrib', 'type', 'ns', 'children')

    OPEN = 1 << 0
    EMPTY = 1 << 1

    def __init__(self, qname, attrib=None, type=None, ns=None):
        self.qname = qname
        self.attrib = _AttributeDict()
        if attrib:
            self.attrib.update(attrib)
        self.type = type
        self.ns = {}
        if ns:
            self.ns.update(ns)
        self.children = []

    def __copy__(self):
        element = self.__class__(self.qname)
        element.attrib = self.attrib.copy()
        element.type = self.type
        element.ns = self.ns.copy()
        element.children = [c.copy() if isinstance(c, self.__class__) else c
                            for c in self.children]
        return element

    copy = __copy__

class _AttributeDict(util.FilterDict):

    __slots__ = ()

    def __convert__(self, key):
        if isinstance(key, QName):
            return QName(key.ns_uri, key.name.lower())
        elif isinstance(key, basestring):
            return key.lower()
        return key

class MarkupLoader(object, HTMLParser):

    _decl = {'new_element': 'new_{}_element',
             'push': '{}_push',
             'pop': '{}_pop',
             'finish': '{}_finish'}

    def __init__(self):
        HTMLParser.__init__(self)
        self.__stack = deque()
        self._cache = {}

        self._object = None
        self._markup = None
        self._text = None
        self._remove = False

    def load(self, object, src, encoding='utf-8', lang='xhtml1'):
        if isinstance(src, basestring):
            try:
                fp = io.open(src, encoding=encoding)
            except (IOError, OSError):
                fp = None
        else:
            fp = src
        if not fp:
            raise MarkupError(util.fqon_of(object), (0, 0),
                              'could not load markup')

        self.reset()
        self.__stack.clear()
        self._cache.clear()
        self._object = object
        self._markup = Markup()
        self._markup.lang = lang.lower()
        self._text = None
        self._remove = False

        while True:
            data = fp.read(8192)
            if data == b'':
                break
            self.feed(data)
        if isinstance(src, basestring):
            fp.close()
        self.close()
        return self._markup

    def close(self):
        HTMLParser.close(self)
        self._impl_of('finish')()

    def handle_starttag(self, name, attrs):
        if self._remove:
            return # children of ayame:remove
        # new element
        element = self._impl_of('new_element')(name, attrs)
        if (self._ptr() == 0 and
            self._markup.root is not None and
            element.qname != AYAME_REMOVE):
            self._throw('multiple root element')
        # push element
        self._impl_of('push')(element)
        if element.qname == AYAME_REMOVE:
            self._remove = True
            if 1 < self._ptr():
                # remove from parent element
                del self._at(-2).children[-1]
        elif self._markup.root is None:
            self._markup.root = element

    def handle_startendtag(self, name, attrs):
        if self._remove:
            return # children of ayame:remove
        # new element
        element = self._impl_of('new_element')(name, attrs, type=Element.EMPTY)
        if element.qname == AYAME_REMOVE:
            return
        elif (self._ptr() == 0 and
              self._markup.root is not None):
            self._throw('multiple root element')
        # push and pop element
        self._impl_of('push')(element)
        self._impl_of('pop')(element.qname)
        if self._markup.root is None:
            self._markup.root = element

    def handle_endtag(self, name):
        qname = self._new_qname(name)
        if qname == AYAME_REMOVE:
            # end tag of ayame:remove
            self._remove = False
        if self._remove:
            return # children of ayame:remove
        # pop element
        pos, element = self._impl_of('pop')(qname)

    def handle_data(self, data):
        if 0 < self._ptr():
            self._append_text(data)

    def handle_charref(self, name):
        if 0 < self._ptr():
            self._append_text('&#{};'.format(name))

    def handle_entityref(self, name):
        if 0 < self._ptr():
            self._append_text('&{};'.format(name))

    def handle_decl(self, decl):
        if _xhtml1_strict_re.match(decl):
            self._markup.lang = 'xhtml1'
            self._markup.doctype = XHTML1_STRICT
        elif _html_re.match(decl):
            self._throw('unsupported html version')
        else:
            self._markup.doctype = '<!' + decl + '>'

    def handle_pi(self, data):
        if not (data.startswith('xml ') and
                data.endswith('?')):
            return

        m = _xml_decl_re.match(data)
        if not m:
            self._throw('malformed xml declaration')
        self._markup.lang = 'xml'

        for k, v in m.groupdict().iteritems():
            if v is None:
                continue
            elif v[0] in ('"', "'"):
                if v[-1] != v[0]:
                    self._throw('mismatched quotes')
                v = v.strip(v[0])
            self._markup.xml_decl[k] = v

    def _throw(self, e, *args, **kwargs):
        raise MarkupError(util.fqon_of(self._object), self.getpos(),
                          e.format(*args, **kwargs))

    def _impl_of(self, name):
        # from method cache
        impl = self._cache.get(name)
        if impl is not None:
            return impl
        # from instance
        decl = MarkupLoader._decl.get(name)
        if decl is not None:
            impl = getattr(self, decl.format(self._markup.lang), None)
            if impl is not None:
                return self._cache.setdefault(name, impl)
        self._throw("'{}' for '{}' document is not implemented", name,
                    self._markup.lang)

    def _new_qname(self, name, ns=None):
        def ns_uri_of(prefix):
            i = self._ptr() - 1
            while 0 <= i:
                element = self._at(i)
                if (element.ns and
                    prefix in element.ns):
                    return element.ns[prefix]
                i -= 1

        ns = ns if ns else {}
        if ':' in name:
            prefix, name = name.split(':', 1)
            uri = ns.get(prefix, ns_uri_of(prefix))
            if uri is None:
                self._throw("unknown namespace prefix '{}'", prefix)
        else:
            uri = ns.get('', ns_uri_of(''))
            if uri is None:
                self._throw('there is no default namespace')
        return QName(uri, name)

    def _append_text(self, text):
        if self._remove:
            return # children of ayame:remove
        elif self._text is None:
            self._text = [text]
        else:
            self._text.append(text)

    def _push(self, element):
        if 0 < self._ptr():
            self._flush_text()
            self._peek().children.append(element)
        self.__stack.append((self.getpos(), element))

    def _pop(self):
        self._flush_text()
        return self.__stack.pop()

    def _flush_text(self):
        if self._text is not None:
            self._peek().children.append(''.join(self._text))
            self._text = None

    def _peek(self):
        if 0 < self._ptr():
            return self.__stack[-1][1]

    def _at(self, index):
        return self.__stack[index][1]

    def _ptr(self):
        return len(self.__stack)

    def new_xml_element(self, name, attrs, type=None, default_ns=''):
        if type is None:
            type = Element.OPEN
        # gather xmlns
        xmlns = {}
        for n, v in tuple(attrs):
            if n == 'xmlns':
                xmlns[''] = v
            elif n.startswith('xmlns:'):
                xmlns[n[6:]] = v
            else:
                continue
            attrs.remove((n, v))
        if self._ptr() == 0:
            # declare xml ns
            xmlns['xml'] = XML_NS
            # declare default ns
            if '' not in xmlns:
                xmlns[''] = default_ns

        new_qname = self._new_qname
        element = Element(qname=new_qname(name, xmlns),
                          type=type,
                          ns=xmlns.copy())
        # convert attr name to qname
        xmlns[''] = element.qname.ns_uri
        for n, v in attrs:
            qname = new_qname(n, xmlns)
            if qname in element.attrib:
                self._throw('attribute {} already exist', qname)
            element.attrib[qname] = v
        return element

    def xml_push(self, element):
        if not self._markup.xml_decl:
            self._throw('xml declaration is not found')
        self._push(element)

    def xml_pop(self, qname):
        if (self._ptr() == 0 or
            self._peek().qname != qname):
            self._throw("end tag for element '{}' which is not open", qname)
        return self._pop()

    def xml_finish(self):
        if 0 < self._ptr():
            self._throw("end tag for element '{}' omitted", self._peek().qname)

    def new_xhtml1_element(self, name, attrs, type=None):
        return self.new_xml_element(name, attrs,
                                    type=type,
                                    default_ns=XHTML_NS)

    xhtml1_push = xml_push
    xhtml1_pop = xml_pop
    xhtml1_finish = xml_finish
