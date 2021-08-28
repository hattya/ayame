#! /usr/bin/env python
#
# setup.py -- ayame setup script
#

from __future__ import print_function
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
        PATH = (path or os.environ['PATH']).split(os.path.pathsep)
    except KeyError:
        raise SystemExit('PATH environment variable is not set')
    name, ext = os.path.splitext(cmd)
    cands = []
    if (not ext
        and sys.platform == 'win32'):
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
    mark = '.'
    out = runcmd([whence('git'), 'describe', '--tags', '--dirty=' + mark, '--long', '--always'], env)
    v = out.strip().rsplit('-', 2)
    if len(v) == 3:
        v[0] = v[0][1:]
        v[2] = v[2][1:]
        if v[1] == '0':
            version = v[0]
            if v[2].endswith(mark):
                mark = '+'
                version += mark
        else:
            version = '{}.{}+{}'.format(*v)
    elif v[0]:
        out = runcmd([whence('git'), 'rev-list', 'HEAD'], env)
        if out:
            version = '0.0.{}+{}'.format(str(len(out.splitlines())), v[0])
    if version.endswith(mark):
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
else:
    version = 'unknown'
    try:
        with open('ayame/__version__.py') as fp:
            for l in fp:
                if l.startswith('version = '):
                    version = l.split('=', 2)[1].strip("\n '")
                    break
    except (OSError, IOError):
        pass


class test(Command):

    description = 'run unit tests'
    user_options = [('failfast', 'f', 'stop on first fail or error')]

    boolean_options = ['failfast']

    def initialize_options(self):
        self.failfast = False

    def finalize_options(self):
        pass

    def run(self):
        import unittest

        if setuptools:
            if self.distribution.install_requires:
                self.distribution.fetch_build_eggs(self.distribution.install_requires)
            if self.distribution.tests_require:
                self.distribution.fetch_build_eggs(self.distribution.tests_require)
            self.run_command('egg_info')
        # run unittest discover
        argv = [sys.argv[0], 'discover', '--start-directory', 'tests']
        if self.verbose:
            argv.append('--verbose')
        if self.failfast:
            argv.append('--failfast')
        unittest.main(None, argv=argv)


try:
    with open('README.rst') as fp:
        long_description = fp.read()
except (OSError, IOError):
    long_description = ''

packages = ['ayame']
package_data = {
    'ayame': ['*/*.html'],
}

cmdclass = {
    'test': test
}

kwargs = {}
if setuptools:
    kwargs.update(install_requires=['Werkzeug < 0.15'])

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
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
          'Topic :: Internet :: WWW/HTTP :: WSGI',
          'Topic :: Software Development :: Libraries :: Application Frameworks',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      cmdclass=cmdclass,
      **kwargs)
