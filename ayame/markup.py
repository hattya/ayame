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

from __future__ import unicode_literals
from HTMLParser import HTMLParser
from collections import deque, namedtuple
import io
import re

from ayame import util
from ayame.exception import MarkupError, RenderingError


__all__ = ['XML_NS', 'XHTML_NS', 'AYAME_NS', 'XHTML1_STRICT', 'QName',
           'HTML', 'HEAD', 'DIV', 'AYAME_CONTAINER', 'AYAME_ENCLOSURE',
           'AYAME_EXTEND', 'AYAME_CHILD', 'AYAME_PANEL', 'AYAME_BORDER',
           'AYAME_BODY', 'AYAME_HEAD', 'AYAME_REMOVE', 'AYAME_ID',
           'MarkupType', 'Markup', 'Element', 'MarkupLoader', 'MarkupRenderer']

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

# from DTD
_empty = ('base', 'meta', 'link', 'hr', 'br', 'param', 'img', 'area', 'input',
          'col')
_pcdata = ('title', 'style', 'script', 'div', 'p', 'h1', 'h2', 'h3', 'h4',
           'h5', 'h6', 'li', 'dt', 'dd', 'address', 'pre', 'blockquote', 'ins',
           'del', 'a', 'span', 'bdo', 'em', 'strong', 'dfn', 'code', 'samp',
           'kbd', 'var', 'cite', 'abbr', 'acronym', 'q', 'sub', 'sup', 'tt',
           'i', 'b', 'big', 'small', 'object', 'label', 'option', 'textarea',
           'fieldset', 'legend', 'button', 'caption', 'th', 'td')

_block = ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'ul', 'ol', 'dl',
          'pre', 'hr', 'blockquote', 'address', 'fieldset', 'table')
_block_ex = _block + ('form', 'noscript', 'ins', 'del', 'script')

# regex: 2+ spaces
_space_re = re.compile('\s{2,}')

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
            raise MarkupError(object, (0, 0), 'could not load markup')

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
            if data == '':
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
            raise MarkupError(self._object, self.getpos(),
                              'multiple root element')
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
            raise MarkupError(self._object, self.getpos(),
                              'multiple root element')
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
            raise MarkupError(self._object, self.getpos(),
                              'unsupported html version')
        else:
            self._markup.doctype = '<!{}>'.format(decl)

    def handle_pi(self, data):
        if data.startswith('xml '):
            m = _xml_decl_re.match(data)
            if not m:
                raise MarkupError(self._object, self.getpos(),
                                  'malformed xml declaration')
            self._markup.lang = 'xml'

            for k, v in m.groupdict().iteritems():
                if v is None:
                    continue
                elif v[0] in ('"', "'"):
                    if v[-1] != v[0]:
                        raise MarkupError(self._object, self.getpos(),
                                          'mismatched quotes')
                    v = v.strip(v[0])
                self._markup.xml_decl[k] = v

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
        raise MarkupError(self._object, self.getpos(),
                          "'{}' for '{}' document is not implemented"
                          .format(name, self._markup.lang))

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
                raise MarkupError(
                        self._object, self.getpos(),
                        "unknown namespace prefix '{}'".format(prefix))
        else:
            uri = ns.get('', ns_uri_of(''))
            if uri is None:
                raise MarkupError(self._object, self.getpos(),
                                  'there is no default namespace')
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
                raise MarkupError(self._object, self.getpos(),
                                  'attribute {} already exist'.format(qname))
            element.attrib[qname] = v
        return element

    def xml_push(self, element):
        if not self._markup.xml_decl:
            raise MarkupError(self._object, self.getpos(),
                              'xml declaration is not found')
        self._push(element)

    def xml_pop(self, qname):
        if (self._ptr() == 0 or
            self._peek().qname != qname):
            raise MarkupError(
                    self._object, self.getpos(),
                    "end tag for element '{}' which is not open".format(qname))
        return self._pop()

    def xml_finish(self):
        if 0 < self._ptr():
            raise MarkupError(self._object, self.getpos(),
                              "end tag for element '{}' omitted"
                              .format(self._peek().qname))

    def new_xhtml1_element(self, name, attrs, type=None):
        return self.new_xml_element(name, attrs,
                                    type=type,
                                    default_ns=XHTML_NS)

    xhtml1_push = xml_push
    xhtml1_pop = xml_pop
    xhtml1_finish = xml_finish

