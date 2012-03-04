#
# ayame.util
#
#   Copyright (c) 2011-2012 Akinori Hattori <hattya@gmail.com>
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

import hashlib
import io
import os
import random
import sys
import types

from ayame.exception import ResourceError


__all__ = ['fqon_of', 'load_data', 'to_bytes', 'to_list' 'FilterDict']

def fqon_of(object):
    if not hasattr(object, '__name__'):
        object = object.__class__
    if hasattr(object, '__module__'):
        if object.__module__ is None:
            return '.'.join(('<unknown>', object.__name__))
        elif object.__module__ != '__builtin__':
            return '.'.join((object.__module__, object.__name__))
    return object.__name__

def load_data(object, suffix, encoding='utf-8'):
    if not hasattr(object, '__name__'):
        object = object.__class__
    if isinstance(object, types.ModuleType):
        module = object
        is_module = True
    else:
        try:
            module = sys.modules[object.__module__]
            is_module = False
        except (AttributeError, KeyError):
            raise ResourceError('could not find module of {!r}'.format(object))
    try:
        parent, name = os.path.split(module.__file__)
    except AttributeError:
        raise ResourceError("could not determine '{}' module location"
                            .format(module.__name__))
    name = os.path.splitext(name)[0]
    if name.lower() != '__init__':
        parent = os.path.join(parent, name)
    if is_module:
        path = parent + suffix
    else:
        path = os.path.join(parent, object.__name__ + suffix)
    loader = getattr(module, '__loader__', None)
    if loader:
        # load data from loader
        try:
            data = loader.get_data(path)
        except (AttributeError, IOError):
            raise ResourceError("could not load '{}' from loader {!r}"
                                .format(path, loader))
        return io.StringIO(data.decode(encoding))
    return io.open(path, encoding=encoding)

def to_bytes(s, encoding='utf-8', errors='strict'):
    if isinstance(s, bytes):
        return s
    elif not isinstance(s, basestring):
        s = str(s)
    return s.encode(encoding, errors)

def to_list(o):
    if o is None:
        return []
    elif hasattr(o, '__iter__'):
        return list(o)
    return [o]

def new_token(algorithm='sha1'):
    m = hashlib.new(algorithm)
    m.update(str(random.random()))
    return m.hexdigest()

class FilterDict(dict):

    def __init__(self, *args, **kwargs):
        super(FilterDict, self).__init__(*args, **kwargs)
        convert = self.__convert__
        pop = super(FilterDict, self).pop
        for key in self:
            new_key = convert(key)
            if new_key != key:
                self[new_key] = pop(key)

    def __convert__(self, key):
        return key

    def __getitem__(self, key):
        return super(FilterDict, self).__getitem__(self.__convert__(key))

    def __setitem__(self, key, value):
        return super(FilterDict, self).__setitem__(self.__convert__(key),
                                                   value)

    def __delitem__(self, key):
        super(FilterDict, self).__delitem__(self.__convert__(key))

    def __contains__(self, item):
        return super(FilterDict, self).__contains__(self.__convert__(item))

    def __copy__(self):
        return self.__class__(self)

    copy = __copy__

    def get(self, key, *args):
        return super(FilterDict, self).get(self.__convert__(key), *args)

    def has_key(self, key):
        return self.__contains__(key)

    def pop(self, key, *args):
        return super(FilterDict, self).pop(self.__convert__(key), *args)

    def setdefault(self, key, *args):
        return super(FilterDict, self).setdefault(self.__convert__(key), *args)

    def update(self, *args, **kwargs):
        prev_keys = tuple(self)
        super(FilterDict, self).update(*args, **kwargs)
        convert = self.__convert__
        pop = super(FilterDict, self).pop
        for key in self:
            if key not in prev_keys:
                new_key = convert(key)
                if new_key != key:
                    self[new_key] = pop(key)
