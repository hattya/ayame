#
# ayame.basic
#
#   Copyright (c) 2011-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import collections.abc
from collections.abc import Callable, Sequence
from typing import Any

from . import core, markup, model as mm, uri


__all__ = ['Label', 'ListView', 'PropertyListView', 'ContextPathGenerator',
           'ContextImage', 'ContextLink']


class Label(core.Component):

    def __init__(self, id: str, model: mm.Model | str | None = None) -> None:
        super().__init__(id, mm.Model(model) if isinstance(model, str) else model)

    def on_render(self, element: markup.Element) -> markup.Node | list[markup.Node]:
        element.children[:] = (self.model_object_as_string(),)
        return element


class ListView(core.MarkupContainer):

    def __init__(self, id: str, model: mm.Model | Sequence[Any] | None = None,
                 populate_item: Callable[[ListItem], None] | None = None) -> None:
        super().__init__(id, mm.Model(model) if isinstance(model, collections.abc.Sequence) else model)
        self._populate_item = populate_item

    def on_before_render(self) -> None:
        if (o := self.model_object) is not None:
            for i in range(len(o)):
                li = self.new_item(i)
                self.add(li)
                self.populate_item(li)
        super().on_before_render()

    def on_render(self, element: markup.Element) -> markup.Node | list[markup.Node]:
        skel = element.copy()
        skel.qname = markup.DIV
        element.children.clear()
        for c in self.children:
            rv = c.on_render(skel.copy())
            assert isinstance(rv, markup.Element)
            element.extend(rv.children)
        return element

    def populate_item(self, item: ListItem) -> None:
        if callable(self._populate_item):
            self._populate_item(item)

    def new_item(self, index: int) -> ListItem:
        return ListItem(index, self.new_model(index))

    def new_model(self, index: int) -> mm.Model:
        return _ListItemModel(self, index)


class ListItem(core.MarkupContainer):

    def __init__(self, index: int, model: mm.Model | None) -> None:
        super().__init__(str(index), model)
        self.__index = index

    @property
    def index(self) -> int:
        return self.__index


class _ListItemModel(mm.Model):

    def __init__(self, list_view: ListView, index: int) -> None:
        self.__list_view = list_view
        self.__index = index

    @property
    def object(self) -> Any:
        return self.__list_view.model_object[self.__index]

    @object.setter
    def object(self, object: Any) -> None:
        self.__list_view.model_object[self.__index] = object


class PropertyListView(ListView):

    def new_model(self, index: int) -> mm.Model:
        return mm.CompoundModel(super().new_model(index))


class ContextPathGenerator(core.AttributeModifier):

    def __init__(self, attr: markup.QName | str, rel_path: str) -> None:
        super().__init__(attr, mm.Model(rel_path))

    def new_value(self, value: str | None, new_value: str | None) -> str | None:
        assert new_value is not None
        return uri.relative_uri(self.environ, new_value)


class ContextImage(core.Component):

    def __init__(self, id: str, rel_path: str) -> None:
        super().__init__(id)
        self.add(ContextPathGenerator('src', rel_path))


class ContextLink(core.Component):

    def __init__(self, id: str, rel_path: str) -> None:
        super().__init__(id)
        self.add(ContextPathGenerator('href', rel_path))
