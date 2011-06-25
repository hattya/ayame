#
# ayame.uri
#
#   Copyright (c) 2011 Akinori Hattori <hattya@gmail.com>
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

from ayame import util


__all__ = ['quote', 'quote_plus', 'application_uri', 'request_uri',
           'request_path']

_safe = "/-._~!$&'()*+,;=:@"

def quote(s, safe=_safe, encoding='utf-8', errors='strict'):
    return urllib.quote(util.to_bytes(s, encoding, errors),
                        util.to_bytes(safe, 'ascii', 'ignore'))

def quote_plus(s, safe='', encoding='utf-8', errors='strict'):
    return urllib.quote_plus(util.to_bytes(s, encoding, errors),
                             util.to_bytes(safe, 'ascii', 'ignore'))

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
        if ((scheme == 'http' and port != '80') or
            (scheme == 'https' and port != '443')):
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
    if query and environ.get('QUERY_STRING'):
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
