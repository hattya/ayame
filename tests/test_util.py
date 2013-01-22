#
# test_util
#
#   Copyright (c) 2011-2013 Akinori Hattori <hattya@gmail.com>
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

import ayame
from ayame import util
from base import AyameTestCase


class UtilTestCase(AyameTestCase):

    def setup(self):
        super(UtilTestCase, self).setup()
        self._module = sys.modules[__name__]

    def teardown(self):
        super(UtilTestCase, self).teardown()
        sys.modules[__name__] = self._module

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
        self.assert_equal(util.fqon_of(O), __name__ + '.O')
        self.assert_equal(util.fqon_of(O()), __name__ + '.O')
        O.__module__ = None
        self.assert_equal(util.fqon_of(O), '<unknown>.O')
        self.assert_equal(util.fqon_of(O()), '<unknown>.O')
        if sys.hexversion < 0x03000000:
            del O.__module__
            self.assert_equal(util.fqon_of(O), 'O')
            self.assert_equal(util.fqon_of(O()), 'O')

        class N(object):
            pass
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

    def test_load_data_class(self):
        class Spam(object):
            pass

        def assert_load(*args):
            with util.load_data(*args) as fp:
                self.assert_equal(fp.read().strip(), 'test_util/Spam.txt')
        assert_load(Spam, 'Spam.txt')
        assert_load(Spam, '.txt')
        assert_load(Spam(), 'Spam.txt')
        assert_load(Spam(), '.txt')

        def assert_load(*args):
            with self.assert_raises_regex(ayame.ResourceError,
                                          "^invalid path '"):
                util.load_data(*args)
        assert_load(Spam, os.path.pardir)
        assert_load(Spam, os.path.join(*(os.path.pardir,) * 2))
        assert_load(Spam, os.path.sep)
        assert_load(Spam(), os.path.pardir)
        assert_load(Spam(), os.path.join(*(os.path.pardir,) * 2))
        assert_load(Spam(), os.path.sep)

        Spam.__module__ = None
        def assert_load(*args):
            with self.assert_raises_regex(ayame.ResourceError,
                                          ' find module '):
                util.load_data(*args)
        assert_load(Spam, 'Spam.txt')
        assert_load(Spam, '.txt')
        assert_load(Spam(), 'Spam.txt')
        assert_load(Spam(), '.txt')

        class Eggs(object):
            pass

        def assert_load(*args):
            with self.assert_raises_regex(ayame.ResourceError, " load .*'$"):
                util.load_data(*args)
        assert_load(Eggs, 'Eggs.txt')
        assert_load(Eggs, '.txt')
        assert_load(Eggs(), 'Eggs.txt')
        assert_load(Eggs(), '.txt')

    def test_load_data_function(self):
        def spam():
            pass

        def assert_load(*args):
            with util.load_data(*args) as fp:
                self.assert_equal(fp.read().strip(), 'test_util/spam.txt')
        assert_load(spam, 'spam.txt')
        assert_load(spam, '.txt')

        def assert_load(*args):
            with self.assert_raises_regex(ayame.ResourceError,
                                          "^invalid path '"):
                util.load_data(*args)
        assert_load(spam, os.path.pardir)
        assert_load(spam, os.path.join(*(os.path.pardir,) * 2))
        assert_load(spam, os.path.sep)

        del spam.__module__
        def assert_load(*args):
            with self.assert_raises_regex(ayame.ResourceError,
                                          ' find module '):
                util.load_data(*args)
        assert_load(spam, 'spam.txt')
        assert_load(spam, '.txt')

        def eggs():
            pass

        def assert_load(*args):
            with self.assert_raises_regex(ayame.ResourceError, " load .*'$"):
                util.load_data(*args)
        assert_load(eggs, 'eggs.txt')
        assert_load(eggs, '.txt')

    def test_load_data_module(self):
        module = sys.modules[__name__]

        with util.load_data(module, '.txt') as fp:
            self.assert_equal(fp.read().strip(), 'test_util/.txt')

        def assert_load(*args):
            with self.assert_raises_regex(ayame.ResourceError,
                                          "^invalid path '"):
                util.load_data(*args)
        assert_load(module, os.path.pardir)
        assert_load(module, os.path.join(*(os.path.pardir,) * 2))
        assert_load(module, os.path.sep)

    def test_load_data_no___file__(self):
        class Module(types.ModuleType):
            pass

        class Spam(object):
            pass
        def spam():
            pass

        sys.modules[__name__] = Module(__name__)
        def assert_load(*args):
            with self.assert_raises_regex(ayame.ResourceError,
                                          "' module location$"):
                util.load_data(*args)
        assert_load(Spam, 'Spam.txt')
        assert_load(Spam, '.txt')
        assert_load(Spam(), 'Spam.txt')
        assert_load(Spam(), '.txt')
        assert_load(spam, 'spam.txt')
        assert_load(spam, '.txt')
        assert_load(sys.modules[__name__], '.txt')

    def test_load_data_no___loader__(self):
        class Module(types.ModuleType):
            __file__ = __file__
            __loader__ = True

        class Spam(object):
            pass
        def spam():
            pass

        sys.modules[__name__] = Module(__name__)
        def assert_load(*args):
            with self.assert_raises_regex(ayame.ResourceError,
                                          " load '.*' from loader "):
                util.load_data(*args)
        assert_load(Spam, 'Spam.txt')
        assert_load(Spam, '.txt')
        assert_load(Spam(), 'Spam.txt')
        assert_load(Spam(), '.txt')
        assert_load(spam, 'spam.txt')
        assert_load(spam, '.txt')
        assert_load(sys.modules[__name__], '.txt')

    def test_load_data___loader__(self):
        class Loader(object):
            def get_data(self, path):
                with io.open(path, 'rb') as fp:
                    return fp.read().strip() + b' from Loader'
        class Module(types.ModuleType):
            __file__ = __file__
            __loader__ = Loader()

        class Spam(object):
            pass
        def spam():
            pass

        sys.modules[__name__] = Module(__name__)

        def assert_load(*args):
            with util.load_data(*args) as fp:
                self.assert_equal(fp.read().strip(),
                                  'test_util/Spam.txt from Loader')
        assert_load(Spam, 'Spam.txt')
        assert_load(Spam, '.txt')
        assert_load(Spam(), 'Spam.txt')
        assert_load(Spam(), '.txt')

        def assert_load(*args):
            with util.load_data(*args) as fp:
                self.assert_equal(fp.read().strip(),
                                  'test_util/spam.txt from Loader')
        assert_load(spam, 'spam.txt')
        assert_load(spam, '.txt')

        with util.load_data(sys.modules[__name__], '.txt') as fp:
            self.assert_equal(fp.read().strip(), 'test_util/.txt from Loader')

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

    def test_filter_dict(self):
        class LowerDict(util.FilterDict):
            def __convert__(self, key):
                if isinstance(key, basestring):
                    return key.lower()
                return super(LowerDict, self).__convert__(key)

        d = LowerDict(a=-1, A=0)
        self.assert_equal(d['A'], 0)
        self.assert_equal(d['a'], 0)
        self.assert_in('A', d)
        self.assert_in('a', d)
        self.assert_equal(d.get('A'), 0)
        self.assert_equal(d.get('a'), 0)
        self.assert_true(d.has_key('A'))
        self.assert_true(d.has_key('a'))
        d.setdefault('a', -1)
        self.assert_equal(d, {'a': 0})

        d['B'] = 1
        self.assert_equal(d['B'], 1)
        self.assert_equal(d['b'], 1)
        self.assert_in('B', d)
        self.assert_in('b', d)
        self.assert_equal(d.get('B'), 1)
        self.assert_equal(d.get('b'), 1)
        self.assert_true(d.has_key('B'))
        self.assert_true(d.has_key('b'))
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
