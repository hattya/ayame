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
        self.assertIsNone(m.object)

        m.object = ''
        self.assertEqual(m.object, '')

    def test_nested_model(self):
        m = model.Model(model.Model(None))
        self.assertIsNone(m.object)

        m.object = model.Model('')
        self.assertEqual(m.object, '')

    def test_inheritable_model(self):
        class InheritableModel(model.InheritableModel):
            def wrap(self, component):
                return super().wrap(component)

        m = InheritableModel(None)
        self.assertIsNone(m.wrap(None))

    def test_wrap_model(self):
        class WrapModel(model.WrapModel):
            @property
            def object(self):
                return super().object

        m = WrapModel(None)
        self.assertIsNone(m.object)

    def test_compound_model_attr(self):
        class Object:
            attr = 'value'

        o = Object()
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer('a', m)
        mc.add(ayame.Component('attr'))
        self.assertEqual(len(mc.children), 1)
        self.assertEqual(o.attr, 'value')
        self.assertEqual(mc.find('attr').model.object, 'value')

        mc.find('attr').model.object = 'new_value'
        self.assertEqual(o.attr, 'new_value')
        self.assertEqual(mc.find('attr').model.object, 'new_value')

    def test_compound_model_property(self):
        class Object:
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
        self.assertEqual(len(mc.children), 1)
        self.assertEqual(o.attr, 'value')
        self.assertEqual(mc.find('attr').model.object, 'value')

        mc.find('attr').model.object = 'new_value'
        self.assertEqual(o.attr, 'new_value')
        self.assertEqual(mc.find('attr').model.object, 'new_value')

    def test_compound_model_method(self):
        class Object:
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
        self.assertEqual(len(mc.children), 1)
        self.assertEqual(o.get_method(), 'value')
        self.assertEqual(mc.find('method').model.object, 'value')

        mc.find('method').model.object = 'new_value'
        self.assertEqual(o.get_method(), 'new_value')
        self.assertEqual(mc.find('method').model.object, 'new_value')

    def test_compound_model_method_noncallable(self):
        class Object:
            get_method = set_method = None

        o = Object()
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer('a', m)
        mc.add(ayame.Component('method'))
        self.assertEqual(len(mc.children), 1)
        self.assertIsNone(mc.find('method').model.object)

        with self.assertRaisesRegex(AttributeError, r'^method$'):
            mc.find('method').model.object = 'new_value'

    def test_compound_model_dict(self):
        o = {'mapping': 'value'}
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer('a', m)
        mc.add(ayame.Component('mapping'))
        self.assertEqual(len(mc.children), 1)
        self.assertEqual(o['mapping'], 'value')
        self.assertEqual(mc.find('mapping').model.object, 'value')

        mc.find('mapping').model.object = 'new_value'
        self.assertEqual(o['mapping'], 'new_value')
        self.assertEqual(mc.find('mapping').model.object, 'new_value')

    def test_compound_model_replace(self):
        o = {
            'b': 'b',
            'c': 'c',
        }
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer('a', m)
        mc.add(ayame.MarkupContainer('b'))
        self.assertEqual(len(mc.children), 1)
        self.assertEqual(mc.find('b').model.object, 'b')

        mc.find('b').add(ayame.Component('c'))
        self.assertEqual(len(mc.children), 1)
        self.assertEqual(len(mc.find('b').children), 1)
        self.assertEqual(mc.find('b:c').model.object, 'c')

        mc.model = model.CompoundModel(object())
        self.assertIsNone(mc.find('b').model.object)
        self.assertIsNone(mc.find('b:c').model.object)
        with self.assertRaisesRegex(AttributeError, r'^b$'):
            setattr(mc.find('b').model, 'object', '')
        with self.assertRaisesRegex(AttributeError, r'^c$'):
            setattr(mc.find('b:c').model, 'object', '')
        self.assertEqual(mc.render(''), '')
