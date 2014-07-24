"""Python 2/3 compatibility utils"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import sys


python_version = sys.version_info[0]


def raise_(exception_type, message=None, traceback=None):
    if python_version == 2:
        # Trying to mimic "raise exception_type, message, traceback"
        if traceback is not None:
            from traceback import print_tb
            print_tb(traceback)
        raise exception_type(message)
    else:
        raise exception_type(message).with_traceback(traceback)
