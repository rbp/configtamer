#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from .config import Config


def parse(string):
    config = Config()
    items = {}
    for line in string.splitlines():
        if line.strip():
            key, value = [i.strip() for i in line.split(":")]

            import re
            interpolation = re.compile(r'\{([^}]+)\}')
            value = interpolation.sub(lambda m: items[m.group(1)], value)

            items[key] = value
            config.__add_key_value__(key, value)
    
    return config
