#
# ayame.link
#
#   Copyright (c) 2012 Akinori Hattori <hattya@gmail.com>
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

import urllib

import ayame.core
from ayame.exception import ComponentError
import ayame.markup
import ayame.model
import ayame.uri


__all__ = ['Link', 'ActionLink', 'PageLink']

# HTML elements
_A = ayame.markup.QName(ayame.markup.XHTML_NS, u'a')
_LINK = ayame.markup.QName(ayame.markup.XHTML_NS, u'link')
_AREA = ayame.markup.QName(ayame.markup.XHTML_NS, u'area')
_SCRIPT = ayame.markup.QName(ayame.markup.XHTML_NS, u'script')
_STYLE = ayame.markup.QName(ayame.markup.XHTML_NS, u'style')

# HTML attributes
_HREF = ayame.markup.QName(ayame.markup.XHTML_NS, u'href')
_SRC = ayame.markup.QName(ayame.markup.XHTML_NS, u'src')

class Link(ayame.core.MarkupContainer):

    def __init__(self, id, model=None):
        if isinstance(model, basestring):
            model = ayame.model.Model(model)
        super(Link, self).__init__(id, model)

    def on_render(self, element):
        # modify attribute
        attr = None
        if element.qname in (_A, _LINK, _AREA):
            attr = _HREF
        elif element.qname in (_SCRIPT, _STYLE):
            attr = _SRC
        if attr is not None:
            uri = self.new_uri(element.attrib.get(attr))
            if uri is None:
                if attr in element.attrib:
                    del element.attrib[attr]
            else:
                element.attrib[attr] = uri
        # replace children by model object
        body = self.model_object_as_string()
        if body:
            element[:] = (body,)
        # render link
        return super(Link, self).on_render(element)

    def new_uri(self, uri):
        return uri

class ActionLink(Link):

    def __init__(self, id, model=None):
        super(ActionLink, self).__init__(id, model)

        self.add(_ActionLinkBehavior())

    def new_uri(self, _):
        query = self.request.query.copy()
        query[ayame.core.AYAME_PATH] = [self.path()]
        environ = self.environ.copy()
        environ['QUERY_STRING'] = urllib.urlencode(query, doseq=True)
        return ayame.uri.request_uri(environ, True)

    def on_click(self):
        pass

class _ActionLinkBehavior(ayame.core.IgnitionBehavior):

    def on_component(self, component, element):
        self.fire()

    def on_fire(self, component):
        component.on_click()

class PageLink(Link):

    def __init__(self, id, page, values=None, anchor=''):
        super(PageLink, self).__init__(id, None)
        if (not issubclass(page, ayame.core.Page) or
            page is ayame.core.Page):
            raise ComponentError(self,
                                 u'{!r} is not subclass of Page'.format(page))
        self._page = page
        self._values = values
        self._anchor = anchor

    def new_uri(self, uri):
        return self.uri_for(self._page, self._values, self._anchor)
