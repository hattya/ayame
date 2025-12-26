#
# ayame.res
#
#   Copyright (c) 2011-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import abc
import datetime
import io
import os
import sys
import time
import types
import zipfile

from .exception import ResourceError


__all__ = ['ResourceLoader', 'Resource', 'FileResource', 'ZipFileResource']


class ResourceLoader:

    def load(self, object, path):
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

    def load_from(self, loader, parent, path):
        if (loader is None
            or (type(loader).__module__.startswith('_frozen_importlib')
                and type(loader).__name__ == 'SourceFileLoader')):
            return FileResource(os.path.join(parent, path))
        elif (type(loader).__module__ == 'zipimport'
              and type(loader).__name__ == 'zipimporter'):
            return ZipFileResource(loader, path if os.path.sep == '/' else path.replace(os.path.sep, '/'))


class Resource(metaclass=abc.ABCMeta):

    def __init__(self, path):
        self._path = path
        self._mtime = 0.0

    @property
    def path(self):
        return self._path

    @property
    def mtime(self):
        return self._mtime

    @abc.abstractmethod
    def open(self, encoding='utf-8'):
        raise NotImplementedError


class FileResource(Resource):

    def __init__(self, path):
        super().__init__(path)
        try:
            self._mtime = os.stat(self._path).st_mtime
        except OSError:
            raise self._error()

    def open(self, encoding='utf-8'):
        try:
            return open(self._path, encoding=encoding)
        except OSError:
            raise self._error()

    def _error(self):
        return ResourceError(f"cannot load '{self._path}'")


class ZipFileResource(Resource):

    def __init__(self, loader, path):
        super().__init__(path)
        self._loader = loader
        try:
            with zipfile.ZipFile(self._loader.archive) as zf:
                zi = zf.getinfo(self._path)
                self._mtime = time.mktime(datetime.datetime(*zi.date_time).timetuple())
        except (KeyError, OSError):
            raise self._error()

    def open(self, encoding='utf-8'):
        try:
            return io.StringIO(str(self._loader.get_data(self._path), encoding))
        except OSError:
            raise self._error()

    def _error(self):
        return ResourceError(f"cannot load '{self._path}' from loader {self._loader!r}")
