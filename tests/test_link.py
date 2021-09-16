#
# test_link
#
#   Copyright (c) 2012-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import textwrap

import ayame
from ayame import http, link, markup, uri
from base import AyameTestCase


class LinkTestCase(AyameTestCase):

    def setUp(self):
        self.app = ayame.Ayame(__name__)

    def test_link_href(self):
        a = markup.Element(link._A)
        with self.application():
            l = link.Link('a')
            l.render(a)
        self.assertEqual(a.attrib, {})
        self.assertEqual(a.children, [])

        a = markup.Element(link._A,
                           attrib={link._HREF: None})
        with self.application():
            l = link.Link('a')
            l.render(a)
        self.assertEqual(a.attrib, {})
        self.assertEqual(a.children, [])

        a = markup.Element(link._A,
                           attrib={link._HREF: '/spam'})
        with self.application():
            l = link.Link('a')
            l.render(a)
        self.assertEqual(a.attrib, {link._HREF: '/spam'})
        self.assertEqual(a.children, [])

    def test_link_src(self):
        script = markup.Element(link._SCRIPT)
        with self.application():
            l = link.Link('a')
            l.render(script)
        self.assertEqual(script.attrib, {})
        self.assertEqual(script.children, [])

        script = markup.Element(link._SCRIPT,
                                attrib={link._SRC: None})
        with self.application():
            l = link.Link('a')
            l.render(script)
        self.assertEqual(script.attrib, {})
        self.assertEqual(script.children, [])

        script = markup.Element(link._SCRIPT,
                                attrib={link._SRC: '/spam'})
        with self.application():
            l = link.Link('a')
            l.render(script)
        self.assertEqual(script.attrib, {link._SRC: '/spam'})
        self.assertEqual(script.children, [])

    def test_link_replace_children(self):
        a = markup.Element(link._A)
        with self.application():
            l = link.Link('a', 'spam')
            l.render(a)
        self.assertEqual(a.attrib, {})
        self.assertEqual(a.children, ['spam'])

    def test_link_unknown(self):
        div = markup.Element(markup.DIV)
        with self.application():
            l = link.Link('a', 'spam')
            l.render(div)
        self.assertEqual(div.attrib, {})
        self.assertEqual(div.children, ['spam'])

    def test_action_link(self):
        map = self.app.config['ayame.route.map']
        map.connect('/', SpamPage)

        with self.application(self.new_environ()):
            p = SpamPage()
            status, headers, content = p()
        html = self.format(SpamPage)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

    def test_action_link_fire(self):
        query = '{path}=link'
        with self.application(self.new_environ(query=query)):
            p = SpamPage()
            with self.assertRaises(Clicked):
                p()

    def test_page_link(self):
        map = self.app.config['ayame.route.map']
        map.connect('/<y:int>', SpamPage)
        map.connect('/', SpamPage)

        a = markup.Element(link._A)
        with self.application(self.new_environ()):
            l = link.PageLink('a', SpamPage)
            l.render(a)
        self.assertEqual(a.attrib, {link._HREF: '/'})

        a = markup.Element(link._A)
        with self.application(self.new_environ()):
            l = link.PageLink('a', SpamPage, {'a': ['1', '2']})
            l.render(a)
        self.assertEqual(a.attrib, {link._HREF: '/?a=1&a=2'})

        a = markup.Element(link._A)
        with self.application(self.new_environ()):
            l = link.PageLink('a', SpamPage, {'y': 2012})
            l.render(a)
        self.assertEqual(a.attrib, {link._HREF: '/2012'})

        a = markup.Element(link._A)
        with self.application(self.new_environ()):
            l = link.PageLink('a', SpamPage, {'y': 2012, 'a': ['1', '2']})
            l.render(a)
        self.assertEqual(a.attrib, {link._HREF: '/2012?a=1&a=2'})

    def test_page_link_error(self):
        with self.application(self.new_environ()):
            with self.assertRaisesRegex(ayame.ComponentError, r' not .* subclass of Page\b'):
                link.PageLink('a', object)


class SpamPage(ayame.Page):

    html_t = textwrap.dedent("""\
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
    """)
    kwargs = {
        'query': uri.quote(f'{ayame.AYAME_PATH}=link', '/='),
    }

    def __init__(self):
        super().__init__()
        self.add(ActionLink('link'))


class ActionLink(link.ActionLink):

    def on_click(self):
        super().on_click()
        raise Clicked()


class Clicked(Exception):
    pass
