#
# ayame.model
#
#   Copyright (c) 2011-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import abc


__all__ = ['Model', 'InheritableModel', 'WrapModel', 'CompoundModel']


class Model:

    def __init__(self, object):
        self.__object = object

    def object():
        def fget(self):
            return self.__object.object if isinstance(self.__object, Model) else self.__object

        def fset(self, object):
            self.__object = object

        return locals()

    object = property(**object())


class InheritableModel(Model, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def wrap(self, component):
        pass


class WrapModel(Model, metaclass=abc.ABCMeta):

    def __init__(self, model):
        super().__init__(None)
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
                super().__init__(model)
                self._component = component

            def object():
                def fget(self):
                    o = self.wrapped_model.object
                    name = self._component.id
                    # instance variable
                    try:
                        return getattr(o, name)
                    except AttributeError:
                        pass
                    # getter method
                    try:
                        getter = getattr(o, 'get_' + name)
                        if callable(getter):
                            return getter()
                    except AttributeError:
                        pass
                    # __getitem__
                    try:
                        return o.__getitem__(name)
                    except (AttributeError, LookupError):
                        pass

                def fset(self, object):
                    o = self.wrapped_model.object
                    name = self._component.id
                    # instance variable
                    try:
                        getattr(o, name)
                    except AttributeError:
                        pass
                    else:
                        return setattr(o, name, object)
                    # setter method
                    try:
                        setter = getattr(o, 'set_' + name)
                        if callable(setter):
                            return setter(object)
                    except AttributeError:
                        pass
                    # __setitem__
                    try:
                        return o.__setitem__(name, object)
                    except AttributeError:
                        pass

                    raise AttributeError(name)

                return locals()

            object = property(**object())

        return CompoundWrapModel(self)
