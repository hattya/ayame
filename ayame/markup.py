#
# ayame.markup
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import abc
import collections
import collections.abc
import html.parser
import io
import re

from . import util
from .exception import MarkupError, RenderingError


__all__ = ['XML_NS', 'XHTML_NS', 'AYAME_NS', 'XHTML1_STRICT', 'QName',
           'HTML', 'HEAD', 'DIV', 'AYAME_CONTAINER', 'AYAME_ENCLOSURE',
           'AYAME_EXTEND', 'AYAME_CHILD', 'AYAME_PANEL', 'AYAME_BORDER',
           'AYAME_BODY', 'AYAME_HEAD', 'AYAME_MESSAGE', 'AYAME_REMOVE',
           'AYAME_ID', 'AYAME_KEY', 'MarkupType', 'Markup', 'Element',
           'Fragment', 'MarkupLoader', 'MarkupRenderer', 'Space',
           'MarkupHandler', 'MarkupPrettifier', 'XMLHandler', 'XHTML1Handler']

# namespace URI
XML_NS = 'http://www.w3.org/XML/1998/namespace'
XHTML_NS = 'http://www.w3.org/1999/xhtml'
AYAME_NS = 'http://hattya.github.io/ayame'

# XML declaration
_xml_decl_re = re.compile(r"""
    \A
    xml
    # VersionInfo
    \s*
    version \s* = \s* (?P<version>["'] 1\.\d ["'])
    # EncodingDecl
    (?:
        \s*
        encoding \s* = \s* (?P<encoding>["'] [a-zA-Z] [a-zA-Z0-9._-]* ["'])
    )?
    # SDDecl
    (?:
        \s*
        standalone \s* = \s* (?P<standalone>["'] (?:yes | no) ["'])
    )?
    \s*
    \?
    \Z
""", re.VERBOSE)

# DOCTYPE of (X)HTML
XHTML1_STRICT = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"'
                 ' "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')
_xhtml1_strict_re = re.compile(r"""
    \A
    DOCTYPE \s+ html
    \s+
    PUBLIC \s+ "-//W3C//DTD\ XHTML\ 1\.0\ Strict//EN"
    \s+
    "http://www\.w3\.org/TR/xhtml1/DTD/xhtml1-strict\.dtd"
    \Z
""", re.VERBOSE)
_html_re = re.compile(r"""
    \A
    DOCTYPE \s+ [hH][tT][mM][lL]
""", re.VERBOSE)

# from DTD
_xhtml1_block = frozenset((
    'p',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',    # %heading;
    'div',
    'ul', 'ol', 'dl',                      # %lists;
    'pre', 'hr', 'blockquote', 'address',  # %blocktext;
    'fieldset',
    'table',
))
_xhtml1_Block = (
    _xhtml1_block | frozenset((
        'form',
        'noscript', 'ins', 'del', 'script',  # %misc;
    ))
)

_xhtml1__EMPTY__ = frozenset(('base', 'meta', 'link', 'hr', 'br', 'param',
                              'img', 'area', 'input', 'col'))
_xhtml1__Inline__ = frozenset(('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'dt',
                               'address', 'pre', 'a', 'span', 'bdo', 'em',
                               'strong', 'dfn', 'code', 'samp', 'kbd', 'var',
                               'cite', 'abbr', 'acronym', 'q', 'sub', 'sup',
                               'tt', 'i', 'b', 'big', 'small', 'label',
                               'legend', 'caption'))
_xhtml1__Flow__ = frozenset(('div', 'li', 'dd', 'ins', 'del', 'button', 'th', 'td'))
_xhtml1__PCDATA__ = frozenset(('title', 'style', 'script', 'option', 'textarea'))

_xhtml1_Block_all = _xhtml1_Block | _xhtml1__Flow__ | frozenset(('dt', 'legend', 'caption'))
_xhtml1__PCDATA__all = _xhtml1__Inline__ | _xhtml1__Flow__ | _xhtml1__PCDATA__ | frozenset(('object', 'fieldset'))


class QName(collections.namedtuple('QName', 'ns_uri, name')):

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
AYAME_MESSAGE = QName(AYAME_NS, 'message')
AYAME_REMOVE = QName(AYAME_NS, 'remove')

