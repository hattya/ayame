#
# test_form
#
#   Copyright (c) 2011-2026 Akinori Hattori <hattya@gmail.com>
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

    def test_form_with_invalid_markup(self):
        f = form.Form(__name__)
        # not form element
        with self.assertRaisesRegex(ayame.RenderingError, r"'form' .* expected\b"):
            f.render(markup.Element(markup.DIV))
        # method is not found
        with self.assertRaisesRegex(ayame.RenderingError, r"'method' .* required .* 'form'"):
            f.render(markup.Element(form._FORM))

    def test_nested_form(self):
        with self.application(self.new_environ(method='POST')):
            f = form.Form('a')
            f._method = 'POST'
            f.add(form.Form('b'))
            with self.assertRaisesRegex(ayame.ComponentError, r"\bForm is nested\b"):
                f.submit()

    def test_form_method(self):
        class Form(form.Form):
            _method_mismatch = True

            def on_method_mismatch(self):
                super().on_method_mismatch()
                return self._method_mismatch

            def on_submit(self):
                super().on_submit()
                raise Valid(self.id)

            def on_error(self):
                super().on_error()
                raise Invalid(self.id)

        # method mismatch
        with self.application(self.new_environ(method='GET')):
            f = Form(__name__)
            f._method = 'POST'
            f._method_mismatch = False
            f.submit()
        # unknown method
        with self.application(self.new_environ(method='PUT')):
            f = Form(__name__)
            f._method = 'POST'
            f._method_mismatch = True
            f.submit()

    def test_form_with_duplicate_buttons(self):
        class Button(form.Button):
            def relative_path(self):
                return super().relative_path()[:-1]

            def on_submit(self):
                super().on_submit()
                raise Valid(self.id)

            def on_error(self):
                super().on_error()
                raise Invalid(self.id)

        query = '&'.join((
            f'{ayame.AYAME_PATH}=a',
            'b',
        ))
        with self.application(self.new_environ(query=query)):
            f = form.Form('a')
            f._method = 'GET'
            f.add(Button('b1'))
            f.add(Button('b2'))
            with self.assertRaisesRegex(Valid, r'^b1$'):
                f.submit()

    def test_form(self):
        with self.application(self.new_environ()):
            p = SpamPage()
            status, headers, content = p()

            f = p.find('form')
            self.assertEqual(f.model_object['text'], '')
            self.assertEqual(f.model_object['password'], '')
            self.assertEqual(f.model_object['hidden'], '')
            self.assertEqual(f.model_object['area'], 'Hello World!\n')
            self.assertEqual(f.model_object['checkbox'], True)
            self.assertIsNone(f.model_object['file'])
            self.assertNotIn('button', f.model_object)
        html = self.format(SpamPage)
        self.assertEqual(status, http.OK.status)
        self.assertEqual(headers, [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', str(len(html))),
        ])
        self.assertEqual(content, [html])

    def test_form_get(self):
        for b in (False, True):
            with self.subTest(button=b):
                q = [
                    f'{ayame.AYAME_PATH}=form',
                    'text=text',
                    'password=password',
                    'hidden=hidden',
                    'area=area',
                    'file=a.txt',
                    'button',
                ]
                o = {
                    'text': 'text',
                    'password': 'password',
                    'hidden': 'hidden',
                    'area': 'area',
                    'checkbox': False,
                    'file': 'a.txt',
                    'button': 'submitted',
                }
                if not b:
                    del q[-1]
                    del o['button']
                with self.application(self.new_environ(query='&'.join(q))):
                    p = SpamPage()
                    with self.assertRaisesRegex(Valid, r'^button$' if b else r'^form$'):
                        p()
                    f = p.find('form')
                    self.assertEqual(f.model_object, o)
                    self.assertFalse(f.has_error())

    def test_form_post(self):
        for b in (False, True):
            with self.subTest(button=b):
                data = [
                    (ayame.AYAME_PATH, 'form'),
                    ('text', 'text'),
                    ('password', 'password'),
                    ('hidden', 'hidden'),
                    ('area', 'area'),
                    ('file', ('a.txt', 'spam\neggs\nham\n', 'text/plain')),
                    ('button', ''),
                ]
                if not b:
                    del data[-1]
                with self.application(self.new_environ(method='POST', form=self.form_data(*data))):
                    p = SpamPage()
                    with self.assertRaisesRegex(Valid, r'^button$' if b else r'^form$'):
                        p()
                    f = p.find('form')
                    self.assertEqual(f.model_object['text'], 'text')
                    self.assertEqual(f.model_object['password'], 'password')
                    self.assertEqual(f.model_object['hidden'], 'hidden')
                    self.assertEqual(f.model_object['area'], 'area')
                    self.assertEqual(f.model_object['checkbox'], False)
                    self.assertEqual(f.model_object['file'].name, 'file')
                    self.assertEqual(f.model_object['file'].filename, 'a.txt')
                    self.assertEqual(f.model_object['file'].read(), b'spam\neggs\nham\n')
                    self.assertEqual(f.model_object['file'].mimetype, 'text/plain')
                    self.assertEqual(f.model_object['file'].mimetype_params, {})
                    if b:
                        self.assertEqual(f.model_object['button'], 'submitted')
                    self.assertFalse(f.has_error())

    def test_form_required_error(self):
        for b in (False, True):
            with self.subTest(button=b):
                q = [
                    f'{ayame.AYAME_PATH}=form',
                    'area=area',
                    'file=a.txt',
                    'button',
                ]
                if not b:
                    del q[-1]
                with self.application(self.new_environ(query='&'.join(q))):
                    p = SpamPage()
                    for path in ('form:text', 'form:password', 'form:hidden'):
                        p.find(path).required = True
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

    def test_form_with_invisible_form_component(self):
        for b in (False, True):
            with self.subTest(button=b):
                q = [
                    f'{ayame.AYAME_PATH}=form',
                    'area=area',
                    'file=a.txt',
                    'button',
                ]
                o = {
                    'text': '',
                    'password': '',
                    'hidden': '',
                    'area': 'area',
                    'checkbox': False,
                    'file': 'a.txt',
                    'button': 'submitted',
                }
                if not b:
                    del q[-1]
                    del o['button']
                with self.application(self.new_environ(query='&'.join(q))):
                    p = SpamPage()
                    for path in ('form:text', 'form:password', 'form:hidden'):
                        p.find(path).visible = False
                        p.find(path).required = True
                    with self.assertRaises(Valid):
                        p()
                    f = p.find('form')
                    self.assertEqual(f.model_object, o)
                    self.assertFalse(f.has_error())

    def test_form_unbound(self):
        query = '&'.join((
            f'{ayame.AYAME_PATH}=__form__',
        ))
        with self.application(self.new_environ(query=query)):
            p = SpamPage()
            p.add(Form('__form__'))
            p()

            self.assertIsNone(p.find('__form__').model_object)

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
        fc = form.FormComponent(__name__)
        fc.required = True
        self.assertIsNone(fc.error)
        with self.application(self.new_environ()):
            for v in (None, ''):
                with self.subTest(value=v):
                    fc.validate(v)
                    self.assertRequiredError(fc, v)

    def test_form_component_conversion_error(self):
        fc = form.FormComponent(__name__)
        fc.type = int
        self.assertIsNone(fc.error)
        with self.application(self.new_environ()):
            fc.validate('str')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), fr"'{__name__}' is not a valid type 'int'")
            self.assertEqual(e.keys, [
                'Converter.int',
                'Converter',
            ])
            self.assertEqual(e.vars, {
                'input': 'str',
                'name': __name__,
                'label': __name__,
                'type': 'int',
            })

    def test_form_component_validation_error_range(self):
        fc = form.FormComponent(__name__)
        v = validator.RangeValidator()
        fc.add(v)
        self.assertIsNone(fc.error)
        with self.application(self.new_environ()):
            for min, max in (
                (0.0, None),
                (None, 0.0),
            ):
                with self.subTest(min=min, max=max):
                    v.min = min
                    v.max = max
                    fc.validate(0)
                    e = fc.error
                    self.assertIsInstance(e, ayame.ValidationError)
                    self.assertRegex(str(e), fr"'{__name__}' cannot validate$")
                    self.assertEqual(e.keys, ['RangeValidator.type'])
                    self.assertEqual(e.vars, {
                        'input': 0,
                        'name': __name__,
                        'label': __name__,
                    })

            v.min = 1
            v.max = None
            fc.validate(0)
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), fr"'{__name__}' must be at least 1$")
            self.assertEqual(e.keys, ['RangeValidator.minimum'])
            self.assertEqual(e.vars, {
                'input': 0,
                'name': __name__,
                'label': __name__,
                'min': 1,
            })

            v.min = None
            v.max = 3
            fc.validate(4)
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), fr"'{__name__}' must be at most 3$")
            self.assertEqual(e.keys, ['RangeValidator.maximum'])
            self.assertEqual(e.vars, {
                'input': 4,
                'name': __name__,
                'label': __name__,
                'max': 3,
            })

            v.min = 5
            v.max = 7
            fc.validate(2)
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), fr"'{__name__}' must be between 5 and 7$")
            self.assertEqual(e.keys, ['RangeValidator.range'])
            self.assertEqual(e.vars, {
                'input': 2,
                'name': __name__,
                'label': __name__,
                'min': 5,
                'max': 7,
            })

            v.min = v.max = 9
            fc.validate(8)
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), fr"'{__name__}' must be exactly 9$")
            self.assertEqual(e.keys, ['RangeValidator.exact'])
            self.assertEqual(e.vars, {
                'input': 8,
                'name': __name__,
                'label': __name__,
                'exact': 9,
            })

    def test_form_component_validation_error_string(self):
        fc = form.FormComponent(__name__)
        v = validator.StringValidator()
        fc.add(v)
        self.assertIsNone(fc.error)
        with self.application(self.new_environ()):
            for min, max, iv in (
                (None, None, None),
                (0.0, None, ''),
                (None, 0.0, ''),
            ):
                with self.subTest(min=min, max=max):
                    v.min = min
                    v.max = max
                    fc.validate(iv)
                    e = fc.error
                    self.assertIsInstance(e, ayame.ValidationError)
                    self.assertRegex(str(e), fr"'{__name__}' cannot validate$")
                    self.assertEqual(e.keys, ['StringValidator.type'])
                    self.assertEqual(e.vars, {
                        'input': iv,
                        'name': __name__,
                        'label': __name__,
                    })

            v.min = 1
            v.max = None
            fc.validate('')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), fr"'{__name__}' must be at least 1 ")
            self.assertEqual(e.keys, ['StringValidator.minimum'])
            self.assertEqual(e.vars, {
                'input': '',
                'name': __name__,
                'label': __name__,
                'min': 1,
            })

            v.min = None
            v.max = 3
            fc.validate('three')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), fr"'{__name__}' must be at most 3 ")
            self.assertEqual(e.keys, ['StringValidator.maximum'])
            self.assertEqual(e.vars, {
                'input': 'three',
                'name': __name__,
                'label': __name__,
                'max': 3,
            })

            v.min = 5
            v.max = 7
            fc.validate('five')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), fr"'{__name__}' must be between 5 and 7 ")
            self.assertEqual(e.keys, ['StringValidator.range'])
            self.assertEqual(e.vars, {
                'input': 'five',
                'name': __name__,
                'label': __name__,
                'min': 5,
                'max': 7,
            })

            v.min = v.max = 9
            fc.validate('nine')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), fr"'{__name__}' must be exactly 9 ")
            self.assertEqual(e.keys, ['StringValidator.exact'])
            self.assertEqual(e.vars, {
                'input': 'nine',
                'name': __name__,
                'label': __name__,
                'exact': 9,
            })

    def test_form_component_validation_error_regex(self):
        fc = form.FormComponent(__name__)
        v = validator.RegexValidator(r'^\d+$')
        fc.add(v)
        self.assertIsNone(fc.error)
        with self.application(self.new_environ()):
            fc.validate('')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), fr"'{__name__}' does not match pattern ")
            self.assertEqual(e.keys, ['RegexValidator'])
            self.assertEqual(e.vars, {
                'input': '',
                'name': __name__,
                'label': __name__,
                'pattern': v.regex.pattern,
            })

    def test_form_component_validation_error_email(self):
        fc = form.FormComponent(__name__)
        v = validator.EmailValidator()
        fc.add(v)
        self.assertIsNone(fc.error)
        with self.application(self.new_environ()):
            fc.validate('')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), fr"'{__name__}' is not a valid email address$")
            self.assertEqual(e.keys, ['EmailValidator'])
            self.assertEqual(e.vars, {
                'input': '',
                'name': __name__,
                'label': __name__,
                'pattern': v.regex.pattern,
            })

    def test_form_component_validation_error_url(self):
        fc = form.FormComponent(__name__)
        v = validator.URLValidator()
        fc.add(v)
        self.assertIsNone(fc.error)
        with self.application(self.new_environ()):
            fc.validate('')
            e = fc.error
            self.assertIsInstance(e, ayame.ValidationError)
            self.assertRegex(str(e), fr"'{__name__}' is not a valid URL$")
            self.assertEqual(e.keys, ['URLValidator'])
            self.assertEqual(e.vars, {
                'input': '',
                'name': __name__,
                'label': __name__,
                'pattern': v.regex.pattern,
            })

    def test_form_component_without_model(self):
        fc = form.FormComponent(__name__)
        with self.application():
            fc.validate('a')
            self.assertIsNone(fc.error)
            self.assertIsNone(fc.model)
            self.assertIsNone(fc.model_object)

    def test_form_component_with_invalid_markup(self):
        for cls, attrib, regex in (
            (
                form.Button,
                {form._TYPE: 'text'},
                r"'input' .* 'submit'",
            ),
            (
                form.Button,
                None,
                r"'input' or 'button' element ",
            ),
            (
                form.FileUploadField,
                None,
                r"'input' element is ",
            ),
            (
                form.TextField,
                None,
                r"'input' element is ",
            ),
            (
                form.TextArea,
                None,
                r"'textarea' element is ",
            ),
            (
                form.CheckBox,
                {form._TYPE: 'text'},
                r"'input' .* 'checkbox'",
            ),
            (
                form.CheckBox,
                None,
                r"'input' element is ",
            ),
            (
                form.SelectChoice,
                None,
                r"'select' element is ",
            ),
        ):
            with self.subTest(cls=cls):
                fc = cls(__name__)
                with self.assertRaisesRegex(ayame.RenderingError, regex):
                    fc.render(markup.Element(form._INPUT, attrib) if attrib else self.empty_element())

    def test_button(self):
        el = markup.Element(form._FORM,
                            {
                                form._METHOD: 'GET',
                            })
        el.append(markup.Element(form._BUTTON,
                                 {
                                     markup.AYAME_ID: 'b',
                                 }))
        f = form.Form('a')
        f.add(form.Button('b'))
        with self.application(self.new_environ()):
            rv = f.render(el)
        self.assertIs(rv, el)
        self.assertEqual(len(rv), 2)

        b = el.children[1]
        self.assertEqual(b.qname, form._BUTTON)
        self.assertEqual(b.attrib, {
            form._NAME: 'b',
        })

    def test_check_box(self):
        el = markup.Element(form._FORM,
                            {
                                form._METHOD: 'GET',
                            })
        el.append(markup.Element(form._INPUT,
                                 {
                                     markup.AYAME_ID: 'b',
                                     form._TYPE: 'checkbox',
                                 }))
        f = form.Form('a')
        f.add(form.CheckBox('b'))
        with self.application(self.new_environ()):
            rv = f.render(el)
        self.assertIs(rv, el)
        self.assertEqual(len(el), 2)

        i = el.children[1]
        self.assertEqual(i.qname, form._INPUT)
        self.assertEqual(i.attrib, {
            form._NAME: 'b',
            form._TYPE: 'checkbox',
            form._VALUE: 'on',
        })

    def test_choice_id_prefix(self):
        fc = form.Choice(__name__)
        el = self.empty_element(attrib={
            form._ID: __name__,
        })
        self.assertEqual(fc._id_prefix_for(el), __name__)

        el = self.empty_element()
        a = fc._id_prefix_for(el)
        b = fc._id_prefix_for(el)
        self.assertNotEqual(a, b)
        self.assertTrue(a.startswith('ayame-'))
        self.assertTrue(b.startswith('ayame-'))

    def test_radio_choice(self):
        for c in (True, False):
            for r in (form.ChoiceRenderer, ChoiceRenderer):
                with self.subTest(choices=c, renderer=r):
                    with self.application(self.new_environ()):
                        p = EggsPage()
                        if not c:
                            p.find('form:radio').choices = []
                        p.find('form:radio').renderer = r()
                        status, headers, content = p()

                        f = p.find('form')
                        self.assertEqual(f.model_object, {'radio': p.choices[0]})
                    html = self.format(EggsPage, choices=c)
                    self.assertEqual(status, http.OK.status)
                    self.assertEqual(headers, [
                        ('Content-Type', 'text/html; charset=UTF-8'),
                        ('Content-Length', str(len(html))),
                    ])
                    self.assertEqual(content, [html])

    def test_radio_choice_post(self):
        for c, data, o in (
            # select
            (
                True,
                self.form_data(
                    (ayame.AYAME_PATH, 'form'),
                    ('radio', '1'),
                ),
                {'radio': EggsPage.choices[1]},
            ),
            # no choices
            (
                False,
                self.form_data(
                    (ayame.AYAME_PATH, 'form'),
                    ('radio', '2'),
                ),
                {'radio': EggsPage.choices[0]},
            ),
            # empty
            (
                True,
                self.form_data(
                    (ayame.AYAME_PATH, 'form'),
                ),
                {'radio': None},
            ),
        ):
            with self.subTest(c=c, form_data=data):
                with self.application(self.new_environ(method='POST', form=data)):
                    p = EggsPage()
                    if not c:
                        p.find('form:radio').choices = []
                    with self.assertRaises(Valid):
                        p()
                    f = p.find('form')
                    self.assertEqual(f.model_object, o)
                    self.assertFalse(f.has_error())

    def test_radio_choice_required_error(self):
        data = self.form_data(
            (ayame.AYAME_PATH, 'form'),
        )
        with self.application(self.new_environ(method='POST', form=data)):
            p = EggsPage()
            p.find('form:radio').required = True
            with self.assertRaises(Invalid):
                p()
            f = p.find('form')
            self.assertEqual(f.model_object, {'radio': p.choices[0]})
            self.assertTrue(f.has_error())
            self.assertRequiredError(f.find('radio'), [])

    def test_radio_choice_validation_error(self):
        for data, v in (
            # out of range
            (
                self.form_data(
                    (ayame.AYAME_PATH, 'form'),
                    ('radio', '-1'),
                ),
                '-1',
            ),
            # no value
            (
                self.form_data(
                    (ayame.AYAME_PATH, 'form'),
                    ('radio', ''),
                ),
                '',
            ),
        ):
            with self.subTest(form_data=data):
                with self.application(self.new_environ(method='POST', form=data)):
                    p = EggsPage()
                    with self.assertRaises(Invalid):
                        p()
                    f = p.find('form')
                    self.assertEqual(f.model_object, {'radio': p.choices[0]})
                    self.assertTrue(f.has_error())
                    self.assertChoiceError(f.find('radio'), [v])

    def test_check_box_choice(self):
        for m in (True, False):
            for c in (True, False):
                for r in (form.ChoiceRenderer, ChoiceRenderer):
                    with self.subTest(multiple=m, choices=c, renderer=r):
                        with self.application(self.new_environ()):
                            p = HamPage(multiple=m)
                            if not c:
                                p.find('form:checkbox').choices = []
                            p.find('form:checkbox').renderer = r()
                            status, headers, content = p()

                            f = p.find('form')
                            self.assertEqual(f.model_object, {'checkbox': p.choices[:2] if m else p.choices[0]})
                        html = self.format(HamPage, choices=(2 if m else 1) * int(c))
                        self.assertEqual(status, http.OK.status)
                        self.assertEqual(headers, [
                            ('Content-Type', 'text/html; charset=UTF-8'),
                            ('Content-Length', str(len(html))),
                        ])
                        self.assertEqual(content, [html])

    def test_check_box_choice_post(self):
        for m, c, data, o in (
            # select
            (
                True,
                True,
                self.form_data(
                    (ayame.AYAME_PATH, 'form'),
                    ('checkbox', '0'),
                    ('checkbox', '1'),
                    ('checkbox', '2'),
                ),
                {'checkbox': HamPage.choices},
            ),
            (
                False,
                True,
                self.form_data(
                    (ayame.AYAME_PATH, 'form'),
                    ('checkbox', '1'),
                ),
                {'checkbox': HamPage.choices[1]},
            ),
            # no choices
            (
                True,
                False,
                self.form_data(
                    (ayame.AYAME_PATH, 'form'),
                    ('checkbox', '0'),
                    ('checkbox', '1'),
                    ('checkbox', '2'),
                ),
                {'checkbox': HamPage.choices[:2]},
            ),
            (
                False,
                False,
                self.form_data(
                    (ayame.AYAME_PATH, 'form'),
                    ('checkbox', '2'),
                ),
                {'checkbox': HamPage.choices[0]},
            ),
            # empty
            (
                True,
                True,
                self.form_data(
                    (ayame.AYAME_PATH, 'form'),
                ),
                {'checkbox': []},
            ),
            (
                False,
                True,
                self.form_data(
                    (ayame.AYAME_PATH, 'form'),
                ),
                {'checkbox': None},
            ),
        ):
            with self.subTest(multiple=m, choices=c, form_data=data):
                with self.application(self.new_environ(method='POST', form=data)):
                    p = HamPage(multiple=m)
                    if not c:
                        p.find('form:checkbox').choices = []
                    with self.assertRaises(Valid):
                        p()
                    f = p.find('form')
                    self.assertEqual(f.model_object, o)
                    self.assertFalse(f.has_error())

    def test_check_box_choice_required_error(self):
        data = self.form_data(
            (ayame.AYAME_PATH, 'form'),
        )
        for m in (True, False):
            with self.subTest(multiple=m):
                with self.application(self.new_environ(method='POST', form=data)):
                    p = HamPage(multiple=m)
                    p.find('form:checkbox').required = True
                    with self.assertRaises(Invalid):
                        p()
                    f = p.find('form')
                    self.assertEqual(f.model_object, {'checkbox': p.choices[:2] if m else p.choices[0]})
                    self.assertTrue(f.has_error())
                    self.assertRequiredError(f.find('checkbox'), [])

    def test_check_box_choice_validation_error(self):
        for m, data, v in (
            # out of range
            (
                True,
                self.form_data(
                    (ayame.AYAME_PATH, 'form'),
                    ('checkbox', '-1'),
                    ('checkbox', '1'),
                    ('checkbox', '3'),
                ),
                ['-1', '1', '3'],
            ),
            (
                False,
                self.form_data(
                    (ayame.AYAME_PATH, 'form'),
                    ('checkbox', '-1'),
                ),
                ['-1'],
            ),
            # no values
            (
                True,
                self.form_data(
                    (ayame.AYAME_PATH, 'form'),
                    ('checkbox', ''),
                    ('checkbox', '1'),
                    ('checkbox', ''),
                ),
                ['', '1', ''],
            ),
            (
                False,
                self.form_data(
                    (ayame.AYAME_PATH, 'form'),
                    ('checkbox', ''),
                ),
                [''],
            ),
        ):
            with self.subTest(multiple=m, form_data=data):
                with self.application(self.new_environ(method='POST', form=data)):
                    p = HamPage(multiple=m)
                    with self.assertRaises(Invalid):
                        p()
                    f = p.find('form')
                    self.assertEqual(f.model_object, {'checkbox': p.choices[:2] if m else p.choices[0]})
                    self.assertTrue(f.has_error())
                    self.assertChoiceError(f.find('checkbox'), v)

    def test_select_choice(self):
        for cls in (ToastPage, BeansPage):
            for m in (True, False):
                for c in (True, False):
                    for r in (form.ChoiceRenderer, ChoiceRenderer):
                        with self.subTest(page=cls, multiple=m, choices=c, renderer=r):
                            with self.application(self.new_environ()):
                                p = cls(multiple=m)
                                if not c:
                                    p.find('form:select').choices = []
                                p.find('form:select').renderer = r()
                                status, headers, content = p()

                                f = p.find('form')
                                self.assertEqual(f.model_object, {'select': p.choices[:2] if m else p.choices[0]})
                            html = self.format(type(p), multiple=m, choices=(2 if m else 1) * int(c))
                            self.assertEqual(status, http.OK.status)
                            self.assertEqual(headers, [
                                ('Content-Type', 'text/html; charset=UTF-8'),
                                ('Content-Length', str(len(html))),
                            ])
                            self.assertEqual(content, [html])

    def test_select_choice_post(self):
        for cls in (ToastPage, BeansPage):
            for m, c, data, o in (
                # select
                (
                    True,
                    True,
                    self.form_data(
                        (ayame.AYAME_PATH, 'form'),
                        ('select', '0'),
                        ('select', '1'),
                        ('select', '2'),
                    ),
                    {'select': ToastPage.choices},
                ),
                (
                    False,
                    True,
                    self.form_data(
                        (ayame.AYAME_PATH, 'form'),
                        ('select', '1'),
                    ),
                    {'select': BeansPage.choices[1]},
                ),
                # no choices
                (
                    True,
                    False,
                    self.form_data(
                        (ayame.AYAME_PATH, 'form'),
                        ('select', '0'),
                        ('select', '1'),
                        ('select', '2'),
                    ),
                    {'select': ToastPage.choices[:2]},
                ),
                (
                    False,
                    False,
                    self.form_data(
                        (ayame.AYAME_PATH, 'form'),
                        ('select', '2'),
                    ),
                    {'select': BeansPage.choices[0]},
                ),
                # empty
                (
                    True,
                    True,
                    self.form_data(
                        (ayame.AYAME_PATH, 'form'),
                    ),
                    {'select': []},
                ),
                (
                    False,
                    True,
                    self.form_data(
                        (ayame.AYAME_PATH, 'form'),
                    ),
                    {'select': None},
                ),
            ):
                with self.subTest(page=cls, multiple=m, choices=c, form_data=data):
                    with self.application(self.new_environ(method='POST', form=data)):
                        p = cls(multiple=m)
                        if not c:
                            p.find('form:select').choices = []
                        with self.assertRaises(Valid):
                            p()
                        f = p.find('form')
                        self.assertEqual(f.model_object, o)
                        self.assertFalse(f.has_error())

    def test_select_choice_required_error(self):
        data = self.form_data(
            (ayame.AYAME_PATH, 'form'),
        )
        for cls in (ToastPage, BeansPage):
            for m in (True, False):
                with self.subTest(page=cls, multiple=m):
                    with self.application(self.new_environ(method='POST', form=data)):
                        p = cls(multiple=m)
                        p.find('form:select').required = True
                        with self.assertRaises(Invalid):
                            p()
                        f = p.find('form')
                        self.assertEqual(f.model_object, {'select': p.choices[:2] if m else p.choices[0]})
                        self.assertTrue(f.has_error())
                        self.assertRequiredError(f.find('select'), [])

    def test_select_choice_validation_error(self):
        for cls in (ToastPage, BeansPage):
            for m, data, v in (
                # out of range
                (
                    True,
                    self.form_data(
                        (ayame.AYAME_PATH, 'form'),
                        ('select', '-1'),
                        ('select', '1'),
                        ('select', '3'),
                    ),
                    ['-1', '1', '3'],
                ),
                (
                    False,
                    self.form_data(
                        (ayame.AYAME_PATH, 'form'),
                        ('select', '-1'),
                    ),
                    ['-1'],
                ),
                # no values
                (
                    True,
                    self.form_data(
                        (ayame.AYAME_PATH, 'form'),
                        ('select', ''),
                        ('select', '1'),
                        ('select', ''),
                    ),
                    ['', '1', ''],
                ),
                (
                    False,
                    self.form_data(
                        (ayame.AYAME_PATH, 'form'),
                        ('select', ''),
                    ),
                    [''],
                ),
            ):
                with self.subTest(page=cls, multiple=m, form_data=data):
                    with self.application(self.new_environ(method='POST', form=data)):
                        p = cls(multiple=m)
                        with self.assertRaises(Invalid):
                            p()
                        f = p.find('form')
                        self.assertEqual(f.model_object, {'select': p.choices[:2] if m else p.choices[0]})
                        self.assertTrue(f.has_error())
                        self.assertChoiceError(f.find('select'), v)


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

    choices = [
        datetime.date(2012, 1, 1),
        datetime.date(2012, 1, 2),
        datetime.date(2012, 1, 3),
    ]
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
        """ if v else '',
    }

    def __init__(self):
        super().__init__()
        self.add(Form('form', model.CompoundModel({})))
        self.find('form').add(form.RadioChoice('radio', choices=self.choices))
        self.find('form:radio').model_object = self.choices[0]


class HamPage(ayame.Page):

    choices = [
        datetime.date(2012, 1, 1),
        datetime.date(2012, 1, 2),
        datetime.date(2012, 1, 3),
    ]
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

    choices = [
        datetime.date(2012, 1, 1),
        datetime.date(2012, 1, 2),
        datetime.date(2012, 1, 3),
    ]
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
        'choices': lambda v=2: textwrap.indent(textwrap.dedent("""
            <option {}value="0">2012-01-01</option>
            <option {}value="1">2012-01-02</option>
            <option {}value="2">2012-01-03</option>\
        """), '  ' * 5).rstrip().format(*('selected="selected" ',) * v + ('',) * (3 - v)) if v else '',
    }

    def __init__(self, multiple):
        super().__init__()
        self.kwargs['title'] = type(self).__name__
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
