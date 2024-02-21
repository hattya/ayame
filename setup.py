#! /usr/bin/env python
#
# setup.py -- ayame setup script
#

import os
import sys

from setuptools import setup, Command


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

        # run unittest discover
        argv = [sys.argv[0], 'discover', '--start-directory', 'tests']
        if self.verbose:
            argv.append('--verbose')
        if self.failfast:
            argv.append('--failfast')
        unittest.main(None, argv=argv)


setup(
    cmdclass={
        'test': test,
    },
    scmver={
        'root': os.path.dirname(os.path.abspath(__file__)),
        'spec': 'micro',
        'write_to': os.path.join('ayame', '__version__.py'),
        'fallback': ['__version__:version', 'ayame'],
    },
)
