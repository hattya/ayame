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
#   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
#   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#   ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#   CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
#

from contextlib import contextmanager
from datetime import date
import io

from nose.tools import assert_raises, eq_, ok_

from ayame import core, form, http, local, markup, model, uri, validator
from ayame import app as _app
from ayame.exception import ComponentError, RenderingError, ValidationError


@contextmanager
def application(environ=None):
    app = _app.Ayame(__name__)
    app.config['ayame.markup.pretty'] = True
    try:
        ctx = local.push(app, environ)
        if environ is not None:
            ctx.request = app.config['ayame.request'](environ, {})
        yield
    finally:
        local.pop()


class Form(form.Form):

    def on_submit(self):
        super(Form, self).on_submit()
        raise Valid()

    def on_error(self):
        super(Form, self).on_error()
        raise Invalid()


class Valid(Exception):
    pass


class Invalid(Exception):
    pass


def test_form_error():
    # not form element
    f = form.Form('a')
    assert_raises(RenderingError, f.render, markup.Element(markup.DIV))

    # method is not found
    root = markup.Element(form._FORM)
    root.attrib[form._ACTION] = u'/'
    f = form.Form('a')
    assert_raises(RenderingError, f.render, root)

    # method mismatch
    class Form(form.Form):
        def on_method_mismatch(self):
            return False
    f = Form('a')
    f.add(form.FormComponent('b'))
    query = 'b=1'
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'QUERY_STRING': uri.quote(query)}
    with application(environ):
        f._method = 'POST'
        f.submit()

    # unknown method
    f = form.Form('a')
    query = 'b=1'
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'PUT',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'QUERY_STRING': uri.quote(query),
               'CONTENT_LENGTH': '0'}
    with application(environ):
        f._method = 'POST'
        f.submit()

    # form is nested
    f = form.Form('a')
    f.add(form.Form('b'))
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_LENGTH': '0'}
    with application(environ):
        f._method = 'POST'
        assert_raises(ComponentError, f.submit)


def test_form():
    class SpamPage(core.Page):
        def __init__(self):
            super(SpamPage, self).__init__()
            self.add(form.Form('form', model.CompoundModel({})))
            self.find('form').add(form.TextField('text'))
            self.find('form:text').model_object = u''
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
            self.find('form').add(Button('button'))

    class Button(form.Button):
        def on_submit(self):
            super(Button, self).on_submit()
            self.model_object = 'submitted'
            raise Valid()
        def on_error(self):
            super(Button, self).on_error()
            raise Invalid()

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
             '        <input name="text" type="text" value=""/><br/>\n'
             '        <input name="password" type="password" value=""/><br/>\n'
             '        <input name="hidden" type="hidden" value=""/><br/>\n'
             '        <textarea name="area">\n'
             '          Hello World!\n'
             '        </textarea>\n'
             '        <input checked="checked" name="checkbox" '
             'type="checkbox" value="on"/><br/>\n'
             '        <input name="file" type="file"/><br/>\n'
             '        <input name="button" type="submit"/>\n'
             '      </fieldset>\n'
             '    </form>\n'
             '  </body>\n'
             '</html>\n').format(doctype=markup.XHTML1_STRICT,
                                 xhtml=markup.XHTML_NS,
                                 path=core.AYAME_PATH)
    xhtml = xhtml.encode('utf-8')

    # GET
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form'}
    with application(environ):
        page = SpamPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)
    f = page.find('form')
    eq_(f.model_object['text'], '')
    eq_(f.model_object['password'], '')
    eq_(f.model_object['hidden'], '')
    eq_(f.model_object['area'], 'Hello World!')
    eq_(f.model_object['checkbox'], True)
    eq_(f.model_object['file'], None)
    ok_('button' not in f.model_object)

    # GET
    query = ('{}=form&'
             'text=text&'
             'password=password&'
             'hidden=hidden&'
             'area=area&'
             'file=a.txt&'
             'button').format(core.AYAME_PATH)
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'QUERY_STRING': uri.quote(query)}
    with application(environ):
        page = SpamPage()
        assert_raises(Valid, page.render)
    eq_(page.find('form').model_object, {'text': 'text',
                                         'password': 'password',
                                         'hidden': 'hidden',
                                         'area': 'area',
                                         'checkbox': False,
                                         'file': 'a.txt',
                                         'button': 'submitted'})
    ok_(not page.find('form').has_error())

    # POST
    data = ('--ayame.form\r\n'
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
            'Content-Disposition: form-data; name="area"\r\n'
            '\r\n'
            'area\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="file"; filename="a.txt"\r\n'
            'Content-Type: text/plain\r\n'
            '\r\n'
            'spam\n'
            'eggs\n'
            'ham\n'
            '\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="button"\r\n'
            '\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = SpamPage()
        assert_raises(Valid, page.render)
    f = page.find('form')
    eq_(f.model_object['text'], 'text')
    eq_(f.model_object['password'], 'password')
    eq_(f.model_object['hidden'], 'hidden')
    eq_(f.model_object['area'], 'area')
    eq_(f.model_object['checkbox'], False)
    eq_(f.model_object['file'].name, 'file')
    eq_(f.model_object['file'].filename, 'a.txt')
    eq_(f.model_object['file'].value, b'spam\neggs\nham\n')
    ok_(f.model_object['file'].file is not None)
    eq_(f.model_object['file'].type, 'text/plain')
    eq_(f.model_object['file'].type_options, {})
    eq_(f.model_object['button'], 'submitted')
    ok_(not f.has_error())

    # required error
    query = ('{}=form&'
             'area=area&'
             'file=a.txt&'
             'button').format(core.AYAME_PATH)
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'QUERY_STRING': uri.quote(query)}
    with application(environ):
        page = SpamPage()
        page.find('form:text').required = True
        page.find('form:password').required = True
        page.find('form:hidden').required = True
        assert_raises(Invalid, page.render)
    eq_(page.find('form').model_object, {'text': '',
                                         'password': '',
                                         'hidden': '',
                                         'area': 'area',
                                         'checkbox': False,
                                         'file': 'a.txt'})
    ok_(page.find('form').has_error())
    ok_(isinstance(page.find('form:text').error, ValidationError))
    ok_(isinstance(page.find('form:password').error, ValidationError))
    ok_(isinstance(page.find('form:hidden').error, ValidationError))


