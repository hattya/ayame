#
# test_link
#
#   Copyright (c) 2012-2026 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import copy
import unittest.mock

import ayame
from ayame import http, link, markup, model, uri
from base import AyameTestCase


class LinkTestCase(AyameTestCase):

    def test_link_href(self):
        for v, rv in (
            (
                {},
                {},
            ),
            (
                {link._HREF: None},
                {},
            ),
            (
                {link._HREF: '/spam'},
                {link._HREF: '/spam'},
            ),
        ):
            with self.subTest(attrib=v):
                el = markup.Element(link._A, v)
                l = link.Link(__name__)
                with self.application():
                    l.render(el)
                self.assertEqual(el.attrib, rv)
                self.assertEqual(el.children, [])

    def test_link_src(self):
        for v, rv in (
            (
                {},
                {},
            ),
            (
                {link._SRC: None},
                {},
            ),
            (
                {link._SRC: '/spam'},
                {link._SRC: '/spam'},
            ),
        ):
            with self.subTest(attrib=v):
                el = markup.Element(link._SCRIPT,
                                    attrib=v)
                l = link.Link(__name__)
                with self.application():
                    l.render(el)
                self.assertEqual(el.attrib, rv)
                self.assertEqual(el.children, [])

    def test_link_replace_children(self):
        for m in (
            model.Model('spam'),
            'spam',
        ):
            with self.subTest(model=type(m)):
                el = markup.Element(link._A)
                l = link.Link(__name__, m)
                with self.application():
                    l.render(el)
                self.assertEqual(el.attrib, {})
                self.assertEqual(el.children, ['spam'])

    def test_link_with_unknown_element(self):
        for m in (
            model.Model('spam'),
            'spam',
        ):
            with self.subTest(model=type(m)):
                el = markup.Element(markup.DIV)
                l = link.Link(__name__, m)
                with self.application():
                    l.render(el)
                self.assertEqual(el.attrib, {})
                self.assertEqual(el.children, ['spam'])

    def test_action_link(self):
        with unittest.mock.patch.dict(self.app.config):
            self.app.config['ayame.route.map'] = map = copy.deepcopy(self.app.config['ayame.route.map'])
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
        query = f'{ayame.AYAME_PATH}=link'
        with self.application(self.new_environ(query=query)):
            p = SpamPage()
            with self.assertRaises(Clicked):
                p()

    def test_page_link_error(self):
        with self.application(self.new_environ()):
            with self.assertRaisesRegex(ayame.ComponentError, r' not .* subclass of Page\b'):
                link.PageLink(__name__, object)

    def test_page_link(self):
        with unittest.mock.patch.dict(self.app.config):
            self.app.config['ayame.route.map'] = map = copy.deepcopy(self.app.config['ayame.route.map'])
            map.connect('/<y:int>', SpamPage)
            map.connect('/', SpamPage)
            for v, a, rv in (
                (
                    None,
                    None,
                    '/',
                ),
                (
                    {
                        'v': [1, 2, 3],
                    },
                    'a',
                    '/?v=1&v=2&v=3#a',
                ),
                (
                    {
                        'y': 2012,
                    },
                    None,
                    '/2012',
                ),
                (
                    {
                        'y': 2012,
                        'v': [1, 2, 3],
                    },
                    'a',
                    '/2012?v=1&v=2&v=3#a',
                ),
            ):
                with self.subTest(values=v, anchor=a):
                    el = markup.Element(link._A)
                    with self.application(self.new_environ()):
                        l = link.PageLink(__name__, SpamPage, v, a)
                        l.render(el)
                    self.assertEqual(el.attrib, {link._HREF: rv})
                    self.assertEqual(el.children, [])


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
        'query': uri.quote(f'{ayame.AYAME_PATH}=link', '/='),
    }

    def __init__(self):
        super().__init__()
        self.add(self.ActionLink('link'))

    class ActionLink(link.ActionLink):

        def on_click(self):
            super().on_click()
            raise Clicked()


class Clicked(Exception):
    pass
