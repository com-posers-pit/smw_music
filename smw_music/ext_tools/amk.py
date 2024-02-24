# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""AMK-specific utility functions"""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import hashlib
import os
import shutil
import zipfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Library imports
import numpy as np
import numpy.typing as npt
from PIL import Image

# Package imports
from smw_music.utils import zip_top

###############################################################################
# API constant definitions
###############################################################################

N_BUILTIN_SAMPLES = 20


###############################################################################
# Private class definitions
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
# API class definitions
###############################################################################


@dataclass
class Utilization:
    variables: int
    engine: int
    song: int
    sample_table: int
    samples: int
    echo: int
    echo_pad: int

    size: int = field(init=False, default=65536)

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def free(self) -> int:
        return self.size - self.util

    ###########################################################################

    @property
    def util(self) -> int:
        return (
            self.variables
            + self.engine
            + self.song
            + self.sample_table
            + self.samples
            + self.echo
            + self.echo_pad
        )


###############################################################################
# API function definitions
###############################################################################


def create_project(path: Path, project_name: str, amk_zname: Path) -> None:
    _unpack_amk(path, amk_zname)

    # Add visualizations directory
    make_vis_dir(path)

    # Apply updates to stock AMK files
    _update_amk(path)


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
    )


###############################################################################


def default_utilization() -> Utilization:
    return Utilization(
        variables=1102,
        engine=9938,
        song=119,
        sample_table=80,
        samples=12815,
        echo=4,
        echo_pad=252,
    )


###############################################################################


def get_ticks(path: Path, project_name: str) -> list[int]:
    fname = (stats_dir(path) / project_name).with_suffix("txt")

    # Filter only lines with "TICKS:" in it
    with open(fname, "r") as fobj:
        tick_lines = [line for line in fobj.readlines() if "TICKS:" in line]

    # Split on whitespace to get the tick value, then (because of a bug in
    # AMK), optionally strip off anything before an 'x'.  Those don't actually
    # return a hex value.
    tick_vals = [line.split()[-1].split("x")[-1] for line in tick_lines]

    return list(map(int, tick_vals))


###############################################################################


# https://www.smwcentral.net/?p=viewthread&t=98793&page=1&pid=1579851#p1579851
def make_vis_dir(path: Path) -> None:
    os.makedirs(vis_dir(path), exist_ok=True)


###############################################################################


def mml_dir(proj_dir: Path) -> Path:
    return proj_dir / "music"


###############################################################################


def samples_dir(proj_dir: Path) -> Path:
    return proj_dir / "samples"


###############################################################################


def spc_dir(proj_dir: Path) -> Path:
    return proj_dir / "SPCs"


###############################################################################


def stats_dir(proj_dir: Path) -> Path:
    return proj_dir / "stats"


###############################################################################


# https://www.smwcentral.net/?p=viewthread&t=98793&page=1&pid=1579851#p1579851
def vis_dir(proj_dir: Path) -> Path:
    return proj_dir / "Visualizations"


###############################################################################
# Private function definitions
###############################################################################


def _count_matches(arr: npt.NDArray[np.uint8], val: _UsageType) -> int:
    (matches,) = np.where((arr == val.value).all(axis=1))
    return len(matches)


###############################################################################


def _unpack_amk(path: Path, amk_zname: Path) -> None:
    members = [
        "1DF9",
        "AddmusicK.exe",
        "Addmusic_sample groups.txt",
        "asar.exe",
        "music",
        "SPCs",
        "1DFC",
        "Addmusic_list.txt",
        "Addmusic_sound effects.txt",
        "asm",
        "samples",
        "stats",
    ]

    extract_dir = path / "unzip"
    with zipfile.ZipFile(str(amk_zname), "r") as zobj:
        # Extract all the files
        zobj.extractall(path=extract_dir)

        # Some AMK releases have a top-level folder in the zip file, some
        # don't.  This figures out what that is, if it's there
        root = zip_top(zobj)

        # Move them up a directory and delete the rest
        for member in members:
            shutil.move(extract_dir / root / member, path / member)

        shutil.rmtree(extract_dir)


###############################################################################


def _update_amk(path: Path) -> None:
    # https://www.smwcentral.net/?p=viewthread&t=98793&page=2&pid=1601787#p1601787
    expected_md5 = "7e9d4bd864cfc1e82272fb0a9379e318"
    fname = path / "music/originals/09 Bonus End.txt"
    with open(fname, "rb") as fobj:
        data = fobj.read()
    actual_md5 = hashlib.new("md5", data, usedforsecurity=False).hexdigest()
    if actual_md5 == expected_md5:
        contents = data.split(b"\n")
        contents = contents[:15] + contents[16:]
        data = b"\n".join(contents)
        with open(fname, "wb") as fobj:
            fobj.write(data)
