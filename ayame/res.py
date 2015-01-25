#
# ayame.res
#
#   Copyright (c) 2011-2015 Akinori Hattori <hattya@gmail.com>
#
#   Permission is hereby granted, free of charge, to any person
#   obtaining a copy of this software and associated documentation files
#   (the "Software"), to deal in the Software without restriction,
#   including without limitation the rights to use, copy, modify, merge,
#   publish, distribute, sublicense, and/or sell copies of the Software,
#   and to permit persons to whom the Software is furnished to do so,
#   subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be
#   included in all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
#   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#   ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#   CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
#

import abc
import datetime
import io
import os
import sys
import time
import types
import zipfile

from . import _compat as five
from .exception import ResourceError


__all__ = ['ResourceLoader', 'Resource', 'FileResource', 'ZipFileResource']


class ResourceLoader(object):

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
                raise ResourceError('cannot find module of {!r}'.format(object))
            is_module = False
        try:
            parent, name = os.path.split(m.__file__)
        except AttributeError:
            raise ResourceError("cannot determine '{}' module location".format(m.__name__))
        name = os.path.splitext(name)[0]
        # check path
        p = os.path.normpath(path)
        if (os.path.isabs(p) or
            p.split(os.path.sep, 1)[0] == os.path.pardir):
            raise ResourceError("invalid path '{}'".format(path))
        path = p
        # prepare path
        if (not is_module and
            path.startswith('.')):
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
            raise ResourceError("cannot load '{}' from loader {!r}".format(path, loader))
        return r

    def load_from(self, loader, parent, path):
        if (loader is None or
            (loader.__class__.__module__ == '_frozen_importlib' and
             loader.__class__.__name__ == 'SourceFileLoader')):
            return FileResource(os.path.join(parent, path))
        elif (loader.__class__.__module__ == 'zipimport' and
              loader.__class__.__name__ == 'zipimporter'):
            return ZipFileResource(loader, path if os.path.sep == '/' else path.replace(os.path.sep, '/'))


class Resource(five.with_metaclass(abc.ABCMeta, object)):

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
        super(FileResource, self).__init__(path)
        self._mtime = self._guard(os.stat, self._path).st_mtime

    def open(self, encoding='utf-8'):
        return self._guard(io.open, self._path, encoding=encoding)

    def _guard(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (OSError, IOError):
            raise ResourceError("cannot load '{}'".format(self._path))


class ZipFileResource(Resource):

    def __init__(self, loader, path):
        super(ZipFileResource, self).__init__(path)
        self._loader = loader
        with self._guard(zipfile.ZipFile, self._loader.archive) as zf:
            zi = self._guard(zf.getinfo, self._path)
            self._mtime = time.mktime(datetime.datetime(*zi.date_time).timetuple())

    def open(self, encoding='utf-8'):
        return io.StringIO(five.str(self._guard(self._loader.get_data, self._path), encoding))

    def _guard(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (OSError, IOError, KeyError):
            raise ResourceError("cannot load '{}' from loader {!r}".format(self._path, self._loader))
