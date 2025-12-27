#
# ayame.local
#
#   Copyright (c) 2011-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import contextvars
from typing import TYPE_CHECKING

from ._typing import WSGIEnvironment
from .exception import AyameError

if TYPE_CHECKING:
    from . import app as am, route, session


__all__ = ['push', 'pop', 'context', 'app']

_stack: contextvars.ContextVar[list[Context]] = contextvars.ContextVar('ayame.local.stack')


class Context:

    request: am.Request
    session: session.Session
    _router: route.Router

    def __init__(self, app: am.Ayame, environ: WSGIEnvironment) -> None:
        self.app = app
        self.environ = environ


def push(app: am.Ayame, environ: WSGIEnvironment) -> Context:
    stack = _stack.get([]).copy()
    ctx = Context(app, environ)
    stack.append(ctx)
    _stack.set(stack)
    return ctx


def pop() -> Context | None:
    stack = _stack.get([])
    if not stack:
        return None
    ctx = stack.pop()
    _stack.set(stack)
    return ctx


def context() -> Context:
    try:
        return _stack.get()[-1]
    except LookupError:
        raise AyameError('there is no application attached to this context')


def app() -> am.Ayame:
    return context().app
