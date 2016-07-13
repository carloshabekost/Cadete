# -*- coding: utf-8 -*-

class Singleton(type):
    """
    Classe Singleton

    Metaclasse utilizada para definir singletons

    """
    _instances = {}

    def __call__(self, *args, **kwargs):
        if self not in self._instances:
            self._instances[self] = super(Singleton, self).__call__(*args, **kwargs)
        return self._instances[self]
