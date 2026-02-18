#
# ayame.markup
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import abc
import collections
import collections.abc
from collections.abc import Callable, Iterable, Iterator, Mapping
import dataclasses
import enum
import html.parser
import io
import re
from typing import overload, Any, ClassVar, IO, NamedTuple, TypeAlias

from . import util
from ._typing import Self
from .exception import MarkupError, RenderingError


__all__ = ['XML_NS', 'XHTML_NS', 'AYAME_NS', 'XHTML1_STRICT', 'QName',
           'HTML', 'HEAD', 'DIV', 'AYAME_CONTAINER', 'AYAME_ENCLOSURE',
           'AYAME_EXTEND', 'AYAME_CHILD', 'AYAME_PANEL', 'AYAME_BORDER',
           'AYAME_BODY', 'AYAME_HEAD', 'AYAME_MESSAGE', 'AYAME_REMOVE',
           'AYAME_ID', 'AYAME_KEY', 'MarkupType', 'Markup', 'Element',
           'Fragment', 'MarkupLoader', 'MarkupRenderer', 'Node', 'Space',
           'MarkupHandler', 'MarkupPrettifier', 'XMLHandler', 'XHTML1Handler']

Node: TypeAlias = 'Element | str'

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


class QName(NamedTuple):

    ns_uri: str
    name: str

    def __repr__(self) -> str:
        return f'{{{self.ns_uri}}}{self.name}'


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


class MarkupType(NamedTuple):

    extension: str
    mime_type: str
    scope: tuple[type, ...]


class Markup:

    __slots__ = ('xml_decl', 'lang', 'doctype', 'root')

    xml_decl: dict[str, str]
    lang: str
    doctype: str
    root: Element | None

    def __init__(self) -> None:
        self.xml_decl = {}
        self.lang = ''
        self.doctype = ''
        self.root = None

    def __copy__(self) -> Self:
        m = type(self)()
        m.xml_decl = self.xml_decl.copy()
        m.lang = self.lang
        m.doctype = self.doctype
        if self.root is not None:
            m.root = self.root.copy()
        return m

    def __getstate__(self) -> tuple[dict[str, str], str, str, Element | None]:
        return self.xml_decl, self.lang, self.doctype, self.root

    def __setstate__(self, state: tuple[dict[str, str], str, str, Element | None]) -> None:
        self.xml_decl, self.lang, self.doctype, self.root = state

    copy = __copy__


class Element:

    __slots__ = ('qname', 'attrib', 'type', 'ns', 'children')

    children: list[Node]

    def __init__(self, qname: QName, attrib: Mapping[QName | str, str | None] | None = None,
                 type: Type | None = None, ns: dict[str, str] | None = None) -> None:
        self.qname = qname
        self.attrib = _AttributeDict()
        if attrib:
            self.attrib.update(attrib)
        self.type = type
        self.ns = {}
        if ns:
            self.ns.update(ns)
        self.children = []

    def __repr__(self) -> str:
        return f'<{util.fqon_of(self)} {self.qname!r} at 0x{id(self):x}>'

    def __bool__(self) -> bool:
        return True

    def __len__(self) -> int:
        return self.children.__len__()

    @overload
    def __getitem__(self, key: int) -> Node: ...
    @overload
    def __getitem__(self, key: slice) -> list[Node]: ...

    def __getitem__(self, key: Any) -> Any:
        return self.children.__getitem__(key)

    @overload
    def __setitem__(self, key: int, value: Node) -> None: ...
    @overload
    def __setitem__(self, key: slice, value: Iterable[Node]) -> None: ...

    def __setitem__(self, key: Any, value: Any) -> None:
        self.children.__setitem__(key, value)

    def __delitem__(self, key: int | slice) -> None:
        self.children.__delitem__(key)

    def __iter__(self) -> Iterator[Node]:
        return self.children.__iter__()

    def __copy__(self) -> Self:
        el = type(self)(self.qname)
        el.attrib = self.attrib.copy()
        el.type = self.type
        el.ns = self.ns.copy()
        el.children = [n.copy() if isinstance(n, Element) else n
                       for n in self.children]
        return el

    def __getstate__(self) -> tuple[QName, _AttributeDict, Type | None, dict[str, str], list[Node]]:
        return self.qname, self.attrib, self.type, self.ns, self.children

    def __setstate__(self, state: tuple[QName, _AttributeDict, Type | None, dict[str, str], list[Node]]) -> None:
        self.qname, self.attrib, self.type, self.ns, self.children = state

    copy = __copy__

    def append(self, node: Node) -> None:
        self.children.append(node)

    def extend(self, nl: Iterable[Node]) -> None:
        self.children.extend(nl)

    def insert(self, i: int, node: Node) -> None:
        self.children.insert(i, node)

    def remove(self, node: Node) -> None:
        self.children.remove(node)

    def walk(self, step: Callable[[Element, int], bool] | None = None) -> Iterator[tuple[Element, int]]:
        queue = collections.deque(((self, 0),))
        while queue:
            element, depth = queue.pop()
            yield element, depth
            # push child elements
            if (step is None
                or step(element, depth)):
                queue.extend((node, depth + 1)
                             for node in reversed(element)
                             if isinstance(node, Element))

    def normalize(self) -> None:
        children: list[Node] = []
        buf = []
        for node in self.children:
            if isinstance(node, str):
                buf.append(node)
            else:
                if buf:
                    children.append(''.join(buf))
                    buf.clear()
                children.append(node)
        if buf:
            children.append(''.join(buf))
        self.children[:] = children

    @enum.unique
    class Type(enum.Flag):

        OPEN = 1 << 0
        EMPTY = 1 << 1


