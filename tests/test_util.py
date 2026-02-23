#
# test_util
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import collections.abc
import os
import pickle
import queue
import threading
import unittest.mock

from ayame import util
from base import AyameTestCase


class UtilTestCase(AyameTestCase):

    def test_fqon_of_builtin(self):
        self.assertEqual(util.fqon_of(None), 'NoneType')
        self.assertEqual(util.fqon_of(True), 'bool')
        self.assertEqual(util.fqon_of(False), 'bool')
        self.assertEqual(util.fqon_of(1), 'int')
        self.assertEqual(util.fqon_of(3.14), 'float')
        self.assertEqual(util.fqon_of(''), 'str')
        self.assertEqual(util.fqon_of(()), 'tuple')
        self.assertEqual(util.fqon_of([]), 'list')
        self.assertEqual(util.fqon_of({}), 'dict')

    def test_fqon_of_class(self):
        class C:
            pass

        self.assertEqual(util.fqon_of(C), f'{__name__}.C')
        self.assertEqual(util.fqon_of(C()), f'{__name__}.C')
        C.__module__ = None
        self.assertEqual(util.fqon_of(C), '<unknown>.C')
        self.assertEqual(util.fqon_of(C()), '<unknown>.C')

    def test_fqon_of_function(self):
        def f():
            pass

        self.assertEqual(util.fqon_of(f), f'{__name__ }.f')
        del f.__module__
        self.assertEqual(util.fqon_of(f), '<unknown>.f')

        f = lambda: None

        self.assertEqual(util.fqon_of(f), f'{__name__ }.<lambda>')
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
        self.assertEqual(util.to_list(True), [True])
        self.assertEqual(util.to_list(False), [False])
        self.assertEqual(util.to_list(''), [''])
        self.assertEqual(util.to_list(()), [])
        self.assertEqual(util.to_list([]), [])
        self.assertEqual(util.to_list({}), [])

        self.assertEqual(util.to_list(1), [1])
        self.assertEqual(util.to_list(3.14), [3.14])
        self.assertEqual(util.to_list('abc'), ['abc'])
        self.assertEqual(util.to_list((1,)), [1])
        self.assertEqual(util.to_list([1]), [1])
        self.assertEqual(util.to_list({'a': 1}), ['a'])

    def test_new_token(self):
        a = util.new_token()
        b = util.new_token()
        self.assertNotEqual(a, b)
        self.assertEqual(len(a), len(b))

        a = util.new_token()
        b = util.new_token('sha512')
        self.assertNotEqual(len(a), len(b))
        self.assertLess(len(a), len(b))

    def test_filter_dict(self):
        class LowerDict(util.FilterDict):
            def __convert__(self, key):
                return key.lower() if isinstance(key, str) else super().__convert__(key)

        for v in (
            [('a', -1), ('A', -1)],
            { 'a': -1,   'A': -1 },
        ):
            with self.subTest(type=type(v)):
                d = LowerDict(v, a=-1, A=1)
                self.assertEqual(d['A'], 1)
                self.assertEqual(d['a'], 1)
                self.assertIn('A', d)
                self.assertIn('a', d)
                self.assertEqual(d.get('A'), 1)
                self.assertEqual(d.get('a'), 1)
                self.assertEqual(d.setdefault('A', -1), 1)
                self.assertEqual(d.setdefault('A', -1), 1)
                self.assertEqual(d, {'a': 1})

        d['B'] = 2
        self.assertEqual(d['B'], 2)
        self.assertEqual(d['b'], 2)
        self.assertIn('B', d)
        self.assertIn('b', d)
        self.assertEqual(d.get('B'), 2)
        self.assertEqual(d.get('b'), 2)
        self.assertEqual(d.setdefault('B', -1), 2)
        self.assertEqual(d.setdefault('b', -1), 2)
        self.assertEqual(d, {'a': 1, 'b': 2})

        with self.assertRaises(KeyError):
            d['_']
        self.assertEqual(d.get('_', 0), 0)
        self.assertIsNone(d.setdefault('_'))
        self.assertEqual(d, {'a': 1, 'b': 2, '_': None})

        del d['_']
        with self.assertRaises(KeyError):
            del d['_']
        self.assertEqual(d, {'a': 1, 'b': 2})
        self.assertEqual(d.pop('A'), 1)
        self.assertEqual(d.pop('b'), 2)
        self.assertEqual(d.pop('_', 0), 0)
        with self.assertRaises(KeyError):
            d.pop('_')
        self.assertEqual(d, {})

        d.update([('a', -1), ('A', -1)], a=-1, A=1)
        self.assertEqual(d, {'a': 1})
        d.update({ 'b': -2,   'B': -2 }, b=-2, B=2)
        self.assertEqual(d, {'a': 1, 'b': 2})

        x = d.copy()
        self.assertIsInstance(x, LowerDict)
        self.assertEqual(x, d)
        self.assertIsNot(x, d)
        d[0] = 'd'
        x[0] = 'x'
        self.assertEqual(d, {'a': 1, 'b': 2, 0: 'd'})
        self.assertEqual(x, {'a': 1, 'b': 2, 0: 'x'})

        d.clear()
        x = d | {'A': 1} | [('B', 2)] | None | object()
        self.assertEqual(d, {})
        self.assertEqual(x, {'a': 1, 'b': 2})

        d.clear()
        d |= {'A': 1}
        d |= [('B', 2)]
        d |= None
        d |= object()
        self.assertEqual(d, {'a': 1, 'b': 2})

    def test_cache(self):
        class Cache(util._Cache):
            def __getitem__(self, key):
                return super().__getitem__(key)

            def __setitem__(self, key, value):
                return super().__setitem__(key, value)

            def _iter(self):
                return super()._iter()

            def _sweep(self):
                super()._sweep()

            def _evict(self, e):
                super()._evict(e)

        class Entry:
            def __init__(self, key, value):
                self.key = key
                self.value = value

        with self.assertRaises(TypeError):
            util._Cache()

        c = Cache()
        with self.assertRaises(NotImplementedError):
            c['a']
        with self.assertRaises(NotImplementedError):
            c['a'] = 1
        with self.assertRaises(NotImplementedError):
            c._iter()
        with self.assertRaises(NotImplementedError):
            c._sweep()
        c._evict(Entry('a', 1))


