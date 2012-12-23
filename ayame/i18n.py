#
# ayame.i18n
#
#   Copyright (c) 2012 Akinori Hattori <hattya@gmail.com>
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
import re
import sys

import ayame.app
import ayame.core
from ayame.exception import ResourceError
import ayame.local
import ayame.util


__all__ = ['Localizer']

_kv_re = re.compile(r"""
    \A
    (?P<key>
        .*? (?<!\\)(?:\\\\)*
    )
    (?:
        # separator
        (?:
            \s* [:=] \s*
        ) |
        \s+
    )
    (?P<value>.*)
    \Z
""", re.VERBOSE)
_backslash_re = re.compile(r'\\(.)')
_lcont_re = re.compile(r'(?<!\\)(?:\\\\)*\\$')
_ctrl_chr = {'f': '\f',
             'n': '\n',
             'r': '\r',
             't': '\t'}


class Localizer(object):

    extension = '.properties'

    def get(self, component, locale, key):
        for bundle, prefix in self._iter_resource(component, locale):
            if bundle:
                if prefix:
                    value = bundle.get(prefix + '.' + key)
                    if value is not None:
                        return value
                value = bundle.get(key)
                if value is not None:
                    return value

    def _iter_resource(self, component, locale):
        def load(module, *args):
            name = '_'.join(args)
            try:
                with ayame.util.load_data(module, name + self.extension) as fp:
                    return self._load(fp)
            except (IOError, ResourceError):
                pass

        for class_, prefix in self._iter_class(component):
            module = sys.modules.get(class_.__module__)
            if module:
                lc, cc = locale[:2]
                if lc:
                    if cc:
                        yield load(module, class_.__name__, lc, cc), prefix
                    yield load(module, class_.__name__, lc), prefix
                yield load(module, class_.__name__), prefix

    def _iter_class(self, component):
        queue = collections.deque(((ayame.local.app().__class__, ''),))
        if isinstance(component, ayame.core.Component):
            path = component.path().split(':')
            index = len(path)
            join = '.'.join
            queue.append((component.__class__, ''))
            for component in component.iter_parent():
                if 0 < index:
                    index -= 1
                queue.append((component.__class__, join(path[index:])))

        while queue:
            class_, prefix = queue.pop()
            yield class_, prefix
            if (not self.is_base_class(class_) and
                class_.__bases__):
                queue.extend((c, prefix) for c in class_.__bases__
                             if self.is_target_class(c))

    def is_target_class(self, class_):
        return issubclass(class_, (ayame.core.Component, ayame.app.Ayame))

    def is_base_class(self, class_):
        return class_ in (ayame.core.Page, ayame.core.MarkupContainer,
                          ayame.core.Component, ayame.app.Ayame)

    def _load(self, fp):
        def repl(m):
            ch = m.group(1)
            return ctrl_get(ch, ch)

        bundle = {}
        ll = []
        match = _kv_re.match
        sub = _backslash_re.sub
        has_lcont = _lcont_re.search
        ctrl_get = _ctrl_chr.get
        for l in fp:
            l = l.lstrip().rstrip('\n\r')
            if (not l or
                l[0] in ('#', '!')):
                # blank or comment line
                continue
            elif l[-1] == '\\':
                if has_lcont(l):
                    # found line continuation
                    ll.append(l[:-1])
                    continue
            if ll:
                ll.append(l)
                l = ''.join(ll)
                ll = []
            m = match(l)
            if m:
                key, value = m.groups()
                value = sub(repl, value)
            else:
                key, value = l, ''
            key = sub(repl, key)
            bundle[key] = value
        return bundle
