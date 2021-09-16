#
# test_util
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import collections.abc
import os
import pickle
import random
import threading
import time

from ayame import util
from base import AyameTestCase


class UtilTestCase(AyameTestCase):

    def test_fqon_of_builtin(self):
        self.assertEqual(util.fqon_of(None), 'NoneType')
        self.assertEqual(util.fqon_of(True), 'bool')
        self.assertEqual(util.fqon_of(False), 'bool')
        self.assertEqual(util.fqon_of(''), 'str')
        self.assertEqual(util.fqon_of([]), 'list')
        self.assertEqual(util.fqon_of({}), 'dict')
        self.assertEqual(util.fqon_of(1), 'int')
        self.assertEqual(util.fqon_of(3.14), 'float')

    def test_fqon_of_class(self):
        class C:
            pass

        self.assertEqual(util.fqon_of(C), __name__ + '.C')
        self.assertEqual(util.fqon_of(C()), __name__ + '.C')
        C.__module__ = None
        self.assertEqual(util.fqon_of(C), '<unknown>.C')
        self.assertEqual(util.fqon_of(C()), '<unknown>.C')

    def test_fqon_of_function(self):
        def f():
            pass

        self.assertEqual(util.fqon_of(f), __name__ + '.f')
        del f.__module__
        self.assertEqual(util.fqon_of(f), '<unknown>.f')

        f = lambda: None

        self.assertEqual(util.fqon_of(f), __name__ + '.<lambda>')
        del f.__module__
        self.assertEqual(util.fqon_of(f), '<unknown>.<lambda>')

    def test_fqon_of_module(self):
        self.assertEqual(util.fqon_of(os), 'os')
        self.assertEqual(util.fqon_of(util), 'ayame.util')

    def test_to_bytes(self):
        # iroha in hiragana
        v = util.to_bytes('\u3044\u308d\u306f')
        self.assertIsInstance(v, bytes)
        self.assertEqual(v, b'\xe3\x81\x84\xe3\x82\x8d\xe3\x81\xaf')

        v = util.to_bytes('\u3044\u308d\u306f', 'ascii', 'ignore')
        self.assertIsInstance(v, bytes)
        self.assertEqual(v, b'')

        with self.assertRaises(UnicodeEncodeError):
            util.to_bytes('\u3044\u308d\u306f', 'ascii')

        v = util.to_bytes(b'abc')
        self.assertIsInstance(v, bytes)
        self.assertEqual(v, b'abc')

        v = util.to_bytes(0)
        self.assertIsInstance(v, bytes)
        self.assertEqual(v, b'0')

        v = util.to_bytes(3.14)
        self.assertIsInstance(v, bytes)
        self.assertEqual(v, b'3.14')

    def test_to_list(self):
        self.assertEqual(util.to_list(None), [])
        self.assertEqual(util.to_list('abc'), ['abc'])
        self.assertEqual(util.to_list(''), [''])
        self.assertEqual(util.to_list(1), [1])
        self.assertEqual(util.to_list(3.14), [3.14])
        self.assertEqual(util.to_list((1,)), [1])
        self.assertEqual(util.to_list([1]), [1])
        self.assertEqual(util.to_list({'a': 1}), ['a'])

    def test_new_token(self):
        a = util.new_token()
        b = util.new_token()
        self.assertNotEqual(a, b)

    def test_iterable(self):
        self.assertTrue(util.iterable(()))
        self.assertTrue(util.iterable([]))
        self.assertTrue(util.iterable({}))

        self.assertFalse(util.iterable(''))

    def test_filter_dict(self):
        class LowerDict(util.FilterDict):
            def __convert__(self, key):
                if isinstance(key, str):
                    return key.lower()
                return super().__convert__(key)

        d = LowerDict(a=-1, A=0)
        self.assertEqual(d['A'], 0)
        self.assertEqual(d['a'], 0)
        self.assertIn('A', d)
        self.assertIn('a', d)
        self.assertEqual(d.get('A'), 0)
        self.assertEqual(d.get('a'), 0)
        d.setdefault('a', -1)
        self.assertEqual(d, {'a': 0})

        d['B'] = 1
        self.assertEqual(d['B'], 1)
        self.assertEqual(d['b'], 1)
        self.assertIn('B', d)
        self.assertIn('b', d)
        self.assertEqual(d.get('B'), 1)
        self.assertEqual(d.get('b'), 1)
        d.setdefault('b', -1)
        self.assertEqual(d, {'a': 0, 'b': 1})

        del d['b']
        self.assertEqual(d, {'a': 0})
        self.assertEqual(d.pop('a'), 0)
        self.assertEqual(d, {})

        d.update(A=0)
        self.assertEqual(d, {'a': 0})
        d.update(A=0, b=1)
        self.assertEqual(d, {'a': 0, 'b': 1})
        d[0] = 'a'
        self.assertEqual(d, {'a': 0, 'b': 1, 0: 'a'})

        x = d.copy()
        self.assertIsInstance(x, LowerDict)
        self.assertEqual(x, d)
        x[0] = 'b'
        self.assertEqual(d, {'a': 0, 'b': 1, 0: 'a'})
        self.assertEqual(x, {'a': 0, 'b': 1, 0: 'b'})


