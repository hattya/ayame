#
# test_util
#
#   Copyright (c) 2011-2015 Akinori Hattori <hattya@gmail.com>
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
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
import random
import threading
import time

from ayame import _compat as five
from ayame import util
from base import AyameTestCase


class UtilTestCase(AyameTestCase):

    def test_fqon_of_builtin(self):
        self.assert_equal(util.fqon_of(None), 'NoneType')
        self.assert_equal(util.fqon_of(True), 'bool')
        self.assert_equal(util.fqon_of(False), 'bool')
        self.assert_equal(util.fqon_of(''), 'str')
        self.assert_equal(util.fqon_of([]), 'list')
        self.assert_equal(util.fqon_of({}), 'dict')
        self.assert_equal(util.fqon_of(1), 'int')
        self.assert_equal(util.fqon_of(3.14), 'float')

    def test_fqon_of_class(self):
        class O:
            pass

        class N(object):
            pass

        self.assert_equal(util.fqon_of(O), __name__ + '.O')
        self.assert_equal(util.fqon_of(O()), __name__ + '.O')
        O.__module__ = None
        self.assert_equal(util.fqon_of(O), '<unknown>.O')
        self.assert_equal(util.fqon_of(O()), '<unknown>.O')
        if five.PY2:
            del O.__module__
            self.assert_equal(util.fqon_of(O), 'O')
            self.assert_equal(util.fqon_of(O()), 'O')

        self.assert_equal(util.fqon_of(N), __name__ + '.N')
        self.assert_equal(util.fqon_of(N()), __name__ + '.N')
        N.__module__ = None
        self.assert_equal(util.fqon_of(N), '<unknown>.N')
        self.assert_equal(util.fqon_of(N()), '<unknown>.N')

    def test_fqon_of_function(self):
        def f():
            pass

        self.assert_equal(util.fqon_of(f), __name__ + '.f')
        del f.__module__
        self.assert_equal(util.fqon_of(f), '<unknown>.f')

        f = lambda: None

        self.assert_equal(util.fqon_of(f), __name__ + '.<lambda>')
        del f.__module__
        self.assert_equal(util.fqon_of(f), '<unknown>.<lambda>')

    def test_fqon_of_module(self):
        self.assert_equal(util.fqon_of(os), 'os')
        self.assert_equal(util.fqon_of(util), 'ayame.util')

    def test_to_bytes(self):
        # iroha in hiragana
        v = util.to_bytes(u'\u3044\u308d\u306f')
        self.assert_is_instance(v, bytes)
        self.assert_equal(v, b'\xe3\x81\x84\xe3\x82\x8d\xe3\x81\xaf')

        v = util.to_bytes(u'\u3044\u308d\u306f', 'ascii', 'ignore')
        self.assert_is_instance(v, bytes)
        self.assert_equal(v, b'')

        with self.assert_raises(UnicodeEncodeError):
            util.to_bytes(u'\u3044\u308d\u306f', 'ascii')

        v = util.to_bytes(b'abc')
        self.assert_is_instance(v, bytes)
        self.assert_equal(v, b'abc')

        v = util.to_bytes(0)
        self.assert_is_instance(v, bytes)
        self.assert_equal(v, b'0')

        v = util.to_bytes(3.14)
        self.assert_is_instance(v, bytes)
        self.assert_equal(v, b'3.14')

    def test_to_list(self):
        self.assert_equal(util.to_list(None), [])
        self.assert_equal(util.to_list('abc'), ['abc'])
        self.assert_equal(util.to_list(''), [''])
        self.assert_equal(util.to_list(1), [1])
        self.assert_equal(util.to_list(3.14), [3.14])
        self.assert_equal(util.to_list((1,)), [1])
        self.assert_equal(util.to_list([1]), [1])
        self.assert_equal(util.to_list({'a': 1}), ['a'])

    def test_new_token(self):
        a = util.new_token()
        b = util.new_token()
        self.assert_not_equal(a, b)

    def test_iterable(self):
        self.assert_true(util.iterable(()))
        self.assert_true(util.iterable([]))
        self.assert_true(util.iterable({}))

        self.assert_false(util.iterable(''))

    def test_filter_dict(self):
        class LowerDict(util.FilterDict):
            def __convert__(self, key):
                if isinstance(key, five.string_type):
                    return key.lower()
                return super(LowerDict, self).__convert__(key)

        d = LowerDict(a=-1, A=0)
        self.assert_equal(d['A'], 0)
        self.assert_equal(d['a'], 0)
        self.assert_in('A', d)
        self.assert_in('a', d)
        self.assert_equal(d.get('A'), 0)
        self.assert_equal(d.get('a'), 0)
        d.setdefault('a', -1)
        self.assert_equal(d, {'a': 0})

        d['B'] = 1
        self.assert_equal(d['B'], 1)
        self.assert_equal(d['b'], 1)
        self.assert_in('B', d)
        self.assert_in('b', d)
        self.assert_equal(d.get('B'), 1)
        self.assert_equal(d.get('b'), 1)
        d.setdefault('b', -1)
        self.assert_equal(d, {'a': 0, 'b': 1})

        del d['b']
        self.assert_equal(d, {'a': 0})
        self.assert_equal(d.pop('a'), 0)
        self.assert_equal(d, {})

        d.update(A=0)
        self.assert_equal(d, {'a': 0})
        d.update(A=0, b=1)
        self.assert_equal(d, {'a': 0, 'b': 1})
        d[0] = 'a'
        self.assert_equal(d, {'a': 0, 'b': 1, 0: 'a'})

        x = d.copy()
        self.assert_is_instance(x, LowerDict)
        self.assert_equal(x, d)
        x[0] = 'b'
        self.assert_equal(d, {'a': 0, 'b': 1, 0: 'a'})
        self.assert_equal(x, {'a': 0, 'b': 1, 0: 'b'})


