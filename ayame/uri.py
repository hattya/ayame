#
# ayame.uri
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import urllib.parse

from . import util


__all__ = ['parse_qs', 'quote', 'quote_plus', 'application_uri', 'request_uri',
           'request_path', 'is_relative_uri', 'relative_uri']

_safe = "/-._~!$&'()*+,;=:@"


def parse_qs(environ):
    qs = environ.get('QUERY_STRING')
    return urllib.parse.parse_qs(qs, keep_blank_values=True) if qs else {}


def quote(s, safe=_safe, encoding='utf-8', errors='strict'):
    return urllib.parse.quote(util.to_bytes(s, encoding, errors),
                              util.to_bytes(safe, 'ascii', 'ignore'))


def quote_plus(s, safe=_safe, encoding='utf-8', errors='strict'):
    return urllib.parse.quote_plus(util.to_bytes(s, encoding, errors),
                                   util.to_bytes(safe, 'ascii', 'ignore'))


def application_uri(environ):
    scheme = environ['wsgi.url_scheme']
    uri = [scheme, '://']
    # HTTP_HOST or SERVER_NAME + SERVER_PORT
    host = environ.get('HTTP_HOST')
    if host:
        if ':' in host:
            host, port = host.split(':', 1)
        else:
            port = ''
    else:
        host = environ['SERVER_NAME']
        port = environ['SERVER_PORT']
    uri.append(host)
    if port:
        if ((scheme == 'http'
             and port != '80')
            or (scheme == 'https'
                and port != '443')):
            uri.append(':')
            uri.append(port)
    # SCRIPT_NAME
    script_name = environ.get('SCRIPT_NAME')
    uri.append(quote(script_name) if script_name else '/')
    return ''.join(uri)


def request_uri(environ, query=False):
    uri = [application_uri(environ)]
    # PATH_INFO
    path_info = environ.get('PATH_INFO')
    if path_info:
        if not environ.get('SCRIPT_NAME'):
            path_info = path_info[1:]
        uri.append(quote(path_info))
    # QUERY_STRING
    if (query
        and environ.get('QUERY_STRING')):
        uri.append('?')
        uri.append(environ['QUERY_STRING'])
    return ''.join(uri)


def request_path(environ):
    path = []
    # SCRIPT_NAME
    script_name = environ.get('SCRIPT_NAME')
    path.append(quote(script_name) if script_name else '/')
    # PATH_INFO
    path_info = environ.get('PATH_INFO')
    if path_info:
        if not script_name:
            path_info = path_info[1:]
        path.append(quote(path_info))
    return ''.join(path)


def is_relative_uri(uri):
    if uri == '':
        return True
    elif (uri is None
          or uri[0] in ('/', '#')):
        return False
    return not urllib.parse.urlsplit(uri).scheme


def relative_uri(environ, uri):
    if not is_relative_uri(uri):
        return uri
    # PATH_INFO
    path_info = environ.get('PATH_INFO')
    if not path_info:
        return uri
    # count segments
    up = 0 if path_info[-1] == '/' else -1
    for x in path_info.split('/'):
        if x:
            up += 1
    relative_uri = ['..'] * up
    relative_uri.append(uri)
    return '/'.join(relative_uri)
