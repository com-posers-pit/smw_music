# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Miscellaneous utility functions."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import csv
from contextlib import suppress
from math import isclose
from pathlib import Path
from typing import Any, Tuple, Type, TypeVar
from urllib import error
from urllib.request import Request, urlopen
from zipfile import ZipFile

from .common import RESOURCES

# TODO: Replace this with a generic function in python 3.12 only
T = TypeVar("T")

###############################################################################
# API function definitions
###############################################################################


def append_suffix(fname: Path, suffix: str) -> Path:
    # h/t: https://stackoverflow.com/questions/49380572
    return fname.parent / (fname.name + suffix)


###############################################################################


def brr_size(fsize: int) -> str:
    rounding = 5
    rounded_size_kb = rounding * round(
        (brr_size_b(fsize) / 1024) / rounding, 1
    )
    if isclose(0, rounded_size_kb):
        return "< 0.5"
    return f"{rounded_size_kb:.1f}"


###############################################################################


def brr_size_b(fsize: int) -> int:
    return fsize - 2


###############################################################################


def codename() -> str:
    with (RESOURCES / "codenames.csv").open() as fobj:
        for row in csv.reader(fobj):
            codename = row[-1]

    return codename


###############################################################################


def filter_type(dtype: Type[T] | Tuple[Type[T]], lst: list[Any]) -> list[T]:
    return list(filter(lambda x: isinstance(x, dtype), lst))


###############################################################################


def hexb(val: int) -> str:
    return f"${val:02X}"


###############################################################################


def newest_release() -> tuple[str, tuple[int, int, int]] | None:
    req = Request(
        "https://github.com/com-posers-pit/smw_music/releases/latest"
    )
    with suppress(error.HTTPError), urlopen(req) as resp:  # nosec: B310
        url = resp.geturl()
        return (url, version_tuple(url.split("/")[-1].lstrip("v")))
    return None


###############################################################################


def pct(val: float, lim: float = 255) -> str:
    return f"{100*val/lim:3.1f}%"


###############################################################################


def version_tuple(version: str) -> tuple[int, int, int]:
    major, minor, patch, *_ = tuple(int(x) for x in version.split("."))
    return (major, minor, patch)


###############################################################################


def zip_top(zobj: ZipFile) -> Path:
    names = zobj.namelist()
    shortest = sorted(names, key=len)[0]
    root = ""
    if all(x.startswith(shortest) for x in names):
        root = shortest

    return Path(root)
