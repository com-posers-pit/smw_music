# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SPCMW-specific logic for interacing with AMK"""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import platform
import subprocess
import zipfile
from glob import glob
from pathlib import Path

# Package imports
from smw_music.ext_tools import amk

from .project import Project

###############################################################################
# API function calls
###############################################################################


def convert(project_path: Path, timeout: float) -> str:
    match platform.system():
        case "Darwin" | "Linux":
            script = ["sh", "convert.sh"]
        case "Windows":
            script = [str(project_path / "convert.bat")]

    return subprocess.check_output(  # nosec B603
        script, cwd=project_path, stderr=subprocess.STDOUT, timeout=timeout
    ).decode()


###############################################################################


def mml_fname(proj: Project) -> Path:
    nfo = proj.info
    mml = (amk.mml_dir(nfo.project_dir) / nfo.project_name).with_suffix(".txt")
    return mml


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
    spc = (amk.vis_dir(pdir) / pname).with_suffix(".spc")
    return spc


###############################################################################


def vis_fname(proj: Project) -> Path:
    pdir, pname = proj.info.project_dir, proj.info.project_name
    png = (amk.vis_dir(pdir) / pname).with_suffix(".png")
    return png