# ayame attributes
AYAME_ID = QName(AYAME_NS, 'id')
# AYAME_CHILD = QName(AYAME_NS, 'child')
AYAME_KEY = QName(AYAME_NS, 'key')
# AYAME_MESSAGE = QName(AYAME_NS, 'message')


MarkupType = collections.namedtuple('MarkupType', 'extension, mime_type, scope')


class Markup:

    __slots__ = ('xml_decl', 'lang', 'doctype', 'root')

    def __init__(self):
        self.xml_decl = {}
        self.lang = None
        self.doctype = None
        self.root = None

    def __copy__(self):
        m = self.__class__()
        m.xml_decl = self.xml_decl.copy()
        m.lang = self.lang
        m.doctype = self.doctype
        if self.root is not None:
            m.root = self.root.copy()
        return m

    def __getstate__(self):
        return (self.xml_decl, self.lang, self.doctype, self.root)

    def __setstate__(self, state):
        self.xml_decl, self.lang, self.doctype, self.root = state

    copy = __copy__


class Element:

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

    def __repr__(self):
        return f'<{util.fqon_of(self)} {self.qname!r} at 0x{id(self):x}>'

    def __bool__(self):
        return True

    def __len__(self):
        return self.children.__len__()

    def __getitem__(self, key):
        return self.children.__getitem__(key)

    def __setitem__(self, key, value):
        return self.children.__setitem__(key, value)

    def __delitem__(self, key):
        return self.children.__delitem__(key)

    def __copy__(self):
        elem = self.__class__(self.qname)
        elem.attrib = self.attrib.copy()
        elem.type = self.type
        elem.ns = self.ns.copy()
        elem.children = [n.copy() if isinstance(n, Element) else n
                         for n in self.children]
        return elem

    def __getstate__(self):
        return (self.qname, self.attrib, self.type, self.ns, self.children)

    def __setstate__(self, state):
        self.qname, self.attrib, self.type, self.ns, self.children = state

    copy = __copy__

    def append(self, node):
        self.children.append(node)

    def extend(self, nl):
        self.children.extend(nl)

    def insert(self, i, node):
        self.children.insert(i, node)

    def remove(self, node):
        self.children.remove(node)

    def walk(self, step=None):
        queue = collections.deque(((self, 0),))
        while queue:
            element, depth = queue.pop()
            yield element, depth
            # push child elements
            if (step is None
                or step(element, depth)):
                queue.extend((node, depth + 1) for node in reversed(element)
                             if isinstance(node, Element))

    def normalize(self):
        beg = end = 0
        children = []
        for i, node in enumerate(self):
            if isinstance(node, str):
                end = i + 1
            else:
                if beg < end:
                    children.append(''.join(self[beg:end]))
                children.append(node)
                beg = i + 1
        if beg < end:
            children.append(''.join(self[beg:end]))
        self[:] = children


class _AttributeDict(util.FilterDict):

    __slots__ = ()

    def __convert__(self, key):
        if isinstance(key, QName):
            return QName(key.ns_uri, key.name.lower())
        elif isinstance(key, str):
            return key.lower()
        return key


class Fragment(list):

    __slots__ = ()

    def __copy__(self):
        return self.__class__(node.copy() if isinstance(node, Element) else node
                              for node in self)

    copy = __copy__


_space_re = re.compile(r'\s{2,}')
_newline_re = re.compile(r'[\n\r]+')


