#
# ayame.panel
#
#   Copyright (c) 2011-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
from . import core, basic, form, markup, model as mm
from .exception import RenderingError


__all__ = ['Panel', 'FeedbackPanel']


class Panel(core.MarkupContainer):

    def __init__(self, id: str, model: mm.Model | None = None) -> None:
        super().__init__(id, model)
        self.has_markup = True
        self.render_body_only = True

    def on_render(self, element: markup.Element) -> markup.Node | list[markup.Node] | None:
        def step(el: markup.Element, _: int) -> bool:
            return el.qname not in (markup.AYAME_PANEL, markup.AYAME_HEAD)

        # load markup for Panel
        m = self.load_markup()
        if m.root is None:
            # markup is empty
            return element

        ayame_panel = ayame_head = None
        for el, _ in m.root.walk(step=step):
            if el.qname == markup.AYAME_PANEL:
                if ayame_panel is None:
                    ayame_panel = el
            elif el.qname == markup.AYAME_HEAD:
                if ('html' in m.lang
                    and ayame_head is None):
                    ayame_head = el
        if ayame_panel is None:
            raise RenderingError(self, "'ayame:panel' element is not found")
        # append ayame:head element to Page
        if ayame_head is not None:
            self.page().head.extend(ayame_head.children)
        # render panel
        element.children[:] = ayame_panel.children
        return super().on_render(element)


class FeedbackPanel(Panel):

    __errors: list[str]

    def __init__(self, id: str) -> None:
        super().__init__(id)
        self.__errors = []

        self.add(self._ListView('feedback', mm.Model(self.__errors)))

    def on_configure(self) -> None:
        if self.request.path:
            if isinstance((c := self.page().find(self.request.path)), form.Form):
                for c, _ in c.walk():
                    if (isinstance(c, form.FormComponent)
                        and c.error):
                        self.__errors.append(str(c.error))
        self.visible = bool(self.__errors)

    class _ListView(basic.ListView):

        def populate_item(self, item: basic.ListItem) -> None:
            item.add(basic.Label('message', item.model_object))
