#
# test_form
#
#   Copyright (c) 2011-2015 Akinori Hattori <hattya@gmail.com>
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
from ayame import _compat as five
from ayame import basic, form, http, markup, model, validator
from base import AyameTestCase


class FormTestCase(AyameTestCase):

    @classmethod
    def setup_class(cls):
        super(FormTestCase, cls).setup_class()
        cls.app.config['ayame.markup.pretty'] = True

    def assert_required_error(self, fc, input):
        e = fc.error
        self.assert_is_instance(e, ayame.ValidationError)
        self.assert_equal(five.str(e), "'{}' is required".format(fc.id))
        self.assert_equal(e.keys, ['Required'])
        self.assert_equal(e.vars, {'input': input,
                                   'name': fc.id,
                                   'label': fc.id})

    def assert_choice_error(self, fc, input):
        e = fc.error
        self.assert_is_instance(e, ayame.ValidationError)
        if fc.multiple:
            self.assert_regex(five.str(e), "'{}' contain invalid choices$".format(fc.id))
            self.assert_equal(e.keys, ['Choice.multiple'])
        else:
            self.assert_regex(five.str(e), "'{}' is not a valid choice$".format(fc.id))
            self.assert_equal(e.keys, ['Choice.single'])
        self.assert_equal(e.vars, {'input': input,
                                   'name': fc.id,
                                   'label': fc.id})

    def new_environ(self, method='GET', query='', form=None):
        return super(FormTestCase, self).new_environ(method=method,
                                                     path='/form',
                                                     query=query,
                                                     form=form)

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

        query = 'b=1'
        with self.application(self.new_environ(query=query)):
            f = Form('a')
            f._method = 'POST'
            f.submit()

        query = 'b=1'
        with self.application(self.new_environ(method='PUT', query=query)):
            f = form.Form('a')
            f._method = 'POST'
            f.submit()

    def test_nested_form(self):
        with self.application(self.new_environ(method='POST')):
            f = form.Form('a')
            f.add(form.Form('b'))
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

        query = ('{path}=a&'
                 'b')
        with self.application(self.new_environ(query=query)):
            f = form.Form('a')
            f.add(Button('b1'))
            f.add(Button('b2'))
            f._method = 'GET'
            with self.assert_raises_regex(Valid,
                                          '^b1$'):
                f.submit()

    def test_form(self):
        with self.application(self.new_environ()):
            p = SpamPage()
            status, headers, content = p()
        html = self.format(SpamPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        f = p.find('form')
        self.assert_equal(f.model_object['text'], '')
        self.assert_equal(f.model_object['password'], '')
        self.assert_equal(f.model_object['hidden'], '')
        self.assert_equal(f.model_object['area'], 'Hello World!\n')
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
            with self.assert_raises_regex(Valid,
                                          '^form$'):
                p()
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
            with self.assert_raises_regex(Valid,
                                          '^button$'):
                p()
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
        data = self.form_data(('{path}', 'form'),
                              ('text', 'text'),
                              ('password', 'password'),
                              ('hidden', 'hidden'),
                              ('area', 'area'),
                              ('file', ('a.txt', 'spam\neggs\nham\n', 'text/plain')))
        with self.application(self.new_environ(method='POST', form=data)):
            p = SpamPage()
            with self.assert_raises_regex(Valid,
                                          '^form$'):
                p()
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

        data = self.form_data(('{path}', 'form'),
                              ('text', 'text'),
                              ('password', 'password'),
                              ('hidden', 'hidden'),
                              ('area', 'area'),
                              ('file', ('a.txt', 'spam\neggs\nham\n', 'text/plain')),
                              ('button', ''))
        with self.application(self.new_environ(method='POST', form=data)):
            p = SpamPage()
            with self.assert_raises_regex(Valid,
                                          '^button$'):
                p()
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
                p()
            f = p.find('form')
            self.assert_equal(f.model_object, {'text': '',
                                               'password': '',
                                               'hidden': '',
                                               'area': 'area',
                                               'checkbox': False,
                                               'file': 'a.txt'})
            self.assert_true(f.has_error())
            self.assert_required_error(f.find('text'), None)
            self.assert_required_error(f.find('password'), None)
            self.assert_required_error(f.find('hidden'), None)
            self.assert_is_none(f.find('area').error)
            self.assert_is_none(f.find('checkbox').error)
            self.assert_is_none(f.find('file').error)

    def test_form_no_element(self):
        query = '{path}=__form__&'
        with self.application(self.new_environ(query=query)):
            p = SpamPage()
            p.add(Form('__form__'))
            p()
        self.assert_is_none(p.find('__form__').model_object)

    def test_form_invisible_form_component(self):
        query = ('{path}=form&'
                 'area=area&'
                 'file=a.txt&'
                 'button')
        with self.application(self.new_environ(query=query)):
            p = SpamPage()
            p.find('form:text').visible = False
            p.find('form:text').required = True
            p.find('form:password').visible = False
            p.find('form:password').required = True
            p.find('form:hidden').visible = False
            p.find('form:hidden').required = True
            with self.assert_raises(Valid):
                p()
            f = p.find('form')
            self.assert_equal(f.model_object, {'text': '',
                                               'password': '',
                                               'hidden': '',
                                               'area': 'area',
                                               'checkbox': False,
                                               'file': 'a.txt',
                                               'button': 'submitted'})
            self.assert_false(f.has_error())

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
        with self.application(self.new_environ()):
            fc = form.FormComponent('a')
            fc.required = True
            self.assert_is_none(fc.error)

            fc.validate(None)
            self.assert_required_error(fc, None)
            fc.validate('')
            self.assert_required_error(fc, '')

    def test_form_component_conversion_error(self):
        with self.application(self.new_environ()):
            fc = form.FormComponent('a')
            fc.type = int
            self.assert_is_none(fc.error)

            fc.validate('a')
            e = fc.error
            self.assert_is_instance(e, ayame.ValidationError)
            self.assert_regex(five.str(e), "'a' is not a valid type 'int'")
            self.assert_equal(e.keys, ['Converter.int',
                                       'Converter'])
            self.assert_equal(e.vars, {'input': 'a',
                                       'name': 'a',
                                       'label': 'a',
                                       'type': 'int'})

    def test_form_component_validation_error_range(self):
        with self.application(self.new_environ()):
            fc = form.FormComponent('a')
            v = validator.RangeValidator()
            fc.add(v)
            self.assert_is_none(fc.error)

            def assert_type_error(min, max, o):
                v.min = min
                v.max = max
                fc.validate(o)
                e = fc.error
                self.assert_is_instance(e, ayame.ValidationError)
                self.assert_regex(five.str(e), "'a' cannot validate$")
                self.assert_equal(e.keys, ['RangeValidator.type'])
                self.assert_equal(e.vars, {'input': o,
                                           'name': 'a',
                                           'label': 'a'})

            assert_type_error(0.0, None, 0)
            assert_type_error(None, 0.0, 0)

            v.min = 5
            v.max = None
            fc.validate(0)
            e = fc.error
            self.assert_is_instance(e, ayame.ValidationError)
            self.assert_regex(five.str(e), "'a' must be at least 5$")
            self.assert_equal(e.keys, ['RangeValidator.minimum'])
            self.assert_equal(e.vars, {'input': 0,
                                       'name': 'a',
                                       'label': 'a',
                                       'min': 5})

            v.min = None
            v.max = 3
            fc.validate(5)
            e = fc.error
            self.assert_is_instance(e, ayame.ValidationError)
            self.assert_regex(five.str(e), "'a' must be at most 3$")
            self.assert_equal(e.keys, ['RangeValidator.maximum'])
            self.assert_equal(e.vars, {'input': 5,
                                       'name': 'a',
                                       'label': 'a',
                                       'max': 3})

            v.min = 3
            v.max = 5
            fc.validate(0)
            e = fc.error
            self.assert_is_instance(e, ayame.ValidationError)
            self.assert_regex(five.str(e), "'a' must be between 3 and 5$")
            self.assert_equal(e.keys, ['RangeValidator.range'])
            self.assert_equal(e.vars, {'input': 0,
                                       'name': 'a',
                                       'label': 'a',
                                       'min': 3,
                                       'max': 5})

            v.min = v.max = 3
            fc.validate(5)
            e = fc.error
            self.assert_is_instance(e, ayame.ValidationError)
            self.assert_regex(five.str(e), "'a' must be exactly 3$")
            self.assert_equal(e.keys, ['RangeValidator.exact'])
            self.assert_equal(e.vars, {'input': 5,
                                       'name': 'a',
                                       'label': 'a',
                                       'exact': 3})

    def test_form_component_validation_error_string(self):
        with self.application(self.new_environ()):
            fc = form.FormComponent('a')
            v = validator.StringValidator()
            fc.add(v)
            self.assert_is_none(fc.error)

            def assert_type_error(min, max, o):
                v.min = min
                v.max = max
                fc.validate(o)
                e = fc.error
                self.assert_is_instance(e, ayame.ValidationError)
                self.assert_regex(five.str(e), "'a' cannot validate$")
                self.assert_equal(e.keys, ['StringValidator.type'])
                self.assert_equal(e.vars, {'input': o,
                                           'name': 'a',
                                           'label': 'a'})

            assert_type_error(None, None, 0)
            assert_type_error(0.0, None, '')
            assert_type_error(None, 0.0, '')

            v.min = 4
            v.max = None
            fc.validate('.jp')
            e = fc.error
            self.assert_is_instance(e, ayame.ValidationError)
            self.assert_regex(five.str(e), "'a' must be at least 4 ")
            self.assert_equal(e.keys, ['StringValidator.minimum'])
            self.assert_equal(e.vars, {'input': '.jp',
                                       'name': 'a',
                                       'label': 'a',
                                       'min': 4})

            v.min = None
            v.max = 4
            fc.validate('.info')
            e = fc.error
            self.assert_is_instance(e, ayame.ValidationError)
            self.assert_regex(five.str(e), "'a' must be at most 4 ")
            self.assert_equal(e.keys, ['StringValidator.maximum'])
            self.assert_equal(e.vars, {'input': '.info',
                                       'name': 'a',
                                       'label': 'a',
                                       'max': 4})

            v.min = 4
            v.max = 5
            fc.validate('.jp')
            e = fc.error
            self.assert_is_instance(e, ayame.ValidationError)
            self.assert_regex(five.str(e), "'a' must be between 4 and 5 ")
            self.assert_equal(e.keys, ['StringValidator.range'])
            self.assert_equal(e.vars, {'input': '.jp',
                                       'name': 'a',
                                       'label': 'a',
                                       'min': 4,
                                       'max': 5})

            v.min = v.max = 4
            fc.validate('.info')
            e = fc.error
            self.assert_is_instance(e, ayame.ValidationError)
            self.assert_regex(five.str(e), "'a' must be exactly 4 ")
            self.assert_equal(e.keys, ['StringValidator.exact'])
            self.assert_equal(e.vars, {'input': '.info',
                                       'name': 'a',
                                       'label': 'a',
                                       'exact': 4})

    def test_form_component_validation_error_regex(self):
        with self.application(self.new_environ()):
            fc = form.FormComponent('a')
            fc.add(validator.RegexValidator('\d+$'))
            self.assert_is_none(fc.error)

            fc.validate('a')
            e = fc.error
            self.assert_is_instance(e, ayame.ValidationError)
            self.assert_regex(five.str(e), "'a' does not match pattern ")
            self.assert_equal(e.keys, ['RegexValidator'])
            self.assert_equal(e.vars, {'input': 'a',
                                       'name': 'a',
                                       'label': 'a',
                                       'pattern': '\d+$'})

    def test_form_component_validation_error_email(self):
        with self.application(self.new_environ()):
            fc = form.FormComponent('a')
            v = validator.EmailValidator()
            fc.add(v)
            self.assert_is_none(fc.error)

            fc.validate('a')
            e = fc.error
            self.assert_is_instance(e, ayame.ValidationError)
            self.assert_regex(five.str(e), "'a' is not a valid email address$")
            self.assert_equal(e.keys, ['EmailValidator'])
            self.assert_equal(e.vars, {'input': 'a',
                                       'name': 'a',
                                       'label': 'a',
                                       'pattern': v.regex.pattern})

    def test_form_component_validation_error_url(self):
        with self.application(self.new_environ()):
            fc = form.FormComponent('a')
            v = validator.URLValidator()
            fc.add(v)
            self.assert_is_none(fc.error)

            fc.validate('a')
            e = fc.error
            self.assert_is_instance(e, ayame.ValidationError)
            self.assert_regex(five.str(e), "'a' is not a valid URL$")
            self.assert_equal(e.keys, ['URLValidator'])
            self.assert_equal(e.vars, {'input': 'a',
                                       'name': 'a',
                                       'label': 'a',
                                       'pattern': v.regex.pattern})

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
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        f = p.find('form')
        self.assert_equal(f.model_object, {'radio': p.choices[0]})

    def test_radio_choice_with_renderer(self):
        with self.application(self.new_environ()):
            p = EggsPage()
            p.find('form:radio').renderer = ChoiceRenderer()
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        f = p.find('form')
        self.assert_equal(f.model_object, {'radio': p.choices[0]})

    def test_radio_choice_no_choices(self):
        with self.application(self.new_environ()):
            p = EggsPage()
            p.find('form:radio').choices = []
            status, headers, content = p()
        html = self.format(EggsPage, choices=False)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        f = p.find('form')
        self.assert_equal(f.model_object, {'radio': p.choices[0]})

    def test_radio_choice_post(self):
        data = self.form_data(('{path}', 'form'),
                              ('radio', '1'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            with self.assert_raises(Valid):
                p()
        f = p.find('form')
        self.assert_equal(f.model_object, {'radio': p.choices[1]})
        self.assert_false(f.has_error())

    def test_radio_choice_post_no_choices(self):
        data = self.form_data(('{path}', 'form'),
                              ('radio', '2'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            p.find('form:radio').choices = []
            with self.assert_raises(Valid):
                p()
        f = p.find('form')
        self.assert_equal(f.model_object, {'radio': p.choices[0]})
        self.assert_false(f.has_error())

    def test_radio_choice_post_empty(self):
        data = self.form_data(('{path}', 'form'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            with self.assert_raises(Valid):
                p()
        f = p.find('form')
        self.assert_equal(f.model_object, {'radio': None})
        self.assert_false(f.has_error())

    def test_radio_choice_required_error(self):
        data = self.form_data(('{path}', 'form'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            p.find('form:radio').required = True
            with self.assert_raises(Invalid):
                p()
            f = p.find('form')
            self.assert_equal(f.model_object, {'radio': p.choices[0]})
            self.assert_true(f.has_error())
            self.assert_required_error(f.find('radio'), [])

    def test_radio_choice_validation_error_out_of_range(self):
        data = self.form_data(('{path}', 'form'),
                              ('radio', '-1'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            with self.assert_raises(Invalid):
                p()
            f = p.find('form')
            self.assert_equal(f.model_object, {'radio': p.choices[0]})
            self .assert_true(f.has_error())
            self.assert_choice_error(f.find('radio'), ['-1'])

    def test_radio_choice_validation_error_no_value(self):
        data = self.form_data(('{path}', 'form'),
                              ('radio', ''))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            with self.assert_raises(Invalid):
                p()
            f = p.find('form')
            self.assert_equal(f.model_object, {'radio': p.choices[0]})
            self.assert_true(f.has_error())
            self.assert_choice_error(f.find('radio'), [''])

    def test_check_box_choice(self):
        with self.application(self.new_environ()):
            p = HamPage()
            status, headers, content = p()
        html = self.format(HamPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})

    def test_check_box_choice_single(self):
        with self.application(self.new_environ()):
            p = HamPage(multiple=False)
            status, headers, content = p()
        html = self.format(HamPage, choices=1)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[0]})

    def test_check_box_choice_with_renderer(self):
        with self.application(self.new_environ()):
            p = HamPage()
            p.find('form:checkbox').renderer = ChoiceRenderer()
            status, headers, content = p()
        html = self.format(HamPage)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})

    def test_check_box_choice_no_choices(self):
        with self.application(self.new_environ()):
            p = HamPage()
            p.find('form:checkbox').choices = []
            status, headers, content = p()
        html = self.format(HamPage, choices=0)
        self.assert_equal(status, http.OK.status)
        self.assert_equal(headers,
                          [('Content-Type', 'text/html; charset=UTF-8'),
                           ('Content-Length', str(len(html)))])
        self.assert_equal(content, [html])

        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})

    def test_check_box_choice_post(self):
        data = self.form_data(('{path}', 'form'),
                              ('checkbox', '0'),
                              ('checkbox', '0'),
                              ('checkbox', '1'),
                              ('checkbox', '1'),
                              ('checkbox', '2'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            with self.assert_raises(Valid):
                p()
        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices})
        self.assert_false(f.has_error())

    def test_check_box_choice_post_single(self):
        data = self.form_data(('{path}', 'form'),
                              ('checkbox', '1'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage(multiple=False)
            with self.assert_raises(Valid):
                p()
        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[1]})
        self.assert_false(f.has_error())

    def test_check_box_choice_post_no_choices(self):
        data = self.form_data(('{path}', 'form'),
                              ('checkbox', '0'),
                              ('checkbox', '1'),
                              ('checkbox', '2'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            p.find('form:checkbox').choices = []
            with self.assert_raises(Valid):
                p()
        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})
        self.assert_false(f.has_error())

    def test_check_box_choice_post_no_model(self):
        data = self.form_data(('{path}', 'form'),
                              ('checkbox', '0'),
                              ('checkbox', '1'),
                              ('checkbox', '2'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            p.find('form').model = None
            with self.assert_raises(Valid):
                p()
        f = p.find('form')
        self.assert_is_none(f.model_object)
        self.assert_false(f.has_error())

    def test_check_box_choice_post_empty(self):
        data = self.form_data(('{path}', 'form'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            with self.assert_raises(Valid):
                p()
        f = p.find('form')
        self.assert_equal(f.model_object, {'checkbox': []})
        self.assert_false(f.has_error())

    def test_check_box_choice_required_error(self):
        data = self.form_data(('{path}', 'form'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            p.find('form:checkbox').required = True
            with self.assert_raises(Invalid):
                p()
            f = p.find('form')
            self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})
            self.assert_true(f.has_error())
            self.assert_required_error(f.find('checkbox'), [])

    def test_check_box_choice_validation_error_out_of_range(self):
        data = self.form_data(('{path}', 'form'),
                              ('checkbox', '-1'),
                              ('checkbox', '0'),
                              ('checkbox', '3'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            with self.assert_raises(Invalid):
                p()
            f = p.find('form')
            self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})
            self.assert_true(f.has_error())
            self.assert_choice_error(f.find('checkbox'), ['-1', '0', '3'])

    def test_check_box_choice_validation_error_no_value(self):
        data = self.form_data(('{path}', 'form'),
                              ('checkbox', ''))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            with self.assert_raises(Invalid):
                p()
            f = p.find('form')
            self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})
            self.assert_true(f.has_error())
            self.assert_choice_error(f.find('checkbox'), [''])

    def test_check_box_choice_validation_error_no_values(self):
        data = self.form_data(('{path}', 'form'),
                              ('checkbox', '0'),
                              ('checkbox', ''),
                              ('checkbox', '1'),
                              ('checkbox', ''),
                              ('checkbox', '2'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            with self.assert_raises(Invalid):
                p()
            f = p.find('form')
            self.assert_equal(f.model_object, {'checkbox': p.choices[:2]})
            self.assert_true(f.has_error())
            self.assert_choice_error(f.find('checkbox'), ['0', '', '1', '', '2'])

    def test_select_choice_invalid_markup(self):
        fc = form.SelectChoice('a')
        with self.assert_raises_regex(ayame.RenderingError,
                                      r"'select' element is "):
            fc.render(markup.Element(markup.DIV))

    def test_select_choice(self):
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ()):
                p = class_()
                status, headers, content = p()
            html = self.format(class_)
            self.assert_equal(status, http.OK.status)
            self.assert_equal(headers,
                              [('Content-Type', 'text/html; charset=UTF-8'),
                               ('Content-Length', str(len(html)))])
            self.assert_equal(content, [html])

            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices[:2]})

    def test_select_choice_single(self):
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ()):
                p = class_(multiple=False)
                status, headers, content = p()
            html = self.format(class_, multiple=False, choices=1)
            self.assert_equal(status, http.OK.status)
            self.assert_equal(headers,
                              [('Content-Type', 'text/html; charset=UTF-8'),
                               ('Content-Length', str(len(html)))])
            self.assert_equal(content, [html])

            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices[0]})

    def test_select_choice_with_renderer(self):
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ()):
                p = class_()
                p.find('form:select').renderer = ChoiceRenderer()
                status, headers, content = p()
            html = self.format(class_)
            self.assert_equal(status, http.OK.status)
            self.assert_equal(headers,
                              [('Content-Type', 'text/html; charset=UTF-8'),
                               ('Content-Length', str(len(html)))])
            self.assert_equal(content, [html])

            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices[:2]})

    def test_select_choice_no_choices(self):
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ()):
                p = class_()
                p.find('form:select').choices = []
                status, headers, content = p()
            html = self.format(class_, choices=False)
            self.assert_equal(status, http.OK.status)
            self.assert_equal(headers,
                              [('Content-Type', 'text/html; charset=UTF-8'),
                               ('Content-Length', str(len(html)))])
            self.assert_equal(content, [html])

            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices[:2]})

    def test_select_choice_post(self):
        data = self.form_data(('{path}', 'form'),
                              ('select', '0'),
                              ('select', '0'),
                              ('select', '1'),
                              ('select', '1'),
                              ('select', '2'))
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', form=data)):
                p = class_()
                with self.assert_raises(Valid):
                    p()
            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices})
            self.assert_false(f.has_error())

    def test_select_choice_post_single(self):
        data = self.form_data(('{path}', 'form'),
                              ('select', '1'))
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', form=data)):
                p = class_(multiple=False)
                with self.assert_raises(Valid):
                    p()
            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices[1]})
            self.assert_false(f.has_error())

    def test_select_choice_post_no_choices(self):
        data = self.form_data(('{path}', 'form'),
                              ('select', '0'),
                              ('select', '1'),
                              ('select', '2'))
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', form=data)):
                p = class_()
                p.find('form:select').choices = []
                with self.assert_raises(Valid):
                    p()
            f = p.find('form')
            self.assert_equal(f.model_object, {'select': p.choices[:2]})
            self.assert_false(f.has_error())

    def test_select_choice_post_no_model(self):
        data = self.form_data(('{path}', 'form'),
                              ('select', '0'),
                              ('select', '1'),
                              ('select', '2'))
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', form=data)):
                p = class_()
                p.find('form').model = None
                with self.assert_raises(Valid):
                    p()
            f = p.find('form')
            self.assert_is_none(f.model_object)
            self.assert_false(f.has_error())

    def test_select_choice_post_empty(self):
        data = self.form_data(('{path}', 'form'))
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', form=data)):
                p = class_()
                with self.assert_raises(Valid):
                    p()
            f = p.find('form')
            self.assert_equal(f.model_object, {'select': []})
            self.assert_false(f.has_error())

    def test_select_choice_required_error(self):
        data = self.form_data(('{path}', 'form'))
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', form=data)):
                p = class_()
                p.find('form:select').required = True
                with self.assert_raises(Invalid):
                    p()
                f = p.find('form')
                self.assert_equal(f.model_object, {'select': p.choices[:2]})
                self.assert_true(f.has_error())
                self.assert_required_error(f.find('select'), [])

    def test_select_choice_validation_error_out_of_range(self):
        data = self.form_data(('{path}', 'form'),
                              ('select', '-1'),
                              ('select', '0'),
                              ('select', '3'))
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', form=data)):
                p = class_()
                with self.assert_raises(Invalid):
                    p()
                f = p.find('form')
                self.assert_equal(f.model_object, {'select': p.choices[:2]})
                self.assert_true(f.has_error())
                self.assert_choice_error(f.find('select'), ['-1', '0', '3'])

    def test_select_choice_validation_error_no_value(self):
        data = self.form_data(('{path}', 'form'),
                              ('select', ''))
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', form=data)):
                p = class_()
                with self.assert_raises(Invalid):
                    p()
                f = p.find('form')
                self.assert_equal(f.model_object, {'select': p.choices[:2]})
                self.assert_true(f.has_error())
                self.assert_choice_error(f.find('select'), [''])

    def test_select_choice_validation_error_no_values(self):
        data = self.form_data(('{path}', 'form'),
                              ('select', '0'),
                              ('select', ''),
                              ('select', '1'),
                              ('select', ''),
                              ('select', '2'))
        for class_ in (ToastPage, BeansPage):
            with self.application(self.new_environ(method='POST', form=data)):
                p = class_()
                with self.assert_raises(Invalid):
                    p()
                f = p.find('form')
                self.assert_equal(f.model_object, {'select': p.choices[:2]})
                self.assert_true(f.has_error())
                self.assert_choice_error(f.find('select'), ['0', '', '1', '', '2'])


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
      <div class="ayame-hidden"><input name="{path}" type="hidden" value="form" /></div>
      <fieldset>
        <legend>form</legend>
        <input name="text" type="text" value="" /><br />
        <input name="password" type="password" value="" /><br />
        <input name="hidden" type="hidden" value="" /><br />
        <textarea name="area">
          Hello World!
        </textarea>
        <input checked="checked" name="checkbox" type="checkbox" value="on" /><br />
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
        self.find('form:area').model_object = u'Hello World!\n'
        self.find('form').add(form.CheckBox('checkbox'))
        self.find('form:checkbox').model_object = True
        self.find('form').add(form.FileUploadField('file'))
        self.find('form:file').model_object = None
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
      <div class="ayame-hidden"><input name="{path}" type="hidden" value="form" /></div>
      <fieldset>
        <legend>radio</legend>
        <div id="radio">{choices}</div>
      </fieldset>
    </form>
  </body>