class RWLockTestCase(AyameTestCase):

    def test_rwlock(self):
        def reader():
            with lock.read():
                self.assertGreater(lock._rcnt, 0)
                self.assertEqual(lock._rwait, 0)
                time.sleep(0.01)

        def writer():
            with lock.write():
                self.assertEqual(lock._rcnt, -1)
                self.assertEqual(lock._rwait, 0)
                time.sleep(0.01)

        lock = util.RWLock()
        for _ in range(10):
            thr = threading.Thread(target=random.choice((reader, writer)))
            thr.daemon = True
            thr.start()
            time.sleep(0.01)
        time.sleep(0.17)
        self.assertEqual(lock._rcnt, 0)
        self.assertEqual(lock._rwait, 0)
        self.assertEqual(threading.active_count(), 1)

    def test_release(self):
        lock = util.RWLock()
        with self.assertRaises(RuntimeError):
            lock.release_read()
        with self.assertRaises(RuntimeError):
            lock.release_write()


class LRUCacheTestCase(AyameTestCase):

    def lru_cache(self, n):
        c = LRUCache(n)
        for i in range(n):
            c[chr(ord('a') + i)] = i + 1
        return c

    def test_lru_cache(self):
        c = LRUCache(3)
        self.assertEqual(c.cap, 3)
        self.assertEqual(len(c), 0)
        self.assertIsInstance(c, collections.abc.MutableMapping)

    def test_repr(self):
        c = self.lru_cache(0)
        self.assertEqual(repr(c), 'LRUCache([])')
        c = self.lru_cache(3)
        self.assertEqual(repr(c), "LRUCache([('c', 3), ('b', 2), ('a', 1)])")

    def test_set(self):
        c = self.lru_cache(3)
        self.assertEqual(len(c), 3)
        self.assertEqual(list(c), ['c', 'b', 'a'])
        self.assertEqual(list(reversed(c)), ['a', 'b', 'c'])
        self.assertIn('a', c)
        self.assertIn('b', c)
        self.assertIn('c', c)
        self.assertEqual(list(c.keys()), ['c', 'b', 'a'])
        self.assertEqual(list(c.values()), [3, 2, 1])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assertEqual(c.evicted, [])

        c['c'] = 3.0
        c['b'] = 2.0
        c['a'] = 1.0
        self.assertEqual(list(reversed(c)), ['c', 'b', 'a'])
        self.assertEqual(list(c.items()), [('a', 1.0), ('b', 2.0), ('c', 3.0)])
        self.assertEqual(c.evicted, [])

        c['a'] = 1
        c['b'] = 2
        c['c'] = 3
        c['d'] = 4
        self.assertEqual(list(reversed(c)), ['b', 'c', 'd'])
        self.assertEqual(list(c.items()), [('d', 4), ('c', 3), ('b', 2)])
        self.assertEqual(c.evicted[0:], [('a', 1.0)])

        self.assertEqual(c.setdefault('c', 0), 3)
        self.assertEqual(c.setdefault('d', 0), 4)
        self.assertEqual(c.setdefault('e', 5), 5)
        self.assertEqual(list(reversed(c)), ['c', 'd', 'e'])
        self.assertEqual(list(c.items()), [('e', 5), ('d', 4), ('c', 3)])
        self.assertEqual(c.evicted[1:], [('b', 2)])

    def test_get(self):
        c = self.lru_cache(3)
        self.assertEqual(list(reversed(c)), ['a', 'b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assertEqual(c.evicted, [])

        self.assertEqual(c['c'], 3)
        self.assertEqual(c['b'], 2)
        self.assertEqual(c['a'], 1)
        self.assertEqual(list(reversed(c)), ['c', 'b', 'a'])
        self.assertEqual(list(c.items()), [('a', 1), ('b', 2), ('c', 3)])
        self.assertEqual(c.evicted, [])

        self.assertEqual(c.peek('a'), 1)
        self.assertEqual(c.peek('b'), 2)
        self.assertEqual(c.peek('c'), 3)
        self.assertEqual(list(reversed(c)), ['c', 'b', 'a'])
        self.assertEqual(list(c.items()), [('a', 1), ('b', 2), ('c', 3)])
        self.assertEqual(c.evicted, [])

        self.assertEqual(c.get('a'), 1)
        self.assertEqual(c.get('b'), 2)
        self.assertEqual(c.get('c'), 3)
        self.assertEqual(c.get('z', 26), 26)
        self.assertEqual(list(reversed(c)), ['a', 'b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assertEqual(c.evicted, [])

    def test_del(self):
        c = self.lru_cache(3)
        del c['a']
        self.assertEqual(list(reversed(c)), ['b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2)])
        self.assertEqual(c.evicted, [('a', 1)])

        c = self.lru_cache(3)
        del c['b']
        self.assertEqual(list(reversed(c)), ['a', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('a', 1)])
        self.assertEqual(c.evicted, [('b', 2)])

        c = self.lru_cache(3)
        del c['c']
        self.assertEqual(list(reversed(c)), ['a', 'b'])
        self.assertEqual(list(c.items()), [('b', 2), ('a', 1)])
        self.assertEqual(c.evicted, [('c', 3)])

        c = self.lru_cache(3)
        self.assertEqual(c.pop('b'), 2)
        self.assertEqual(list(reversed(c)), ['a', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('a', 1)])
        self.assertEqual(c.evicted, [('b', 2)])

        with self.assertRaises(KeyError):
            c.pop('b')
        self.assertIsNone(c.pop('b', None))

        c = self.lru_cache(3)
        n = len(c)
        for i in range(1, n + 1):
            self.assertEqual(len(c.popitem()), 2)
            self.assertEqual(len(c), n - i)
            self.assertEqual(len(c.evicted), i)
        with self.assertRaises(KeyError):
            c.popitem()

    def test_resize(self):
        c = self.lru_cache(3)

        c.cap = 2
        self.assertEqual(list(reversed(c)), ['b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2)])
        self.assertEqual(c.evicted[0:], [('a', 1)])

        c['d'] = 4
        self.assertEqual(list(reversed(c)), ['c', 'd'])
        self.assertEqual(list(c.items()), [('d', 4), ('c', 3)])
        self.assertEqual(c.evicted[1:], [('b', 2)])

        c.cap = 1
        self.assertEqual(list(reversed(c)), ['d'])
        self.assertEqual(list(c.items()), [('d', 4)])
        self.assertEqual(c.evicted[2:], [('c', 3)])

        c['e'] = 5
        self.assertEqual(list(reversed(c)), ['e'])
        self.assertEqual(list(c.items()), [('e', 5)])
        self.assertEqual(c.evicted[3:], [('d', 4)])

        c.cap = 0
        self.assertEqual(list(reversed(c)), [])
        self.assertEqual(list(c.items()), [])
        self.assertEqual(c.evicted[4:], [('e', 5)])

        c.cap = -1
        c['f'] = 6
        c['g'] = 7
        c['h'] = 8
        c['i'] = 9
        self.assertEqual(list(reversed(c)), ['f', 'g', 'h', 'i'])
        self.assertEqual(list(c.items()), [('i', 9), ('h', 8), ('g', 7), ('f', 6)])
        self.assertEqual(c.evicted[5:], [])

    def test_clear(self):
        c = self.lru_cache(3)
        c.clear()
        self.assertEqual(list(reversed(c)), [])
        self.assertEqual(list(c.items()), [])
        self.assertEqual(c.evicted, [])

    def test_update(self):
        c = self.lru_cache(3)
        with self.assertRaises(NotImplementedError):
            c.update()

    def test_copy(self):
        self._test_dup(lambda c: c.copy())

    def test_pickle(self):
        self._test_dup(lambda c: pickle.loads(pickle.dumps(c)))

    def _test_dup(self, dup):
        r = self.lru_cache(3)
        c = dup(r)
        self.assertIsNot(c, r)
        self.assertEqual(c.cap, 3)
        self.assertEqual(list(reversed(c)), ['a', 'b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assertEqual(c.evicted, [])


class LRUCache(util.LRUCache):

    def on_init(self):
        super().on_init()
        self.evicted = []

    def on_evicted(self, k, v):
        super().on_evicted(k, v)
        self.evicted.append((k, v))


class LFUCacheTestCase(AyameTestCase):

    def lfu_cache(self, n):
        c = LFUCache(n)
        for i in range(n):
            c[chr(ord('a') + i)] = i + 1
        return c

    def test_lfu_cache(self):
        c = LFUCache(3)
        self.assertEqual(c.cap, 3)
        self.assertEqual(len(c), 0)
        self.assertIsInstance(c, collections.abc.MutableMapping)
        with self.assertRaises(RuntimeError):
            c._lfu()

    def test_repr(self):
        c = self.lfu_cache(0)
        self.assertEqual(repr(c), 'LFUCache([])')
        c = self.lfu_cache(3)
        self.assertEqual(repr(c), "LFUCache([('c', 3), ('b', 2), ('a', 1)])")

    def test_set(self):
        c = self.lfu_cache(3)
        self.assertEqual(len(c), 3)
        self.assertEqual(list(c), ['c', 'b', 'a'])
        self.assertEqual(list(reversed(c)), ['a', 'b', 'c'])
        self.assertIn('a', c)
        self.assertIn('b', c)
        self.assertIn('c', c)
        self.assertEqual(list(c.keys()), ['c', 'b', 'a'])
        self.assertEqual(list(c.values()), [3, 2, 1])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assertEqual(c.evicted, [])

        c['c'] = 3.0
        c['b'] = 2.0
        c['a'] = 1.0
        self.assertEqual(list(reversed(c)), ['c', 'b', 'a'])
        self.assertEqual(list(c.items()), [('a', 1.0), ('b', 2.0), ('c', 3.0)])
        self.assertEqual(c.evicted[0:], [('c', 3), ('b', 2), ('a', 1)])

        c['a'] = 1
        c['b'] = 2
        c['c'] = 3
        c['d'] = 4
        self.assertEqual(list(reversed(c)), ['b', 'c', 'd'])
        self.assertEqual(list(c.items()), [('d', 4), ('c', 3), ('b', 2)])
        self.assertEqual(c.evicted[3:], [('a', 1.0), ('b', 2.0), ('c', 3.0), ('a', 1)])

        self.assertEqual(c.setdefault('d', 0), 4)
        self.assertEqual(c.setdefault('e', 5), 5)
        self.assertEqual(c.setdefault('c', 0), 3)
        self.assertEqual(list(reversed(c)), ['e', 'd', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('d', 4), ('e', 5)])
        self.assertEqual(c.evicted[7:], [('b', 2)])

    def test_get(self):
        c = self.lfu_cache(3)
        self.assertEqual(list(reversed(c)), ['a', 'b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assertEqual(c.evicted, [])

        self.assertEqual(c['c'], 3)
        self.assertEqual(c['b'], 2)
        self.assertEqual(c['a'], 1)
        self.assertEqual(list(reversed(c)), ['c', 'b', 'a'])
        self.assertEqual(list(c.items()), [('a', 1), ('b', 2), ('c', 3)])
        self.assertEqual(c.evicted, [])

        self.assertEqual(c.peek('a'), 1)
        self.assertEqual(c.peek('b'), 2)
        self.assertEqual(c.peek('c'), 3)
        self.assertEqual(list(reversed(c)), ['c', 'b', 'a'])
        self.assertEqual(list(c.items()), [('a', 1), ('b', 2), ('c', 3)])
        self.assertEqual(c.evicted, [])

        self.assertEqual(c.get('a'), 1)
        self.assertEqual(c.get('b'), 2)
        self.assertEqual(c.get('c'), 3)
        self.assertEqual(c.get('z', 26), 26)
        self.assertEqual(list(reversed(c)), ['a', 'b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assertEqual(c.evicted, [])

    def test_del(self):
        c = self.lfu_cache(3)
        del c['a']
        self.assertEqual(list(reversed(c)), ['b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2)])
        self.assertEqual(c.evicted, [('a', 1)])

        c = self.lfu_cache(3)
        del c['b']
        self.assertEqual(list(reversed(c)), ['a', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('a', 1)])
        self.assertEqual(c.evicted, [('b', 2)])

        c = self.lfu_cache(3)
        del c['c']
        self.assertEqual(list(reversed(c)), ['a', 'b'])
        self.assertEqual(list(c.items()), [('b', 2), ('a', 1)])
        self.assertEqual(c.evicted, [('c', 3)])

        c = self.lfu_cache(3)
        self.assertEqual(c.pop('b'), 2)
        self.assertEqual(list(reversed(c)), ['a', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('a', 1)])
        self.assertEqual(c.evicted, [('b', 2)])

        with self.assertRaises(KeyError):
            c.pop('b')
        self.assertIsNone(c.pop('b', None))

        c = self.lfu_cache(3)
        n = len(c)
        for i in range(1, n + 1):
            self.assertEqual(len(c.popitem()), 2)
            self.assertEqual(len(c), n - i)
            self.assertEqual(len(c.evicted), i)
        with self.assertRaises(KeyError):
            c.popitem()

    def test_resize(self):
        c = self.lfu_cache(3)

        c.cap = 2
        self.assertEqual(list(reversed(c)), ['b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2)])
        self.assertEqual(c.evicted[0:], [('a', 1)])
        c['d'] = 4
        self.assertEqual(list(reversed(c)), ['c', 'd'])
        self.assertEqual(list(c.items()), [('d', 4), ('c', 3)])
        self.assertEqual(c.evicted[1:], [('b', 2)])

        c.cap = 1
        self.assertEqual(list(reversed(c)), ['d'])
        self.assertEqual(list(c.items()), [('d', 4)])
        self.assertEqual(c.evicted[2:], [('c', 3)])
        c['e'] = 5
        self.assertEqual(list(reversed(c)), ['e'])
        self.assertEqual(list(c.items()), [('e', 5)])
        self.assertEqual(c.evicted[3:], [('d', 4)])

        c.cap = 0
        self.assertEqual(list(reversed(c)), [])
        self.assertEqual(list(c.items()), [])
        self.assertEqual(c.evicted[4:], [('e', 5)])

        c.cap = -1
        c['f'] = 6
        c['g'] = 7
        c['h'] = 8
        c['i'] = 9
        self.assertEqual(list(reversed(c)), ['f', 'g', 'h', 'i'])
        self.assertEqual(list(c.items()), [('i', 9), ('h', 8), ('g', 7), ('f', 6)])
        self.assertEqual(c.evicted[5:], [])

    def test_clear(self):
        c = self.lfu_cache(3)
        c.clear()
        self.assertEqual(list(reversed(c)), [])
        self.assertEqual(list(c.items()), [])
        self.assertEqual(c.evicted, [])

    def test_update(self):
        c = self.lfu_cache(3)
        with self.assertRaises(NotImplementedError):
            c.update()

    def test_copy(self):
        self._test_dup(lambda c: c.copy())

    def test_pickle(self):
        self._test_dup(lambda c: pickle.loads(pickle.dumps(c)))

    def _test_dup(self, dup):
        f = self.lfu_cache(3)
        c = dup(f)
        self.assertIsNot(c, f)
        self.assertEqual(c.cap, 3)
        self.assertEqual(list(reversed(c)), ['a', 'b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assertEqual(c.evicted, [])
        freq = c._head.next
        self.assertEqual(freq.value, 1)
        self.assertEqual(freq.len, 3)
        self.assertEqual(c._head.prev.value, 1)

        f = self.lfu_cache(3)
        f['b']
        f['c']
        f['c']
        c = dup(f)
        self.assertIsNot(c, f)
        self.assertEqual(c.cap, 3)
        self.assertEqual(list(reversed(c)), ['a', 'b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assertEqual(c.evicted, [])
        freq = c._head.next
        self.assertEqual(freq.value, 1)
        self.assertEqual(freq.len, 1)
        self.assertEqual(freq.head.key, 'a')
        self.assertEqual(freq.head.value, 1)
        freq = c._head.next.next
        self.assertEqual(freq.value, 2)
        self.assertEqual(freq.len, 1)
        self.assertEqual(freq.head.key, 'b')
        self.assertEqual(freq.head.value, 2)
        freq = c._head.next.next.next
        self.assertEqual(freq.value, 3)
        self.assertEqual(freq.len, 1)
        self.assertEqual(freq.head.key, 'c')
        self.assertEqual(freq.head.value, 3)
        self.assertEqual(c._head.prev.value, 3)


class LFUCache(util.LFUCache):

    def on_init(self):
        super().on_init()
        self.evicted = []

    def on_evicted(self, k, v):
        super().on_evicted(k, v)
        self.evicted.append((k, v))
