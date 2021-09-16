#
# test_validator
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import ayame
from ayame import markup, validator
from base import AyameTestCase


class ValidatorTestCase(AyameTestCase):

    def test_validation_error(self):
        e = ayame.ValidationError()
        self.assertEqual(repr(e), 'ValidationError(keys=[], vars=[])')
        self.assertEqual(str(e), '')
        e.component = True
        self.assertEqual(str(e), '')

        e = ayame.ValidationError('a')
        self.assertEqual(repr(e), "ValidationError('a', keys=[], vars=[])")
        self.assertEqual(str(e), 'a')
        e.component = True
        self.assertEqual(str(e), 'a')
        e = ayame.ValidationError('a', 'b')
        self.assertEqual(repr(e), "ValidationError('a', 'b', keys=[], vars=[])")
        self.assertEqual(str(e), 'a')
        e.component = True
        self.assertEqual(str(e), 'a')

        e = ayame.ValidationError(0)
        self.assertEqual(repr(e), 'ValidationError(0, keys=[], vars=[])')
        self.assertEqual(str(e), '0')
        e.component = True
        self.assertEqual(str(e), '0')
        e = ayame.ValidationError(0, 1)
        self.assertEqual(repr(e), 'ValidationError(0, 1, keys=[], vars=[])')
        self.assertEqual(str(e), '0')
        e.component = True
        self.assertEqual(str(e), '0')

    def test_validator(self):
        class Validator(validator.Validator):
            def validate(self, object):
                return super().validate(object)

        with self.assertRaises(TypeError):
            validator.Validator()

        v = Validator()
        self.assertFalse(v.validate(None))

    def test_email_validator(self):
        v = validator.EmailValidator()
        self.assertFalse(v.validate('a@example.com'))
        self.assertFalse(v.validate('a@localhost'))

        for o in (
            None,
            '',
            'a@b@example.com',
            'a@example.',
        ):
            with self.subTest(object=o):
                with self.assertRaises(ayame.ValidationError) as cm:
                    v.validate(o)
                e = cm.exception
                self.assertEqual(str(e), '')
                self.assertEqual(e.keys, ['EmailValidator'])
                self.assertEqual(e.vars, {'pattern': v.regex.pattern})

    def test_url_validator(self):
        v = validator.URLValidator()
        for host in ('127.0.0.1', 'localhost', 'example.com'):
            for port in ('', ':80'):
                for s in ('', '/'):
                    o = f'http://{host}{port}{s}'
                    with self.subTest(object=o):
                        self.assertFalse(v.validate(o))

        self.assertFalse(v.validate('http://user@example.com/'))
        self.assertFalse(v.validate('http://user:password@example.com/'))
        self.assertFalse(v.validate('http://example.com/?query'))
        self.assertFalse(v.validate('http://example.com/#fragment'))
        self.assertFalse(v.validate('http://example.com/?query#fragment'))
        self.assertFalse(v.validate('http://example.com/segment/?query'))
        self.assertFalse(v.validate('http://example.com/segment/#fragment'))
        self.assertFalse(v.validate('http://example.com/segment/?query#fragment'))

        for o in (
            None,
            '',
            'mailto:a@example.com',
            'http://user`@example.com',
        ):
            with self.subTest(object=o):
                with self.assertRaises(ayame.ValidationError) as cm:
                    v.validate(o)
                e = cm.exception
                self.assertEqual(str(e), '')
                self.assertEqual(e.keys, ['URLValidator'])
                self.assertEqual(e.vars, {'pattern': v.regex.pattern})

    def test_range_validator(self):
        v = validator.RangeValidator()
        v.min = v.max = None
        self.assertFalse(v.validate(None))
        self.assertFalse(v.validate(''))
        self.assertFalse(v.validate(0))

        for min, max, o in (
            (0, 0, None),
            (0, 0, 'a'),
            (0, 0, 0.0),
            ('a', 'a', None),
            ('a', 'a', 0),
            ('a', 'a', 0.0),
            (0.0, 0.0, None),
            (0.0, 0.0, 0),
            (0.0, 0.0, 'a'),
        ):
            with self.subTest(min=min, max=max, object=o):
                v.min = min
                v.max = max
                with self.assertRaises(ayame.ValidationError) as cm:
                    v.validate(o)
                e = cm.exception
                self.assertEqual(str(e), '')
                self.assertEqual(e.keys, ['RangeValidator.type'])
                self.assertEqual(e.vars, {})

        v.min = 0
        v.max = None
        self.assertFalse(v.validate(0))
        with self.assertRaises(ayame.ValidationError) as cm:
            v.validate(-1)
        e = cm.exception
        self.assertEqual(str(e), '')
        self.assertEqual(e.keys, ['RangeValidator.minimum'])
        self.assertEqual(e.vars, {'min': 0})

        v.min = None
        v.max = 9
        self.assertFalse(v.validate(9))
        with self.assertRaises(ayame.ValidationError) as cm:
            v.validate(10)
        e = cm.exception
        self.assertEqual(str(e), '')
        self.assertEqual(e.keys, ['RangeValidator.maximum'])
        self.assertEqual(e.vars, {'max': 9})

        v.min = 0
        v.max = 9
        self.assertFalse(v.validate(0))
        with self.assertRaises(ayame.ValidationError) as cm:
            v.validate(-1)
        e = cm.exception
        self.assertEqual(str(e), '')
        self.assertEqual(e.keys, ['RangeValidator.range'])
        self.assertEqual(e.vars, {
            'min': 0,
            'max': 9,
        })

        v.min = v.max = 9
        self.assertFalse(v.validate(9))
        with self.assertRaises(ayame.ValidationError) as cm:
            v.validate(10)
        e = cm.exception
        self.assertEqual(str(e), '')
        self.assertEqual(e.keys, ['RangeValidator.exact'])
        self.assertEqual(e.vars, {'exact': 9})

    def test_string_validator(self):
        v = validator.StringValidator()
        v.min = v.max = None
        self.assertFalse(v.validate(''))

        for min, max, o in (
            (None, None, 0),
            (0.0, None, ''),
            (None, 0.0, ''),
        ):
            with self.subTest(min=min, max=max, object=o):
                v.min = min
                v.max = max
                with self.assertRaises(ayame.ValidationError) as cm:
                    v.validate(o)
                e = cm.exception
                self.assertEqual(str(e), '')
                self.assertEqual(e.keys, ['StringValidator.type'])
                self.assertEqual(e.vars, {})

        v.min = 4
        v.max = None
        self.assertFalse(v.validate('.com'))
        with self.assertRaises(ayame.ValidationError) as cm:
            v.validate('.jp')
        e = cm.exception
        self.assertEqual(str(e), '')
        self.assertEqual(e.keys, ['StringValidator.minimum'])
        self.assertEqual(e.vars, {'min': 4})

        v.min = None
        v.max = 4
        self.assertFalse(v.validate('.com'))
        with self.assertRaises(ayame.ValidationError) as cm:
            v.validate('.info')
        e = cm.exception
        self.assertEqual(str(e), '')
        self.assertEqual(e.keys, ['StringValidator.maximum'])
        self.assertEqual(e.vars, {'max': 4})

        v.min = 4
        v.max = 5
        self.assertFalse(v.validate('.com'))
        with self.assertRaises(ayame.ValidationError) as cm:
            v.validate('.jp')
        e = cm.exception
        self.assertEqual(str(e), '')
        self.assertEqual(e.keys, ['StringValidator.range'])
        self.assertEqual(e.vars, {
            'min': 4,
            'max': 5,
        })

        v.min = v.max = 4
        self.assertFalse(v.validate('.com'))
        with self.assertRaises(ayame.ValidationError) as cm:
            v.validate('.info')
        e = cm.exception
        self.assertEqual(str(e), '')
        self.assertEqual(e.keys, ['StringValidator.exact'])
        self.assertEqual(e.vars, {'exact': 4})

    def test_string_validator_maxlength(self):
        root = markup.Element(validator._INPUT,
                              attrib={validator._TYPE: 'text'})
        mc = ayame.MarkupContainer('a')
        v = validator.StringValidator()
        mc.add(v)

        root = mc.render(root)
        self.assertEqual(root.attrib, {validator._TYPE: 'text'})

        v.max = 3
        root = mc.render(root)
        self.assertEqual(root.attrib, {
            validator._TYPE: 'text',
            validator._MAXLENGTH: '3',
        })