def test_form_component():
    # relative path
    f = form.Form('a')
    f.add(form.FormComponent('b1'))
    f.add(core.MarkupContainer('b2'))
    f.find('b2').add(form.FormComponent('c'))
    eq_(f.find('b1').relative_path(), 'b1')
    eq_(f.find('b2:c').relative_path(), 'b2:c')
    assert_raises(ComponentError, form.FormComponent('a').relative_path)

    # required error
    fc = form.FormComponent('a')
    fc.required = True
    fc.validate(None)
    ok_(isinstance(fc.error, ValidationError))
    fc.validate('')
    ok_(isinstance(fc.error, ValidationError))

    # conversion error
    with application():
        fc = form.FormComponent('a')
        fc.type = int
        fc.validate('a')
        ok_(isinstance(fc.error, ValidationError))

    # validation error
    with application():
        fc = form.FormComponent('a')
        fc.add(validator.StringValidator(max=4))
        fc.validate('.info')
        ok_(isinstance(fc.error, ValidationError))

    # no model
    with application():
        fc = form.FormComponent('a')
        fc.validate('a')
        eq_(fc.model, None)
        eq_(fc.model_object, None)


def test_choice():
    choice = form.Choice('a')
    s = choice._id_prefix_for(markup.Element(markup.DIV))
    ok_(s)
    ok_(not s[0].isdigit())


