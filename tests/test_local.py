#
# test_local
#
#   Copyright (c) 2012-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import ayame
from ayame import local
from base import AyameTestCase


class LocalTestCase(AyameTestCase):

    def test_empty(self):
        self.assertIsNone(local.pop())

        with self.assertRaises(ayame.AyameError):
            local.context()
        with self.assertRaises(ayame.AyameError):
            local.app()

    def test_push(self):
        ctx = local.push(0, 1)
        self.assertEqual(ctx.app, 0)
        self.assertEqual(ctx.environ, 1)
        self.assertIsNone(ctx.request)
        self.assertIsNone(ctx._router)

        self.assertIs(local.context(), ctx)
        self.assertIs(local.app(), ctx.app)
        self.assertIs(local.pop(), ctx)

        self.assertIsNone(local.pop())

        with self.assertRaises(ayame.AyameError):
            local.context()
        with self.assertRaises(ayame.AyameError):
            local.app()
