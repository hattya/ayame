#
# ayame._typing
#
#   Copyright (c) 2025-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from collections.abc import Iterable
from typing import TYPE_CHECKING, runtime_checkable, Any, Protocol, TypeAlias, TypeVar


__all__ = ['Headers', 'Locale', 'OptExcInfo', 'SupportsKeysAndGetItem']

_KT = TypeVar('_KT')
_VT_co = TypeVar('_VT_co', covariant=True)

Headers: TypeAlias = list[tuple[str, str]]
Locale: TypeAlias = tuple[str | None, str | None]

if TYPE_CHECKING:
    from _typeshed import OptExcInfo
else:
    OptExcInfo = Any


@runtime_checkable
class SupportsKeysAndGetItem(Protocol[_KT, _VT_co]):

    def keys(self) -> Iterable[_KT]: ...
    def __getitem__(self, key: _KT, /) -> _VT_co: ...