class MarkupRenderer(object):

    _decl = {'compile_element': 'compile_{}_element',
             'indent_tag': 'indent_{}_tag',
             'render_start_tag': 'render_{}_start_tag',
             'render_end_tag': 'render_{}_end_tag',
             'render_text': 'render_{}_text'}

    def __init__(self):
        self.__stack = deque()
        self._cache = {}

        self._object = None
        self._buffer = None
        self._lang = None
        self._indent = 0

    def is_xml(self):
        return (self._lang == 'xml' or
                'xhtml' in self._lang)

    def render(self, object, markup, encoding='utf-8', indent=2, pretty=False):
        self.__stack.clear()
        self._cache.clear()

        self._object = object
        self._buffer = io.StringIO()
        self._lang = markup.lang.lower()
        self._indent = indent

        # render XML declaration
        if self.is_xml():
            self.render_xml_decl(markup.xml_decl, encoding)
        # render DOCTYPE
        self.render_doctype(markup.doctype)
        # render nodes
        if pretty:
            compile_element = self._impl_of('compile_element')
        else:
            compile_element = lambda element: (element, False)
        queue = deque()
        if isinstance(markup.root, Element):
            queue.append((-1, markup.root))
        while queue:
            index, node = queue.pop()
            if 0 < self._ptr():
                self._peek().pending -= 1
            if isinstance(node, Element):
                # render start or empty tag
                element, newline = compile_element(node)
                self._push(element, newline)
                if element.children:
                    element.type = Element.OPEN
                else:
                    element.type = Element.EMPTY
                self.render_start_tag(index, element)
                if element.type == Element.EMPTY:
                    self._pop()
                # push children
                child_index = len(element.children) - 1
                while 0 <= child_index:
                    queue.append((child_index, element.children[child_index]))
                    child_index -= 1
            elif isinstance(node, basestring):
                # render text
                self.render_text(index, node)
            else:
                raise RenderingError(self._object,
                                     "invalid type '{}'", type(node))
            # render end tag(s)
            while (0 < self._ptr() and
                   self._peek().pending == 0):
                self.render_end_tag(self._peek().element)
                self._pop()
        self._writeln()
        try:
            return self._buffer.getvalue().encode(encoding)
        finally:
            self._buffer.close()

    def render_xml_decl(self, xml_decl, encoding):
        self._write('<?xml',
                    # VersionInfo
                    ' version="', xml_decl.get('version', '1.0'), '"')
        # EncodingDecl
        encoding = xml_decl.get('encoding', encoding).upper()
        if (encoding != 'UTF-8' and
            'UTF-16' not in encoding):
            self._write(' encoding="', encoding, '"')
        # SDDecl
        standalone = xml_decl.get('standalone')
        if standalone:
            self._write(' standalone="', standalone, '"')
        self._writeln('?>')

    def render_doctype(self, doctype):
        if self._lang == 'xml':
            if doctype:
                self._writeln(doctype)
        elif self._lang == 'xhtml1':
            if doctype:
                self._writeln(doctype)
            else:
                self._writeln(XHTML1_STRICT)

    def render_start_tag(self, index, element):
        # stack pointer of parent element
        sp = self._ptr() - 2
        # indent start tag
        if (0 <= sp and
            self._at(sp).newline):
            self._impl_of('indent_tag')(self._at(sp).element, index)
        # render start tag
        self._impl_of('render_start_tag')(index, element)

    def render_end_tag(self, element):
        # indent end tag
        if self._peek().newline:
            self._impl_of('indent_tag')(None, -1)
        # render end tag
        self._impl_of('render_end_tag')(element)

    def render_text(self, index, text):
        self._impl_of('render_text')(index, text)

    def _write(self, *args):
        write = self._buffer.write
        for s in args:
            write(s)

    def _writeln(self, *args):
        self._write(*args + ('\n',))

    def _impl_of(self, name):
        # from method cache
        impl = self._cache.get(name)
        if impl is not None:
            return impl
        # from instance
        decl = MarkupRenderer._decl.get(name)
        if decl is not None:
            impl = getattr(self, decl.format(self._lang), None)
            if impl is not None:
                return self._cache.setdefault(name, impl)
        raise RenderingError(
                self._object,
                "'{}' for '{}' document is not implemented".format(name,
                                                                   self._lang))

    def _push(self, element, newline=False):
        self.__stack.append(_ElementState(element, newline))

    def _pop(self):
        return self.__stack.pop()

    def _peek(self):
        if 0 < self._ptr():
            return self.__stack[-1]

    def _at(self, index):
        return self.__stack[index]

    def _ptr(self):
        return len(self.__stack)

    def _count(self, ptr):
        count = i = 0
        while i < ptr:
            if self._at(i).element.type == Element.OPEN:
                count += 1
            i += 1
        return count

    def _prefix_for(self, ns_uri):
        i = self._ptr() - 1
        known_prefixes = []
        while 0 <= i:
            element = self._at(i).element
            if element.ns:
                for prefix in element.ns:
                    if prefix in known_prefixes:
                        raise RenderingError(self._object,
                                             "namespace URI for '{}' was "
                                             "overwritten".format(prefix))
                    elif element.ns[prefix] == ns_uri:
                        return prefix
                    known_prefixes.append(prefix)
            i -= 1
        raise RenderingError(self._object,
                             "unknown namespace URI '{}'".format(ns_uri))

    def _compile_children(self, parent, element=True, text=True, space=True):
        last = len(parent.children) - 1
        children = []
        shift_width = -1
        marks = []
        line_count = index = 0
        for node in parent.children:
            if isinstance(node, Element):
                if element:
                    children.append(node)
            elif isinstance(node, basestring):
                if (text and
                    node):
                    # strip newlines at the beginning of the 1st node
                    if index == 0:
                        node = node.lstrip('\r\n')
                    # calculate shift width
                    for l in node.splitlines():
                        # skip empty line
                        s = l.lstrip()
                        if s:
                            # number of leading spaces
                            sp_count = len(l) - len(s)
                            if space:
                                # 1+ spaces -> space
                                s = _space_re.sub(' ', s)
                                if 0 < sp_count:
                                    l = ''.join((' ' * sp_count, s))
                                    # order: element -> text
                                    if (children and
                                        isinstance(children[-1], Element)):
                                        children.append('')
                                else:
                                    l = s
                            # mark text node index
                            marks.append(len(children))
                            if (shift_width < 0 or
                                sp_count < shift_width):
                                shift_width = sp_count
                            children.append(l)
                            line_count += 1
                        elif (children and
                              isinstance(children[-1], Element)):
                            # order: element -> text
                            if space:
                                children.append('')
                            # count line if previous node is element
                            line_count += 1
                    if space:
                        if (index < last and
                            node[-1] in ('\r', '\n') and
                            (children and
                             isinstance(children[-1], basestring) and
                             not children[-1].endswith(' '))):
                            # newline -> space
                            children.append('')
                        elif (index == last and
                              (children and
                               isinstance(children[-1], basestring) and
                               children[-1].endswith(' '))):
                            # strip space at the end of the last node
                            children[-1] = children[-1][:-1]
            else:
                raise RenderingError(self._object,
                                     "invalid type '{}'", type(node))
            index += 1
        # remove indent
        if 0 < shift_width:
            for i in marks:
                children[i] = children[i][shift_width:]
        parent.children = children
        return parent, line_count

    def compile_xml_element(self, element):
        if element.children:
            element, line_count = self._compile_children(element, space=False)
        else:
            line_count = 0
        newline = (1 < line_count or
                   0 < len(element.children) - line_count)
        return element, newline

    def indent_xml_tag(self, parent, index):
        self._write('\n',
                    ' ' * (self._indent * self._count(self._ptr() - 1)))

    def render_xml_start_tag(self, index, element):
        prefix_for = self._prefix_for

        element_prefix = prefix_for(element.qname.ns_uri)
        self._write('<')
        if element_prefix != '':
            self._write(element_prefix, ':')
        self._write(element.qname.name)
        # xmlns attributes
        for prefix in sorted(element.ns):
            ns_uri = element.ns[prefix]
            if ns_uri != XML_NS:
                self._write(' xmlns')
                if prefix != '':
                    self._write(':', prefix)
                self._write('="', ns_uri, '"')
        # attributes
        attrib = [(prefix_for(a.ns_uri), a.name, v)
                  for a, v in element.attrib.iteritems()]
        default_ns = False
        for prefix, name, value in sorted(attrib):
            self._write(' ')
            if prefix == '':
                default_ns = True
            elif prefix != element_prefix:
                self._write(prefix, ':')
            elif (default_ns and
                  prefix == element_prefix):
                raise RenderingError(self._object,
                                     'cannout combine with default namespace')
            self._write(name, '="', value, '"')
        self._write('/>' if element.type == Element.EMPTY else '>')

    def render_xml_end_tag(self, element):
        prefix = self._prefix_for(element.qname.ns_uri)
        self._write('</')
        if prefix != '':
            self._write(prefix, ':')
        self._write(element.qname.name, '>')

    def render_xml_text(self, index, text):
        # indent
        if self._peek().newline:
            self._write('\n',
                        ' ' * (self._indent * self._count(self._ptr())))
        self._write(text)

    def compile_xhtml1_element(self, element):
        # reset XML and XHTML namespaces
        if element.qname == HTML:
            for prefix in tuple(element.ns):
                if element.ns[prefix] in (XML_NS, XHTML_NS):
                    del element.ns[prefix]
            element.ns['xml'] = XML_NS
            element.ns[''] = XHTML_NS
        # force element type as OPEN
        if element.type != Element.EMPTY:
            element.type = Element.OPEN
        return self.compile_html4_element(element)

    def indent_xhtml1_tag(self, parent, index):
        return self.indent_xml_tag(parent, index)

    def render_xhtml1_start_tag(self, index, element):
        for attr in element.attrib:
            if element.attrib[attr] is None:
                raise RenderingError(self._object,
                                     "'{}' attribute is None".format(attr))
        return self.render_xml_start_tag(index, element)

    render_xhtml1_end_tag = render_xml_end_tag

    def render_xhtml1_text(self, index, text):
        if self._peek().newline:
            if text != '':
                # indent
                self._write('\n',
                            ' ' * (self._indent * self._count(self._ptr())))
        elif text == '':
            # space
            self._write(' ')
        self._write(text)

    def compile_html4_element(self, element):
        name = element.qname.name
        newline = False
        if element.qname.ns_uri != XHTML_NS:
            element = self._compile_children(element)[0]
            newline = True
        elif name in _empty:
            element.children = []
        elif name not in _pcdata:
            element.children = [c for c in element.children
                                if not isinstance(c, basestring)]
            newline = True
        elif name in ('title', 'style', 'script', 'option', 'textarea'):
            element, line_count = self._compile_children(element,
                                                         element=False)
            newline = (name not in ('title', 'option') and
                       1 < line_count)
        elif name in ('div', 'li', 'dd', 'object', 'fieldset', 'button', 'th',
                      'td', 'ins', 'del'):
            element = self._compile_children(element)[0]
            newline = self._has_html4_block_element(element)
        elif name == 'blockquote':
            element = self._compile_children(element, text=False)[0]
            newline = True
        elif name == 'pre':
            return element, newline
        else:
            element = self._compile_children(element)[0]
        # remove leading spaces
        if not newline:
            i = len(element.children) - 1
            while 0 <= i:
                node = element.children[i]
                if isinstance(node, basestring):
                    element.children[i] = node.lstrip()
                i -= 1
        return element, newline

    def _has_html4_block_element(self, root):
        queue = deque()
        if isinstance(root, Element):
            queue.append(root)
        while queue:
            element = queue.pop()
            for node in element.children:
                if not isinstance(node, Element):
                    continue
                elif node.qname.ns_uri != XHTML_NS:
                    return True
                name = node.qname.name
                if name in ('ins', 'del'):
                    queue.appendleft(node)
                elif name in _block_ex:
                    return True

class _ElementState(object):

    __slots__ = ('element', 'pending', 'newline')

    def __init__(self, element, newline):
        # element
        self.element = element
        # number of pending children
        self.pending = len(element.children)
        # newline flag for children
        self.newline = newline
