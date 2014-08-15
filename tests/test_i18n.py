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
from ayame import _compat as five
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
            self.assert_equal(list(l._iter_class(p.find('a1:b'))),
                              [(Page, (), 'a1.b'),
                               (ayame.Page, (), 'a1.b'),
                               (MarkupContainer, (), 'b'),
                               (ayame.MarkupContainer, (), 'b'),
                               (Component, (), ''),
                               (ayame.Component, (), ''),
                               (Application, (), ''),
                               (ayame.Ayame, (), '')])
            self.assert_equal(list(l._iter_class(p.find('a2:b'))),
                              [(Page, (), 'a2.b'),
                               (ayame.Page, (), 'a2.b'),
                               (Page.MarkupContainer, (Page,), 'b'),
                               (ayame.MarkupContainer, (), 'b'),
                               (Component, (), ''),
                               (ayame.Component, (), ''),
                               (Application, (), ''),
                               (ayame.Ayame, (), '')])
            self.assert_equal(list(l._iter_class(p.find('a1'))),
                              [(Page, (), 'a1'),
                               (ayame.Page, (), 'a1'),
                               (MarkupContainer, (), ''),
                               (ayame.MarkupContainer, (), ''),
                               (Application, (), ''),
                               (ayame.Ayame, (), '')])
            self.assert_equal(list(l._iter_class(p.find('a2'))),
                              [(Page, (), 'a2'),
                               (ayame.Page, (), 'a2'),
                               (Page.MarkupContainer, (Page,), ''),
                               (ayame.MarkupContainer, (), ''),
                               (Application, (), ''),
                               (ayame.Ayame, (), '')])
            self.assert_equal(list(l._iter_class(p)),
                              [(Page, (), ''),
                               (ayame.Page, (), ''),
                               (Application, (), ''),
                               (ayame.Ayame, (), '')])
            self.assert_equal(list(l._iter_class(None)),
                              [(Application, (), ''),
                               (ayame.Ayame, (), '')])

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
        locale = (None,) * 2
        self._test_get(Page(), locale)

    def test_get_ja(self):
        locale = ('ja', 'JP')
        self._test_get(Page(), locale)

    def test_get_unknown_module(self):
        class P(Page):
            __module__ = None

        locale = ('en', 'US')
        self._test_get(P(), locale)

    def _test_get(self, page, locale):
        with self.application():
            l = i18n.Localizer()
            for i in five.range(1, 3):
                c = page.find('a{}:b'.format(i))
                for k in ('spam', 'eggs', 'ham', 'toast', 'beans', 'bacon'):
                    v = k
                    if k in ('ham', 'toast'):
                        v += str(i)
                    self.assert_equal(l.get(c, locale, k), v)

    def test_cache(self):
        config = self.app.config.copy()
        try:
            with self.application():
                locale = (None,) * 2
                l = i18n.Localizer()
                p = Page()
                for i in five.range(1, 3):
                    self.app.config['ayame.resource.loader'] = self.new_resource_loader()
                    self.app.config['ayame.i18n.cache'] = config['ayame.i18n.cache'].copy()

                    c = p.find('a{}:b'.format(i))
                    self.assert_equal(l.get(c, locale, 'spam'), 'spam')
                    self.assert_is_none(l.get(c, locale, 'spam'))
                    self.assert_is_none(l.get(c, locale, 'eggs'))
        finally:
            self.app.config = config


class Application(ayame.Ayame):
    pass


class Page(ayame.Page):

    def __init__(self):
        super(Page, self).__init__()
        self.add(MarkupContainer('a1'))
        self.find('a1').add(Component('b'))
        self.add(self.MarkupContainer('a2'))
        self.find('a2').add(Component('b'))

    @ayame.nested
    class MarkupContainer(ayame.MarkupContainer):
        pass


class MarkupContainer(ayame.MarkupContainer):
    pass


class Component(ayame.Component):
    pass