class _AttributeDict(util.FilterDict[QName | str, str | None]):

    __slots__ = ()

    def __convert__(self, key: Any) -> QName | str:
        return QName(key.ns_uri, key.name.lower()) if isinstance(key, QName) else key.lower()


class Fragment(list[Node]):

    __slots__ = ()

    def __copy__(self) -> Self:
        return type(self)(node.copy() if isinstance(node, Element) else node
                          for node in self)

    copy = __copy__


_space_re = re.compile(r'\s{2,}')
_newline_re = re.compile(r'[\n\r]+')


class MarkupLoader(html.parser.HTMLParser):

    _stack: collections.deque[tuple[tuple[int, int], Element]]
    _text: list[str]

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._stack = collections.deque()

    def load(self, object: Any, src: IO[str], lang: str = 'xhtml1') -> Markup:
        self.reset()
        self._stack.clear()

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

    def close(self) -> None:
        super().close()
        if self._stack:
            raise MarkupError(self._object, self.getpos(),
                              f"end tag for element '{self._peek().qname}' omitted")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._remove:
            # children of ayame:remove element
            return
        # new element
        el = self._new_element(tag, attrs)
        if (not self._stack
            and self._markup.root is not None
            and el.qname != AYAME_REMOVE):
            raise MarkupError(self._object, self.getpos(),
                              'there are multiple root elements')
        # push element
        self._push(el)
        if el.qname == AYAME_REMOVE:
            self._remove = True
            if len(self._stack) > 1:
                # remove from parent element
                del self._at(-2)[-1]
        elif self._markup.root is None:
            self._markup.root = el

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._remove:
            # children of ayame:remove element
            return
        # new element
        el = self._new_element(tag, attrs, type=Element.Type.EMPTY)
        if el.qname == AYAME_REMOVE:
            return
        elif (not self._stack
              and self._markup.root is not None):
            raise MarkupError(self._object, self.getpos(),
                              'there are multiple root elements')
        # push and pop element
        self._push(el)
        if self._markup.root is None:
            self._markup.root = el
        self._pop(el.qname)

    def handle_endtag(self, tag: str) -> None:
        qname = self._new_qname(tag)
        if qname == AYAME_REMOVE:
            # end tag of ayame:remove element
            self._remove = False
        elif self._remove:
            # children of ayame:remove element
            return
        # pop element
        self._pop(qname)

    def handle_data(self, data: str) -> None:
        self._append_text(data)

    def handle_charref(self, name: str) -> None:
        self._append_text(f'&#{name};')

    def handle_entityref(self, name: str) -> None:
        self._append_text(f'&{name};')

    def handle_decl(self, decl: str) -> None:
        if _xhtml1_strict_re.match(decl):
            self._markup.lang = 'xhtml1'
            self._markup.doctype = XHTML1_STRICT
        elif _html_re.match(decl):
            raise MarkupError(self._object, self.getpos(),
                              'unsupported HTML version')
        else:
            self._markup.doctype = f'<!{decl}>'

    def handle_pi(self, data: str) -> None:
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

    def _new_qname(self, name: str, ns: dict[str, str] | None = None) -> QName:
        def ns_uri_of(pfx: str) -> str | None:
            for i in range(len(self._stack) - 1, -1, -1):
                if pfx in (el := self._at(i)).ns:
                    return el.ns[pfx]
            return None

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

    def _append_text(self, text: str) -> None:
        if self._stack:
            if self._remove:
                # children of ayame:remove element
                return
            self._text.append(text)

    def _push(self, element: Element) -> None:
        if self._stack:
            self._flush_text()
            self._peek().append(element)
        self._stack.append((self.getpos(), element))

    def _pop(self, qname: QName) -> tuple[tuple[int, int], Element]:
        self._flush_text()
        if (not self._stack
            or self._peek().qname != qname):
            raise MarkupError(self._object, self.getpos(),
                              f"end tag for element '{qname}' which is not open")
        return self._stack.pop()

    def _flush_text(self) -> None:
        if self._text:
            self._peek().append(''.join(self._text))
            self._text.clear()

    def _peek(self) -> Element:
        return self._stack[-1][1]

    def _at(self, index: int) -> Element:
        return self._stack[index][1]

    def _new_element(self, name: str, attrs: list[tuple[str, str | None]], type: Element.Type = Element.Type.OPEN) -> Element:
        # gather xmlns
        xmlns = {}
        for n, v in tuple(attrs):
            if n == 'xmlns':
                assert v is not None, f"'{n}' attribute requires value"
                xmlns[''] = v
            elif n.startswith('xmlns:'):
                assert v is not None, f"'{n}' attribute requires value"
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
        el = Element(new_qname(name, xmlns),
                     type=type,
                     ns=xmlns.copy())
        # convert attr name to qname
        xmlns[''] = el.qname.ns_uri
        for n, v in attrs:
            qname = new_qname(n, xmlns)
            if qname in el.attrib:
                raise MarkupError(self._object, self.getpos(),
                                  f"attribute '{qname}' already exists")
            el.attrib[qname] = v
        return el


