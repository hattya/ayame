#
# test_model
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
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

        with self.assertRaises(TypeError):
            model.InheritableModel(None)

        m = InheritableModel(None)
        with self.assertRaises(NotImplementedError):
            m.wrap(None)

    def test_wrap_model(self):
        class WrapModel(model.WrapModel):
            @property
            def object(self):
                return super().object

            @object.setter
            def object(self, object):
                model.WrapModel.object.__set__(self, object)

        with self.assertRaises(TypeError):
            model.WrapModel(model.Model(None))

        m = model.Model(None)
        wm = WrapModel(m)
        self.assertIs(wm.wrapped_model, m)
        with self.assertRaises(NotImplementedError):
            wm.object
        with self.assertRaises(NotImplementedError):
            wm.object = ''

    def test_compound_model_attr(self):
        class O:
            attr = 'value'

        o = O()
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer(__name__, m)
        mc.add(ayame.Component('attr'))
        self.assertEqual(len(mc.children), 1)
        self.assertEqual(o.attr, 'value')
        self.assertEqual(mc.find('attr').model.object, 'value')

        mc.find('attr').model.object = 'new_value'
        self.assertEqual(o.attr, 'new_value')
        self.assertEqual(mc.find('attr').model.object, 'new_value')

    def test_compound_model_property(self):
        class O:
            def __init__(self):
                self.__attr = 'value'

            @property
            def attr(self):
                return self.__attr

            @attr.setter
            def attr(self, attr):
                self.__attr = attr

        o = O()
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer(__name__, m)
        mc.add(ayame.Component('attr'))
        self.assertEqual(len(mc.children), 1)
        self.assertEqual(o.attr, 'value')
        self.assertEqual(mc.find('attr').model.object, 'value')

        mc.find('attr').model.object = 'new_value'
        self.assertEqual(o.attr, 'new_value')
        self.assertEqual(mc.find('attr').model.object, 'new_value')

    def test_compound_model_method(self):
        class O:
            def __init__(self):
                self.__attr = 'value'

            def get_attr(self):
                return self.__attr

            def set_attr(self, attr):
                self.__attr = attr

        o = O()
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer(__name__, m)
        mc.add(ayame.Component('attr'))
        self.assertEqual(len(mc.children), 1)
        self.assertEqual(o.get_attr(), 'value')
        self.assertEqual(mc.find('attr').model.object, 'value')

        mc.find('attr').model.object = 'new_value'
        self.assertEqual(o.get_attr(), 'new_value')
        self.assertEqual(mc.find('attr').model.object, 'new_value')

    def test_compound_model_method_noncallable(self):
        class O:
            get_attr = set_attr = None

        o = O()
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer(__name__, m)
        mc.add(ayame.Component('attr'))
        self.assertEqual(len(mc.children), 1)
        self.assertIsNone(mc.find('attr').model.object)

        with self.assertRaisesRegex(AttributeError, r'^attr$'):
            mc.find('attr').model.object = 'new_value'

    def test_compound_model_dict(self):
        o = {'attr': 'value'}
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer(__name__, m)
        mc.add(ayame.Component('attr'))
        self.assertEqual(len(mc.children), 1)
        self.assertEqual(o['attr'], 'value')
        self.assertEqual(mc.find('attr').model.object, 'value')

        mc.find('attr').model.object = 'new_value'
        self.assertEqual(o['attr'], 'new_value')
        self.assertEqual(mc.find('attr').model.object, 'new_value')

    def test_compound_model_replace(self):
        o = {
            'a': 'a',
            'b': 'b',
        }
        m = model.CompoundModel(o)
        mc = ayame.MarkupContainer(__name__, m)
        mc.add(ayame.MarkupContainer('a'))
        self.assertEqual(len(mc.children), 1)
        self.assertEqual(mc.find('a').model.object, 'a')

        mc.find('a').add(ayame.Component('b'))
        self.assertEqual(len(mc.children), 1)
        self.assertEqual(len(mc.find('a').children), 1)
        self.assertEqual(mc.find('a:b').model.object, 'b')

        mc.model = model.CompoundModel(object())
        self.assertIsNone(mc.find('a').model.object)
        self.assertIsNone(mc.find('a:b').model.object)
        with self.assertRaisesRegex(AttributeError, r'^a$'):
            setattr(mc.find('a').model, 'object', '')
        with self.assertRaisesRegex(AttributeError, r'^b$'):
            setattr(mc.find('a:b').model, 'object', '')
