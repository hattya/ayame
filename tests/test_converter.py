#
# test_converter
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

import sys
from datetime import date, time, datetime, timedelta, tzinfo

from nose.tools import assert_raises, eq_, ok_

from ayame import converter
from ayame.exception import ConversionError


def test_locator():
    class O:
        pass
    class OO(O):
        pass

    class N(object):
        pass
    class NN(N):
        pass

    class NO(N, O):
        pass
    class ON(O, N):
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

    locator = converter.Locator()
    locator.add(OConverter())
    locator.add(NConverter())

    eq_(locator.converter_for(sys), locator.get(object))
    eq_(locator.converter_for(test_locator), locator.get(object))
    eq_(locator.converter_for(None), locator.get(object))
    eq_(locator.converter_for(0), locator.get(int))
    eq_(locator.converter_for(True), locator.get(bool))

    eq_(locator.converter_for(O), locator.get(O))
    eq_(locator.converter_for(N), locator.get(N))
    eq_(locator.converter_for(OO), locator.get(O))
    eq_(locator.converter_for(NN), locator.get(N))
    eq_(locator.converter_for(ON), locator.get(O))
    eq_(locator.converter_for(NO), locator.get(N))

    eq_(locator.converter_for(O()), locator.get(O))
    eq_(locator.converter_for(N()), locator.get(N))
    eq_(locator.converter_for(OO()), locator.get(O))
    eq_(locator.converter_for(NN()), locator.get(N))
    eq_(locator.converter_for(ON()), locator.get(O))
    eq_(locator.converter_for(NO()), locator.get(N))

    locator.remove(O)

    eq_(locator.converter_for(O()), locator.get(object))
    eq_(locator.converter_for(N()), locator.get(N))
    eq_(locator.converter_for(OO()), locator.get(object))
    eq_(locator.converter_for(NN()), locator.get(N))
    eq_(locator.converter_for(ON()), locator.get(N))
    eq_(locator.converter_for(NO()), locator.get(N))

def test_converter():
    class C(converter.Converter):
        @property
        def type(self):
            return super(C, self).type
        def to_python(self, value):
            return super(C, self).to_python(value)

    c = C()
    eq_(c.type, None)
    eq_(c.to_python(None), None)
    eq_(c.to_string(None), 'None')

def test_object():
    c = converter._ObjectConverter()

    class O:
        pass
    class N(object):
        pass

    o = O()
    n = N()

    eq_(c.type, object)
    ok_(isinstance(o, c.type))
    ok_(isinstance(n, c.type))

    eq_(c.to_python(None), None)
    eq_(c.to_python(o), o)
    eq_(c.to_python(n), n)

    eq_(c.to_string(None), 'None')
    eq_(c.to_string(o), unicode(o))
    eq_(c.to_string(n), unicode(n))

def test_boolean():
    c = converter.BooleanConverter()

    eq_(c.type, bool)
    ok_(isinstance(True, c.type))
    ok_(isinstance(False, c.type))

    eq_(c.to_python(None), False)
    eq_(c.to_python(0), False)
    eq_(c.to_python(''), False)
    eq_(c.to_python('false'), False)
    eq_(c.to_python('off'), False)
    eq_(c.to_python('no'), False)
    eq_(c.to_python('n'), False)
    eq_(c.to_python(object()), True)
    eq_(c.to_python(1), True)
    eq_(c.to_python('true'), True)

    assert_raises(ConversionError, c.to_string, None)
    eq_(c.to_string(False), 'False')
    assert_raises(ConversionError, c.to_string, 0)
    assert_raises(ConversionError, c.to_string, '')
    eq_(c.to_string(True), 'True')
    assert_raises(ConversionError, c.to_string, 1)
    assert_raises(ConversionError, c.to_string, 'true')

def test_float():
    c = converter.FloatConverter()
    pi = '3.141592653589793'
    inf = float('inf')
    nan = float('nan')

    eq_(c.type, float)
    ok_(isinstance(3.14, c.type))

    eq_(c.to_python('-inf'), -inf)
    eq_(c.to_python('-3.14'), -3.14)
    eq_(c.to_python('0'), 0.0)
    eq_(c.to_python('0'), 0.0)
    ok_(isinstance(c.to_python('0'), float))
    eq_(c.to_python(None), 0.0)
    ok_(isinstance(c.to_python(None), float))
    eq_(c.to_python('3.14'), 3.14)
    eq_(c.to_python('inf'), inf)
    ok_(c.to_python('nan') != nan)
    assert_raises(ConversionError, c.to_python, '')
    assert_raises(ConversionError, c.to_python, object())

    eq_(c.to_string(-inf), '-inf')
    eq_(c.to_string(-float(pi)), '-3.14159265359')
    eq_(c.to_string(-3.14), '-3.14')
    eq_(c.to_string(0.0), '0.0')
    eq_(c.to_string(-0.0), '-0.0')
    eq_(c.to_string(3.14), '3.14')
    eq_(c.to_string(float(pi)), '3.14159265359')
    eq_(c.to_string(inf), 'inf')
    eq_(c.to_string(nan), 'nan')
    assert_raises(ConversionError, c.to_string, None)
    assert_raises(ConversionError, c.to_string, '')
    assert_raises(ConversionError, c.to_string, object())

