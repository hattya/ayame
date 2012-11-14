#
# test_util
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

import io
import sys

from nose.tools import assert_raises, eq_, ok_

from ayame import util
from ayame.exception import ResourceError


def test_fqon_of():
    class O:
        pass
    class N(object):
        pass

    o = O()
    n = N()

    def f():
        pass
    def u():
        pass
    del u.__module__

    eq_(util.fqon_of(O), __name__ + '.O')
    eq_(util.fqon_of(o), __name__ + '.O')
    eq_(util.fqon_of(N), __name__ + '.N')
    eq_(util.fqon_of(n), __name__ + '.N')
    eq_(util.fqon_of(f), __name__ + '.f')
    eq_(util.fqon_of(u), '<unknown>.u')
    eq_(util.fqon_of(util), 'ayame.util')
    # __builtin__
    eq_(util.fqon_of([]), 'list')
    eq_(util.fqon_of({}), 'dict')
    eq_(util.fqon_of(1), 'int')
    eq_(util.fqon_of(1.0), 'float')

def test_load_data():
    class Spam(object):
        pass

    def spam():
        pass

    with util.load_data(Spam, 'Spam.txt') as fp:
        eq_(fp.read().strip(), 'test_util/Spam.txt')
    with util.load_data(Spam, '.txt') as fp:
        eq_(fp.read().strip(), 'test_util/Spam.txt')
    with util.load_data(Spam(), 'Spam.txt') as fp:
        eq_(fp.read().strip(), 'test_util/Spam.txt')
    with util.load_data(Spam(), '.txt') as fp:
        eq_(fp.read().strip(), 'test_util/Spam.txt')
    with util.load_data(spam, 'spam.txt') as fp:
        eq_(fp.read().strip(), 'test_util/spam.txt')
    with util.load_data(spam, '.txt') as fp:
        eq_(fp.read().strip(), 'test_util/spam.txt')
    with util.load_data(sys.modules[__name__], '.txt') as fp:
        eq_(fp.read().strip(), 'test_util/.txt')

    class Eggs(object):
        pass
    assert_raises(ResourceError, util.load_data, Eggs, 'Eggs.txt')
    assert_raises(ResourceError, util.load_data, Eggs, '.txt')
    assert_raises(ResourceError, util.load_data, Eggs(), 'Eggs.txt')
    assert_raises(ResourceError, util.load_data, Eggs(), '.txt')

    def eggs():
        pass
    del eggs.__module__
    assert_raises(ResourceError, util.load_data, eggs, 'eggs.txt')
    assert_raises(ResourceError, util.load_data, eggs, '.txt')

    class Module(object):
        __name__ = __name__
    module = sys.modules[__name__]
    sys.modules[__name__] = Module()
    assert_raises(ResourceError, util.load_data, Spam, 'Spam.txt')
    assert_raises(ResourceError, util.load_data, Spam, '.txt')
    assert_raises(ResourceError, util.load_data, Spam(), 'Spam.txt')
    assert_raises(ResourceError, util.load_data, Spam(), '.txt')
    assert_raises(ResourceError, util.load_data, spam, 'spam.txt')
    assert_raises(ResourceError, util.load_data, spam, '.txt')
    assert_raises(ResourceError, util.load_data, sys.modules[__name__], '.txt')
    sys.modules[__name__] = module

    class Module(object):
        __file__ = __file__
        __loader__ = True
        __name__ = __name__
    module = sys.modules[__name__]
    sys.modules[__name__] = Module()
    assert_raises(ResourceError, util.load_data, Spam, 'Spam.txt')
    assert_raises(ResourceError, util.load_data, Spam, '.txt')
    assert_raises(ResourceError, util.load_data, Spam(), 'Spam.txt')
    assert_raises(ResourceError, util.load_data, Spam(), '.txt')
    assert_raises(ResourceError, util.load_data, spam, 'spam.txt')
    assert_raises(ResourceError, util.load_data, spam, '.txt')
    assert_raises(ResourceError, util.load_data, sys.modules[__name__], '.txt')
    sys.modules[__name__] = module

    class Loader(object):
        def get_data(self, path):
            with io.open(path, 'rb') as fp:
                return fp.read().strip() + b' from Loader'
    class Module(object):
        __file__ = __file__
        __loader__ = Loader()
        __name__ = __name__
    module = sys.modules[__name__]
    sys.modules[__name__] = Module()
    with util.load_data(Spam, 'Spam.txt') as fp:
        eq_(fp.read().strip(), 'test_util/Spam.txt from Loader')
    with util.load_data(Spam, '.txt') as fp:
        eq_(fp.read().strip(), 'test_util/Spam.txt from Loader')
    with util.load_data(Spam(), 'Spam.txt') as fp:
        eq_(fp.read().strip(), 'test_util/Spam.txt from Loader')
    with util.load_data(Spam(), '.txt') as fp:
        eq_(fp.read().strip(), 'test_util/Spam.txt from Loader')
    with util.load_data(spam, 'spam.txt') as fp:
        eq_(fp.read().strip(), 'test_util/spam.txt from Loader')
    with util.load_data(spam, '.txt') as fp:
        eq_(fp.read().strip(), 'test_util/spam.txt from Loader')
    loader = getattr(module, '__loader__', None)
    module.__loader__ = Loader()
    with util.load_data(module, '.txt') as fp:
        eq_(fp.read().strip(), 'test_util/.txt from Loader')
    if loader:
        module.__loader__ = loader
    else:
        del module.__loader__
    sys.modules[__name__] = module

