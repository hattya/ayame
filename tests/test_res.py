#
# test_res
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import contextlib
import datetime
import importlib.util
import io
import os
import sys
import tempfile
import textwrap
import time
import types
import zipfile

import ayame
from ayame import res
from base import AyameTestCase


class ResTestCase(AyameTestCase):

    def setUp(self):
        self._module = sys.modules[__name__]

    def tearDown(self):
        sys.modules[__name__] = self._module

    def new_module(self, loader):
        class Module(types.ModuleType):
            def __init__(self):
                super().__init__(__name__)
                self.__file__ = __file__
                self.__spec__ = importlib.util.spec_from_loader(__name__, loader,
                                                                origin=__spec__.origin)

        return Module()

    def test_resource(self):
        class Resource(res.Resource):
            def open(self, encoding='utf-8'):
                return super().open(encoding)

        with self.assertRaises(TypeError):
            res.Resource(None)

        r = Resource(None)
        self.assertIsNone(r.path)
        self.assertIsNone(r.mtime)
        self.assertIsNone(r.open())

    def test_unknown_module(self):
        loader = res.ResourceLoader()

        class Spam:
            pass

        def ham():
            pass

        for o in (Spam, Spam(), ham):
            o.__module__ = None
            with self.subTest(object=o):
                with self.assertRaisesRegex(ayame.ResourceError, r'^cannot find module '):
                    loader.load(o, None)

    def test_unknown_module_location(self):
        sys.modules[__name__] = types.ModuleType(__name__)
        self._test_error(r" module location$")

    def test_invalid_path(self):
        loader = res.ResourceLoader()

        class Spam:
            pass

        def ham():
            pass

        for o in (Spam, Spam(), ham, sys.modules[__name__]):
            for p in (os.path.pardir, os.path.join(*(os.path.pardir,) * 2), os.path.sep):
                with self.subTest(object=o, path=p):
                    with self.assertRaisesRegex(ayame.ResourceError, r'^invalid path '):
                        loader.load(o, p)

    def test_unknown_loader(self):
        sys.modules[__name__] = self.new_module(True)
        self._test_error(r"^cannot load '.*' from loader True$")

    def _test_error(self, regex):
        loader = res.ResourceLoader()

        class Spam:
            pass

        def ham():
            pass

        for o in (Spam, Spam()):
            for p in ('Spam.txt', '.txt'):
                with self.subTest(object=o, path=p):
                    with self.assertRaisesRegex(ayame.ResourceError, regex):
                        loader.load(o, p)

        for p in ('ham.txt', '.txt'):
            with self.subTest(path=p):
                with self.assertRaisesRegex(ayame.ResourceError, regex):
                    loader.load(ham, p)

        with self.assertRaisesRegex(ayame.ResourceError, regex):
            loader.load(sys.modules[__name__], '.txt')

    def test_loader(self):
        class Loader:
            def get_data(self, path):
                with open(path) as fp:
                    return fp.read().strip() + ' from Loader'

        sys.modules[__name__] = self.new_module(Loader())

        class ResourceLoader(res.ResourceLoader):
            def load_from(self, loader, parent, path):
                return Resource(loader, os.path.join(parent, path))

        class Resource(res.FileResource):
            def __init__(self, loader, path):
                super().__init__(path)
                self._loader = loader

            def open(self):
                return io.StringIO(self._loader.get_data(path))

        loader = ResourceLoader()

        class Spam:
            pass

        def ham():
            pass

        path = self.path_for('Spam.txt')
        for o in (Spam, Spam()):
            for p in ('Spam.txt', '.txt'):
                with self.subTest(object=o, path=p):
                    r = loader.load(o, p)
                    self.assertIsInstance(r, res.FileResource)
                    self.assertEqual(r.path, path)
                    self.assertEqual(r.mtime, os.path.getmtime(path))
                    with r.open() as fp:
                        self.assertEqual(fp.read(), 'test_res/Spam.txt from Loader')

        path = self.path_for('ham.txt')
        for p in ('ham.txt', '.txt'):
            with self.subTest(path=p):
                r = loader.load(ham, p)
                self.assertIsInstance(r, res.FileResource)
                self.assertEqual(r.path, path)
                self.assertEqual(r.mtime, os.path.getmtime(path))
                with r.open() as fp:
                    self.assertEqual(fp.read(), 'test_res/ham.txt from Loader')


