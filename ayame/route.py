#
# ayame.route
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

from collections import defaultdict
import os
import re
import sys
import urlparse
import urllib

from ayame import http, uri, util
from ayame.exception import RouteError, RequestSlash, ValidationError


__all__ = ['Rule', 'Map', 'Router', 'Converter']

_rule_re = re.compile(r'''
    (?P<static>[^<]*)
    <
        (?:
            (?P<converter>[a-zA-Z_][a-zA-Z0-9_-]*)
            (?:\((?P<args>.*?)\))?
            :
        )?
        (?P<variable>[a-zA-Z][a-zA-Z0-9_-]*)
    >
''', re.VERBOSE)
_simple_rule_re = re.compile(r'<([^>]+)>')

class Rule(object):

    def __init__(self, path, object, methods=None, redirection=False):
        self.__map = None
        self.__path = path
        self.__leaf = not path.endswith('/')
        self.__object = object
        if methods is None:
            self.__methods = ('GET', 'POST')
        else:
            self.__methods = tuple(set(m.upper() for m in methods))
        self.__redirection = redirection

        self._regex = None
        self._segments = []
        self._converters = {}
        self._variables = set()

    @property
    def map(self):
        return self.__map

    @property
    def path(self):
        return self.__path

    @property
    def object(self):
        return self.__object

    @property
    def methods(self):
        return self.__methods

    def is_leaf(self):
        return self.__leaf

    def has_redirect(self):
        return self.__redirection

    def bind(self, map):
        if self.map is not None:
            raise RouteError('rule {!r} already bound '
                             'to map {!r}'.format(self, self.map))
        self.__map = map
        self._compile()

    def _compile(self):
        assert self.map is not None, 'rule not bound to map'
        path = self.path if self.is_leaf() else self.path.rstrip('/')

        self._segments = []
        self._converters.clear()
        self._variables.clear()

        buf = ['^']
        for conv, args, var in self._parse(path):
            if conv is None:
                buf.append(re.escape(var))
                self._segments.append((False, var))
            elif var in self._variables:
                raise RouteError(
                        'variable name {!r} already in use'.format(var))
            else:
                conv = self._new_converter(conv, args)
                regex = conv.regex
                buf.append('(?P<{}>{})'.format(var, regex))
                self._segments.append((True, var))
                self._converters[var] = conv
                self._variables.add(var)
        if not self.is_leaf():
            self._segments.append((False, '/'))
        buf.append('(?P<__slash__>/?)')
        buf.append('$')

        self._regex = re.compile(''.join(buf))

    def _parse(self, path):
        pos = 0
        end = len(path)
        match = _rule_re.match
        while pos < end:
            m = match(path, pos)
            if m is None:
                break
            grp = m.groupdict()
            if grp['static']:
                yield None, None, grp['static']
            conv = grp['converter'] or 'default'
            args = grp['args'] or None
            yield conv, args, grp['variable']
            pos = m.end()
        if pos < end:
            yield None, None, path[pos:]

    def _new_converter(self, name, args):
        cls = self.map.converters.get(name)
        if not cls:
            raise RouteError('converter {!r} not found'.format(name))
        if args:
            args, kwargs = eval('(lambda *a, **kw: (a, kw))({})'.format(args),
                                {'__builtins__': None})
        else:
            args, kwargs = (), {}
        return cls(self.map, *args, **kwargs)

    def match(self, path):
        assert self.map is not None, 'rule not bound to map'
        m = self._regex.search(path)
        if not m:
            return
        grp = m.groupdict()
        slash = grp.pop('__slash__')
        if (self.map.slash and
            not self.is_leaf() and
            not slash):
            raise RequestSlash()

        values = {}
        for var in grp:
            try:
                values[var] = self._converters[var].to_python(grp[var])
            except ValidationError:
                return
        return values

    def build(self, values, anchor=None, method=None, append_query=True):
        assert self.map is not None, 'rule not bound to map'
        if (method is not None and
            method not in self.methods):
            return
        for var in self._variables:
            if var not in values:
                return

        buf = []
        cache = {}
        for dyn, var in self._segments:
            if dyn:
                cache[var] = util.to_list(values[var])
                if not cache[var]:
                    return
                data = cache[var].pop(0)
                try:
                    buf.append(self._converters[var].to_uri(data))
                except ValidationError:
                    return
            else:
                buf.append(var)

        if append_query:
            query = []
            for var in values:
                data = cache.get(var, util.to_list(values[var]))
                var = util.to_bytes(var, self.map.encoding)
                query.extend(((var, x) for x in data))
            if query:
                query = sorted(query, key=self.map.sort_key)
                buf.append('?')
                buf.append(urllib.urlencode(query, doseq=True))

        if anchor:
            buf.append('#')
            buf.append(uri.quote(anchor, encoding=self.map.encoding))

        return ''.join(buf)