</html>
"""
    kwargs = {
        'choices': lambda v=True: """
          <input checked="checked" id="radio-0" name="radio" type="radio" value="0" /><label for="radio-0">2012-01-01</label><br />
          <input id="radio-1" name="radio" type="radio" value="1" /><label for="radio-1">2012-01-02</label><br />
          <input id="radio-2" name="radio" type="radio" value="2" /><label for="radio-2">2012-01-03</label>
        \
""" if v else ''
    }

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
      <div class="ayame-hidden"><input name="{path}" type="hidden" value="form" /></div>
      <fieldset>
        <legend>checkbox</legend>
        <div id="checkbox">{choices}</div>
      </fieldset>
    </form>
  </body>
</html>
"""
    kwargs = {
        'choices': lambda v=2: """
          <input {}id="checkbox-0" name="checkbox" type="checkbox" value="0" /><label for="checkbox-0">2012-01-01</label><br />
          <input {}id="checkbox-1" name="checkbox" type="checkbox" value="1" /><label for="checkbox-1">2012-01-02</label><br />
          <input {}id="checkbox-2" name="checkbox" type="checkbox" value="2" /><label for="checkbox-2">2012-01-03</label>
        \
""".format(*('checked="checked" ',) * v + ('',) * (3 - v)) if v else ''
    }

    def __init__(self, multiple=True):
        super(HamPage, self).__init__()
        self.add(Form('form', model.CompoundModel({})))
        self.find('form').add(form.CheckBoxChoice('checkbox',
                                                  choices=self.choices))
        self.find('form:checkbox').model_object = self.choices[:2] if multiple else self.choices[0]
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
      <div class="ayame-hidden"><input name="{path}" type="hidden" value="form" /></div>
      <fieldset>
        <legend>select</legend>
        <select {multiple}name="select">{choices}
        </select>
      </fieldset>
    </form>
  </body>
</html>
"""
    kwargs = {
        'multiple': lambda v=True: 'multiple="multiple" ' if v else '',
        'choices': lambda v=2: """
          <option {}value="0">2013-01-01</option>
          <option {}value="1">2013-01-02</option>
          <option {}value="2">2013-01-03</option>\
""".format(*('selected="selected" ',) * v + ('',) * (3 - v)) if v else ''
    }

    def __init__(self, multiple=True):
        super(SelectChoicePage, self).__init__()
        self.kwargs['title'] = self.__class__.__name__
        self.add(Form('form', model.CompoundModel({})))
        self.find('form').add(form.SelectChoice('select',
                                                choices=self.choices))
        self.find('form:select').model_object = self.choices[:2] if multiple else self.choices[0]
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


class Button(form.Button):

    def on_submit(self):
        super(Button, self).on_submit()
        self.model_object = 'submitted'
        raise Valid(self.id)

    def on_error(self):
        super(Button, self).on_error()
        raise Invalid(self.id)


class Valid(Exception):
    pass


class Invalid(Exception):
    pass


class ChoiceRenderer(form.ChoiceRenderer):

    def label_for(self, object):
        return object.strftime('%Y-%m-%d')
