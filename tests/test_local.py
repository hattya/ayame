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
        self.assert_is_none(local.pop())

        with self.assert_raises(ayame.AyameError):
            local.context()
        with self.assert_raises(ayame.AyameError):
            local.app()

    def test_push(self):
        ctx = local.push(0, 1)
        self.assert_equal(ctx.app, 0)
        self.assert_equal(ctx.environ, 1)
        self.assert_is_none(ctx.request)
        self.assert_is_none(ctx._router)

        self.assert_is(local.context(), ctx)
        self.assert_is(local.app(), ctx.app)
        self.assert_is(local.pop(), ctx)

        self.assert_is_none(local.pop())

        with self.assert_raises(ayame.AyameError):
            local.context()
        with self.assert_raises(ayame.AyameError):
            local.app()
