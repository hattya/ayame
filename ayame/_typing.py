#
# ayame._typing
#
#   Copyright (c) 2025-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from collections.abc import Iterable
import sys
from typing import TYPE_CHECKING, runtime_checkable, Any, Protocol, TypeAlias, TypeVar


__all__ = ['Headers', 'Locale', 'OptExcInfo', 'Self', 'SupportsKeysAndGetItem',
           'InputStream', 'StartResponse', 'WSGIEnvironment']

_KT = TypeVar('_KT')
_VT_co = TypeVar('_VT_co', covariant=True)

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


@runtime_checkable
class SupportsKeysAndGetItem(Protocol[_KT, _VT_co]):

    def keys(self) -> Iterable[_KT]: ...
    def __getitem__(self, key: _KT, /) -> _VT_co: ...
