# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""AMK-specific utility functions"""

###############################################################################

# Standard library imports
import hashlib
import os
import shutil
import stat
import zipfile
from enum import Enum, auto
from pathlib import Path

# Library imports
from mako.template import Template  # type: ignore

# Package imports
from smw_music import RESOURCES
from smw_music.utils import zip_top

###############################################################################
# Private constant definitions
###############################################################################

_SAMPLE_GROUP_FNAME = "Addmusic_sample groups.txt"

###############################################################################
# API function definitions
###############################################################################


def create_project(path: Path, project_name: str, amk_zname: Path) -> None:
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

    # Append new sample groups
    _append_spcmw_sample_groups(path)

    # Add visualizations directory
    make_vis_dir(path)

    # Apply updates to stock AMK files
    # https://www.smwcentral.net/?p=viewthread&t=98793&page=2&pid=1601787#p1601787
    expected_md5 = "7e9d4bd864cfc1e82272fb0a9379e318"
    fname = path / "music/originals/09 Bonus End.txt"
    with open(fname, "rb") as fobj:
        data = fobj.read()
    actual_md5 = hashlib.md5(data).hexdigest()  # nosec: B324
    if actual_md5 == expected_md5:
        contents = data.split(b"\n")
        contents = contents[:15] + contents[16:]
        data = b"\n".join(contents)
        with open(fname, "wb") as fobj:
            fobj.write(data)

    # Create the conversion scripts
    for tmpl_name in ["convert.bat", "convert.sh"]:
        tmpl = Template(RESOURCES / tmpl_name)  # nosec B702
        script = tmpl.render(project=project_name)
        target = path / tmpl_name

        with open(target, "w", encoding="utf8") as fobj:
            fobj.write(script)

        os.chmod(target, os.stat(target).st_mode | stat.S_IXUSR)


###############################################################################


# https://www.smwcentral.net/?p=viewthread&t=98793&page=1&pid=1579851#p1579851
def make_vis_dir(path: Path) -> None:
    os.makedirs(path / "Visualizations", exist_ok=True)


###############################################################################


def update_sample_groups_file(
    path: Path,
    sample_group: "BuiltinSampleGroup",
    sample_sources: list["BuiltinSampleSource"],
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
# Private function definitions
###############################################################################


def _append_spcmw_sample_groups(path: Path) -> None:
    # Append new sample groups
    with (RESOURCES / "sample_groups.txt").open("r") as fobj_in, open(
        path / _SAMPLE_GROUP_FNAME, "a", newline="\r\n"
    ) as fobj_out:
        fobj_out.write(fobj_in.read())


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
