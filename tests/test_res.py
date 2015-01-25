#
# test_res
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

import contextlib
import datetime
import io
import os
import sys
import tempfile
import time
import types
import zipfile

import ayame
from ayame import res
from base import AyameTestCase


class ResTestCase(AyameTestCase):

    def setup(self):
        super(ResTestCase, self).setup()
        self._module = sys.modules[__name__]

    def teardown(self):
        super(ResTestCase, self).teardown()
        sys.modules[__name__] = self._module

    def new_module(self, loader):
        class Module(types.ModuleType):
            def __init__(self):
                super(Module, self).__init__(__name__)
                self.__file__ = __file__
                if sys.version_info < (3, 4):
                    self.__loader__ = loader
                else:
                    from importlib.util import spec_from_loader

                    self.__spec__ = spec_from_loader(__name__, loader,
                                                     origin=__spec__.origin)

        return Module()

    def test_resource(self):
        class Resource(res.Resource):
            def open(self, encoding='utf-8'):
                return super(Resource, self).open(encoding)

        with self.assert_raises(TypeError):
            res.Resource(None)

        r = Resource(None)
        self.assert_is_none(r.path)
        self.assert_is_none(r.mtime)
        self.assert_is_none(r.open())

    def test_unknown_module(self):
        loader = res.ResourceLoader()

        class Spam(object):
            pass

        def ham():
            pass

        for o in (Spam, Spam(), ham):
            o.__module__ = None
            with self.assert_raises_regex(ayame.ResourceError,
                                          '^cannot find module '):
                loader.load(o, None)

    def test_unknown_module_location(self):
        sys.modules[__name__] = types.ModuleType(__name__)
        self._test_error(" module location$")

    def test_invalid_path(self):
        loader = res.ResourceLoader()

        class Spam(object):
            pass

        def ham():
            pass

        for o in (Spam, Spam(), ham, sys.modules[__name__]):
            for p in (os.path.pardir, os.path.join(*(os.path.pardir,) * 2), os.path.sep):
                with self.assert_raises_regex(ayame.ResourceError,
                                              '^invalid path '):
                    loader.load(o, p)

    def test_unknown_loader(self):
        sys.modules[__name__] = self.new_module(True)
        self._test_error("^cannot load '.*' from loader True$")

    def _test_error(self, regex):
        loader = res.ResourceLoader()

        class Spam(object):
            pass

        def ham():
            pass

        for o in (Spam, Spam()):
            for p in ('Spam.txt', '.txt'):
                with self.assert_raises_regex(ayame.ResourceError,
                                              regex):
                    loader.load(o, p)

        for p in ('ham.txt', '.txt'):
            with self.assert_raises_regex(ayame.ResourceError,
                                          regex):
                loader.load(ham, p)

        with self.assert_raises_regex(ayame.ResourceError,
                                      regex):
            loader.load(sys.modules[__name__], '.txt')

    def test_loader(self):
        class Loader(object):
            def get_data(self, path):
                with io.open(path) as fp:
                    return fp.read().strip() + ' from Loader'

        sys.modules[__name__] = self.new_module(Loader())

        class ResourceLoader(res.ResourceLoader):
            def load_from(self, loader, parent, path):
                return Resource(loader, os.path.join(parent, path))

        class Resource(res.FileResource):
            def __init__(self, loader, path):
                super(Resource, self).__init__(path)
                self._loader = loader

            def open(self):
                return io.StringIO(self._loader.get_data(path))

        loader = ResourceLoader()

        class Spam(object):
            pass

        def ham():
            pass

        path = self.path_for('Spam.txt')
        for o in (Spam, Spam()):
            for p in ('Spam.txt', '.txt'):
                r = loader.load(o, p)
                self.assert_is_instance(r, res.FileResource)
                self.assert_equal(r.path, path)
                self.assert_equal(r.mtime, os.path.getmtime(path))
                with r.open() as fp:
                    self.assert_equal(fp.read(), 'test_res/Spam.txt from Loader')

        path = self.path_for('ham.txt')
        for p in ('ham.txt', '.txt'):
            r = loader.load(ham, p)
            self.assert_is_instance(r, res.FileResource)
            self.assert_equal(r.path, path)
            self.assert_equal(r.mtime, os.path.getmtime(path))
            with r.open() as fp:
                self.assert_equal(fp.read(), 'test_res/ham.txt from Loader')


