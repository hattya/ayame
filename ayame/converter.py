#
# ayame.converter
#
#   Copyright (c) 2011-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import abc
import builtins
import collections
import datetime
from typing import Any

from .exception import ConversionError


__all__ = ['ConverterRegistry', 'Converter', 'BooleanConverter',
           'IntegerConverter', 'FloatConverter', 'DateConverter',
           'TimeConverter', 'DateTimeConverter']


class ConverterRegistry:

    __registry: dict[type, Converter]

    def __init__(self) -> None:
        self.__registry = {}

        self.add(BooleanConverter())
        self.add(IntegerConverter())
        self.add(FloatConverter())
        self.add(DateConverter())
        self.add(TimeConverter())
        self.add(DateTimeConverter())
        self.add(_ObjectConverter())

    def get(self, type: type) -> Converter | None:
        return self.__registry.get(type)

    def converter_for(self, value: Any) -> Converter:
        cls = value if isinstance(value, type) else type(value)

        queue = collections.deque((cls,))
        while queue:
            cls = queue.pop()
            if cls in self.__registry:
                return self.__registry[cls]
            queue.extend(c for c in reversed(cls.__bases__)
                         if c is not object)
        return self.__registry[object]

    def add(self, converter: Converter) -> None:
        if isinstance(converter.type, tuple):
            self.__registry.update((t, converter) for t in converter.type
                                   if t is not None)
        elif converter.type is not None:
            self.__registry[converter.type] = converter

    def remove(self, type: type) -> None:
        if type in self.__registry:
            del self.__registry[type]


class Converter(metaclass=abc.ABCMeta):

    @property
    @abc.abstractmethod
    def type(self) -> builtins.type | tuple[builtins.type, ...]:
        raise NotImplementedError

    @abc.abstractmethod
    def to_python(self, value: Any) -> Any:
        raise NotImplementedError

    def to_string(self, value: Any) -> str:
        if (e := self.check_type(value)) is not None:
            raise e

        return str(value)

    def check_type(self, value: Any) -> ConversionError | None:
        if not (self.type is None
                or isinstance(value, self.type)):
            q = "'{}'".format
            et: list[str] | str
            if isinstance(self.type, tuple):
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
        return None

    def error(self, value: Any, type: builtins.type | tuple[builtins.type, ...] | None = None,
              message: str | None = None) -> ConversionError:
        return ConversionError(message if message is not None else f"cannot convert '{value}' to '{type}'",
                               converter=self,
                               value=value,
                               type=type if type is not None else self.type)


class _ObjectConverter(Converter):

    @property
    def type(self) -> builtins.type | tuple[builtins.type, ...]:
        return object

    def to_python(self, value: Any) -> Any:
        return value


class BooleanConverter(Converter):

    @property
    def type(self) -> builtins.type | tuple[builtins.type, ...]:
        return bool

    def to_python(self, value: Any) -> bool:
        if isinstance(value, str):
            if value.lower() in ('false', 'off', 'no', 'n'):
                return False
        return bool(value)


class FloatConverter(Converter):

    @property
    def type(self) -> builtins.type | tuple[builtins.type, ...]:
        return float

    def to_python(self, value: Any) -> float:
        try:
            return float(value) if value is not None else 0.0
        except (TypeError, ValueError):
            raise self.error(value)


class IntegerConverter(Converter):

    @property
    def type(self) -> builtins.type | tuple[builtins.type, ...]:
        return int

    def to_python(self, value: Any) -> int:
        try:
            return int(value) if value is not None else 0
        except (TypeError, ValueError):
            raise self.error(value)


class DateConverter(Converter):

    _format = '%Y-%m-%d'

    @property
    def type(self) -> builtins.type | tuple[builtins.type, ...]:
        return datetime.date

    def to_python(self, value: Any) -> datetime.date:
        try:
            return datetime.datetime.strptime(value, self._format).date()
        except (TypeError, ValueError):
            raise self.error(value)

    def to_string(self, value: Any) -> str:
        if (e := self.check_type(value)) is not None:
            raise e

        return str(value.strftime(self._format))


class TimeConverter(Converter):

    _format = '%H:%M:%S'

    @property
    def type(self) -> builtins.type | tuple[builtins.type, ...]:
        return datetime.time

    def to_python(self, value: Any) -> datetime.time:
        try:
            return datetime.datetime.strptime(value, self._format).time()
        except (TypeError, ValueError):
            raise self.error(value)

    def to_string(self, value: Any) -> str:
        if (e := self.check_type(value)) is not None:
            raise e

        return str(value.strftime(self._format))


class DateTimeConverter(Converter):

    @property
    def type(self) -> builtins.type | tuple[builtins.type, ...]:
        return datetime.datetime

    def to_python(self, value: Any) -> datetime.datetime:
        if not isinstance(value, str):
            raise self.error(value)

        ds = value
        off: int | str
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
            if ' ' not in ds:
                raise self.error(value)
            ds = ds.replace(' ', 'T')
        # datetime
        try:
            dt = datetime.datetime.strptime(ds, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            raise self.error(value)
        return dt.replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(minutes=off)

    def to_string(self, value: Any) -> str:
        if (e := self.check_type(value)) is not None:
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
