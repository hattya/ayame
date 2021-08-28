#
# ayame._compat
#
#   Copyright (c) 2014-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import sys


__all__ = ['PY2', 'UTC', 'class_types', 'integer_types', 'string_type', 'int',
           'str', 'range', 'items', 'reraise', 'html_escape', 'urlencode',
           'urlparse_qs', 'urlquote', 'urlquote_plus', 'urlsplit',
           'with_metaclass', 'HTMLParser']

PY2 = sys.version_info[0] == 2
if PY2:
    from HTMLParser import HTMLParser as _HTMLParser
    import cgi
    import datetime
    import types
    from urllib import quote as urlquote
    from urllib import quote_plus as urlquote_plus
    from urllib import urlencode
    import urlparse
    from urlparse import urlsplit

    class_types = (type, types.ClassType)
    integer_types = (long, int)
    string_type = basestring

    int = long
    str = unicode
    range = xrange

    def items(d):
        return d.viewitems()

    exec('def reraise(t, v, tb=None): raise t, v, tb')

    def html_escape(s, quote=True):
        s = cgi.escape(s, quote)
        return s.replace("'", '&#x27;') if quote else s

    class UTC(datetime.tzinfo):

        __slots__ = ()

        _ZERO = datetime.timedelta(0)
        _inst = None

        def __repr__(self):
            return '<UTC>'

        def __str__(self):
            return 'UTC'

        def __new__(cls):
            if cls._inst is None:
                cls._inst = super(UTC, cls).__new__(cls)
            return cls._inst

        def utcoffset(self, dt):
            return self._ZERO

        def tzname(self, dt):
            return self.__str__()

        def dst(self, dt):
            return self._ZERO

    UTC = UTC()

    def urlparse_qs(qs, keep_blank_values=False, strict_parsing=False,
                    encoding='utf-8', errors='replace'):
        qs = urlparse.parse_qs(qs, keep_blank_values)
        return {unicode(k, encoding, errors): [unicode(s, encoding, errors) for s in v]
                for k, v in qs.iteritems()}

    class HTMLParser(_HTMLParser, object):

        def __init__(self, strict=False, convert_charrefs=False):
            _HTMLParser.__init__(self)
else:
    import datetime
    from html import escape as html_escape
    from html.parser import HTMLParser as HTMLParser
    from urllib.parse import urlencode, urlsplit
    from urllib.parse import parse_qs as urlparse_qs
    from urllib.parse import quote as urlquote
    from urllib.parse import quote_plus as urlquote_plus

    class_types = (type,)
    integer_types = (int,)
    string_type = str

    int = int
    str = str
    range = range

    def items(d):
        return d.items()

    def reraise(t, v, tb=None):
        if v.__traceback__ is not tb:
            raise v.with_traceback(tb)
        raise v

    UTC = datetime.timezone.utc


def with_metaclass(meta, *bases):
    #
    # call order:
    #
    # 1) metaclass('metaclass', None, {})
    # 2) type.__new__(cls, name, (), ns)
    #    => metaclass.__new__(..., bases=None, ...)
    #    => metaclass.__init__ = type.__init__(..., bases=None, ...)
    # 3) meta(name, bases, ns)
    #    => metaclass.__new__(..., bases=(metaclass,), ...)
    #    => meta.__new__(..., bases=bases, ...)
    #    => meta.__init__(..., bases=bases, ...)
    #    => meta.__call__()
    #
    class metaclass(meta):

        def __new__(cls, name, bases_, ns):
            if bases_ is None:
                return type.__new__(cls, name, (), ns)
            return meta(name, bases, ns)

        __init__ = type.__init__

    return metaclass('metaclass', None, {})
