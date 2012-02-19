#
# test_form
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
#i   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
#   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#   ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#   CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
#

from __future__ import unicode_literals
from contextlib import contextmanager
import io

from nose.tools import assert_raises, eq_, ok_

from ayame import core, form, http, markup, model, validator
from ayame.exception import AyameError, ComponentError, RenderingError
from ayame.exception import ValidationError


@contextmanager
def application(environ=None):
    local = core._local
    app = core.Ayame(__name__)
    app.config['ayame.markup.pretty'] = True
    try:
        local.app = app
        local.environ = environ
        yield
    finally:
        local.environ = None
        local.app = None

def test_form_error():
    # not form element
    f = form.Form('a')
    assert_raises(RenderingError, f.render, markup.Element(markup.DIV))

    # method is not found
    root = markup.Element(form._FORM)
    root.attrib[form._ACTION] = '/'
    f = form.Form('a')
    assert_raises(RenderingError, f.render, root)

    # method mismatch
    class Form(form.Form):
        def on_method_mismatch(self):
            return False
    f = Form('a')
    f.add(form.FormComponent('b'))
    query = 'b=1'
    environ = {'REQUEST_METHOD': 'GET',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'QUERY_STRING': query.encode('utf-8')}
    with application(environ):
        request = core.Request(environ, {})
        f._method = 'POST'
        f.submit(request)

    # unknown method
    f = form.Form('a')
    query = 'b=1'
    environ = {'REQUEST_METHOD': 'PUT',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'QUERY_STRING': query.encode('utf-8')}
    with application(environ):
        request = core.Request(environ, {})
        f._method = 'POST'
        f.submit(request)

    # form is nested
    f = form.Form('a')
    f.add(form.Form('b'))
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form'}
    with application(environ):
        request = core.Request(environ, {})
        f._method = 'POST'
        assert_raises(ComponentError, f.submit, request)

def test_form():
    content_length = '737'
    xhtml = ('<?xml version="1.0"?>\n'
             '{doctype}\n'
             '<html xmlns="{xhtml}">\n'
             '  <head>\n'
             '    <title>SpamPage</title>\n'
             '  </head>\n'
             '  <body>\n'
             '    <form action="/form" method="post">\n'
             '      <div class="ayame-hidden">'
             '<input name="{path}" type="hidden" value="form"/></div>\n'
             '      <fieldset>\n'
             '        <legend>form</legend>\n'
             '        <input name="text" type="text"/><br/>\n'
             '        <input name="password" type="password"/><br/>\n'
             '        <input name="hidden" type="hidden"/><br/>\n'
             '        <input checked="checked" name="checkbox" '
             'type="checkbox" value="on"/><br/>\n'
             '        <input name="button" type="submit"/>\n'
             '      </fieldset>\n'
             '    </form>\n'
             '  </body>\n'
             '</html>\n').format(doctype=markup.XHTML1_STRICT,
                                 xhtml=markup.XHTML_NS,
                                 path=core.AYAME_PATH)
    model_object = {'text': 'text',
                    'password': 'password',
                    'hidden': 'hidden',
                    'checkbox': False,
                    'button': 'submitted'}

    class Button(form.Button):
        def on_submit(self):
            super(Button, self).on_submit()
            self.model_object = 'submitted'

    class SpamPage(core.Page):
        def __init__(self, request):
            super(SpamPage, self).__init__(request)
            self.add(form.Form('form',
                               model.CompoundModel({'checkbox': True})))
            self.find('form').add(form.TextField('text'))
            self.find('form').add(form.PasswordField('password'))
            self.find('form').add(form.HiddenField('hidden'))
            self.find('form').add(form.CheckBox('checkbox'))
            self.find('form').add(Button('button'))

    # GET
    query = ('{}=form&'
             'text=text&'
             'password=password&'
             'hidden=hidden&'
             'button').format(core.AYAME_PATH)
    environ = {'REQUEST_METHOD': 'GET',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'QUERY_STRING': query.encode('utf-8')}
    with application(environ):
        request = core.Request(environ, {})
        page = SpamPage(request)
        status, headers, body = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', content_length)])
    eq_(body, xhtml)
    eq_(page.find('form').model_object, model_object)

    # POST
    body = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="text"\r\n'
            '\r\n'
            'text\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="password"\r\n'
            '\r\n'
            'password\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="hidden"\r\n'
            '\r\n'
            'hidden\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="button"\r\n'
            '\r\n'
            '--ayame.form--\r\n'
            '\r\n').format(core.AYAME_PATH)
    environ = {'wsgi.input': io.BytesIO(body.encode('utf-8')),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form'}
    with application(environ):
        request = core.Request(environ, {})
        page = SpamPage(request)
        status, headers, body = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', content_length)])
    eq_(body, xhtml)
    eq_(page.find('form').model_object, model_object)

def test_form_component():
    # relative path
    f = form.Form('a')
    f.add(form.FormComponent('b1'))
    f.add(core.MarkupContainer('b2'))
    f.find('b2').add(form.FormComponent('c'))
    eq_(f.find('b1').relative_path(), 'b1')
    eq_(f.find('b2').find('c').relative_path(), 'b2:c')
    assert_raises(ComponentError, form.FormComponent('a').relative_path)

    # required error
    fc = form.FormComponent('a')
    fc.required = True
    assert_raises(ValidationError, fc.validate, None)
    assert_raises(ValidationError, fc.validate, '')

    # conversion error
    with application():
        fc = form.FormComponent('a')
        fc.type = int
        assert_raises(ValidationError, fc.validate, 'a')

    # validation error
    with application():
        fc = form.FormComponent('a')
        fc.add(validator.StringValidator(max=4))
        assert_raises(ValidationError, fc.validate, '.info')

    # no model
    with application():
        fc = form.FormComponent('a')
        fc.validate('a')
        eq_(fc.model, None)
        eq_(fc.model_object, None)

def test_invalid_markup():
    input = markup.Element(form._INPUT)
    input.attrib[form._TYPE] = 'text'

    button = form.Button('a')
    assert_raises(RenderingError, button.render, input)
    assert_raises(RenderingError, button.render, markup.Element(markup.DIV))

    tf = form.TextField('a')
    assert_raises(RenderingError, tf.render, markup.Element(markup.DIV))

    checkbox = form.CheckBox('a')
    assert_raises(RenderingError, checkbox.render, input)
    assert_raises(RenderingError, checkbox.render, markup.Element(markup.DIV))
