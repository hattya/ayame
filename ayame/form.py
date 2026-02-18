#
# ayame.form
#
#   Copyright (c) 2011-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import collections
from collections.abc import Sequence
import html
import operator
from typing import TYPE_CHECKING, Any

from . import core, markup, uri, util, validator
from .exception import (ComponentError, ConversionError, RenderingError,
                        ValidationError)

if TYPE_CHECKING:
    from . import model as mm


__all__ = ['Form', 'FormComponent', 'Button', 'FileUploadField', 'TextField',
           'PasswordField', 'HiddenField', 'TextArea', 'CheckBox', 'Choice',
           'ChoiceRenderer', 'RadioChoice', 'CheckBoxChoice', 'SelectChoice']

# HTML elements
_BR = markup.QName(markup.XHTML_NS, 'br')

_FORM = markup.QName(markup.XHTML_NS, 'form')
_INPUT = markup.QName(markup.XHTML_NS, 'input')
_BUTTON = markup.QName(markup.XHTML_NS, 'button')
_TEXTAREA = markup.QName(markup.XHTML_NS, 'textarea')
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

    _method: str | None

    def __init__(self, id: str, model: mm.Model | None = None) -> None:
        super().__init__(id, model)
        self._method = None

    def on_fire(self) -> None:
        form = self.element()
        if form is None:
            return
        # submit
        self._method = v.upper() if (v := form.attrib.get(_METHOD)) else 'POST'
        try:
            self.submit()
        finally:
            self._method = None

    def on_render(self, element: markup.Element) -> markup.Node | list[markup.Node] | None:
        if element.qname != _FORM:
            raise RenderingError(self, "'form' element is expected")
        elif _METHOD not in element.attrib:
            raise RenderingError(self, "'method' attribute is required for 'form' element")

        # modify attributes
        element.attrib[_ACTION] = uri.request_path(self.environ)
        element.attrib[_METHOD] = v.lower() if (v := element.attrib[_METHOD]) else v
        # insert hidden field for marking
        div = markup.Element(markup.DIV)
        div.attrib[_CLASS] = 'ayame-hidden'
        input = markup.Element(_INPUT, type=markup.Element.Type.EMPTY)
        input.attrib[_TYPE] = 'hidden'
        input.attrib[_NAME] = core.AYAME_PATH
        input.attrib[_VALUE] = self.path()
        div.append(input)
        element.insert(0, div)
        # render form
        return super().on_render(element)

    def submit(self) -> None:
        values: dict[str, list[Any]]
        if not (self.request.method == self._method
                or self.on_method_mismatch()):
            # abort
            return
        elif self.request.method == 'GET':
            values = self.request.query
        elif self.request.method == 'POST':
            values = self.request.form_data
        else:
            # unknown method
            return

        queue: collections.deque[core.Component] = collections.deque((self,))
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
                    raise ComponentError(self, 'Form is nested')
                form = c
            elif isinstance(c, FormComponent):
                # validate
                name = c.relative_path()
                if isinstance(c, Button):
                    if (name in values
                        and button is None):
                        button = c
                elif isinstance(c, Choice):
                    c.validate(v if (v := values.get(name)) else [])
                else:
                    c.validate(v[0] if (v := values.get(name)) else None)
                if valid:
                    valid = c.error is None
            # push children
            if isinstance(c, core.MarkupContainer):
                queue.extend(reversed(c.children))
        if valid:
            if button is not None:
                button.on_submit()
            self.on_submit()
        else:
            if button is not None:
                button.on_error()
            self.on_error()

    def on_method_mismatch(self) -> bool:
        return True  # continue

    def on_submit(self) -> None:
        pass

    def on_error(self) -> None:
        pass

    def has_error(self) -> bool:
        for c, _ in self.walk():
            if (isinstance(c, FormComponent)
                and c.error):
                return True
        return False


class FormComponent(core.MarkupContainer):

    required: bool
    type: type | None
    error: ValidationError | None

    def __init__(self, id: str, model: mm.Model | None = None) -> None:
        super().__init__(id, model)
        self.required = False
        self.type = None
        self.error = None

    def relative_path(self) -> str:
        lis = [self.id]
        lis.extend(c.id for c in self.iter_parent(Form))
        # relative path from Form
        del lis[-1]
        return ':'.join(reversed(lis))

    def validate(self, value: Any) -> None:
        try:
            # check required
            if (self.required
                and not value):
                raise self.required_error()
            # convert to object
            o = self.convert(value)
            # validate
            for b in self.behaviors:
                if isinstance(b, validator.Validator):
                    b.validate(o)
        except ValidationError as e:
            e.component = self
            e.vars.update(input=value,
                          name=self.id,
                          label=s if (s := self.tr(self.id, self.parent)) is not None else self.id)
            self.error = e
            self.on_invalid()
        else:
            if self.model is not None:
                self.model.object = o
            self.on_valid()

    def on_valid(self) -> None:
        pass

    def on_invalid(self) -> None:
        pass

    def convert(self, value: Any) -> Any:
        if self.type is None:
            return value

        try:
            return self.converter_for(self.type).to_python(value)
        except ConversionError as e:
            raise self.conversion_error(e)

    def required_error(self) -> ValidationError:
        e = ValidationError()
        e.keys.append('Required')
        return e

    def conversion_error(self, ce: ConversionError) -> ValidationError:
        assert self.type is not None
        n = self.type.__name__
        e = ValidationError(str(ce))
        e.keys.append('Converter.' + n)
        e.keys.append('Converter')
        e.vars['type'] = n
        return e


