#
# test_util
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

from __future__ import unicode_literals

from nose.tools import assert_raises, eq_, ok_

from ayame import util


def test_to_bytes():
    # iroha in hiragana
    v = util.to_bytes('\u3044\u308d\u306f')
    eq_(v, b'\xe3\x81\x84\xe3\x82\x8d\xe3\x81\xaf')
    ok_(isinstance(v, bytes))

    v = util.to_bytes('\u3044\u308d\u306f', 'ascii', 'ignore')
    eq_(v, b'')
    ok_(isinstance(v, bytes))

    assert_raises(UnicodeEncodeError,
                  util.to_bytes, '\u3044\u308d\u306f', 'ascii')

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
