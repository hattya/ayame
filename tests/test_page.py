#
# test_page
#
#   Copyright (c) 2012-2015 Akinori Hattori <hattya@gmail.com>
#
#   Permission is hereby granted, free of charge, to any person
#   obtaining a copy of this software and associated documentation files
#   (the "Software"), to deal in the Software without restriction,
#   including without limitation the rights to use, copy, modify, merge,
#   publish, distribute, sublicense, and/or sell copies of the Software,
#   and to permit persons to whom the Software is furnished to do so,
#   subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be
#   included in all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
#   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#   ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#   CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
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
        self.assert_equal(headers,
                          [('Location', location),
                           ('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', '931')])
        self.assert_true(content)
        self.assert_regex(content[0], b'<p>.*</p>')

    def test_http_304(self):
        with self.application(self.new_environ()):
            p = page.HTTPStatusPage(http.NotModified())
            status, headers, content = p()
        self.assert_equal(status, http.NotModified.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', '852')])
        self.assert_true(content)
        self.assert_not_in(b'<p>', content[0])
