#
# ayame.border
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

from . import core, markup
from .exception import RenderingError


__all__ = ['Border']


class Border(core.MarkupContainer):

    def __init__(self, id, model=None):
        super(Border, self).__init__(id, model)
        self.has_markup = True
        self.render_body_only = True
        # ayame:body element
        self.body = _BorderBodyContainer(id)
        self.add_to_border(self.body)
        self.__body = False

    def add_to_border(self, *args):
        return super(Border, self).add(*args)

    def add(self, *args):
        for o in args:
            if isinstance(o, core._MessageContainer):
                self.add_to_border(o)
            else:
                self.body.add(o)
        return self

    def on_render(self, element):
        def step(element, depth):
            return element.qname not in (markup.AYAME_BODY, markup.AYAME_HEAD)

        # load markup for Panel
        m = self.load_markup()
        if m.root is None:
            # markup is empty
            return element

        body = element
        ayame_border = ayame_body = ayame_head = None
        for elem, _ in m.root.walk(step=step):
            if elem.qname == markup.AYAME_BORDER:
                if ayame_border is None:
                    ayame_border = elem
            elif elem.qname == markup.AYAME_BODY:
                if (ayame_border is not None and
                    ayame_body is None):
                    # replace children of ayame:body element
                    ayame_body = elem
                    ayame_body.type = markup.Element.OPEN
                    ayame_body[:] = body
            elif elem.qname == markup.AYAME_HEAD:
                if ('html' in m.lang and
                    ayame_head is None):
                    ayame_head = elem
        if ayame_border is None:
            raise RenderingError(self, "'ayame:border' element is not found")
        elif ayame_body is None:
            raise RenderingError(self, "'ayame:body' element is not found")
        # append ayame:head element to Page
        if ayame_head is not None:
            self.page().head.extend(ayame_head)
        # render ayame:border element
        return super(Border, self).on_render(ayame_border)

    def on_render_element(self, element):
        if element.qname == markup.AYAME_BORDER:
            return element
        elif element.qname == markup.AYAME_BODY:
            # skip duplicates
            if not self.__body:
                element.attrib[markup.AYAME_ID] = self.body.id
                self.__body = True
            return element
        return super(Border, self).on_render_element(element)


class _BorderBodyContainer(core.MarkupContainer):

    def __init__(self, id, model=None):
        super(_BorderBodyContainer, self).__init__(id + u'_body', model)
        self.render_body_only = True

    def on_render_element(self, element):
        if element.qname == markup.AYAME_BODY:
            return element
        return super(_BorderBodyContainer, self).on_render_element(element)

    def tr(self, key, component=None):
        # retrieve message from parent of Border
        return super(_BorderBodyContainer, self).tr(key, self.parent.parent)
