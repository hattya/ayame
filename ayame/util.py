#
# ayame.util
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
import hashlib
import io
import os
import pkgutil
import random
import sys
import threading
import types

from . import _compat as five
from .exception import ResourceError


__all__ = ['fqon_of', 'load_data', 'to_bytes', 'to_list', 'new_token',
           'FilterDict', 'RWLock', 'LRUCache']

if five.PY2:
    _builtins = '__builtin__'
else:
    _builtins = 'builtins'


def fqon_of(object):
    if not hasattr(object, '__name__'):
        object = object.__class__

    if hasattr(object, '__module__'):
        if object.__module__ is None:
            return '.'.join(('<unknown>', object.__name__))
        elif object.__module__ != _builtins:
            return '.'.join((object.__module__, object.__name__))
    return object.__name__


def load_data(object, path, encoding='utf-8'):
    if isinstance(object, types.ModuleType):
        module = object
        is_module = True
    else:
        if not hasattr(object, '__name__'):
            object = object.__class__
        try:
            module = sys.modules[object.__module__]
            is_module = False
        except (AttributeError, KeyError):
            raise ResourceError('cannot find module of {!r}'.format(object))
    try:
        parent, name = os.path.split(module.__file__)
        name = os.path.splitext(name)[0]
    except AttributeError:
        raise ResourceError("cannot determine '{}' module location".format(module.__name__))

    new_path = os.path.normpath(path)
    if (os.path.isabs(new_path) or
        new_path.split(os.path.sep, 1)[0] == os.path.pardir):
        raise ResourceError("invalid path '{}'".format(path))
    path = new_path
    if (not is_module and
        path.startswith('.')):
        path = object.__name__ + path
    if name.lower() != '__init__':
        path = os.path.join(name, path)

    try:
        data = pkgutil.get_data(module.__name__, path)
        if data is not None:
            return io.StringIO(five.str(data, encoding))
    except (OSError, IOError):
        raise ResourceError("cannot load '{}' from loader".format(path))
    path = os.path.join(parent, path)
    try:
        return io.open(path, encoding=encoding)
    except (OSError, IOError):
        raise ResourceError("cannot load '{}'".format(path))


def to_bytes(s, encoding='utf-8', errors='strict'):
    if isinstance(s, bytes):
        return s
    elif not isinstance(s, five.string_type):
        s = five.str(s)
    return s.encode(encoding, errors)


def to_list(o):
    if o is None:
        return []
    elif iterable(o):
        return list(o)
    return [o]


def new_token(algorithm='sha1'):
    m = hashlib.new(algorithm)
    m.update(to_bytes(random.random()))
    return m.hexdigest()


def iterable(o):
    return (isinstance(o, collections.Iterable) and
            not isinstance(o, five.string_type))


class FilterDict(dict):

    def __init__(self, *args, **kwargs):
        super(FilterDict, self).__init__(*args, **kwargs)
        convert = self.__convert__
        pop = super(FilterDict, self).pop
        for key in tuple(self):
            new_key = convert(key)
            if new_key != key:
                self[new_key] = pop(key)

    def __convert__(self, key):
        return key

    def __getitem__(self, key):
        return super(FilterDict, self).__getitem__(self.__convert__(key))

    def __setitem__(self, key, value):
        return super(FilterDict, self).__setitem__(self.__convert__(key), value)

    def __delitem__(self, key):
        super(FilterDict, self).__delitem__(self.__convert__(key))

    def __contains__(self, item):
        return super(FilterDict, self).__contains__(self.__convert__(item))

    def __copy__(self):
        return self.__class__(self)

    copy = __copy__

    def get(self, key, *args):
        return super(FilterDict, self).get(self.__convert__(key), *args)

    def pop(self, key, *args):
        return super(FilterDict, self).pop(self.__convert__(key), *args)

    def setdefault(self, key, *args):
        return super(FilterDict, self).setdefault(self.__convert__(key), *args)

    def update(self, *args, **kwargs):
        keys = tuple(self)
        super(FilterDict, self).update(*args, **kwargs)
        convert = self.__convert__
        pop = super(FilterDict, self).pop
        for key in tuple(self):
            if key not in keys:
                new_key = convert(key)
                if new_key != key:
                    self[new_key] = pop(key)


