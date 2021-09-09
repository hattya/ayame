#
# ayame.res
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
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
                object = object.__class__
            try:
                m = sys.modules[object.__module__]
            except (AttributeError, KeyError):
                raise ResourceError(f'cannot find module of {object!r}')
            is_module = False
        try:
            parent, name = os.path.split(m.__file__)
        except AttributeError:
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

        loader = getattr(m, '__loader__', None)
        if loader is None:
            spec = getattr(m, '__spec__', None)
            if spec:
                loader = spec.loader
        r = self.load_from(loader, parent, path)
        if r is None:
            raise ResourceError(f"cannot load '{path}' from loader {loader!r}")
        return r

    def load_from(self, loader, parent, path):
        if (loader is None
            or (loader.__class__.__module__.startswith('_frozen_importlib')
                and loader.__class__.__name__ == 'SourceFileLoader')):
            return FileResource(os.path.join(parent, path))
        elif (loader.__class__.__module__ == 'zipimport'
              and loader.__class__.__name__ == 'zipimporter'):
            return ZipFileResource(loader, path if os.path.sep == '/' else path.replace(os.path.sep, '/'))


class Resource(metaclass=abc.ABCMeta):

    def __init__(self, path):
        self._path = path
        self._mtime = None

    @property
    def path(self):
        return self._path

    @property
    def mtime(self):
        return self._mtime

    @abc.abstractmethod
    def open(self, encoding='utf-8'):
        pass


class FileResource(Resource):

    def __init__(self, path):
        super().__init__(path)
        self._mtime = self._guard(os.stat, self._path).st_mtime

    def open(self, encoding='utf-8'):
        return self._guard(open, self._path, encoding=encoding)

    def _guard(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OSError:
            raise ResourceError(f"cannot load '{self._path}'")


class ZipFileResource(Resource):

    def __init__(self, loader, path):
        super().__init__(path)
        self._loader = loader
        with self._guard(zipfile.ZipFile, self._loader.archive) as zf:
            zi = self._guard(zf.getinfo, self._path)
            self._mtime = time.mktime(datetime.datetime(*zi.date_time).timetuple())

    def open(self, encoding='utf-8'):
        return io.StringIO(str(self._guard(self._loader.get_data, self._path), encoding))

    def _guard(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (OSError, KeyError):
            raise ResourceError(f"cannot load '{self._path}' from loader {self._loader!r}")
