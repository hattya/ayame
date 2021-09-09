#
# ayame.converter
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import abc
import collections
import collections.abc
import datetime

from .exception import ConversionError


__all__ = ['ConverterRegistry', 'Converter', 'BooleanConverter',
           'IntegerConverter', 'FloatConverter', 'DateConverter',
           'TimeConverter', 'DateTimeConverter']


class ConverterRegistry:

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
        class_ = value if isinstance(value, type) else value.__class__

        queue = collections.deque((class_,))
        while queue:
            class_ = queue.pop()
            conv = self.get(class_)
            if conv is not None:
                return conv
            queue.extend(c for c in reversed(class_.__bases__)
                         if c is not object)
        return self.get(object)

    def add(self, converter):
        if isinstance(converter.type, collections.abc.Iterable):
            self.__registry.update((t, converter) for t in converter.type
                                   if t is not None)
        elif converter.type is not None:
            self.__registry[converter.type] = converter

    def remove(self, type):
        if type in self.__registry:
            del self.__registry[type]


class Converter(metaclass=abc.ABCMeta):

    @abc.abstractproperty
    def type(self):
        pass

    @abc.abstractmethod
    def to_python(self, value):
        return value

    def to_string(self, value):
        e = self.check_type(value)
        if e is not None:
            raise e

        return str(value)

    def check_type(self, value):
        if not (self.type is None
                or isinstance(value, self.type)):
            q = "'{}'".format
            if isinstance(self.type, collections.abc.Iterable):
                et = []
                for t in self.type:
                    if et:
                        et.append(', ')
                    et.append(q(t))
                if len(et) > 2:
                    et[-2] = ' or '
                et = ''.join(et)
            else:
                et = q(self.type)
            return self.error(value, message=f"expected {et} but got '{type(value)}'")

    def error(self, value, type=None, message=None):
        if type is None:
            type = self.type
        if message is None:
            message = f"cannot convert '{value}' to '{type}'"

        return ConversionError(message,
                               converter=self,
                               value=value,
                               type=type)


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
        if isinstance(value, str):
            if value.lower() in ('false', 'off', 'no', 'n'):
                return False
        return bool(value)


class FloatConverter(Converter):

    @property
    def type(self):
        return float

    def to_python(self, value):
        try:
            return float(value) if value is not None else float()
        except (TypeError, ValueError):
            raise self.error(value)


class IntegerConverter(Converter):

    @property
    def type(self):
        return int

    def to_python(self, value):
        try:
            return int(value) if value is not None else int()
        except (TypeError, ValueError):
            raise self.error(value, type=int)


class DateConverter(Converter):

    _format = '%Y-%m-%d'

    @property
    def type(self):
        return datetime.date

    def to_python(self, value):
        try:
            return datetime.datetime.strptime(value, self._format).date()
        except (TypeError, ValueError):
            raise self.error(value)

    def to_string(self, value):
        e = self.check_type(value)
        if e is not None:
            raise e

        try:
            return str(value.strftime(self._format))
        except ValueError as e:
            raise self.error(value, message=str(e))


class TimeConverter(Converter):

    _format = '%H:%M:%S'

    @property
    def type(self):
        return datetime.time

    def to_python(self, value):
        try:
            return datetime.datetime.strptime(value, self._format).time()
        except (TypeError, ValueError):
            raise self.error(value)

    def to_string(self, value):
        e = self.check_type(value)
        if e is not None:
            raise e

        return str(value.strftime(self._format))


class DateTimeConverter(Converter):

    @property
    def type(self):
        return datetime.datetime

    def to_python(self, value):
        if not isinstance(value, str):
            raise self.error(value)

        ds = value
        # parse time zone
        if ds.endswith('Z'):
            # UTC
            ds = ds[:-1]
            off = 0
        else:
            # local time
            pos = max(ds.rfind('-'), ds.rfind('+'))
            ds, off = ds[:pos], ds[pos:]
            # check time zone range
            if ':' in off:
                sign = off[0]
                h, m = off[1:].split(':', 1)
                if (h.isdigit()
                    and m.isdigit()):
                    minutes = int(h) * 60 + int(m)
                    if sign == '+':
                        if minutes <= 840:  # UTC+14:00
                            off = -minutes
                    else:
                        if minutes <= 720:  # UTC-12:00
                            off = minutes
            if not isinstance(off, int):
                raise self.error(value)
        # parse date and time
        if 'T' not in ds:
            if ' ' in ds:
                ds = ds.replace(' ', 'T')
            else:
                raise self.error(value)
        # datetime
        try:
            dt = datetime.datetime.strptime(ds, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            raise self.error(value)
        return dt.replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(minutes=off)

    def to_string(self, value):
        e = self.check_type(value)
        if e is not None:
            raise e

        try:
            off = value.utcoffset()
        except TypeError as e:
            raise self.error(value, message=str(e))
        if not off:
            z = 'Z'
        else:
            mins = off.total_seconds() / 60
            z = f'{mins / 60:+03.0f}:{mins % 60:02.0f}'
        return f'{value:%Y-%m-%d %H:%M:%S}{z}'
