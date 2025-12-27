#
# ayame.border
#
#   Copyright (c) 2011-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
from typing import TYPE_CHECKING, Any

from . import basic, core, form, markup
from ._typing import Self
from .exception import RenderingError

if TYPE_CHECKING:
    from . import model as mm


__all__ = ['Border', 'FeedbackFieldBorder']


class Border(core.MarkupContainer):

    def __init__(self, id: str, model: mm.Model | None = None) -> None:
        super().__init__(id, model)
        self.has_markup = True
        self.render_body_only = True
        # ayame:body element
        self.body = _BorderBodyContainer(id)
        self.add_to_border(self.body)
        self.__body = False

    def add_to_border(self, *args: Any) -> Self:
        return super().add(*args)

    def add(self, *args: Any) -> Self:
        for o in args:
            if isinstance(o, core._MessageContainer):
                self.add_to_border(o)
            else:
                self.body.add(o)
        return self

    def on_render(self, element: markup.Element) -> markup.Node | list[markup.Node] | None:
        def step(el: markup.Element, _: int) -> bool:
            return el.qname not in (markup.AYAME_BODY, markup.AYAME_HEAD)

        # load markup for Panel
        m = self.load_markup()
        if m.root is None:
            # markup is empty
            return element

        ayame_border = ayame_body = ayame_head = None
        for el, _ in m.root.walk(step=step):
            if el.qname == markup.AYAME_BORDER:
                if ayame_border is None:
                    ayame_border = el
            elif el.qname == markup.AYAME_BODY:
                if (ayame_border is not None
                    and ayame_body is None):
                    # replace children of ayame:body element
                    ayame_body = el
                    ayame_body.type = markup.Element.OPEN
                    ayame_body.children[:] = element.children
            elif el.qname == markup.AYAME_HEAD:
                if ('html' in m.lang
                    and ayame_head is None):
                    ayame_head = el
        if ayame_border is None:
            raise RenderingError(self, "'ayame:border' element is not found")
        elif ayame_body is None:
            raise RenderingError(self, "'ayame:body' element is not found")
        # append ayame:head element to Page
        if ayame_head is not None:
            self.page().head.extend(ayame_head.children)
        # render border
        element.children[:] = ayame_border.children
        return super().on_render(element)

    def on_render_element(self, element: markup.Element) -> markup.Element | list[markup.Node] | None:
        if element.qname == markup.AYAME_BODY:
            # skip duplicates
            if not self.__body:
                element.attrib[markup.AYAME_ID] = self.body.id
                self.__body = True
            return element
        return super().on_render_element(element)


class _BorderBodyContainer(core.MarkupContainer):

    def __init__(self, id: str, model: mm.Model | None = None) -> None:
        super().__init__(id + '_body', model)
        self.render_body_only = True

    def on_render_element(self, element: markup.Element) -> markup.Element | list[markup.Node] | None:
        if element.qname == markup.AYAME_BODY:
            return element
        return super().on_render_element(element)

    def tr(self, key: str, component: core.Component | None = None) -> str | None:
        # retrieve message from parent of Border
        assert self.parent is not None
        return super().tr(key, self.parent.parent)


class FeedbackFieldBorder(Border):

    def __init__(self, id: str) -> None:
        super().__init__(id)
        self.render_body_only = False

        self.__feedback = basic.Label('feedback', '')
        self.add_to_border(self.__feedback)
        self.add_to_border(self._ClassModifier('class', self.__feedback.model))

    def on_configure(self) -> None:
        assert self.__feedback.model is not None
        for c, _ in self.walk():
            if isinstance(c, form.FormComponent):
                self.__feedback.model.object = c.error
                self.__feedback.visible = bool(c.error)

    class _ClassModifier(core.AttributeModifier):

        def new_value(self, value: str | None, new_value: str | None) -> str | None:
            if new_value:
                return value + '-error' if value else 'error'
            return value
