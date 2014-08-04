#
# test_i18n
#
#   Copyright (c) 2012-2014 Akinori Hattori <hattya@gmail.com>
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

import io

import ayame
from ayame import i18n
from base import AyameTestCase


class I18nTestCase(AyameTestCase):

    @classmethod
    def setup_class(cls):
        super(I18nTestCase, cls).setup_class()
        cls.app = Application(__name__)

    def test_iter_class(self):
        with self.application():
            l = i18n.Localizer()
            p = Page()
            self.assert_equal(list(l._iter_class(p.find('a:b'))),
                              [(Page, 'a.b'),
                               (ayame.Page, 'a.b'),
                               (MarkupContainer, 'b'),
                               (ayame.MarkupContainer, 'b'),
                               (Component, ''),
                               (ayame.Component, ''),
                               (Application, ''),
                               (ayame.Ayame, '')])
            self.assert_equal(list(l._iter_class(p.find('a'))),
                              [(Page, 'a'),
                               (ayame.Page, 'a'),
                               (MarkupContainer, ''),
                               (ayame.MarkupContainer, ''),
                               (Application, ''),
                               (ayame.Ayame, '')])
            self.assert_equal(list(l._iter_class(p)),
                              [(Page, ''),
                               (ayame.Page, ''),
                               (Application, ''),
                               (ayame.Ayame, '')])
            self.assert_equal(list(l._iter_class(None)),
                              [(Application, ''),
                               (ayame.Ayame, '')])

    def test_load(self):
        with io.open(self.path_for('i18n.txt')) as fp:
            l = i18n.Localizer()
            self.assert_equal(l._load(fp),
                              {'spam': 'spam',
                               'eggs': 'eggs',
                               'ham': 'ham',
                               'toast:': 'toast:',
                               'toast=': 'toast=',
                               'toast ': 'toast ',
                               'beans1\\': 'beans1',
                               'beans2\\': 'beans2',
                               'beans3\\': 'beans3',
                               'beans\\:': 'beans:',
                               'beans\\=': 'beans=',
                               'beans\\ ': 'beans ',
                               'bacon1': 'bacon bacon',
                               'bacon2': 'bacon\\',
                               'sausage': 'sausage\nsausage',
                               'tomato': '',
                               'lobster=': '= lobster',
                               'lobster:': ': lobster',
                               'lobster ': '  lobster'})

    def test_get(self):
        with self.application():
            locale = (None,) * 2
            l = i18n.Localizer()
            p = Page()
            for s in ('spam', 'eggs', 'ham', 'toast', 'beans', 'bacon'):
                self.assert_equal(l.get(p.find('a:b'), locale, s), s)

    def test_get_ja(self):
        with self.application():
            locale = ('ja', 'JP')
            l = i18n.Localizer()
            p = Page()
            for s in ('spam', 'eggs', 'ham', 'toast', 'beans', 'bacon'):
                self.assert_equal(l.get(p.find('a:b'), locale, s), s)

    def test_get_unknown_module(self):
        class P(Page):
            __module__ = None

        with self.application():
            locale = ('ja', 'JP')
            l = i18n.Localizer()
            p = P()
            for s in ('spam', 'eggs', 'ham', 'toast', 'beans', 'bacon'):
                self.assert_equal(l.get(p.find('a:b'), locale, s), s)


class Application(ayame.Ayame):
    pass


class Page(ayame.Page):

    def __init__(self):
        super(Page, self).__init__()
        self.add(MarkupContainer('a'))
        self.find('a').add(Component('b'))


class MarkupContainer(ayame.MarkupContainer):
    pass


class Component(ayame.Component):
    pass
