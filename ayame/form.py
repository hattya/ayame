#
# ayame.form
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

from __future__ import unicode_literals
import cgi
import collections
import operator

from ayame import core, markup, uri, util, validator
from ayame.exception import ComponentError, ConversionError, RenderingError
from ayame.exception import ValidationError


__all__ = ['Form', 'FormComponent', 'Button', 'TextField', 'PasswordField',
           'HiddenField', 'CheckBox', 'Choice', 'ChoiceRenderer',
           'RadioChoice', 'CheckBoxChoice', 'SelectChoice']

# HTML elements
_BR = markup.QName(markup.XHTML_NS, 'br')

_FORM = markup.QName(markup.XHTML_NS, 'form')
_INPUT = markup.QName(markup.XHTML_NS, 'input')
_BUTTON = markup.QName(markup.XHTML_NS, 'button')
_LABEL = markup.QName(markup.XHTML_NS, 'label')
_SELECT = markup.QName(markup.XHTML_NS, 'select')
_OPTION = markup.QName(markup.XHTML_NS, 'option')

# HTML attributes
_ID = markup.QName(markup.XHTML_NS, 'id')
_CLASS = markup.QName(markup.XHTML_NS, 'class')

_ACTION = markup.QName(markup.XHTML_NS, 'action')
_METHOD = markup.QName(markup.XHTML_NS, 'method')
_TYPE = markup.QName(markup.XHTML_NS, 'type')
_NAME = markup.QName(markup.XHTML_NS, 'name')
_VALUE = markup.QName(markup.XHTML_NS, 'value')
_CHECKED = markup.QName(markup.XHTML_NS, 'checked')
_FOR = markup.QName(markup.XHTML_NS, 'for')
_MULTIPLE = markup.QName(markup.XHTML_NS, 'multiple')
_SELECTED = markup.QName(markup.XHTML_NS, 'selected')

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
                elif isinstance(component, Choice):
                    value = values.get(name)
                    if component.multiple:
                        value = [] if value is None else value
                    else:
                        value = None if value is None else value[0]
                    component.validate(value)
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
        element.attrib[_VALUE] = self.model_object_as_string()
        # render text field
        return super(TextField, self).on_render(element)

class PasswordField(TextField):

    input_type = 'password'

class HiddenField(TextField):

    input_type = 'hidden'

class CheckBox(FormComponent):

    def __init__(self, id, model=None):
        super(CheckBox, self).__init__(id, model)
        self.type = bool

    def on_render(self, element):
        if element.qname != _INPUT:
            raise RenderingError(self, "'input' element is expected")
        elif element.attrib[_TYPE] != 'checkbox':
            raise RenderingError(self,
                                 "'input' element with 'type' attribute of "
                                 "'checkbox' is expected")

        converter = self.converter_for(self.type)
        checked = converter.to_python(self.model_object)
        # modify attributes
        element.attrib[_NAME] = self.relative_path()
        element.attrib[_VALUE] = 'on'
        if checked:
            element.attrib[_CHECKED] = 'checked'
        # render checkbox
        return super(CheckBox, self).on_render(element)

class Choice(FormComponent):

    def __init__(self, id, model=None, choices=None, renderer=None):
        super(Choice, self).__init__(id, model)
        self.choices = [] if choices is None else choices
        self.renderer = ChoiceRenderer() if renderer is None else renderer
        self.multiple = False
        self.prefix = []
        self.suffix = []

    def validate(self, value):
        if self.choices:
            if self.multiple:
                # convert to object
                values = set(value)
                selected = []
                for index, choice in enumerate(self.choices):
                    value = self.renderer.value_of(index, choice)
                    if value in values:
                        values.remove(value)
                        selected.append(choice)
                if not values:
                    # check required
                    if (self.required and
                        not selected):
                        self.on_invalid()
                        raise ValidationError()

                    if self.model is not None:
                        self.model.object = selected
                    return self.on_valid()
            else:
                if value is None:
                    return super(Choice, self).validate(value)
                for index, choice in enumerate(self.choices):
                    if self.renderer.value_of(index, choice) == value:
                        return super(Choice, self).validate(choice)

        self.on_invalid()
        raise ValidationError()

    def _id_prefix_for(self, element):
        id = element.attrib.get(_ID)
        return id if id else 'ayame-' + util.new_token()[:7]

    def render_element(self, element, index, choice):
        return element

class ChoiceRenderer(object):

    def label_for(self, object):
        label = object
        return '' if label is None else label

    def value_of(self, index, object):
        return unicode(index)

