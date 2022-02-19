# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Logging decorators."""

###############################################################################
# Standard library imports
###############################################################################

import logging

from functools import wraps

###############################################################################
# Private function definitions
###############################################################################


def _wrapper(log_type, log_args: bool, log_rv: bool):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            log_type(
                "Calling %s(%d):%s(%s,%s)",
                self.__class__.__name__,
                id(self),
                func.__name__,
                args if log_args else "",
                kwargs if log_args else "",
            )
            rv = func(self, *args, **kwargs)
            if log_rv:
                log_type("Returns %s", rv)

            return rv

        return wrapper

    return decorator


###############################################################################
# API function definitions
###############################################################################


def debug(args: bool = False, rv: bool = False):
    return _wrapper(logging.debug, args, rv)


###############################################################################


def info(args: bool = False, rv: bool = False):
    return _wrapper(logging.info, args, rv)
