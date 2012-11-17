#
# ayame.converter
#
#   Copyright (c) 2011-2012 Akinori Hattori <hattya@gmail.com>
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

import abc
import collections
import datetime
import sys
import types

from ayame.exception import ConversionError


__all__ = ['Locator', 'Converter', 'BooleanConverter', 'IntegerConverter',
           'FloatConverter', 'DateConverter', 'TimeConverter',
           'DateTimeConverter']

class Locator(object):

    def __init__(self):
        self.__registry = {}

        self.add(BooleanConverter())
        self.add(IntegerConverter())
        self.add(FloatConverter())
        self.add(DateConverter())
        self.add(TimeConverter())
        self.add(DateTimeConverter())
        self.add(_ObjectConverter())

    def get(self, type):
        if type in self.__registry:
            return self.__registry[type]

    def converter_for(self, value):
        if isinstance(value, (type, types.ClassType)):
            class_ = value
        else:
            class_ = value.__class__

        queue = collections.deque((object, class_))
        while queue:
            class_ = queue.pop()
            converter = self.get(class_)
            if converter is not None:
                return converter
            for c in reversed(class_.__bases__):
                if c is not object:
                    queue.append(c)

    def add(self, converter):
        if isinstance(converter.type, tuple):
            for type in converter.type:
                self.__registry[type] = converter
        elif converter.type is not None:
            self.__registry[converter.type] = converter

    def remove(self, type):
        if type in self.__registry:
            del self.__registry[type]

class Converter(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def type(self):
        pass

    @abc.abstractmethod
    def to_python(self, value):
        return value

    def to_string(self, value):
        error = self._check_type(value)
        if error:
            raise error
        return unicode(value)

    def _check_type(self, value):
        if not (self.type is None or
                isinstance(value, self.type)):
            q = "'{}'".format
            if isinstance(self.type, tuple):
                et = []
                for t in self.type:
                    if et:
                        et.append(', ')
                    et.append(q(t))
                if 2 < len(et):
                    et[-2] = ' or '
                et = ''.join(et)
            else:
                et = q(self.type)
            return ConversionError(
                    "expected {} but got '{}'".format(et, type(value)))

    def _new_error(self, value, type=None):
        if type is None:
            type = self.type
        return ConversionError(u"could not convert '{}' to '{}'".format(value,
                                                                        type))

class _ObjectConverter(Converter):

    @property
    def type(self):
        return object

    def to_python(self, value):
        return value

class BooleanConverter(Converter):

    @property
    def type(self):
        return bool

    def to_python(self, value):
        if isinstance(value, basestring):
            s = value.lower()
            if s in ('false', 'off', 'no', 'n'):
                return False
        return bool(value)

class FloatConverter(Converter):

    @property
    def type(self):
        return float

    if sys.hexversion < 0x03020000:
        def to_string(self, value):
            error = self._check_type(value)
            if error:
                raise error
            return repr(value)

    def to_python(self, value):
        try:
            if value is None:
                return float()
            return float(value)
        except (TypeError, ValueError):
            raise self._new_error(value)

class IntegerConverter(Converter):

    if sys.hexversion < 0x03000000:
        @property
        def type(self):
            return (long, int)
    else:
        @property
        def type(self):
            return int

    def to_python(self, value):
        try:
            if value is None:
                return long()
            return long(value)
        except (TypeError, ValueError):
            raise self._new_error(value, type=long)

class DateConverter(Converter):

    _format = '%Y-%m-%d'

    @property
    def type(self):
        return datetime.date

    def to_python(self, value):
        try:
            return datetime.datetime.strptime(value, self._format).date()
        except (TypeError, ValueError):
            raise self._new_error(value)

    def to_string(self, value):
        error = self._check_type(value)
        if error:
            raise error
        try:
            return unicode(value.strftime(self._format))
        except ValueError as e:
            raise ConversionError(unicode(e))

class TimeConverter(Converter):

    _format = '%H:%M:%S'

    @property
    def type(self):
        return datetime.time

    def to_python(self, value):
        try:
            return datetime.datetime.strptime(value, self._format).time()
        except (TypeError, ValueError):
            raise self._new_error(value)

    def to_string(self, value):
        error = self._check_type(value)
        if error:
            raise error
        return unicode(value.strftime(self._format))

class DateTimeConverter(Converter):

    @property
    def type(self):
        return datetime.datetime

    def to_python(self, value):
        if not isinstance(value, basestring):
            raise self._new_error(value)

        ds = value
        # parse time zone
        if ds.endswith('Z'):
            # UTC
            ds = ds[:-1]
            offset = 0
        else:
            # local time
            pos = max(ds.rfind('-'), ds.rfind('+'))
            ds, offset = ds[:pos], ds[pos:]
            # check time zone range
            if ':' in offset:
                sign = offset[0]
                h, m = offset[1:].split(':', 1)
                if (h.isdigit() and
                    m.isdigit()):
                    minutes = int(h) * 60 + int(m)
                    if sign == '-':
                        if minutes <= 720:  # UTC-12:00
                            offset = minutes
                    else:
                        if minutes <= 840:  # UTC+14:00
                            offset = minutes
            if not isinstance(offset, int):
                raise self._new_error(value)
        # parse date and time
        if 'T' not in ds:
            if ' ' in ds:
                ds = ds.replace(' ', 'T')
            else:
                raise self._new_error(value)
        # datetime
        try:
            return datetime.datetime.strptime(ds, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            raise self._new_error(value)

    def to_string(self, value):
        error = self._check_type(value)
        if error:
            raise error
        try:
            utcoffset = value.utcoffset()
        except TypeError as e:
            raise ConversionError(unicode(e))
        if utcoffset is None:
            z = 'Z'
        else:
            seconds = utcoffset.total_seconds()
            if seconds == 0:
                z = 'Z'
            else:
                minutes = seconds / 60
                z = '{:+03.0f}:{:02.0f}'.format(minutes / 60, minutes % 60)
        return u'{:%Y-%m-%d %H:%M:%S}{Z}'.format(value, Z=z)
