#
# test_validator
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import unittest.mock

import ayame
from ayame import markup, validator
from base import AyameTestCase


class ValidatorTestCase(AyameTestCase):

    @unittest.mock.patch.object(ayame.Component, 'tr')
    def test_validation_error(self, tr):
        e = ayame.ValidationError()
        self.assertEqual(repr(e), 'ValidationError(keys=[], vars=[])')
        self.assertEqual(str(e), '')

        e = ayame.ValidationError('a')
        self.assertEqual(repr(e), "ValidationError('a', keys=[], vars=[])")
        self.assertEqual(str(e), 'a')
        e = ayame.ValidationError('a', 'b')
        self.assertEqual(repr(e), "ValidationError('a', 'b', keys=[], vars=[])")
        self.assertEqual(str(e), 'a')

        e = ayame.ValidationError(0)
        self.assertEqual(repr(e), 'ValidationError(0, keys=[], vars=[])')
        self.assertEqual(str(e), '0')
        e = ayame.ValidationError(0, 1)
        self.assertEqual(repr(e), 'ValidationError(0, 1, keys=[], vars=[])')
        self.assertEqual(str(e), '0')

        class Validator(validator.Validator):
            def validate(self, _):
                pass

        c = ayame.Component(__name__)

        tr.return_value = None
        e = ayame.ValidationError('args', component=c, validator=Validator(), variation='variation')
        self.assertEqual(str(e), 'args')

        tr.side_effect = lambda v: v
        e = ayame.ValidationError('args', component=c, validator=Validator(), variation='variation')
        self.assertEqual(str(e), 'Validator.variation')

    def test_validator(self):
        class Validator(validator.Validator):
            def validate(self, object):
                super().validate(object)

        with self.assertRaises(TypeError):
            validator.Validator()

        v = Validator()
        with self.assertRaises(NotImplementedError):
            v.validate(None)

    def test_email_validator(self):
        v = validator.EmailValidator()
        v.validate('a@example.com')
        v.validate('a@localhost')

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
                        v.validate(o)

        v.validate('http://user@example.com/')
        v.validate('http://user:password@example.com/')
        v.validate('http://example.com/?query')
        v.validate('http://example.com/#fragment')
        v.validate('http://example.com/?query#fragment')
        v.validate('http://example.com/segment/?query')
        v.validate('http://example.com/segment/#fragment')
        v.validate('http://example.com/segment/?query#fragment')

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
        v.validate(None)
        v.validate('')
        v.validate(0)

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
        v.validate(0)
        with self.assertRaises(ayame.ValidationError) as cm:
            v.validate(-1)
        e = cm.exception
        self.assertEqual(str(e), '')
        self.assertEqual(e.keys, ['RangeValidator.minimum'])
        self.assertEqual(e.vars, {'min': 0})

        v.min = None
        v.max = 9
        v.validate(9)
        with self.assertRaises(ayame.ValidationError) as cm:
            v.validate(10)
        e = cm.exception
        self.assertEqual(str(e), '')
        self.assertEqual(e.keys, ['RangeValidator.maximum'])
        self.assertEqual(e.vars, {'max': 9})

        v.min = 0
        v.max = 9
        v.validate(0)
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
        v.validate(9)
        with self.assertRaises(ayame.ValidationError) as cm:
            v.validate(10)
        e = cm.exception
        self.assertEqual(str(e), '')
        self.assertEqual(e.keys, ['RangeValidator.exact'])
        self.assertEqual(e.vars, {'exact': 9})

    def test_string_validator(self):
        v = validator.StringValidator()
        v.min = v.max = None
        v.validate('')

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
        v.validate('.com')
        with self.assertRaises(ayame.ValidationError) as cm:
            v.validate('.jp')
        e = cm.exception
        self.assertEqual(str(e), '')
        self.assertEqual(e.keys, ['StringValidator.minimum'])
        self.assertEqual(e.vars, {'min': 4})

        v.min = None
        v.max = 4
        v.validate('.com')
        with self.assertRaises(ayame.ValidationError) as cm:
            v.validate('.info')
        e = cm.exception
        self.assertEqual(str(e), '')
        self.assertEqual(e.keys, ['StringValidator.maximum'])
        self.assertEqual(e.vars, {'max': 4})

        v.min = 4
        v.max = 5
        v.validate('.com')
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
        v.validate('.com')
        with self.assertRaises(ayame.ValidationError) as cm:
            v.validate('.info')
        e = cm.exception
        self.assertEqual(str(e), '')
        self.assertEqual(e.keys, ['StringValidator.exact'])
        self.assertEqual(e.vars, {'exact': 4})

    def test_string_validator_maxlength(self):
        el = markup.Element(validator._INPUT,
                            {
                                validator._TYPE: 'text',
                            })
        mc = ayame.MarkupContainer('a')
        v = validator.StringValidator()
        mc.add(v)

        el = mc.render(el)
        self.assertEqual(el.attrib, {validator._TYPE: 'text'})

        v.max = 3
        el = mc.render(el)
        self.assertEqual(el.attrib, {
            validator._TYPE: 'text',
            validator._MAXLENGTH: '3',
        })
