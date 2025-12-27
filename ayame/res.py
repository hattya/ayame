#
# ayame.res
#
#   Copyright (c) 2011-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import abc
import datetime
from importlib.abc import Loader
import io
import os
import sys
import time
import types
from typing import cast, Any, IO
import zipfile
import zipimport

from .exception import ResourceError


__all__ = ['ResourceLoader', 'Resource', 'FileResource', 'ZipFileResource']


class ResourceLoader:

    def load(self, object: Any, path: str) -> Resource:
        if isinstance(object, types.ModuleType):
            m = object
            is_module = True
        else:
            if not hasattr(object, '__name__'):
                object = type(object)
            try:
                m = sys.modules[object.__module__]
            except (AttributeError, KeyError):
                raise ResourceError(f'cannot find module of {object!r}')
            is_module = False
        if file := getattr(m, '__file__', None):
            parent, name = os.path.split(file)
        else:
            raise ResourceError(f"cannot determine '{m.__name__}' module location")
        name = os.path.splitext(name)[0]
        # check path
        p = os.path.normpath(path)
        if (os.path.isabs(p)
            or p.split(os.path.sep, 1)[0] == os.path.pardir):
            raise ResourceError(f"invalid path '{path}'")
        path = p
        # prepare path
        if (not is_module
            and path.startswith('.')):
            path = object.__name__ + path
        if name.lower() != '__init__':
            path = os.path.join(name, path)

        loader = spec.loader if (spec := m.__spec__) else None
        r = self.load_from(loader, parent, path)
        if r is None:
            raise ResourceError(f"cannot load '{path}' from loader {loader!r}")
        return r

    def load_from(self, loader: Loader | None, parent: str, path: str) -> Resource | None:
        if (loader is None
            or (type(loader).__module__.startswith('_frozen_importlib')
                and type(loader).__name__ == 'SourceFileLoader')):
            return FileResource(os.path.join(parent, path))
        elif (type(loader).__module__ == 'zipimport'
              and type(loader).__name__ == 'zipimporter'):
            return ZipFileResource(cast(zipimport.zipimporter, loader), path if os.path.sep == '/' else path.replace(os.path.sep, '/'))
        return None


class Resource(metaclass=abc.ABCMeta):

    def __init__(self, path: str) -> None:
        self._path = path
        self._mtime = 0.0

    @property
    def path(self) -> str:
        return self._path

    @property
    def mtime(self) -> float:
        return self._mtime

    @abc.abstractmethod
    def open(self, encoding: str = 'utf-8') -> IO[str]:
        raise NotImplementedError


class FileResource(Resource):

    def __init__(self, path: str) -> None:
        super().__init__(path)
        try:
            self._mtime = os.stat(self._path).st_mtime
        except OSError:
            raise self._error()

    def open(self, encoding: str = 'utf-8') -> IO[str]:
        try:
            return open(self._path, encoding=encoding)
        except OSError:
            raise self._error()

    def _error(self) -> ResourceError:
        return ResourceError(f"cannot load '{self._path}'")


class ZipFileResource(Resource):

    def __init__(self, loader: zipimport.zipimporter, path: str) -> None:
        super().__init__(path)
        self._loader = loader
        try:
            with zipfile.ZipFile(self._loader.archive) as zf:
                zi = zf.getinfo(self._path)
                self._mtime = time.mktime(datetime.datetime(*zi.date_time).timetuple())
        except (KeyError, OSError):
            raise self._error()

    def open(self, encoding: str = 'utf-8') -> IO[str]:
        try:
            return io.StringIO(str(self._loader.get_data(self._path), encoding))
        except OSError:
            raise self._error()

    def _error(self) -> ResourceError:
        return ResourceError(f"cannot load '{self._path}' from loader {self._loader!r}")
