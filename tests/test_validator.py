#
# test_validator
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

import ayame
from ayame import markup, validator
from base import AyameTestCase


class ValidatorTestCase(AyameTestCase):

    def test_validator(self):
        class Validator(validator.Validator):
            def validate(self, object):
                super(Validator, self).validate(object)

        v = Validator()
        self.assert_false(v.validate(None))

    def test_email_validator(self):
        v = validator.EmailValidator()
        self.assert_false(v.validate('a@example.com'))
        self.assert_false(v.validate('a@localhost'))

        with self.assert_raises(ayame.ValidationError):
            v.validate(None)
        with self.assert_raises(ayame.ValidationError):
            v.validate('')
        with self.assert_raises(ayame.ValidationError):
            v.validate('a@b@example.com')
        with self.assert_raises(ayame.ValidationError):
            v.validate('a@example.')

    def test_url_validator(self):
        v = validator.URLValidator()
        self.assert_false(v.validate('http://127.0.0.1'))
        self.assert_false(v.validate('http://127.0.0.1/'))
        self.assert_false(v.validate('http://127.0.0.1:80'))
        self.assert_false(v.validate('http://127.0.0.1:80/'))
        self.assert_false(v.validate('http://localhost'))
        self.assert_false(v.validate('http://localhost/'))
        self.assert_false(v.validate('http://localhost:80'))
        self.assert_false(v.validate('http://localhost:80/'))
        self.assert_false(v.validate('http://example.com'))
        self.assert_false(v.validate('http://example.com/'))
        self.assert_false(v.validate('http://example.com:80'))
        self.assert_false(v.validate('http://example.com:80/'))

        self.assert_false(v.validate('http://user@example.com/'))
        self.assert_false(v.validate('http://user:password@example.com/'))
        self.assert_false(v.validate('http://example.com/?query'))
        self.assert_false(v.validate('http://example.com/#fragment'))
        self.assert_false(v.validate('http://example.com/?query#fragment'))
        self.assert_false(v.validate('http://example.com/segment/?query'))
        self.assert_false(v.validate('http://example.com/segment/#fragment'))
        self.assert_false(
            v.validate('http://example.com/segment/?query#fragment'))

        with self.assert_raises(ayame.ValidationError):
            v.validate(None)
        with self.assert_raises(ayame.ValidationError):
            v.validate('')
        with self.assert_raises(ayame.ValidationError):
            v.validate('mailto:a@example.com')
        with self.assert_raises(ayame.ValidationError):
            v.validate('http://user`@example.com')

    def test_range_validator(self):
        v = validator.RangeValidator()
        v.min = None
        v.max = None
        self.assert_false(v.validate(None))
        self.assert_false(v.validate(''))
        self.assert_false(v.validate(0))

    def test_range_validator_str(self):
        v = validator.RangeValidator()
        v.min = 'a'
        v.max = None
        self.assert_false(v.validate('a'))
        with self.assert_raises(ayame.ValidationError):
            v.validate('0')

        v.max = 'f'
        self.assert_false(v.validate('f'))
        with self.assert_raises(ayame.ValidationError):
            v.validate('g')

    def test_range_validator_int(self):
        v = validator.RangeValidator()
        v.min = 0
        v.max = None
        self.assert_false(v.validate(0))
        with self.assert_raises(ayame.ValidationError):
            v.validate(-1)

        v.max = 9
        self.assert_false(v.validate(9))
        with self.assert_raises(ayame.ValidationError):
            v.validate(10)

        with self.assert_raises(ayame.ValidationError):
            v.validate(None)
        with self.assert_raises(ayame.ValidationError):
            v.validate('')
        with self.assert_raises(ayame.ValidationError):
            v.validate(0.0)

    def test_range_validator_float(self):
        v = validator.RangeValidator()
        v.min = 0.0
        v.max = None
        self.assert_false(v.validate(0.0))
        with self.assert_raises(ayame.ValidationError):
            v.validate(-0.1)

    def test_string_validator(self):
        v = validator.StringValidator()
        self.assert_false(v.validate(''))

        with self.assert_raises(ayame.ValidationError):
            v.validate(None)
        with self.assert_raises(ayame.ValidationError):
            v.validate(0)

        v.min = 4
        v.max = 4
        self.assert_false(v.validate('.com'))
        with self.assert_raises(ayame.ValidationError):
            v.validate('')
        with self.assert_raises(ayame.ValidationError):
            v.validate('.info')

    def test_string_validator_maxlength(self):
        root = markup.Element(validator._INPUT,
                              attrib={validator._TYPE: 'text'})
        mc = ayame.MarkupContainer('a')
        v = validator.StringValidator()
        mc.add(v)

        root = mc.render(root)
        self.assert_equal(root.attrib, {validator._TYPE: 'text'})

        v.max = 3
        root = mc.render(root)
        self.assert_equal(root.attrib, {validator._TYPE: 'text',
                                        validator._MAXLENGTH: '3'})
