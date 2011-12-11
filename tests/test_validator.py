#
# test_validator
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

from ayame import core, markup, validator
from ayame.exception import ValidationError


def test_validator():
    class Validator(validator.Validator):
        def validate(self, object):
            super(Validator, self).validate(object)

    v = Validator()
    eq_(v.validate(None), None)

def test_email_validator():
    v = validator.EmailValidator()
    eq_(v.validate('a@example.com'), None)
    eq_(v.validate('a@localhost'), None)
    assert_raises(ValidationError, v.validate, None)
    assert_raises(ValidationError, v.validate, '')
    assert_raises(ValidationError, v.validate, 'a@b@example.com')
    assert_raises(ValidationError, v.validate, 'a@example.')

def test_url_validator():
    v = validator.URLValidator()

    eq_(v.validate('http://127.0.0.1'), None)
    eq_(v.validate('http://127.0.0.1/'), None)
    eq_(v.validate('http://127.0.0.1:80'), None)
    eq_(v.validate('http://127.0.0.1:80/'), None)
    eq_(v.validate('http://localhost'), None)
    eq_(v.validate('http://localhost/'), None)
    eq_(v.validate('http://localhost:80'), None)
    eq_(v.validate('http://localhost:80/'), None)
    eq_(v.validate('http://example.com'), None)
    eq_(v.validate('http://example.com/'), None)
    eq_(v.validate('http://example.com:80'), None)
    eq_(v.validate('http://example.com:80/'), None)

    eq_(v.validate('http://user@example.com/'), None)
    eq_(v.validate('http://user:password@example.com/'), None)
    eq_(v.validate('http://example.com/?query'), None)
    eq_(v.validate('http://example.com/#fragment'), None)
    eq_(v.validate('http://example.com/?query#fragment'), None)
    eq_(v.validate('http://example.com/segment/?query'), None)
    eq_(v.validate('http://example.com/segment/#fragment'), None)
    eq_(v.validate('http://example.com/segment/?query#fragment'), None)

    assert_raises(ValidationError, v.validate, None)
    assert_raises(ValidationError, v.validate, '')
    assert_raises(ValidationError, v.validate, 'mailto:a@example.com')
    assert_raises(ValidationError, v.validate, 'http://user`@example.com')

def test_range_validator():
    v = validator.RangeValidator()

    # unlimited
    v.min = None
    v.max = None
    eq_(v.validate(None), None)
    eq_(v.validate(''), None)
    eq_(v.validate(0), None)

    # integer
    v.min = 0
    v.max = None
    eq_(v.validate(0), None)
    assert_raises(ValidationError, v.validate, -1)
    v.max = 9
    eq_(v.validate(9), None)
    assert_raises(ValidationError, v.validate, 10)
    assert_raises(ValidationError, v.validate, None)
    assert_raises(ValidationError, v.validate, '')
    assert_raises(ValidationError, v.validate, 0.0)

def test_string_validator():
    v = validator.StringValidator()
    eq_(v.validate(''), None)
    assert_raises(ValidationError, v.validate, None)
    assert_raises(ValidationError, v.validate, 0)
    v.min = 4
    v.max = 4
    eq_(v.validate('.com'), None)
    assert_raises(ValidationError, v.validate, '')
    assert_raises(ValidationError, v.validate, '.info')

    root = markup.Element(validator._INPUT)
    root.attrib[validator._TYPE] = 'text'
    mc = core.MarkupContainer('a')
    v = validator.StringValidator()
    mc.add(v)
    root = mc.render(root)
    eq_(root.attrib, {validator._TYPE: 'text'})
    v.max = 3
    root = mc.render(root)
    eq_(root.attrib, {validator._TYPE: 'text',
                      validator._MAXLENGTH: '3'})