class MarkupLoader(html.parser.HTMLParser):

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self._stack = collections.deque()
        self._cache = {}

    def load(self, object, src, lang='xhtml1'):
        self.reset()
        self._stack.clear()
        self._cache.clear()

        self._object = object
        self._markup = Markup()
        self._markup.lang = lang.lower()
        self._text = []
        self._remove = False

        while True:
            data = src.read(8192)
            if data == '':
                break
            self.feed(data)
        self.close()
        return self._markup

    def close(self):
        super().close()
        if self._stack:
            raise MarkupError(self._object, self.getpos(),
                              f"end tag for element '{self._peek().qname}' omitted")

    def handle_starttag(self, name, attrs):
        if self._remove:
            # children of ayame:remove element
            return
        # new element
        elem = self._new_element(name, attrs)
        if (not self._stack
            and self._markup.root is not None
            and elem.qname != AYAME_REMOVE):
            raise MarkupError(self._object, self.getpos(),
                              'there are multiple root elements')
        # push element
        self._push(elem)
        if elem.qname == AYAME_REMOVE:
            self._remove = True
            if len(self._stack) > 1:
                # remove from parent element
                del self._at(-2)[-1]
        elif self._markup.root is None:
            self._markup.root = elem

    def handle_startendtag(self, name, attrs):
        if self._remove:
            # children of ayame:remove element
            return
        # new element
        elem = self._new_element(name, attrs, type=Element.EMPTY)
        if elem.qname == AYAME_REMOVE:
            return
        elif (not self._stack
              and self._markup.root is not None):
            raise MarkupError(self._object, self.getpos(),
                              'there are multiple root elements')
        # push and pop element
        self._push(elem)
        if self._markup.root is None:
            self._markup.root = elem
        self._pop(elem.qname)

    def handle_endtag(self, name):
        qname = self._new_qname(name)
        if qname == AYAME_REMOVE:
            # end tag of ayame:remove element
            self._remove = False
        elif self._remove:
            # children of ayame:remove element
            return
        # pop element
        self._pop(qname)

    def handle_data(self, data):
        self._append_text(data)

    def handle_charref(self, name):
        self._append_text(''.join(('&#', name, ';')))

    def handle_entityref(self, name):
        self._append_text(''.join(('&', name, ';')))

    def handle_decl(self, decl):
        if _xhtml1_strict_re.match(decl):
            self._markup.lang = 'xhtml1'
            self._markup.doctype = XHTML1_STRICT
        elif _html_re.match(decl):
            raise MarkupError(self._object, self.getpos(),
                              'unsupported HTML version')
        else:
            self._markup.doctype = f'<!{decl}>'

    def handle_pi(self, data):
        if data.startswith('xml '):
            m = _xml_decl_re.match(data)
            if not m:
                raise MarkupError(self._object, self.getpos(),
                                  'malformed XML declaration')
            self._markup.lang = 'xml'

            for k, v in m.groupdict().items():
                if not v:
                    continue
                elif v[0] != v[-1]:
                    raise MarkupError(self._object, self.getpos(),
                                      'mismatched quotes')
                self._markup.xml_decl[k] = v.strip(v[0])

    def _new_qname(self, name, ns=None):
        def ns_uri_of(pfx):
            for i in range(len(self._stack) - 1, -1, -1):
                elem = self._at(i)
                if pfx in elem.ns:
                    return elem.ns[pfx]

        if ns is None:
            ns = {}

        if ':' in name:
            prefix, name = name.split(':', 1)
            uri = ns[prefix] if prefix in ns else ns_uri_of(prefix)
            if uri is None:
                raise MarkupError(self._object, self.getpos(),
                                  f"unknown namespace prefix '{prefix}'")
        else:
            uri = ns[''] if '' in ns else ns_uri_of('')
            if uri is None:
                raise MarkupError(self._object, self.getpos(),
                                  'there is no default namespace')
        return QName(uri, name)

    def _append_text(self, text):
        if self._stack:
            if self._remove:
                # children of ayame:remove element
                return
            self._text.append(text)

    def _push(self, element):
        if self._stack:
            self._flush_text()
            self._peek().append(element)
        self._stack.append((self.getpos(), element))

    def _pop(self, qname):
        self._flush_text()
        if (not self._stack
            or self._peek().qname != qname):
            raise MarkupError(self._object, self.getpos(),
                              f"end tag for element '{qname}' which is not open")
        return self._stack.pop()

    def _flush_text(self):
        if self._text:
            self._peek().append(''.join(self._text))
            del self._text[:]

    def _peek(self):
        return self._stack[-1][1]

    def _at(self, index):
        return self._stack[index][1]

    def _new_element(self, name, attrs, type=Element.OPEN):
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

        if not self._stack:
            if (self._markup.lang in ('xml', 'xhtml1')
                and not self._markup.xml_decl):
                raise MarkupError(self._object, self.getpos(),
                                  'XML declaration is not found')
            # declare xml ns
            xmlns['xml'] = XML_NS
            # declare default ns
            if '' not in xmlns:
                if self._markup.lang == 'xhtml1':
                    xmlns[''] = XHTML_NS
                else:
                    xmlns[''] = ''

        new_qname = self._new_qname
        elem = Element(new_qname(name, xmlns),
                       type=type,
                       ns=xmlns.copy())
        # convert attr name to qname
        xmlns[''] = elem.qname.ns_uri
        for n, v in attrs:
            qname = new_qname(n, xmlns)
            if qname in elem.attrib:
                raise MarkupError(self._object, self.getpos(),
                                  f"attribute '{qname}' already exists")
            elem.attrib[qname] = v
        return elem