def test_radio_choice():
    class EggsPage(core.Page):
        def __init__(self):
            super(EggsPage, self).__init__()
            self.add(Form('form', model.CompoundModel({})))
            self.find('form').add(form.RadioChoice('radio', choices=choices))
            self.find('form:radio').model_object = choices[0]

    choices = [date(2012, 1, 1), date(2012, 1, 2), date(2012, 1, 3)]
    xhtml = ('<?xml version="1.0"?>\n'
             '{doctype}\n'
             '<html xmlns="{xhtml}">\n'
             '  <head>\n'
             '    <title>EggsPage</title>\n'
             '  </head>\n'
             '  <body>\n'
             '    <form action="/form" method="post">\n'
             '      <div class="ayame-hidden">'
             '<input name="{path}" type="hidden" value="form"/></div>\n'
             '      <fieldset>\n'
             '        <legend>radio</legend>\n'
             '        <div id="radio">\n'
             '          <input checked="checked" id="radio-0" name="radio" '
             'type="radio" value="0"/>'
             '<label for="radio-0">2012-01-01</label><br/>\n'
             '          <input id="radio-1" name="radio" type="radio" '
             'value="1"/><label for="radio-1">2012-01-02</label><br/>\n'
             '          <input id="radio-2" name="radio" type="radio" '
             'value="2"/><label for="radio-2">2012-01-03</label>\n'
             '        </div>\n'
             '      </fieldset>\n'
             '    </form>\n'
             '  </body>\n'
             '</html>\n').format(doctype=markup.XHTML1_STRICT,
                                 xhtml=markup.XHTML_NS,
                                 path=core.AYAME_PATH)
    xhtml = xhtml.encode('utf-8')

    # GET
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form'}
    with application(environ):
        page = EggsPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)
    eq_(page.find('form').model_object, {'radio': choices[0]})

    # POST
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="radio"\r\n'
            '\r\n'
            '2\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = EggsPage()
        assert_raises(Valid, page.render)
    eq_(page.find('form').model_object, {'radio': choices[2]})
    ok_(not page.find('form').has_error())

    # POST
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = EggsPage()
        assert_raises(Valid, page.render)
    eq_(page.find('form').model_object, {'radio': None})
    ok_(not page.find('form').has_error())

    # validation error
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="radio"\r\n'
            '\r\n'
            '-1\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = EggsPage()
        assert_raises(Invalid, page.render)
    eq_(page.find('form').model_object, {'radio': choices[0]})
    ok_(page.find('form').has_error())
    ok_(isinstance(page.find('form:radio').error, ValidationError))

    # validation error
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="radio"\r\n'
            '\r\n'
            '\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = EggsPage()
        assert_raises(Invalid, page.render)
    eq_(page.find('form').model_object, {'radio': choices[0]})
    ok_(page.find('form').has_error())
    ok_(isinstance(page.find('form:radio').error, ValidationError))


def test_checkbox_choice():
    class HamPage(core.Page):
        def __init__(self):
            super(HamPage, self).__init__()
            self.add(Form('form', model.CompoundModel({})))
            self.find('form').add(form.CheckBoxChoice('checkbox',
                                                      choices=choices))
            self.find('form:checkbox').model_object = [choices[1]]
            self.find('form:checkbox').multiple = True

    choices = [date(2012, 1, 1), date(2012, 1, 2), date(2012, 1, 3)]
    xhtml = ('<?xml version="1.0"?>\n'
             '{doctype}\n'
             '<html xmlns="{xhtml}">\n'
             '  <head>\n'
             '    <title>HamPage</title>\n'
             '  </head>\n'
             '  <body>\n'
             '    <form action="/form" method="post">\n'
             '      <div class="ayame-hidden">'
             '<input name="{path}" type="hidden" value="form"/></div>\n'
             '      <fieldset>\n'
             '        <legend>checkbox</legend>\n'
             '        <div id="checkbox">\n'
             '          <input id="checkbox-0" name="checkbox" '
             'type="checkbox" value="0"/>'
             '<label for="checkbox-0">2012-01-01</label><br/>\n'
             '          <input checked="checked" id="checkbox-1" '
             'name="checkbox" type="checkbox" value="1"/>'
             '<label for="checkbox-1">2012-01-02</label><br/>\n'
             '          <input id="checkbox-2" name="checkbox" '
             'type="checkbox" value="2"/>'
             '<label for="checkbox-2">2012-01-03</label>\n'
             '        </div>\n'
             '      </fieldset>\n'
             '    </form>\n'
             '  </body>\n'
             '</html>\n').format(doctype=markup.XHTML1_STRICT,
                                 xhtml=markup.XHTML_NS,
                                 path=core.AYAME_PATH)
    xhtml = xhtml.encode('utf-8')

    # GET
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form'}
    with application(environ):
        page = HamPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)
    eq_(page.find('form').model_object, {'checkbox': [choices[1]]})

    # POST
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="checkbox"\r\n'
            '\r\n'
            '0\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="checkbox"\r\n'
            '\r\n'
            '0\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="checkbox"\r\n'
            '\r\n'
            '1\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="checkbox"\r\n'
            '\r\n'
            '1\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="checkbox"\r\n'
            '\r\n'
            '2\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = HamPage()
        assert_raises(Valid, page.render)
    eq_(page.find('form').model_object, {'checkbox': choices})
    ok_(not page.find('form').has_error())

    # POST
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = HamPage()
        assert_raises(Valid, page.render)
    eq_(page.find('form').model_object, {'checkbox': []})
    ok_(not page.find('form').has_error())

    # validation error
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="checkbox"\r\n'
            '\r\n'
            '0\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="checkbox"\r\n'
            '\r\n'
            '\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="checkbox"\r\n'
            '\r\n'
            '1\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="checkbox"\r\n'
            '\r\n'
            '\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="checkbox"\r\n'
            '\r\n'
            '2\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = HamPage()
        assert_raises(Invalid, page.render)
    eq_(page.find('form').model_object, {'checkbox': [choices[1]]})
    ok_(page.find('form').has_error())
    ok_(isinstance(page.find('form:checkbox').error, ValidationError))

    # validation error
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="checkbox"\r\n'
            '\r\n'
            '-1\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="checkbox"\r\n'
            '\r\n'
            '0\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="checkbox"\r\n'
            '\r\n'
            '3\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = HamPage()
        assert_raises(Invalid, page.render)
    eq_(page.find('form').model_object, {'checkbox': [choices[1]]})
    ok_(page.find('form').has_error())
    ok_(isinstance(page.find('form:checkbox').error, ValidationError))

    # validation error
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="checkbox"\r\n'
            '\r\n'
            '\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = HamPage()
        assert_raises(Invalid, page.render)
    eq_(page.find('form').model_object, {'checkbox': [choices[1]]})
    ok_(page.find('form').has_error())
    ok_(isinstance(page.find('form:checkbox').error, ValidationError))

    # validation error
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = HamPage()
        page.find('form:checkbox').required = True
        assert_raises(Invalid, page.render)
    eq_(page.find('form').model_object, {'checkbox': [choices[1]]})
    ok_(page.find('form').has_error())
    ok_(isinstance(page.find('form:checkbox').error, ValidationError))


