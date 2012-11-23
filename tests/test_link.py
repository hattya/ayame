#
# test_link
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
import io
import os
import urllib

from nose.tools import assert_raises, eq_

from ayame import core, http, link, markup, uri
from ayame.exception import ComponentError


@contextmanager
def application(app, environ=None):
    local = core._local
    if environ is None:
        environ = {'REQUEST_METHOD': 'GET'}
    try:
        local.app = app
        local.environ = environ
        local.request = core.Request(environ, {})
        local._router = app.config['ayame.route.map'].bind(environ)
        yield
    finally:
        local._router = None
        local.request = None
        local.environ = None
        local.app = None

def test_link():
    app = core.Ayame(__name__)
    eq_(app._name, __name__)
    eq_(app._root, os.path.dirname(__file__))

    # href attribute
    element = markup.Element(link._A)
    with application(app):
        lnk = link.Link('a')
        lnk.render(element)
    eq_(element.attrib, {})
    eq_(element.children, [])

    element = markup.Element(link._A)
    element.attrib[link._HREF] = None
    with application(app):
        lnk = link.Link('a')
        lnk.render(element)
    eq_(element.attrib, {})
    eq_(element.children, [])

    element = markup.Element(link._A)
    element.attrib[link._HREF] = '/spam'
    with application(app):
        l = link.Link('a')
        l.render(element)
    eq_(element.attrib, {link._HREF: '/spam'})
    eq_(element.children, [])

    # replace children by model object
    element = markup.Element(link._A)
    with application(app):
        lnk = link.Link('a', 'spam')
        lnk.render(element)
    eq_(element.attrib, {})
    eq_(element.children, ['spam'])

    # src attribute
    element = markup.Element(link._SCRIPT)
    with application(app):
        l = link.Link('a')
        l.render(element)
    eq_(element.attrib, {})
    eq_(element.children, [])

def test_action_link():
    class SpamPage(core.Page):
        def __init__(self):
            super(SpamPage, self).__init__()
            self.add(ActionLink('link'))

    class ActionLink(link.ActionLink):
        def on_click(self):
            super(ActionLink, self).on_click()
            raise OK()

    class OK(Exception):
        pass

    query = {core.AYAME_PATH: 'link'}
    xhtml = ('<?xml version="1.0"?>\n'
             '{doctype}\n'
             '<html xmlns="{xhtml}">\n'
             '  <head>\n'
             '    <title>SpamPage</title>\n'
             '  </head>\n'
             '  <body>\n'
             '    <a href="http://localhost/?{query}">_</a>\n'
             '  </body>\n'
             '</html>\n').format(doctype=markup.XHTML1_STRICT,
                                 xhtml=markup.XHTML_NS,
                                 query=urllib.urlencode(query))
    xhtml = xhtml.encode('utf-8')

    app = core.Ayame(__name__)
    eq_(app._name, __name__)
    eq_(app._root, os.path.dirname(__file__))

    map = app.config['ayame.route.map']
    map.connect('/', SpamPage)

    query = ''
    environ = {'wsgi.url_scheme': 'http',
               'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET',
               'HTTP_HOST': 'localhost',
               'SCRIPT_NAME': '',
               'PATH_INFO': '',
               'QUERY_STRING': uri.quote(query)}
    with application(app, environ):
        page = SpamPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)

    query = '{}=link'.format(core.AYAME_PATH)
    environ = {'wsgi.url_scheme': 'http',
               'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET',
               'HTTP_HOST': 'localhost',
               'SCRIPT_NAME': '',
               'PATH_INFO': '',
               'QUERY_STRING': uri.quote(query)}
    with application(app, environ):
        page = SpamPage()
        assert_raises(OK, page.render)

def test_page_link():
    class SpamPage(core.Page):
        pass

    app = core.Ayame(__name__)
    eq_(app._name, __name__)
    eq_(app._root, os.path.dirname(__file__))

    map = app.config['ayame.route.map']
    map.connect('/<int:y>', SpamPage)
    map.connect('/', SpamPage)

    element = markup.Element(link._A)
    with application(app):
        l = link.PageLink('a', SpamPage)
        l.render(element)
    eq_(element.attrib, {link._HREF: '/'})

    element = markup.Element(link._A)
    with application(app):
        l = link.PageLink('a', SpamPage, {'a': ['1', '2']})
        l.render(element)
    eq_(element.attrib, {link._HREF: '/?a=1&a=2'})

    element = markup.Element(link._A)
    with application(app):
        l = link.PageLink('a', SpamPage, {'y': 2012, 'a': '1'})
        l.render(element)
    eq_(element.attrib, {link._HREF: '/2012?a=1'})

    # error
    element = markup.Element(link._A)
    with application(app):
        assert_raises(ComponentError, link.PageLink, 'a', object)
