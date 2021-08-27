#
# ayame.validator
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import abc
import re

from . import _compat as five
from . import core, markup
from .exception import ValidationError


__all__ = ['Validator', 'RegexValidator', 'EmailValidator', 'URLValidator',
           'RangeValidator', 'StringValidator']

# from RFC 1035 and RFC 2822
_atext = "[A-Z0-9!#$%&'*+\-/=?^_`{|}~]"
_label = '(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)'
_email = r"""
    \A
    # local part
    {atext}+ (?:\. {atext}+)*
    @
    # domain
    {label} (?:\. {label})*
    \Z
""".format(atext=_atext,
           label=_label)

# from RFC 3986
_pct_encoded = '(?:%[0-9A-F][0-9A-F])'
_unreserved = '[A-Z0-9\-._~]'
_sub_delims = "[!$&'()*+,;=]"
_pchar = '(?:{}|{}|{}|[:@])'.format(_unreserved, _pct_encoded, _sub_delims)
_ipv4 = '(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
_url = r"""
    \A
    # scheme
    (?:https? | ftp) : //
    # authority
    (?:
        # userinfo
        (?:{unreserved} | {pct_encoded} | {sub_delims})+
        (?:
            :
            (?:{unreserved} | {pct_encoded} | {sub_delims})+
        )?
        @
    )?
    (?:
        # host
        (?:{label} (?:\. {label})*) |
        {ipv4}
    )
    (?:
        # port
        :
        \d+
    )?
    # path
    (?:/ {pchar}*)*
    # query
    (?:
        \?
        (?:{pchar} | [/?])*
    )?
    # fragment
    (?:
        \#
        (?:{pchar} | [/?])*
    )?
    \Z
""".format(unreserved=_unreserved,
           pct_encoded=_pct_encoded,
           sub_delims=_sub_delims,
           label=_label,
           ipv4=_ipv4,
           pchar=_pchar)

# HTML elements
_INPUT = markup.QName(markup.XHTML_NS, 'input')
# HTML attributes
_TYPE = markup.QName(markup.XHTML_NS, 'type')
_MAXLENGTH = markup.QName(markup.XHTML_NS, 'maxlength')


class Validator(five.with_metaclass(abc.ABCMeta, core.Behavior)):

    @abc.abstractmethod
    def validate(self, object):
        pass

    def error(self, **kwargs):
        return ValidationError(validator=self, **kwargs)


class RegexValidator(Validator):

    def __init__(self, pattern, flags=0):
        super(RegexValidator, self).__init__()
        self.regex = re.compile(pattern, flags)

    def validate(self, object):
        if not (isinstance(object, five.string_type) and
                self.regex.match(object)):
            e = self.error()
            e.vars['pattern'] = self.regex.pattern
            raise e


class EmailValidator(RegexValidator):

    def __init__(self):
        super(EmailValidator, self).__init__(_email, re.IGNORECASE | re.VERBOSE)


class URLValidator(RegexValidator):

    def __init__(self):
        super(URLValidator, self).__init__(_url, re.IGNORECASE | re.VERBOSE)


class RangeValidator(Validator):

    def __init__(self, min=None, max=None):
        super(RangeValidator, self).__init__()
        self.min = min
        self.max = max

    def validate(self, object):
        if ((self.min is not None and
             not isinstance(object, self.typeof(self.min))) or
            (self.max is not None and
             not isinstance(object, self.typeof(self.max)))):
            raise self.error(variation='type')
        elif ((self.min is not None and
               object < self.min) or
              (self.max is not None and
               self.max < object)):
            vars = {}
            if self.max is None:
                mode = 'minimum'
                vars['min'] = self.min
            elif self.min is None:
                mode = 'maximum'
                vars['max'] = self.max
            elif self.min == self.max:
                mode = 'exact'
                vars['exact'] = self.max
            else:
                mode = 'range'
                vars.update(min=self.min,
                            max=self.max)
            e = self.error(variation=mode)
            e.vars.update(vars)
            raise e

    if five.PY2:
        def typeof(self, object):
            if isinstance(object, five.integer_types):
                return five.integer_types
            elif isinstance(object, five.string_type):
                return five.string_type
            return object.__class__
    else:
        def typeof(self, object):
            return object.__class__


class StringValidator(RangeValidator):

    def validate(self, object):
        if not isinstance(object, five.string_type):
            raise self.error(variation='type')
        super(StringValidator, self).validate(len(object))

    def on_component(self, component, element):
        if (self.max is not None and
            self.is_text_input(element)):
            element.attrib[_MAXLENGTH] = five.str(self.max)

    def is_text_input(self, element):
        return (element.qname == _INPUT and
                element.attrib[_TYPE] in ('text', 'password'))