def test_select_choice():
    class ToastPage(core.Page):
        def __init__(self):
            super(ToastPage, self).__init__()
            self.add(Form('form', model.CompoundModel({})))
            self.find('form').add(form.SelectChoice('select',
                                                    choices=choices))
            self.find('form:select').model_object = [choices[1]]
            self.find('form:select').multiple = True

    choices = [date(2012, 1, 1), date(2012, 1, 2), date(2012, 1, 3)]
    xhtml = ('<?xml version="1.0"?>\n'
             '{doctype}\n'
             '<html xmlns="{xhtml}">\n'
             '  <head>\n'
             '    <title>ToastPage</title>\n'
             '  </head>\n'
             '  <body>\n'
             '    <form action="/form" method="post">\n'
             '      <div class="ayame-hidden">'
             '<input name="{path}" type="hidden" value="form"/></div>\n'
             '      <fieldset>\n'
             '        <legend>select</legend>\n'
             '        <select multiple="multiple" name="select">\n'
             '          <option value="0">2012-01-01</option>\n'
             '          <option selected="selected" value="1">2012-01-02'
             '</option>\n'
             '          <option value="2">2012-01-03</option>\n'
             '        </select>\n'
             '      </fieldset>\n'
             '    </form>\n'
             '  </body>\n'
             '</html>\n').format(doctype=markup.XHTML1_STRICT,
                                 xhtml=markup.XHTML_NS,
                                 path=core.AYAME_PATH)
    xhtml = xhtml.encode('utf-8')

    # GET
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form'}
    with application(environ):
        page = ToastPage()
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)
    eq_(page.find('form').model_object, {'select': [choices[1]]})

    # POST
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="select"\r\n'
            '\r\n'
            '0\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="select"\r\n'
            '\r\n'
            '0\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="select"\r\n'
            '\r\n'
            '1\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="select"\r\n'
            '\r\n'
            '1\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="select"\r\n'
            '\r\n'
            '2\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = ToastPage()
        assert_raises(Valid, page.render)
    eq_(page.find('form').model_object, {'select': choices})
    ok_(not page.find('form').has_error())

    # POST
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = ToastPage()
        assert_raises(Valid, page.render)
    eq_(page.find('form').model_object, {'select': []})
    ok_(not page.find('form').has_error())

    # GET (single)
    xhtml = xhtml.replace(b' multiple="multiple"', b'')
    environ = {'wsgi.input': io.BytesIO(),
               'REQUEST_METHOD': 'GET',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form'}
    with application(environ):
        page = ToastPage()
        select = page.find('form:select')
        select.model_object = select.model_object[0]
        select.multiple = False
        status, headers, content = page.render()
    eq_(status, http.OK.status)
    eq_(headers, [('Content-Type', 'text/html; charset=UTF-8'),
                  ('Content-Length', str(len(xhtml)))])
    eq_(content, xhtml)
    eq_(page.find('form').model_object, {'select': choices[1]})

    # POST (single)
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = ToastPage()
        select = page.find('form:select')
        select.model_object = select.model_object[0]
        select.multiple = False
        assert_raises(Valid, page.render)
    eq_(page.find('form').model_object, {'select': None})
    ok_(not page.find('form').has_error())

    # validation error
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="select"\r\n'
            '\r\n'
            '0\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="select"\r\n'
            '\r\n'
            '\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="select"\r\n'
            '\r\n'
            '1\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="select"\r\n'
            '\r\n'
            '\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="select"\r\n'
            '\r\n'
            '2\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = ToastPage()
        assert_raises(Invalid, page.render)
    eq_(page.find('form').model_object, {'select': [choices[1]]})
    ok_(page.find('form').has_error())
    ok_(isinstance(page.find('form:select').error, ValidationError))

    # validation error
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="select"\r\n'
            '\r\n'
            '-1\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="select"\r\n'
            '\r\n'
            '0\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="select"\r\n'
            '\r\n'
            '3\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = ToastPage()
        assert_raises(Invalid, page.render)
    eq_(page.find('form').model_object, {'select': [choices[1]]})
    ok_(page.find('form').has_error())
    ok_(isinstance(page.find('form:select').error, ValidationError))

    # validation error
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form\r\n'
            'Content-Disposition: form-data; name="select"\r\n'
            '\r\n'
            '\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = ToastPage()
        assert_raises(Invalid, page.render)
    eq_(page.find('form').model_object, {'select': [choices[1]]})
    ok_(page.find('form').has_error())
    ok_(isinstance(page.find('form:select').error, ValidationError))

    # validation error
    data = ('--ayame.form\r\n'
            'Content-Disposition: form-data; name="{}"\r\n'
            '\r\n'
            'form\r\n'
            '--ayame.form--\r\n').format(core.AYAME_PATH)
    data = data.encode('utf-8')
    environ = {'wsgi.input': io.BytesIO(data),
               'REQUEST_METHOD': 'POST',
               'SCRIPT_NAME': '',
               'PATH_INFO': '/form',
               'CONTENT_TYPE': 'multipart/form-data; boundary=ayame.form',
               'CONTENT_LENGTH': str(len(data))}
    with application(environ):
        page = ToastPage()
        page.find('form:select').required = True
        assert_raises(Invalid, page.render)
    eq_(page.find('form').model_object, {'select': [choices[1]]})
    ok_(page.find('form').has_error())
    ok_(isinstance(page.find('form:select').error, ValidationError))


def test_invalid_markup():
    input = markup.Element(form._INPUT)
    input.attrib[form._TYPE] = 'text'

    button = form.Button('a')
    assert_raises(RenderingError, button.render, input)
    assert_raises(RenderingError, button.render, markup.Element(markup.DIV))

    upload = form.FileUploadField('a')
    assert_raises(RenderingError, upload.render, markup.Element(markup.DIV))

    text = form.TextField('a')
    assert_raises(RenderingError, text.render, markup.Element(markup.DIV))

    area = form.TextArea('a')
    assert_raises(RenderingError, area.render, markup.Element(markup.DIV))

    checkbox = form.CheckBox('a')
    assert_raises(RenderingError, checkbox.render, input)
    assert_raises(RenderingError, checkbox.render, markup.Element(markup.DIV))

    select = form.SelectChoice('a')
    assert_raises(RenderingError, select.render, markup.Element(markup.DIV))
