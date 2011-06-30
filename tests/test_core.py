#
# test_core
#
#   Copyright (c) 2011 Akinori Hattori <hattya@gmail.com>
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

import os
import wsgiref.util

from nose.tools import eq_, ok_

from ayame import core


def test_simple_app():
    aym = core.Ayame(__name__)
    eq_(aym._name, __name__)
    eq_(aym._root, os.path.dirname(__file__))

    map = aym.config['ayame.route.map']
    map.connect('/', 0)
    status, headers, exc_info, data = wsgi_call(aym.make_app())
    eq_(status, '200 OK')
    eq_(headers, [('Content-Type', 'text/plain;charset=UTF-8')])
    eq_(exc_info, None)
    eq_(data, [])

def wsgi_call(application, **kwargs):
    environ = {}
    var = {}
    def start_response(status, headers, exc_info=None):
        var.update(status=status, headers=headers, exc_info=exc_info)
    wsgiref.util.setup_testing_defaults(environ)
    data = application(environ, start_response)
    return var['status'], var['headers'], var['exc_info'], data
