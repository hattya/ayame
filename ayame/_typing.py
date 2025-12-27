#
# ayame._typing
#
#   Copyright (c) 2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import sys
from typing import TYPE_CHECKING, Any, TypeAlias


__all__ = ['Headers', 'Locale', 'OptExcInfo', 'Self',
           'InputStream', 'StartResponse', 'WSGIEnvironment']

Headers: TypeAlias = list[tuple[str, str]]
Locale: TypeAlias = tuple[str | None, str | None]

if TYPE_CHECKING:
    from _typeshed import OptExcInfo
else:
    OptExcInfo = Any

if sys.version_info >= (3, 11):
    from typing import Self
    from wsgiref.types import InputStream, StartResponse, WSGIEnvironment
elif TYPE_CHECKING:
    from typing_extensions import Self
    from _typeshed.wsgi import InputStream, StartResponse, WSGIEnvironment
else:
    Self = Any
    InputStream = StartResponse = WSGIEnvironment = Any
