#
# ayame.http
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

import cgi
import re

from . import _compat as five
from .exception import AyameError


__all__ = ['parse_accept', 'parse_form_data', 'HTTPStatus', 'HTTPSuccessful',
           'OK', 'Created', 'Accepted', 'NoContent', 'HTTPRedirection',
           'MovedPermanently', 'Found', 'SeeOther', 'NotModified', 'HTTPError',
           'HTTPClientError', 'BadRequest', 'Unauthrized', 'Forbidden',
           'NotFound', 'MethodNotAllowed', 'RequestTimeout', 'HTTPServerError',
           'InternalServerError', 'NotImplemented']

_accept_re = re.compile(r"""
    (?P<param>[^\s,;]+)
    (?:
        [^,;]* ; \s* q= (?P<qvalue>\d+ (?:\. \d+)?)
    )?
""", re.VERBOSE)


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
    for field in fs.list:
        if (isinstance(field, cgi.FieldStorage) and
            field.done == -1):
            raise RequestTimeout()
        if five.PY2:
            field.name = unicode(field.name, 'utf-8', 'replace')
            if field.filename:
                field.filename = unicode(field.filename, 'utf-8', 'replace')
                value = field
            else:
                value = unicode(field.value, 'utf-8', 'replace')
        else:
            value = field if field.filename else field.value
        if field.name in form_data:
            form_data[field.name].append(value)
        else:
            form_data[field.name] = [value]
    return form_data


class _HTTPStatusMetaclass(type):

    def __new__(cls, name, bases, ns):
        if 'code' not in ns:
            ns['code'] = 0
        if 'reason' not in ns:
            if ns['code']:
                prev = ''
                buf = []
                for c in name:
                    if (c.isupper() and
                        prev.islower()):
                        buf.append(' ')
                    buf.append(c)
                    prev = c
                ns['reason'] = ''.join(buf)
            else:
                ns['reason'] = ''
        if 'status' not in ns:
            ns['status'] = '{code} {reason}'.format(**ns) if ns['code'] else ''
        return type.__new__(cls, name, bases, ns)


class HTTPStatus(five.with_metaclass(_HTTPStatusMetaclass, AyameError)):

    def __init__(self, description='', headers=None):
        super(HTTPStatus, self).__init__(self.status)
        self.description = description
        self.headers = list(headers) if headers is not None else []


class HTTPSuccessful(HTTPStatus):
    pass


class OK(HTTPSuccessful):

    code = 200


class Created(HTTPSuccessful):

    code = 201


class Accepted(HTTPSuccessful):

    code = 202


class NoContent(HTTPSuccessful):

    code = 204


class HTTPRedirection(HTTPStatus):
    pass


class _HTTPMove(HTTPRedirection):

    _template = ('The requested resource has moved to '
                 '<a href="{location}">{location}</a>.')

    def __init__(self, location, headers=None):
        if headers is None:
            headers = []
        super(_HTTPMove, self).__init__(self._template.format(location=five.html_escape(location)),
                                        headers + [('Location', location)])


class MovedPermanently(_HTTPMove):

    code = 301


class Found(_HTTPMove):

    code = 302
    _template = ('The requested resource was found at '
                 '<a href="{location}">{location}</a>.')


class SeeOther(_HTTPMove):

    code = 303


class NotModified(HTTPRedirection):

    code = 304


class HTTPError(HTTPStatus):
    pass


class HTTPClientError(HTTPError):
    pass


class BadRequest(HTTPClientError):

    code = 400


class Unauthrized(HTTPClientError):

    code = 401

    def __init__(self, headers=None):
        super(Unauthrized, self).__init__('This server could not verify that you are '
                                          'authorized to access the requested resource.',
                                          headers)


class Forbidden(HTTPClientError):

    code = 403

    def __init__(self, uri, headers=None):
        super(Forbidden, self).__init__('You do not have permission to access <code>{uri}</code> on '
                                        'this server.'.format(uri=uri),
                                        headers)


class NotFound(HTTPClientError):

    code = 404

    def __init__(self, uri, headers=None):
        super(NotFound, self).__init__('The requested URI <code>{uri}</code> was not found on '
                                       'this server'.format(uri=uri),
                                       headers)


class MethodNotAllowed(HTTPClientError):

    code = 405

    def __init__(self, method, uri, allow, headers=None):
        if headers is None:
            headers = []
        super(MethodNotAllowed, self).__init__('The requested method <code>{method}</code> is not allowed for '
                                               'the URI <code>{uri}</code>.'.format(method=method, uri=uri),
                                               headers + [('Allow', ', '.join(allow))])


class RequestTimeout(HTTPClientError):

    code = 408

    def __init__(self, headers=None):
        super(RequestTimeout, self).__init__('This server timed out while waiting for '
                                             'the request from the client.',
                                             headers)


class HTTPServerError(HTTPError):
    pass


class InternalServerError(HTTPServerError):

    code = 500


class NotImplemented(HTTPServerError):

    code = 501

    def __init__(self, method, uri, headers=None):
        super(NotImplemented, self).__init__('The requested method <code>{method}</code> is not implemented for '
                                             'the URI <code>{uri}</code>'.format(method=method, uri=uri),
                                             headers)
