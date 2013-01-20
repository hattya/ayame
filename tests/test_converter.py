#
# test_converter
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
        class O:
            pass
        class N(object):
            pass

        class OO(O):
            pass
        class NN(N):
            pass

        class ON(O, N):
            pass
        class NO(N, O):
            pass

        class OConverter(object):
            @property
            def type(self):
                return O
            def to_python(self, value):
                return unicode(value)
        class NConverter(object):
            @property
            def type(self):
                return N
            def to_python(self, value):
                return unicode(value)

        registry = converter.ConverterRegistry()
        registry.add(OConverter())
        registry.add(NConverter())
        self.assert_is(registry.converter_for(O), registry.get(O))
        self.assert_is(registry.converter_for(O()), registry.get(O))
        self.assert_is(registry.converter_for(N), registry.get(N))
        self.assert_is(registry.converter_for(N()), registry.get(N))
        self.assert_is(registry.converter_for(OO), registry.get(O))
        self.assert_is(registry.converter_for(OO()), registry.get(O))
        self.assert_is(registry.converter_for(NN), registry.get(N))
        self.assert_is(registry.converter_for(NN()), registry.get(N))
        self.assert_is(registry.converter_for(ON), registry.get(O))
        self.assert_is(registry.converter_for(ON()), registry.get(O))
        self.assert_is(registry.converter_for(NO), registry.get(N))
        self.assert_is(registry.converter_for(NO()), registry.get(N))

        registry.remove(O)
        self.assert_is(registry.converter_for(O), registry.get(object))
        self.assert_is(registry.converter_for(O()), registry.get(object))
        self.assert_is(registry.converter_for(N), registry.get(N))
        self.assert_is(registry.converter_for(N()), registry.get(N))
        self.assert_is(registry.converter_for(OO), registry.get(object))
        self.assert_is(registry.converter_for(OO()), registry.get(object))
        self.assert_is(registry.converter_for(NN), registry.get(N))
        self.assert_is(registry.converter_for(NN()), registry.get(N))
        self.assert_is(registry.converter_for(ON), registry.get(N))
        self.assert_is(registry.converter_for(ON()), registry.get(N))
        self.assert_is(registry.converter_for(NO), registry.get(N))
        self.assert_is(registry.converter_for(NO()), registry.get(N))

        registry.remove(N)
        self.assert_is(registry.converter_for(O), registry.get(object))
        self.assert_is(registry.converter_for(O()), registry.get(object))
        self.assert_is(registry.converter_for(N), registry.get(object))
        self.assert_is(registry.converter_for(N()), registry.get(object))
        self.assert_is(registry.converter_for(OO), registry.get(object))
        self.assert_is(registry.converter_for(OO()), registry.get(object))
        self.assert_is(registry.converter_for(NN), registry.get(object))
        self.assert_is(registry.converter_for(NN()), registry.get(object))
        self.assert_is(registry.converter_for(ON), registry.get(object))
        self.assert_is(registry.converter_for(ON()), registry.get(object))
        self.assert_is(registry.converter_for(NO), registry.get(object))
        self.assert_is(registry.converter_for(NO()), registry.get(object))

    def test_converter(self):
        class Converter(converter.Converter):
            @property
            def type(self):
                return super(Converter, self).type
            def to_python(self, value):
                return super(Converter, self).to_python(value)

        c = Converter()
        self.assert_is_none(c.type)
        self.assert_is_none(c.to_python(None))
        self.assert_equal(c.to_string(None), 'None')

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
        self.assert_equal(c.to_string(o), unicode(o))
        self.assert_equal(c.to_string(n), unicode(n))

    def test_boolean(self):
        c = converter.BooleanConverter()
        self.assert_is(c.type, bool)
        self.assert_is_instance(True, c.type)
        self.assert_is_instance(False, c.type)

        self.assert_equal(c.to_python(None), False)
        self.assert_equal(c.to_python(0), False)
        self.assert_equal(c.to_python(''), False)
        self.assert_equal(c.to_python('false'), False)
        self.assert_equal(c.to_python('off'), False)
        self.assert_equal(c.to_python('no'), False)
        self.assert_equal(c.to_python('n'), False)
        self.assert_equal(c.to_python(object()), True)
        self.assert_equal(c.to_python(1), True)
        self.assert_equal(c.to_python('true'), True)

        with self.assert_raises(ayame.ConversionError):
            c.to_string(None)
        self.assert_equal(c.to_string(False), 'False')
        with self.assert_raises(ayame.ConversionError):
            c.to_string(0)
        with self.assert_raises(ayame.ConversionError):
            c.to_string('')
        self.assert_equal(c.to_string(True), 'True')
        with self.assert_raises(ayame.ConversionError):
            c.to_string(1)
        with self.assert_raises(ayame.ConversionError):
            c.to_string('true')

    def test_float(self):
        pi = '3.141592653589793'[:sys.float_info.dig + 1]
        inf = float('inf')
        nan = float('nan')

        c = converter.FloatConverter()
        self.assert_is(c.type, float)
        self.assert_is_instance(3.14, c.type)

        self.assert_equal(c.to_python('-inf'), -inf)
        self.assert_equal(c.to_python('-' + pi), -float(pi))
        self.assert_equal(c.to_python('-3.14'), -3.14)
        self.assert_equal(c.to_python('-0'), 0.0)
        self.assert_equal(c.to_python('0'), 0.0)
        self.assert_equal(c.to_python(None), 0.0)
        self.assert_equal(c.to_python('3.14'), 3.14)
        self.assert_equal(c.to_python(pi), float(pi))
        self.assert_equal(c.to_python('inf'), inf)
        self.assert_is_instance(c.to_python('nan'), float)
        self.assert_not_equal(c.to_python('nan'), nan)
        with self.assert_raises(ayame.ConversionError):
            c.to_python('')
        with self.assert_raises(ayame.ConversionError):
            c.to_python(object())

        self.assert_equal(c.to_string(-inf), '-inf')
        self.assert_equal(c.to_string(-float(pi)), '-' + pi)
        self.assert_equal(c.to_string(-3.14), '-3.14')
        self.assert_equal(c.to_string(-0.0), '-0.0')
        self.assert_equal(c.to_string(0.0), '0.0')
        self.assert_equal(c.to_string(3.14), '3.14')
        self.assert_equal(c.to_string(float(pi)), pi)
        self.assert_equal(c.to_string(inf), 'inf')
        self.assert_equal(c.to_string(nan), 'nan')
        with self.assert_raises(ayame.ConversionError):
            c.to_string(None)
        with self.assert_raises(ayame.ConversionError):
            c.to_string('')
        with self.assert_raises(ayame.ConversionError):
            c.to_string(object())

    def test_int(self):
        c = converter.IntegerConverter()
        if sys.hexversion < 0x03000000:
            self.assert_equal(c.type, (long, int))
        else:
            self.assert_is(c.type, int)
        self.assert_is_instance(int(0), c.type)
        self.assert_is_instance(long(0), c.type)

        self.assert_equal(c.to_python(unicode(-8192)), -8192)
        self.assert_equal(c.to_python('0'), 0)
        self.assert_equal(c.to_python(None), 0)
        self.assert_equal(c.to_python(unicode(8192)), 8192)
        with self.assert_raises(ayame.ConversionError):
            c.to_python('')
        with self.assert_raises(ayame.ConversionError):
            c.to_python(object())

        self.assert_equal(c.to_string(int(-8192)), unicode(-8192))
        self.assert_equal(c.to_string(long(-8192)), unicode(-8192))
        self.assert_equal(c.to_string(int(0)), '0')
        self.assert_equal(c.to_string(long(0)), '0')
        self.assert_equal(c.to_string(int(-0)), '0')
        self.assert_equal(c.to_string(long(-0)), '0')
        self.assert_equal(c.to_string(int(8192)), unicode(8192))
        self.assert_equal(c.to_string(long(8192)), unicode(8192))
        with self.assert_raises(ayame.ConversionError):
            c.to_string(None)
        with self.assert_raises(ayame.ConversionError):
            c.to_string('')
        with self.assert_raises(ayame.ConversionError):
            c.to_string(object())

    def test_date(self):
        c = converter.DateConverter()
        self.assert_is(c.type, datetime.date)
        self.assert_is_instance(datetime.date.today(), c.type)

        self.assert_equal(c.to_python('2011-01-01'), datetime.date(2011, 1, 1))
        with self.assert_raises(ayame.ConversionError):
            c.to_python('1-1-1')
        with self.assert_raises(ayame.ConversionError):
            c.to_python(None)
        with self.assert_raises(ayame.ConversionError):
            c.to_python('')
        with self.assert_raises(ayame.ConversionError):
            c.to_python(object())

        self.assert_equal(c.to_string(datetime.date(2011, 1, 1)), '2011-01-01')
        with self.assert_raises(ayame.ConversionError):
            c.to_string(datetime.date(1, 1, 1))
        with self.assert_raises(ayame.ConversionError):
            c.to_string(None)
        with self.assert_raises(ayame.ConversionError):
            c.to_string('')
        with self.assert_raises(ayame.ConversionError):
            c.to_string(object())

    def test_time(self):
        c = converter.TimeConverter()
        self.assert_is(c.type, datetime.time)
        self.assert_is_instance(datetime.datetime.now().time(), c.type)

        self.assert_equal(c.to_python('00:00:00'), datetime.time(0, 0, 0))
        with self.assert_raises(ayame.ConversionError):
            c.to_python('24:00:00')
        with self.assert_raises(ayame.ConversionError):
            c.to_python(None)
        with self.assert_raises(ayame.ConversionError):
            c.to_python('')
        with self.assert_raises(ayame.ConversionError):
            c.to_python(object())

        self.assert_equal(c.to_string(datetime.time(0, 0, 0)), '00:00:00')
        with self.assert_raises(ayame.ConversionError):
            c.to_string(None)
        with self.assert_raises(ayame.ConversionError):
            c.to_string('')
        with self.assert_raises(ayame.ConversionError):
            c.to_string(object())

    def test_datetime(self):
        c = converter.DateTimeConverter()
        self.assert_is(c.type, datetime.datetime)
        self.assert_is_instance(datetime.datetime.now(), c.type)

        self.assert_equal(c.to_python('2011-01-01T00:00:00-05:00'),
                          datetime.datetime(2011, 1, 1, 0, 0, 0))
        self.assert_equal(c.to_python('2011-01-01T00:00:00Z'),
                          datetime.datetime(2011, 1, 1, 0, 0, 0))
        self.assert_equal(c.to_python('2011-01-01 00:00:00+09:00'),
                          datetime.datetime(2011, 1, 1, 0, 0, 0))
        with self.assert_raises(ayame.ConversionError):
            c.to_python('2011-01-01T00:00:00')
        with self.assert_raises(ayame.ConversionError):
            c.to_python('2011-01-01T00:00:00-0500')
        with self.assert_raises(ayame.ConversionError):
            c.to_python('2011-01-01T00:00:00+0900')
        with self.assert_raises(ayame.ConversionError):
            c.to_python('2011-01-01T00:00:00-a:a')
        with self.assert_raises(ayame.ConversionError):
            c.to_python('2011-01-01T00:00:00-12:01')
        with self.assert_raises(ayame.ConversionError):
            c.to_python('2011-01-01T00:00:00+14:01')
        with self.assert_raises(ayame.ConversionError):
            c.to_python('2011-01-01t00:00:00Z')
        with self.assert_raises(ayame.ConversionError):
            c.to_python('1-01-01T00:00:00Z')
        with self.assert_raises(ayame.ConversionError):
            c.to_python(None)
        with self.assert_raises(ayame.ConversionError):
            c.to_python('')
        with self.assert_raises(ayame.ConversionError):
            c.to_python(object())

        class Eastern(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(hours=-5) + self.dst(dt)
            def tzname(self, dt):
                return 'EDT' if self.dst(dt) else 'EST'
            def dst(self, dt):
                start = datetime.datetime(2011, 3, 13, 2, 0, 0, tzinfo=None)
                end = datetime.datetime(2011, 11, 6, 2, 0, 0, tzinfo=None)
                if start <= dt.replace(tzinfo=None) < end:
                    return datetime.timedelta(hours=1)
                return datetime.timedelta(0)
        class UTC(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(0)
            def tzname(self, dt):
                return 'UTC'
            def dst(self, dt):
                return datetime.timedelta(0)
        class JST(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(hours=9)
            def tzname(self, dt):
                return 'JST'
            def dst(self, dt):
                return datetime.timedelta(hours=9)
        class Invalid(datetime.tzinfo):
            def utcoffset(self, dt):
                return 0
            def tzname(self, dt):
                return 'INVALID'
            def dst(self, dt):
                return 0
        self.assert_equal(c.to_string(datetime.datetime(2011, 1, 1, 0, 0, 0)),
                          '2011-01-01 00:00:00Z')
        self.assert_equal(c.to_string(datetime.datetime(2011, 1, 1, 0, 0, 0,
                                                        tzinfo=Eastern())),
                          '2011-01-01 00:00:00-05:00')
        self.assert_equal(c.to_string(datetime.datetime(2011, 1, 1, 0, 0, 0,
                                                        tzinfo=UTC())),
                          '2011-01-01 00:00:00Z')
        self.assert_equal(c.to_string(datetime.datetime(2011, 1, 1, 0, 0, 0,
                                                        tzinfo=JST())),
                          '2011-01-01 00:00:00+09:00')
        with self.assert_raises(ayame.ConversionError):
            c.to_string(datetime.datetime(2011, 1, 1, 0, 0, 0,
                                          tzinfo=Invalid()))
        with self.assert_raises(ayame.ConversionError):
            c.to_string(None)
        with self.assert_raises(ayame.ConversionError):
            c.to_string('')
        with self.assert_raises(ayame.ConversionError):
            c.to_string(object())