def test_int():
    c = converter.IntegerConverter()

    eq_(c.type, (long, int))
    ok_(isinstance(int(0), c.type))
    ok_(isinstance(long(0), c.type))

    eq_(c.to_python(unicode(-8192)), -8192)
    eq_(c.to_python('0'), 0)
    eq_(c.to_python(None), 0)
    eq_(c.to_python(unicode(8192)), 8192)
    assert_raises(ConversionError, c.to_python, '')
    assert_raises(ConversionError, c.to_python, object())

    eq_(c.to_string(int(-8192)), unicode(-8192))
    eq_(c.to_string(long(-8192)), unicode(-8192))
    eq_(c.to_string(int(0)), '0')
    eq_(c.to_string(long(0)), '0')
    eq_(c.to_string(int(-0)), '0')
    eq_(c.to_string(long(-0)), '0')
    eq_(c.to_string(int(8192)), unicode(8192))
    eq_(c.to_string(long(8192)), unicode(8192))
    assert_raises(ConversionError, c.to_string, None)
    assert_raises(ConversionError, c.to_string, '')
    assert_raises(ConversionError, c.to_string, object())

def test_date():
    c = converter.DateConverter()

    eq_(c.type, date)
    ok_(date.today(), c.type)

    eq_(c.to_python('2011-01-01'), date(2011, 1, 1))
    assert_raises(ConversionError, c.to_python, '1-1-1')
    assert_raises(ConversionError, c.to_python, None)
    assert_raises(ConversionError, c.to_python, '')
    assert_raises(ConversionError, c.to_python, object())

    eq_(c.to_string(date(2011, 1, 1)), '2011-01-01')
    assert_raises(ConversionError, c.to_string, date(1, 1, 1))
    assert_raises(ConversionError, c.to_string, None)
    assert_raises(ConversionError, c.to_string, '')
    assert_raises(ConversionError, c.to_string, object())

def test_time():
    c = converter.TimeConverter()

    eq_(c.type, time)
    ok_(datetime.now().time(), c.type)

    eq_(c.to_python('00:00:00'), time(0, 0, 0))
    assert_raises(ConversionError, c.to_python, '24:00:00')
    assert_raises(ConversionError, c.to_python, None)
    assert_raises(ConversionError, c.to_python, '')
    assert_raises(ConversionError, c.to_python, object())

    eq_(c.to_string(time(0, 0, 0)), '00:00:00')
    assert_raises(ConversionError, c.to_string, None)
    assert_raises(ConversionError, c.to_string, '')
    assert_raises(ConversionError, c.to_string, object())

def test_datetime():
    c = converter.DateTimeConverter()

    eq_(c.type, datetime)
    ok_(datetime.now(), c.type)

    eq_(c.to_python('2011-01-01T00:00:00-05:00'),
        datetime(2011, 1, 1, 0, 0, 0))
    eq_(c.to_python('2011-01-01T00:00:00Z'), datetime(2011, 1, 1, 0, 0, 0))
    eq_(c.to_python('2011-01-01 00:00:00+09:00'),
        datetime(2011, 1, 1, 0, 0, 0))
    assert_raises(ConversionError, c.to_python, '2011-01-01T00:00:00')
    assert_raises(ConversionError, c.to_python, '2011-01-01T00:00:00-0500')
    assert_raises(ConversionError, c.to_python, '2011-01-01T00:00:00+0900')
    assert_raises(ConversionError, c.to_python, '2011-01-01T00:00:00-a:a')
    assert_raises(ConversionError, c.to_python, '2011-01-01T00:00:00-12:01')
    assert_raises(ConversionError, c.to_python, '2011-01-01T00:00:00+14:01')
    assert_raises(ConversionError, c.to_python, '2011-01-01t00:00:00Z')
    assert_raises(ConversionError, c.to_python, '1-01-01T00:00:00Z')
    assert_raises(ConversionError, c.to_python, None)
    assert_raises(ConversionError, c.to_python, '')
    assert_raises(ConversionError, c.to_python, object())

    class Eastern(tzinfo):
        def utcoffset(self, dt):
            return timedelta(hours=-5) + self.dst(dt)
        def tzname(self, dt):
            if self.dst(dt):
                return 'EDT'
            return 'EST'
        def dst(self, dt):
            start = datetime(2011, 3, 13, 2, 0, 0, tzinfo=None)
            end = datetime(2011, 11, 6, 2, 0, 0, tzinfo=None)
            if start <= dt.replace(tzinfo=None) < end:
                return timedelta(hours=1)
            return timedelta(0)
    class UTC(tzinfo):
        def utcoffset(self, dt):
            return timedelta(0)
        def tzname(self, dt):
            return 'UTC'
        def dst(self, dt):
            return timedelta(0)
    class JST(tzinfo):
        def utcoffset(self, dt):
            return timedelta(hours=9)
        def tzname(self, dt):
            return 'JST'
        def dst(self, dt):
            return timedelta(hours=9)
    class Invalid(tzinfo):
        def utcoffset(self, dt):
            return 0
        def tzname(self, dt):
            return 'INVALID'
        def dst(self, dt):
            return 0

    eq_(c.to_string(datetime(2011, 1, 1, 0, 0, 0)), '2011-01-01 00:00:00Z')
    eq_(c.to_string(datetime(2011, 1, 1, 0, 0, 0, tzinfo=Eastern())),
        '2011-01-01 00:00:00-05:00')
    eq_(c.to_string(datetime(2011, 1, 1, 0, 0, 0, tzinfo=UTC())),
        '2011-01-01 00:00:00Z')
    eq_(c.to_string(datetime(2011, 1, 1, 0, 0, 0, tzinfo=JST())),
        '2011-01-01 00:00:00+09:00')
    assert_raises(ConversionError, c.to_string,
                  datetime(2011, 1, 1, 0, 0, 0, tzinfo=Invalid()))
    assert_raises(ConversionError, c.to_string, None)
    assert_raises(ConversionError, c.to_string, '')
    assert_raises(ConversionError, c.to_string, object())
