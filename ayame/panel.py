#
# ayame.panel
#
#   Copyright (c) 2011 Akinori Hattori <hattya@gmail.com>
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

from ayame import core, markup, util
from ayame.exception import RenderingError


__all__ = ['Panel']

class Panel(core.MarkupContainer):

    def __init__(self, id, model=None):
        super(Panel, self).__init__(id, model)
        self.render_body_only = True

    def on_render(self, element):
        push_children = self._push_children

        def throw(cls, msg):
            raise RenderingError('{}: {}'.format(util.fqon_of(cls), msg))

        def walk(root):
            queue = self._new_queue(root)
            while queue:
                parent, index, element = queue.pop()
                if element.qname in (markup.AYAME_PANEL, markup.AYAME_HEAD):
                    yield parent, index, element
                else:
                    push_children(queue, element)

        # load markup for Panel
        m = self.load_markup()
        html = 'html' in m.lang
        ayame_panel = ayame_head = None
        for parent, index, element in walk(m.root):
            if element.qname == markup.AYAME_PANEL:
                if ayame_panel is None:
                    ayame_panel = element
            elif element.qname == markup.AYAME_HEAD:
                if (html and
                    ayame_head is None):
                    ayame_head = element
        if ayame_panel is None:
            throw(self, 'ayame:panel element is not found')
        # push ayame:head to parent component
        if ayame_head:
            self.push_ayame_head(ayame_head)
        # render ayame:panel
        return super(Panel, self).on_render(ayame_panel)

    def render_ayame_element(self, element):
        if element.qname == markup.AYAME_PANEL:
            element.qname = markup.DIV
            return element
        return super(Panel, self).render_ayame_element(element)