class Button(FormComponent):

    def on_render(self, element: markup.Element) -> markup.Node | list[markup.Node] | None:
        if element.qname == _INPUT:
            if element.attrib[_TYPE] not in ('submit', 'button', 'image'):
                raise RenderingError(self, "'input' element with 'type' attribute of 'submit', 'button' or 'image' is expected")
        elif element.qname != _BUTTON:
            raise RenderingError(self, "'input' or 'button' element is expected")

        # modify attributes
        element.attrib[_NAME] = self.relative_path()
        # render button
        return super().on_render(element)

    def on_submit(self) -> None:
        pass

    def on_error(self) -> None:
        pass


class FileUploadField(FormComponent):

    def on_render(self, element: markup.Element) -> markup.Node | list[markup.Node] | None:
        if element.qname != _INPUT:
            raise RenderingError(self, "'input' element is expected")

        # modify attributes
        element.attrib[_TYPE] = 'file'
        element.attrib[_NAME] = self.relative_path()
        # render file upload field
        return super().on_render(element)


class TextField(FormComponent):

    input_type = 'text'

    def on_render(self, element: markup.Element) -> markup.Node | list[markup.Node] | None:
        if element.qname != _INPUT:
            raise RenderingError(self, "'input' element is expected")

        # modify attributes
        element.attrib[_TYPE] = self.input_type
        element.attrib[_NAME] = self.relative_path()
        element.attrib[_VALUE] = self.model_object_as_string()
        # render text field
        return super().on_render(element)


class PasswordField(TextField):

    input_type = 'password'


class HiddenField(TextField):

    input_type = 'hidden'


class TextArea(FormComponent):

    def on_render(self, element: markup.Element) -> markup.Node | list[markup.Node] | None:
        if element.qname != _TEXTAREA:
            raise RenderingError(self, "'textarea' element is expected")

        # modify attributes
        element.attrib[_NAME] = self.relative_path()
        # modify children
        element.children[:] = (self.model_object_as_string(),)
        # render text area
        return super().on_render(element)


class CheckBox(FormComponent):

    def __init__(self, id: str, model: mm.Model | None = None) -> None:
        super().__init__(id, model)
        self.type = bool

    def on_render(self, element: markup.Element) -> markup.Node | list[markup.Node] | None:
        if element.qname != _INPUT:
            raise RenderingError(self, "'input' element is expected")
        elif element.attrib[_TYPE] != 'checkbox':
            raise RenderingError(self, "'input' element with 'type' attribute of 'checkbox' is expected")

        checked = self.converter_for(self.type).to_python(self.model_object)
        # modify attributes
        element.attrib[_NAME] = self.relative_path()
        element.attrib[_VALUE] = 'on'
        if checked:
            element.attrib[_CHECKED] = 'checked'
        # render checkbox
        return super().on_render(element)


class Choice(FormComponent):

    def __init__(self, id: str, model: mm.Model | None = None,
                 choices: Sequence[Any] | None = None, renderer: ChoiceRenderer | None = None) -> None:
        super().__init__(id, model)
        self.choices = choices if choices is not None else []
        self.renderer = renderer if renderer is not None else ChoiceRenderer()
        self.multiple = False
        self.prefix = markup.Fragment()
        self.suffix = markup.Fragment()

    def validate(self, value: Any) -> None:
        if self.choices:
            super().validate(value)

    def convert(self, value: Any) -> Any:
        if self.multiple:
            values = set(value)
            selected = []
            for i, choice in enumerate(self.choices):
                if (v := self.renderer.value_of(i, choice)) in values:
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
        return None

    def choice_error(self) -> ValidationError:
        e = ValidationError()
        e.keys.append(f'Choice.{"multiple" if self.multiple else "single"}')
        return e

    def _id_prefix_for(self, element: markup.Element) -> str:
        return element.attrib.get(_ID) or 'ayame-' + util.new_token()[:7]

    def render_element(self, element: markup.Element, index: int, choice: Any) -> markup.Element:
        return element


class ChoiceRenderer:

    def label_for(self, object: Any) -> Any:
        return object if object is not None else ''

    def value_of(self, index: int, object: Any) -> str:
        return str(index)


