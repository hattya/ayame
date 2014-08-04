#
# test_validator
#
#   Copyright (c) 2011-2014 Akinori Hattori <hattya@gmail.com>
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
from ayame import _compat as five
from ayame import markup, validator
from base import AyameTestCase


class ValidatorTestCase(AyameTestCase):

    def test_validation_error(self):
        e = ayame.ValidationError()
        self.assert_equal(repr(e), 'ValidationError(keys=[], vars=[])')
        self.assert_equal(str(e), '')
        e.component = True
        self.assert_equal(str(e), '')

        e = ayame.ValidationError('a')
        self.assert_equal(repr(e), "ValidationError('a', keys=[], vars=[])")
        self.assert_equal(str(e), 'a')
        e.component = True
        self.assert_equal(str(e), 'a')
        e = ayame.ValidationError('a', 'b')
        self.assert_equal(repr(e), "ValidationError('a', 'b', keys=[], vars=[])")
        self.assert_equal(str(e), 'a')
        e.component = True
        self.assert_equal(str(e), 'a')

        e = ayame.ValidationError(0)
        self.assert_equal(repr(e), 'ValidationError(0, keys=[], vars=[])')
        self.assert_equal(str(e), '0')
        e.component = True
        self.assert_equal(str(e), '0')
        e = ayame.ValidationError(0, 1)
        self.assert_equal(repr(e), 'ValidationError(0, 1, keys=[], vars=[])')
        self.assert_equal(str(e), '0')
        e.component = True
        self.assert_equal(str(e), '0')

    def test_validator(self):
        class Validator(validator.Validator):
            def validate(self, object):
                return super(Validator, self).validate(object)

        with self.assert_raises(TypeError):
            validator.Validator()

        v = Validator()
        self.assert_false(v.validate(None))

    def test_email_validator(self):
        v = validator.EmailValidator()
        self.assert_false(v.validate('a@example.com'))
        self.assert_false(v.validate('a@localhost'))

        def assert_error(o):
            with self.assert_raises(ayame.ValidationError) as cm:
                v.validate(o)
            e = cm.exception
            self.assert_equal(five.str(e), '')
            self.assert_equal(e.keys, ['EmailValidator'])
            self.assert_equal(e.vars, {'pattern': v.regex.pattern})

        assert_error(None)
        assert_error('')
        assert_error('a@b@example.com')
        assert_error('a@example.')

    def test_url_validator(self):
        v = validator.URLValidator()
        for host in ('127.0.0.1', 'localhost', 'example.com'):
            for port in ('', ':80'):
                for s in ('', '/'):
                    self.assert_false(v.validate('http://' + host + port + s))

        self.assert_false(v.validate('http://user@example.com/'))
        self.assert_false(v.validate('http://user:password@example.com/'))
        self.assert_false(v.validate('http://example.com/?query'))
        self.assert_false(v.validate('http://example.com/#fragment'))
        self.assert_false(v.validate('http://example.com/?query#fragment'))
        self.assert_false(v.validate('http://example.com/segment/?query'))
        self.assert_false(v.validate('http://example.com/segment/#fragment'))
        self.assert_false(v.validate('http://example.com/segment/?query#fragment'))

        def assert_error(o):
            with self.assert_raises(ayame.ValidationError) as cm:
                v.validate(o)
            e = cm.exception
            self.assert_equal(five.str(e), '')
            self.assert_equal(e.keys, ['URLValidator'])
            self.assert_equal(e.vars, {'pattern': v.regex.pattern})

        assert_error(None)
        assert_error('')
        assert_error('mailto:a@example.com')
        assert_error('http://user`@example.com')

    def test_range_validator(self):
        v = validator.RangeValidator()
        v.min = v.max = None
        self.assert_false(v.validate(None))
        self.assert_false(v.validate(''))
        self.assert_false(v.validate(0))

        def assert_type_error(o):
            with self.assert_raises(ayame.ValidationError) as cm:
                v.validate(o)
            e = cm.exception
            self.assert_equal(five.str(e), '')
            self.assert_equal(e.keys, ['RangeValidator.type'])
            self.assert_equal(e.vars, {})

        v.min = v.max = 0
        assert_type_error(None)
        assert_type_error('a')
        assert_type_error(0.0)
        v.min = v.max = 'a'
        assert_type_error(None)
        assert_type_error(0)
        assert_type_error(0.0)
        v.min = v.max = 0.0
        assert_type_error(None)
        assert_type_error(0)
        assert_type_error('a')

        v.min = 0
        v.max = None
        self.assert_false(v.validate(0))
        with self.assert_raises(ayame.ValidationError) as cm:
            v.validate(-1)
        e = cm.exception
        self.assert_equal(five.str(e), '')
        self.assert_equal(e.keys, ['RangeValidator.minimum'])
        self.assert_equal(e.vars, {'min': 0})

        v.min = None
        v.max = 9
        self.assert_false(v.validate(9))
        with self.assert_raises(ayame.ValidationError) as cm:
            v.validate(10)
        e = cm.exception
        self.assert_equal(five.str(e), '')
        self.assert_equal(e.keys, ['RangeValidator.maximum'])
        self.assert_equal(e.vars, {'max': 9})

        v.min = 0
        v.max = 9
        self.assert_false(v.validate(0))
        with self.assert_raises(ayame.ValidationError) as cm:
            v.validate(-1)
        e = cm.exception
        self.assert_equal(five.str(e), '')
        self.assert_equal(e.keys, ['RangeValidator.range'])
        self.assert_equal(e.vars, {'min': 0,
                                   'max': 9})

        v.min = v.max = 9
        self.assert_false(v.validate(9))
        with self.assert_raises(ayame.ValidationError) as cm:
            v.validate(10)
        e = cm.exception
        self.assert_equal(five.str(e), '')
        self.assert_equal(e.keys, ['RangeValidator.exact'])
        self.assert_equal(e.vars, {'exact': 9})

    def test_string_validator(self):
        v = validator.StringValidator()
        v.min = v.max = None
        self.assert_false(v.validate(''))

        def assert_type_error(min, max, o):
            v.min = min
            v.max = max
            with self.assert_raises(ayame.ValidationError) as cm:
                v.validate(o)
            e = cm.exception
            self.assert_equal(five.str(e), '')
            self.assert_equal(e.keys, ['StringValidator.type'])
            self.assert_equal(e.vars, {})

        assert_type_error(None, None, 0)
        assert_type_error(0.0, None, '')
        assert_type_error(None, 0.0, '')

        v.min = 4
        v.max = None
        self.assert_false(v.validate('.com'))
        with self.assert_raises(ayame.ValidationError) as cm:
            v.validate('.jp')
        e = cm.exception
        self.assert_equal(five.str(e), '')
        self.assert_equal(e.keys, ['StringValidator.minimum'])
        self.assert_equal(e.vars, {'min': 4})

        v.min = None
        v.max = 4
        self.assert_false(v.validate('.com'))
        with self.assert_raises(ayame.ValidationError) as cm:
            v.validate('.info')
        e = cm.exception
        self.assert_equal(five.str(e), '')
        self.assert_equal(e.keys, ['StringValidator.maximum'])
        self.assert_equal(e.vars, {'max': 4})

        v.min = 4
        v.max = 5
        self.assert_false(v.validate('.com'))
        with self.assert_raises(ayame.ValidationError) as cm:
            v.validate('.jp')
        e = cm.exception
        self.assert_equal(five.str(e), '')
        self.assert_equal(e.keys, ['StringValidator.range'])
        self.assert_equal(e.vars, {'min': 4,
                                   'max': 5})

        v.min = v.max = 4
        self.assert_false(v.validate('.com'))
        with self.assert_raises(ayame.ValidationError) as cm:
            v.validate('.info')
        e = cm.exception
        self.assert_equal(five.str(e), '')
        self.assert_equal(e.keys, ['StringValidator.exact'])
        self.assert_equal(e.vars, {'exact': 4})

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
