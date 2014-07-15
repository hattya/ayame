#
# ayame.form
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

import collections
import operator

from . import _compat as five
from . import core, markup, uri, util, validator
from .exception import (ComponentError, ConversionError, RenderingError,
                        ValidationError)


__all__ = ['Form', 'FormComponent', 'Button', 'FileUploadField', 'TextField',
           'PasswordField', 'HiddenField', 'TextArea', 'CheckBox', 'Choice',
           'ChoiceRenderer', 'RadioChoice', 'CheckBoxChoice', 'SelectChoice']

# HTML elements
_BR = markup.QName(markup.XHTML_NS, u'br')

_FORM = markup.QName(markup.XHTML_NS, u'form')
_INPUT = markup.QName(markup.XHTML_NS, u'input')
_BUTTON = markup.QName(markup.XHTML_NS, u'button')
_TEXTAREA = markup.QName(markup.XHTML_NS, u'textarea')
_LABEL = markup.QName(markup.XHTML_NS, u'label')
_SELECT = markup.QName(markup.XHTML_NS, u'select')
_OPTION = markup.QName(markup.XHTML_NS, u'option')

# HTML attributes
_ID = markup.QName(markup.XHTML_NS, u'id')
_CLASS = markup.QName(markup.XHTML_NS, u'class')

_ACTION = markup.QName(markup.XHTML_NS, u'action')
_METHOD = markup.QName(markup.XHTML_NS, u'method')
_TYPE = markup.QName(markup.XHTML_NS, u'type')
_NAME = markup.QName(markup.XHTML_NS, u'name')
_VALUE = markup.QName(markup.XHTML_NS, u'value')
_CHECKED = markup.QName(markup.XHTML_NS, u'checked')
_FOR = markup.QName(markup.XHTML_NS, u'for')
_MULTIPLE = markup.QName(markup.XHTML_NS, u'multiple')
_SELECTED = markup.QName(markup.XHTML_NS, u'selected')


class Form(core.MarkupContainer):

    def __init__(self, id, model=None):
        super(Form, self).__init__(id, model)
        self._method = None

    def on_fire(self):
        form = self.element()
        if form is None:
            return
        # submit
        self._method = form.attrib.get(_METHOD, 'post').upper()
        try:
            self.submit()
        finally:
            self._method = None

    def on_render(self, element):
        if element.qname != _FORM:
            raise RenderingError(self, "'form' element is expected")
        elif _METHOD not in element.attrib:
            raise RenderingError(self,
                                 "'method' attribute is required for 'form' element")

        # modify attributes
        element.attrib[_ACTION] = uri.request_path(self.environ)
        element.attrib[_METHOD] = element.attrib[_METHOD].lower()
        # insert hidden field for marking
        div = markup.Element(markup.DIV)
        div.attrib[_CLASS] = u'ayame-hidden'
        input = markup.Element(_INPUT, type=markup.Element.EMPTY)
        input.attrib[_TYPE] = u'hidden'
        input.attrib[_NAME] = core.AYAME_PATH
        input.attrib[_VALUE] = self.path()
        div.append(input)
        element.insert(0, div)
        # render form
        return super(Form, self).on_render(element)

    def submit(self):
        if not (self.request.method == self._method or
                self.on_method_mismatch()):
            # abort
            return
        elif self.request.method == 'GET':
            values = self.request.query
        elif self.request.method == 'POST':
            values = self.request.form_data
        else:
            # unknown method
            return

        queue = collections.deque((self,))
        form = button = None
        valid = True
        while queue:
            c = queue.pop()
            if not c.visible:
                # skip invisible component
                continue
            elif isinstance(c, Form):
                # check nested form
                if form is not None:
                    raise ComponentError(self, "Form is nested")
                form = c
            elif isinstance(c, FormComponent):
                # validate
                name = c.relative_path()
                if isinstance(c, Button):
                    if (name in values and
                        button is None):
                        button = c
                elif isinstance(c, Choice):
                    c.validate(values[name] if name in values else [])
                else:
                    c.validate(values[name][0] if name in values else None)
                if valid:
                    valid = c.error is None
            # push children
            if isinstance(c, core.MarkupContainer):
                queue.extend(reversed(c.children))
        if not valid:
            if button is not None:
                button.on_error()
            self.on_error()
        else:
            if button is not None:
                button.on_submit()
            self.on_submit()

    def on_method_mismatch(self):
        return True  # continue

    def on_error(self):
        pass

    def on_submit(self):
        pass

    def has_error(self):
        for c, _ in self.walk():
            if (isinstance(c, FormComponent) and
                c.error):
                return True
        return False


