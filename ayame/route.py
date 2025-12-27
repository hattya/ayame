#
# ayame.route
#
#   Copyright (c) 2011-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import collections
from collections.abc import Callable, Iterable, Iterator, Mapping
import re
from typing import overload, Any, Literal
import urllib.parse

from . import http, uri, util
from ._typing import WSGIEnvironment
from .exception import _RequestSlash, RouteError


__all__ = ['Rule', 'Map', 'Router', 'Converter']

_rule_re = re.compile(r"""
    (?P<static>[^<]*)
    <
        (?P<variable>[a-zA-Z] [a-zA-Z0-9_-]*)
        (?:
            :
            (?P<converter>[a-zA-Z_] [a-zA-Z0-9_-]*)
            (?:
                \( (?P<args>.*?) \)
            )?
        )?
    >
""", re.VERBOSE)
_simple_rule_re = re.compile(r'<([^>]+)>')

_args_re = re.compile(r"""
    \s*
    (?:
        (?P<name>\w+) \s* = \s*
    )?
    (?P<value>
        (?P<const>
            None |
            True |
            False
        ) |
        (?P<float>
            [+-]?
            (?:
                (?:
                    \d+ |
                    \d* \. \d+ |
                    \d+ \.
                )
                [eE] [+-]? \d+
            ) |
            (?:
                \d* \. \d+ |
                \d+ \.
            )
        ) |
        (?P<int>
            [+-]?
            (?:
               [1-9] \d* |
               0 [oO] [0-7]+ |
               0 [xX] [\da-fA-F]+ |
               0 [bB] [01]+ |
               0+
            )
        ) |
        (?P<str>
            ".*? (?<!\\)(?:\\\\)*" |
            '.*? (?<!\\)(?:\\\\)*'
        )
    )
    (?P<error>[^,]*?)
    \s*
    (?P<sep>
        , \s* |
        \Z
    )
""", re.VERBOSE)
_sep_re = re.compile(r'[\s,]')


