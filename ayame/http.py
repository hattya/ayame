#
# ayame.http
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import cgi
import html
import re

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
    if ct not in ('application/x-www-form-urlencoded', 'multipart/form-data'):
        return {}

    # isolate QUERY_STRING
    fs_environ = environ.copy()
    fs_environ['QUERY_STRING'] = ''
    fs = cgi.FieldStorage(fp=environ['wsgi.input'],
                          environ=fs_environ,
                          keep_blank_values=True)

    form_data = {}
    for field in fs.list:
        if (isinstance(field, cgi.FieldStorage)
            and field.done == -1):
            raise RequestTimeout()
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
                    if (c.isupper()
                        and prev.islower()):
                        buf.append(' ')
                    buf.append(c)
                    prev = c
                ns['reason'] = ''.join(buf)
            else:
                ns['reason'] = ''
        if 'status' not in ns:
            ns['status'] = '{code} {reason}'.format(**ns) if ns['code'] else ''
        return type.__new__(cls, name, bases, ns)


class HTTPStatus(AyameError, metaclass=_HTTPStatusMetaclass):

    def __init__(self, description='', headers=None):
        super().__init__(self.status)
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
        super().__init__(self._template.format(location=html.escape(location)),
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
        super().__init__('This server could not verify that you are '
                         'authorized to access the requested resource.',
                         headers)


class Forbidden(HTTPClientError):

    code = 403

    def __init__(self, uri, headers=None):
        super().__init__(f'You do not have permission to access <code>{uri}</code> on this server.',
                         headers)


class NotFound(HTTPClientError):

    code = 404

    def __init__(self, uri, headers=None):
        super().__init__(f'The requested URI <code>{uri}</code> was not found on this server',
                         headers)


class MethodNotAllowed(HTTPClientError):

    code = 405

    def __init__(self, method, uri, allow, headers=None):
        if headers is None:
            headers = []
        super().__init__(f'The requested method <code>{method}</code> is not allowed for the URI <code>{uri}</code>.',
                         headers + [('Allow', ', '.join(allow))])


class RequestTimeout(HTTPClientError):

    code = 408

    def __init__(self, headers=None):
        super().__init__('This server timed out while waiting for the request from the client.',
                         headers)


class HTTPServerError(HTTPError):
    pass


class InternalServerError(HTTPServerError):

    code = 500


class NotImplemented(HTTPServerError):

    code = 501

    def __init__(self, method, uri, headers=None):
        super().__init__(f'The requested method <code>{method}</code> is not implemented for the URI <code>{uri}</code>',
                         headers)
