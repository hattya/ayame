#
# ayame.page
#
#   Copyright (c) 2012-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
from . import basic, core
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import http


__all__ = ['HTTPStatusPage']


class HTTPStatusPage(core.Page):

    def __init__(self, error: http.HTTPStatus) -> None:
        super().__init__()
        self._error = error
        self.status = error.status
        for n, v in error.headers:
            self.headers[n] = v

        self.add(basic.Label('status', error.status))
        self.add(basic.Label('reason', error.reason))
        label = basic.Label('description', error.description)
        label.escape_model_string = False
        label.visible = bool(label.model_object)
        self.add(label)
