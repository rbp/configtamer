#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from .config import Config


def parse(string):
    config = Config()
    items = {}
    to_interpolate = {}

    import re
    re_interpolation = re.compile(r'\{([^}]+)\}')

    for line in string.splitlines():
        if line.strip():
            key, value = [i.strip() for i in line.split(":")]

            if re_interpolation.search(value):
                to_interpolate[key] = value
                continue

            items[key] = value

    for key, value in to_interpolate.items():
        value = re_interpolation.sub(lambda m: items[m.group(1)], value)
        items[key] = value
    
    for key, value in items.items():
        config.__add_key_value__(key, value)

    return config