class MarkupRenderer:

    _registry = {}

    @classmethod
    def register(cls, lang, handler):
        cls._registry[lang] = handler

    def __init__(self):
        self._stack = collections.deque()

    def render(self, object, markup, encoding='utf-8', pretty=False):
        self._stack.clear()

        self.object = object
        self._buf = io.StringIO()

        try:
            h = self._registry[markup.lang.lower()](self)
        except KeyError:
            raise RenderingError(self.object, f"unknown markup language '{markup.lang}'")
        if pretty:
            if not isinstance(pretty, collections.abc.Mapping):
                pretty = {}
            h = MarkupPrettifier(h, **pretty)

        # render XML declaration
        if h.xml:
            self.xml_decl(markup.xml_decl, encoding)
        # render DOCTYPE
        h.doctype(markup.doctype)
        # render nodes
        queue = collections.deque(((-1, markup.root),))
        while queue:
            index, node = queue.pop()
            if self._stack:
                self.peek().pending -= 1
            if isinstance(node, Element):
                # render start tag or empty tag
                node.type = Element.OPEN if not h.is_empty(node) else Element.EMPTY
                self.push(index, node)
                h.start_tag()
                if node.type == Element.OPEN:
                    # push children
                    queue.extend((i, node[i])
                                 for i in range(len(node) - 1, -1, -1))
                else:
                    self.pop()
            elif isinstance(node, str):
                # render text
                h.text(index, node)
            else:
                raise RenderingError(self.object, f"invalid type '{type(node)}'")
            # render end tags
            while (self._stack
                   and self.peek().pending == 0):
                h.end_tag()
                self.pop()
        self.writeln()
        try:
            return self._buf.getvalue().encode(encoding)
        finally:
            self._buf.close()

    def xml_decl(self, xml_decl, encoding):
        self.write('<?xml',
                   # VersionInfo
                   ' version="', xml_decl.get('version', '1.0'), '"')
        # EncodingDecl
        encoding = xml_decl.get('encoding', encoding).upper()
        if (encoding != 'UTF-8'
            and not encoding.startswith('UTF-16')):
            self.write(' encoding="', encoding, '"')
        # SDDecl
        standalone = xml_decl.get('standalone')
        if standalone:
            self.write(' standalone="', standalone, '"')

        self.writeln('?>')

    def write(self, *args):
        write = self._buf.write
        for s in args:
            write(s)

    def writeln(self, *args):
        self.write(*args + ('\n',))

    def push(self, index, element):
        self._stack.append(_ElementState(index, element))

    def pop(self):
        return self._stack.pop()

    def peek(self):
        return self._stack[-1]

    def at(self, index):
        return self._stack[index]

    def depth(self):
        return len(self._stack)

    def prefix_for(self, ns_uri):
        known = set()
        for i in range(len(self._stack) - 1, -1, -1):
            elem = self.at(i).element
            for pfx in elem.ns:
                if pfx in known:
                    raise RenderingError(self.object, f"namespace URI for '{pfx}' was overwritten")
                elif elem.ns[pfx] == ns_uri:
                    return pfx
                known.add(pfx)
        raise RenderingError(self.object, f"unknown namespace URI '{ns_uri}'")


class _ElementState:

    __slots__ = ('index', 'element', 'pending', 'flags')

    def __init__(self, index, element):
        # index in parent element
        self.index = index
        # element
        self.element = element
        # number of pending children
        self.pending = len(element)
        # indent flags for children
        self.flags = 0


class Space(str):

    __slots__ = ()

    def __repr__(self):
        return self.__class__.__name__


Space = Space()