class MarkupRenderer:

    _registry: ClassVar[dict[str, type[MarkupHandler]]] = {}
    _stack: collections.deque[_ElementState]

    @classmethod
    def register(cls, lang: str, handler: type[MarkupHandler]) -> None:
        cls._registry[lang] = handler

    def __init__(self) -> None:
        self._stack = collections.deque()

    def render(self, object: Any, markup: Markup, encoding: str = 'utf-8', pretty: bool | Mapping[str, Any] = False) -> bytes:
        self._stack.clear()

        self.object = object
        self._buf = io.StringIO()

        try:
            h = self._registry[markup.lang.lower()](self)
        except KeyError:
            raise RenderingError(self.object, f"unknown markup language '{markup.lang}'")
        if pretty:
            h = MarkupPrettifier(h, **pretty if isinstance(pretty, collections.abc.Mapping) else {})

        # render XML declaration
        if h.xml:
            self.xml_decl(markup.xml_decl, encoding)
        # render DOCTYPE
        h.doctype(markup.doctype)
        # render nodes
        queue: collections.deque[tuple[int, Any]] = collections.deque(((-1, markup.root),))
        while queue:
            index, node = queue.pop()
            if self._stack:
                self.peek().pending -= 1
            if isinstance(node, Element):
                # render start tag or empty tag
                node.type = Element.Type.OPEN if not h.is_empty(node) else Element.Type.EMPTY
                self.push(index, node)
                h.start_tag()
                if node.type == Element.Type.OPEN:
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

    def xml_decl(self, xml_decl: dict[str, str], encoding: str) -> None:
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

    def write(self, *args: str) -> None:
        write = self._buf.write
        for s in args:
            write(s)

    def writeln(self, *args: str) -> None:
        self.write(*args + ('\n',))

    def push(self, index: int, element: Element) -> None:
        self._stack.append(_ElementState(index, element))

    def pop(self) -> _ElementState:
        return self._stack.pop()

    def peek(self) -> _ElementState:
        return self._stack[-1]

    def at(self, index: int) -> _ElementState:
        return self._stack[index]

    def depth(self) -> int:
        return len(self._stack)

    def prefix_for(self, ns_uri: str) -> str:
        known = set()
        for i in range(len(self._stack) - 1, -1, -1):
            for pfx in (el := self.at(i).element).ns:
                if pfx in known:
                    raise RenderingError(self.object, f"namespace URI for '{pfx}' was overwritten")
                elif el.ns[pfx] == ns_uri:
                    return pfx
                known.add(pfx)
        raise RenderingError(self.object, f"unknown namespace URI '{ns_uri}'")


