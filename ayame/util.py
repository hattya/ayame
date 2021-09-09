#
# ayame.util
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import collections.abc
import hashlib
import itertools
import random
import threading


__all__ = ['fqon_of', 'to_bytes', 'to_list', 'new_token', 'FilterDict',
           'RWLock', 'LRUCache', 'LFUCache']


def fqon_of(object):
    if not hasattr(object, '__name__'):
        object = object.__class__

    if hasattr(object, '__module__'):
        if object.__module__ is None:
            return '.'.join(('<unknown>', object.__name__))
        elif object.__module__ != 'builtins':
            return '.'.join((object.__module__, object.__name__))
    return object.__name__


def to_bytes(s, encoding='utf-8', errors='strict'):
    if isinstance(s, bytes):
        return s
    elif not isinstance(s, str):
        s = str(s)
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
    return (isinstance(o, collections.abc.Iterable)
            and not isinstance(o, str))


class FilterDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        convert = self.__convert__
        pop = super().pop
        for key in tuple(self):
            new_key = convert(key)
            if new_key != key:
                self[new_key] = pop(key)

    def __convert__(self, key):
        return key

    def __getitem__(self, key):
        return super().__getitem__(self.__convert__(key))

    def __setitem__(self, key, value):
        return super().__setitem__(self.__convert__(key), value)

    def __delitem__(self, key):
        super().__delitem__(self.__convert__(key))

    def __contains__(self, item):
        return super().__contains__(self.__convert__(item))

    def __copy__(self):
        return self.__class__(self)

    copy = __copy__

    def get(self, key, *args):
        return super().get(self.__convert__(key), *args)

    def pop(self, key, *args):
        return super().pop(self.__convert__(key), *args)

    def setdefault(self, key, *args):
        return super().setdefault(self.__convert__(key), *args)

    def update(self, *args, **kwargs):
        keys = tuple(self)
        super().update(*args, **kwargs)
        convert = self.__convert__
        pop = super().pop
        for key in tuple(self):
            if key not in keys:
                new_key = convert(key)
                if new_key != key:
                    self[new_key] = pop(key)


class RWLock:

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
            if rcnt > 0:
                # wait for readers
                self._w.wait()

    def release_write(self):
        with self._lock:
            if self._rcnt >= 0:
                raise RuntimeError('write lock is not acquired')
            self._rcnt += 1
            # wake up readers
            self._r.notify_all()
            # wake up writers
            self._w.notify_all()

    class _Lock:

        def __init__(self, acquire, release):
            self._acquire = acquire
            self._release = release

        def __enter__(self):
            self._acquire()
            return self

        def __exit__(self, *exc_info):
            self._release()


class _Cache:

    __slots__ = ('_cap', '_ref', '_head', '_lock')

    def __init__(self, cap=-1):
        self._cap = cap
        self.on_init()

    def cap():
        def fget(self):
            with self._lock.read():
                return self._cap

        def fset(self, cap):
            with self._lock.write():
                self._cap = cap
                self._sweep()

        return locals()

    cap = property(**cap())

    def __repr__(self):
        return f'{self.__class__.__name__}({list(self.items())})'

    def __len__(self):
        with self._lock.read():
            return len(self._ref)

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

    def items(self):
        with self._lock.read():
            for e in self._iter():
                yield (e.key, e.value)

    keys = __iter__

    def values(self):
        with self._lock.read():
            for e in self._iter():
                yield e.value

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
        self._lock = RWLock()

    def on_evicted(self, key, value):
        pass


class LRUCache(_Cache):

    __slots__ = ()

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

    def __copy__(self):
        with self._lock.read():
            c = self.__class__(self._cap)
            for e in self._iter(reverse=True):
                c[e.key] = e.value
            return c

    def __getstate__(self):
        with self._lock.read():
            return (self._cap, tuple((e.key, e.value) for e in self._iter()))

    def __setstate__(self, state):
        self._cap = state[0]
        self.on_init()
        for k, v in reversed(state[1]):
            self[k] = v

    copy = __copy__

    def clear(self):
        with self._lock.write():
            self._ref.clear()
            self._head = None

    def on_init(self):
        super().on_init()
        self._head = None

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
        if self._cap >= 0:
            it = self._iter(reverse=True)
            while len(self._ref) > self._cap:
                self._evict(next(it))

    def _evict(self, e):
        e.next.prev = e.prev
        e.prev.next = e.next
        del self._ref[e.key]
        if e is self._head:
            if (not self._ref
                or self._cap == 1):
                self._head = None
            else:
                self._head = e.next
        self.on_evicted(e.key, e.value)

    class _Entry:

        __slots__ = ('key', 'value', 'next', 'prev')

        def __init__(self, key, value):
            self.key = key
            self.value = value
            self.next = self.prev = None