class MarkupHandler(metaclass=abc.ABCMeta):

    INDENT_BEFORE = 1 << 0
    INDENT_INSIDE = 1 << 1
    INDENT_AFTER = 1 << 2
    INDENT_TEXT = 1 << 3
    INDENT_AROUND = INDENT_BEFORE | INDENT_AFTER
    INDENT_ALL = INDENT_AROUND | INDENT_INSIDE | INDENT_TEXT

    def __init__(self, renderer):
        self.renderer = renderer

    @abc.abstractproperty
    def xml(self):
        pass

    def doctype(self, doctype):
        if doctype:
            self.renderer.writeln(doctype)

    @abc.abstractmethod
    def is_empty(self, element):
        pass

    @abc.abstractmethod
    def start_tag(self):
        pass

    @abc.abstractmethod
    def end_tag(self):
        pass

    def text(self, index, text):
        if text:
            self.renderer.write(text)

    def indent(self, pos, indent):
        def next_nonblank(element, index):
            for node in element[index:]:
                if node:
                    return node

        r = self.renderer

        curr = r.peek()
        # calculate indent level
        lv = -1
        if pos == self.INDENT_BEFORE:
            if r.depth() > 1:
                lv = r.depth() - 1
        elif pos == self.INDENT_INSIDE:
            if curr.pending > 0:
                # after start tag
                lv = r.depth()
            else:
                # before end tag
                lv = r.depth() - 1
        elif pos == self.INDENT_AFTER:
            if (r.depth() > 1
                and next_nonblank(r.at(-2).element, curr.index + 1)):
                lv = r.depth() - 1
        elif pos == self.INDENT_TEXT:
            if not curr.flags & self.INDENT_TEXT:
                r.write(' ')
                return False
            lv = r.depth()
        # indent
        if lv >= 0:
            r.write('\n', ' ' * (indent * lv))
            return True
        return False

    def compile(self, element):
        flags = self.INDENT_AROUND
        children = []
        for node in element:
            if isinstance(node, Element):
                flags = self.INDENT_ALL
                children.append(node)
            elif isinstance(node, str):
                if not node:
                    continue
                # 2+ newlines -> newline
                node = _newline_re.sub('\n', node)

                first = True
                for l in node.splitlines(True):
                    s = l.lstrip()
                    if first:
                        first = False
                        if (s != l
                            and (children
                                 and children[-1] is not Space)):
                            children.append(Space)
                    if not s:
                        continue
                    # 2+ spaces -> space
                    l = _space_re.sub(' ', s)

                    s = l.rstrip()
                    children.append(s)
                    if s != l:
                        children.append(Space)
            else:
                raise RenderingError(self.renderer.object, f"invalid type '{type(node)}'")
        if (children
            and children[-1] is Space):
            flags = self.INDENT_ALL
            del children[-1]
        element.children = children
        return flags


class MarkupPrettifier(MarkupHandler):

    def __init__(self, handler, indent=2):
        self._handler = handler
        self._indent = indent
        self._bol = False

    @property
    def xml(self):
        return self._handler.xml

    def doctype(self, doctype):
        return self._handler.doctype(doctype)

    def is_empty(self, element):
        return self._handler.is_empty(element)

    def start_tag(self):
        h = self._handler

        curr = h.renderer.peek()
        curr.flags = h.compile(curr.element)
        curr.pending = len(curr.element)

        if (not self._bol
            and curr.flags & self.INDENT_BEFORE):
            h.indent(self.INDENT_BEFORE, self._indent)

        h.start_tag()

        pos = self.INDENT_INSIDE if curr.element.type == Element.OPEN else self.INDENT_AFTER
        if curr.flags & pos:
            self._bol = h.indent(pos, self._indent)
        else:
            self._bol = False

    def end_tag(self):
        h = self._handler

        curr = h.renderer.peek()
        if (not self._bol
            and curr.flags & self.INDENT_INSIDE):
            h.indent(self.INDENT_INSIDE, self._indent)

        h.end_tag()

        if curr.flags & self.INDENT_AFTER:
            self._bol = h.indent(self.INDENT_AFTER, self._indent)
        else:
            self._bol = False

    def text(self, index, text):
        h = self._handler

        if text is Space:
            if not self._bol:
                self._bol = h.indent(self.INDENT_TEXT, self._indent)
        else:
            h.text(index, text)

            if text:
                self._bol = False

    def indent(self, pos):
        return self._handler.indent(pos)

    def compile(self, element):
        return self._handler.compile(element)