class RadioChoice(Choice):

    def __init__(self, id: str, model: mm.Model | None = None,
                 choices: Sequence[Any] | None = None, renderer: ChoiceRenderer | None = None) -> None:
        super().__init__(id, model, choices, renderer)
        self.suffix[:] = (markup.Element(_BR, type=markup.Element.Type.EMPTY),)

    def on_render(self, element: markup.Element) -> markup.Node | list[markup.Node] | None:
        # clear children
        element.children.clear()

        if self.choices:
            name = self.relative_path()
            selected = self.model_object
            pfx = self._id_prefix_for(element)
            last = len(self.choices) - 1
            for i, choice in enumerate(self.choices):
                id = f'{pfx}-{i}'
                # append prefix
                element.extend(self.prefix.copy())
                # radio button
                input = markup.Element(_INPUT, type=markup.Element.Type.EMPTY)
                input.attrib[_ID] = id
                input.attrib[_TYPE] = 'radio'
                input.attrib[_NAME] = name
                input.attrib[_VALUE] = self.renderer.value_of(i, choice)
                if choice == selected:
                    input.attrib[_CHECKED] = 'checked'
                input = self.render_element(input, i, choice)
                element.append(input)
                # label
                s = self.renderer.label_for(choice)
                if not isinstance(s, str):
                    s = self.converter_for(s).to_string(s)
                label = markup.Element(_LABEL, type=markup.Element.Type.EMPTY)
                label.attrib[_FOR] = id
                label.append(html.escape(s))
                label = self.render_element(label, i, choice)
                element.append(label)
                # append suffix
                if i < last:
                    element.extend(self.suffix.copy())
        # render radio choice
        return super().on_render(element)


class CheckBoxChoice(Choice):

    def __init__(self, id: str, model: mm.Model | None = None,
                 choices: Sequence[Any] | None = None, renderer: ChoiceRenderer | None = None) -> None:
        super().__init__(id, model, choices, renderer)
        self.suffix[:] = (markup.Element(_BR, type=markup.Element.Type.EMPTY),)

    def on_render(self, element: markup.Element) -> markup.Node | list[markup.Node] | None:
        # clear children
        element.children.clear()

        if self.choices:
            name = self.relative_path()
            selected = self.model_object
            is_selected = operator.contains if self.multiple else operator.eq
            pfx = self._id_prefix_for(element)
            last = len(self.choices) - 1
            for i, choice in enumerate(self.choices):
                id = f'{pfx}-{i}'
                # append prefix
                element.extend(self.prefix.copy())
                # checkbox
                input = markup.Element(_INPUT, type=markup.Element.Type.EMPTY)
                input.attrib[_ID] = id
                input.attrib[_TYPE] = 'checkbox'
                input.attrib[_NAME] = name
                input.attrib[_VALUE] = self.renderer.value_of(i, choice)
                if (selected is not None
                    and is_selected(selected, choice)):
                    input.attrib[_CHECKED] = 'checked'
                input = self.render_element(input, i, choice)
                element.append(input)
                # label
                s = self.renderer.label_for(choice)
                if not isinstance(s, str):
                    s = self.converter_for(s).to_string(s)
                label = markup.Element(_LABEL, type=markup.Element.Type.EMPTY)
                label.attrib[_FOR] = id
                label.append(html.escape(s))
                label = self.render_element(label, i, choice)
                element.append(label)
                # append suffix
                if i < last:
                    element.extend(self.suffix.copy())
        # render checkbox choice
        return super().on_render(element)


class SelectChoice(Choice):

    def __init__(self, id: str, model: mm.Model | None = None,
                 choices: Sequence[Any] | None = None, renderer: ChoiceRenderer | None = None) -> None:
        super().__init__(id, model, choices, renderer)

    def on_render(self, element: markup.Element) -> markup.Node | list[markup.Node] | None:
        if element.qname != _SELECT:
            raise RenderingError(self, "'select' element is expected")

        # modify attributes
        element.attrib[_NAME] = self.relative_path()
        if self.multiple:
            element.attrib[_MULTIPLE] = 'multiple'
        elif _MULTIPLE in element.attrib:
            del element.attrib[_MULTIPLE]
        # clear children
        element.children.clear()

        if self.choices:
            selected = self.model_object
            is_selected = operator.contains if self.multiple else operator.eq
            last = len(self.choices) - 1
            for i, choice in enumerate(self.choices):
                # append prefix
                element.extend(self.prefix.copy())
                # option
                option = markup.Element(_OPTION, type=markup.Element.Type.EMPTY)
                option.attrib[_VALUE] = self.renderer.value_of(i, choice)
                if (selected is not None
                    and is_selected(selected, choice)):
                    option.attrib[_SELECTED] = 'selected'
                option = self.render_element(option, i, choice)
                # label
                s = self.renderer.label_for(choice)
                if not isinstance(s, str):
                    s = self.converter_for(s).to_string(s)
                option.append(html.escape(s))
                element.append(option)
                # append suffix
                if i < last:
                    element.extend(self.suffix.copy())
        # render select choice
        return super().on_render(element)
