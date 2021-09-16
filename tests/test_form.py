#
# test_form
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import datetime
import textwrap

import ayame
from ayame import basic, form, http, markup, model, validator
from base import AyameTestCase


class FormTestCase(AyameTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.app.config['ayame.markup.pretty'] = True

    def assertRequiredError(self, fc, input):
        e = fc.error
        self.assertIsInstance(e, ayame.ValidationError)
        self.assertEqual(str(e), f"'{fc.id}' is required")
        self.assertEqual(e.keys, ['Required'])
        self.assertEqual(e.vars, {
            'input': input,
            'name': fc.id,
            'label': fc.id,
        })

    def assertChoiceError(self, fc, input):
        e = fc.error
        self.assertIsInstance(e, ayame.ValidationError)
        if fc.multiple:
            self.assertRegex(str(e), fr"'{fc.id}' contain invalid choices$")
            self.assertEqual(e.keys, ['Choice.multiple'])
        else:
            self.assertRegex(str(e), fr"'{fc.id}' is not a valid choice$")
            self.assertEqual(e.keys, ['Choice.single'])
        self.assertEqual(e.vars, {
            'input': input,
            'name': fc.id,
            'label': fc.id,
        })

    def new_environ(self, method='GET', query='', form=None):
        return super().new_environ(method=method,
                                   path='/form',
                                   query=query,
                                   form=form)

    def test_form_invalid_markup(self):
        # not form element
        f = form.Form('a')
        with self.assertRaisesRegex(ayame.RenderingError, r"'form' .* expected\b"):
            f.render(markup.Element(markup.DIV))

        # method is not found
        root = markup.Element(form._FORM,
                              attrib={form._ACTION: '/'})
        f = form.Form('a')
        with self.assertRaisesRegex(ayame.RenderingError, r"'method' .* required .* 'form'"):
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
            with self.assertRaisesRegex(ayame.ComponentError, r"\bForm is nested\b"):
                f.submit()

    def test_form_duplicate_buttons(self):
        class Button(form.Button):
            def relative_path(self):
                return super().relative_path()[:-1]

            def on_submit(self):
                raise Valid(self.id)

        query = ('{path}=a&'
                 'b')
        with self.application(self.new_environ(query=query)):
            f = form.Form('a')
            f.add(Button('b1'))
            f.add(Button('b2'))
            f._method = 'GET'
            with self.assertRaisesRegex(Valid, r'^b1$'):
                f.submit()

    def test_form(self):
        with self.application(self.new_environ()):
            p = SpamPage()
            status, headers, content = p()
        html = self.format(SpamPage)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        f = p.find('form')
        self.assertEqual(f.model_object['text'], '')
        self.assertEqual(f.model_object['password'], '')
        self.assertEqual(f.model_object['hidden'], '')
        self.assertEqual(f.model_object['area'], 'Hello World!\n')
        self.assertEqual(f.model_object['checkbox'], True)
        self.assertIsNone(f.model_object['file'])
        self.assertNotIn('button', f.model_object)

    def test_form_get(self):
        query = ('{path}=form&'
                 'text=text&'
                 'password=password&'
                 'hidden=hidden&'
                 'area=area&'
                 'file=a.txt')
        with self.application(self.new_environ(query=query)):
            p = SpamPage()
            with self.assertRaisesRegex(Valid, r'^form$'):
                p()
        f = p.find('form')
        self.assertEqual(f.model_object, {
            'text': 'text',
            'password': 'password',
            'hidden': 'hidden',
            'area': 'area',
            'checkbox': False,
            'file': 'a.txt',
        })
        self.assertFalse(f.has_error())

        query = ('{path}=form&'
                 'text=text&'
                 'password=password&'
                 'hidden=hidden&'
                 'area=area&'
                 'file=a.txt&'
                 'button')
        with self.application(self.new_environ(query=query)):
            p = SpamPage()
            with self.assertRaisesRegex(Valid, r'^button$'):
                p()
        f = p.find('form')
        self.assertEqual(f.model_object, {
            'text': 'text',
            'password': 'password',
            'hidden': 'hidden',
            'area': 'area',
            'checkbox': False,
            'file': 'a.txt',
            'button': 'submitted',
        })
        self.assertFalse(f.has_error())

    def test_form_post(self):
        data = self.form_data(('{path}', 'form'),
                              ('text', 'text'),
                              ('password', 'password'),
                              ('hidden', 'hidden'),
                              ('area', 'area'),
                              ('file', ('a.txt', 'spam\neggs\nham\n', 'text/plain')))
        with self.application(self.new_environ(method='POST', form=data)):
            p = SpamPage()
            with self.assertRaisesRegex(Valid, r'^form$'):
                p()
        f = p.find('form')
        self.assertEqual(f.model_object['text'], 'text')
        self.assertEqual(f.model_object['password'], 'password')
        self.assertEqual(f.model_object['hidden'], 'hidden')
        self.assertEqual(f.model_object['area'], 'area')
        self.assertEqual(f.model_object['checkbox'], False)
        self.assertEqual(f.model_object['file'].name, 'file')
        self.assertEqual(f.model_object['file'].filename, 'a.txt')
        self.assertEqual(f.model_object['file'].value, b'spam\neggs\nham\n')
        self.assertIsNotNone(f.model_object['file'].file)
        self.assertEqual(f.model_object['file'].type, 'text/plain')
        self.assertEqual(f.model_object['file'].type_options, {})
        self.assertNotIn('button', f.model_object)
        self.assertFalse(f.has_error())

        data = self.form_data(('{path}', 'form'),
                              ('text', 'text'),
                              ('password', 'password'),
                              ('hidden', 'hidden'),
                              ('area', 'area'),
                              ('file', ('a.txt', 'spam\neggs\nham\n', 'text/plain')),
                              ('button', ''))
        with self.application(self.new_environ(method='POST', form=data)):
            p = SpamPage()
            with self.assertRaisesRegex(Valid, r'^button$'):
                p()
        f = p.find('form')
        self.assertEqual(f.model_object['text'], 'text')
        self.assertEqual(f.model_object['password'], 'password')
        self.assertEqual(f.model_object['hidden'], 'hidden')
        self.assertEqual(f.model_object['area'], 'area')
        self.assertEqual(f.model_object['checkbox'], False)
        self.assertEqual(f.model_object['file'].name, 'file')
        self.assertEqual(f.model_object['file'].filename, 'a.txt')
        self.assertEqual(f.model_object['file'].value, b'spam\neggs\nham\n')
        self.assertIsNotNone(f.model_object['file'].file)
        self.assertEqual(f.model_object['file'].type, 'text/plain')
        self.assertEqual(f.model_object['file'].type_options, {})
        self.assertEqual(f.model_object['button'], 'submitted')
        self.assertFalse(f.has_error())

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
            with self.assertRaises(Invalid):
                p()
            f = p.find('form')
            self.assertEqual(f.model_object, {
                'text': '',
                'password': '',
                'hidden': '',
                'area': 'area',
                'checkbox': False,
                'file': 'a.txt',
            })
            self.assertTrue(f.has_error())
            self.assertRequiredError(f.find('text'), None)
            self.assertRequiredError(f.find('password'), None)
            self.assertRequiredError(f.find('hidden'), None)
            self.assertIsNone(f.find('area').error)
            self.assertIsNone(f.find('checkbox').error)
            self.assertIsNone(f.find('file').error)

    def test_form_no_element(self):
        query = '{path}=__form__&'
        with self.application(self.new_environ(query=query)):
            p = SpamPage()
            p.add(Form('__form__'))
            p()
        self.assertIsNone(p.find('__form__').model_object)

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
            with self.assertRaises(Valid):
                p()
            f = p.find('form')
            self.assertEqual(f.model_object, {
                'text': '',
                'password': '',
                'hidden': '',
                'area': 'area',
                'checkbox': False,
                'file': 'a.txt',
                'button': 'submitted',
            })
            self.assertFalse(f.has_error())

    def test_form_component_relative_path(self):
        f = form.Form('a')
        f.add(form.FormComponent('b1'))
        f.add(ayame.MarkupContainer('b2'))
        f.find('b2').add(form.FormComponent('c'))

        self.assertEqual(f.find('b1').relative_path(), 'b1')
        self.assertEqual(f.find('b2:c').relative_path(), 'b2:c')
        with self.assertRaisesRegex(ayame.ComponentError, r' is not attached .*\.Form\b'):
            form.FormComponent('a').relative_path()

    def test_form_component_required_error(self):
        with self.application(self.new_environ()):
            fc = form.FormComponent('a')
            fc.required = True
            self.assertIsNone(fc.error)

            fc.validate(None)
            self.assertRequiredError(fc, None)
            fc.validate('')
            self.assertRequiredError(fc, '')

    def test_form_component_conversion_error(self):
        with self.application(self.new_environ()):
            fc = form.FormComponent('a')
            fc.type = int
            self.assertIsNone(fc.error)

            fc.validate('a')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), r"'a' is not a valid type 'int'")
            self.assertEqual(e.keys, [
                'Converter.int',
                'Converter',
            ])
            self.assertEqual(e.vars, {
                'input': 'a',
                'name': 'a',
                'label': 'a',
                'type': 'int',
            })

    def test_form_component_validation_error_range(self):
        with self.application(self.new_environ()):
            fc = form.FormComponent('a')
            v = validator.RangeValidator()
            fc.add(v)
            self.assertIsNone(fc.error)

            for min, max, o in (
                (0.0, None, 0),
                (None, 0.0, 0),
            ):
                with self.subTest(min=min, max=max, object=o):
                    v.min = min
                    v.max = max
                    fc.validate(o)
                    e = fc.error
                    self.assertIsInstance(e, ayame.ValidationError)
                    self.assertRegex(str(e), r"'a' cannot validate$")
                    self.assertEqual(e.keys, ['RangeValidator.type'])
                    self.assertEqual(e.vars, {
                        'input': o,
                        'name': 'a',
                        'label': 'a',
                    })

            v.min = 5
            v.max = None
            fc.validate(0)
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), r"'a' must be at least 5$")
            self.assertEqual(e.keys, ['RangeValidator.minimum'])
            self.assertEqual(e.vars, {
                'input': 0,
                'name': 'a',
                'label': 'a',
                'min': 5,
            })

            v.min = None
            v.max = 3
            fc.validate(5)
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), r"'a' must be at most 3$")
            self.assertEqual(e.keys, ['RangeValidator.maximum'])
            self.assertEqual(e.vars, {
                'input': 5,
                'name': 'a',
                'label': 'a',
                'max': 3,
            })

            v.min = 3
            v.max = 5
            fc.validate(0)
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), r"'a' must be between 3 and 5$")
            self.assertEqual(e.keys, ['RangeValidator.range'])
            self.assertEqual(e.vars, {
                'input': 0,
                'name': 'a',
                'label': 'a',
                'min': 3,
                'max': 5,
            })

            v.min = v.max = 3
            fc.validate(5)
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), r"'a' must be exactly 3$")
            self.assertEqual(e.keys, ['RangeValidator.exact'])
            self.assertEqual(e.vars, {
                'input': 5,
                'name': 'a',
                'label': 'a',
                'exact': 3,
            })

    def test_form_component_validation_error_string(self):
        with self.application(self.new_environ()):
            fc = form.FormComponent('a')
            v = validator.StringValidator()
            fc.add(v)
            self.assertIsNone(fc.error)

            for min, max, o in (
                (None, None, 0),
                (0.0, None, ''),
                (None, 0.0, ''),
            ):
                with self.subTest(min=min, max=max, object=o):
                    v.min = min
                    v.max = max
                    fc.validate(o)
                    e = fc.error
                    self.assertIsInstance(e, ayame.ValidationError)
                    self.assertRegex(str(e), r"'a' cannot validate$")
                    self.assertEqual(e.keys, ['StringValidator.type'])
                    self.assertEqual(e.vars, {
                        'input': o,
                        'name': 'a',
                        'label': 'a',
                    })

            v.min = 4
            v.max = None
            fc.validate('.jp')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), r"'a' must be at least 4 ")
            self.assertEqual(e.keys, ['StringValidator.minimum'])
            self.assertEqual(e.vars, {
                'input': '.jp',
                'name': 'a',
                'label': 'a',
                'min': 4,
            })

            v.min = None
            v.max = 4
            fc.validate('.info')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), r"'a' must be at most 4 ")
            self.assertEqual(e.keys, ['StringValidator.maximum'])
            self.assertEqual(e.vars, {
                'input': '.info',
                'name': 'a',
                'label': 'a',
                'max': 4,
            })

            v.min = 4
            v.max = 5
            fc.validate('.jp')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), r"'a' must be between 4 and 5 ")
            self.assertEqual(e.keys, ['StringValidator.range'])
            self.assertEqual(e.vars, {
                'input': '.jp',
                'name': 'a',
                'label': 'a',
                'min': 4,
                'max': 5,
            })

            v.min = v.max = 4
            fc.validate('.info')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), r"'a' must be exactly 4 ")
            self.assertEqual(e.keys, ['StringValidator.exact'])
            self.assertEqual(e.vars, {
                'input': '.info',
                'name': 'a',
                'label': 'a',
                'exact': 4,
            })

    def test_form_component_validation_error_regex(self):
        with self.application(self.new_environ()):
            fc = form.FormComponent('a')
            fc.add(validator.RegexValidator(r'\d+$'))
            self.assertIsNone(fc.error)

            fc.validate('a')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), r"'a' does not match pattern ")
            self.assertEqual(e.keys, ['RegexValidator'])
            self.assertEqual(e.vars, {
                'input': 'a',
                'name': 'a',
                'label': 'a',
                'pattern': r'\d+$',
            })

    def test_form_component_validation_error_email(self):
        with self.application(self.new_environ()):
            fc = form.FormComponent('a')
            v = validator.EmailValidator()
            fc.add(v)
            self.assertIsNone(fc.error)

            fc.validate('a')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), r"'a' is not a valid email address$")
            self.assertEqual(e.keys, ['EmailValidator'])
            self.assertEqual(e.vars, {
                'input': 'a',
                'name': 'a',
                'label': 'a',
                'pattern': v.regex.pattern,
            })

    def test_form_component_validation_error_url(self):
        with self.application(self.new_environ()):
            fc = form.FormComponent('a')
            v = validator.URLValidator()
            fc.add(v)
            self.assertIsNone(fc.error)

            fc.validate('a')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), r"'a' is not a valid URL$")
            self.assertEqual(e.keys, ['URLValidator'])
            self.assertEqual(e.vars, {
                'input': 'a',
                'name': 'a',
                'label': 'a',
                'pattern': v.regex.pattern,
            })

    def test_form_component_no_model(self):
        with self.application():
            fc = form.FormComponent('a')
            fc.validate('a')
            self.assertIsNone(fc.error)
            self.assertIsNone(fc.model)
            self.assertIsNone(fc.model_object)

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
        self.assertEqual(len(element), 2)
        button = element.children[1]
        self.assertEqual(button.attrib, {form._NAME: 'b'})

    def test_button_invalid_markup(self):
        input = markup.Element(form._INPUT,
                               attrib={form._TYPE: 'text'})

        fc = form.Button('a')
        with self.assertRaisesRegex(ayame.RenderingError, r"'input' .* 'submit'"):
            fc.render(input)
        with self.assertRaisesRegex(ayame.RenderingError, r"'input' or 'button' element "):
            fc.render(markup.Element(markup.DIV))

    def test_file_upload_field_invalid_markup(self):
        fc = form.FileUploadField('a')
        with self.assertRaisesRegex(ayame.RenderingError, r"'input' element is "):
            fc.render(markup.Element(markup.DIV))

    def test_text_field_invalid_markup(self):
        fc = form.TextField('a')
        with self.assertRaisesRegex(ayame.RenderingError, r"'input' element is "):
            fc.render(markup.Element(markup.DIV))

    def test_text_area_invalid_markup(self):
        fc = form.TextArea('a')
        with self.assertRaisesRegex(ayame.RenderingError, r"'textarea' element is "):
            fc.render(markup.Element(markup.DIV))

    def test_check_box(self):
        element = markup.Element(form._FORM,
                                 attrib={form._METHOD: 'GET'})
        input = markup.Element(form._INPUT,
                               attrib={
                                   markup.AYAME_ID: 'b',
                                   form._TYPE: 'checkbox',
                               })
        element.append(input)
        with self.application(self.new_environ()):
            f = form.Form('a')
            f.add(form.CheckBox('b'))
            f.render(element)
        self.assertEqual(len(element), 2)
        input = element.children[1]
        self.assertEqual(input.attrib, {
            form._NAME: 'b',
            form._TYPE: 'checkbox',
            form._VALUE: 'on',
        })

    def test_check_box_invalid_markup(self):
        input = markup.Element(form._INPUT,
                               attrib={form._TYPE: 'text'})

        fc = form.CheckBox('a')
        with self.assertRaisesRegex(ayame.RenderingError, r"'input' .* 'checkbox'"):
            fc.render(input)
        with self.assertRaisesRegex(ayame.RenderingError, r"'input' element is "):
            fc.render(markup.Element(markup.DIV))

    def test_choice(self):
        fc = form.Choice('a')
        s = fc._id_prefix_for(markup.Element(markup.DIV))
        self.assertTrue(s)
        self.assertFalse(s[0].isdigit())

    def test_radio_choice(self):
        with self.application(self.new_environ()):
            p = EggsPage()
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        f = p.find('form')
        self.assertEqual(f.model_object, {'radio': p.choices[0]})

    def test_radio_choice_with_renderer(self):
        with self.application(self.new_environ()):
            p = EggsPage()
            p.find('form:radio').renderer = ChoiceRenderer()
            status, headers, content = p()
        html = self.format(EggsPage)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        f = p.find('form')
        self.assertEqual(f.model_object, {'radio': p.choices[0]})

    def test_radio_choice_no_choices(self):
        with self.application(self.new_environ()):
            p = EggsPage()
            p.find('form:radio').choices = []
            status, headers, content = p()
        html = self.format(EggsPage, choices=False)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        f = p.find('form')
        self.assertEqual(f.model_object, {'radio': p.choices[0]})

    def test_radio_choice_post(self):
        data = self.form_data(('{path}', 'form'),
                              ('radio', '1'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            with self.assertRaises(Valid):
                p()
        f = p.find('form')
        self.assertEqual(f.model_object, {'radio': p.choices[1]})
        self.assertFalse(f.has_error())

    def test_radio_choice_post_no_choices(self):
        data = self.form_data(('{path}', 'form'),
                              ('radio', '2'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            p.find('form:radio').choices = []
            with self.assertRaises(Valid):
                p()
        f = p.find('form')
        self.assertEqual(f.model_object, {'radio': p.choices[0]})
        self.assertFalse(f.has_error())

    def test_radio_choice_post_empty(self):
        data = self.form_data(('{path}', 'form'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            with self.assertRaises(Valid):
                p()
        f = p.find('form')
        self.assertEqual(f.model_object, {'radio': None})
        self.assertFalse(f.has_error())

    def test_radio_choice_required_error(self):
        data = self.form_data(('{path}', 'form'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            p.find('form:radio').required = True
            with self.assertRaises(Invalid):
                p()
            f = p.find('form')
            self.assertEqual(f.model_object, {'radio': p.choices[0]})
            self.assertTrue(f.has_error())
            self.assertRequiredError(f.find('radio'), [])

    def test_radio_choice_validation_error_out_of_range(self):
        data = self.form_data(('{path}', 'form'),
                              ('radio', '-1'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            with self.assertRaises(Invalid):
                p()
            f = p.find('form')
            self.assertEqual(f.model_object, {'radio': p.choices[0]})
            self.assertTrue(f.has_error())
            self.assertChoiceError(f.find('radio'), ['-1'])

    def test_radio_choice_validation_error_no_value(self):
        data = self.form_data(('{path}', 'form'),
                              ('radio', ''))
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            with self.assertRaises(Invalid):
                p()
            f = p.find('form')
            self.assertEqual(f.model_object, {'radio': p.choices[0]})
            self.assertTrue(f.has_error())
            self.assertChoiceError(f.find('radio'), [''])

    def test_check_box_choice(self):
        with self.application(self.new_environ()):
            p = HamPage()
            status, headers, content = p()
        html = self.format(HamPage)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        f = p.find('form')
        self.assertEqual(f.model_object, {'checkbox': p.choices[:2]})

    def test_check_box_choice_single(self):
        with self.application(self.new_environ()):
            p = HamPage(multiple=False)
            status, headers, content = p()
        html = self.format(HamPage, choices=1)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        f = p.find('form')
        self.assertEqual(f.model_object, {'checkbox': p.choices[0]})

    def test_check_box_choice_with_renderer(self):
        with self.application(self.new_environ()):
            p = HamPage()
            p.find('form:checkbox').renderer = ChoiceRenderer()
            status, headers, content = p()
        html = self.format(HamPage)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        f = p.find('form')
        self.assertEqual(f.model_object, {'checkbox': p.choices[:2]})

    def test_check_box_choice_no_choices(self):
        with self.application(self.new_environ()):
            p = HamPage()
            p.find('form:checkbox').choices = []
            status, headers, content = p()
        html = self.format(HamPage, choices=0)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

        f = p.find('form')
        self.assertEqual(f.model_object, {'checkbox': p.choices[:2]})

    def test_check_box_choice_post(self):
        data = self.form_data(('{path}', 'form'),
                              ('checkbox', '0'),
                              ('checkbox', '0'),
                              ('checkbox', '1'),
                              ('checkbox', '1'),
                              ('checkbox', '2'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            with self.assertRaises(Valid):
                p()
        f = p.find('form')
        self.assertEqual(f.model_object, {'checkbox': p.choices})
        self.assertFalse(f.has_error())

    def test_check_box_choice_post_single(self):
        data = self.form_data(('{path}', 'form'),
                              ('checkbox', '1'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage(multiple=False)
            with self.assertRaises(Valid):
                p()
        f = p.find('form')
        self.assertEqual(f.model_object, {'checkbox': p.choices[1]})
        self.assertFalse(f.has_error())

    def test_check_box_choice_post_no_choices(self):
        data = self.form_data(('{path}', 'form'),
                              ('checkbox', '0'),
                              ('checkbox', '1'),
                              ('checkbox', '2'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            p.find('form:checkbox').choices = []
            with self.assertRaises(Valid):
                p()
        f = p.find('form')
        self.assertEqual(f.model_object, {'checkbox': p.choices[:2]})
        self.assertFalse(f.has_error())

    def test_check_box_choice_post_no_model(self):
        data = self.form_data(('{path}', 'form'),
                              ('checkbox', '0'),
                              ('checkbox', '1'),
                              ('checkbox', '2'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            p.find('form').model = None
            with self.assertRaises(Valid):
                p()
        f = p.find('form')
        self.assertIsNone(f.model_object)
        self.assertFalse(f.has_error())

    def test_check_box_choice_post_empty(self):
        data = self.form_data(('{path}', 'form'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            with self.assertRaises(Valid):
                p()
        f = p.find('form')
        self.assertEqual(f.model_object, {'checkbox': []})
        self.assertFalse(f.has_error())

    def test_check_box_choice_required_error(self):
        data = self.form_data(('{path}', 'form'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            p.find('form:checkbox').required = True
            with self.assertRaises(Invalid):
                p()
            f = p.find('form')
            self.assertEqual(f.model_object, {'checkbox': p.choices[:2]})
            self.assertTrue(f.has_error())
            self.assertRequiredError(f.find('checkbox'), [])

    def test_check_box_choice_validation_error_out_of_range(self):
        data = self.form_data(('{path}', 'form'),
                              ('checkbox', '-1'),
                              ('checkbox', '0'),
                              ('checkbox', '3'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            with self.assertRaises(Invalid):
                p()
            f = p.find('form')
            self.assertEqual(f.model_object, {'checkbox': p.choices[:2]})
            self.assertTrue(f.has_error())
            self.assertChoiceError(f.find('checkbox'), ['-1', '0', '3'])

    def test_check_box_choice_validation_error_no_value(self):
        data = self.form_data(('{path}', 'form'),
                              ('checkbox', ''))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            with self.assertRaises(Invalid):
                p()
            f = p.find('form')
            self.assertEqual(f.model_object, {'checkbox': p.choices[:2]})
            self.assertTrue(f.has_error())
            self.assertChoiceError(f.find('checkbox'), [''])

    def test_check_box_choice_validation_error_no_values(self):
        data = self.form_data(('{path}', 'form'),
                              ('checkbox', '0'),
                              ('checkbox', ''),
                              ('checkbox', '1'),
                              ('checkbox', ''),
                              ('checkbox', '2'))
        with self.application(self.new_environ(method='POST', form=data)):
            p = HamPage()
            with self.assertRaises(Invalid):
                p()
            f = p.find('form')
            self.assertEqual(f.model_object, {'checkbox': p.choices[:2]})
            self.assertTrue(f.has_error())
            self.assertChoiceError(f.find('checkbox'), ['0', '', '1', '', '2'])

    def test_select_choice_invalid_markup(self):
        fc = form.SelectChoice('a')
        with self.assertRaisesRegex(ayame.RenderingError, r"'select' element is "):
            fc.render(markup.Element(markup.DIV))

    def test_select_choice(self):
        for class_ in (ToastPage, BeansPage):
            with self.subTest(page=class_):
                with self.application(self.new_environ()):
                    p = class_()
                    status, headers, content = p()
                html = self.format(class_)
                self.assertEqual(status, http.OK.status)
                self.assertEqual(headers, [
                    ('Content-Type', 'text/html; charset=UTF-8'),
                    ('Content-Length', str(len(html))),
                ])
                self.assertEqual(content, [html])

                f = p.find('form')
                self.assertEqual(f.model_object, {'select': p.choices[:2]})

    def test_select_choice_single(self):
        for class_ in (ToastPage, BeansPage):
            with self.subTest(page=class_):
                with self.application(self.new_environ()):
                    p = class_(multiple=False)
                    status, headers, content = p()
                html = self.format(class_, multiple=False, choices=1)
                self.assertEqual(status, http.OK.status)
                self.assertEqual(headers, [
                    ('Content-Type', 'text/html; charset=UTF-8'),
                    ('Content-Length', str(len(html))),
                ])
                self.assertEqual(content, [html])

                f = p.find('form')
                self.assertEqual(f.model_object, {'select': p.choices[0]})

    def test_select_choice_with_renderer(self):
        for class_ in (ToastPage, BeansPage):
            with self.subTest(page=class_):
                with self.application(self.new_environ()):
                    p = class_()
                    p.find('form:select').renderer = ChoiceRenderer()
                    status, headers, content = p()
                html = self.format(class_)
                self.assertEqual(status, http.OK.status)
                self.assertEqual(headers, [
                    ('Content-Type', 'text/html; charset=UTF-8'),
                    ('Content-Length', str(len(html))),
                ])
                self.assertEqual(content, [html])

                f = p.find('form')
                self.assertEqual(f.model_object, {'select': p.choices[:2]})

    def test_select_choice_no_choices(self):
        for class_ in (ToastPage, BeansPage):
            with self.subTest(page=class_):
                with self.application(self.new_environ()):
                    p = class_()
                    p.find('form:select').choices = []
                    status, headers, content = p()
                html = self.format(class_, choices=False)
                self.assertEqual(status, http.OK.status)
                self.assertEqual(headers, [
                    ('Content-Type', 'text/html; charset=UTF-8'),
                    ('Content-Length', str(len(html))),
                ])
                self.assertEqual(content, [html])

                f = p.find('form')
                self.assertEqual(f.model_object, {'select': p.choices[:2]})

    def test_select_choice_post(self):
        data = self.form_data(('{path}', 'form'),
                              ('select', '0'),
                              ('select', '0'),
                              ('select', '1'),
                              ('select', '1'),
                              ('select', '2'))
        for class_ in (ToastPage, BeansPage):
            with self.subTest(page=class_):
                with self.application(self.new_environ(method='POST', form=data)):
                    p = class_()
                    with self.assertRaises(Valid):
                        p()
                f = p.find('form')
                self.assertEqual(f.model_object, {'select': p.choices})
                self.assertFalse(f.has_error())

    def test_select_choice_post_single(self):
        data = self.form_data(('{path}', 'form'),
                              ('select', '1'))
        for class_ in (ToastPage, BeansPage):
            with self.subTest(page=class_):
                with self.application(self.new_environ(method='POST', form=data)):
                    p = class_(multiple=False)
                    with self.assertRaises(Valid):
                        p()
                f = p.find('form')
                self.assertEqual(f.model_object, {'select': p.choices[1]})
                self.assertFalse(f.has_error())

    def test_select_choice_post_no_choices(self):
        data = self.form_data(('{path}', 'form'),
                              ('select', '0'),
                              ('select', '1'),
                              ('select', '2'))
        for class_ in (ToastPage, BeansPage):
            with self.subTest(page=class_):
                with self.application(self.new_environ(method='POST', form=data)):
                    p = class_()
                    p.find('form:select').choices = []
                    with self.assertRaises(Valid):
                        p()
                f = p.find('form')
                self.assertEqual(f.model_object, {'select': p.choices[:2]})
                self.assertFalse(f.has_error())

    def test_select_choice_post_no_model(self):
        data = self.form_data(('{path}', 'form'),
                              ('select', '0'),
                              ('select', '1'),
                              ('select', '2'))
        for class_ in (ToastPage, BeansPage):
            with self.subTest(page=class_):
                with self.application(self.new_environ(method='POST', form=data)):
                    p = class_()
                    p.find('form').model = None
                    with self.assertRaises(Valid):
                        p()
                f = p.find('form')
                self.assertIsNone(f.model_object)
                self.assertFalse(f.has_error())

    def test_select_choice_post_empty(self):
        data = self.form_data(('{path}', 'form'))
        for class_ in (ToastPage, BeansPage):
            with self.subTest(page=class_):
                with self.application(self.new_environ(method='POST', form=data)):
                    p = class_()
                    with self.assertRaises(Valid):
                        p()
                f = p.find('form')
                self.assertEqual(f.model_object, {'select': []})
                self.assertFalse(f.has_error())

    def test_select_choice_required_error(self):
        data = self.form_data(('{path}', 'form'))
        for class_ in (ToastPage, BeansPage):
            with self.subTest(page=class_):
                with self.application(self.new_environ(method='POST', form=data)):
                    p = class_()
                    p.find('form:select').required = True
                    with self.assertRaises(Invalid):
                        p()
                    f = p.find('form')
                    self.assertEqual(f.model_object, {'select': p.choices[:2]})
                    self.assertTrue(f.has_error())
                    self.assertRequiredError(f.find('select'), [])

    def test_select_choice_validation_error_out_of_range(self):
        data = self.form_data(('{path}', 'form'),
                              ('select', '-1'),
                              ('select', '0'),
                              ('select', '3'))
        for class_ in (ToastPage, BeansPage):
            with self.subTest(page=class_):
                with self.application(self.new_environ(method='POST', form=data)):
                    p = class_()
                    with self.assertRaises(Invalid):
                        p()
                    f = p.find('form')
                    self.assertEqual(f.model_object, {'select': p.choices[:2]})
                    self.assertTrue(f.has_error())
                    self.assertChoiceError(f.find('select'), ['-1', '0', '3'])

    def test_select_choice_validation_error_no_value(self):
        data = self.form_data(('{path}', 'form'),
                              ('select', ''))
        for class_ in (ToastPage, BeansPage):
            with self.subTest(page=class_):
                with self.application(self.new_environ(method='POST', form=data)):
                    p = class_()
                    with self.assertRaises(Invalid):
                        p()
                    f = p.find('form')
                    self.assertEqual(f.model_object, {'select': p.choices[:2]})
                    self.assertTrue(f.has_error())
                    self.assertChoiceError(f.find('select'), [''])

    def test_select_choice_validation_error_no_values(self):
        data = self.form_data(('{path}', 'form'),
                              ('select', '0'),
                              ('select', ''),
                              ('select', '1'),
                              ('select', ''),
                              ('select', '2'))
        for class_ in (ToastPage, BeansPage):
            with self.subTest(page=class_):
                with self.application(self.new_environ(method='POST', form=data)):
                    p = class_()
                    with self.assertRaises(Invalid):
                        p()
                    f = p.find('form')
                    self.assertEqual(f.model_object, {'select': p.choices[:2]})
                    self.assertTrue(f.has_error())
                    self.assertChoiceError(f.find('select'), ['0', '', '1', '', '2'])


class SpamPage(ayame.Page):

    html_t = textwrap.dedent("""\
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
    """)

    def __init__(self):
        super().__init__()
        self.add(Form('form', model.CompoundModel({})))
        self.find('form').add(basic.Label('legend', 'form'))
        self.find('form').add(form.TextField('text'))
        self.find('form:text').model_object = ''
        self.find('form:text').add(ayame.Behavior())
        self.find('form').add(form.PasswordField('password'))
        self.find('form:password').model_object = ''
        self.find('form').add(form.HiddenField('hidden'))
        self.find('form:hidden').model_object = ''
        self.find('form').add(form.TextArea('area'))
        self.find('form:area').model_object = 'Hello World!\n'
        self.find('form').add(form.CheckBox('checkbox'))
        self.find('form:checkbox').model_object = True
        self.find('form').add(form.FileUploadField('file'))
        self.find('form:file').model_object = None
        self.find('form').add(Button('button'))


class EggsPage(ayame.Page):

    choices = [datetime.date(2012, 1, 1),
               datetime.date(2012, 1, 2),
               datetime.date(2012, 1, 3)]
    html_t = textwrap.dedent("""\
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
    """)
    kwargs = {
        'choices': lambda v=True: """
          <input checked="checked" id="radio-0" name="radio" type="radio" value="0" /><label for="radio-0">2012-01-01</label><br />
          <input id="radio-1" name="radio" type="radio" value="1" /><label for="radio-1">2012-01-02</label><br />
          <input id="radio-2" name="radio" type="radio" value="2" /><label for="radio-2">2012-01-03</label>
        """ if v else '',
    }

    def __init__(self):
        super().__init__()
        self.add(Form('form', model.CompoundModel({})))
        self.find('form').add(form.RadioChoice('radio', choices=self.choices))
        self.find('form:radio').model_object = self.choices[0]


class HamPage(ayame.Page):

    choices = [datetime.date(2012, 1, 1),
               datetime.date(2012, 1, 2),
               datetime.date(2012, 1, 3)]
    html_t = textwrap.dedent("""\
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
    """)
    kwargs = {
        'choices': lambda v=2: """
          <input {}id="checkbox-0" name="checkbox" type="checkbox" value="0" /><label for="checkbox-0">2012-01-01</label><br />
          <input {}id="checkbox-1" name="checkbox" type="checkbox" value="1" /><label for="checkbox-1">2012-01-02</label><br />
          <input {}id="checkbox-2" name="checkbox" type="checkbox" value="2" /><label for="checkbox-2">2012-01-03</label>
        """.format(*('checked="checked" ',) * v + ('',) * (3 - v)) if v else '',
    }

    def __init__(self, multiple=True):
        super().__init__()
        self.add(Form('form', model.CompoundModel({})))
        self.find('form').add(form.CheckBoxChoice('checkbox',
                                                  choices=self.choices))
        self.find('form:checkbox').model_object = self.choices[:2] if multiple else self.choices[0]
        self.find('form:checkbox').multiple = multiple


class SelectChoicePage(ayame.Page):

    choices = [datetime.date(2013, 1, 1),
               datetime.date(2013, 1, 2),
               datetime.date(2013, 1, 3)]
    html_t = textwrap.dedent("""\
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
    """)
    kwargs = {
        'multiple': lambda v=True: 'multiple="multiple" ' if v else '',
        'choices': lambda v=2: textwrap.indent(textwrap.dedent("""
            <option {}value="0">2013-01-01</option>
            <option {}value="1">2013-01-02</option>
            <option {}value="2">2013-01-03</option>\
        """), ' ' * 10).rstrip().format(*('selected="selected" ',) * v + ('',) * (3 - v)) if v else '',
    }

    def __init__(self, multiple=True):
        super().__init__()
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
        super().on_submit()
        raise Valid(self.id)

    def on_error(self):
        super().on_error()
        raise Invalid(self.id)


class Button(form.Button):

    def on_submit(self):
        super().on_submit()
        self.model_object = 'submitted'
        raise Valid(self.id)

    def on_error(self):
        super().on_error()
        raise Invalid(self.id)


class Valid(Exception):
    pass


class Invalid(Exception):
    pass


class ChoiceRenderer(form.ChoiceRenderer):

    def label_for(self, object):
        return object.strftime('%Y-%m-%d')
