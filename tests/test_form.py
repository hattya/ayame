#
# test_form
#
#   Copyright (c) 2011-2013 Akinori Hattori <hattya@gmail.com>
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

import datetime

import ayame
from ayame import basic, form, http, markup, model, validator
from base import AyameTestCase


class FormTestCase(AyameTestCase):

    def setup(self):
        super(FormTestCase, self).setup()
        self.app.config['ayame.markup.pretty'] = True
        self.boundary = 'ayame.form'

    def new_environ(self, method='GET', query='', body=None):
        return super(FormTestCase, self).new_environ(
            method=method, path='/form', query=query, body=body)

    def test_form_invalid_markup(self):
        # not form element
        f = form.Form('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      r"'form' .* expected\b"):
            f.render(markup.Element(markup.DIV))

        # method is not found
        root = markup.Element(form._FORM,
                              attrib={form._ACTION: u'/'})
        f = form.Form('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      "'method' .* required .* 'form'"):
            f.render(root)

    def test_form_method(self):
        class Form(form.Form):
            def on_method_mismatch(self):
                return False

        f = Form('a')
        query = 'b=1'
        with self.application(self.new_environ(query=query)):
            f._method = 'POST'
            f.submit()

        f = form.Form('a')
        query = 'b=1'
        with self.application(self.new_environ(method='PUT', query=query)):
            f._method = 'POST'
            f.submit()

    def test_nested_form(self):
        f = form.Form('a')
        f.add(form.Form('b'))
        with self.application(self.new_environ(method='POST')):
            f._method = 'POST'
            with self.assert_raises_regex(ayame.ComponentError,
                                          r"\bForm is nested\b"):
                f.submit()

    def test_form_duplicate_buttons(self):
        class Button(form.Button):
            def relative_path(self):
                return super(Button, self).relative_path()[:-1]
            def on_submit(self):
                raise Valid(self.id)

        f = form.Form('a')
        f.add(Button('b1'))
        f.add(Button('b2'))
        query = ('{path}=a&'
                 'b')
        with self.application(self.new_environ(query=query)):
            f._method = 'GET'
            with self.assert_raises_regex(Valid, '^b1$'):
                f.submit()

    def test_form(self):
        with self.application(self.new_environ()):
            p = SpamPage()
            status, headers, content = p.render()
        html = self.format(SpamPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

        f = p.find('form')
        self.assert_equal(f.model_object['text'], '')
        self.assert_equal(f.model_object['password'], '')
        self.assert_equal(f.model_object['hidden'], '')
        self.assert_equal(f.model_object['area'], 'Hello World!')
        self.assert_equal(f.model_object['checkbox'], True)
        self.assert_is_none(f.model_object['file'])
        self.assert_not_in('button', f.model_object)

    def test_form_get(self):
        query = ('{path}=form&'
                 'text=text&'
                 'password=password&'
                 'hidden=hidden&'
                 'area=area&'
                 'file=a.txt')
        with self.application(self.new_environ(query=query)):
            p = SpamPage()
            with self.assert_raises_regex(Valid, '^form$'):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object,
                          {'text': 'text',
                           'password': 'password',
                           'hidden': 'hidden',
                           'area': 'area',
                           'checkbox': False,
                           'file': 'a.txt'})
        self.assert_false(f.has_error())

        query = ('{path}=form&'
                 'text=text&'
                 'password=password&'
                 'hidden=hidden&'
                 'area=area&'
                 'file=a.txt&'
                 'button')
        with self.application(self.new_environ(query=query)):
            p = SpamPage()
            with self.assert_raises_regex(Valid, '^button$'):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object,
                          {'text': 'text',
                           'password': 'password',
                           'hidden': 'hidden',
                           'area': 'area',
                           'checkbox': False,
                           'file': 'a.txt',
                           'button': 'submitted'})
        self.assert_false(f.has_error())

    def test_form_post(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="text"

text
{__}
Content-Disposition: form-data; name="password"

password
{__}
Content-Disposition: form-data; name="hidden"

hidden
{__}
Content-Disposition: form-data; name="area"

area
{__}
Content-Disposition: form-data; name="file"; filename="a.txt"
Content-Type: text/plain

spam
eggs
ham

{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = SpamPage()
            with self.assert_raises_regex(Valid, '^form$'):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object['text'], 'text')
        self.assert_equal(f.model_object['password'], 'password')
        self.assert_equal(f.model_object['hidden'], 'hidden')
        self.assert_equal(f.model_object['area'], 'area')
        self.assert_equal(f.model_object['checkbox'], False)
        self.assert_equal(f.model_object['file'].name, 'file')
        self.assert_equal(f.model_object['file'].filename, 'a.txt')
        self.assert_equal(f.model_object['file'].value, (b'spam\n'
                                                         b'eggs\n'
                                                         b'ham\n'))
        self.assert_is_not_none(f.model_object['file'].file)
        self.assert_equal(f.model_object['file'].type, 'text/plain')
        self.assert_equal(f.model_object['file'].type_options, {})
        self.assert_not_in('button', f.model_object)
        self.assert_false(f.has_error())

        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="text"

text
{__}
Content-Disposition: form-data; name="password"

password
{__}
Content-Disposition: form-data; name="hidden"

hidden
{__}
Content-Disposition: form-data; name="area"

area
{__}
Content-Disposition: form-data; name="file"; filename="a.txt"
Content-Type: text/plain

spam
eggs
ham

{__}
Content-Disposition: form-data; name="button"

{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = SpamPage()
            with self.assert_raises_regex(Valid, '^button$'):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object['text'], 'text')
        self.assert_equal(f.model_object['password'], 'password')
        self.assert_equal(f.model_object['hidden'], 'hidden')
        self.assert_equal(f.model_object['area'], 'area')
        self.assert_equal(f.model_object['checkbox'], False)
        self.assert_equal(f.model_object['file'].name, 'file')
        self.assert_equal(f.model_object['file'].filename, 'a.txt')
        self.assert_equal(f.model_object['file'].value, (b'spam\n'
                                                         b'eggs\n'
                                                         b'ham\n'))
        self.assert_is_not_none(f.model_object['file'].file)
        self.assert_equal(f.model_object['file'].type, 'text/plain')
        self.assert_equal(f.model_object['file'].type_options, {})
        self.assert_equal(f.model_object['button'], 'submitted')
        self.assert_false(f.has_error())

    def test_form_required_error(self):
        query = ('{path}=form&'
                 'area=area&'
                 'file=a.txt&'
                 'button')
        with self.application(self.new_environ(query=query)):
            p = SpamPage()
            p.find('form:text').required = True
            p.find('form:password').required = True
            p.find('form:hidden').required = True
            with self.assert_raises(Invalid):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object, {'text': '',
                                           'password': '',
                                           'hidden': '',
                                           'area': 'area',
                                           'checkbox': False,
                                           'file': 'a.txt'})
        self.assert_true(f.has_error())
        self.assert_is_instance(f.find('text').error,
                                ayame.ValidationError)
        self.assert_is_instance(f.find('password').error,
                                ayame.ValidationError)
        self.assert_is_instance(f.find('hidden').error,
                                ayame.ValidationError)
        self.assert_is_none(f.find('area').error)
        self.assert_is_none(f.find('checkbox').error)
        self.assert_is_none(f.find('file').error)

    def test_form_component_relative_path(self):
        f = form.Form('a')
        f.add(form.FormComponent('b1'))
        f.add(ayame.MarkupContainer('b2'))
        f.find('b2').add(form.FormComponent('c'))

        self.assert_equal(f.find('b1').relative_path(), 'b1')
        self.assert_equal(f.find('b2:c').relative_path(), 'b2:c')
        with self.assert_raises_regex(ayame.ComponentError,
                                      r' is not attached .*\.Form\b'):
            form.FormComponent('a').relative_path()

    def test_form_component_required_error(self):
        fc = form.FormComponent('a')
        fc.required = True
        self.assert_is_none(fc.error)

        fc.validate(None)
        self.assert_is_instance(fc.error, ayame.ValidationError)
        fc.validate('')
        self.assert_is_instance(fc.error, ayame.ValidationError)

    def test_form_component_conversion_error(self):
        with self.application():
            fc = form.FormComponent('a')
            fc.type = int
            self.assert_is_none(fc.error)
            fc.validate('a')
            self.assert_is_instance(fc.error, ayame.ValidationError)

    def test_form_component_validation_error(self):
        with self.application():
            fc = form.FormComponent('a')
            fc.add(validator.StringValidator(max=4))
            self.assert_is_none(fc.error)
            fc.validate('.info')
            self.assert_is_instance(fc.error, ayame.ValidationError)

    def test_form_component_no_model(self):
        with self.application():
            fc = form.FormComponent('a')
            fc.validate('a')
            self.assert_is_none(fc.error)
            self.assert_is_none(fc.model)
            self.assert_is_none(fc.model_object)

    def test_button(self):
        element = markup.Element(form._FORM,
                                 attrib={form._METHOD: 'GET'})
        button = markup.Element(form._BUTTON,
                                attrib={markup.AYAME_ID: 'b'})
        element.append(button)
        with self.application(self.new_environ()):
            f = form.Form('a')
            f.add(form.Button('b'))
            element = f.render(element)
        self.assert_equal(len(element), 2)
        button = element.children[1]
        self.assert_equal(button.attrib, {form._NAME: 'b'})

    def test_button_invalid_markup(self):
        input = markup.Element(form._INPUT,
                               attrib={form._TYPE: 'text'})

        fc = form.Button('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      "'input' .* 'submit'"):
            fc.render(input)
        with self.assert_raises_regex(ayame.RenderingError,
                                      "'input' or 'button' element "):
            fc.render(markup.Element(markup.DIV))

    def test_file_upload_field_invalid_markup(self):
        fc = form.FileUploadField('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      "'input' element is "):
            fc.render(markup.Element(markup.DIV))

    def test_text_field_invalid_markup(self):
        fc = form.TextField('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      "'input' element is "):
            fc.render(markup.Element(markup.DIV))

    def test_text_area_invalid_markup(self):
        fc = form.TextArea('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      "'textarea' element is "):
            fc.render(markup.Element(markup.DIV))

    def test_check_box(self):
        element = markup.Element(form._FORM,
                                 attrib={form._METHOD: 'GET'})
        input = markup.Element(form._INPUT,
                               attrib={markup.AYAME_ID: 'b',
                                       form._TYPE: 'checkbox'})
        element.append(input)
        with self.application(self.new_environ()):
            f = form.Form('a')
            f.add(form.CheckBox('b'))
            f.render(element)
        self.assert_equal(len(element), 2)
        input = element.children[1]
        self.assert_equal(input.attrib, {form._NAME: 'b',
                                         form._TYPE: 'checkbox',
                                         form._VALUE: 'on'})

    def test_check_box_invalid_markup(self):
        input = markup.Element(form._INPUT,
                               attrib={form._TYPE: 'text'})

        fc = form.CheckBox('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      "'input' .* 'checkbox'"):
            fc.render(input)
        with self.assert_raises_regex(ayame.RenderingError,
                                      "'input' element is "):
            fc.render(markup.Element(markup.DIV))

    def test_choice(self):
        fc = form.Choice('a')
        s = fc._id_prefix_for(markup.Element(markup.DIV))
        self.assert_true(s)
        self.assert_false(s[0].isdigit())

    def test_radio_choice(self):
        with self.application(self.new_environ()):
            p = EggsPage()
            status, headers, content = p.render()
        html = self.format(EggsPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

        f = p.find('form')
        self.assert_equal(f.model_object, {'radio': p.choices[0]})

    def test_radio_choice_with_renderer(self):
        with self.application(self.new_environ()):
            p = EggsPage()
            p.find('form:radio').renderer = ChoiceRenderer()
            status, headers, content = p.render()
        html = self.format(EggsPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

        f = p.find('form')
        self.assert_equal(f.model_object, {'radio': p.choices[0]})

    def test_radio_choice_no_choices(self):
        with self.application(self.new_environ()):
            p = EggsPage()
            p.find('form:radio').choices = []
            status, headers, content = p.render()
        html = self.format(EggsPage, choices=False)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

        f = p.find('form')
        self.assert_equal(f.model_object, {'radio': p.choices[0]})

    def test_radio_choice_post(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="radio"

2
{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = EggsPage()
            with self.assert_raises(Valid):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object, {'radio': p.choices[2]})
        self.assert_false(f.has_error())

    def test_radio_choice_post_no_choices(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="radio"

2
{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = EggsPage()
            p.find('form:radio').choices = []
            with self.assert_raises(Valid):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object, {'radio': p.choices[0]})
        self.assert_false(f.has_error())

    def test_radio_choice_post_empty(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = EggsPage()
            with self.assert_raises(Valid):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object, {'radio': None})
        self.assert_false(f.has_error())

    def test_radio_choice_validation_error_out_of_range(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="radio"

-1
{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = EggsPage()
            with self.assert_raises(Invalid):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object, {'radio': p.choices[0]})
        self.assert_true(f.has_error())
        self.assert_is_instance(f.find('radio').error, ayame.ValidationError)

    def test_radio_choice_validation_error_no_value(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="radio"


{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = EggsPage()
            with self.assert_raises(Invalid):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object, {'radio': p.choices[0]})
        self.assert_true(f.has_error())
        self.assert_is_instance(f.find('radio').error, ayame.ValidationError)

    def test_check_box_choice(self):
        with self.application(self.new_environ()):
            p = HamPage()
            status, headers, content = p.render()
        html = self.format(HamPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})

    def test_check_box_choice_single(self):
        with self.application(self.new_environ()):
            p = HamPage(multiple=False)
            status, headers, content = p.render()
        html = self.format(HamPage, choices=1)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[0]})

    def test_check_box_choice_with_renderer(self):
        with self.application(self.new_environ()):
            p = HamPage()
            p.find('form:checkbox').renderer = ChoiceRenderer()
            status, headers, content = p.render()
        html = self.format(HamPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})

    def test_check_box_choice_no_choices(self):
        with self.application(self.new_environ()):
            p = HamPage()
            p.find('form:checkbox').choices = []
            status, headers, content = p.render()
        html = self.format(HamPage, choices=0)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, html)

        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})

    def test_check_box_choice_post(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="checkbox"

0
{__}
Content-Disposition: form-data; name="checkbox"

0
{__}
Content-Disposition: form-data; name="checkbox"

1
{__}
Content-Disposition: form-data; name="checkbox"

1
{__}
Content-Disposition: form-data; name="checkbox"

2
{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = HamPage()
            with self.assert_raises(Valid):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices})
        self.assert_false(f.has_error())

    def test_check_box_choice_post_single(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="checkbox"

2
{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = HamPage(multiple=False)
            with self.assert_raises(Valid):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[2]})
        self.assert_false(f.has_error())

    def test_check_box_choice_post_no_choices(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="checkbox"

0
{__}
Content-Disposition: form-data; name="checkbox"

1
{__}
Content-Disposition: form-data; name="checkbox"

2
{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = HamPage()
            p.find('form:checkbox').choices = []
            with self.assert_raises(Valid):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})
        self.assert_false(f.has_error())

    def test_check_box_choice_post_no_model(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="checkbox"

0
{__}
Content-Disposition: form-data; name="checkbox"

1
{__}
Content-Disposition: form-data; name="checkbox"

2
{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = HamPage()
            p.find('form').model = None
            with self.assert_raises(Valid):
                p.render()
        f = p.find('form')
        self.assert_is_none(f.model_object)
        self.assert_false(f.has_error())

    def test_check_box_choice_post_empty(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = HamPage()
            with self.assert_raises(Valid):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': []})
        self.assert_false(f.has_error())

    def test_check_box_choice_required_error(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = HamPage()
            p.find('form:checkbox').required = True
            with self.assert_raises(Invalid):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})
        self.assert_true(f.has_error())
        self.assert_is_instance(f.find('checkbox').error,
                                ayame.ValidationError)

    def test_check_box_choice_validation_error_out_of_range(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="checkbox"

-1
{__}
Content-Disposition: form-data; name="checkbox"

0
{__}
Content-Disposition: form-data; name="checkbox"

3
{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = HamPage()
            with self.assert_raises(Invalid):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})
        self.assert_true(f.has_error())
        self.assert_is_instance(f.find('checkbox').error,
                                ayame.ValidationError)

    def test_check_box_choice_validation_error_no_value(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="checkbox"


{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = HamPage()
            with self.assert_raises(Invalid):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})
        self.assert_true(f.has_error())
        self.assert_is_instance(f.find('checkbox').error,
                                ayame.ValidationError)

    def test_check_box_choice_validation_error_no_values(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="checkbox"

0
{__}
Content-Disposition: form-data; name="checkbox"


{__}
Content-Disposition: form-data; name="checkbox"

1
{__}
Content-Disposition: form-data; name="checkbox"


{__}
Content-Disposition: form-data; name="checkbox"

2
{____}
"""
        with self.application(self.new_environ(method='POST', body=data)):
            p = HamPage()
            with self.assert_raises(Invalid):
                p.render()
        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})
        self.assert_true(f.has_error())
        self.assert_is_instance(f.find('checkbox').error,
                                ayame.ValidationError)

    def test_select_choice_invalid_markup(self):
        fc = form.SelectChoice('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      r"'select' element is "):
            fc.render(markup.Element(markup.DIV))

    def test_select_choice(self):
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ()):
                p = class_()
                status, headers, content = p.render()
            html = self.format(class_)
            self.assert_equal(status, http.OK.status)
            self.assert_equal(headers,
                              [('Content-Type', 'text/html; charset=UTF-8'),
                               ('Content-Length', str(len(html)))])
            self.assert_equal(content, html)

            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices[:2]})

    def test_select_choice_single(self):
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ()):
                p = class_(multiple=False)
                status, headers, content = p.render()
            html = self.format(class_, multiple=False, choices=1)
            self.assert_equal(status, http.OK.status)
            self.assert_equal(headers,
                              [('Content-Type', 'text/html; charset=UTF-8'),
                               ('Content-Length', str(len(html)))])
            self.assert_equal(content, html)

            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices[0]})

    def test_select_choice_with_renderer(self):
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ()):
                p = class_()
                p.find('form:select').renderer = ChoiceRenderer()
                status, headers, content = p.render()
            html = self.format(class_)
            self.assert_equal(status, http.OK.status)
            self.assert_equal(headers,
                              [('Content-Type', 'text/html; charset=UTF-8'),
                               ('Content-Length', str(len(html)))])
            self.assert_equal(content, html)

            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices[:2]})

    def test_select_choice_no_choices(self):
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ()):
                p = class_()
                p.find('form:select').choices = []
                status, headers, content = p.render()
            html = self.format(class_, choices=False)
            self.assert_equal(status, http.OK.status)
            self.assert_equal(headers,
                              [('Content-Type', 'text/html; charset=UTF-8'),
                               ('Content-Length', str(len(html)))])
            self.assert_equal(content, html)

            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices[:2]})

    def test_select_choice_post(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="select"

0
{__}
Content-Disposition: form-data; name="select"

0
{__}
Content-Disposition: form-data; name="select"

1
{__}
Content-Disposition: form-data; name="select"

1
{__}
Content-Disposition: form-data; name="select"

2
{____}
"""
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', body=data)):
                p = class_()
                with self.assert_raises(Valid):
                    p.render()
            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices})
            self.assert_false(f.has_error())

    def test_select_choice_post_single(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{____}
"""
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', body=data)):
                p = class_(multiple=False)
                with self.assert_raises(Valid):
                    p.render()
            f = p.find('form')
            self.assert_equal(f.model_object, {'select': None})
            self.assert_false(f.has_error())

    def test_select_choice_post_no_choices(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="select"

0
{__}
Content-Disposition: form-data; name="select"

1
{__}
Content-Disposition: form-data; name="select"

2
{____}
"""
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', body=data)):
                p = class_()
                p.find('form:select').choices = []
                with self.assert_raises(Valid):
                    p.render()
            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices[:2]})
            self.assert_false(f.has_error())

    def test_select_choice_post_no_model(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="select"

0
{__}
Content-Disposition: form-data; name="select"

1
{__}
Content-Disposition: form-data; name="select"

2
{____}
"""
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', body=data)):
                p = class_()
                p.find('form').model = None
                with self.assert_raises(Valid):
                    p.render()
            f = p.find('form')
            self.assert_is_none(f.model_object)
            self.assert_false(f.has_error())

    def test_select_choice_post_empty(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{____}
"""
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', body=data)):
                p = class_()
                with self.assert_raises(Valid):
                    p.render()
            f = p.find('form')
            self.assert_equal(f.model_object, {'select': []})
            self.assert_false(f.has_error())

    def test_select_choice_required_error(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{____}
"""
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', body=data)):
                p = class_()
                p.find('form:select').required = True
                with self.assert_raises(Invalid):
                    p.render()
            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices[:2]})
            self.assert_true(f.has_error())
            self.assert_is_instance(f.find('select').error,
                                    ayame.ValidationError)

    def test_select_choice_validation_error_out_of_range(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="select"

-1
{__}
Content-Disposition: form-data; name="select"

0
{__}
Content-Disposition: form-data; name="select"

3
{____}
"""
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', body=data)):
                p = class_()
                with self.assert_raises(Invalid):
                    p.render()
            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices[:2]})
            self.assert_true(f.has_error())
            self.assert_is_instance(f.find('select').error,
                                    ayame.ValidationError)

    def test_select_choice_validation_error_no_value(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="select"


{____}
"""
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', body=data)):
                p = class_()
                with self.assert_raises(Invalid):
                    p.render()
            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices[:2]})
            self.assert_true(f.has_error())
            self.assert_is_instance(f.find('select').error,
                                    ayame.ValidationError)

    def test_select_choice_validation_error_no_values(self):
        data = """\
{__}
Content-Disposition: form-data; name="{path}"

form
{__}
Content-Disposition: form-data; name="select"

0
{__}
Content-Disposition: form-data; name="select"


{__}
Content-Disposition: form-data; name="select"

1
{__}
Content-Disposition: form-data; name="select"


{__}
Content-Disposition: form-data; name="select"

2
{____}
"""
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', body=data)):
                p = class_()
                with self.assert_raises(Invalid):
                    p.render()
            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices[:2]})
            self.assert_true(f.has_error())
            self.assert_is_instance(f.find('select').error,
                                    ayame.ValidationError)


class SpamPage(ayame.Page):

    html_t = """\
<?xml version="1.0"?>
{doctype}
<html xmlns="{xhtml}">
  <head>
    <title>SpamPage</title>
  </head>
  <body>
    <form action="/form" method="post">
      <div class="ayame-hidden"><input name="{path}" type="hidden" \
value="form" /></div>
      <fieldset>
        <legend>form</legend>
        <input name="text" type="text" value="" /><br />
        <input name="password" type="password" value="" /><br />
        <input name="hidden" type="hidden" value="" /><br />
        <textarea name="area">
          Hello World!
        </textarea>
        <input checked="checked" name="checkbox" type="checkbox" value="on" />\
<br />
        <input name="file" type="file" /><br />
        <input name="button" type="submit" />
      </fieldset>
    </form>
  </body>
</html>
"""

    def __init__(self):
        super(SpamPage, self).__init__()
        self.add(Form('form', model.CompoundModel({})))
        self.find('form').add(basic.Label('legend', 'form'))
        self.find('form').add(form.TextField('text'))
        self.find('form:text').model_object = u''
        self.find('form:text').add(ayame.Behavior())
        self.find('form').add(form.PasswordField('password'))
        self.find('form:password').model_object = u''
        self.find('form').add(form.HiddenField('hidden'))
        self.find('form:hidden').model_object = u''
        self.find('form').add(form.TextArea('area'))
        self.find('form:area').model_object = u'Hello World!'
        self.find('form').add(form.CheckBox('checkbox'))
        self.find('form:checkbox').model_object = True
        self.find('form').add(form.FileUploadField('file'))
        self.find('form:file').model_object = None
        class Button(form.Button):
            def on_submit(self):
                super(Button, self).on_submit()
                self.model_object = 'submitted'
                raise Valid(self.id)
            def on_error(self):
                super(Button, self).on_error()
                raise Invalid(self.id)
        self.find('form').add(Button('button'))


class EggsPage(ayame.Page):

    choices = [datetime.date(2012, 1, 1),
               datetime.date(2012, 1, 2),
               datetime.date(2012, 1, 3)]
    html_t = """\
<?xml version="1.0"?>
{doctype}
<html xmlns="{xhtml}">
  <head>
    <title>EggsPage</title>
  </head>
  <body>
    <form action="/form" method="post">
      <div class="ayame-hidden"><input name="{path}" type="hidden" \
value="form" /></div>
      <fieldset>
        <legend>radio</legend>
        <div id="radio">{choices}</div>
      </fieldset>
    </form>
  </body>
</html>
"""
    kwargs = {'choices': lambda v=True: """
          <input checked="checked" id="radio-0" name="radio" type="radio" \
value="0" /><label for="radio-0">2012-01-01</label><br />
          <input id="radio-1" name="radio" type="radio" value="1" /><label \
for="radio-1">2012-01-02</label><br />
          <input id="radio-2" name="radio" type="radio" value="2" /><label \
for="radio-2">2012-01-03</label>
        \
""" if v else ''}

    def __init__(self):
        super(EggsPage, self).__init__()
        self.add(Form('form', model.CompoundModel({})))
        self.find('form').add(form.RadioChoice('radio', choices=self.choices))
        self.find('form:radio').model_object = self.choices[0]


class HamPage(ayame.Page):

    choices = [datetime.date(2012, 1, 1),
               datetime.date(2012, 1, 2),
               datetime.date(2012, 1, 3)]
    html_t = """\
<?xml version="1.0"?>
{doctype}
<html xmlns="{xhtml}">
  <head>
    <title>HamPage</title>
  </head>
  <body>
    <form action="/form" method="post">
      <div class="ayame-hidden"><input name="{path}" type="hidden" \
value="form" /></div>
      <fieldset>
        <legend>checkbox</legend>
        <div id="checkbox">{choices}</div>
      </fieldset>
    </form>
  </body>
</html>
"""
    kwargs = {'choices': lambda v=2: """
          <input {}id="checkbox-0" name="checkbox" type="checkbox" \
value="0" /><label for="checkbox-0">2012-01-01</label><br />
          <input {}id="checkbox-1" name="checkbox" type="checkbox" \
value="1" /><label for="checkbox-1">2012-01-02</label><br />
          <input {}id="checkbox-2" name="checkbox" type="checkbox" \
value="2" /><label for="checkbox-2">2012-01-03</label>
        \
""".format(*('checked="checked" ',) * v + ('',) * (3 - v)) if v else ''}

    def __init__(self, multiple=True):
        super(HamPage, self).__init__()
        self.add(Form('form', model.CompoundModel({})))
        self.find('form').add(form.CheckBoxChoice('checkbox',
                                                  choices=self.choices))
        if multiple:
            self.find('form:checkbox').model_object = self.choices[:2]
        else:
            self.find('form:checkbox').model_object = self.choices[0]
        self.find('form:checkbox').multiple = multiple


class SelectChoicePage(ayame.Page):

    choices = [datetime.date(2013, 1, 1),
               datetime.date(2013, 1, 2),
               datetime.date(2013, 1, 3)]
    html_t = """\
<?xml version="1.0"?>
{doctype}
<html xmlns="{xhtml}">
  <head>
    <title>{title}</title>
  </head>
  <body>
    <form action="/form" method="post">
      <div class="ayame-hidden"><input name="{path}" type="hidden" \
value="form" /></div>
      <fieldset>
        <legend>select</legend>
        <select {multiple}name="select">{choices}
        </select>
      </fieldset>
    </form>
  </body>
</html>
"""
    kwargs = {'multiple': lambda v=True: 'multiple="multiple" ' if v else '',
              'choices': lambda v=2: """
          <option {}value="0">2013-01-01</option>
          <option {}value="1">2013-01-02</option>
          <option {}value="2">2013-01-03</option>\
""".format(*('selected="selected" ',) * v + ('',) * (3 - v)) if v else ''}

    def __init__(self, multiple=True):
        super(SelectChoicePage, self).__init__()
        self.kwargs['title'] = self.__class__.__name__
        self.add(Form('form', model.CompoundModel({})))
        self.find('form').add(form.SelectChoice('select',
                                                choices=self.choices))
        if multiple:
            self.find('form:select').model_object = self.choices[:2]
        else:
            self.find('form:select').model_object = self.choices[0]
        self.find('form:select').multiple = multiple


class ToastPage(SelectChoicePage):
    pass


class BeansPage(SelectChoicePage):
    pass


class Form(form.Form):

    def on_submit(self):
        super(Form, self).on_submit()
        raise Valid(self.id)

    def on_error(self):
        super(Form, self).on_error()
        raise Invalid(self.id)


class Valid(Exception):
    pass


class Invalid(Exception):
    pass


class ChoiceRenderer(form.ChoiceRenderer):

    def label_for(self, object):
        return object.strftime('%Y-%m-%d')