class FileResourceTestCase(AyameTestCase):

    regex = r'^cannot load '

    def test_load_by_class(self):
        loader = res.ResourceLoader()
        path = self.path_for('Spam.txt')

        class Spam:
            pass

        class Eggs:
            pass

        for o in (Spam, Spam()):
            for p in ('Spam.txt', '.txt'):
                with self.subTest(object=o, path=p):
                    r = loader.load(o, p)
                    self.assertIsInstance(r, res.FileResource)
                    self.assertEqual(r.path, path)
                    self.assertEqual(r.mtime, os.path.getmtime(path))
                    with r.open() as fp:
                        self.assertEqual(fp.read().strip(), 'test_res/Spam.txt')

        for o in (Eggs, Eggs()):
            for p in ('Eggx.txt', '.txt'):
                with self.subTest(object=o, path=p):
                    with self.assertRaisesRegex(ayame.ResourceError, self.regex):
                        loader.load(o, p)

    def test_load_by_function(self):
        loader = res.ResourceLoader()
        path = self.path_for('ham.txt')

        def ham():
            pass

        def toast():
            pass

        for p in ('ham.txt', '.txt'):
            with self.subTest(path=p):
                r = loader.load(ham, p)
                self.assertIsInstance(r, res.FileResource)
                self.assertEqual(r.path, path)
                self.assertEqual(r.mtime, os.path.getmtime(path))
                with r.open() as fp:
                    self.assertEqual(fp.read().strip(), 'test_res/ham.txt')

        for p in ('toast.txt', '.txt'):
            with self.subTest(path=p):
                with self.assertRaisesRegex(ayame.ResourceError, self.regex):
                    loader.load(toast, p)

    def test_load_by_module(self):
        loader = res.ResourceLoader()
        path = self.path_for('.txt')

        r = loader.load(sys.modules[__name__], '.txt')
        self.assertEqual(r.path, path)
        self.assertEqual(r.mtime, os.path.getmtime(path))
        with r.open() as fp:
            self.assertEqual(fp.read().strip(), 'test_res/.txt')

        with self.assertRaisesRegex(ayame.ResourceError, self.regex):
            loader.load(ayame, '.txt')


class ZipFileResourceTestCase(AyameTestCase):

    date_time = (2014, 1, 1, 0, 0, 0)
    mtime = time.mktime(datetime.datetime(*date_time).timetuple())
    regex = r"^cannot load '.*' from loader "

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
        src = textwrap.dedent("""\
            class Spam:
                pass

            class Eggs:
                pass
        """)

        with self.import_('m', [('m.py', src),
                                (path, path + '\n')]) as m:
            for o in (m.Spam, m.Spam()):
                for p in ('Spam.txt', '.txt'):
                    with self.subTest(object=o, path=p):
                        r = loader.load(o, p)
                        self.assertIsInstance(r, res.ZipFileResource)
                        self.assertEqual(r.path, path)
                        self.assertEqual(r.mtime, self.mtime)
                        with r.open() as fp:
                            self.assertEqual(fp.read().strip(), 'm/Spam.txt')

            for o in (m.Eggs, m.Eggs()):
                for p in ('Eggs.txt', '.txt'):
                    with self.subTest(object=o, path=p):
                        with self.assertRaisesRegex(ayame.ResourceError, self.regex):
                            loader.load(o, p)

    def test_load_by_function(self):
        loader = res.ResourceLoader()
        path = 'm/ham.txt'
        src = textwrap.dedent("""\
            def ham():
                pass

            def toast():
                pass
        """)

        with self.import_('m', [('m.py', src),
                                (path, path + '\n')]) as m:
            for p in ('ham.txt', '.txt'):
                with self.subTest(path=p):
                    r = loader.load(m.ham, p)
                    self.assertIsInstance(r, res.ZipFileResource)
                    self.assertEqual(r.mtime, self.mtime)
                    with r.open() as fp:
                        self.assertEqual(fp.read().strip(), 'm/ham.txt')

            for p in ('toast.txt', '.txt'):
                with self.subTest(path=p):
                    with self.assertRaisesRegex(ayame.ResourceError, self.regex):
                        loader.load(m.toast, p)

    def test_load_by_module(self):
        loader = res.ResourceLoader()
        path = 'm/.txt'

        with self.import_('m', [('m.py', ''),
                                (path, path + '\n')]) as m:
            r = loader.load(m, '.txt')
            with r.open() as fp:
                self.assertEqual(fp.read().strip(), 'm/.txt')

        with self.import_('m', [('m.py', '')]) as m:
            with self.assertRaisesRegex(ayame.ResourceError, self.regex):
                loader.load(m, '.txt')