class XMLHandler(MarkupHandler):

    xml = True

    def is_empty(self, element):
        return not element.children

    def start_tag(self, empty='/>'):
        r = self.renderer

        elem = r.peek().element
        epfx = r.prefix_for(elem.qname.ns_uri)
        r.write('<')
        if epfx != '':
            r.write(epfx, ':')
        r.write(elem.qname.name)
        # xmlns attributes
        for pfx in sorted(elem.ns):
            ns_uri = elem.ns[pfx]
            if ns_uri != XML_NS:
                r.write(' xmlns')
                if pfx != '':
                    r.write(':', pfx)
                r.write('="', ns_uri, '"')
        # attributes
        default_ns = False
        for pfx, n, v in sorted([(r.prefix_for(a.ns_uri), a.name, v)
                                 for a, v in elem.attrib.items()]):
            r.write(' ')
            if pfx == '':
                default_ns = True
            elif pfx != epfx:
                r.write(pfx, ':')
            elif default_ns:
                raise RenderingError(self.renderer.object, 'cannot combine with default namespace')
            r.write(n, '="', v, '"')
        r.write('>' if elem.type != Element.EMPTY else empty)

    def end_tag(self):
        r = self.renderer

        elem = r.peek().element
        pfx = r.prefix_for(elem.qname.ns_uri)
        r.write('</')
        if pfx != '':
            r.write(pfx, ':')
        r.write(elem.qname.name, '>')

    def compile(self, element):
        if element.children:
            return super().compile(element)
        return self.INDENT_AROUND


MarkupRenderer.register('xml', XMLHandler)


class XHTML1Handler(XMLHandler):

    def doctype(self, doctype):
        self.renderer.writeln(doctype if doctype else XHTML1_STRICT)

    def is_empty(self, element):
        return element.qname.name in _xhtml1__EMPTY__

    def start_tag(self):
        super().start_tag(' />')

    def compile(self, element):
        if element.qname.ns_uri != XHTML_NS:
            return super().compile(element)

        name = element.qname.name
        # reset XML and XHTML namespaces
        if name == 'html':
            for pfx in tuple(element.ns):
                if element.ns[pfx] in (XML_NS, XHTML_NS):
                    del element.ns[pfx]
            element.ns['xml'] = XML_NS
            element.ns[''] = XHTML_NS

        flags = 0
        if name in _xhtml1__EMPTY__:
            del element[:]
            if name == 'br':
                flags = self.INDENT_AFTER
            elif name not in ('img', 'input'):
                flags = self.INDENT_AROUND
        elif name not in _xhtml1__PCDATA__all:
            element[:] = (n for n in element
                          if not isinstance(n, str))
            flags = self.INDENT_ALL ^ self.INDENT_TEXT
        elif name == 'pre':
            flags = self.INDENT_AROUND
        elif name in _xhtml1__PCDATA__:
            flags = self.INDENT_AROUND
            children = []
            indent = 0
            for n in element:
                if isinstance(n, str):
                    for l in n.splitlines(True):
                        s = l.lstrip()
                        if not s:
                            continue
                        i = len(l) - len(s)
                        if (i > 0
                            and (indent == 0
                                 or i < indent)):
                            indent = i
                        s = l.rstrip()
                        children.append(s)
                        if s != l:
                            children.append(Space)
            if (children
                and children[-1] is Space):
                flags = self.INDENT_ALL
                del children[-1]
            if indent > 0:
                for i, s in enumerate(children):
                    if s is not Space:
                        children[i] = s[indent:]
            element.children = children
        else:
            super().compile(element)
            if name in ('fieldset', 'object'):
                flags = self.INDENT_ALL
            elif name in _xhtml1_Block_all:
                if self._has_block_element(element):
                    flags = self.INDENT_ALL
                elif self._has_br_element(element):
                    flags = self.INDENT_ALL ^ self.INDENT_TEXT
                elif name not in ('ins', 'del', 'button'):
                    flags = self.INDENT_AROUND
        return flags

    def _has_block_element(self, root):
        def step(element, depth):
            return (depth == 0
                    or (element.qname.ns_uri == XHTML_NS
                        and element.qname.name in ('ins', 'del', 'button')))

        for elem, depth in root.walk(step=step):
            if depth > 0:
                if elem.qname.ns_uri != XHTML_NS:
                    return True
                elif (elem.qname.name not in ('ins', 'del', 'button')
                      and elem.qname.name in _xhtml1_Block):
                    return True

    def _has_br_element(self, root):
        def step(element, depth):
            return element.qname.ns_uri == XHTML_NS

        for elem, depth in root.walk(step=step):
            if depth > 0:
                if elem.qname.name == 'br':
                    return True


MarkupRenderer.register('xhtml1', XHTML1Handler)
