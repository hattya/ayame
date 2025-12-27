#
# ayame.i18n
#
#   Copyright (c) 2012-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import collections
from collections.abc import Iterator, MutableMapping
import re
import sys
import types
from typing import IO

import ayame
from . import core, local, res
from ._typing import Locale
from .exception import ResourceError


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
_lcont_re = re.compile(r"""
    (?<!\\)(?:\\\\)* \\
    \Z
""", re.VERBOSE)
_ctrl_chr = {
    'f': '\f',
    'n': '\n',
    'r': '\r',
    't': '\t',
}


class Localizer:

    extension = '.properties'

    def get(self, component: core.Component, locale: Locale, key: str) -> str | None:
        for bundle, prefix in self._iter_resource(component, locale):
            if bundle:
                if prefix:
                    if (v := bundle.get(f'{prefix}.{key}')) is not None:
                        return v
                if (v := bundle.get(key)) is not None:
                    return v
        return None

    def _iter_resource(self, component: core.Component, locale: Locale) -> Iterator[tuple[dict[str, str] | None, str]]:
        rl: res.ResourceLoader = component.config['ayame.resource.loader']
        sep: str = component.config['ayame.markup.separator']
        cache: MutableMapping[str, tuple[float, dict[str, str]]] = component.config['ayame.i18n.cache']

        def load(module: types.ModuleType, *args: str) -> dict[str, str] | None:
            name = '_'.join(args)
            key = f'{module.__name__}:{name}'
            try:
                mtime, bundle = cache[key]
            except KeyError:
                mtime, bundle = -1, None
            try:
                if (r := rl.load(module, name + self.extension)).mtime > mtime:
                    with r.open() as fp:
                        bundle = self._load(fp)
                    cache[key] = (r.mtime, bundle)
            except (OSError, ResourceError):
                bundle = None
                try:
                    del cache[key]
                except KeyError:
                    pass
            return bundle

        for cls, scope, prefix in self._iter_class(component):
            if m := sys.modules.get(cls.__module__):
                n = sep.join(c.__name__ for c in scope + (cls,)) if scope else cls.__name__
                lc, cc = locale[:2]
                if lc:
                    if cc:
                        yield load(m, n, lc, cc), prefix
                    yield load(m, n, lc), prefix
                yield load(m, n), prefix

    def _iter_class(self, component: core.Component) -> Iterator[tuple[type, tuple[type, ...], str]]:
        queue: collections.deque[tuple[type, tuple[type, ...], str]] = collections.deque()
        path = component.path().split(':')
        scope: tuple[type, ...] = ()
        for i, c in enumerate(reversed(tuple(component.iter_parent()))):
            cls = type(c)
            if cls.markup_type.scope:
                scope = cls.markup_type.scope
            queue.appendleft((cls, scope, '.'.join(path[i:])))
        queue.appendleft((type(component), self._scope_of(type(component)), ''))
        queue.appendleft((type(local.app()), (), ''))

        while queue:
            cls, scope, prefix = queue.pop()
            yield cls, scope, prefix
            if (not self._is_base_class(cls)
                and cls.__bases__):
                queue.extend((c, self._scope_of(c), prefix) for c in cls.__bases__
                             if self._is_target_class(c))

    def _is_base_class(self, cls: type) -> bool:
        return cls in (core.Page, core.MarkupContainer, core.Component, ayame.Ayame)

    def _is_target_class(self, cls: type) -> bool:
        return issubclass(cls, (core.Component, ayame.Ayame))

    def _scope_of(self, cls: type) -> tuple[type, ...]:
        if issubclass(cls, core.MarkupContainer):
            return cls.markup_type.scope
        return ()

    def _load(self, fp: IO[str]) -> dict[str, str]:
        match = _kv_re.match
        sub = _backslash_re.sub
        has_lcont = _lcont_re.search
        ctrl_get = _ctrl_chr.get

        def repl(m: re.Match[str]) -> str:
            ch = m.group(1)
            return ctrl_get(ch, ch)

        bundle = {}
        ll = []
        for l in fp:
            l = l.lstrip().rstrip('\n\r')
            if (not l
                or l[0] in ('#', '!')):
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
                key = l
                value = ''
            key = sub(repl, key)
            bundle[key] = value
        return bundle