class FormComponent(core.MarkupContainer):

    def __init__(self, id, model=None):
        super(FormComponent, self).__init__(id, model)
        self.required = False
        self.type = None
        self.error = None

    def relative_path(self):
        lis = [self.id]
        lis.extend(c.id for c in self.iter_parent(Form))
        # relative path from Form
        del lis[-1]
        return u':'.join(reversed(lis))

    def validate(self, value):
        try:
            # check required
            if (self.required and
                not value):
                raise self.required_error()
            # convert to object
            o = self.convert(value)
            # validate
            for b in self.behaviors:
                if isinstance(b, validator.Validator):
                    b.validate(o)
        except ValidationError as e:
            label = self.tr(self.id, self.parent)
            e.component = self
            e.vars.update(input=value,
                          name=self.id,
                          label=label if label is not None else self.id)
            self.error = e
            self.on_invalid()
        else:
            if self.model is not None:
                self.model.object = o
            self.on_valid()

    def on_valid(self):
        pass

    def on_invalid(self):
        pass

    def convert(self, value):
        if self.type is None:
            return value

        try:
            return self.converter_for(self.type).to_python(value)
        except ConversionError as e:
            raise self.conversion_error(e)

    def required_error(self):
        e = ValidationError()
        e.keys.append('Required')
        return e

    def conversion_error(self, ce):
        n = self.type.__name__
        e = ValidationError(five.str(ce))
        e.keys.append('Converter.' + n)
        e.keys.append('Converter')
        e.vars['type'] = n
        return e


class Button(FormComponent):

    def on_render(self, element):
        if element.qname == _INPUT:
            if element.attrib[_TYPE] not in ('submit', 'button', 'image'):
                raise RenderingError(self,
                                     "'input' element with 'type' attribute of "
                                     "'submit', 'button' or 'image' is expected")
        elif element.qname != _BUTTON:
            raise RenderingError(self,
                                 "'input' or 'button' element is expected")

        # modify attributes
        element.attrib[_NAME] = self.relative_path()
        # render button
        return super(Button, self).on_render(element)

    def on_error(self):
        pass

    def on_submit(self):
        pass


class FileUploadField(FormComponent):

    def on_render(self, element):
        if element.qname != _INPUT:
            raise RenderingError(self, "'input' element is expected")

        # modify attributes
        element.attrib[_TYPE] = u'file'
        element.attrib[_NAME] = self.relative_path()
        # render file upload field
        return super(FileUploadField, self).on_render(element)


class TextField(FormComponent):

    input_type = u'text'

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

    input_type = u'password'


class HiddenField(TextField):

    input_type = u'hidden'


class TextArea(FormComponent):

    def on_render(self, element):
        if element.qname != _TEXTAREA:
            raise RenderingError(self, "'textarea' element is expected")

        # modify attributes
        element.attrib[_NAME] = self.relative_path()
        # modify children
        element[:] = (self.model_object_as_string(),)
        # render text area
        return super(TextArea, self).on_render(element)


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

        checked = self.converter_for(self.type).to_python(self.model_object)
        # modify attributes
        element.attrib[_NAME] = self.relative_path()
        element.attrib[_VALUE] = u'on'
        if checked:
            element.attrib[_CHECKED] = u'checked'
        # render checkbox
        return super(CheckBox, self).on_render(element)


class Choice(FormComponent):

    def __init__(self, id, model=None, choices=None, renderer=None):
        super(Choice, self).__init__(id, model)
        self.choices = choices if choices is not None else []
        self.renderer = renderer if renderer is not None else ChoiceRenderer()
        self.multiple = False
        self.prefix = markup.Fragment()
        self.suffix = markup.Fragment()

    def validate(self, value):
        if self.choices:
            super(Choice, self).validate(value)

    def convert(self, value):
        if self.multiple:
            values = set(value)
            selected = []
            for i, choice in enumerate(self.choices):
                v = self.renderer.value_of(i, choice)
                if v in values:
                    values.remove(v)
                    selected.append(choice)
            if values:
                raise self.choice_error()
            return selected
        elif value:
            v = value[0]
            for i, choice in enumerate(self.choices):
                if self.renderer.value_of(i, choice) == v:
                    return choice
            raise self.choice_error()

    def choice_error(self):
        e = ValidationError()
        e.keys.append('Choice.' + ('multiple' if self.multiple else 'single'))
        return e

    def _id_prefix_for(self, element):
        id = element.attrib.get(_ID)
        return id if id else u'ayame-' + util.new_token()[:7]

    def render_element(self, element, index, choice):
        return element


