#
# test_model
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

from nose.tools import assert_raises, eq_

from ayame import core, model


def test_model():
    m = model.Model(None)
    eq_(m.object, None)
    m.object = ''
    eq_(m.object, '')

def test_nested_model():
    inner = model.Model(None)
    outer = model.Model(inner)
    eq_(inner.object, None)
    eq_(outer.object, None)
    outer.object = model.Model('')
    eq_(outer.object, '')

def test_inheritable_model():
    assert_raises(TypeError, model.InheritableModel)

    class InheritableModel(model.InheritableModel):
        def wrap(self, component):
            return super(InheritableModel, self).wrap(component)

    m = InheritableModel(None)
    eq_(m.wrap(None), None)

def test_wrap_model():
    assert_raises(TypeError, model.WrapModel)

    class WrapModel(model.WrapModel):
        @property
        def object(self):
            return super(WrapModel, self).object

    m = WrapModel(None)
    eq_(m.object, None)

def test_compound_model():
    class Object(object):
        attr = 'value'
    o = Object()
    m = model.CompoundModel(o)
    mc = core.MarkupContainer('a', m)
    mc.add(core.Component('attr'))
    eq_(len(mc.children), 1)
    eq_(o.attr, 'value')
    eq_(mc.find('attr').model.object, 'value')
    mc.find('attr').model.object = 'new_value'
    eq_(o.attr, 'new_value')
    eq_(mc.find('attr').model.object, 'new_value')

    class Object(object):
        def __init__(self):
            self.__method = 'value'
        def get_method(self):
            return self.__method
        def set_method(self, method):
            self.__method = method
    o = Object()
    m = model.CompoundModel(o)
    mc = core.MarkupContainer('a', m)
    mc.add(core.Component('method'))
    eq_(len(mc.children), 1)
    eq_(o.get_method(), 'value')
    eq_(mc.find('method').model.object, 'value')
    mc.find('method').model.object = 'new_value'
    eq_(o.get_method(), 'new_value')
    eq_(mc.find('method').model.object, 'new_value')

    o = {'mapping': 'value'}
    m = model.CompoundModel(o)
    mc = core.MarkupContainer('a', m)
    mc.add(core.Component('mapping'))
    eq_(len(mc.children), 1)
    eq_(o['mapping'], 'value')
    eq_(mc.find('mapping').model.object, 'value')
    mc.find('mapping').model.object = 'new_value'
    eq_(o['mapping'], 'new_value')
    eq_(mc.find('mapping').model.object, 'new_value')

    o = {'b': 'b',
         'c': 'c'}
    m = model.CompoundModel(o)
    mc = core.MarkupContainer('a', m)
    mc.add(core.MarkupContainer('b'))
    eq_(len(mc.children), 1)
    eq_(mc.find('b').model.object, 'b')
    mc.find('b').add(core.Component('c'))
    eq_(len(mc.children), 1)
    eq_(len(mc.find('b').children), 1)
    eq_(mc.find('b:c').model.object, 'c')
    mc.model = model.CompoundModel(object())
    assert_raises(AttributeError, lambda: mc.find('b').model.object)
    assert_raises(AttributeError, lambda: mc.find('b:c').model.object)
    assert_raises(AttributeError, setattr, mc.find('b').model, 'object', '')
    assert_raises(AttributeError, setattr, mc.find('b:c').model, 'object', '')
    eq_(mc.render(''), '')
