#
# ayame.panel
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from . import core, basic, form, markup
from . import model as mm
from .exception import RenderingError


__all__ = ['Panel', 'FeedbackPanel']


class Panel(core.MarkupContainer):

    def __init__(self, id, model=None):
        super().__init__(id, model)
        self.has_markup = True
        self.render_body_only = True

    def on_render(self, element):
        def step(element, depth):
            return element.qname not in (markup.AYAME_PANEL, markup.AYAME_HEAD)

        # load markup for Panel
        m = self.load_markup()
        if m.root is None:
            # markup is empty
            return element

        ayame_panel = ayame_head = None
        for elem, _ in m.root.walk(step=step):
            if elem.qname == markup.AYAME_PANEL:
                if ayame_panel is None:
                    ayame_panel = elem
            elif elem.qname == markup.AYAME_HEAD:
                if ('html' in m.lang
                    and ayame_head is None):
                    ayame_head = elem
        if ayame_panel is None:
            raise RenderingError(self, "'ayame:panel' element is not found")
        # append ayame:head element to Page
        if ayame_head is not None:
            self.page().head.extend(ayame_head)
        # render panel
        element[:] = ayame_panel
        return super().on_render(element)


class FeedbackPanel(Panel):

    def __init__(self, id):
        super().__init__(id)
        self.__errors = []

        self.add(self._ListView('feedback', mm.Model(self.__errors)))

    def on_configure(self):
        if self.request.path:
            c = self.page().find(self.request.path)
            if isinstance(c, form.Form):
                for c, _ in c.walk():
                    if (isinstance(c, form.FormComponent)
                        and c.error):
                        self.__errors.append(str(c.error))
        self.visible = bool(self.__errors)

    class _ListView(basic.ListView):

        def populate_item(self, item):
            item.add(basic.Label('message', item.model_object))