class Rule:

    __map: Map | None

    _regex: re.Pattern[str] | None
    _segs: list[tuple[bool, str]]
    _convs: dict[str, Converter]
    _vars: set[str]

    def __init__(self, path: str, object: Any, methods: Iterable[str] | None = None, redirection: bool = False) -> None:
        self.__map = None
        self.__path = path
        self.__leaf = not path.endswith('/')
        self.__object = object
        self.__methods = tuple({m.upper() for m in methods}) if methods else ('GET', 'POST')
        self.__redirection = redirection

        self._regex = None
        self._segs = []
        self._convs = {}
        self._vars = set()

    @property
    def map(self) -> Map | None:
        return self.__map

    @property
    def path(self) -> str:
        return self.__path

    @property
    def object(self) -> Any:
        return self.__object

    @property
    def methods(self) -> tuple[str, ...]:
        return self.__methods

    def is_leaf(self) -> bool:
        return self.__leaf

    def has_redirect(self) -> bool:
        return self.__redirection

    def bind(self, map: Map) -> None:
        if self.map is not None:
            raise RouteError(f'rule {self!r} already bound to map {self.map!r}')
        self.__map = map
        self._compile()

    def _compile(self) -> None:
        assert self.map is not None, 'rule not bound to map'
        path = self.path if self.is_leaf() else self.path.rstrip('/')

        self._segs = []
        self._convs.clear()
        self._vars.clear()

        conv: Converter | str | None
        buf = [r'\A']
        for var, conv, args in self._parse(path):
            if conv is None:
                buf.append(re.escape(var))
                self._segs.append((False, var))
            elif var in self._vars:
                raise RouteError(f"variable name '{var}' already in use")
            elif conv not in self.map.converters:
                raise RouteError(f"converter '{conv}' not found")
            else:
                if args:
                    a, kw = self._parse_args(args)
                    conv = self.map.converters[conv](self.map, *a, **kw)
                else:
                    conv = self.map.converters[conv](self.map)
                buf.append(fr'(?P<{var}>{conv.pattern})')
                self._segs.append((True, var))
                self._convs[var] = conv
                self._vars.add(var)
        if not self.is_leaf():
            self._segs.append((False, '/'))
        buf.append(r'(?P<__slash__>/?)')
        buf.append(r'\Z')

        self._regex = re.compile(''.join(buf))

    def _parse(self, path: str) -> Iterator[tuple[str, str | None, str | None]]:
        pos = 0
        for m in _rule_re.finditer(path):
            g = m.groupdict()
            if g['static']:
                yield g['static'], None, None
            yield (g['variable'],
                   g['converter'] if g['converter'] else 'default',
                   g['args'] if g['args'] else None)
            pos = m.end()
        if pos < len(path):
            yield path[pos:], None, None

    def _parse_args(self, expr: str) -> tuple[tuple[Any, ...], dict[str, Any]]:
        def error(msg: str, offset: int) -> SyntaxError:
            return SyntaxError(msg, ('<args>', 1, offset, expr))

        pos = 0
        args = []
        kwargs: dict[str, Any] = {}
        for m in _args_re.finditer(expr):
            if m.group('error'):
                raise error('invalid syntax', m.start('error') + 1)

            name = m.group('name')
            if kwargs:
                if name is None:
                    raise error('non-keyword arg after keyword arg', m.endpos)
                elif name in kwargs:
                    raise error('keyword argument repeated', m.start('name') + 1)

            if (v := m.group('const')) is not None:
                match v:
                    case 'True':
                        v = True
                    case 'False':
                        v = False
                    case _:
                        v = None
            elif (v := m.group('int')) is not None:
                v = int(v, 0)
            elif (v := m.group('float')) is not None:
                v = float(v)
            else:
                v = m.group('str')
                q = v[0]
                v = str(v[1:-1].replace('\\' + q, q))

            if name is None:
                args.append(v)
            else:
                kwargs[name] = v
            pos = m.endpos

        if (pos != len(expr)
            and _sep_re.sub('', expr)):
            raise error('invalid syntax', max(pos, 1))
        return tuple(args), kwargs

    def match(self, path: str) -> dict[str, Any] | None:
        assert self.map is not None and self._regex is not None, 'rule not bound to map'
        m = self._regex.search(path)
        if not m:
            return None
        g = m.groupdict()
        slash = g.pop('__slash__')
        if (self.map.slash
            and not self.is_leaf()
            and not slash):
            raise _RequestSlash()

        values = {}
        for var, val in g.items():
            try:
                values[var] = self._convs[var].to_python(val)
            except ValueError:
                return None
        return values

    def build(self, values: Mapping[str, Any], anchor: Any = None, method: str | None = None, query: bool = True) -> str | None:
        assert self.map is not None, 'rule not bound to map'
        if not (method is None
                or method in self.methods):
            return None
        for var in self._vars:
            if var not in values:
                return None
        # path
        buf = []
        cache = {}
        for dyn, var in self._segs:
            if dyn:
                cache[var] = util.to_list(values[var])
                if not cache[var]:
                    return None
                val = cache[var].pop(0)
                try:
                    buf.append(self._convs[var].to_uri(val))
                except ValueError:
                    return None
            else:
                buf.append(var)
        # query
        if query:
            qsl = []
            for var, val in values.items():
                if val := cache[var] if var in cache else util.to_list(val):
                    qsl.append((util.to_bytes(var, self.map.encoding), [util.to_bytes(v, self.map.encoding) for v in val]))
            if qsl:
                buf.append('?')
                buf.append(urllib.parse.urlencode(sorted(qsl, key=self.map.sort_key), doseq=True))
        # anchor
        if anchor:
            buf.append('#')
            buf.append(uri.quote(anchor, encoding=self.map.encoding))
        return ''.join(buf)


class Map:

    converters: dict[str, type[Converter]]

    _rules: list[Rule]
    _ref: dict[Any, list[Rule]]

    def __init__(self, encoding: str = 'utf-8', slash: bool = True, converters: Mapping[str, type[Converter]] | None = None,
                 sort_key: Callable[[Any], Any] | None = None) -> None:
        self.encoding = encoding
        self.slash = slash
        self.converters = {
            'default': _StringConverter,
            'string': _StringConverter,
            'path': _PathConverter,
            'int': _IntegerConverter,
        }
        if converters:
            self.converters.update(converters)
        self.sort_key = sort_key

        self._rules = []
        self._ref = collections.defaultdict(list)

    def add(self, rule: Rule) -> None:
        rule.bind(self)
        self._rules.append(rule)
        self._ref[rule.object].append(rule)

    def connect(self, path: str, object: Any, methods: Iterable[str] | None = None) -> None:
        self.add(Rule(path, object, methods))

    def redirect(self, path: str, dest: Any, methods: Iterable[str] | None = None) -> None:
        self.add(Rule(path, dest, methods, True))

    def mount(self, path: str) -> _SubMap:
        return _SubMap(self, path)

    def bind(self, environ: WSGIEnvironment) -> Router:
        return Router(self, environ)


