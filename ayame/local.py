#
# ayame.local
#
#   Copyright (c) 2011-2023 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import contextvars

from .exception import AyameError


__all__ = ['push', 'pop', 'context', 'app']

_stack = contextvars.ContextVar('ayame.local.stack')


class _Context:

    def __init__(self, app, environ):
        self.app = app
        self.environ = environ
        self.request = None
        self._router = None


def push(app, environ):
    stack = _stack.get([]).copy()
    ctx = _Context(app, environ)
    stack.append(ctx)
    _stack.set(stack)
    return ctx


def pop():
    stack = _stack.get([])
    if not stack:
        return
    ctx = stack.pop()
    _stack.set(stack)
    return ctx


def context():
    try:
        return _stack.get()[-1]
    except LookupError:
        raise AyameError('there is no application attached to this context')


def app():
    return context().app
