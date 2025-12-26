#
# test_local
#
#   Copyright (c) 2012-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import ayame
from ayame import app as am, local
from base import AyameTestCase


class LocalTestCase(AyameTestCase):

    def test_empty(self):
        self.assertIsNone(local.pop())

        with self.assertRaises(ayame.AyameError):
            local.context()
        with self.assertRaises(ayame.AyameError):
            local.app()

    def test_push(self):
        app = am.Ayame(__name__)
        environ = {}

        ctx = local.push(app, environ)
        self.assertIs(ctx.app, app)
        self.assertIs(ctx.environ, environ)

        self.assertIs(local.context(), ctx)
        self.assertIs(local.app(), ctx.app)
        self.assertIs(local.pop(), ctx)

        self.assertIsNone(local.pop())

        with self.assertRaises(ayame.AyameError):
            local.context()
        with self.assertRaises(ayame.AyameError):
            local.app()
