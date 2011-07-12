#
# ayame.util
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

import io
import os
import sys
import types


__all__ = ['fqon_of', 'load_data', 'to_bytes', 'to_list', 'version']

def fqon_of(obj):
    if not hasattr(obj, '__name__'):
        obj = obj.__class__
    if hasattr(obj, '__module__'):
        if obj.__module__ is None:
            return '<unknown>.' + obj.__name__
        elif obj.__module__ != '__builtin__':
            return obj.__module__ + '.' + obj.__name__
    return obj.__name__

def load_data(obj, suffix, encoding='utf-8'):
    cls = _class_of(obj)
    try:
        module = sys.modules[cls.__module__]
        parent, name = os.path.split(module.__file__)
    except (AttributeError, KeyError):
        raise IOError("could not determine "
                      "'{}' module location".format(cls.__module__))
    name = os.path.splitext(name)[0]
    if name.lower() != '__init__':
        parent = os.path.join(parent, name)
    path = os.path.join(parent, cls.__name__ + suffix)
    loader = getattr(module, '__loader__', None)
    if loader:
        # load data from loader
        try:
            data = loader.get_data(path)
        except (AttributeError, IOError):
            raise IOError("could not load '{}' "
                          "from loader {!r}".format(path, loader))
        return io.StringIO(data.decode(encoding))
    return io.open(path, encoding=encoding)

def _class_of(obj):
    if (isinstance(obj, type) or
        isinstance(obj, types.ClassType)):
        return obj
    else:
        return obj.__class__

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

def version():
    try:
        from ayame import __version__

        return __version__.version
    except ImportError:
        return 'unknown'
