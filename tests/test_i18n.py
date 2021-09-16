#
# test_i18n
#
#   Copyright (c) 2012-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import ayame
from ayame import i18n
from base import AyameTestCase


class I18nTestCase(AyameTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.app = Application(__name__)

    def test_iter_class(self):
        with self.application():
            l = i18n.Localizer()
            p = Page()
            self.assertEqual(list(l._iter_class(p.find('a1:b'))), [
                (Page, (), 'a1.b'),
                (ayame.Page, (), 'a1.b'),
                (MarkupContainer, (), 'b'),
                (ayame.MarkupContainer, (), 'b'),
                (Component, (), ''),
                (ayame.Component, (), ''),
                (Application, (), ''),
                (ayame.Ayame, (), ''),
            ])
            self.assertEqual(list(l._iter_class(p.find('a2:b'))), [
                (Page, (), 'a2.b'),
                (ayame.Page, (), 'a2.b'),
                (Page.MarkupContainer, (Page,), 'b'),
                (ayame.MarkupContainer, (), 'b'),
                (Component, (), ''),
                (ayame.Component, (), ''),
                (Application, (), ''),
                (ayame.Ayame, (), ''),
            ])
            self.assertEqual(list(l._iter_class(p.find('a1'))), [
                (Page, (), 'a1'),
                (ayame.Page, (), 'a1'),
                (MarkupContainer, (), ''),
                (ayame.MarkupContainer, (), ''),
                (Application, (), ''),
                (ayame.Ayame, (), ''),
            ])
            self.assertEqual(list(l._iter_class(p.find('a2'))), [
                (Page, (), 'a2'),
                (ayame.Page, (), 'a2'),
                (Page.MarkupContainer, (Page,), ''),
                (ayame.MarkupContainer, (), ''),
                (Application, (), ''),
                (ayame.Ayame, (), ''),
            ])
            self.assertEqual(list(l._iter_class(p)), [
                (Page, (), ''),
                (ayame.Page, (), ''),
                (Application, (), ''),
                (ayame.Ayame, (), ''),
            ])
            self.assertEqual(list(l._iter_class(None)), [
                (Application, (), ''),
                (ayame.Ayame, (), ''),
            ])

    def test_load(self):
        with open(self.path_for('i18n.txt')) as fp:
            l = i18n.Localizer()
            self.assertEqual(l._load(fp), {
                'spam': 'spam',
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
                'lobster ': '  lobster',
            })

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
            for i in range(1, 3):
                c = page.find(f'a{i}:b')
                for k in ('spam', 'eggs', 'ham', 'toast', 'beans', 'bacon'):
                    v = k
                    if k in ('ham', 'toast'):
                        v += str(i)
                    with self.subTest(path=c.path(), locale=locale, key=k):
                        self.assertEqual(l.get(c, locale, k), v)

    def test_cache(self):
        config = self.app.config.copy()
        try:
            with self.application():
                locale = (None,) * 2
                l = i18n.Localizer()
                p = Page()
                for i in range(1, 3):
                    self.app.config['ayame.resource.loader'] = self.new_resource_loader()
                    self.app.config['ayame.i18n.cache'] = config['ayame.i18n.cache'].copy()

                    c = p.find(f'a{i}:b')
                    with self.subTest(path=c.path()):
                        self.assertEqual(l.get(c, locale, 'spam'), 'spam')
                        self.assertIsNone(l.get(c, locale, 'spam'))
                        self.assertIsNone(l.get(c, locale, 'eggs'))
        finally:
            self.app.config = config


class Application(ayame.Ayame):
    pass


class Page(ayame.Page):

    def __init__(self):
        super().__init__()
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