class FileResourceTestCase(AyameTestCase):

    regex = '^cannot load '

    def test_load_by_class(self):
        loader = res.ResourceLoader()
        path = self.path_for('Spam.txt')

        class Spam(object):
            pass

        class Eggs(object):
            pass

        for o in (Spam, Spam()):
            for p in ('Spam.txt', '.txt'):
                r = loader.load(o, p)
                self.assert_is_instance(r, res.FileResource)
                self.assert_equal(r.path, path)
                self.assert_equal(r.mtime, os.path.getmtime(path))
                with r.open() as fp:
                    self.assert_equal(fp.read().strip(), 'test_res/Spam.txt')

        for o in (Eggs, Eggs()):
            for p in ('Eggx.txt', '.txt'):
                with self.assert_raises_regex(ayame.ResourceError,
                                              self.regex):
                    loader.load(o, p)

    def test_load_by_function(self):
        loader = res.ResourceLoader()
        path = self.path_for('ham.txt')

        def ham():
            pass

        def toast():
            pass

        for p in ('ham.txt', '.txt'):
            r = loader.load(ham, p)
            self.assert_is_instance(r, res.FileResource)
            self.assert_equal(r.path, path)
            self.assert_equal(r.mtime, os.path.getmtime(path))
            with r.open() as fp:
                self.assert_equal(fp.read().strip(), 'test_res/ham.txt')

        for p in ('toast.txt', '.txt'):
            with self.assert_raises_regex(ayame.ResourceError,
                                          self.regex):
                loader.load(toast, p)

    def test_load_by_module(self):
        loader = res.ResourceLoader()
        path = self.path_for('.txt')

        r = loader.load(sys.modules[__name__], '.txt')
        self.assert_equal(r.path, path)
        self.assert_equal(r.mtime, os.path.getmtime(path))
        with r.open() as fp:
            self.assert_equal(fp.read().strip(), 'test_res/.txt')

        with self.assert_raises_regex(ayame.ResourceError,
                                      self.regex):
            loader.load(ayame, '.txt')


class ZipFileResourceTestCase(AyameTestCase):

    date_time = (2014, 1, 1, 0, 0, 0)
    mtime = time.mktime(datetime.datetime(*date_time).timetuple())
    regex = "^cannot load '.*' from loader "

    @contextlib.contextmanager
    def import_(self, name, files):
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as fp:
            with zipfile.ZipFile(fp, 'w') as zf:
                for n, s in files:
                    zi = zipfile.ZipInfo(n, date_time=self.date_time)
                    zf.writestr(zi, s)

        sys.path.append(fp.name)
        try:
            yield __import__(name)
        finally:
            sys.path.pop()
            del sys.modules[name]
            os.remove(fp.name)

    def test_load_by_class(self):
        loader = res.ResourceLoader()
        path = 'm/Spam.txt'
        src = """\
class Spam(object):
    pass

class Eggs(object):
    pass
"""

        with self.import_('m', [('m.py', src),
                                (path, path + '\n')]) as m:
            for o in (m.Spam, m.Spam()):
                for p in ('Spam.txt', '.txt'):
                    r = loader.load(o, p)
                    self.assert_is_instance(r, res.ZipFileResource)
                    self.assert_equal(r.path, path)
                    self.assert_equal(r.mtime, self.mtime)
                    with r.open() as fp:
                        self.assert_equal(fp.read().strip(), 'm/Spam.txt')

            for o in (m.Eggs, m.Eggs()):
                for p in ('Eggs.txt', '.txt'):
                    with self.assert_raises_regex(ayame.ResourceError,
                                                  self.regex):
                        loader.load(o, p)

    def test_load_by_function(self):
        loader = res.ResourceLoader()
        path = 'm/ham.txt'
        src = """\
def ham():
    pass

def toast():
    pass
"""

        with self.import_('m', [('m.py', src),
                                (path, path + '\n')]) as m:
            for p in ('ham.txt', '.txt'):
                r = loader.load(m.ham, p)
                self.assert_is_instance(r, res.ZipFileResource)
                self.assert_equal(r.mtime, self.mtime)
                with r.open() as fp:
                    self.assert_equal(fp.read().strip(), 'm/ham.txt')

            for p in ('toast.txt', '.txt'):
                with self.assert_raises_regex(ayame.ResourceError,
                                              self.regex):
                    loader.load(m.toast, p)

    def test_load_by_module(self):
        loader = res.ResourceLoader()
        path = 'm/.txt'

        with self.import_('m', [('m.py', ''),
                                (path, path + '\n')]) as m:
            r = loader.load(m, '.txt')
            with r.open() as fp:
                self.assert_equal(fp.read().strip(), 'm/.txt')

        with self.import_('m', [('m.py', '')]) as m:
            with self.assert_raises_regex(ayame.ResourceError,
                                          self.regex):
                loader.load(m, '.txt')
