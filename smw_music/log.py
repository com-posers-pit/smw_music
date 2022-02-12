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
# API function definitions
###############################################################################


def debug(func):
    @wraps(func)
    def f(self, *args, **kwargs):
        logging.debug(
            "Calling %s(%d):%s()",
            self.__class__.__name__,
            id(self),
            func.__name__,
        )
        return func(self, *args, **kwargs)

    return f


###############################################################################


def info(func):
    @wraps(func)
    def f(self, *args, **kwargs):
        logging.info(
            "Calling %s(%d):%s()",
            self.__class__.__name__,
            id(self),
            func.__name__,
        )
        return func(self, *args, **kwargs)

    return f
