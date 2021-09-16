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
        self.assertEqual(status, http.Found.status)
        self.assertEqual(headers, [
            ('Location', location),
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', '931'),
        ])
        self.assertTrue(content)
        self.assertRegex(content[0], br'<p>.*</p>')

    def test_http_304(self):
        with self.application(self.new_environ()):
            p = page.HTTPStatusPage(http.NotModified())
            status, headers, content = p()
        self.assertEqual(status, http.NotModified.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', '852'),
        ])
        self.assertTrue(content)
        self.assertNotIn(b'<p>', content[0])
