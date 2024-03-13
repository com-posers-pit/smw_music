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
from glob import glob
from pathlib import Path
from typing import Callable

# Library imports
from mako.template import Template  # type: ignore

# Package imports
from smw_music.common import RESOURCES
from smw_music.ext_tools import amk
from smw_music.utils import append_suffix

from .common import SpcmwException
from .instrument import SampleSource
from .project import Project
from .sample import SamplePack

###############################################################################
# Private function definitions
###############################################################################


def _convert(project: Project, timeout: float) -> str:
    project_path = project.project_dir
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


def _fname_gen(proj: Project, subdir: Callable[[Path, str], Path]) -> Path:
    return subdir(proj.project_dir, proj.info.project_name)


###############################################################################


def _generate_manifest(proj: Project) -> None:
    # TODO: Add stat parsing and reporting
    pass


###############################################################################


def _vis_fname(proj: Project) -> Path:
    return _fname_gen(proj, amk.vis_fname)


###############################################################################
# API function definitions
###############################################################################


def create_project(path: Path, project_name: str, amk_zname: Path) -> None:
    amk.create_project(path, project_name, amk_zname)

    # Create the conversion scripts
    _create_conversion_scripts(path, project_name)


###############################################################################


def generate_spc(
    project: Project, sample_packs: dict[str, SamplePack], timeout: int
) -> str:
    project = deepcopy(project)

    if not mml_fname(project).exists():
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

    _generate_manifest(project)

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

    mml = mml_fname(project)
    spc = spc_fname(project)
    samples = samples_dir(project)
    project_name = Path(info.project_name)

    zname = append_suffix(project.project_dir / project_name, ".zip")
    with zipfile.ZipFile(zname, "w") as zobj:
        zobj.write(mml, mml.name)
        zobj.write(spc, spc.name)
        for brr in glob("**/*.brr", root_dir=samples, recursive=True):
            zobj.write(samples / brr, arcname=str(project_name / brr))

    return zname


###############################################################################


def samples_dir(proj: Project) -> Path:
    return amk.samples_dir(proj.project_dir) / proj.info.project_name


###############################################################################


def mml_fname(proj: Project) -> Path:
    return _fname_gen(proj, amk.mml_fname)


###############################################################################


def spc_fname(proj: Project) -> Path:
    return _fname_gen(proj, amk.spc_fname)


###############################################################################


def stats_fname(proj: Project) -> Path:
    return _fname_gen(proj, amk.stats_fname)


###############################################################################


def utilization(project: Project) -> amk.Utilization:
    return amk.decode_utilization(_vis_fname(project))
