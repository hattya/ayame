#! /usr/bin/env python
#
# setup.py -- ayame setup script
#

from __future__ import print_function
try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    from distutils.command.build_py import build_py
from distutils.command.clean import clean as _clean
from distutils.dir_util import remove_tree
try:
    from distutils.util import Mixin2to3
except ImportError:
    class Mixin2to3:
        def run_2to3(self, files):
            pass
import imp
import os
import subprocess
import sys
import time

try:
    from setuptools import setup, Command
    setuptools = True
except ImportError:
    from distutils.core import setup, Command
    setuptools = False


def whence(cmd, path=None):
    try:
        PATH = (path or os.environ['PATH']).split(os.pathsep)
    except KeyError:
        raise SystemExit('PATH environment variable is not set')
    name, ext = os.path.splitext(cmd)
    cands = []
    if (not ext and
        sys.platform == 'win32'):
        cands.extend(name + ext for ext in ('.exe', '.bat', '.cmd'))
    else:
        cands.append(cmd)
    for path in PATH:
        for cand in cands:
            cmd = os.path.join(path, cand)
            if os.path.isfile(cmd):
                return cmd


def runcmd(argv, env):
    proc = subprocess.Popen(argv,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            env=env,
                            universal_newlines=True)
    out, err = proc.communicate()
    return '' if err else out


version = ''

if os.path.isdir('.git'):
    env = {'LANGUAGE': 'C'}
    if 'SystemRoot' in os.environ:
        env['SystemRoot'] = os.environ['SystemRoot']
    out = runcmd([whence('git'), 'describe', '--tags',
                  '--dirty=+', '--long', '--always'],
                 env)
    v = out.strip().rsplit('-', 2)
    if len(v) == 3:
        v[0] = v[0][1:]
        v[2] = v[2][1:]
        if v[1] == '0':
            version = v[0]
            if v[2].endswith('+'):
                version += '+'
        else:
            version = '{}.{}-{}'.format(*v)
    elif v[0]:
        out = runcmd([whence('git'), 'rev-list', 'HEAD'], env)
        if out:
            version = '0.0.{}-{}'.format(str(len(out.splitlines())), v[0])
    if version.endswith('+'):
        version += time.strftime('%Y-%m-%d')

if version:
    with open('ayame/__version__.py', 'w') as fp:
        def print_(*args):
            print(*args, file=fp)

        print_('#')
        print_('# ayame.__version__')
        print_('#')
        print_('# this file is automatically generated by setup.py')
        print_('')
        print_("version = '{}'".format(version))

try:
    fp, path, desc = imp.find_module('__version__', [os.path.abspath('ayame')])
    with fp:
        v = imp.load_module('__version__', fp, path, desc)
        version = v.version
except (AttributeError, ImportError):
    version = 'unknown'


class clean(_clean):

    def initialize_options(self):
        _clean.initialize_options(self)
        self.build_tests = None

    def finalize_options(self):
        _clean.finalize_options(self)
        self.set_undefined_options('test', ('build_tests', 'build_tests'))

    def run(self):
        if os.path.exists(self.build_tests):
            remove_tree(self.build_tests)
        _clean.run(self)


class test(Command, Mixin2to3):

    description = 'run unit tests'
    user_options = [('build-tests=', 'd', 'directory to "test" (copy) to')]

    def initialize_options(self):
        self.build_base = None
        self.build_lib = None
        self.build_tests = None

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_base', 'build_base'),
                                   ('build_lib', 'build_lib'))
        if self.build_tests is None:
            self.build_tests = os.path.join(self.build_base, 'tests')

    def run(self):
        import unittest

        if setuptools:
            if self.distribution.install_requires:
                self.distribution.fetch_build_eggs(
                    self.distribution.install_requires)
            if self.distribution.tests_require:
                self.distribution.fetch_build_eggs(
                    self.distribution.tests_require)
            self.run_command('egg_info')

        self.run_command('build')
        # load modules from build-lib
        sys.path.insert(0, os.path.abspath(self.build_lib))
        # 2to3
        test_files = []
        for root, dirs, files in os.walk('tests'):
            if '__pycache__' in dirs:
                dirs.remove('__pycache__')
            self.mkpath(os.path.join(self.build_base, root))
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext not in ('.py', '.html', '.properties', '.txt', '.htm',
                               ''):
                    continue
                path = os.path.join(root, f)
                rv = self.copy_file(path, os.path.join(self.build_base, path))
                if (rv[1] and
                    ext == '.py'):
                    test_files.append(rv[0])
        self.run_2to3(test_files)
        # run unittest discover
        argv = [sys.argv[0], 'discover', '--start-directory', self.build_tests]
        if self.verbose:
            argv.append('--verbose')
        unittest.main(None, argv=argv)


try:
    with open('README.rst') as fp:
        long_description = fp.read()
except:
    long_description = ''

packages = ['ayame']
package_data = {'ayame': ['*/*.html']}

cmdclass = {'build_py': build_py,
            'clean': clean,
            'test': test}

kwargs = {}
if setuptools:
    kwargs.update(zip_safe=False,
                  install_requires=['Beaker'])

setup(name='ayame',
      version=version,
      description='An Apache Wicket-like component based WSGI framework',
      long_description=long_description,
      author='Akinori Hattori',
      author_email='hattya@gmail.com',
      url='https://github.com/hattya/ayame',
      license='MIT',
      packages=packages,
      package_data=package_data,
      classifiers=(
          'Development Status :: 3 - Alpha',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Topic :: Internet :: WWW/HTTP',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
          'Topic :: Internet :: WWW/HTTP :: WSGI',
          'Topic :: Software Development :: Libraries :: Application Frameworks',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ),
      cmdclass=cmdclass,
      **kwargs)
