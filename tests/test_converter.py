#
# test_converter
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
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
        registry = converter.ConverterRegistry()
        self.assert_is(registry.converter_for(sys), registry.get(object))
        self.assert_is(registry.converter_for(self), registry.get(object))
        self.assert_is(registry.converter_for(None), registry.get(object))
        self.assert_is(registry.converter_for(0), registry.get(int))
        self.assert_is(registry.converter_for(True), registry.get(bool))

    def test_registry_for_class(self):
        # class
        class O:
            pass

        class N(object):
            pass

        # single inheritance
        class OO(O):
            pass

        class NN(N):
            pass

        # multiple inheritance
        class ON(O, N):
            pass

        class NO(N, O):
            pass

        # converters
        class OConverter:
            @property
            def type(self):
                return O

            def to_python(self, value):
                return str(value)

        class NConverter:
            @property
            def type(self):
                return N

            def to_python(self, value):
                return str(value)

        registry = converter.ConverterRegistry()
        oc = OConverter()
        registry.add(oc)
        nc = NConverter()
        registry.add(nc)
        for v in (
            O, O(),
            OO, OO(),
            ON, ON(),
        ):
            self.assert_is(registry.converter_for(v), oc)
        for v in (
            N, N(),
            NN, NN(),
            NN, NN(),
        ):
            self.assert_is(registry.converter_for(v), nc)

        registry.remove(O)
        for v in (
            O, O(),
            OO, OO(),
        ):
            self.assert_is(registry.converter_for(v), registry.get(object))
        for v in (
            N, N(),
            NN, NN(),
            ON, ON(),
            NO, NO(),
        ):
            self.assert_is(registry.converter_for(v), nc)

        registry.remove(N)
        for v in (
            O, O(),
            N, N(),
            OO, OO(),
            NN, NN(),
            ON, ON(),
            NO, NO(),
        ):
            self.assert_is(registry.converter_for(v), registry.get(object))

    def test_registry_no_type(self):
        class Converter(converter.Converter):
            @property
            def type(self):
                pass

            def to_python(self, value):
                pass

        registry = converter.ConverterRegistry()
        c = Converter()
        registry.add(c)
        self.assert_is_not(registry.converter_for(None), c)
        self.assert_is(registry.converter_for(None), registry.get(object))

        registry.remove(None)
        self.assert_is(registry.converter_for(None), registry.get(object))

    def test_converter(self):
        class Converter(converter.Converter):
            @property
            def type(self):
                return super().type

            def to_python(self, value):
                return super().to_python(value)

        with self.assert_raises(TypeError):
            converter.Converter()

        c = Converter()
        self.assert_is_none(c.type)
        self.assert_is_none(c.to_python(None))
        self.assert_equal(c.to_string(None), 'None')

    def test_conversion_error(self):
        class Converter(converter.Converter):
            @property
            def type(self):
                return (str,)

            def to_python(self, value):
                pass

        with self.assert_raises_regex(ayame.ConversionError, r" .* 'str'.* but "):
            Converter().to_string(0)

        class Converter(converter.Converter):
            @property
            def type(self):
                return (int, float)

            def to_python(self, value):
                pass

        with self.assert_raises_regex(ayame.ConversionError, r" .* 'int'.* or .* 'float'.* but "):
            Converter().to_string('')

    def test_object(self):
        class O:
            pass

        class N(object):
            pass

        o = O()
        n = N()

        c = converter._ObjectConverter()
        self.assert_is(c.type, object)
        self.assert_is_instance(o, c.type)
        self.assert_is_instance(n, c.type)

        self.assert_is_none(c.to_python(None))
        self.assert_is(c.to_python(o), o)
        self.assert_is(c.to_python(n), n)

        self.assert_equal(c.to_string(None), 'None')
        self.assert_equal(c.to_string(o), str(o))
        self.assert_equal(c.to_string(n), str(n))

    def test_boolean(self):
        c = converter.BooleanConverter()
        self.assert_is(c.type, bool)
        self.assert_is_instance(True, c.type)
        self.assert_is_instance(False, c.type)

        for v in (None, 0, '', 'false', 'off', 'no', 'n'):
            self.assert_is(c.to_python(v), False)
        for v in (object(), 1, ' ', 'true', 'on', 'yes', 'y'):
            self.assert_is(c.to_python(v), True)

        self.assert_equal(c.to_string(False), 'False')
        for v in (None, 0, ''):
            with self.assert_raises(ayame.ConversionError):
                c.to_string(v)
        self.assert_equal(c.to_string(True), 'True')
        for v in (object(), 1, ' '):
            with self.assert_raises(ayame.ConversionError):
                c.to_string(v)

    def test_float(self):
        pi = '3.141592653589793'[:sys.float_info.dig + 1]
        inf = float('inf')
        nan = float('nan')

        c = converter.FloatConverter()
        self.assert_is(c.type, float)
        self.assert_is_instance(3.14, c.type)

        self.assert_equal(c.to_python('-inf'), -inf)
        self.assert_equal(c.to_python('-' + pi), -float(pi))
        self.assert_equal(c.to_python('-0'), 0.0)
        self.assert_equal(c.to_python(None), 0.0)
        self.assert_equal(c.to_python('0'), 0.0)
        self.assert_equal(c.to_python(pi), float(pi))
        self.assert_equal(c.to_python('inf'), inf)
        self.assert_is_instance(c.to_python('nan'), float)
        self.assert_not_equal(c.to_python('nan'), nan)
        for v in ('', object()):
            with self.assert_raises(ayame.ConversionError):
                c.to_python(v)

        self.assert_equal(c.to_string(-inf), '-inf')
        self.assert_equal(c.to_string(-float(pi)), '-' + pi)
        self.assert_equal(c.to_string(-0.0), '-0.0')
        self.assert_equal(c.to_string(0.0), '0.0')
        self.assert_equal(c.to_string(float(pi)), pi)
        self.assert_equal(c.to_string(inf), 'inf')
        self.assert_equal(c.to_string(nan), 'nan')
        for v in (None, '', object()):
            with self.assert_raises(ayame.ConversionError):
                c.to_string(v)

    def test_int(self):
        c = converter.IntegerConverter()
        self.assert_equal(c.type, int)
        self.assert_is_instance(int(0), c.type)

        self.assert_equal(c.to_python('-8192'), -8192)
        self.assert_equal(c.to_python('-0'), 0)
        self.assert_equal(c.to_python(None), 0)
        self.assert_equal(c.to_python('0'), 0)
        self.assert_equal(c.to_python('8192'), 8192)
        for v in ('', object()):
            with self.assert_raises(ayame.ConversionError):
                c.to_python(v)

        self.assert_equal(c.to_string(int(-8192)), '-8192')
        self.assert_equal(c.to_string(int(-0)), '0')
        self.assert_equal(c.to_string(int(0)), '0')
        self.assert_equal(c.to_string(int(8192)), '8192')
        for v in (None, '', object()):
            with self.assert_raises(ayame.ConversionError):
                c.to_string(v)

    def test_date(self):
        c = converter.DateConverter()
        self.assert_is(c.type, datetime.date)
        self.assert_is_instance(datetime.date.today(), c.type)

        self.assert_equal(c.to_python('2011-01-01'), datetime.date(2011, 1, 1))
        for v in ('1-1-1', None, '', object()):
            with self.assert_raises(ayame.ConversionError):
                c.to_python(v)

        self.assert_equal(c.to_string(datetime.date(2011, 1, 1)), '2011-01-01')
        for v in (None, '', object()):
            with self.assert_raises(ayame.ConversionError):
                c.to_string(v)

    def test_time(self):
        c = converter.TimeConverter()
        self.assert_is(c.type, datetime.time)
        self.assert_is_instance(datetime.datetime.now().time(), c.type)

        self.assert_equal(c.to_python('00:00:00'), datetime.time(0, 0, 0))
        for v in ('24:00:00', None, '', object()):
            with self.assert_raises(ayame.ConversionError):
                c.to_python(v)

        self.assert_equal(c.to_string(datetime.time(0, 0, 0)), '00:00:00')
        for v in (None, '', object()):
            with self.assert_raises(ayame.ConversionError):
                c.to_string(v)

    def test_datetime(self):
        c = converter.DateTimeConverter()
        self.assert_is(c.type, datetime.datetime)
        self.assert_is_instance(datetime.datetime.now(), c.type)

        for v in (
            '2010-12-31T19:00:00-05:00',
            '2011-01-01T00:00:00Z',
            '2011-01-01 09:00:00+09:00',
        ):
            self.assert_equal(c.to_python(v), datetime.datetime(2011, 1, 1, tzinfo=datetime.timezone.utc))
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
            with self.assert_raises(ayame.ConversionError):
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
            def utcoffset(self, dt):
                return self.offset

            def tzname(self, dt):
                return self.__class__.__name__

            def dst(self, dt):
                return self.offset

        class UTC(TZInfo):
            offset = datetime.timedelta(0)

        class JST(TZInfo):
            offset = datetime.timedelta(hours=9)

        class Invalid(TZInfo):
            offset = 0

        self.assert_equal(c.to_string(datetime.datetime(2011, 1, 1)),
                          '2011-01-01 00:00:00Z')
        self.assert_equal(c.to_string(datetime.datetime(2011, 1, 1, tzinfo=Eastern())),
                          '2011-01-01 00:00:00-05:00')
        self.assert_equal(c.to_string(datetime.datetime(2011, 1, 1, tzinfo=UTC())),
                          '2011-01-01 00:00:00Z')
        self.assert_equal(c.to_string(datetime.datetime(2011, 1, 1, tzinfo=JST())),
                          '2011-01-01 00:00:00+09:00')
        with self.assert_raises(ayame.ConversionError):
            c.to_string(datetime.datetime(2011, 1, 1, tzinfo=Invalid()))

        for v in (None, '', object()):
            with self.assert_raises(ayame.ConversionError):
                c.to_string(v)
