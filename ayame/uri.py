#
# ayame.uri
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

import urllib
import urlparse

from ayame import _compat as five
import ayame.util


__all__ = ['parse_qs', 'quote', 'quote_plus', 'application_uri', 'request_uri',
           'request_path', 'is_relative_uri', 'relative_uri']

_safe = "/-._~!$&'()*+,;=:@"

if five.PY2:
    _decode = lambda s: unicode(s, 'utf-8', 'replace')
else:
    _decode = None


def parse_qs(environ):
    qs = environ.get('QUERY_STRING')
    if not qs:
        return {}

    qs = urlparse.parse_qs(qs, keep_blank_values=True)
    if _decode is not None:
        return {_decode(k): [_decode(s) for s in v] for k, v in qs.iteritems()}
    return qs


def quote(s, safe=_safe, encoding='utf-8', errors='strict'):
    return urllib.quote(ayame.util.to_bytes(s, encoding, errors),
                        ayame.util.to_bytes(safe, 'ascii', 'ignore'))


def quote_plus(s, safe=_safe, encoding='utf-8', errors='strict'):
    return urllib.quote_plus(ayame.util.to_bytes(s, encoding, errors),
                             ayame.util.to_bytes(safe, 'ascii', 'ignore'))


def application_uri(environ):
    scheme = environ['wsgi.url_scheme']
    uri = [scheme, '://']
    # HTTP_HOST or SERVER_NAME + SERVER_PORT
    host = environ.get('HTTP_HOST')
    if host:
        port = ''
        if ':' in host:
            host, port = host.split(':', 1)
    else:
        host = environ['SERVER_NAME']
        port = environ['SERVER_PORT']
    uri.append(host)
    if port:
        if ((scheme == 'http' and
             port != '80') or
            (scheme == 'https' and
             port != '443')):
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
    if (query and
        environ.get('QUERY_STRING')):
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
    elif (uri is None or
          uri[0] in ('/', '#')):
        return False
    return not urlparse.urlsplit(uri).scheme


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
