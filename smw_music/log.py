# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Logging decorators."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import logging
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

###############################################################################
# Private type definitions
###############################################################################

_P = ParamSpec("_P")
_T = TypeVar("_T")

###############################################################################
# Private function definitions
###############################################################################


def _wrapper(
    log_type: Callable[..., None], log_args: bool, log_rv: bool
) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    def decorator(func: Callable[_P, _T]) -> Callable[_P, _T]:
        @wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            self = args[0]
            log_type(
                "Calling %s(%d):%s(%s,%s)",
                self.__class__.__name__,
                id(self),
                func.__name__,
                args if log_args else "",
                kwargs if log_args else "",
            )
            rv = func(*args, **kwargs)
            if log_rv:
                log_type("Returns %s", rv)

            return rv

        return wrapper

    return decorator


###############################################################################
# API function definitions
###############################################################################


def debug(
    args: bool = False, rv: bool = False
) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    """
    Decorator for logging a method invocation at DEBUG level

    Arguments
    ---------
    args: bool
        Log the method arguments iff True

    rv: bool
        Log the method return value iff True
    """
    return _wrapper(logging.debug, args, rv)


###############################################################################


def info(
    args: bool = False, rv: bool = False
) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    """
    Decorator for logging a method invocation at INFO level

    Arguments
    ---------
    args: bool
        Log the method arguments iff True

    rv: bool
        Log the method return value iff True
    """
    return _wrapper(logging.info, args, rv)