class IndentRule(enum.Flag):

    NONE = 0
    BEFORE = 1 << 0
    INSIDE = 1 << 1
    AFTER = 1 << 2
    TEXT = 1 << 3
    AROUND = BEFORE | AFTER
    ALL = BEFORE | AFTER | INSIDE | TEXT


@dataclasses.dataclass
class _ElementState:

    # index in parent element
    index: int
    # element
    element: Element
    # number of pending children
    pending: int = dataclasses.field(init=False)
    # indent rule for children
    rule: IndentRule = IndentRule.NONE

    def __post_init__(self) -> None:
        self.pending = len(self.element)


Space = type('Space', (str,), {'__repr__': lambda self: type(self).__name__})()


class MarkupHandler(metaclass=abc.ABCMeta):

    def __init__(self, renderer: MarkupRenderer) -> None:
        self.renderer = renderer

    @property
    @abc.abstractmethod
    def xml(self) -> bool:
        raise NotImplementedError

    def doctype(self, doctype: str) -> None:
        if doctype:
            self.renderer.writeln(doctype)

    @abc.abstractmethod
    def is_empty(self, element: Element) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def start_tag(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def end_tag(self) -> None:
        raise NotImplementedError

    def text(self, index: int, text: str) -> None:
        if text:
            self.renderer.write(text)

    def indent(self, rule: IndentRule, indent: int) -> bool:
        def next_nonblank(element: Element, index: int) -> bool:
            for node in element.children[index:]:
                if node:
                    return True
            return False

        r = self.renderer

        curr = r.peek()
        # calculate indent level
        lv = -1
        if rule == IndentRule.BEFORE:
            if r.depth() > 1:
                lv = r.depth() - 1
        elif rule == IndentRule.INSIDE:
            if curr.pending > 0:
                # after start tag
                lv = r.depth()
            else:
                # before end tag
                lv = r.depth() - 1
        elif rule == IndentRule.AFTER:
            if (r.depth() > 1
                and next_nonblank(r.at(-2).element, curr.index + 1)):
                lv = r.depth() - 1
        elif rule == IndentRule.TEXT:
            if not curr.rule & IndentRule.TEXT:
                r.write(' ')
                return False
            lv = r.depth()
        # indent
        if lv >= 0:
            r.write('\n', ' ' * (indent * lv))
            return True
        return False

    def compile(self, element: Element) -> IndentRule:
        rule = IndentRule.AROUND
        children: list[Node] = []
        for node in element.children:
            if isinstance(node, Element):
                rule = IndentRule.ALL
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
            rule = IndentRule.ALL
            del children[-1]
        element.children[:] = children
        return rule


class MarkupPrettifier(MarkupHandler):

    def __init__(self, handler: MarkupHandler, indent: int = 2) -> None:
        self._handler = handler
        self._indent = indent
        self._bol = False

    @property
    def xml(self) -> bool:
        return self._handler.xml

    def doctype(self, doctype: str) -> None:
        self._handler.doctype(doctype)

    def is_empty(self, element: Element) -> bool:
        return self._handler.is_empty(element)

    def start_tag(self) -> None:
        h = self._handler

        curr = h.renderer.peek()
        curr.rule = h.compile(curr.element)
        curr.pending = len(curr.element)

        if (not self._bol
            and curr.rule & IndentRule.BEFORE):
            h.indent(IndentRule.BEFORE, self._indent)

        h.start_tag()

        rule = IndentRule.INSIDE if curr.element.type == Element.Type.OPEN else IndentRule.AFTER
        if curr.rule & rule:
            self._bol = h.indent(rule, self._indent)
        else:
            self._bol = False

    def end_tag(self) -> None:
        h = self._handler

        curr = h.renderer.peek()
        if (not self._bol
            and curr.rule & IndentRule.INSIDE):
            h.indent(IndentRule.INSIDE, self._indent)

        h.end_tag()

        if curr.rule & IndentRule.AFTER:
            self._bol = h.indent(IndentRule.AFTER, self._indent)
        else:
            self._bol = False

    def text(self, index: int, text: str) -> None:
        h = self._handler

        if text is Space:
            if not self._bol:
                self._bol = h.indent(IndentRule.TEXT, self._indent)
        else:
            h.text(index, text)

            self._bol = False

    def indent(self, rule: IndentRule, indent: int = -1) -> bool:
        return self._handler.indent(rule, self._indent)

    def compile(self, element: Element) -> IndentRule:
        return self._handler.compile(element)


class XMLHandler(MarkupHandler):

    @property
    def xml(self) -> bool:
        return True

    def is_empty(self, element: Element) -> bool:
        return not element.children

    def start_tag(self, empty: str = '/>') -> None:
        r = self.renderer

        el = r.peek().element
        epfx = r.prefix_for(el.qname.ns_uri)
        r.write('<')
        if epfx != '':
            r.write(epfx, ':')
        r.write(el.qname.name)
        # xmlns attributes
        for pfx in sorted(el.ns):
            if (ns_uri := el.ns[pfx]) != XML_NS:
                r.write(' xmlns')
                if pfx != '':
                    r.write(':', pfx)
                r.write('="', ns_uri, '"')
        # attributes
        default_ns = False
        for pfx, n, v in sorted((r.prefix_for(a.ns_uri), a.name, v)
                                for a, v in el.attrib.items()
                                if isinstance(a, QName)):
            r.write(' ')
            if pfx == '':
                default_ns = True
            elif pfx != epfx:
                r.write(pfx, ':')
            elif default_ns:
                raise RenderingError(self.renderer.object, 'cannot combine with default namespace')
            r.write(n, '="', v or '', '"')
        r.write('>' if el.type != Element.Type.EMPTY else empty)

    def end_tag(self) -> None:
        r = self.renderer

        el = r.peek().element
        pfx = r.prefix_for(el.qname.ns_uri)
        r.write('</')
        if pfx != '':
            r.write(pfx, ':')
        r.write(el.qname.name, '>')

    def compile(self, element: Element) -> IndentRule:
        if element.children:
            return super().compile(element)
        return IndentRule.AROUND


MarkupRenderer.register('xml', XMLHandler)


class XHTML1Handler(XMLHandler):

    def doctype(self, doctype: str) -> None:
        self.renderer.writeln(doctype if doctype else XHTML1_STRICT)

    def is_empty(self, element: Element) -> bool:
        return element.qname.name in _xhtml1__EMPTY__

    def start_tag(self, empty: str = ' />') -> None:
        super().start_tag(empty)

    def compile(self, element: Element) -> IndentRule:
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

        rule = IndentRule.NONE
        if name in _xhtml1__EMPTY__:
            element.children.clear()
            if name == 'br':
                rule = IndentRule.AFTER
            elif name not in ('img', 'input'):
                rule = IndentRule.AROUND
        elif name not in _xhtml1__PCDATA__all:
            element.children[:] = (n for n in element.children
                                   if not isinstance(n, str))
            rule = IndentRule.ALL ^ IndentRule.TEXT
        elif name == 'pre':
            rule = IndentRule.AROUND
        elif name in _xhtml1__PCDATA__:
            rule = IndentRule.AROUND
            children: list[str] = []
            indent = 0
            for n in element.children:
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
                rule = IndentRule.ALL
                del children[-1]
            if indent > 0:
                for i, s in enumerate(children):
                    if s is not Space:
                        children[i] = s[indent:]
            element.children[:] = children
        else:
            super().compile(element)
            if name in ('fieldset', 'object'):
                rule = IndentRule.ALL
            elif name in _xhtml1_Block_all:
                if self._has_block_element(element):
                    rule = IndentRule.ALL
                elif self._has_br_element(element):
                    rule = IndentRule.ALL ^ IndentRule.TEXT
                elif name not in ('ins', 'del', 'button'):
                    rule = IndentRule.AROUND
        return rule

    def _has_block_element(self, root: Element) -> bool:
        def step(el: Element, depth: int) -> bool:
            return (depth == 0
                    or (el.qname.ns_uri == XHTML_NS
                        and el.qname.name in ('ins', 'del', 'button')))

        for el, depth in root.walk(step=step):
            if depth > 0:
                if el.qname.ns_uri != XHTML_NS:
                    return True
                elif (el.qname.name not in ('ins', 'del', 'button')
                      and el.qname.name in _xhtml1_Block):
                    return True
        return False

    def _has_br_element(self, root: Element) -> bool:
        def step(el: Element, _: int) -> bool:
            return el.qname.ns_uri == XHTML_NS

        for el, depth in root.walk(step=step):
            if depth > 0:
                if el.qname.name == 'br':
                    return True
        return False


MarkupRenderer.register('xhtml1', XHTML1Handler)
