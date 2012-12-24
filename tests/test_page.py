#
# test_page
#
#   Copyright (c) 2012 Akinori Hattori <hattya@gmail.com>
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

from contextlib import contextmanager

from nose.tools import eq_, ok_

from ayame import http, local
from ayame import app as _app
from ayame import page as _page


@contextmanager
def application(environ=None):
    app = _app.Ayame(__name__)
    try:
        ctx = local.push(app, environ)
        yield
    finally:
        local.pop()


def test_http_status_page():
    location = 'http://localhost/'
    with application():
        page = _page.HTTPStatusPage(http.Found(location))
        status, headers, content = page.render()
    eq_(status, http.Found.status)
    eq_(headers, [('Location', location),
                  ('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', '930')])
    ok_(content)
