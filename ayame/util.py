#
# ayame.util
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import abc
import collections.abc
from collections.abc import Callable, Iterable, Iterator
from contextlib import AbstractContextManager
import dataclasses
import itertools
import secrets
import threading
from typing import cast, overload, Any, Generic, Protocol, TypeAlias, TypeVar

from ._typing import Self, SupportsKeysAndGetItem


__all__ = ['fqon_of', 'to_bytes', 'to_list', 'new_token', 'FilterDict',
           'RWLock', 'LRUCache', 'LFUCache']


T = TypeVar('T')
KT = TypeVar('KT')
VT = TypeVar('VT')
_KT = TypeVar('_KT')
_VT = TypeVar('_VT')

MappingLike: TypeAlias = SupportsKeysAndGetItem[Any, VT] | Iterable[tuple[Any, VT]]

_unset = object()


def fqon_of(o: Any) -> str:
    if not hasattr(o, '__name__'):
        o = type(o)

    if hasattr(o, '__module__'):
        match o.__module__:
            case None:
                return f'<unknown>.{o.__name__}'
            case 'builtins':
                pass
            case _:
                return f'{o.__module__}.{o.__name__}'
    n: str = o.__name__
    return n


def to_bytes(s: Any, encoding: str = 'utf-8', errors: str = 'strict') -> bytes:
    if isinstance(s, bytes):
        return s
    return (s if isinstance(s, str) else str(s)).encode(encoding, errors)


def to_list(o: Any) -> list[Any]:
    if o is None:
        return []
    elif (isinstance(o, collections.abc.Iterable)
          and not isinstance(o, str)):
        return list(o)
    return [o]


