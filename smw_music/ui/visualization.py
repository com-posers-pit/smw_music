# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only


###############################################################################
# Imports
###############################################################################

# Standard library imports
from collections import namedtuple
from enum import Enum
from pathlib import Path

# Library imports
import numpy as np
import numpy.typing as npt
from PIL import Image

###############################################################################
# Private Class Definitions
###############################################################################


class _UsageType(Enum):
    VARIABLES = (255, 0, 0)
    ENGINE = (255, 255, 0)
    SONG = (0, 128, 0)
    SAMPLE_TABLE = (0, 255, 0)
    ECHO = (160, 0, 160)
    ECHO_PAD = (63, 63, 63)
    FREE = (0, 0, 0)


###############################################################################
# Private Function Definitions
###############################################################################


def _count_matches(arr: npt.NDArray[np.uint8], val: _UsageType) -> int:
    (matches,) = np.where((arr == val.value).all(axis=1))
    return len(matches)


###############################################################################
# API Class Definitions
###############################################################################

Utilization = namedtuple(
    "Utilization",
    [
        "variables",
        "engine",
        "song",
        "sample_table",
        "samples",
        "echo",
        "echo_pad",
        "free",
    ],
)

###############################################################################
# API Function Definitions
###############################################################################


def decode_utilization(png_name: Path) -> Utilization:
    with Image.open(png_name) as png:
        img = np.array(png.convert("RGB").getdata())

    variables = _count_matches(img, _UsageType.VARIABLES)
    engine = _count_matches(img, _UsageType.ENGINE)
    song = _count_matches(img, _UsageType.SONG)
    sample_table = _count_matches(img, _UsageType.SAMPLE_TABLE)
    echo = _count_matches(img, _UsageType.ECHO)
    echo_pad = _count_matches(img, _UsageType.ECHO_PAD)
    free = _count_matches(img, _UsageType.FREE)
    samples = (
        len(img)
        - variables
        - engine
        - song
        - sample_table
        - echo
        - echo_pad
        - free
    )

    return Utilization(
        variables=variables,
        engine=engine,
        song=song,
        sample_table=sample_table,
        samples=samples,
        echo=echo,
        echo_pad=echo_pad,
        free=free,
    )