class ChoiceRenderer(object):

    def label_for(self, object):
        label = object
        return label if label is not None else u''

    def value_of(self, index, object):
        return five.str(index)


class RadioChoice(Choice):

    def __init__(self, id, model=None, choices=None, renderer=None):
        super(RadioChoice, self).__init__(id, model, choices, renderer)
        self.suffix[:] = (markup.Element(_BR, type=markup.Element.EMPTY),)

    def on_render(self, element):
        # clear children
        del element[:]

        if self.choices:
            name = self.relative_path()
            selected = self.model_object
            pfx = self._id_prefix_for(element)
            last = len(self.choices) - 1
            for i, choice in enumerate(self.choices):
                id = u'-'.join((pfx, five.str(i)))
                # append prefix
                element.extend(self.prefix.copy())
                # radio button
                input = markup.Element(_INPUT, type=markup.Element.EMPTY)
                input.attrib[_ID] = id
                input.attrib[_TYPE] = u'radio'
                input.attrib[_NAME] = name
                input.attrib[_VALUE] = self.renderer.value_of(i, choice)
                if choice == selected:
                    input.attrib[_CHECKED] = u'checked'
                input = self.render_element(input, i, choice)
                element.append(input)
                # label
                s = self.renderer.label_for(choice)
                if not isinstance(s, five.string_type):
                    s = self.converter_for(s).to_string(s)
                label = markup.Element(_LABEL, type=markup.Element.EMPTY)
                label.attrib[_FOR] = id
                label.append(five.html_escape(s))
                label = self.render_element(label, i, choice)
                element.append(label)
                # append suffix
                if i < last:
                    element.extend(self.suffix.copy())
        # render radio choice
        return super(RadioChoice, self).on_render(element)


class CheckBoxChoice(Choice):

    def __init__(self, id, model=None, choices=None, renderer=None):
        super(CheckBoxChoice, self).__init__(id, model, choices, renderer)
        self.suffix[:] = (markup.Element(_BR, type=markup.Element.EMPTY),)

    def on_render(self, element):
        # clear children
        del element[:]

        if self.choices:
            name = self.relative_path()
            selected = self.model_object
            is_selected = operator.contains if self.multiple else operator.eq
            pfx = self._id_prefix_for(element)
            last = len(self.choices) - 1
            for i, choice in enumerate(self.choices):
                id = u'-'.join((pfx, five.str(i)))
                # append prefix
                element.extend(self.prefix.copy())
                # checkbox
                input = markup.Element(_INPUT, type=markup.Element.EMPTY)
                input.attrib[_ID] = id
                input.attrib[_TYPE] = u'checkbox'
                input.attrib[_NAME] = name
                input.attrib[_VALUE] = self.renderer.value_of(i, choice)
                if (selected is not None and
                    is_selected(selected, choice)):
                    input.attrib[_CHECKED] = u'checked'
                input = self.render_element(input, i, choice)
                element.append(input)
                # label
                s = self.renderer.label_for(choice)
                if not isinstance(s, five.string_type):
                    s = self.converter_for(s).to_string(s)
                label = markup.Element(_LABEL, type=markup.Element.EMPTY)
                label.attrib[_FOR] = id
                label.append(five.html_escape(s))
                label = self.render_element(label, i, choice)
                element.append(label)
                # append suffix
                if i < last:
                    element.extend(self.suffix.copy())
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
            element.attrib[_MULTIPLE] = u'multiple'
        elif _MULTIPLE in element.attrib:
            del element.attrib[_MULTIPLE]
        # clear children
        del element[:]

        if self.choices:
            selected = self.model_object
            is_selected = operator.contains if self.multiple else operator.eq
            last = len(self.choices) - 1
            for i, choice in enumerate(self.choices):
                # append prefix
                element.extend(self.prefix.copy())
                # option
                option = markup.Element(_OPTION, type=markup.Element.EMPTY)
                option.attrib[_VALUE] = self.renderer.value_of(i, choice)
                if (selected is not None and
                    is_selected(selected, choice)):
                    option.attrib[_SELECTED] = u'selected'
                option = self.render_element(option, i, choice)
                # label
                s = self.renderer.label_for(choice)
                if not isinstance(s, five.string_type):
                    s = self.converter_for(s).to_string(s)
                option.append(five.html_escape(s))
                element.append(option)
                # append suffix
                if i < last:
                    element.extend(self.suffix.copy())
        # render select choice
        return super(SelectChoice, self).on_render(element)