class RWLockTestCase(AyameTestCase):

    def test_rwlock(self):
        def reader():
            with lock.read():
                self.assert_greater(lock._rcnt, 0)
                self.assert_equal(lock._rwait, 0)
                time.sleep(0.01)

        def writer():
            with lock.write():
                self.assert_equal(lock._rcnt, -1)
                self.assert_equal(lock._rwait, 0)
                time.sleep(0.01)

        lock = util.RWLock()
        for _ in five.range(10):
            thr = threading.Thread(target=random.choice((reader, writer)))
            thr.daemon = True
            thr.start()
            time.sleep(0.01)
        time.sleep(0.17)
        self.assert_equal(lock._rcnt, 0)
        self.assert_equal(lock._rwait, 0)
        self.assert_equal(threading.active_count(), 1)

    def test_release(self):
        lock = util.RWLock()
        with self.assert_raises(RuntimeError):
            lock.release_read()
        with self.assert_raises(RuntimeError):
            lock.release_write()


class LRUCacheTestCase(AyameTestCase):

    def lru_cache(self, n):
        c = LRUCache(n)
        for i in five.range(n):
            c[chr(ord('a') + i)] = i + 1
        return c

    def test_lru_cache(self):
        c = LRUCache(3)
        self.assert_equal(c.cap, 3)
        self.assert_equal(len(c), 0)
        self.assert_is_instance(c, collections.MutableMapping)

    def test_repr(self):
        c = self.lru_cache(0)
        self.assert_equal(repr(c), 'LRUCache([])')
        c = self.lru_cache(3)
        self.assert_equal(repr(c), "LRUCache([('c', 3), ('b', 2), ('a', 1)])")

    def test_set(self):
        c = self.lru_cache(3)
        self.assert_equal(len(c), 3)
        self.assert_equal(list(c), ['c', 'b', 'a'])
        self.assert_equal(list(reversed(c)), ['a', 'b', 'c'])
        self.assert_in('a', c)
        self.assert_in('b', c)
        self.assert_in('c', c)
        self.assert_equal(list(c.keys()), ['c', 'b', 'a'])
        self.assert_equal(list(c.values()), [3, 2, 1])
        self.assert_equal(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assert_equal(c.evicted, [])

        c['c'] = 3.0
        c['b'] = 2.0
        c['a'] = 1.0
        self.assert_equal(list(reversed(c)), ['c', 'b', 'a'])
        self.assert_equal(list(c.items()), [('a', 1.0), ('b', 2.0), ('c', 3.0)])
        self.assert_equal(c.evicted, [])

        c['a'] = 1
        c['b'] = 2
        c['c'] = 3
        c['d'] = 4
        self.assert_equal(list(reversed(c)), ['b', 'c', 'd'])
        self.assert_equal(list(c.items()), [('d', 4), ('c', 3), ('b', 2)])
        self.assert_equal(c.evicted[0:], [('a', 1.0)])

        self.assert_equal(c.setdefault('c', 0), 3)
        self.assert_equal(c.setdefault('d', 0), 4)
        self.assert_equal(c.setdefault('e', 5), 5)
        self.assert_equal(list(reversed(c)), ['c', 'd', 'e'])
        self.assert_equal(list(c.items()), [('e', 5), ('d', 4), ('c', 3)])
        self.assert_equal(c.evicted[1:], [('b', 2)])

    def test_get(self):
        c = self.lru_cache(3)
        self.assert_equal(list(reversed(c)), ['a', 'b', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assert_equal(c.evicted, [])

        self.assert_equal(c['c'], 3)
        self.assert_equal(c['b'], 2)
        self.assert_equal(c['a'], 1)
        self.assert_equal(list(reversed(c)), ['c', 'b', 'a'])
        self.assert_equal(list(c.items()), [('a', 1), ('b', 2), ('c', 3)])
        self.assert_equal(c.evicted, [])

        self.assert_equal(c.peek('a'), 1)
        self.assert_equal(c.peek('b'), 2)
        self.assert_equal(c.peek('c'), 3)
        self.assert_equal(list(reversed(c)), ['c', 'b', 'a'])
        self.assert_equal(list(c.items()), [('a', 1), ('b', 2), ('c', 3)])
        self.assert_equal(c.evicted, [])

        self.assert_equal(c.get('a'), 1)
        self.assert_equal(c.get('b'), 2)
        self.assert_equal(c.get('c'), 3)
        self.assert_equal(c.get('z', 26), 26)
        self.assert_equal(list(reversed(c)), ['a', 'b', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assert_equal(c.evicted, [])

    def test_del(self):
        c = self.lru_cache(3)
        del c['a']
        self.assert_equal(list(reversed(c)), ['b', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('b', 2)])
        self.assert_equal(c.evicted, [('a', 1)])

        c = self.lru_cache(3)
        del c['b']
        self.assert_equal(list(reversed(c)), ['a', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('a', 1)])
        self.assert_equal(c.evicted, [('b', 2)])

        c = self.lru_cache(3)
        del c['c']
        self.assert_equal(list(reversed(c)), ['a', 'b'])
        self.assert_equal(list(c.items()), [('b', 2), ('a', 1)])
        self.assert_equal(c.evicted, [('c', 3)])

        c = self.lru_cache(3)
        self.assert_equal(c.pop('b'), 2)
        self.assert_equal(list(reversed(c)), ['a', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('a', 1)])
        self.assert_equal(c.evicted, [('b', 2)])

        with self.assert_raises(KeyError):
            c.pop('b')
        self.assert_is_none(c.pop('b', None))

        c = self.lru_cache(3)
        n = len(c)
        for i in five.range(1, n + 1):
            self.assert_equal(len(c.popitem()), 2)
            self.assert_equal(len(c), n - i)
            self.assert_equal(len(c.evicted), i)
        with self.assert_raises(KeyError):
            c.popitem()

    def test_resize(self):
        c = self.lru_cache(3)

        c.cap = 2
        self.assert_equal(list(reversed(c)), ['b', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('b', 2)])
        self.assert_equal(c.evicted[0:], [('a', 1)])

        c['d'] = 4
        self.assert_equal(list(reversed(c)), ['c', 'd'])
        self.assert_equal(list(c.items()), [('d', 4), ('c', 3)])
        self.assert_equal(c.evicted[1:], [('b', 2)])

        c.cap = 1
        self.assert_equal(list(reversed(c)), ['d'])
        self.assert_equal(list(c.items()), [('d', 4)])
        self.assert_equal(c.evicted[2:], [('c', 3)])

        c['e'] = 5
        self.assert_equal(list(reversed(c)), ['e'])
        self.assert_equal(list(c.items()), [('e', 5)])
        self.assert_equal(c.evicted[3:], [('d', 4)])

        c.cap = 0
        self.assert_equal(list(reversed(c)), [])
        self.assert_equal(list(c.items()), [])
        self.assert_equal(c.evicted[4:], [('e', 5)])

        c.cap = -1
        c['f'] = 6
        c['g'] = 7
        c['h'] = 8
        c['i'] = 9
        self.assert_equal(list(reversed(c)), ['f', 'g', 'h', 'i'])
        self.assert_equal(list(c.items()), [('i', 9), ('h', 8), ('g', 7), ('f', 6)])
        self.assert_equal(c.evicted[5:], [])

    def test_clear(self):
        c = self.lru_cache(3)
        c.clear()
        self.assert_equal(list(reversed(c)), [])
        self.assert_equal(list(c.items()), [])
        self.assert_equal(c.evicted, [])

    def test_update(self):
        c = self.lru_cache(3)
        with self.assert_raises(NotImplementedError):
            c.update()

    def test_copy(self):
        self._test_dup(lambda c: c.copy())

    def test_pickle(self):
        self._test_dup(lambda c: pickle.loads(pickle.dumps(c)))

    def _test_dup(self, dup):
        r = self.lru_cache(3)
        c = dup(r)
        self.assert_is_not(c, r)
        self.assert_equal(c.cap, 3)
        self.assert_equal(list(reversed(c)), ['a', 'b', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assert_equal(c.evicted, [])


class LRUCache(util.LRUCache):

    def on_init(self):
        super(LRUCache, self).on_init()
        self.evicted = []

    def on_evicted(self, k, v):
        super(LRUCache, self).on_evicted(k, v)
        self.evicted.append((k, v))


class LFUCacheTestCase(AyameTestCase):

    def lfu_cache(self, n):
        c = LFUCache(n)
        for i in five.range(n):
            c[chr(ord('a') + i)] = i + 1
        return c

    def test_lfu_cache(self):
        c = LFUCache(3)
        self.assert_equal(c.cap, 3)
        self.assert_equal(len(c), 0)
        self.assert_is_instance(c, collections.MutableMapping)
        with self.assert_raises(RuntimeError):
            c._lfu()

    def test_repr(self):
        c = self.lfu_cache(0)
        self.assert_equal(repr(c), 'LFUCache([])')
        c = self.lfu_cache(3)
        self.assert_equal(repr(c), "LFUCache([('c', 3), ('b', 2), ('a', 1)])")

    def test_set(self):
        c = self.lfu_cache(3)
        self.assert_equal(len(c), 3)
        self.assert_equal(list(c), ['c', 'b', 'a'])
        self.assert_equal(list(reversed(c)), ['a', 'b', 'c'])
        self.assert_in('a', c)
        self.assert_in('b', c)
        self.assert_in('c', c)
        self.assert_equal(list(c.keys()), ['c', 'b', 'a'])
        self.assert_equal(list(c.values()), [3, 2, 1])
        self.assert_equal(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assert_equal(c.evicted, [])

        c['c'] = 3.0
        c['b'] = 2.0
        c['a'] = 1.0
        self.assert_equal(list(reversed(c)), ['c', 'b', 'a'])
        self.assert_equal(list(c.items()), [('a', 1.0), ('b', 2.0), ('c', 3.0)])
        self.assert_equal(c.evicted[0:], [('c', 3), ('b', 2), ('a', 1)])

        c['a'] = 1
        c['b'] = 2
        c['c'] = 3
        c['d'] = 4
        self.assert_equal(list(reversed(c)), ['b', 'c', 'd'])
        self.assert_equal(list(c.items()), [('d', 4), ('c', 3), ('b', 2)])
        self.assert_equal(c.evicted[3:], [('a', 1.0), ('b', 2.0), ('c', 3.0), ('a', 1)])

        self.assert_equal(c.setdefault('d', 0), 4)
        self.assert_equal(c.setdefault('e', 5), 5)
        self.assert_equal(c.setdefault('c', 0), 3)
        self.assert_equal(list(reversed(c)), ['e', 'd', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('d', 4), ('e', 5)])
        self.assert_equal(c.evicted[7:], [('b', 2)])

    def test_get(self):
        c = self.lfu_cache(3)
        self.assert_equal(list(reversed(c)), ['a', 'b', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assert_equal(c.evicted, [])

        self.assert_equal(c['c'], 3)
        self.assert_equal(c['b'], 2)
        self.assert_equal(c['a'], 1)
        self.assert_equal(list(reversed(c)), ['c', 'b', 'a'])
        self.assert_equal(list(c.items()), [('a', 1), ('b', 2), ('c', 3)])
        self.assert_equal(c.evicted, [])

        self.assert_equal(c.peek('a'), 1)
        self.assert_equal(c.peek('b'), 2)
        self.assert_equal(c.peek('c'), 3)
        self.assert_equal(list(reversed(c)), ['c', 'b', 'a'])
        self.assert_equal(list(c.items()), [('a', 1), ('b', 2), ('c', 3)])
        self.assert_equal(c.evicted, [])

        self.assert_equal(c.get('a'), 1)
        self.assert_equal(c.get('b'), 2)
        self.assert_equal(c.get('c'), 3)
        self.assert_equal(c.get('z', 26), 26)
        self.assert_equal(list(reversed(c)), ['a', 'b', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assert_equal(c.evicted, [])

    def test_del(self):
        c = self.lfu_cache(3)
        del c['a']
        self.assert_equal(list(reversed(c)), ['b', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('b', 2)])
        self.assert_equal(c.evicted, [('a', 1)])

        c = self.lfu_cache(3)
        del c['b']
        self.assert_equal(list(reversed(c)), ['a', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('a', 1)])
        self.assert_equal(c.evicted, [('b', 2)])

        c = self.lfu_cache(3)
        del c['c']
        self.assert_equal(list(reversed(c)), ['a', 'b'])
        self.assert_equal(list(c.items()), [('b', 2), ('a', 1)])
        self.assert_equal(c.evicted, [('c', 3)])

        c = self.lfu_cache(3)
        self.assert_equal(c.pop('b'), 2)
        self.assert_equal(list(reversed(c)), ['a', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('a', 1)])
        self.assert_equal(c.evicted, [('b', 2)])

        with self.assert_raises(KeyError):
            c.pop('b')
        self.assert_is_none(c.pop('b', None))

        c = self.lfu_cache(3)
        n = len(c)
        for i in five.range(1, n + 1):
            self.assert_equal(len(c.popitem()), 2)
            self.assert_equal(len(c), n - i)
            self.assert_equal(len(c.evicted), i)
        with self.assert_raises(KeyError):
            c.popitem()

    def test_resize(self):
        c = self.lfu_cache(3)

        c.cap = 2
        self.assert_equal(list(reversed(c)), ['b', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('b', 2)])
        self.assert_equal(c.evicted[0:], [('a', 1)])
        c['d'] = 4
        self.assert_equal(list(reversed(c)), ['c', 'd'])
        self.assert_equal(list(c.items()), [('d', 4), ('c', 3)])
        self.assert_equal(c.evicted[1:], [('b', 2)])

        c.cap = 1
        self.assert_equal(list(reversed(c)), ['d'])
        self.assert_equal(list(c.items()), [('d', 4)])
        self.assert_equal(c.evicted[2:], [('c', 3)])
        c['e'] = 5
        self.assert_equal(list(reversed(c)), ['e'])
        self.assert_equal(list(c.items()), [('e', 5)])
        self.assert_equal(c.evicted[3:], [('d', 4)])

        c.cap = 0
        self.assert_equal(list(reversed(c)), [])
        self.assert_equal(list(c.items()), [])
        self.assert_equal(c.evicted[4:], [('e', 5)])

        c.cap = -1
        c['f'] = 6
        c['g'] = 7
        c['h'] = 8
        c['i'] = 9
        self.assert_equal(list(reversed(c)), ['f', 'g', 'h', 'i'])
        self.assert_equal(list(c.items()), [('i', 9), ('h', 8), ('g', 7), ('f', 6)])
        self.assert_equal(c.evicted[5:], [])

    def test_clear(self):
        c = self.lfu_cache(3)
        c.clear()
        self.assert_equal(list(reversed(c)), [])
        self.assert_equal(list(c.items()), [])
        self.assert_equal(c.evicted, [])

    def test_update(self):
        c = self.lfu_cache(3)
        with self.assert_raises(NotImplementedError):
            c.update()

    def test_copy(self):
        self._test_dup(lambda c: c.copy())

    def test_pickle(self):
        self._test_dup(lambda c: pickle.loads(pickle.dumps(c)))

    def _test_dup(self, dup):
        f = self.lfu_cache(3)
        c = dup(f)
        self.assert_is_not(c, f)
        self.assert_equal(c.cap, 3)
        self.assert_equal(list(reversed(c)), ['a', 'b', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assert_equal(c.evicted, [])
        freq = c._head.next
        self.assert_equal(freq.value, 1)
        self.assert_equal(freq.len, 3)
        self.assert_equal(c._head.prev.value, 1)

        f = self.lfu_cache(3)
        f['b']
        f['c']
        f['c']
        c = dup(f)
        self.assert_is_not(c, f)
        self.assert_equal(c.cap, 3)
        self.assert_equal(list(reversed(c)), ['a', 'b', 'c'])
        self.assert_equal(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assert_equal(c.evicted, [])
        freq = c._head.next
        self.assert_equal(freq.value, 1)
        self.assert_equal(freq.len, 1)
        self.assert_equal(freq.head.key, 'a')
        self.assert_equal(freq.head.value, 1)
        freq = c._head.next.next
        self.assert_equal(freq.value, 2)
        self.assert_equal(freq.len, 1)
        self.assert_equal(freq.head.key, 'b')
        self.assert_equal(freq.head.value, 2)
        freq = c._head.next.next.next
        self.assert_equal(freq.value, 3)
        self.assert_equal(freq.len, 1)
        self.assert_equal(freq.head.key, 'c')
        self.assert_equal(freq.head.value, 3)
        self.assert_equal(c._head.prev.value, 3)


class LFUCache(util.LFUCache):

    def on_init(self):
        super(LFUCache, self).on_init()
        self.evicted = []

    def on_evicted(self, k, v):
        super(LFUCache, self).on_evicted(k, v)
        self.evicted.append((k, v))