class RadioChoice(Choice):

    def __init__(self, id, model=None, choices=None, renderer=None):
        super(RadioChoice, self).__init__(id, model, choices, renderer)
        self.suffix = [markup.Element(_BR, type=markup.Element.EMPTY)]

    def on_render(self, element):
        # clear children
        element.children = []

        if self.choices:
            name = self.relative_path()
            selected = self.model_object
            id_prefix = self._id_prefix_for(element)
            last = len(self.choices) - 1
            for index, choice in enumerate(self.choices):
                id = '-'.join((id_prefix, unicode(index)))
                # append prefix
                element.children += self.prefix
                # radio button
                input = markup.Element(_INPUT, type=markup.Element.EMPTY)
                input.attrib[_ID] = id
                input.attrib[_TYPE] = 'radio'
                input.attrib[_NAME] = name
                input.attrib[_VALUE] = self.renderer.value_of(index, choice)
                if choice == selected:
                    input.attrib[_CHECKED] = 'checked'
                input = self.render_element(input, index, choice)
                element.children.append(input)
                # label
                text = self.renderer.label_for(choice)
                if not isinstance(text, basestring):
                    converter = self.converter_for(type(text))
                    text = converter.to_string(text)
                label = markup.Element(_LABEL, type=markup.Element.EMPTY)
                label.attrib[_FOR] = id
                label.children.append(cgi.escape(text, True))
                label = self.render_element(label, index, choice)
                element.children.append(label)
                # append suffix
                if index < last:
                    element.children += self.suffix
        # render radio choice
        return super(RadioChoice, self).on_render(element)

class CheckBoxChoice(Choice):

    def __init__(self, id, model=None, choices=None, renderer=None):
        super(CheckBoxChoice, self).__init__(id, model, choices, renderer)
        self.suffix = [markup.Element(_BR, type=markup.Element.EMPTY)]

    def on_render(self, element):
        # clear children
        element.children = []

        if self.choices:
            name = self.relative_path()
            selected = self.model_object
            is_selected = operator.contains if self.multiple else operator.eq
            id_prefix = self._id_prefix_for(element)
            last = len(self.choices) - 1
            for index, choice in enumerate(self.choices):
                id = '-'.join((id_prefix, unicode(index)))
                # append prefix
                element.children += self.prefix
                # checkbox
                input = markup.Element(_INPUT, type=markup.Element.EMPTY)
                input.attrib[_ID] = id
                input.attrib[_TYPE] = 'checkbox'
                input.attrib[_NAME] = name
                input.attrib[_VALUE] = self.renderer.value_of(index, choice)
                if (selected is not None and
                    is_selected(selected, choice)):
                    input.attrib[_CHECKED] = 'checked'
                input = self.render_element(input, index, choice)
                element.children.append(input)
                # label
                text = self.renderer.label_for(choice)
                if not isinstance(text, basestring):
                    converter = self.converter_for(type(text))
                    text = converter.to_string(text)
                label = markup.Element(_LABEL, type=markup.Element.EMPTY)
                label.attrib[_FOR] = id
                label.children.append(cgi.escape(text, True))
                label = self.render_element(label, index, choice)
                element.children.append(label)
                # append suffix
                if index < last:
                    element.children += self.suffix
        # render checkbox choice
        return super(CheckBoxChoice, self).on_render(element)

class SelectChoice(Choice):

    def __init__(self, id, model=None, choices=None, renderer=None):
        super(SelectChoice, self).__init__(id, model, choices, renderer)

    def on_render(self, element):
        if element.qname != _SELECT:
            raise RenderingError(self, "'select' element is expected")

        # modify attributes
        element.attrib[_NAME] = self.relative_path()
        if self.multiple:
            element.attrib[_MULTIPLE] = 'multiple'
        elif _MULTIPLE in element.attrib:
            del element.attrib[_MULTIPLE]
        # clear children
        element.children = []

        if self.choices:
            selected = self.model_object
            is_selected = operator.contains if self.multiple else operator.eq
            last = len(self.choices) - 1
            for index, choice in enumerate(self.choices):
                # append prefix
                element.children += self.prefix
                # option
                option = markup.Element(_OPTION, type=markup.Element.EMPTY)
                option.attrib[_VALUE] = self.renderer.value_of(index, choice)
                if (selected is not None and
                    is_selected(selected, choice)):
                    option.attrib[_SELECTED] = 'selected'
                option = self.render_element(option, index, choice)
                # label
                text = self.renderer.label_for(choice)
                if not isinstance(text, basestring):
                    converter = self.converter_for(type(text))
                    text = converter.to_string(text)
                option.children.append(cgi.escape(text, True))
                element.children.append(option)
                # append suffix
                if index < last:
                    element.children += self.suffix
        # render select choice
        return super(SelectChoice, self).on_render(element)
