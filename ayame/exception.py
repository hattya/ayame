#
# ayame.exception
#
#   Copyright (c) 2011-2014 Akinori Hattori <hattya@gmail.com>
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

from . import _compat as five


__all__ = ['AyameError', 'ComponentError', 'ConversionError', 'MarkupError',
           'RenderingError', 'ResourceError', 'RouteError', 'ValidationError']


class AyameError(Exception):
    pass


class ComponentError(AyameError):
    pass


class ConversionError(AyameError):

    def __init__(self, *args, **kwargs):
        super(ConversionError, self).__init__(*args)
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
        super(_Redirect, self).__init__(object, values, anchor, type)


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
        super(ValidationError, self).__init__(*args)
        self.component = kwargs.get('component')
        self.keys = []
        self.vars = {}

        validator = kwargs.get('validator')
        if validator:
            key = validator.__class__.__name__
            variation = kwargs.get('variation')
            if variation:
                key += '.' + variation
            self.keys.append(key)

    def __repr__(self):
        args = repr(self.args)[1:-1].rstrip(',') + ', ' if self.args else ''
        return '{}({}keys={}, vars={})'.format(self.__class__.__name__,
                                               args,
                                               self.keys,
                                               list(self.vars))

    def __str__(self):
        if self.component:
            for key in self.keys:
                msg = self.component.tr(key)
                if msg is not None:
                    return msg.format(**self.vars)
        return five.str(self.args[0]) if 0 < len(self.args) else u''