class RWLockTestCase(AyameTestCase):

    def test_lock_with_rr(self):
        lock = util.RWLock()
        data = queue.SimpleQueue()
        done = threading.Barrier(2)
        r_set = threading.Event()

        def r1(lock, data, r_set, done):
            with lock.read():
                data.put((lock._rcnt, lock._rwait))
                r_set.set()
                done.wait()

        def r2(lock, data, r_set, done):
            r_set.wait()
            with lock.read():
                data.put((lock._rcnt, lock._rwait))
                done.wait()

        t1 = threading.Thread(target=r1, args=(lock, data, r_set, done))
        t1.start()
        t2 = threading.Thread(target=r2, args=(lock, data, r_set, done))
        t2.start()

        t1.join()
        t2.join()
        self.assertEqual(threading.active_count(), 1)

        self.assertEqual(data.qsize(), 2)
        self.assertEqual(data.get(), (1, 0))
        self.assertEqual(data.get(), (2, 0))

    def test_lock_with_ww(self):
        lock = util.RWLock()
        data = queue.SimpleQueue()
        done = threading.Barrier(2)
        w_set = threading.Event()
        w_wait = lock._w.wait

        def w1(lock, data, w_set, done):
            with lock.write():
                data.put((lock._rcnt, lock._rwait))
                w_set.set()
                done.wait()

        def w2(lock, data, w_set):
            w_set.wait()
            with lock.write():
                data.put((lock._rcnt, lock._rwait))

        def side_effect():
            done.wait()
            w_wait()

        with unittest.mock.patch.object(lock._w, 'wait', side_effect=side_effect):
            t1 = threading.Thread(target=w1, args=(lock, data, w_set, done))
            t1.start()
            t2 = threading.Thread(target=w2, args=(lock, data, w_set))
            t2.start()

            t1.join()
            t2.join()
            self.assertEqual(threading.active_count(), 1)

        self.assertEqual(data.qsize(), 2)
        self.assertEqual(data.get(), (-1, 0))
        self.assertEqual(data.get(), (-1, 0))

    def test_lock_with_wr(self):
        lock = util.RWLock()
        data = queue.SimpleQueue()
        done = threading.Barrier(2)
        r_set = threading.Event()
        r_wait = lock._r.wait

        def w(lock, data, r_set, done):
            with lock.write():
                data.put((lock._rcnt, lock._rwait))
                r_set.set()
                done.wait()

        def r(lock, data, r_set):
            r_set.wait()
            with lock.read():
                data.put((lock._rcnt, lock._rwait))

        def side_effect():
            done.wait()
            r_wait()

        with unittest.mock.patch.object(lock._r, 'wait', side_effect=side_effect):
            t1 = threading.Thread(target=w, args=(lock, data, r_set, done))
            t1.start()
            t2 = threading.Thread(target=r, args=(lock, data, r_set))
            t2.start()

            t1.join()
            t2.join()
            self.assertEqual(threading.active_count(), 1)

        self.assertEqual(data.qsize(), 2)
        self.assertEqual(data.get(), (-1, 0))
        self.assertEqual(data.get(), (1, 0))

    def test_lock_with_rrw(self):
        lock = util.RWLock()
        data = queue.SimpleQueue()
        r_done = threading.Barrier(2)
        w_done = threading.Barrier(3)
        r_set = threading.Event()
        w_set = threading.Event()
        w_wait = lock._w.wait

        def r1(lock, data, r_set, r_done, w_done):
            with lock.read():
                data.put((lock._rcnt, lock._rwait))
                r_set.set()
                w_done.wait()
                data.put((lock._rcnt, lock._rwait))
                r_done.wait()

        def r2(lock, data, r_set, w_set, r_done, w_done):
            r_set.wait()
            with lock.read():
                data.put((lock._rcnt, lock._rwait))
                w_set.set()
                w_done.wait()
                data.put((lock._rcnt, lock._rwait))
                r_done.wait()

        def w(lock, data, w_set):
            w_set.wait()
            with lock.write():
                data.put((lock._rcnt, lock._rwait))

        def side_effect():
            w_done.wait()
            w_wait()

        with unittest.mock.patch.object(lock._w, 'wait', side_effect=side_effect):
            t1 = threading.Thread(target=r1, args=(lock, data, r_set, r_done, w_done))
            t1.start()
            t2 = threading.Thread(target=r2, args=(lock, data, r_set, w_set, r_done, w_done))
            t2.start()
            t3 = threading.Thread(target=w, args=(lock, data, w_set))
            t3.start()

            t1.join()
            t2.join()
            t3.join()
            self.assertEqual(threading.active_count(), 1)

        self.assertEqual(data.qsize(), 5)
        self.assertEqual(data.get(), (1, 0))
        self.assertEqual(data.get(), (2, 0))
        self.assertEqual(data.get(), (-3, 2))
        self.assertEqual(data.get(), (-3, 2))
        self.assertEqual(data.get(), (-1, 0))

    def test_release(self):
        lock = util.RWLock()
        with self.assertRaises(RuntimeError):
            lock.release_read()
        with self.assertRaises(RuntimeError):
            lock.release_write()


