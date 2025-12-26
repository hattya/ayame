#
# ayame.basic
#
#   Copyright (c) 2011-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import collections.abc

from . import core, markup, model as mm, uri


__all__ = ['Label', 'ListView', 'PropertyListView', 'ContextPathGenerator',
           'ContextImage', 'ContextLink']


class Label(core.Component):

    def __init__(self, id, model=None):
        super().__init__(id, mm.Model(model) if isinstance(model, str) else model)

    def on_render(self, element):
        element.children[:] = (self.model_object_as_string(),)
        return element


class ListView(core.MarkupContainer):

    def __init__(self, id, model=None, populate_item=None):
        super().__init__(id, mm.Model(model) if isinstance(model, collections.abc.Sequence) else model)
        self._populate_item = populate_item

    def on_before_render(self):
        if (o := self.model_object) is not None:
            for i in range(len(o)):
                li = self.new_item(i)
                self.add(li)
                self.populate_item(li)
        super().on_before_render()

    def on_render(self, element):
        skel = element.copy()
        skel.qname = markup.DIV
        element.children.clear()
        for c in self.children:
            element.extend(c.on_render(skel.copy()))
        return element

    def populate_item(self, item):
        if callable(self._populate_item):
            self._populate_item(item)

    def new_item(self, index):
        return _ListItem(index, self.new_model(index))

    def new_model(self, index):
        return _ListItemModel(self, index)


class _ListItem(core.MarkupContainer):

    def __init__(self, index, model):
        super().__init__(str(index), model)
        self.__index = index

    @property
    def index(self):
        return self.__index


class _ListItemModel(mm.Model):

    def __init__(self, list_view, index):
        self.__list_view = list_view
        self.__index = index

    @property
    def object(self):
        return self.__list_view.model_object[self.__index]

    @object.setter
    def object(self, object):
        self.__list_view.model_object[self.__index] = object


class PropertyListView(ListView):

    def new_model(self, index):
        return mm.CompoundModel(super().new_model(index))


class ContextPathGenerator(core.AttributeModifier):

    def __init__(self, attr, rel_path):
        super().__init__(attr, mm.Model(rel_path))

    def new_value(self, value, new_value):
        return uri.relative_uri(self.environ, new_value)


class ContextImage(core.Component):

    def __init__(self, id, rel_path):
        super().__init__(id)
        self.add(ContextPathGenerator('src', rel_path))


class ContextLink(core.Component):

    def __init__(self, id, rel_path):
        super().__init__(id)
        self.add(ContextPathGenerator('href', rel_path))
