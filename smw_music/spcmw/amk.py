# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SPCMW-specific logic for interacing with AMK"""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import os
import platform
import shutil
import stat
import subprocess
import zipfile
from copy import deepcopy
from enum import Enum, auto
from glob import glob
from pathlib import Path

# Library imports
from mako.template import Template  # type: ignore

# Package imports
from smw_music.common import RESOURCES, SpcmwException
from smw_music.ext_tools import amk

from .instrument import SampleSource
from .project import Project
from .sample import SamplePack

###############################################################################
# Private constant definitions
###############################################################################

_SAMPLE_GROUP_FNAME = "Addmusic_sample groups.txt"

###############################################################################
# API Class definitions
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


def _convert(project: Project, timeout: float) -> str:
    project_path = project.info.project_dir
    match platform.system():
        case "Darwin" | "Linux":
            script = ["sh", "convert.sh"]
        case "Windows":
            script = [str(project_path / "convert.bat")]

    return subprocess.check_output(  # nosec B603
        script, cwd=project_path, stderr=subprocess.STDOUT, timeout=timeout
    ).decode()


###############################################################################


def _copy_samples(project: Project, packs: dict[str, SamplePack]) -> None:
    samples_path = samples_dir(project)

    msg = ""
    for inst in project.settings.instruments.values():
        for sample in inst.samples.values():
            if sample.sample_source == SampleSource.BRR:
                shutil.copy2(sample.brr_fname, samples_path)
            if sample.sample_source == SampleSource.SAMPLEPACK:
                pack_name, pack_path = sample.pack_sample
                target = samples_path / pack_name / pack_path
                os.makedirs(target.parents[0], exist_ok=True)
                with open(target, "wb") as fobj:
                    try:
                        fobj.write(packs[pack_name][pack_path].data)
                    except KeyError:
                        msg += f"Could not find sample pack {pack_name}\n"

    if msg:
        raise SpcmwException(msg)


###############################################################################


def _create_conversion_scripts(path: Path, project_name: str) -> None:
    for tmpl_name in ["convert.bat", "convert.sh"]:
        tmpl = Template(filename=str(RESOURCES / tmpl_name))  # nosec B702
        script = tmpl.render(project=project_name)
        target = path / tmpl_name

        with open(target, "w", encoding="utf8") as fobj:
            fobj.write(script)

        os.chmod(target, os.stat(target).st_mode | stat.S_IXUSR)


###############################################################################


def _mml_fname(proj: Project) -> Path:
    pdir, pname = proj.info.project_dir, proj.info.project_name
    return (amk.mml_dir(pdir) / pname).with_suffix(".txt")


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


def _vis_fname(proj: Project) -> Path:
    pdir, pname = proj.info.project_dir, proj.info.project_name
    return (amk.vis_dir(pdir) / pname).with_suffix(".png")


###############################################################################
# API function definitions
###############################################################################


def create_project(path: Path, project_name: str, amk_zname: Path) -> None:
    amk.create_project(path, project_name, amk_zname)

    # Append new sample groups
    _append_spcmw_sample_groups(path)

    # Create the conversion scripts
    _create_conversion_scripts(path, project_name)


###############################################################################


def generate_spc(
    project: Project, sample_packs: dict[str, SamplePack], timeout: int
) -> str:
    project = deepcopy(project)

    if not _mml_fname(project).exists():
        raise SpcmwException("MML not Generated")

    samples_path = samples_dir(project)

    shutil.rmtree(samples_path, ignore_errors=True)
    os.makedirs(samples_path, exist_ok=True)

    _copy_samples(project, sample_packs)

    try:
        msg = _convert(project, timeout)
    except subprocess.CalledProcessError as e:
        raise SpcmwException(e.output.decode("utf8")) from e
    except subprocess.TimeoutExpired as e:
        raise SpcmwException("Conversion timed out") from e

    # TODO: Add stat parsing and reporting
    # TODO: Generate manifest

    return msg


###############################################################################


def render_zip(project: Project) -> Path:
    info = project.info
    sets = project.settings

    # Turn off the preview features
    sets.start_measure = 1
    for sample in sets.samples.values():
        sample.mute = False
        sample.solo = False

    mml = _mml_fname(project)
    spc = spc_fname(project)
    samples = samples_dir(project)
    project_name = Path(info.project_name)

    zname = info.project_dir / project_name.with_suffix(".zip")
    with zipfile.ZipFile(zname, "w") as zobj:
        zobj.write(mml, mml.name)
        zobj.write(spc, spc.name)
        for brr in glob("**/*.brr", root_dir=samples, recursive=True):
            zobj.write(samples / brr, arcname=str(project_name / brr))

    return zname


###############################################################################


def samples_dir(proj: Project) -> Path:
    info = proj.info
    return amk.samples_dir(info.project_dir) / info.project_name


###############################################################################


def spc_fname(proj: Project) -> Path:
    pdir, pname = proj.info.project_dir, proj.info.project_name
    return (amk.spc_dir(pdir) / pname).with_suffix(".spc")


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


def utilization(project: Project) -> amk.Utilization:
    return amk.decode_utilization(_vis_fname(project))