class _SubMap:

    def __init__(self, map: Map, path: str) -> None:
        self.map = map
        self.path = path

    def add(self, rule: Rule) -> None:
        self.map.add(Rule(self.path + rule.path, rule.object, rule.methods, rule.has_redirect()))

    def connect(self, path: str, object: Any, methods: Iterable[str] | None = None) -> None:
        self.map.add(Rule(self.path + path, object, methods))

    def redirect(self, path: str, dest: Any, methods: Iterable[str] | None = None) -> None:
        self.map.add(Rule(self.path + path, dest, methods, True))


class Router:

    def __init__(self, map: Map, environ: WSGIEnvironment) -> None:
        self.map = map
        self.environ = environ

    @overload
    def match(self, as_rule: Literal[True]) -> tuple[Rule, dict[str, Any]]: ...
    @overload
    def match(self, as_rule: Literal[False] = False) -> tuple[Any, dict[str, Any]]: ...

    def match(self, as_rule: bool = False) -> tuple[Rule | Any, dict[str, Any]]:
        def repl(m: re.Match[str]) -> str:
            assert values is not None
            var = m.group(1)
            return rule._convs[var].to_uri(values[var])

        path = self.environ['PATH_INFO']
        method = self.environ['REQUEST_METHOD']
        allow: set[str] = set()
        for rule in self.map._rules:
            try:
                values = rule.match(path)
            except _RequestSlash:
                environ = self.environ.copy()
                environ['PATH_INFO'] += '/'
                raise http.MovedPermanently(uri.request_uri(environ, True))
            if values is None:
                continue
            elif method not in rule.methods:
                allow.update(rule.methods)
                continue
            elif rule.has_redirect():
                location = _simple_rule_re.sub(repl, rule.object) if isinstance(rule.object, str) else rule.object(**values)
                environ = self.environ | {'PATH_INFO': location}
                raise http.MovedPermanently(uri.request_uri(environ, True))
            return rule if as_rule else rule.object, values
        if allow:
            raise http.NotImplemented(method, uri.request_path(self.environ))
        raise http.NotFound(uri.request_path(self.environ))

    def build(self, object: Any, values: Mapping[str, Any] | None = None, anchor: Any = None, method: str | None = None, query: bool = True,
              relative: bool = False) -> str:
        if values is None:
            values = {}

        for rule in self.map._ref.get(object, ()):
            path = rule.build(values, anchor, method, query)
            if path is None:
                continue
            elif relative:
                return path
            return uri.quote(self.environ.get('SCRIPT_NAME', '')) + path
        raise RouteError('no rule for building URI')


class Converter:

    pattern = r'[^/]+'

    def __init__(self, map: Map, *args: Any, **kwargs: Any) -> None:
        self.map = map

    def to_python(self, value: str) -> Any:
        return value

    def to_uri(self, value: Any) -> str:
        return uri.quote(value, encoding=self.map.encoding)


class _StringConverter(Converter):

    def __init__(self, map: Map, len: int | None = None, min: int | None = None) -> None:
        super().__init__(map)
        self.len = len
        self.min = min
        cnt: Any
        if min is not None:
            max = len if len is not None else ''
            cnt = fr'{min},{max}'
        elif len is not None:
            cnt = len
        else:
            cnt = '1,'
        self.pattern = fr'[^/]{{{cnt}}}'

    def to_uri(self, value: Any) -> str:
        uri = super().to_uri(value)
        if self.min is not None:
            if (len(uri) < self.min
                or (self.len is not None
                    and len(uri) > self.len)):
                raise ValueError()
        elif (self.len is not None
              and len(uri) != self.len):
            raise ValueError()
        return uri


class _PathConverter(Converter):

    pattern = r'[^/].*?'


class _IntegerConverter(Converter):

    pattern = r'\d+'

    def __init__(self, map: Map, digits: int | None = None, min: int | None = None, max: int | None = None) -> None:
        super().__init__(map)
        self.digits = digits
        self.min = min
        self.max = max
        if digits is not None:
            self.pattern = fr'\d{{{digits}}}'

    def to_python(self, value: str) -> int:
        v = int(value)
        if ((self.min is not None
             and v < self.min)
            or (self.max is not None
                and v > self.max)):
            raise ValueError()
        return v

    def to_uri(self, value: Any) -> str:
        v = self.to_python(value)
        if self.digits is not None:
            uri = f'{v:0{self.digits}d}'
            if len(uri) > self.digits:
                raise ValueError()
            return uri
        return str(v)
