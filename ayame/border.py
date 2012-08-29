#
# ayame.border
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

from ayame import core, markup
from ayame.exception import RenderingError


__all__ = ['Border']

class Border(core.MarkupContainer):

    def __init__(self, id, model=None):
        super(Border, self).__init__(id, model)
        self.render_body_only = True
        # ayame:body
        self.body = _BorderBody(id)
        self.body.render_body_only = True
        self.add_to_border(self.body)

    def add_to_border(self, *args):
        return super(Border, self).add(*args)

    def add(self, *args):
        return self.body.add(*args)

    def on_render(self, element):
        body = element

        def step(element, depth):
            return element.qname not in (markup.AYAME_BODY, markup.AYAME_HEAD)

        # load markup for Panel
        m = self.load_markup()
        if m.root is None:
            # markup is empty
            return element
        html = 'html' in m.lang
        ayame_border = ayame_body = ayame_head = None
        for element, depth in m.root.walk(step=step):
            if element.qname == markup.AYAME_BORDER:
                if ayame_border is None:
                    ayame_border = element
            elif element.qname == markup.AYAME_BODY:
                if (ayame_border is not None and
                    ayame_body is None):
                    # replace ayame:body
                    ayame_body = element
                    ayame_body.type = markup.Element.OPEN
                    ayame_body[:] = body.children
            elif element.qname == markup.AYAME_HEAD:
                if (html and
                    ayame_head is None):
                    ayame_head = element
        if ayame_border is None:
            raise RenderingError(self, "'ayame:border' element is not found")
        elif ayame_body is None:
            raise RenderingError(self, "'ayame:body' element is not found")
        # push ayame:head to parent component
        if ayame_head:
            self.push_ayame_head(ayame_head)
        # render ayame:border
        return super(Border, self).on_render(ayame_border)

    def render_ayame_element(self, element):
        if element.qname == markup.AYAME_BORDER:
            element.qname = markup.DIV
            return element
        elif element.qname == markup.AYAME_BODY:
            element.qname = markup.DIV
            element.attrib[markup.AYAME_ID] = self.body.id
            return element
        return super(Border, self).render_ayame_element(element)

class _BorderBody(core.MarkupContainer):

    def __init__(self, id, model=None):
        super(_BorderBody, self).__init__(id + u'_body', model)
