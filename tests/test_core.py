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

from ayame import core
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

    c = core.Component('1')
    eq_(c.id, '1')
    eq_(c.model, None)
    eq_(c.model_object, None)
    assert_raises(AyameError, lambda: c.app)
    assert_raises(AyameError, lambda: c.config)
    eq_(c.render(''), '')

def test_component_with_model():
    assert_raises(ComponentError, core.Component, '1', '')

    m = core.Model(None)
    eq_(m.object, None)
    c = core.Component('1', m)
    eq_(c.id, '1')
    eq_(c.model, m)
    eq_(c.model_object, None)
    assert_raises(AyameError, lambda: c.app)
    assert_raises(AyameError, lambda: c.config)
    eq_(c.render(''), '')

    m = core.Model('&<>')
    eq_(m.object, '&<>')
    c = core.Component('1', m)
    eq_(c.id, '1')
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
    mc = core.MarkupContainer('1')
    eq_(len(mc.children), 0)
    eq_(mc.find(None), mc)
    eq_(mc.find(''), mc)

    child2a = core.Component('2a')
    mc.add(child2a)
    eq_(len(mc.children), 1)
    eq_(mc.find('2a'), child2a)
    assert_raises(ComponentError, mc.add, child2a)

    child2b = core.MarkupContainer('2b')
    mc.add(child2b)
    eq_(len(mc.children), 2)
    eq_(mc.find('2b'), child2b)
    assert_raises(ComponentError, mc.add, child2b)

    eq_(mc.render(''), '')

def test_compound_model():
    class Object(object):
        attr = 'attr'
    mc = core.MarkupContainer('1', core.CompoundModel(Object()))
    mc.add(core.Component('attr'))
    eq_(len(mc.children), 1)
    eq_(mc.find('attr').model.object, 'attr')

    class Object(object):
        def get_getter(self):
            return 'getter'
    mc = core.MarkupContainer('1', core.CompoundModel(Object()))
    mc.add(core.Component('getter'))
    eq_(len(mc.children), 1)
    eq_(mc.find('getter').model.object, 'getter')

    class Object(object):
        def __getitem__(self, key):
            if key == 'key':
                return 'key'
            raise KeyError(key)
    mc = core.MarkupContainer('1', core.CompoundModel(Object()))
    mc.add(core.Component('key'))
    eq_(len(mc.children), 1)
    eq_(mc.find('key').model.object, 'key')
    mc.model = core.CompoundModel(object())
    mc.find('key').model = None
    assert_raises(AttributeError, lambda: mc.find('key').model.object)

    mc = core.MarkupContainer('1', core.CompoundModel({'2': '2', '3': '3'}))
    mc.add(core.MarkupContainer('2'))
    eq_(len(mc.children), 1)
    eq_(mc.find('2').model.object, '2')
    mc.find('2').add(core.Component('3'))
    eq_(len(mc.children), 1)
    eq_(len(mc.find('2').children), 1)
    eq_(mc.find('2:3').model.object, '3')

    eq_(mc.render(''), '')
