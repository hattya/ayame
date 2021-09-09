#
# ayame.local
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import threading

from .exception import AyameError


__all__ = ['push', 'pop', 'context', 'app']

_local = threading.local()


class _Context:

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
    if (stack is not None
        and len(stack) > 0):
        return stack.pop()


def context():
    try:
        return _local.stack[-1]
    except (AttributeError, IndexError):
        raise AyameError(f"there is no application attached to '{threading.current_thread().name}'")


def app():
    return context().app