@unittest.mock.patch.object(util.LRUCache, 'on_evicted', autospec=True, wraps=util.LRUCache.on_evicted)
class LRUCacheTestCase(AyameTestCase):

    def lru_cache(self, n):
        c = util.LRUCache(n)
        for i in range(n):
            c[chr(ord('a')+i)] = i + 1
        return c

    def call_args_list(self, mock):
        return [c.args[1:] for c in mock.call_args_list]

    def test_lru_cache(self, _):
        c = util.LRUCache(3)
        self.assertEqual(c.cap, 3)
        self.assertEqual(len(c), 0)
        self.assertIsInstance(c, collections.abc.MutableMapping)

    def test_repr(self, _):
        c = self.lru_cache(0)
        self.assertEqual(repr(c), 'LRUCache([])')

        c = self.lru_cache(3)
        self.assertEqual(repr(c), "LRUCache([('c', 3), ('b', 2), ('a', 1)])")

    def test_set(self, on_evicted):
        c = self.lru_cache(3)

        c['c'] = 3.0
        c['b'] = 2.0
        c['a'] = 1.0
        self.assertEqual(list(reversed(c)), ['c', 'b', 'a'])
        self.assertEqual(list(c.items()), [('a', 1.0), ('b', 2.0), ('c', 3.0)])
        self.assertEqual(self.call_args_list(on_evicted), [])

        c['a'] = 1
        c['b'] = 2
        c['c'] = 3
        c['d'] = 4
        self.assertEqual(list(reversed(c)), ['b', 'c', 'd'])
        self.assertEqual(list(c.items()), [('d', 4), ('c', 3), ('b', 2)])
        self.assertEqual(self.call_args_list(on_evicted)[0:], [('a', 1.0)])

        self.assertEqual(c.setdefault('c', 0), 3)
        self.assertEqual(c.setdefault('d', 0), 4)
        self.assertEqual(c.setdefault('e', 5), 5)
        self.assertEqual(list(reversed(c)), ['c', 'd', 'e'])
        self.assertEqual(list(c.items()), [('e', 5), ('d', 4), ('c', 3)])
        self.assertEqual(self.call_args_list(on_evicted)[1:], [('b', 2)])

    def test_get(self, on_evicted):
        c = self.lru_cache(3)
        self.assertEqual(list(reversed(c)), ['a', 'b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assertEqual(self.call_args_list(on_evicted), [])

        self.assertEqual(c['c'], 3)
        self.assertEqual(c['b'], 2)
        self.assertEqual(c['a'], 1)
        self.assertEqual(list(reversed(c)), ['c', 'b', 'a'])
        self.assertEqual(list(c.items()), [('a', 1), ('b', 2), ('c', 3)])
        self.assertEqual(self.call_args_list(on_evicted), [])

        self.assertEqual(c.peek('a'), 1)
        self.assertEqual(c.peek('b'), 2)
        self.assertEqual(c.peek('c'), 3)
        self.assertEqual(list(reversed(c)), ['c', 'b', 'a'])
        self.assertEqual(list(c.items()), [('a', 1), ('b', 2), ('c', 3)])
        self.assertEqual(self.call_args_list(on_evicted), [])

        self.assertEqual(c.get('a'), 1)
        self.assertEqual(c.get('b'), 2)
        self.assertEqual(c.get('c'), 3)
        self.assertEqual(c.get('z', 26), 26)
        self.assertEqual(list(reversed(c)), ['a', 'b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assertEqual(self.call_args_list(on_evicted), [])

    def test_del(self, on_evicted):
        c = self.lru_cache(3)
        del c['a']
        self.assertEqual(list(reversed(c)), ['b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2)])
        self.assertEqual(self.call_args_list(on_evicted), [('a', 1)])

        on_evicted.reset_mock()
        c = self.lru_cache(3)
        del c['b']
        self.assertEqual(list(reversed(c)), ['a', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('a', 1)])
        self.assertEqual(self.call_args_list(on_evicted), [('b', 2)])

        on_evicted.reset_mock()
        c = self.lru_cache(3)
        del c['c']
        self.assertEqual(list(reversed(c)), ['a', 'b'])
        self.assertEqual(list(c.items()), [('b', 2), ('a', 1)])
        self.assertEqual(self.call_args_list(on_evicted), [('c', 3)])

        on_evicted.reset_mock()
        c = self.lru_cache(3)
        self.assertEqual(c.pop('b'), 2)
        self.assertEqual(list(reversed(c)), ['a', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('a', 1)])
        self.assertEqual(self.call_args_list(on_evicted), [('b', 2)])

        with self.assertRaises(KeyError):
            c.pop('b')
        self.assertIsNone(c.pop('b', None))
        self.assertEqual(c.pop('c', 0), 3)

        on_evicted.reset_mock()
        c = self.lru_cache(3)
        n = len(c)
        for i in range(1, n + 1):
            self.assertEqual(len(c.popitem()), 2)
            self.assertEqual(len(c), n - i)
            self.assertEqual(on_evicted.call_count, i)
        with self.assertRaises(KeyError):
            c.popitem()

    def test_iter(self, _):
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

    def test_resize(self, on_evicted):
        c = self.lru_cache(3)

        c.cap = 2
        self.assertEqual(list(reversed(c)), ['b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2)])
        self.assertEqual(self.call_args_list(on_evicted)[0:], [('a', 1)])
        c['d'] = 4
        self.assertEqual(list(reversed(c)), ['c', 'd'])
        self.assertEqual(list(c.items()), [('d', 4), ('c', 3)])
        self.assertEqual(self.call_args_list(on_evicted)[1:], [('b', 2)])

        c.cap = 1
        self.assertEqual(list(reversed(c)), ['d'])
        self.assertEqual(list(c.items()), [('d', 4)])
        self.assertEqual(self.call_args_list(on_evicted)[2:], [('c', 3)])
        c['e'] = 5
        self.assertEqual(list(reversed(c)), ['e'])
        self.assertEqual(list(c.items()), [('e', 5)])
        self.assertEqual(self.call_args_list(on_evicted)[3:], [('d', 4)])

        c.cap = 0
        self.assertEqual(list(reversed(c)), [])
        self.assertEqual(list(c.items()), [])
        self.assertEqual(self.call_args_list(on_evicted)[4:], [('e', 5)])

        c.cap = -1
        c['f'] = 6
        c['g'] = 7
        c['h'] = 8
        c['i'] = 9
        self.assertEqual(list(reversed(c)), ['f', 'g', 'h', 'i'])
        self.assertEqual(list(c.items()), [('i', 9), ('h', 8), ('g', 7), ('f', 6)])
        self.assertEqual(self.call_args_list(on_evicted)[5:], [])

    def test_clear(self, on_evicted):
        c = self.lru_cache(3)
        c.clear()
        self.assertEqual(list(reversed(c)), [])
        self.assertEqual(list(c.items()), [])
        self.assertEqual(self.call_args_list(on_evicted), [])

    def test_update(self, _):
        c = self.lru_cache(3)
        with self.assertRaises(NotImplementedError):
            c.update()

    def test_copy(self, on_evicted):
        self._test_dup(on_evicted, lambda c: c.copy())

    def test_pickle(self, on_evicted):
        self._test_dup(on_evicted, lambda c: pickle.loads(pickle.dumps(c)))

    def _test_dup(self, on_evicted, dup):
        r = self.lru_cache(3)
        c = dup(r)
        self.assertIsNot(c, r)
        self.assertEqual(c.cap, 3)
        self.assertEqual(list(reversed(c)), ['a', 'b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assertEqual(self.call_args_list(on_evicted), [])


@unittest.mock.patch.object(util.LFUCache, 'on_evicted', autospec=True, wraps=util.LFUCache.on_evicted)
class LFUCacheTestCase(AyameTestCase):

    def lfu_cache(self, n):
        c = util.LFUCache(n)
        for i in range(n):
            c[chr(ord('a')+i)] = i + 1
        return c

    def call_args_list(self, mock):
        return [c.args[1:] for c in mock.call_args_list]

    def test_lfu_cache(self, _):
        c = util.LFUCache(3)
        self.assertEqual(c.cap, 3)
        self.assertEqual(len(c), 0)
        self.assertIsInstance(c, collections.abc.MutableMapping)
        with self.assertRaises(RuntimeError):
            c._lfu()

    def test_repr(self, _):
        c = self.lfu_cache(0)
        self.assertEqual(repr(c), 'LFUCache([])')

        c = self.lfu_cache(3)
        self.assertEqual(repr(c), "LFUCache([('c', 3), ('b', 2), ('a', 1)])")

    def test_set(self, on_evicted):
        c = self.lfu_cache(3)

        c['c'] = 3.0
        c['b'] = 2.0
        c['a'] = 1.0
        self.assertEqual(list(reversed(c)), ['c', 'b', 'a'])
        self.assertEqual(list(c.items()), [('a', 1.0), ('b', 2.0), ('c', 3.0)])
        self.assertEqual(self.call_args_list(on_evicted)[0:], [('c', 3), ('b', 2), ('a', 1)])

        c['a'] = 1
        c['b'] = 2
        c['c'] = 3
        c['d'] = 4
        self.assertEqual(list(reversed(c)), ['b', 'c', 'd'])
        self.assertEqual(list(c.items()), [('d', 4), ('c', 3), ('b', 2)])
        self.assertEqual(self.call_args_list(on_evicted)[3:], [('a', 1.0), ('b', 2.0), ('c', 3.0), ('a', 1)])

        self.assertEqual(c.setdefault('d', 0), 4)
        self.assertEqual(c.setdefault('e', 5), 5)
        self.assertEqual(c.setdefault('c', 0), 3)
        self.assertEqual(list(reversed(c)), ['e', 'd', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('d', 4), ('e', 5)])
        self.assertEqual(self.call_args_list(on_evicted)[7:], [('b', 2)])

    def test_get(self, on_evicted):
        c = self.lfu_cache(3)
        self.assertEqual(list(reversed(c)), ['a', 'b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assertEqual(self.call_args_list(on_evicted), [])

        self.assertEqual(c['c'], 3)
        self.assertEqual(c['b'], 2)
        self.assertEqual(c['a'], 1)
        self.assertEqual(list(reversed(c)), ['c', 'b', 'a'])
        self.assertEqual(list(c.items()), [('a', 1), ('b', 2), ('c', 3)])
        self.assertEqual(self.call_args_list(on_evicted), [])

        self.assertEqual(c.peek('a'), 1)
        self.assertEqual(c.peek('b'), 2)
        self.assertEqual(c.peek('c'), 3)
        self.assertEqual(list(reversed(c)), ['c', 'b', 'a'])
        self.assertEqual(list(c.items()), [('a', 1), ('b', 2), ('c', 3)])
        self.assertEqual(self.call_args_list(on_evicted), [])

        self.assertEqual(c.get('a'), 1)
        self.assertEqual(c.get('b'), 2)
        self.assertEqual(c.get('c'), 3)
        self.assertEqual(c.get('z', 26), 26)
        self.assertEqual(list(reversed(c)), ['a', 'b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assertEqual(self.call_args_list(on_evicted), [])

    def test_del(self, on_evicted):
        c = self.lfu_cache(3)
        del c['a']
        self.assertEqual(list(reversed(c)), ['b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2)])
        self.assertEqual(self.call_args_list(on_evicted), [('a', 1)])

        on_evicted.reset_mock()
        c = self.lfu_cache(3)
        del c['b']
        self.assertEqual(list(reversed(c)), ['a', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('a', 1)])
        self.assertEqual(self.call_args_list(on_evicted), [('b', 2)])

        on_evicted.reset_mock()
        c = self.lfu_cache(3)
        del c['c']
        self.assertEqual(list(reversed(c)), ['a', 'b'])
        self.assertEqual(list(c.items()), [('b', 2), ('a', 1)])
        self.assertEqual(self.call_args_list(on_evicted), [('c', 3)])

        on_evicted.reset_mock()
        c = self.lfu_cache(3)
        self.assertEqual(c.pop('b'), 2)
        self.assertEqual(list(reversed(c)), ['a', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('a', 1)])
        self.assertEqual(self.call_args_list(on_evicted), [('b', 2)])

        with self.assertRaises(KeyError):
            c.pop('b')
        self.assertIsNone(c.pop('b', None))
        self.assertEqual(c.pop('c', 0), 3)

        on_evicted.reset_mock()
        c = self.lfu_cache(3)
        n = len(c)
        for i in range(1, n + 1):
            self.assertEqual(len(c.popitem()), 2)
            self.assertEqual(len(c), n - i)
            self.assertEqual(on_evicted.call_count, i)
        with self.assertRaises(KeyError):
            c.popitem()

    def test_iter(self, _):
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

    def test_resize(self, on_evicted):
        c = self.lfu_cache(3)

        c.cap = 2
        self.assertEqual(list(reversed(c)), ['b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2)])
        self.assertEqual(self.call_args_list(on_evicted)[0:], [('a', 1)])
        c['d'] = 4
        self.assertEqual(list(reversed(c)), ['c', 'd'])
        self.assertEqual(list(c.items()), [('d', 4), ('c', 3)])
        self.assertEqual(self.call_args_list(on_evicted)[1:], [('b', 2)])

        c.cap = 1
        self.assertEqual(list(reversed(c)), ['d'])
        self.assertEqual(list(c.items()), [('d', 4)])
        self.assertEqual(self.call_args_list(on_evicted)[2:], [('c', 3)])
        c['e'] = 5
        self.assertEqual(list(reversed(c)), ['e'])
        self.assertEqual(list(c.items()), [('e', 5)])
        self.assertEqual(self.call_args_list(on_evicted)[3:], [('d', 4)])

        c.cap = 0
        self.assertEqual(list(reversed(c)), [])
        self.assertEqual(list(c.items()), [])
        self.assertEqual(self.call_args_list(on_evicted)[4:], [('e', 5)])

        c.cap = -1
        c['f'] = 6
        c['g'] = 7
        c['h'] = 8
        c['i'] = 9
        self.assertEqual(list(reversed(c)), ['f', 'g', 'h', 'i'])
        self.assertEqual(list(c.items()), [('i', 9), ('h', 8), ('g', 7), ('f', 6)])
        self.assertEqual(self.call_args_list(on_evicted)[5:], [])

    def test_clear(self, on_evicted):
        c = self.lfu_cache(3)
        c.clear()
        self.assertEqual(list(reversed(c)), [])
        self.assertEqual(list(c.items()), [])
        self.assertEqual(self.call_args_list(on_evicted), [])

    def test_update(self, _):
        c = self.lfu_cache(3)
        with self.assertRaises(NotImplementedError):
            c.update()

    def test_copy(self, on_evicted):
        self._test_dup(on_evicted, lambda c: c.copy())

    def test_pickle(self, on_evicted):
        self._test_dup(on_evicted, lambda c: pickle.loads(pickle.dumps(c)))

    def _test_dup(self, on_evicted, dup):
        f = self.lfu_cache(3)
        c = dup(f)
        self.assertIsNot(c, f)
        self.assertEqual(c.cap, 3)
        self.assertEqual(list(reversed(c)), ['a', 'b', 'c'])
        self.assertEqual(list(c.items()), [('c', 3), ('b', 2), ('a', 1)])
        self.assertEqual(self.call_args_list(on_evicted), [])
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
        self.assertEqual(self.call_args_list(on_evicted), [])
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
