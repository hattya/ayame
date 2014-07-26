#
# ayame.panel
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

from . import _compat as five
from . import core, basic, form, markup
from . import model as mm
from .exception import RenderingError


__all__ = ['Panel', 'FeedbackPanel']


class Panel(core.MarkupContainer):

    def __init__(self, id, model=None):
        super(Panel, self).__init__(id, model)
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
                if ('html' in m.lang and
                    ayame_head is None):
                    ayame_head = elem
        if ayame_panel is None:
            raise RenderingError(self, "'ayame:panel' element is not found")
        # append ayame:head element to Page
        if ayame_head is not None:
            self.page().head.extend(ayame_head)
        # render panel
        element[:] = ayame_panel
        return super(Panel, self).on_render(element)


class FeedbackPanel(Panel):

    def __init__(self, id):
        super(FeedbackPanel, self).__init__(id)
        self.__errors = []

        self.add(self._ListView('feedback', mm.Model(self.__errors)))

    def on_configure(self):
        if self.request.path:
            c = self.page().find(self.request.path)
            if isinstance(c, form.Form):
                for c, _ in c.walk():
                    if (isinstance(c, form.FormComponent) and
                        c.error):
                        self.__errors.append(five.str(c.error))
        self.visible = bool(self.__errors)

    class _ListView(basic.ListView):

        def populate_item(self, item):
            item.add(basic.Label('message', item.model_object))