def test_to_bytes():
    # iroha in hiragana
    v = util.to_bytes(u'\u3044\u308d\u306f')
    eq_(v, b'\xe3\x81\x84\xe3\x82\x8d\xe3\x81\xaf')
    ok_(isinstance(v, bytes))

    v = util.to_bytes(u'\u3044\u308d\u306f', 'ascii', 'ignore')
    eq_(v, b'')
    ok_(isinstance(v, bytes))

    assert_raises(UnicodeEncodeError,
                  util.to_bytes, u'\u3044\u308d\u306f', 'ascii')

    v = util.to_bytes(b'abc')
    eq_(v, b'abc')
    ok_(isinstance(v, bytes))

    v = util.to_bytes(0)
    eq_(v, b'0')
    ok_(isinstance(v, bytes))

    v = util.to_bytes(3.14)
    eq_(v, b'3.14')
    ok_(isinstance(v, bytes))

def test_to_list():
    eq_(util.to_list(1), [1])
    eq_(util.to_list(3.14), [3.14])
    eq_(util.to_list('abc'), ['abc'])
    eq_(util.to_list(''), [''])
    eq_(util.to_list(None), [])
    eq_(util.to_list([1]), [1])
    eq_(util.to_list((1,)), [1])
    eq_(util.to_list({'a': 1}), ['a'])

def test_new_token():
    a = util.new_token()
    b = util.new_token()
    ok_(a != b)

def test_filter_dict():
    class LowerDict(util.FilterDict):
        def __convert__(self, key):
            if isinstance(key, basestring):
                return key.lower()
            return super(LowerDict, self).__convert__(key)

    d = LowerDict(A=0)

    eq_(d['A'], 0)
    eq_(d['a'], 0)
    ok_('A' in d)
    ok_('a' in d)
    eq_(d.get('A'), 0)
    eq_(d.get('a'), 0)
    ok_(d.has_key('A'))
    ok_(d.has_key('a'))
    d.setdefault('a', -1)
    eq_(d, {'a': 0})

    d['B'] = 1
    eq_(d['B'], 1)
    eq_(d['b'], 1)
    ok_('B' in d)
    ok_('b' in d)
    eq_(d.get('B'), 1)
    eq_(d.get('b'), 1)
    ok_(d.has_key('B'))
    ok_(d.has_key('b'))
    d.setdefault('b', -1)
    eq_(d, {'a': 0, 'b': 1})

    del d['b']
    eq_(d, {'a': 0})

    eq_(d.pop('a'), 0)
    eq_(d, {})

    d.update(A=0, b=1)
    eq_(d, {'a': 0, 'b': 1})

    d[0] = 'a'
    eq_(d, {'a': 0, 'b': 1, 0: 'a'})

    x = d.copy()
    ok_(isinstance(x, LowerDict))
    eq_(x, d)

    x[0] = 'b'
    eq_(d, {'a': 0, 'b': 1, 0: 'a'})
    eq_(x, {'a': 0, 'b': 1, 0: 'b'})
