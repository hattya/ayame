#
# test_basic
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

from nose.tools import assert_raises, eq_

from ayame import basic, core, markup
from ayame.exception import ComponentError


def test_label():
    c = basic.Label('1')
    eq_(c.model, None)
    elem = c.render(markup.Element(None))
    eq_(elem.attrib, {})
    eq_(elem.children, [''])

def test_label_with_model():
    m = core.Model([])
    c = basic.Label('1', m)
    eq_(c.model, m)
    assert_raises(ComponentError, c.render, markup.Element(None))

    m = core.Model('<tag>')
    c = basic.Label('1', m)
    eq_(c.model, m)
    elem = c.render(markup.Element(None))
    eq_(elem.attrib, {})
    eq_(elem.children, ['&lt;tag&gt;'])

    c = basic.Label('1', '<tag>')
    eq_(c.model.object, '<tag>')
    elem = c.render(markup.Element(None))
    eq_(elem.attrib, {})
    eq_(elem.children, ['&lt;tag&gt;'])
