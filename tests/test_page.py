#
# test_page
#
#   Copyright (c) 2012-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from ayame import http, page
from base import AyameTestCase


class PageTestCase(AyameTestCase):

    def test_http_302(self):
        location = 'http://localhost/'
        with self.application(self.new_environ()):
            p = page.HTTPStatusPage(http.Found(location))
            status, headers, content = p()
        self.assert_equal(status, http.Found.status)
        self.assert_equal(headers, [
            ('Location', location),
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', '931'),
        ])
        self.assert_true(content)
        self.assert_regex(content[0], br'<p>.*</p>')

    def test_http_304(self):
        with self.application(self.new_environ()):
            p = page.HTTPStatusPage(http.NotModified())
            status, headers, content = p()
        self.assert_equal(status, http.NotModified.status)
        self.assert_equal(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', '852'),
        ])
        self.assert_true(content)
        self.assert_not_in(b'<p>', content[0])
