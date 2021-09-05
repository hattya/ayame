#
# test_model
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import ayame
from ayame import model
from base import AyameTestCase


class ModelTestCase(AyameTestCase):

    def test_model(self):
        m = model.Model(None)
        self.assert_is_none(m.object)

        m.object = ''
        self.assert_equal(m.object, '')

    def test_nested_model(self):
        m = model.Model(model.Model(None))
        self.assert_is_none(m.object)

        m.object = model.Model('')
        self.assert_equal(m.object, '')

    def test_inheritable_model(self):
        class InheritableModel(model.InheritableModel):
            def wrap(self, component):
                return super(InheritableModel, self).wrap(component)

        m = InheritableModel(None)
        self.assert_is_none(m.wrap(None))

    def test_wrap_model(self):
        class WrapModel(model.WrapModel):
            @property
            def object(self):
                return super(WrapModel, self).object

        m = WrapModel(None)
        self.assert_is_none(m.object)

    def test_compound_model_attr(self):
        class Object(object):
            attr = 'value'

        o = Object()
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer('a', m)
        mc.add(ayame.Component('attr'))
        self.assert_equal(len(mc.children), 1)
        self.assert_equal(o.attr, 'value')
        self.assert_equal(mc.find('attr').model.object, 'value')

        mc.find('attr').model.object = 'new_value'
        self.assert_equal(o.attr, 'new_value')
        self.assert_equal(mc.find('attr').model.object, 'new_value')

    def test_compound_model_property(self):
        class Object(object):
            def __init__(self):
                self.__attr = 'value'

            def attr():
                def fget(self):
                    return self.__attr

                def fset(self, attr):
                    self.__attr = attr

                return locals()

            attr = property(**attr())

        o = Object()
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer('a', m)
        mc.add(ayame.Component('attr'))
        self.assert_equal(len(mc.children), 1)
        self.assert_equal(o.attr, 'value')
        self.assert_equal(mc.find('attr').model.object, 'value')

        mc.find('attr').model.object = 'new_value'
        self.assert_equal(o.attr, 'new_value')
        self.assert_equal(mc.find('attr').model.object, 'new_value')

    def test_compound_model_method(self):
        class Object(object):
            def __init__(self):
                self.__method = 'value'

            def get_method(self):
                return self.__method

            def set_method(self, method):
                self.__method = method

        o = Object()
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer('a', m)
        mc.add(ayame.Component('method'))
        self.assert_equal(len(mc.children), 1)
        self.assert_equal(o.get_method(), 'value')
        self.assert_equal(mc.find('method').model.object, 'value')

        mc.find('method').model.object = 'new_value'
        self.assert_equal(o.get_method(), 'new_value')
        self.assert_equal(mc.find('method').model.object, 'new_value')

    def test_compound_model_method_noncallable(self):
        class Object(object):
            get_method = set_method = None

        o = Object()
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer('a', m)
        mc.add(ayame.Component('method'))
        self.assert_equal(len(mc.children), 1)
        self.assert_is_none(mc.find('method').model.object)

        with self.assert_raises_regex(AttributeError, r'^method$'):
            mc.find('method').model.object = 'new_value'

    def test_compound_model_dict(self):
        o = {'mapping': 'value'}
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer('a', m)
        mc.add(ayame.Component('mapping'))
        self.assert_equal(len(mc.children), 1)
        self.assert_equal(o['mapping'], 'value')
        self.assert_equal(mc.find('mapping').model.object, 'value')

        mc.find('mapping').model.object = 'new_value'
        self.assert_equal(o['mapping'], 'new_value')
        self.assert_equal(mc.find('mapping').model.object, 'new_value')

    def test_compound_model_replace(self):
        o = {
            'b': 'b',
            'c': 'c'
        }
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer('a', m)
        mc.add(ayame.MarkupContainer('b'))
        self.assert_equal(len(mc.children), 1)
        self.assert_equal(mc.find('b').model.object, 'b')

        mc.find('b').add(ayame.Component('c'))
        self.assert_equal(len(mc.children), 1)
        self.assert_equal(len(mc.find('b').children), 1)
        self.assert_equal(mc.find('b:c').model.object, 'c')

        mc.model = model.CompoundModel(object())
        self.assert_is_none(mc.find('b').model.object)
        self.assert_is_none(mc.find('b:c').model.object)
        with self.assert_raises_regex(AttributeError, r'^b$'):
            setattr(mc.find('b').model, 'object', '')
        with self.assert_raises_regex(AttributeError, r'^c$'):
            setattr(mc.find('b:c').model, 'object', '')
        self.assert_equal(mc.render(''), '')
