#
# ayame.http
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

import cgi
import re
import sys

from ayame.exception import AyameError


__all__ = ['parse_accept', 'parse_form_data', 'HTTPStatus', 'HTTPSuccessful',
           'OK', 'Created', 'Accepted', 'NoContent', 'HTTPError',
           'Redirection', 'MovedPermanently', 'Found', 'SeeOther',
           'NotModified', 'ClientError', 'BadRequest', 'Unauthrized',
           'Forbidden', 'NotFound', 'MethodNotAllowed', 'RequestTimeout'
           'ServerError', 'InternalServerError', 'NotImplemented']

_HTML = ('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" '
         '"http://www.w3.org/TR/html4/strict.dtd">\n'
         '<html>\n'
         '  <head>\n'
         '    <title>{status}</title>\n'
         '  <head>\n'
         '  <body>\n'
         '    <h1>{reason}</h1>\n'
         '    <p>{description}</p>\n'
         '  </body>\n'
         '</html>\n')

_accept_re = re.compile(r"""
    (?P<param>[^\s,;]+)
    (?:
        [^,;]*; \s* q= (?P<qvalue>\d+ (?:\. \d+)?)
    )?
""", re.VERBOSE)

if sys.hexversion < 0x03000000:
    _decode = lambda s: unicode(s, 'utf-8', 'replace')
else:
    _decode = None


def parse_accept(value):
    if not value:
        return ()

    qlist = []
    for i, m in enumerate(_accept_re.finditer(value)):
        v, q = m.groups()
        q = min(float(q), 1.0) if q else 1.0
        qlist.append((-q, i, v))
    return tuple((v, -q) for q, i, v in sorted(qlist))


def parse_form_data(environ):
    ct = cgi.parse_header(environ.get('CONTENT_TYPE', ''))[0]
    if ct not in ('application/x-www-form-urlencoded',
                  'multipart/form-data'):
        return {}

    # isolate QUERY_STRING
    fs_environ = environ.copy()
    fs_environ['QUERY_STRING'] = ''
    fs = cgi.FieldStorage(fp=environ['wsgi.input'],
                          environ=fs_environ,
                          keep_blank_values=True)

    form_data = {}
    if fs.list:
        for field in fs.list:
            if (isinstance(field, cgi.FieldStorage) and
                field.done == -1):
                raise RequestTimeout()
            if _decode is not None:
                field.name = _decode(field.name)
            if field.filename:
                if _decode is not None:
                    field.filename = _decode(field.filename)
                value = field
            else:
                if _decode is not None:
                    value = _decode(field.value)
                else:
                    value = field.value
            if field.name in form_data:
                form_data[field.name].append(value)
            else:
                form_data[field.name] = [value]
    return form_data


class _HTTPStatusMetaclass(type):

    def __new__(cls, name, bases, dict):
        if not dict.get('code'):
            dict['code'] = 0
        if not dict.get('reason'):
            if dict['code']:
                prev = None
                buf = []
                for ch in name:
                    if (prev and
                        buf and
                        (prev.islower() and
                         ch.isupper())):
                        buf.append(' ')
                    buf.append(ch)
                    prev = ch
                dict['reason'] = ''.join(buf)
            else:
                dict['reason'] = ''
        if not dict.get('status'):
            if dict['code']:
                dict['status'] = '{code} {reason}'.format(**dict)
            else:
                dict['status'] = ''
        return type.__new__(cls, name, bases, dict)


class HTTPStatus(AyameError):

    __metaclass__ = _HTTPStatusMetaclass

    def __init__(self, description='', headers=None):
        super(HTTPStatus, self).__init__(self.status)
        self.description = description
        self.headers = list(headers) if headers else []

    def html(self):
        return _HTML.format(reason=self.reason,
                            status=self.status,
                            description=self.description)


def _location_init(superclass, s):
    def __init__(self, location):
        superclass.__init__(self,
                            s.format(location=cgi.escape(location, True)),
                            headers=[('Location', location)])
    return __init__


def _uri_init(superclass, s):
    def __init__(self, uri):
        superclass.__init__(self, s.format(uri=uri))
    return __init__


def _method_init(superclass, s):
    def __init__(self, method, uri, allow=None):
        headers = []
        if allow:
            if hasattr(allow, '__iter__'):
                allow = ','.join(allow)
            headers.append(('Allow', allow))
        superclass.__init__(self, s.format(method=method, uri=uri),
                            headers=headers)
    return __init__


class HTTPSuccessful(HTTPStatus):

    def html(self):
        return ''


class OK(HTTPSuccessful):

    code = 200


class Created(HTTPSuccessful):

    code = 201


class Accepted(HTTPSuccessful):

    code = 202


class NoContent(HTTPSuccessful):

    code = 204


class HTTPError(HTTPStatus):
    pass


class Redirection(HTTPError):
    pass


class MovedPermanently(Redirection):

    code = 301

    __init__ = _location_init(
        Redirection, 'The document has moved <a href="{location}">here</a>.')


class Found(Redirection):

    code = 302

    __init__ = _location_init(
        Redirection, 'The document has moved <a href="{location}">here</a>.')


class SeeOther(Redirection):

    code = 303

    __init__ = _location_init(
        Redirection,
        'The answer to your request is located <a href="{location}">here</a>.')


class NotModified(Redirection):

    code = 304

    def html(self):
        return ''


class ClientError(HTTPError):
    pass


class BadRequest(ClientError):

    code = 400


class Unauthrized(ClientError):

    code = 401

    def __init__(self, headers=None):
        super(Unauthrized, self).__init__(
            'This server could not verify that you are authorized to access '
            'the document requested. Either you supplied the wrong '
            'credentials (e.g. bad password), or your browser does not '
            'understand how to supply the credentials required.',
            headers)


class Forbidden(ClientError):

    code = 403

    __init__ = _uri_init(
        ClientError,
        'You do not have permission to access {uri} on this server.')


class NotFound(ClientError):

    code = 404

    __init__ = _uri_init(
        ClientError, 'The requested URL {uri} was not found on this server.')


class MethodNotAllowed(ClientError):

    code = 405

    __init__ = _method_init(
        ClientError,
        'The requested method {method} is not allowd for the URL {uri}.')


class RequestTimeout(ClientError):

    code = 408

    def __init__(self, headers=None):
        super(RequestTimeout, self).__init__(
            'This server timed out while waiting for the request from the '
            'client.',
            headers)


class ServerError(HTTPError):
    pass


class InternalServerError(ServerError):

    code = 500


class NotImplemented(ServerError):

    code = 501

    __init__ = _method_init(ServerError,
                            '{method} to {uri} is not implemented.')