class RWLock(object):

    def __init__(self):
        self._rcnt = 0
        self._rwait = 0
        self._lock = threading.Lock()
        self._r = threading.Condition(self._lock)
        self._w = threading.Condition(self._lock)

    def read(self):
        return self._Lock(self.acquire_read, self.release_read)

    def write(self):
        return self._Lock(self.acquire_write, self.release_write)

    def acquire_read(self):
        with self._lock:
            while self._rcnt < 0:
                # wait for writer
                self._r.wait()
            self._rcnt += 1

    def release_read(self):
        with self._lock:
            if self._rcnt == 0:
                raise RuntimeError('read lock is not acquired')
            if self._rcnt < 0:
                # writer is waiting
                self._rcnt += 1
                self._rwait -= 1
                if self._rwait == 0:
                    # wake up writers
                    self._w.notify_all()
            else:
                self._rcnt -= 1

    def acquire_write(self):
        with self._lock:
            while self._rcnt < 0:
                # wait for writer
                self._w.wait()
            rcnt = self._rcnt
            self._rcnt = -rcnt - 1
            self._rwait = rcnt
            if 0 < rcnt:
                # wait for readers
                self._w.wait()

    def release_write(self):
        with self._lock:
            if 0 <= self._rcnt:
                raise RuntimeError('write lock is not acquired')
            self._rcnt += 1
            # wake up readers
            self._r.notify_all()
            # wake up writers
            self._w.notify_all()

    class _Lock(object):

        def __init__(self, acquire, release):
            self._acquire = acquire
            self._release = release

        def __enter__(self):
            self._acquire()
            return self

        def __exit__(self, *exc_info):
            self._release()


class LRUCache(object):

    __slots__ = ('__cap', '_ref', '_head', '_lock')

    def __init__(self, cap=-1):
        self.__cap = cap
        self.on_init()

    def cap():
        def fget(self):
            with self._lock.read():
                return self.__cap

        def fset(self, cap):
            with self._lock.write():
                self.__cap = cap
                self._sweep()

        return locals()

    cap = property(**cap())

    def __repr__(self):
        return u'{}({})'.format(self.__class__.__name__, list(self.items()))

    def __len__(self):
        with self._lock.read():
            return len(self._ref)

    def __getitem__(self, key):
        with self._lock.write():
            return self._move_to_front(self._ref[key]).value

    def __setitem__(self, key, value):
        with self._lock.write():
            if key in self._ref:
                e = self._ref[key]
                e.value = value
            else:
                self._ref[key] = e = self._Entry(key, value)
                self._sweep()

            if self._head is None:
                self._head = e.next = e.prev = e
            else:
                self._move_to_front(e)

    def __delitem__(self, key):
        with self._lock.write():
            self._evict(self._ref[key])

    def __iter__(self):
        with self._lock.read():
            for e in self._iter():
                yield e.key

    def __reversed__(self):
        with self._lock.read():
            for e in self._iter(reverse=True):
                yield e.key

    def __contains__(self, key):
        with self._lock.read():
            return key in self._ref

    def __copy__(self):
        with self._lock.read():
            c = self.__class__(self.__cap)
            for e in self._iter(reverse=True):
                c[e.key] = e.value
            return c

    def __getstate__(self):
        with self._lock.read():
            return (self.__cap, tuple((e.key, e.value) for e in self._iter()))

    def __setstate__(self, state):
        self.__cap = state[0]
        self.on_init()
        for k, v in reversed(state[1]):
            self[k] = v

    def items(self):
        with self._lock.read():
            for e in self._iter():
                yield (e.key, e.value)

    keys = __iter__

    def values(self):
        with self._lock.read():
            for e in self._iter():
                yield e.value

    copy = __copy__

    def clear(self):
        with self._lock.write():
            self._ref.clear()
            self._head = None

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def peek(self, key):
        with self._lock.read():
            return self._ref[key].value

    def setdefault(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    def update(self, *args, **kwargs):
        raise NotImplementedError

    def pop(self, key, *args):
        with self._lock.write():
            e = self._ref.pop(key, *args)
            if e in args:
                return e
            # reset for evict
            self._ref[key] = e
            self._evict(e)
            return e.value

    def popitem(self):
        with self._lock.write():
            k, e = self._ref.popitem()
            # reset for evict
            self._ref[k] = e
            self._evict(e)
            return (e.key, e.value)

    def on_init(self):
        self._ref = {}
        self._head = None
        self._lock = RWLock()

    def on_evicted(self, key, value):
        pass

    def _iter(self, reverse=False):
        if self._head is None:
            # no entries
            return
        elif not reverse:
            # forward iterator
            e = self._head
            while True:
                n = e.next
                yield e
                if n is self._head:
                    break
                e = n
        else:
            # reverse iterator
            e = self._head.prev
            while True:
                p = e.prev
                yield e
                if e is self._head:
                    break
                e = p

    def _move_to_front(self, e):
        if e is self._head:
            # already at front
            return e
        # remove from current position
        if e.next is not None:
            e.next.prev = e.prev
            e.prev.next = e.next
        # insert at front
        n = self._head
        e.next = n
        e.prev = n.prev
        self._head = n.prev.next = n.prev = e
        return e

    def _sweep(self):
        if 0 <= self.__cap:
            it = self._iter(reverse=True)
            while self.__cap < len(self._ref):
                self._evict(next(it))

    def _evict(self, e):
        e.next.prev = e.prev
        e.prev.next = e.next
        del self._ref[e.key]
        if e is self._head:
            if (not self._ref or
                self.__cap < 2):
                self._head = None
            else:
                self._head = e.next
        self.on_evicted(e.key, e.value)

    class _Entry(object):

        __slots__ = ('key', 'value', 'next', 'prev')

        def __init__(self, key, value):
            self.key = key
            self.value = value
            self.next = self.prev = None


collections.MutableMapping.register(LRUCache)
