#
# ayame.markup
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

import collections
import io
import re

from ayame import _compat as five
from ayame.exception import MarkupError, RenderingError
import ayame.util


__all__ = ['XML_NS', 'XHTML_NS', 'AYAME_NS', 'XHTML1_STRICT', 'QName',
           'HTML', 'HEAD', 'DIV', 'AYAME_CONTAINER', 'AYAME_ENCLOSURE',
           'AYAME_EXTEND', 'AYAME_CHILD', 'AYAME_PANEL', 'AYAME_BORDER',
           'AYAME_BODY', 'AYAME_HEAD', 'AYAME_MESSAGE', 'AYAME_REMOVE',
           'AYAME_ID', 'AYAME_KEY', 'MarkupType', 'Markup', 'Element',
           'Fragment', 'MarkupLoader', 'MarkupRenderer']

# namespace URI
XML_NS = u'http://www.w3.org/XML/1998/namespace'
XHTML_NS = u'http://www.w3.org/1999/xhtml'
AYAME_NS = u'http://hattya.github.com/ayame'

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
        encoding \s* = \s* (?P<encoding>["'] [a-zA-Z][a-zA-Z0-9._-]* ["'])
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
XHTML1_STRICT = (u'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"'
                 u' "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')
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

# regex for pretty-print
_space_re = re.compile('\s{2,}')
_newline_re = re.compile('[\n\r]+')


class QName(collections.namedtuple('QName', 'ns_uri, name')):

    __slots__ = ()

    def __repr__(self):
        return u'{{{}}}{}'.format(*self)


# HTML elements
HTML = QName(XHTML_NS, u'html')
HEAD = QName(XHTML_NS, u'head')
DIV = QName(XHTML_NS, u'div')

# ayame elements
AYAME_CONTAINER = QName(AYAME_NS, u'container')
AYAME_ENCLOSURE = QName(AYAME_NS, u'enclosure')
AYAME_EXTEND = QName(AYAME_NS, u'extend')
AYAME_CHILD = QName(AYAME_NS, u'child')
AYAME_PANEL = QName(AYAME_NS, u'panel')
AYAME_BORDER = QName(AYAME_NS, u'border')
AYAME_BODY = QName(AYAME_NS, u'body')
AYAME_HEAD = QName(AYAME_NS, u'head')
AYAME_MESSAGE = QName(AYAME_NS, u'message')
AYAME_REMOVE = QName(AYAME_NS, u'remove')

# ayame attributes
AYAME_ID = QName(AYAME_NS, u'id')
#AYAME_CHILD = QName(AYAME_NS, u'child')
AYAME_KEY = QName(AYAME_NS, u'key')
#AYAME_MESSAGE = QName(AYAME_NS, u'message')


MarkupType = collections.namedtuple('MarkupType',
                                    'extension, mime_type, scope')


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
        element.children = [n.copy() if isinstance(n, Element) else n
                            for n in self.children]
        return element

    def __repr__(self):
        return '<{} {} at 0x{:x}>'.format(ayame.util.fqon_of(self),
                                          repr(self.qname), id(self))

    if five.PY2:
        def __nonzero__(self):
            return True
    else:
        def __bool__(self):
            return True

    def __len__(self):
        return self.children.__len__()

    def __getitem__(self, key):
        return self.children.__getitem__(key)

    def __setitem__(self, key, value):
        return self.children.__setitem__(key, value)

    def __delitem__(self, key):
        self.children.__delitem__(key)

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
            if (step is None or
                step(element, depth)):
                queue.extend((node, depth + 1) for node in reversed(element)
                             if isinstance(node, Element))

    def normalize(self):
        beg = end = 0
        children = []
        for i, node in enumerate(self):
            if isinstance(node, five.string_type):
                end = i + 1
            else:
                if beg < end:
                    children.append(u''.join(self[beg:end]))
                children.append(node)
                beg = i + 1
        if beg < end:
            children.append(u''.join(self[beg:end]))
        self[:] = children


class _AttributeDict(ayame.util.FilterDict):

    __slots__ = ()

    def __convert__(self, key):
        if isinstance(key, QName):
            return QName(key.ns_uri, key.name.lower())
        elif isinstance(key, five.string_type):
            return key.lower()
        return key


class Fragment(list):

    __slots__ = ()

    def __copy__(self):
        return self.__class__(n.copy() if isinstance(n, Element) else n
                              for n in self)

    copy = __copy__


class MarkupLoader(five.HTMLParser):

    _decl = {'new_element': 'new_{}_element',
             'push': '{}_push',
             'pop': '{}_pop',
             'finish': '{}_finish'}

    def __init__(self):
        super(MarkupLoader, self).__init__(convert_charrefs=False)
        self.__stack = collections.deque()
        self._cache = {}

        self._object = None
        self._markup = None
        self._text = None
        self._remove = False

    def load(self, object, src, encoding='utf-8', lang=u'xhtml1'):
        if isinstance(src, five.string_type):
            try:
                fp = io.open(src, encoding=encoding)
            except (OSError, IOError):
                fp = None
        else:
            fp = src
        if fp is None:
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
        if isinstance(src, five.string_type):
            fp.close()
        self.close()
        return self._markup

    def close(self):
        super(MarkupLoader, self).close()
        self._impl_of('finish')()

    def handle_starttag(self, name, attrs):
        if self._remove:
            # children of ayame:remove
            return
        # new element
        element = self._impl_of('new_element')(name, attrs)
        if (self._ptr() == 0 and
            self._markup.root is not None and
            element.qname != AYAME_REMOVE):
            raise MarkupError(self._object, self.getpos(),
                              'there are multiple root elements')
        # push element
        self._impl_of('push')(element)
        if element.qname == AYAME_REMOVE:
            self._remove = True
            if 1 < self._ptr():
                # remove from parent element
                del self._at(-2)[-1]
        elif self._markup.root is None:
            self._markup.root = element

    def handle_startendtag(self, name, attrs):
        if self._remove:
            # children of ayame:remove
            return
        # new element
        element = self._impl_of('new_element')(name, attrs, type=Element.EMPTY)
        if element.qname == AYAME_REMOVE:
            return
        elif (self._ptr() == 0 and
              self._markup.root is not None):
            raise MarkupError(self._object, self.getpos(),
                              'there are multiple root elements')
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
            # children of ayame:remove
            return
        # pop element
        pos, element = self._impl_of('pop')(qname)

    def handle_data(self, data):
        if 0 < self._ptr():
            self._append_text(data)

    def handle_charref(self, name):
        if 0 < self._ptr():
            self._append_text(u''.join(('&#', name, ';')))

    def handle_entityref(self, name):
        if 0 < self._ptr():
            self._append_text(u''.join(('&', name, ';')))

    def handle_decl(self, decl):
        if _xhtml1_strict_re.match(decl):
            self._markup.lang = u'xhtml1'
            self._markup.doctype = XHTML1_STRICT
        elif _html_re.match(decl):
            raise MarkupError(self._object, self.getpos(),
                              'unsupported HTML version')
        else:
            self._markup.doctype = u''.join(('<!', decl, '>'))

    def handle_pi(self, data):
        if data.startswith('xml '):
            m = _xml_decl_re.match(data)
            if not m:
                raise MarkupError(self._object, self.getpos(),
                                  'malformed XML declaration')
            self._markup.lang = u'xml'

            for k, v in five.items(m.groupdict()):
                if not v:
                    continue
                elif v[0] != v[-1]:
                    raise MarkupError(self._object, self.getpos(),
                                      'mismatched quotes')
                self._markup.xml_decl[k] = v.strip(v[0])

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
        msg = u"'{}' for '{}' document is not implemented".format(
            name, self._markup.lang)
        raise MarkupError(self._object, self.getpos(), msg)

    def _new_qname(self, name, ns=None):
        def ns_uri_of(prefix):
            for i in five.range(self._ptr() - 1, -1, -1):
                element = self._at(i)
                if (element.ns and
                    prefix in element.ns):
                    return element.ns[prefix]

        if ns is None:
            ns = {}

        if ':' in name:
            prefix, name = name.split(':', 1)
            uri = ns.get(prefix, ns_uri_of(prefix))
            if uri is None:
                raise MarkupError(
                    self._object, self.getpos(),
                    u"unknown namespace prefix '{}'".format(prefix))
        else:
            uri = ns.get('', ns_uri_of(''))
            if uri is None:
                raise MarkupError(self._object, self.getpos(),
                                  'there is no default namespace')
        return QName(uri, name)

    def _append_text(self, text):
        if self._remove:
            # children of ayame:remove
            return
        elif self._text is None:
            self._text = [text]
        else:
            self._text.append(text)

    def _push(self, element):
        if 0 < self._ptr():
            self._flush_text()
            self._peek().append(element)
        self.__stack.append((self.getpos(), element))

    def _pop(self):
        self._flush_text()
        return self.__stack.pop()

    def _flush_text(self):
        if self._text is not None:
            self._peek().append(u''.join(self._text))
            self._text = None

    def _peek(self):
        return self.__stack[-1][1]

    def _at(self, index):
        return self.__stack[index][1]

    def _ptr(self):
        return len(self.__stack)

    def new_xml_element(self, name, attrs, type=None, default_ns=u''):
        # gather xmlns
        xmlns = {}
        for n, v in tuple(attrs):
            if n == 'xmlns':
                xmlns[u''] = v
            elif n.startswith('xmlns:'):
                xmlns[n[6:]] = v
            else:
                continue
            attrs.remove((n, v))
        if self._ptr() == 0:
            # declare xml ns
            xmlns[u'xml'] = XML_NS
            # declare default ns
            if '' not in xmlns:
                xmlns[u''] = default_ns

        new_qname = self._new_qname
        element = Element(qname=new_qname(name, xmlns),
                          type=type if type is not None else Element.OPEN,
                          ns=xmlns.copy())
        # convert attr name to qname
        xmlns[u''] = element.qname.ns_uri
        for n, v in attrs:
            qname = new_qname(n, xmlns)
            if qname in element.attrib:
                raise MarkupError(
                    self._object, self.getpos(),
                    u"attribute '{}' already exists".format(qname))
            element.attrib[qname] = v
        return element

    def xml_push(self, element):
        if not self._markup.xml_decl:
            raise MarkupError(self._object, self.getpos(),
                              'XML declaration is not found')
        self._push(element)

    def xml_pop(self, qname):
        if (self._ptr() == 0 or
            self._peek().qname != qname):
            raise MarkupError(
                self._object, self.getpos(),
                u"end tag for element '{}' which is not open".format(qname))
        return self._pop()

    def xml_finish(self):
        if 0 < self._ptr():
            raise MarkupError(
                self._object, self.getpos(),
                u"end tag for element '{}' omitted".format(self._peek().qname))

    def new_xhtml1_element(self, name, attrs, type=None):
        return self.new_xml_element(name, attrs,
                                    type=type,
                                    default_ns=XHTML_NS)

    xhtml1_push = xml_push
    xhtml1_pop = xml_pop
    xhtml1_finish = xml_finish


class MarkupRenderer(object):

    _decl = {'compile_element': 'compile_{}_element',
             'indent': 'indent_{}',
             'render_start_tag': 'render_{}_start_tag',
             'render_end_tag': 'render_{}_end_tag',
             'render_text': 'render_{}_text'}

    def __init__(self):
        self.__stack = collections.deque()
        self._cache = {}

        self._object = None
        self._buffer = None
        self._lang = None
        self._indent = 0
        self._pretty = False
        self._bol = False

    def is_xml(self):
        return (self._lang == 'xml' or
                'xhtml' in self._lang)

    def is_empty_element(self, element):
        if ('html' in self._lang and
            element.qname.ns_uri == XHTML_NS):
            return element.qname.name in _empty
        return not element.children

    def render(self, object, markup, encoding='utf-8', indent=2, pretty=False):
        self.__stack.clear()
        self._cache.clear()

        self._object = object
        self._buffer = io.StringIO()
        self._lang = markup.lang.lower()
        self._indent = indent
        self._pretty = pretty
        self._bol = False

        # render XML declaration
        if self.is_xml():
            self.render_xml_decl(markup.xml_decl, encoding)
        # render DOCTYPE
        self.render_doctype(markup.doctype)
        # render nodes
        queue = collections.deque()
        if isinstance(markup.root, Element):
            queue.append((-1, markup.root))
        while queue:
            index, node = queue.pop()
            if 0 < self._ptr():
                self._peek().pending -= 1
            if isinstance(node, Element):
                # render start or empty tag
                if pretty:
                    element, newline = self._impl_of('compile_element')(node)
                else:
                    element, newline = node, 0
                if self.is_empty_element(element):
                    element.type = Element.EMPTY
                else:
                    element.type = Element.OPEN
                self._push(index, element, newline)
                self.render_start_tag()
                if element.type == Element.EMPTY:
                    self._pop()
                else:
                    # push children
                    queue.extend((i, element[i])
                                 for i in five.range(len(element) - 1, -1, -1))
            elif isinstance(node, five.string_type):
                # render text
                self.render_text(index, node)
            else:
                raise RenderingError(self._object,
                                     u"invalid type '{}'".format(type(node)))
            # render end tag(s)
            while (0 < self._ptr() and
                   self._peek().pending == 0):
                self.render_end_tag()
                self._pop()
        self._writeln()
        try:
            return self._buffer.getvalue().encode(encoding)
        finally:
            self._buffer.close()

    def render_xml_decl(self, xml_decl, encoding):
        self._write(u'<?xml',
                    # VersionInfo
                    u' version="', xml_decl.get('version', u'1.0'), u'"')
        # EncodingDecl
        encoding = xml_decl.get('encoding', encoding).upper()
        if (encoding != 'UTF-8' and
            'UTF-16' not in encoding):
            self._write(u' encoding="', encoding, u'"')
        # SDDecl
        standalone = xml_decl.get('standalone')
        if standalone:
            self._write(u' standalone="', standalone, u'"')
        self._writeln(u'?>')

    def render_doctype(self, doctype):
        if self._lang == 'xml':
            if doctype:
                self._writeln(doctype)
        elif self._lang == 'xhtml1':
            if doctype:
                self._writeln(doctype)
            else:
                self._writeln(XHTML1_STRICT)

    def render_start_tag(self):
        current = self._peek()
        # indent start tag
        if self._pretty:
            if self._impl_of('indent')('before'):
                self._bol = True
        # render start tag
        self._impl_of('render_start_tag')(current.index, current.element)
        self._bol = False
        # indent after empty tag or inside of start tag
        if self._pretty:
            if current.element.type == Element.EMPTY:
                mode = 'after'
            else:
                mode = 'inside'
            if self._impl_of('indent')(mode):
                self._bol = True

    def render_end_tag(self):
        current = self._peek()
        # indent end tag
        if self._pretty:
            if self._impl_of('indent')('inside'):
                self._bol = True
        # render end tag
        self._impl_of('render_end_tag')(current.element)
        self._bol = False
        # indent after end tag
        if self._pretty:
            if current.element.type == Element.OPEN:
                if self._impl_of('indent')('after'):
                    self._bol = True

    def render_text(self, index, text):
        # indent text
        if self._pretty:
            if self._impl_of('indent')('text', index, text):
                self._bol = True
        # render text
        if text:
            self._impl_of('render_text')(index, text)
            self._bol = False

    if five.PY2:
        def _write(self, *args):
            write = self._buffer.write
            for s in args:
                write(s if isinstance(s, five.str) else five.str(s))
    else:
        def _write(self, *args):
            write = self._buffer.write
            for s in args:
                write(s)

    def _writeln(self, *args):
        self._write(*args + (u'\n',))

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
        msg = u"'{}' for '{}' document is not implemented".format(name,
                                                                  self._lang)
        raise RenderingError(self._object, msg)

    def _push(self, index, element, newline=0):
        self.__stack.append(_ElementState(index, element, newline))

    def _pop(self):
        return self.__stack.pop()

    def _peek(self):
        return self.__stack[-1]

    def _at(self, index):
        return self.__stack[index]

    def _ptr(self):
        return len(self.__stack)

    def _count(self, ptr):
        count = 0
        for i in five.range(ptr):
            if self._at(i).element.type == Element.OPEN:
                count += 1
        return count

    def _prefix_for(self, ns_uri):
        known_prefixes = []
        for i in five.range(self._ptr() - 1, -1, -1):
            element = self._at(i).element
            if element.ns:
                for prefix in element.ns:
                    if prefix in known_prefixes:
                        raise RenderingError(self._object,
                                             u"namespace URI for '{}' was "
                                             u"overwritten".format(prefix))
                    elif element.ns[prefix] == ns_uri:
                        return prefix
                    known_prefixes.append(prefix)
        raise RenderingError(self._object,
                             u"unknown namespace URI '{}'".format(ns_uri))

    def _compile_children(self, parent, element=True, text=True, space=True):
        children = []
        shift_width = -1
        marks = []
        for node in parent:
            if isinstance(node, Element):
                if element:
                    children.append(node)
            elif isinstance(node, five.string_type):
                if (text and
                    node):
                    # normalize newlines
                    node = _newline_re.sub('\n', node)
                    lines = node.splitlines(True)
                    # process 1st line
                    if 0 < len(lines):
                        if space:
                            # 2+ spaces -> space
                            l = _space_re.sub(' ', lines[0])
                        else:
                            l = lines[0]

                        found = (children and
                                 children[-1] == '')
                        s = l.lstrip()
                        if s:
                            if (not found and
                                s != l):
                                children.append(u'')
                            t = s.rstrip()
                            children.append(t)
                            if t != s:
                                children.append(u'')
                        elif not found:
                            children.append(u'')
                    # calculate shift width
                    for l in lines[1:]:
                        s = l.lstrip()
                        if not s:
                            # skip empty line
                            continue
                        # number of leading spaces
                        cnt = len(l) - len(s)
                        if space:
                            # 2+ spaces -> space
                            s = _space_re.sub(' ', s)
                            l = u''.join((' ' * cnt, s)) if 0 < cnt else s
                        # mark text node index
                        marks.append(len(children))
                        if (shift_width < 0 or
                            cnt < shift_width):
                            shift_width = cnt
                        s = l.rstrip()
                        children.append(s)
                        if s != l:
                            children.append(u'')
            else:
                raise RenderingError(self._object,
                                     "invalid type '{}'".format(type(node)))
        # remove indent
        if 0 < shift_width:
            for i in marks:
                children[i] = children[i][shift_width:]
        parent[:] = children

    def compile_xml_element(self, element):
        if element.children:
            self._compile_children(element, space=False)
        return element, _ElementState.NEWLINE_ALL

    def indent_xml(self, name, *args):
        def next_nonblank(element, beg):
            for node in element[beg:]:
                if node != '':
                    return node

        def indent(off):
            self._write(u'\n',
                        u' ' * (self._indent * self._count(self._ptr() + off)))
            return True

        if self._bol:
            # beginning of line
            return

        current = self._peek()
        if name == 'before':
            if current.newline & _ElementState.NEWLINE_BEFORE:
                if 1 < self._ptr():
                    return indent(-1)
        elif name == 'inside':
            if current.newline & _ElementState.NEWLINE_INSIDE:
                if 0 < current.pending:
                    # after start tag
                    return indent(0)
                else:
                    # before end tag
                    return indent(-1)
        elif name == 'after':
            if current.newline & _ElementState.NEWLINE_AFTER:
                if self._ptr() < 2:
                    return
                parent = self._at(self._ptr() - 2)
                if next_nonblank(parent.element, current.index + 1):
                    return indent(-1)
        elif name == 'text':
            index, text = args
            if text != '':
                return
            elif (current.newline & _ElementState.NEWLINE_INSIDE and
                  not next_nonblank(current.element, index + 1)):
                return

            if current.newline & _ElementState.NEWLINE_TEXT:
                return indent(0)
            else:
                self._write(u' ')

    def render_xml_start_tag(self, index, element, empty=u'/>'):
        prefix_for = self._prefix_for

        element_prefix = prefix_for(element.qname.ns_uri)
        self._write(u'<')
        if element_prefix != '':
            self._write(element_prefix, u':')
        self._write(element.qname.name)
        # xmlns attributes
        for prefix in sorted(element.ns):
            ns_uri = element.ns[prefix]
            if ns_uri != XML_NS:
                self._write(u' xmlns')
                if prefix != '':
                    self._write(u':', prefix)
                self._write(u'="', ns_uri, u'"')
        # attributes
        attrib = [(prefix_for(a.ns_uri), a.name, v)
                  for a, v in five.items(element.attrib)]
        default_ns = False
        for prefix, name, value in sorted(attrib):
            self._write(u' ')
            if prefix == '':
                default_ns = True
            elif prefix != element_prefix:
                self._write(prefix, u':')
            elif (default_ns and
                  prefix == element_prefix):
                raise RenderingError(self._object,
                                     'cannot combine with default namespace')
            self._write(name, u'="', value, u'"')
        self._write(empty if element.type == Element.EMPTY else u'>')

    def render_xml_end_tag(self, element):
        prefix = self._prefix_for(element.qname.ns_uri)
        self._write(u'</')
        if prefix != '':
            self._write(prefix, u':')
        self._write(element.qname.name, u'>')

    def render_xml_text(self, index, text):
        self._write(text)

    def compile_xhtml1_element(self, element):
        # reset XML and XHTML namespaces
        if element.qname == HTML:
            for prefix in tuple(element.ns):
                if element.ns[prefix] in (XML_NS, XHTML_NS):
                    del element.ns[prefix]
            element.ns[u'xml'] = XML_NS
            element.ns[u''] = XHTML_NS
        # force element type as OPEN
        if element.type != Element.EMPTY:
            element.type = Element.OPEN
        return self.compile_html4_element(element)

    indent_xhtml1 = indent_xml

    def render_xhtml1_start_tag(self, index, element):
        for attr in element.attrib:
            if element.attrib[attr] is None:
                raise RenderingError(self._object,
                                     u"'{}' attribute is None".format(attr))
        return self.render_xml_start_tag(index, element, u' />')

    render_xhtml1_end_tag = render_xml_end_tag
    render_xhtml1_text = render_xml_text

    def compile_html4_element(self, element):
        name = element.qname.name
        newline = 0
        if element.qname.ns_uri != XHTML_NS:
            self._compile_children(element)
            newline = _ElementState.NEWLINE_ALL
        elif name in _empty:
            del element[:]
            if name == 'br':
                newline = _ElementState.NEWLINE_AFTER
            elif name not in ('img', 'input'):
                newline = _ElementState.NEWLINE_AROUND
        elif name not in _pcdata:
            element[:] = (n for n in element
                          if not isinstance(n, five.string_type))
            newline = (_ElementState.NEWLINE_AROUND |
                       _ElementState.NEWLINE_INSIDE)
        elif name in ('title', 'style', 'script', 'option', 'textarea'):
            self._compile_children(element, element=False)
            if name not in ('title', 'option'):
                newline = _ElementState.NEWLINE_ALL
            else:
                newline = _ElementState.NEWLINE_AROUND
        elif name == 'blockquote':
            self._compile_children(element, text=False)
            newline = (_ElementState.NEWLINE_AROUND |
                       _ElementState.NEWLINE_INSIDE)
        elif name == 'pre':
            return element, _ElementState.NEWLINE_AROUND
        else:
            self._compile_children(element)
            if name in ('div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li',
                        'dt', 'dd', 'th', 'td'):
                if self._has_html4_block_element(element):
                    newline = _ElementState.NEWLINE_ALL
                elif self._has_html4_br_element(element):
                    newline = (_ElementState.NEWLINE_AROUND |
                               _ElementState.NEWLINE_INSIDE)
                else:
                    newline = _ElementState.NEWLINE_AROUND
            elif name in ('ins', 'del', 'button'):
                if self._has_html4_block_element(element):
                    newline = _ElementState.NEWLINE_ALL
            elif name in ('address', 'legend', 'caption'):
                newline = _ElementState.NEWLINE_AROUND
            elif name in ('fieldset', 'object'):
                newline = _ElementState.NEWLINE_ALL
        return element, newline

    def _has_html4_block_element(self, root):
        def step(element, depth):
            return (depth == 0 or
                    (element.qname.ns_uri == XHTML_NS and
                     element.qname.name in ('ins', 'del', 'button')))

        for element, depth in root.walk(step=step):
            if 0 < depth:
                if element.qname.ns_uri != XHTML_NS:
                    return True
                elif (element.qname.name not in ('ins', 'del', 'button') and
                      element.qname.name in _block_ex):
                    return True

    def _has_html4_br_element(self, root):
        def step(element, depth):
            return element.qname.ns_uri == XHTML_NS

        for element, depth in root.walk(step=step):
            if 0 < depth:
                if element.qname.name == 'br':
                    return True


class _ElementState(object):

    __slots__ = ('index', 'element', 'pending', 'newline')

    NEWLINE_BEFORE = 1 << 0
    NEWLINE_AFTER = 1 << 1
    NEWLINE_AROUND = NEWLINE_BEFORE | NEWLINE_AFTER
    NEWLINE_INSIDE = 1 << 2
    NEWLINE_TEXT = 1 << 3
    NEWLINE_ALL = NEWLINE_AROUND | NEWLINE_INSIDE | NEWLINE_TEXT

    def __init__(self, index, element, newline=0):
        # index in parent element
        self.index = index
        # element
        self.element = element
        # number of pending children
        self.pending = len(element)
        # newline flag for children
        self.newline = newline