class Map(object):

    def __init__(self, encoding='utf-8', slash=True, converters=None,
                 sort_key=None):
        self.encoding = encoding
        self.slash = slash
        self.converters = {
                'default': _StringConverter,
                'string': _StringConverter,
                'path': _PathConverter,
                'int': _IntegerConverter}
        if converters:
            self.converters.update(converters)
        self.sort_key = sort_key

        self._rules = []
        self._ref = defaultdict(list)

    def add(self, rule):
        rule.bind(self)
        self._rules.append(rule)
        self._ref[rule.object].append(rule)

    def connect(self, path, object, methods=None):
        self.add(Rule(path, object, methods))

    def redirect(self, path, dest, methods=None):
        self.add(Rule(path, dest, methods, True))

    def mount(self, path):
        return _Submap(self, path)

    def bind(self, environ):
        return Router(self, environ)

class _Submap(object):

    def __init__(self, map, path):
        self.map = map
        self.path = path

    def add(self, rule):
        self.map.add(Rule(self.path + rule.path, rule.object, rule.methods,
                          rule.has_redirect()))

    def connect(self, path, object, methods=None):
        self.map.add(Rule(self.path + path, object, methods))

    def redirect(self, path, dest, methods=None):
        self.map.add(Rule(self.path + path, dest, methods, True))

class Router(object):

    def __init__(self, map, environ):
        self.map = map
        self.environ = environ

    def match(self, as_rule=False):
        path = self.environ['PATH_INFO']
        method = self.environ['REQUEST_METHOD']
        allow = set()
        for rule in self.map._rules:
            try:
                values = rule.match(path)
            except RequestSlash:
                environ = self.environ.copy()
                environ['PATH_INFO'] += '/'
                raise http.MovedPermanently(uri.request_uri(environ, True))
            if values is None:
                continue
            elif method not in rule.methods:
                allow.update(rule.methods)
                continue
            elif rule.has_redirect():
                if isinstance(rule.object, basestring):
                    def repl(m):
                        var = m.group(1)
                        converter = rule._converters[var]
                        return converter.to_uri(values[var])
                    location = _simple_rule_re.sub(repl, rule.object)
                else:
                    location = rule.object(**values)
                environ = self.environ.copy()
                environ['PATH_INFO'] = location
                raise http.MovedPermanently(uri.request_uri(environ, True))
            return rule if as_rule else rule.object, values
        if allow:
            raise http.NotImplemented(method, uri.request_path(self.environ),
                                      sorted(allow))
        raise http.NotFound(uri.request_path(self.environ))

    def build(self, object, values=None, anchor=None, method=None,
              append_query=True):
        if not values:
            values = {}
        for rule in self.map._ref.get(object, ()):
            uri = rule.build(values, anchor, method, append_query)
            if uri is not None:
                return uri
        raise RouteError('no rule for building URI')

class Converter(object):

    regex = '[^/]+'

    def __init__(self, map):
        self.map = map

    def to_python(self, value):
        return value

    def to_uri(self, value):
        return uri.quote(value, encoding=self.map.encoding)

class _StringConverter(Converter):

    def __init__(self, map, length=None, min=None):
        super(_StringConverter, self).__init__(map)
        self.length = length
        self.min = min
        if min is not None:
            max = '' if length is None else int(length)
            count = '{},{}'.format(int(min), max)
        elif length is not None:
            count = int(length)
        else:
            count = '1,'
        self.regex = '[^/]{{{}}}'.format(count)

    def to_uri(self, value):
        value = super(_StringConverter, self).to_uri(value)
        if self.min:
            if (len(value) < self.min or
                (self.length and
                 len(value) > self.length)):
                raise ValidationError()
        elif (self.length and
              len(value) != self.length):
            raise ValidationError()
        return value

class _PathConverter(Converter):

    regex = '[^/].*?'

class _IntegerConverter(Converter):

    regex = '\d+'

    def __init__(self, map, digits=None, min=None, max=None):
        super(_IntegerConverter, self).__init__(map)
        self.digits = digits
        self.min = min
        self.max = max
        if digits is not None:
            self.regex = '\d{{{}}}'.format(int(digits))

    def to_python(self, value):
        value = int(value)
        if ((self.min is not None and
             value < self.min) or
            (self.max is not None and
             value > self.max)):
            raise ValidationError()
        return value

    def to_uri(self, value):
        try:
            value = self.to_python(value)
        except ValueError:
            raise ValidationError()
        if self.digits:
            value = '{:0{}d}'.format(value, self.digits)
            if len(value) > self.digits:
                raise ValidationError()
            return value
        return str(value)
