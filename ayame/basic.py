#
# ayame.basic
#
#   Copyright (c) 2011-2014 Akinori Hattori <hattya@gmail.com>
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

import collections

from . import _compat as five
from . import core, markup, uri
from . import model as mm


__all__ = ['Label', 'ListView', 'PropertyListView', 'ContextPathGenerator',
           'ContextImage', 'ContextLink']


class Label(core.Component):

    def __init__(self, id, model=None):
        if isinstance(model, five.string_type):
            model = mm.Model(model)
        super(Label, self).__init__(id, model)

    def on_render(self, element):
        element[:] = (self.model_object_as_string(),)
        return element


class ListView(core.MarkupContainer):

    def __init__(self, id, model=None, populate_item=None):
        if isinstance(model, collections.Sequence):
            model = mm.Model(model)
        super(ListView, self).__init__(id, model)
        self._populate_item = populate_item

    def on_before_render(self):
        o = self.model_object
        if o is not None:
            for i in five.range(len(o)):
                li = self.new_item(i)
                self.add(li)
                self.populate_item(li)
        super(ListView, self).on_before_render()

    def on_render(self, element):
        skel = element.copy()
        skel.qname = markup.DIV
        del element[:]
        for c in self.children:
            element.extend(c.on_render(skel.copy()))
        return element

    def populate_item(self, item):
        if callable(self._populate_item):
            return self._populate_item(item)

    def new_item(self, index):
        return _ListItem(index, self.new_model(index))

    def new_model(self, index):
        return _ListItemModel(self, index)


class _ListItem(core.MarkupContainer):

    def __init__(self, index, model):
        super(_ListItem, self).__init__(five.str(index), model)
        self.__index = index

    @property
    def index(self):
        return self.__index


class _ListItemModel(mm.Model):

    def __init__(self, list_view, index):
        self.__list_view = list_view
        self.__index = index

    def object():
        def fget(self):
            return self.__list_view.model_object[self.__index]

        def fset(self, object):
            self.__list_view.model_object[self.__index] = object

        return locals()

    object = property(**object())


class PropertyListView(ListView):

    def new_model(self, index):
        return mm.CompoundModel(super(PropertyListView, self).new_model(index))


class ContextPathGenerator(core.AttributeModifier):

    def __init__(self, attr, rel_path):
        super(ContextPathGenerator, self).__init__(attr, mm.Model(rel_path))

    def new_value(self, value, new_value):
        return uri.relative_uri(self.environ, new_value)


class ContextImage(core.Component):

    def __init__(self, id, rel_path):
        super(ContextImage, self).__init__(id)
        self.add(ContextPathGenerator(u'src', rel_path))


class ContextLink(core.Component):

    def __init__(self, id, rel_path):
        super(ContextLink, self).__init__(id)
        self.add(ContextPathGenerator(u'href', rel_path))
