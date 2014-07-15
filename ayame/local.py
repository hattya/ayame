#
# ayame.local
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

import threading

from .exception import AyameError


__all__ = ['push', 'pop', 'context', 'app']

_local = threading.local()


class _Context(object):

    def __init__(self, app, environ):
        self.app = app
        self.environ = environ
        self.request = None
        self._router = None


def push(app, environ):
    stack = getattr(_local, 'stack', None)
    if stack is None:
        _local.stack = stack = []

    ctx = _Context(app, environ)
    stack.append(ctx)
    return ctx


def pop():
    stack = getattr(_local, 'stack', None)
    if (stack is not None and
        0 < len(stack)):
        return stack.pop()


def context():
    try:
        return _local.stack[-1]
    except (AttributeError, IndexError):
        raise AyameError(u"there is no application attached to '{}'".format(threading.current_thread().name))


def app():
    return context().app