collections.abc.MutableMapping.register(LRUCache)


class LFUCache(_Cache):
    """An implementation of LFU cache algorithm

    This is based upon K. Shah, A. Mitra and D. Matani,
    "An O(1) algorithm for implementation the LFU cache eviction scheme" August 2010
    """

    __slots__ = ()

    def __getitem__(self, key):
        with self._lock.write():
            e = self._ref[key]
            curr = e.parent
            # remove from current frequency node
            self._remove(e)
            # append to next frequency node
            next = curr.next
            if (next is self._head
                or next.value != curr.value + 1):
                next = self._new_freq(curr.value + 1, next)
            next.append(e)

            return e.value

    def __setitem__(self, key, value):
        with self._lock.write():
            if key in self._ref:
                self._evict(self._ref[key])
            self._sweep(self._cap - 1 if self._cap > 0 else self._cap)

            freq = self._head.next
            if freq.value != 1:
                freq = self._new_freq(1, freq)
            self._ref[key] = e = self._Entry(key, value)
            freq.append(e)

    def __copy__(self):
        with self._lock.read():
            c = self.__class__(self._cap)
            for fv, g in itertools.groupby(self._iter(), lambda e: e.parent.value):
                for e in reversed(tuple(g)):
                    c[e.key] = e.value
                c._head.next.value = fv
            return c

    def __getstate__(self):
        with self._lock.read():
            return (self._cap,
                    tuple((fv, tuple((e.key, e.value) for e in g))
                          for fv, g in itertools.groupby(self._iter(), lambda e: e.parent.value)))

    def __setstate__(self, state):
        self._cap = state[0]
        self.on_init()
        for fv, g in state[1]:
            for k, v in reversed(g):
                self[k] = v
            self._head.next.value = fv

    copy = __copy__

    def clear(self):
        with self._lock.write():
            self._ref.clear()
            self._head.next = self._head.prev = self._head

    def on_init(self):
        super().on_init()
        self._head = self._Frequency(0)

    def _iter(self, reverse=False):
        if self._head.next is self._head:
            # no entries
            return
        elif not reverse:
            # forward iterator
            freq = self._head.prev
            while freq is not self._head:
                e = freq.head.prev
                while True:
                    p = e.prev
                    yield e
                    if e is freq.head:
                        break
                    e = p
                freq = freq.prev
        else:
            # reverse iterator
            freq = self._head.next
            while freq is not self._head:
                e = freq.head
                while True:
                    n = e.next
                    yield e
                    if n is freq.head:
                        break
                    e = n
                freq = freq.next

    def _new_freq(self, v, next):
        freq = self._Frequency(v)
        freq.next = next
        freq.prev = next.prev
        next.prev.next = next.prev = freq
        return freq

    def _sweep(self, cap=None):
        if cap is None:
            cap = self._cap

        if cap >= 0:
            while len(self._ref) > cap:
                self._evict(self._lfu())

    def _evict(self, e):
        self._remove(e)
        del self._ref[e.key]
        self.on_evicted(e.key, e.value)

    def _remove(self, e):
        freq = e.parent
        freq.remove(e)
        if freq.len == 0:
            freq.next.prev = freq.prev
            freq.prev.next = freq.next

    def _lfu(self):
        if self._head.next is self._head:
            raise RuntimeError(f"'{self.__class__.__name__}' is empty")
        return self._ref[self._head.next.head.key]

    class _Frequency:

        __slots__ = ('value', 'head', 'len', 'next', 'prev')

        def __init__(self, value):
            self.value = value
            self.head = None
            self.len = 0
            self.next = self.prev = self

        def append(self, e):
            if self.head is None:
                self.head = e.next = e.prev = e
            else:
                n = self.head
                e.next = n
                e.prev = n.prev
                n.prev.next = n.prev = e
            e.parent = self
            self.len += 1

        def remove(self, e):
            if e.next is e:
                self.head = None
            else:
                e.next.prev = e.prev
                e.prev.next = e.next
                if self.head is e:
                    self.head = e.next
            e.parent = None
            self.len -= 1

    class _Entry:

        __slots__ = ('key', 'value', 'parent', 'next', 'prev')

        def __init__(self, key, value):
            self.key = key
            self.value = value
            self.parent = None
            self.next = self.prev = None


collections.abc.MutableMapping.register(LFUCache)
