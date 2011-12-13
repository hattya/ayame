#
# ayame.form
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

from __future__ import unicode_literals
import collections

from ayame import core, markup, uri, validator
from ayame.exception import ComponentError, ConversionError, RenderingError
from ayame.exception import ValidationError


__all__ = ['Form', 'FormComponent', 'Button', 'TextField', 'PasswordField']

# HTML elements
_FORM = markup.QName(markup.XHTML_NS, 'form')
_INPUT = markup.QName(markup.XHTML_NS, 'input')
_BUTTON = markup.QName(markup.XHTML_NS, 'button')

# HTML attributes
_CLASS = markup.QName(markup.XHTML_NS, 'class')

_ACTION = markup.QName(markup.XHTML_NS, 'action')
_METHOD = markup.QName(markup.XHTML_NS, 'method')
_TYPE = markup.QName(markup.XHTML_NS, 'type')
_NAME = markup.QName(markup.XHTML_NS, 'name')
_VALUE = markup.QName(markup.XHTML_NS, 'value')

class Form(core.MarkupContainer):

    def __init__(self, id, model=None):
        super(Form, self).__init__(id, model)
        self._method = None

        self.add(_FormActionBehavior())

    def on_render(self, element):
        if element.qname != _FORM:
            raise RenderingError(self, "'form' element is expected")
        elif _METHOD not in element.attrib:
            raise RenderingError(
                    self, "'method' attribute is required for 'form' element")

        # modify attributes
        self._method = element.attrib[_METHOD].upper()
        element.attrib[_ACTION] = unicode(uri.request_path(self.environ))
        element.attrib[_METHOD] = self._method.lower()
        # insert hidden field for marking
        div = markup.Element(markup.DIV)
        div.attrib[_CLASS] = 'ayame-hidden'
        input = markup.Element(_INPUT, type=markup.Element.EMPTY)
        input.attrib[_TYPE] = 'hidden'
        input.attrib[_NAME] = unicode(core.AYAME_PATH)
        input.attrib[_VALUE] = unicode(self.path())
        div.children.append(input)
        element.children.insert(0, div)
        # render form
        return super(Form, self).on_render(element)

    def submit(self, request):
        if (request.method != self._method and
            not self.on_method_mismatch()):
            return  # abort
        elif request.method == 'GET':
            values = request.query
        elif request.method == 'POST':
            values = request.body
        else:
            return  # unknown method

        form = button = None
        queue = collections.deque()
        queue.append(self)
        while queue:
            component = queue.pop()
            # check nested form
            if isinstance(component, Form):
                if form is not None:
                    raise ComponentError(self, "'form' element is nested")
                form = component
            # validate
            if isinstance(component, FormComponent):
                name = component.relative_path()
                if isinstance(component, Button):
                    if (name in values and
                        button is None):
                        button = component
                else:
                    value = values.get(name)
                    component.validate(None if value is None else value[0])
            # push children
            if isinstance(component, core.MarkupContainer):
                queue.extend(reversed(component.children))
        if button is not None:
            button.on_submit()
        self.on_submit()

    def on_method_mismatch(self):
        return True  # continue

    def on_submit(self):
        pass

class _FormActionBehavior(core.IgnitionBehavior):

    def on_after_render(self, component):
        self.fire()

    def on_fire(self, component, request):
        component.submit(request)

class FormComponent(core.MarkupContainer):

    def __init__(self, id, model=None):
        super(FormComponent, self).__init__(id, model)
        self.required = False
        self.type = None

    def relative_path(self):
        current = self
        buf = []
        while not (isinstance(current, Form) or
                   current.parent is None):
            buf.append(current.id)
            current = current.parent
        if not isinstance(current, Form):
            raise ComponentError(self, 'component is not attached to Form')
        return ':'.join(reversed(buf))

    def validate(self, value):
        try:
            # check required
            if (self.required and
                not value):
                raise ValidationError()
            # convert to object
            if self.type is not None:
                try:
                    converter = self.converter_for(self.type)
                    object = converter.to_python(value)
                except ConversionError as e:
                    raise ValidationError(unicode(e))
            else:
                object = value
            # validate
            for behavior in self.behaviors:
                if isinstance(behavior, validator.Validator):
                    behavior.validate(object)
        except ValidationError:
            self.on_invalid()
            raise

        if self.model is not None:
            self.model.object = object
        self.on_valid()

    def on_valid(self):
        pass

    def on_invalid(self):
        pass

class Button(FormComponent):

    def on_render(self, element):
        if element.qname == _INPUT:
            if element.attrib[_TYPE] not in ('submit', 'button', 'image'):
                raise RenderingError(
                        self,
                        "'input' element with 'type' attribute of 'submit', "
                        "'button' or 'image' is expected")
        elif element.qname != _BUTTON:
            raise RenderingError(self,
                                 "'input' or 'button' element is expected")

        # modify attributes
        element.attrib[_NAME] = self.relative_path()
        # render button
        return super(Button, self).on_render(element)

    def on_submit(self):
        pass

class TextField(FormComponent):

    input_type = 'text'

    def on_render(self, element):
        if element.qname != _INPUT:
            raise RenderingError(self, "'input' element is expected")

        # modify attributes
        element.attrib[_TYPE] = self.input_type
        element.attrib[_NAME] = self.relative_path()
        # render text field
        return super(TextField, self).on_render(element)

class PasswordField(TextField):

    input_type = 'password'
