#!/usr/bin/env python

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import collections


class Config(collections.Mapping):
    def __getattr__(self, attr):
        if attr.lower() in self.__dict__:
            return self.__dict__[attr.lower()]
        raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, attr))

    def __repr__(self):
        return self.__dict__.__str__()
    # TODO: perhaps have __str__ return a config file-like representation
    __str__ = __repr__
        

    # FIXME: this should probably go :)
    def __add_key_value__(self, key, value):
        self.__dict__[key.lower()] = value


    # Mapping ABC
    def __getitem__(self, key):
        return self.__dict__[key.lower()]
    def __iter__(self):
        return self.__dict__.__iter__()
    def __len__(self):
        return self.__dict__.__len__()
