#
# test_local
#
#   Copyright (c) 2012 Akinori Hattori <hattya@gmail.com>
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

from nose.tools import assert_raises, eq_

from ayame import local
from ayame.exception import AyameError


def test_empty():
    eq_(local.pop(), None)

    assert_raises(AyameError, local.context)
    assert_raises(AyameError, local.app)


def test_push():
    ctx = local.push(0, 1)
    eq_(ctx.app, 0)
    eq_(ctx.environ, 1)
    eq_(ctx.request, None)
    eq_(ctx._router, None)

    eq_(local.context(), ctx)
    eq_(local.app(), ctx.app)
    eq_(local.pop(), ctx)

    eq_(local.pop(), None)

    assert_raises(AyameError, local.context)
    assert_raises(AyameError, local.app)
