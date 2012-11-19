#
# ayame.panel
#
#   Copyright (c) 2011-2012 Akinori Hattori <hattya@gmail.com>
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

import ayame.core
from ayame.exception import RenderingError
import ayame.markup


__all__ = ['Panel']

class Panel(ayame.core.MarkupContainer):

    def __init__(self, id, model=None):
        super(Panel, self).__init__(id, model)
        self.render_body_only = True

    def on_render(self, element):
        def step(element, depth):
            return element.qname not in (ayame.markup.AYAME_PANEL,
                                         ayame.markup.AYAME_HEAD)

        # load markup for Panel
        m = self.load_markup()
        if m.root is None:
            # markup is empty
            return element

        html = 'html' in m.lang
        ayame_panel = ayame_head = None
        for element, depth in m.root.walk(step=step):
            if element.qname == ayame.markup.AYAME_PANEL:
                if ayame_panel is None:
                    ayame_panel = element
            elif element.qname == ayame.markup.AYAME_HEAD:
                if (html and
                    ayame_head is None):
                    ayame_head = element
        if ayame_panel is None:
            raise RenderingError(self, "'ayame:panel' element is not found")
        # push ayame:head to parent component
        if ayame_head is not None:
            self.push_ayame_head(ayame_head)
        # render ayame:panel
        return super(Panel, self).on_render(ayame_panel)

    def render_ayame_element(self, element):
        if element.qname == ayame.markup.AYAME_PANEL:
            element.qname = ayame.markup.DIV
            return element
        return super(Panel, self).render_ayame_element(element)
