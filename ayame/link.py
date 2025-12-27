#
# ayame.link
#
#   Copyright (c) 2012-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
from collections.abc import Mapping
from typing import Any
import urllib.parse

from . import core, markup, model as mm, uri as um, util
from .exception import ComponentError


__all__ = ['Link', 'ActionLink', 'PageLink']

# HTML elements
_A = markup.QName(markup.XHTML_NS, 'a')
_LINK = markup.QName(markup.XHTML_NS, 'link')
_AREA = markup.QName(markup.XHTML_NS, 'area')
_SCRIPT = markup.QName(markup.XHTML_NS, 'script')
_STYLE = markup.QName(markup.XHTML_NS, 'style')

# HTML attributes
_HREF = markup.QName(markup.XHTML_NS, 'href')
_SRC = markup.QName(markup.XHTML_NS, 'src')


class Link(core.MarkupContainer):

    def __init__(self, id: str, model: mm.Model | str | None = None) -> None:
        super().__init__(id, mm.Model(model) if isinstance(model, str) else model)

    def on_render(self, element: markup.Element) -> markup.Node | list[markup.Node] | None:
        # modify attribute
        a = None
        if element.qname in (_A, _LINK, _AREA):
            a = _HREF
        elif element.qname in (_SCRIPT, _STYLE):
            a = _SRC
        if a is not None:
            if (uri := self.new_uri(element.attrib.get(a))) is not None:
                element.attrib[a] = uri
            elif a in element.attrib:
                del element.attrib[a]
        # replace children by model object
        if body := self.model_object_as_string():
            element.children[:] = (body,)
        # render link
        return super().on_render(element)

    def new_uri(self, uri: str | None) -> str | None:
        return uri


class ActionLink(Link):

    def on_fire(self) -> None:
        self.on_click()

    def new_uri(self, uri: str | None) -> str | None:
        query = self.request.query | {core.AYAME_PATH: [self.path()]}
        environ = self.environ | {'QUERY_STRING': urllib.parse.urlencode(query, doseq=True)}
        return um.request_uri(environ, True)

    def on_click(self) -> None:
        pass


class PageLink(Link):

    def __init__(self, id: str, page: type[core.Page], values: Mapping[str, Any] | None = None, anchor: Any = None) -> None:
        super().__init__(id, None)
        if not issubclass(page, core.Page):
            raise ComponentError(self, f"'{util.fqon_of(page)}' is not a subclass of Page")
        self._page = page
        self._values = values
        self._anchor = anchor

    def new_uri(self, uri: str | None) -> str | None:
        return self.uri_for(self._page, self._values, self._anchor)
