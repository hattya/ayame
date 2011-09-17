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

from nose.tools import assert_raises, eq_, ok_

from ayame import core, markup
from ayame.exception import AyameError, ComponentError


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

def test_component():
    assert_raises(ComponentError, core.Component, None)

    c = core.Component('a')
    eq_(c.id, 'a')
    eq_(c.model, None)
    eq_(c.model_object, None)
    assert_raises(AyameError, lambda: c.app)
    assert_raises(AyameError, lambda: c.config)
    eq_(c.render(''), '')

def test_component_with_model():
    assert_raises(ComponentError, core.Component, '1', '')

    m = core.Model(None)
    eq_(m.object, None)
    c = core.Component('a', m)
    eq_(c.id, 'a')
    eq_(c.model, m)
    eq_(c.model_object, None)
    assert_raises(AyameError, lambda: c.app)
    assert_raises(AyameError, lambda: c.config)
    eq_(c.render(''), '')

    m = core.Model('&<>')
    eq_(m.object, '&<>')
    c = core.Component('a', m)
    eq_(c.id, 'a')
    eq_(c.model, m)
    eq_(c.model_object, '&amp;&lt;&gt;')
    c.escape_model_string = False
    eq_(c.model_object, '&<>')

def test_nested_model():
    inner = core.Model(None)
    outer = core.Model(inner)
    eq_(inner.object, None)
    eq_(outer.object, None)

def test_markup_container():
    mc = core.MarkupContainer('a')
    eq_(len(mc.children), 0)
    eq_(mc.find(None), mc)
    eq_(mc.find(''), mc)

    b1 = core.Component('b1')
    mc.add(b1)
    eq_(len(mc.children), 1)
    eq_(mc.find('b1'), b1)
    assert_raises(ComponentError, mc.add, b1)

    b2 = core.MarkupContainer('b2')
    mc.add(b2)
    eq_(len(mc.children), 2)
    eq_(mc.find('b2'), b2)
    assert_raises(ComponentError, mc.add, b2)

    eq_(mc.render(''), '')

def test_compound_model():
    class Object(object):
        attr = 'attr'
    mc = core.MarkupContainer('a', core.CompoundModel(Object()))
    mc.add(core.Component('attr'))
    eq_(len(mc.children), 1)
    eq_(mc.find('attr').model.object, 'attr')

    class Object(object):
        def get_getter(self):
            return 'getter'
    mc = core.MarkupContainer('a', core.CompoundModel(Object()))
    mc.add(core.Component('getter'))
    eq_(len(mc.children), 1)
    eq_(mc.find('getter').model.object, 'getter')

    class Object(object):
        def __getitem__(self, key):
            if key == 'key':
                return 'key'
            raise KeyError(key)
    mc = core.MarkupContainer('a', core.CompoundModel(Object()))
    mc.add(core.Component('key'))
    eq_(len(mc.children), 1)
    eq_(mc.find('key').model.object, 'key')
    mc.model = core.CompoundModel(object())
    mc.find('key').model = None
    assert_raises(AttributeError, lambda: mc.find('key').model.object)

    mc = core.MarkupContainer('a', core.CompoundModel({'b': 'b', 'c': 'c'}))
    mc.add(core.MarkupContainer('b'))
    eq_(len(mc.children), 1)
    eq_(mc.find('b').model.object, 'b')
    mc.find('b').add(core.Component('c'))
    eq_(len(mc.children), 1)
    eq_(len(mc.find('b').children), 1)
    eq_(mc.find('b:c').model.object, 'c')

    eq_(mc.render(''), '')

def test_render_children():
    # no child component
    root = markup.Element(markup.QName('', 'root'))
    mc = core.MarkupContainer('a')
    eq_(mc.render(root), root)

    # unknown ayame attribute
    root = markup.Element(markup.QName('', 'root'))
    root.attrib[markup.AYAME_ID] = 'b'
    root.attrib[markup.QName(markup.AYAME_NS, 'foo')] = ''
    mc = core.MarkupContainer('a')
    mc.add(core.Component('b'))
    assert_raises(ComponentError, mc.render, root)

    # component is not found
    root = markup.Element(markup.QName('', 'root'))
    root.attrib[markup.AYAME_ID] = 'c'
    mc = core.MarkupContainer('a')
    mc.add(core.Component('b'))
    assert_raises(ComponentError, mc.render, root)

    # replace root element
    class Component(core.Component):
        def on_render(self, element):
            return None
    root = markup.Element(markup.QName('', 'root'))
    root.attrib[markup.AYAME_ID] = 'b'
    mc = core.MarkupContainer('a')
    mc.add(Component('b'))
    eq_(mc.render(root), '')

    # remove element
    class Component(core.Component):
        def on_render(self, element):
            return None
    root = markup.Element(markup.QName('', 'root'))
    root.children.append('')
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.children.append(a)
    root.children.append('')
    mc = core.MarkupContainer('a')
    mc.add(Component('b'))

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(len(root.children), 1)

    # replace element by string
    class Component(core.Component):
        def on_render(self, element):
            return ''
    root = markup.Element(markup.QName('', 'root'))
    root.children.append('')
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.children.append(a)
    root.children.append('')
    mc = core.MarkupContainer('a')
    mc.add(Component('b'))

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(len(root.children), 1)
    eq_(root.children[0], '')

    # replace element by list
    class Component(core.Component):
        def on_render(self, element):
            return ['', '', 0, '', '']
    root = markup.Element(markup.QName('', 'root'))
    root.children.append('')
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.children.append(a)
    root.children.append('')
    mc = core.MarkupContainer('a')
    mc.add(Component('b'))

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(len(root.children), 3)
    eq_(root.children[0], '')
    eq_(root.children[1], 0)
    eq_(root.children[2], '')

    # replace element by list
    class Component(core.Component):
        def on_render(self, element):
            return ['', '', 0, '', '']
    root = markup.Element(markup.QName('', 'root'))
    root.children.append('')
    a = markup.Element(markup.QName('', 'a'))
    a.attrib[markup.AYAME_ID] = 'b'
    root.children.append(a)
    root.children.append(1)
    mc = core.MarkupContainer('a')
    mc.add(Component('b'))

    root = mc.render(root)
    eq_(root.qname, markup.QName('', 'root'))
    eq_(root.attrib, {})
    eq_(len(root.children), 4)
    eq_(root.children[0], '')
    eq_(root.children[1], 0)
    eq_(root.children[2], '')
    eq_(root.children[3], 1)
