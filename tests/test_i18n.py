#
# test_i18n
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

from nose.tools import eq_

from ayame import core, i18n


class Application(core.Ayame):
    pass

class Page(core.Page):
    def __init__(self):
        super(Page, self).__init__(None)
        self.add(MarkupContainer('a'))
        self.find('a').add(Component('b'))

class MarkupContainer(core.MarkupContainer):
    pass

class Component(core.Component):
    pass

@contextmanager
def application():
    local = core._local
    app = Application(__name__)
    try:
        local.app = app
        yield
    finally:
        local.app = None

def test_iter_class():
    with application():
        page = Page()
        l = i18n.Localizer()
        eq_([v for v in l._iter_class(page.find('a:b'))],
            [(Page, 'a.b'),
             (core.Page, 'a.b'),
             (MarkupContainer, 'b'),
             (core.MarkupContainer, 'b'),
             (Component, ''),
             (core.Component, ''),
             (Application, ''),
             (core.Ayame, '')])
        eq_([v for v in l._iter_class(page.find('a'))],
            [(Page, 'a'),
             (core.Page, 'a'),
             (MarkupContainer, ''),
             (core.MarkupContainer, ''),
             (Application, ''),
             (core.Ayame, '')])
        eq_([v for v in l._iter_class(page)],
            [(Page, ''),
             (core.Page, ''),
             (Application, ''),
             (core.Ayame, '')])

def test_load():
    l = i18n.Localizer()
    data = ur"""
# comment
spam : spam
! comment
eggs = eggs
ham ham
toast\:: toast:
toast\== toast=
toast\  toast\ 
beans1\\: beans1
beans2\\= beans2
beans3\\ beans3
beans\\\: beans:
beans\\\= beans=
beans\\\  beans\ 
bacon = bacon \
        bacon
sausage = sausage\nsausage
tomato
lobster\= == lobster
lobster\: :: lobster
lobster\   \  lobster
"""
    bundle = l._load(io.StringIO(data))
    eq_(bundle, {'spam': 'spam',
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
                 'bacon': 'bacon bacon',
                 'sausage': 'sausage\nsausage',
                 'tomato': '',
                 'lobster=': '= lobster',
                 'lobster:': ': lobster',
                 'lobster ': '  lobster'})

def test_get():
    with application():
        page = Page()
        locale = ('ja', 'JP')
        l = i18n.Localizer()
        eq_(l.get(page.find('a:b'), locale, 'spam'), 'spam')
        eq_(l.get(page.find('a:b'), locale, 'eggs'), 'eggs')
        eq_(l.get(page.find('a:b'), locale, 'ham'), 'ham')
        eq_(l.get(page.find('a:b'), locale, 'toast'), 'toast')
        eq_(l.get(page.find('a:b'), locale, 'beans'), 'beans')
        eq_(l.get(page.find('a:b'), locale, 'bacon'), 'bacon')
