#
# test_link
#
#   Copyright (c) 2012-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import ayame
from ayame import http, link, markup, uri
from base import AyameTestCase


class LinkTestCase(AyameTestCase):

    def setup(self):
        super(LinkTestCase, self).setup()
        self.app = ayame.Ayame(__name__)

    def test_link_href(self):
        a = markup.Element(link._A)
        with self.application():
            l = link.Link('a')
            l.render(a)
        self.assert_equal(a.attrib, {})
        self.assert_equal(a.children, [])

        a = markup.Element(link._A,
                           attrib={link._HREF: None})
        with self.application():
            l = link.Link('a')
            l.render(a)
        self.assert_equal(a.attrib, {})
        self.assert_equal(a.children, [])

        a = markup.Element(link._A,
                           attrib={link._HREF: '/spam'})
        with self.application():
            l = link.Link('a')
            l.render(a)
        self.assert_equal(a.attrib, {link._HREF: '/spam'})
        self.assert_equal(a.children, [])

    def test_link_src(self):
        script = markup.Element(link._SCRIPT)
        with self.application():
            l = link.Link('a')
            l.render(script)
        self.assert_equal(script.attrib, {})
        self.assert_equal(script.children, [])

        script = markup.Element(link._SCRIPT,
                                attrib={link._SRC: None})
        with self.application():
            l = link.Link('a')
            l.render(script)
        self.assert_equal(script.attrib, {})
        self.assert_equal(script.children, [])

        script = markup.Element(link._SCRIPT,
                                attrib={link._SRC: '/spam'})
        with self.application():
            l = link.Link('a')
            l.render(script)
        self.assert_equal(script.attrib, {link._SRC: '/spam'})
        self.assert_equal(script.children, [])

    def test_link_replace_children(self):
        a = markup.Element(link._A)
        with self.application():
            l = link.Link('a', 'spam')
            l.render(a)
        self.assert_equal(a.attrib, {})
        self.assert_equal(a.children, ['spam'])

    def test_link_unknown(self):
        div = markup.Element(markup.DIV)
        with self.application():
            l = link.Link('a', 'spam')
            l.render(div)
        self.assert_equal(div.attrib, {})
        self.assert_equal(div.children, ['spam'])

    def test_action_link(self):
        map = self.app.config['ayame.route.map']
        map.connect('/', SpamPage)

        with self.application(self.new_environ()):
            p = SpamPage()
            status, headers, content = p()
        html = self.format(SpamPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assert_equal(content, [html])

    def test_action_link_fire(self):
        query = '{path}=link'
        with self.application(self.new_environ(query=query)):
            p = SpamPage()
            with self.assert_raises(Clicked):
                p()

    def test_page_link(self):
        map = self.app.config['ayame.route.map']
        map.connect('/<y:int>', SpamPage)
        map.connect('/', SpamPage)

        a = markup.Element(link._A)
        with self.application(self.new_environ()):
            l = link.PageLink('a', SpamPage)
            l.render(a)
        self.assert_equal(a.attrib, {link._HREF: '/'})

        a = markup.Element(link._A)
        with self.application(self.new_environ()):
            l = link.PageLink('a', SpamPage, {'a': ['1', '2']})
            l.render(a)
        self.assert_equal(a.attrib, {link._HREF: '/?a=1&a=2'})

        a = markup.Element(link._A)
        with self.application(self.new_environ()):
            l = link.PageLink('a', SpamPage, {'y': 2012})
            l.render(a)
        self.assert_equal(a.attrib, {link._HREF: '/2012'})

        a = markup.Element(link._A)
        with self.application(self.new_environ()):
            l = link.PageLink('a', SpamPage, {'y': 2012, 'a': ['1', '2']})
            l.render(a)
        self.assert_equal(a.attrib, {link._HREF: '/2012?a=1&a=2'})

    def test_page_link_error(self):
        with self.application(self.new_environ()):
            with self.assert_raises_regex(ayame.ComponentError, r' not .* subclass of Page\b'):
                link.PageLink('a', object)


class SpamPage(ayame.Page):

    html_t = """\
<?xml version="1.0"?>
{doctype}
<html xmlns="{xhtml}">
  <head>
    <title>SpamPage</title>
  </head>
  <body>
    <a href="http://localhost/?{query}">_</a>
  </body>
</html>
"""
    kwargs = {
        'query': uri.quote('{}=link'.format(ayame.AYAME_PATH), '/=')
    }

    def __init__(self):
        super(SpamPage, self).__init__()
        self.add(ActionLink('link'))


class ActionLink(link.ActionLink):

    def on_click(self):
        super(ActionLink, self).on_click()
        raise Clicked()


class Clicked(Exception):
    pass
