#
# ayame.model
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

import abc


__all__ = ['Model', 'InheritableModel', 'WrapModel', 'CompoundModel']

class Model(object):

    def __init__(self, object):
        self.__object = object

    def object():
        def fget(self):
            if isinstance(self.__object, Model):
                return self.__object.object
            return self.__object

        def fset(self, object):
            self.__object = object

        return locals()

    object = property(**object())

class InheritableModel(Model):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def wrap(self, component):
        pass

class WrapModel(Model):

    __metaclass__ = abc.ABCMeta

    def __init__(self, model):
        super(WrapModel, self).__init__(None)
        self.__wrapped_model = model

    @property
    def wrapped_model(self):
        return self.__wrapped_model

    @abc.abstractproperty
    def object(self):
        pass

class CompoundModel(InheritableModel):

    def wrap(self, component):
        class CompoundWrapModel(WrapModel):

            def __init__(self, model):
                super(CompoundWrapModel, self).__init__(model)
                self._component = component

            def object():
                def fget(self):
                    wrapped_object = self.wrapped_model.object
                    name = self._component.id
                    # instance variable
                    try:
                        return getattr(wrapped_object, name)
                    except AttributeError:
                        pass
                    # getter method
                    try:
                        getter = getattr(wrapped_object, 'get_' + name)
                        if callable(getter):
                            return getter()
                    except AttributeError:
                        pass
                    # __getitem__
                    try:
                        return wrapped_object.__getitem__(name)
                    except (AttributeError, LookupError):
                        pass

                def fset(self, object):
                    wrapped_object = self.wrapped_model.object
                    name = self._component.id
                    # instance variable
                    try:
                        getattr(wrapped_object, name)
                    except AttributeError:
                        pass
                    else:
                        return setattr(wrapped_object, name, object)
                    # setter method
                    try:
                        setter = getattr(wrapped_object, 'set_' + name)
                        if callable(setter):
                            return setter(object)
                    except AttributeError:
                        pass
                    # __setitem__
                    try:
                        return wrapped_object.__setitem__(name, object)
                    except AttributeError:
                        pass

                    raise AttributeError(name)

                return locals()

            object = property(**object())

        return CompoundWrapModel(self)
