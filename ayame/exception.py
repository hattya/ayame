#
# ayame.exception
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import enum
from typing import TYPE_CHECKING, Any, AnyStr

if TYPE_CHECKING:
    from . import converter, core, validator


__all__ = ['AyameError', 'ComponentError', 'ConversionError', 'MarkupError',
           'RenderingError', 'ResourceError', 'RouteError', 'ValidationError']


class AyameError(Exception):
    pass


class ComponentError(AyameError):
    pass


class ConversionError(AyameError):

    def __init__(self, *args: Any, converter: converter.Converter | None = None, value: Any | None = None,
                 type: type | tuple[type, ...] | None = None):
        super().__init__(*args)
        self.converter = converter
        self.value = value
        self.type = type


class MarkupError(AyameError):
    pass


class _Redirect(AyameError):

    def __init__(self, object: Any, values: dict[AnyStr, Any] | None = None, anchor: AnyStr | None = None,
                 type: Type | None = None):
        super().__init__(object, values, anchor, type)

    @enum.unique
    class Type(enum.Enum):

        INTERNAL = enum.auto()
        PERMANENT = enum.auto()
        TEMPORARY = enum.auto()


class RenderingError(AyameError):
    pass


class ResourceError(AyameError):
    pass


class RouteError(AyameError):
    pass


class _RequestSlash(RouteError):
    pass


class ValidationError(AyameError):

    vars: dict[str, Any]

    def __init__(self, *args: Any, component: core.Component | None = None,
                 validator: validator.Validator | None = None, variation: str | None = None) -> None:
        super().__init__(*args)
        self.component = component
        self.keys = []
        self.vars = {}

        if validator:
            key = type(validator).__name__
            if variation:
                key += '.' + variation
            self.keys.append(key)

    def __repr__(self) -> str:
        args = repr(self.args)[1:-1].rstrip(',') + ', ' if self.args else ''
        return f'{type(self).__name__}({args}keys={self.keys}, vars={list(self.vars)})'

    def __str__(self) -> str:
        if self.component:
            for key in self.keys:
                if (msg := self.component.tr(key)) is not None:
                    return msg.format(**self.vars)
        return str(self.args[0]) if len(self.args) > 0 else ''
