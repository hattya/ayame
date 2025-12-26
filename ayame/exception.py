#
# ayame.exception
#
#   Copyright (c) 2011-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

__all__ = ['AyameError', 'ComponentError', 'ConversionError', 'MarkupError',
           'RenderingError', 'ResourceError', 'RouteError', 'ValidationError']


class AyameError(Exception):
    pass


class ComponentError(AyameError):
    pass


class ConversionError(AyameError):

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.converter = kwargs.get('converter')
        self.value = kwargs.get('value')
        self.type = kwargs.get('type')


class MarkupError(AyameError):
    pass


class _Redirect(AyameError):

    INTERNAL = -1
    PERMANENT = 1
    TEMPORARY = 2

    def __init__(self, object, values=None, anchor=None, type=None):
        super().__init__(object, values, anchor, type)


class RenderingError(AyameError):
    pass


class ResourceError(AyameError):
    pass


class RouteError(AyameError):
    pass


class _RequestSlash(RouteError):
    pass


class ValidationError(AyameError):

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.component = kwargs.get('component')
        self.keys = []
        self.vars = {}

        validator = kwargs.get('validator')
        if validator:
            key = type(validator).__name__
            variation = kwargs.get('variation')
            if variation:
                key += '.' + variation
            self.keys.append(key)

    def __repr__(self):
        args = repr(self.args)[1:-1].rstrip(',') + ', ' if self.args else ''
        return f'{type(self).__name__}({args}keys={self.keys}, vars={list(self.vars)})'

    def __str__(self):
        if self.component:
            for key in self.keys:
                if (msg := self.component.tr(key)) is not None:
                    return msg.format(**self.vars)
        return str(self.args[0]) if len(self.args) > 0 else ''
