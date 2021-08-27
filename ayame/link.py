#
# ayame.link
#
#   Copyright (c) 2012-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from . import _compat as five
from . import core, markup, uri, util
from . import model as mm
from .exception import ComponentError


__all__ = ['Link', 'ActionLink', 'PageLink']

# HTML elements
_A = markup.QName(markup.XHTML_NS, u'a')
_LINK = markup.QName(markup.XHTML_NS, u'link')
_AREA = markup.QName(markup.XHTML_NS, u'area')
_SCRIPT = markup.QName(markup.XHTML_NS, u'script')
_STYLE = markup.QName(markup.XHTML_NS, u'style')

# HTML attributes
_HREF = markup.QName(markup.XHTML_NS, u'href')
_SRC = markup.QName(markup.XHTML_NS, u'src')


class Link(core.MarkupContainer):

    def __init__(self, id, model=None):
        if isinstance(model, five.string_type):
            model = mm.Model(model)
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

    def on_fire(self):
        self.on_click()

    def new_uri(self, _):
        query = self.request.query.copy()
        query[core.AYAME_PATH] = [self.path()]
        environ = self.environ.copy()
        environ['QUERY_STRING'] = five.urlencode(query, doseq=True)
        return uri.request_uri(environ, True)

    def on_click(self):
        pass


class PageLink(Link):

    def __init__(self, id, page, values=None, anchor=''):
        super(PageLink, self).__init__(id, None)
        if (not issubclass(page, core.Page) or
            page is core.Page):
            raise ComponentError(self,
                                 "'{}' is not a subclass of Page".format(util.fqon_of(page)))
        self._page = page
        self._values = values
        self._anchor = anchor

    def new_uri(self, uri):
        return self.uri_for(self._page, self._values, self._anchor)
