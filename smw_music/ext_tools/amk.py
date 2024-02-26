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
from enum import Enum, auto
from pathlib import Path

# Library imports
import numpy as np
import numpy.typing as npt
from PIL import Image

# Package imports
from smw_music.common import RESOURCES
from smw_music.utils import append_suffix, zip_top

###############################################################################
# Private constant definitions
###############################################################################

_SAMPLE_GROUP_FNAME = "Addmusic_sample groups.txt"

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


class BuiltinSampleGroup(Enum):
    DEFAULT = auto()
    OPTIMIZED = auto()
    REDUX1 = auto()
    REDUX2 = auto()
    CUSTOM = auto()


###############################################################################


class BuiltinSampleSource(Enum):
    DEFAULT = auto()
    OPTIMIZED = auto()
    EMPTY = auto()


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

    # Append new sample groups
    _append_spcmw_sample_groups(path)

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
    fname = append_suffix(stats_dir(path) / project_name, ".txt")

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


def update_sample_groups_file(
    path: Path,
    sample_group: BuiltinSampleGroup,
    sample_sources: list[BuiltinSampleSource],
) -> None:
    _remove_spcmw_sample_groups(path)
    _append_spcmw_sample_groups(path)

    if sample_group == BuiltinSampleGroup.CUSTOM:
        smap = [
            '00 SMW @0.brr"!',
            '01 SMW @1.brr"!',
            '02 SMW @2.brr"!',
            '03 SMW @3.brr"!',
            '04 SMW @4.brr"!',
            '05 SMW @8.brr"!',
            '06 SMW @22.brr"!',
            '07 SMW @5.brr"!',
            '08 SMW @6.brr"!',
            '09 SMW @7.brr"!',
            '0A SMW @9.brr"!',
            '0B SMW @10.brr"!',
            '0C SMW @13.brr"!',
            '0D SMW @14.brr"',
            '0E SMW @29.brr"!',
            '0F SMW @21.brr"',
            '10 SMW @12.brr"!',
            '11 SMW @17.brr"',
            '12 SMW @15.brr"!',
            '13 SMW Thunder.brr"!',
        ]

        group = ["", "#custom", "{"]
        for src, sample in zip(sample_sources, smap):
            match src:
                case BuiltinSampleSource.DEFAULT:
                    group.append(f'\t"default/{sample}')
                case BuiltinSampleSource.OPTIMIZED:
                    group.append(f'\t"optimized/{sample}')
                case BuiltinSampleSource.EMPTY:
                    group.append('\t"EMPTY.brr"')
        group.extend(["}", ""])
        with open(path / _SAMPLE_GROUP_FNAME, "a", newline="\r\n") as fobj:
            fobj.write("\n".join(group))


###############################################################################


# https://www.smwcentral.net/?p=viewthread&t=98793&page=1&pid=1579851#p1579851
def vis_dir(proj_dir: Path) -> Path:
    return proj_dir / "Visualizations"


###############################################################################
# Private function definitions
###############################################################################


def _append_spcmw_sample_groups(path: Path) -> None:
    # Append new sample groups
    with (RESOURCES / "sample_groups.txt").open("r") as fobj_in, open(
        path / _SAMPLE_GROUP_FNAME, "a", newline="\r\n"
    ) as fobj_out:
        fobj_out.write(fobj_in.read())


###############################################################################


def _count_matches(arr: npt.NDArray[np.uint8], val: _UsageType) -> int:
    (matches,) = np.where((arr == val.value).all(axis=1))
    return len(matches)


###############################################################################


def _remove_spcmw_sample_groups(path: Path) -> None:
    builtin_group_count = 3  # {default, optimized, AMM}

    sep = "}"
    fname = path / _SAMPLE_GROUP_FNAME
    with open(fname) as fobj:
        contents = [x for x in fobj.read().split(sep) if x]

    contents = contents[:builtin_group_count]
    contents.append("\n")

    with open(fname, "w", newline="\r\n") as fobj:
        fobj.write(sep.join(contents))


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
