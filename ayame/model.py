#
# ayame.model
#
#   Copyright (c) 2011-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import abc
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from . import core


__all__ = ['Model', 'InheritableModel', 'WrapModel', 'CompoundModel']


class Model:

    def __init__(self, object: Any) -> None:
        self.__object = object

    @property
    def object(self) -> Any:
        return self.__object.object if isinstance(self.__object, Model) else self.__object

    @object.setter
    def object(self, object: Any) -> None:
        self.__object = object


class InheritableModel(Model, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def wrap(self, component: core.Component) -> WrapModel:
        raise NotImplementedError


class WrapModel(Model, metaclass=abc.ABCMeta):

    def __init__(self, model: Model) -> None:
        super().__init__(None)
        self.__wrapped_model = model

    @property
    def wrapped_model(self) -> Model:
        return self.__wrapped_model

    @property
    @abc.abstractmethod
    def object(self) -> Any:
        raise NotImplementedError

    @object.setter
    @abc.abstractmethod
    def object(self, object: Any) -> None:
        raise NotImplementedError


class CompoundModel(InheritableModel):

    def wrap(self, component: core.Component) -> WrapModel:
        class CompoundWrapModel(WrapModel):

            def __init__(self, model: Model) -> None:
                super().__init__(model)
                self._component = component

            @property
            def object(self) -> Any:
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

                return None

            @object.setter
            def object(self, object: Any) -> None:
                o = self.wrapped_model.object
                name = self._component.id
                # instance variable
                try:
                    getattr(o, name)
                except AttributeError:
                    pass
                else:
                    setattr(o, name, object)
                    return
                # setter method
                try:
                    setter = getattr(o, 'set_' + name)
                except AttributeError:
                    pass
                else:
                    if callable(setter):
                        setter(object)
                        return
                # __setitem__
                try:
                    o.__setitem__(name, object)
                except AttributeError:
                    pass
                else:
                    return

                raise AttributeError(name)

        return CompoundWrapModel(self)
