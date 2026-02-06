#
# test_converter
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import datetime
import sys

import ayame
from ayame import converter
from base import AyameTestCase


class ConverterTestCase(AyameTestCase):

    def test_registry_for_builtin(self):
        r = converter.ConverterRegistry()
        self.assertIs(r.converter_for(sys), r.get(object))
        self.assertIs(r.converter_for(self), r.get(object))
        self.assertIs(r.converter_for(None), r.get(object))
        self.assertIs(r.converter_for(0), r.get(int))
        self.assertIs(r.converter_for(True), r.get(bool))

    def test_registry_for_no_type(self):
        class Converter(converter.Converter):
            @property
            def type(self):
                pass

            def to_python(self, _):
                pass

        r = converter.ConverterRegistry()
        c = Converter()
        r.add(c)
        self.assertIsNot(r.converter_for(None), c)
        self.assertIs(r.converter_for(None), r.get(object))

        r.remove(type(None))
        self.assertIs(r.converter_for(None), r.get(object))

    def test_registry_for_single_type(self):
        # class
        class A:
            pass

        class Z:
            pass

        # single inheritance
        class AA(A):
            pass

        class ZZ(Z):
            pass

        # multiple inheritance
        class AZ(A, Z):
            pass

        class ZA(Z, A):
            pass

        # converters
        class AConverter(converter.Converter):
            @property
            def type(self):
                return A

            def to_python(self, _):
                pass

        class ZConverter(converter.Converter):
            @property
            def type(self):
                return Z

            def to_python(self, _):
                pass

        r = converter.ConverterRegistry()
        ac = AConverter()
        r.add(ac)
        zc = ZConverter()
        r.add(zc)
        for v in (
            A, A(),
            AA, AA(),
            AZ, AZ(),
        ):
            with self.subTest(value=v):
                self.assertIs(r.converter_for(v), ac)
        for v in (
            Z, Z(),
            ZZ, ZZ(),
            ZA, ZA(),
        ):
            with self.subTest(value=v):
                self.assertIs(r.converter_for(v), zc)

        r.remove(A)
        for v in (
            A, A(),
            AA, AA(),
        ):
            with self.subTest(value=v):
                self.assertIs(r.converter_for(v), r.get(object))
        for v in (
            Z, Z(),
            ZZ, ZZ(),
            AZ, AZ(),
            ZA, ZA(),
        ):
            with self.subTest(value=v):
                self.assertIs(r.converter_for(v), zc)

        r.remove(Z)
        for v in (
            A, A(),
            Z, Z(),
            AA, AA(),
            ZZ, ZZ(),
            AZ, AZ(),
            ZA, ZA(),
        ):
            with self.subTest(value=v):
                self.assertIs(r.converter_for(v), r.get(object))

    def test_registry_for_multiple_type(self):
        class A:
            pass

        class Z:
            pass

        class Converter(converter.Converter):
            @property
            def type(self):
                return A, Z

            def to_python(self, _):
                pass

        r = converter.ConverterRegistry()
        c = Converter()
        r.add(c)
        for v in (
            A, A(),
            Z, Z(),
        ):
            with self.subTest(value=v):
                self.assertIs(r.converter_for(v), c)

        r.remove(A)
        for v in (
            A, A(),
        ):
            with self.subTest(value=v):
                self.assertIs(r.converter_for(v), r.get(object))
        for v in (
            Z, Z(),
        ):
            with self.subTest(value=v):
                self.assertIs(r.converter_for(v), c)

        r.remove(Z)
        for v in (
            A, A(),
            Z, Z(),
        ):
            with self.subTest(value=v):
                self.assertIs(r.converter_for(v), r.get(object))

    def test_converter(self):
        class Converter(converter.Converter):
            @property
            def type(self):
                return super().type

            def to_python(self, value):
                return super().to_python(value)

        with self.assertRaises(TypeError):
            converter.Converter()

        c = Converter()
        with self.assertRaises(NotImplementedError):
            c.type
        with self.assertRaises(NotImplementedError):
            c.to_python(None)
        with self.assertRaises(NotImplementedError):
            c.to_string(None)

    def test_conversion_error(self):
        class Converter(converter.Converter):
            def __init__(self, type):
                self.__type = type

            @property
            def type(self):
                return self.__type

            def to_python(self, _):
                pass

        with self.assertRaisesRegex(ayame.ConversionError, r" .* 'str'.* but "):
            Converter(str).to_string(None)
        with self.assertRaisesRegex(ayame.ConversionError, r" .* 'str'.* but "):
            Converter((str,)).to_string(None)
        with self.assertRaisesRegex(ayame.ConversionError, r" .* 'int'.* or .* 'float'.* but "):
            Converter((int, float)).to_string(None)

    def test_object(self):
        o = object()
        c = converter._ObjectConverter()
        self.assertIs(c.type, object)
        self.assertIsInstance(o, c.type)

        self.assertIsNone(c.to_python(None))
        self.assertIs(c.to_python(o), o)

        self.assertEqual(c.to_string(None), 'None')
        self.assertEqual(c.to_string(o), str(o))

    def test_boolean(self):
        c = converter.BooleanConverter()
        self.assertIs(c.type, bool)
        self.assertIsInstance(True, c.type)
        self.assertIsInstance(False, c.type)

        for v in (object(), 1, ' ', 'true', 'on', 'yes', 'y'):
            with self.subTest(value=v):
                self.assertIs(c.to_python(v), True)
        for v in (None, 0, '', 'false', 'off', 'no', 'n'):
            with self.subTest(value=v):
                self.assertIs(c.to_python(v), False)

        self.assertEqual(c.to_string(True), 'True')
        for v in (object(), 1, ' '):
            with self.subTest(value=v):
                with self.assertRaises(ayame.ConversionError):
                    c.to_string(v)
        self.assertEqual(c.to_string(False), 'False')
        for v in (None, 0, ''):
            with self.subTest(value=v):
                with self.assertRaises(ayame.ConversionError):
                    c.to_string(v)

    def test_float(self):
        pi = '3.141592653589793'[:sys.float_info.dig+1]
        inf = float('inf')
        nan = float('nan')
        c = converter.FloatConverter()
        self.assertIs(c.type, float)
        self.assertIsInstance(3.14, c.type)

        self.assertEqual(c.to_python('-inf'), -inf)
        self.assertEqual(c.to_python(f'-{pi}'), -float(pi))
        self.assertEqual(c.to_python('-0'), 0.0)
        self.assertEqual(c.to_python(None), 0.0)
        self.assertEqual(c.to_python('0'), 0.0)
        self.assertEqual(c.to_python(pi), float(pi))
        self.assertEqual(c.to_python('inf'), inf)
        self.assertIsInstance(c.to_python('nan'), float)
        self.assertNotEqual(c.to_python('nan'), nan)
        for v in ('', object()):
            with self.subTest(value=v):
                with self.assertRaises(ayame.ConversionError):
                    c.to_python(v)

        self.assertEqual(c.to_string(-inf), '-inf')
        self.assertEqual(c.to_string(-float(pi)), f'-{pi}')
        self.assertEqual(c.to_string(-0.0), '-0.0')
        self.assertEqual(c.to_string(0.0), '0.0')
        self.assertEqual(c.to_string(float(pi)), pi)
        self.assertEqual(c.to_string(inf), 'inf')
        self.assertEqual(c.to_string(nan), 'nan')
        for v in (None, '', object()):
            with self.subTest(value=v):
                with self.assertRaises(ayame.ConversionError):
                    c.to_string(v)

    def test_int(self):
        c = converter.IntegerConverter()
        self.assertEqual(c.type, int)
        self.assertIsInstance(0, c.type)

        self.assertEqual(c.to_python('-8192'), -8192)
        self.assertEqual(c.to_python('-0'), 0)
        self.assertEqual(c.to_python(None), 0)
        self.assertEqual(c.to_python('0'), 0)
        self.assertEqual(c.to_python('8192'), 8192)
        for v in ('', object()):
            with self.subTest(value=v):
                with self.assertRaises(ayame.ConversionError):
                    c.to_python(v)

        self.assertEqual(c.to_string(-8192), '-8192')
        self.assertEqual(c.to_string(-0), '0')
        self.assertEqual(c.to_string(0), '0')
        self.assertEqual(c.to_string(8192), '8192')
        for v in (None, '', object()):
            with self.subTest(value=v):
                with self.assertRaises(ayame.ConversionError):
                    c.to_string(v)

    def test_date(self):
        c = converter.DateConverter()
        self.assertIs(c.type, datetime.date)
        self.assertIsInstance(datetime.date.today(), c.type)

        self.assertEqual(c.to_python('2011-01-01'), datetime.date(2011, 1, 1))
        for v in ('1-01-01', None, '', object()):
            with self.subTest(value=v):
                with self.assertRaises(ayame.ConversionError):
                    c.to_python(v)

        self.assertEqual(c.to_string(datetime.date(2011, 1, 1)), '2011-01-01')
        for v in (None, '', object()):
            with self.subTest(value=v):
                with self.assertRaises(ayame.ConversionError):
                    c.to_string(v)

    def test_time(self):
        c = converter.TimeConverter()
        self.assertIs(c.type, datetime.time)
        self.assertIsInstance(datetime.datetime.now().time(), c.type)

        self.assertEqual(c.to_python('00:00:00'), datetime.time(0, 0, 0))
        for v in ('24:00:00', None, '', object()):
            with self.subTest(value=v):
                with self.assertRaises(ayame.ConversionError):
                    c.to_python(v)

        self.assertEqual(c.to_string(datetime.time(0, 0, 0)), '00:00:00')
        for v in (None, '', object()):
            with self.subTest(value=v):
                with self.assertRaises(ayame.ConversionError):
                    c.to_string(v)

    def test_datetime(self):
        c = converter.DateTimeConverter()
        self.assertIs(c.type, datetime.datetime)
        self.assertIsInstance(datetime.datetime.now(), c.type)

        for v in (
            '2010-12-31T19:00:00-05:00',
            '2011-01-01T00:00:00Z',
            '2011-01-01 09:00:00+09:00',
        ):
            with self.subTest(value=v):
                self.assertEqual(c.to_python(v), datetime.datetime(2011, 1, 1, tzinfo=datetime.timezone.utc))
        for v in (
            '2011-01-01T00:00:00',
            '2011-01-01T00:00:00-0500',
            '2011-01-01T00:00:00+0900',
            '2011-01-01T00:00:00-a:a',
            '2011-01-01T00:00:00-12:01',
            '2011-01-01T00:00:00+14:01',
            '2011-01-01t00:00:00Z',
            '1-01-01T00:00:00Z',
            None,
            '',
            object(),
        ):
            with self.subTest(value=v):
                with self.assertRaises(ayame.ConversionError):
                    c.to_python(v)

        class Eastern(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(hours=-5) + self.dst(dt)

            def tzname(self, dt):
                return 'EDT' if self.dst(dt) else 'EST'

            def dst(self, dt):
                start = datetime.datetime(2011, 3, 13, 2, tzinfo=None)
                end = datetime.datetime(2011, 11, 6, 2, tzinfo=None)
                if start <= dt.replace(tzinfo=None) < end:
                    return datetime.timedelta(hours=1)
                return datetime.timedelta(0)

        class TZInfo(datetime.tzinfo):
            def utcoffset(self, _):
                return self.offset

            def tzname(self, _):
                return type(self).__name__

            def dst(self, _):
                return self.offset

        class UTC(TZInfo):
            offset = datetime.timedelta(0)

        class JST(TZInfo):
            offset = datetime.timedelta(hours=9)

        class Invalid(TZInfo):
            offset = 0

        self.assertEqual(c.to_string(datetime.datetime(2011, 1, 1)),
                         '2011-01-01 00:00:00Z')
        self.assertEqual(c.to_string(datetime.datetime(2011, 1, 1, tzinfo=Eastern())),
                         '2011-01-01 00:00:00-05:00')
        self.assertEqual(c.to_string(datetime.datetime(2011, 1, 1, tzinfo=UTC())),
                         '2011-01-01 00:00:00Z')
        self.assertEqual(c.to_string(datetime.datetime(2011, 1, 1, tzinfo=JST())),
                         '2011-01-01 00:00:00+09:00')
        with self.assertRaises(ayame.ConversionError):
            c.to_string(datetime.datetime(2011, 1, 1, tzinfo=Invalid()))

        for v in (None, '', object()):
            with self.subTest(value=v):
                with self.assertRaises(ayame.ConversionError):
                    c.to_string(v)