def new_token(n: int = 8) -> str:
    return secrets.token_hex((n + 1) // 2)[:n]


class FilterDict(dict[KT, VT]):

    def __init__(self, m: MappingLike[VT] | None = None, **kwargs: VT) -> None:
        super().__init__()
        self.update(m, **kwargs)

    def __convert__(self, key: Any) -> KT:
        return cast(KT, key)

    def __getitem__(self, key: Any) -> VT:
        return super().__getitem__(self.__convert__(key))

    def __setitem__(self, key: Any, value: VT) -> None:
        super().__setitem__(self.__convert__(key), value)

    def __delitem__(self, key: Any) -> None:
        super().__delitem__(self.__convert__(key))

    def __contains__(self, key: Any) -> bool:
        return super().__contains__(self.__convert__(key))

    def __or__(self, other: MappingLike[VT]) -> Self:  # type: ignore[override]
        rv = self.copy()
        rv.update(other)
        return rv

    def __ior__(self, other: MappingLike[VT]) -> Self:  # type: ignore[override]
        self.update(other)
        return self

    def __copy__(self) -> Self:
        return type(self)(self)

    copy = __copy__

    @overload
    def get(self, key: Any, default: None = None, /) -> VT | None: ...
    @overload
    def get(self, key: Any, default: VT, /) -> VT: ...
    @overload
    def get(self, key: Any, default: T, /) -> VT | T: ...

    def get(self, key: Any, default: object = _unset, /) -> Any:
        if default is _unset:
            return super().get(self.__convert__(key))
        return super().get(self.__convert__(key), default)

    @overload
    def pop(self, key: Any, /) -> VT: ...
    @overload
    def pop(self, key: Any, default: VT, /) -> VT: ...
    @overload
    def pop(self, key: Any, default: T, /) -> VT | T: ...

    def pop(self, key: Any, default: object = _unset, /) -> Any:
        if default is _unset:
            return super().pop(self.__convert__(key))
        return super().pop(self.__convert__(key), default)

    @overload
    def setdefault(self: FilterDict[KT, VT | None], key: Any, default: None = None, /) -> VT | None: ...
    @overload
    def setdefault(self, key: Any, default: VT, /) -> VT: ...

    def setdefault(self, key: Any, default: Any = None, /) -> Any:
        return super().setdefault(self.__convert__(key), default)

    def update(self, m: MappingLike[VT] | None = None, **kwargs: VT) -> None:  # type:ignore[override]
        def gen(m: MappingLike[VT] | None = None, **kwargs: VT) -> Iterator[tuple[KT, VT]]:
            if m is not None:
                if isinstance(m, SupportsKeysAndGetItem):
                    for k in m.keys():
                        yield (self.__convert__(k), m[k])
                elif isinstance(m, Iterable):
                    for k, v in m:
                        yield (self.__convert__(k), v)
            for k, v in kwargs.items():
                yield (self.__convert__(k), v)

        super().update(gen(m, **kwargs))


class RWLock:

    def __init__(self) -> None:
        self._rcnt = 0
        self._rwait = 0
        self._lock = threading.Lock()
        self._r = threading.Condition(self._lock)
        self._w = threading.Condition(self._lock)

    def read(self) -> AbstractContextManager[Any]:
        return self._Lock(self.acquire_read, self.release_read)

    def write(self) -> AbstractContextManager[Any]:
        return self._Lock(self.acquire_write, self.release_write)

    def acquire_read(self) -> None:
        with self._lock:
            while self._rcnt < 0:
                # wait for writer
                self._r.wait()
            self._rcnt += 1

    def release_read(self) -> None:
        with self._lock:
            if self._rcnt == 0:
                raise RuntimeError('read lock is not acquired')
            if self._rcnt < 0:
                # writer is waiting
                self._rcnt += 1
                self._rwait -= 1
                if self._rwait == 0:
                    # wake up writers
                    self._w.notify_all()
            else:
                self._rcnt -= 1

    def acquire_write(self) -> None:
        with self._lock:
            while self._rcnt < 0:
                # wait for writer
                self._w.wait()
            rcnt = self._rcnt
            self._rcnt = -rcnt - 1
            self._rwait = rcnt
            if rcnt > 0:
                # wait for readers
                self._w.wait()

    def release_write(self) -> None:
        with self._lock:
            if self._rcnt >= 0:
                raise RuntimeError('write lock is not acquired')
            self._rcnt += 1
            # wake up readers
            self._r.notify_all()
            # wake up writers
            self._w.notify_all()

    class _Lock:

        def __init__(self, acquire: Callable[[], None], release: Callable[[], None]) -> None:
            self._acquire = acquire
            self._release = release

        def __enter__(self) -> Self:
            self._acquire()
            return self

        def __exit__(self, *exc_info: object) -> None:
            self._release()


class _Cache(Generic[KT, VT], metaclass=abc.ABCMeta):

    __slots__ = ('_cap', '_ref', '_head', '_lock')

    _ref: dict[KT, _Entry[KT, VT]]

    def __init__(self, cap: int = -1) -> None:
        self._cap = cap
        self.on_init()

    @property
    def cap(self) -> int:
        with self._lock.read():
            return self._cap

    @cap.setter
    def cap(self, cap: int) -> None:
        with self._lock.write():
            self._cap = cap
            self._sweep()

    def __repr__(self) -> str:
        return f'{type(self).__name__}({list(self.items())})'

    def __len__(self) -> int:
        with self._lock.read():
            return len(self._ref)

    @abc.abstractmethod
    def __getitem__(self, key: KT) -> VT:
        raise NotImplementedError

    @abc.abstractmethod
    def __setitem__(self, key: KT, value: VT) -> None:
        raise NotImplementedError

    def __delitem__(self, key: KT) -> None:
        with self._lock.write():
            self._evict(self._ref[key])

    def __iter__(self) -> Iterator[KT]:
        with self._lock.read():
            for e in self._iter():
                yield e.key

    def __reversed__(self) -> Iterator[KT]:
        with self._lock.read():
            for e in self._iter(reverse=True):
                yield e.key

    def __contains__(self, key: object) -> bool:
        with self._lock.read():
            return key in self._ref

    def items(self) -> Iterator[tuple[KT, VT]]:
        with self._lock.read():
            for e in self._iter():
                yield (e.key, e.value)

    keys = __iter__

    def values(self) -> Iterator[VT]:
        with self._lock.read():
            for e in self._iter():
                yield e.value

    @overload
    def get(self, key: KT, default: None = None, /) -> VT | None: ...
    @overload
    def get(self, key: KT, default: VT, /) -> VT: ...
    @overload
    def get(self, key: KT, default: T, /) -> VT | T: ...

    def get(self, key: KT, default: object = None, /) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    @overload
    def pop(self, key: KT, /) -> VT: ...
    @overload
    def pop(self, key: KT, default: VT, /) -> VT: ...
    @overload
    def pop(self, key: KT, default: T, /) -> VT | T: ...

    def pop(self, key: KT, default: Any = _unset, /) -> Any:
        with self._lock.write():
            if default is _unset:
                e = self._ref.pop(key)
            else:
                e = self._ref.pop(key, default)
                if e is default:
                    return e
            # reset for evict
            self._ref[key] = e
            self._evict(e)
            return e.value

    def popitem(self) -> tuple[KT, VT]:
        with self._lock.write():
            k, e = self._ref.popitem()
            # reset for evict
            self._ref[k] = e
            self._evict(e)
            return e.key, e.value

    @overload
    def setdefault(self: _Cache[KT, VT | None], key: KT, default: None = None, /) -> T | None: ...
    @overload
    def setdefault(self, key: KT, default: VT, /) -> VT: ...

    def setdefault(self, key: KT, default: Any = None, /) -> Any:
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    def update(self, *args: Any, **kwargs: VT) -> None:
        raise NotImplementedError

    def peek(self, key: KT) -> VT:
        with self._lock.read():
            return self._ref[key].value

    def on_init(self) -> None:
        self._ref = {}
        self._lock = RWLock()

    def on_evicted(self, key: KT, value: VT) -> None:
        pass

    @abc.abstractmethod
    def _iter(self, reverse: bool = False) -> Iterator[_Entry[KT, VT]]:
        raise NotImplementedError

    @abc.abstractmethod
    def _sweep(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def _evict(self, e: _Entry[KT, VT]) -> None:
        self.on_evicted(e.key, e.value)

    class _Entry(Protocol[_KT, _VT]):

        key: _KT
        value: _VT


@collections.abc.MutableMapping.register
class LRUCache(_Cache[KT, VT]):

    __slots__ = ()

    _head: _Entry[KT, VT] | None

    def __getitem__(self, key: KT) -> VT:
        with self._lock.write():
            return self._move_to_front(self._ref[key]).value

    def __setitem__(self, key: KT, value: VT) -> None:
        with self._lock.write():
            if key in self._ref:
                e = cast(LRUCache._Entry[KT, VT], self._ref[key])
                e.value = value
                exists = True
            else:
                self._ref[key] = e = self._Entry(key, value)
                self._sweep()
                exists = False

            if self._head is None:
                self._head = e.next = e.prev = e
            else:
                self._move_to_front(e, exists)

    def __copy__(self) -> Self:
        with self._lock.read():
            c = type(self)(self._cap)
            for e in self._iter(reverse=True):
                c[e.key] = e.value
            return c

    def __getstate__(self) -> tuple[int, tuple[tuple[KT, VT], ...]]:
        with self._lock.read():
            return self._cap, tuple((e.key, e.value) for e in self._iter())

    def __setstate__(self, state: tuple[int, tuple[tuple[KT, VT], ...]]) -> None:
        self._cap = state[0]
        self.on_init()
        for k, v in reversed(state[1]):
            self[k] = v

    copy = __copy__

    def clear(self) -> None:
        with self._lock.write():
            self._ref.clear()
            self._head = None

    def on_init(self) -> None:
        super().on_init()
        self._head = None

    def _iter(self, reverse: bool = False) -> Iterator[_Entry[KT, VT]]:
        if self._head is None:
            # no entries
            return
        elif not reverse:
            # forward iterator
            e = self._head
            while True:
                n = e.next
                yield e
                if n is self._head:
                    break
                e = n
        else:
            # reverse iterator
            e = self._head.prev
            while True:
                p = e.prev
                yield e
                if e is self._head:
                    break
                e = p

    def _sweep(self) -> None:
        if self._cap >= 0:
            it = self._iter(reverse=True)
            while len(self._ref) > self._cap:
                self._evict(next(it))

    def _evict(self, e: _Cache._Entry[KT, VT]) -> None:
        e = cast(LRUCache._Entry[KT, VT], e)
        e.next.prev = e.prev
        e.prev.next = e.next
        del self._ref[e.key]
        if e is self._head:
            if (not self._ref
                or self._cap == 1):
                self._head = None
            else:
                self._head = e.next
        self.on_evicted(e.key, e.value)

    def _move_to_front(self, e: _Cache._Entry[KT, VT], exists: bool = True) -> _Entry[KT, VT]:
        e = cast(LRUCache._Entry[KT, VT], e)
        if e is self._head:
            # already at front
            return e
        # remove from current position
        if exists:
            e.next.prev = e.prev
            e.prev.next = e.next
        # insert at front
        assert self._head is not None
        n = self._head
        e.next = n
        e.prev = n.prev
        self._head = n.prev.next = n.prev = e
        return e

    @dataclasses.dataclass
    class _Entry(Generic[_KT, _VT]):

        key: _KT
        value: _VT
        next: LRUCache._Entry[_KT, _VT] = dataclasses.field(init=False)
        prev: LRUCache._Entry[_KT, _VT] = dataclasses.field(init=False)


@collections.abc.MutableMapping.register
class LFUCache(_Cache[KT, VT]):
    """An implementation of LFU cache algorithm

    This is based upon K. Shah, A. Mitra and D. Matani,
    "An O(1) algorithm for implementation the LFU cache eviction scheme" August 2010
    """

    __slots__ = ()

    _head: _Frequency[KT, VT]

    def __getitem__(self, key: KT) -> VT:
        with self._lock.write():
            e = cast(LFUCache._Entry[KT, VT], self._ref[key])
            curr = e.parent
            # remove from current frequency node
            self._remove(e)
            # append to next frequency node
            next = curr.next
            if (next is self._head
                or next.value != curr.value + 1):
                next = self._new_freq(curr.value + 1, next)
            next.append(e)

            return e.value

    def __setitem__(self, key: KT, value: VT) -> None:
        with self._lock.write():
            if key in self._ref:
                self._evict(self._ref[key])
            self._sweep(self._cap - 1 if self._cap > 0 else self._cap)

            freq = self._head.next
            if freq.value != 1:
                freq = self._new_freq(1, freq)
            self._ref[key] = e = self._Entry(key, value)
            freq.append(e)

    def __copy__(self) -> Self:
        with self._lock.read():
            c = type(self)(self._cap)
            for fv, g in itertools.groupby(self._iter(), lambda e: e.parent.value):
                for e in reversed(tuple(g)):
                    c[e.key] = e.value
                c._head.next.value = fv
            return c

    def __getstate__(self) -> tuple[int, tuple[tuple[int, tuple[tuple[KT, VT], ...]], ...]]:
        with self._lock.read():
            return (self._cap,
                    tuple((fv, tuple((e.key, e.value) for e in g))
                          for fv, g in itertools.groupby(self._iter(), lambda e: e.parent.value)))

    def __setstate__(self, state: tuple[int, tuple[tuple[int, tuple[tuple[KT, VT], ...]], ...]]) -> None:
        self._cap = state[0]
        self.on_init()
        for fv, g in state[1]:
            for k, v in reversed(g):
                self[k] = v
            self._head.next.value = fv

    copy = __copy__

    def clear(self) -> None:
        with self._lock.write():
            self._ref.clear()
            self._head.next = self._head.prev = self._head

    def on_init(self) -> None:
        super().on_init()
        self._head = self._Frequency(0)

    def _iter(self, reverse: bool = False) -> Iterator[_Entry[KT, VT]]:
        if self._head.next is self._head:
            # no entries
            return
        elif not reverse:
            # forward iterator
            freq = self._head.prev
            while freq is not self._head:
                assert freq.head is not None
                e = freq.head.prev
                while True:
                    p = e.prev
                    yield e
                    if e is freq.head:
                        break
                    e = p
                freq = freq.prev
        else:
            # reverse iterator
            freq = self._head.next
            while freq is not self._head:
                assert freq.head is not None
                e = freq.head
                while True:
                    n = e.next
                    yield e
                    if n is freq.head:
                        break
                    e = n
                freq = freq.next

    def _sweep(self, cap: int | None = None) -> None:
        if cap is None:
            cap = self._cap

        if cap >= 0:
            while len(self._ref) > cap:
                self._evict(self._lfu())

    def _evict(self, e: _Cache._Entry[KT, VT]) -> None:
        e = cast(LFUCache._Entry[KT, VT], e)
        self._remove(e)
        del self._ref[e.key]
        self.on_evicted(e.key, e.value)

    def _new_freq(self, v: int, next: _Frequency[KT, VT]) -> _Frequency[KT, VT]:
        freq: LFUCache._Frequency[KT, VT] = self._Frequency(v)
        freq.next = next
        freq.prev = next.prev
        next.prev.next = next.prev = freq
        return freq

    def _remove(self, e: _Entry[KT, VT]) -> None:
        freq = e.parent
        freq.remove(e)
        if freq.len == 0:
            freq.next.prev = freq.prev
            freq.prev.next = freq.next

    def _lfu(self) -> _Cache._Entry[KT, VT]:
        if self._head.next is self._head:
            raise RuntimeError(f"'{type(self).__name__}' is empty")
        assert self._head.next.head is not None
        return self._ref[self._head.next.head.key]

    @dataclasses.dataclass
    class _Entry(Generic[_KT, _VT]):

        key: _KT
        value: _VT
        parent: LFUCache._Frequency[_KT, _VT] = dataclasses.field(init=False)
        next: LFUCache._Entry[_KT, _VT] = dataclasses.field(init=False)
        prev: LFUCache._Entry[_KT, _VT] = dataclasses.field(init=False)

    class _Frequency(Generic[_KT, _VT]):

        __slots__ = ('value', 'head', 'len', 'next', 'prev')

        head: LFUCache._Entry[_KT, _VT] | None

        def __init__(self, value: int) -> None:
            self.value = value
            self.head = None
            self.len = 0
            self.next = self.prev = self

        def append(self, e: LFUCache._Entry[_KT, _VT]) -> None:
            if self.head is None:
                self.head = e.next = e.prev = e
            else:
                n = self.head
                e.next = n
                e.prev = n.prev
                n.prev.next = n.prev = e
            e.parent = self
            self.len += 1

        def remove(self, e: LFUCache._Entry[_KT, _VT]) -> None:
            if e.next is e:
                self.head = None
            else:
                e.next.prev = e.prev
                e.prev.next = e.next
                if self.head is e:
                    self.head = e.next
            del e.parent
            self.len -= 1
