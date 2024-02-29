# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Music XML -> AMK Converter."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import os
import platform
from contextlib import suppress
from pathlib import Path

# Library imports
import yaml

# Package imports
from smw_music.common import SmwMusicException
from smw_music.spcmw.preferences import Preferences

from . import amk
from .project import Project, ProjectInfo

###############################################################################
# Private function definitions
###############################################################################


def _config_dir(new: bool = True) -> Path:
    app = "spcmw" if new else "xml2mml"

    sys = platform.system()
    match sys:
        case "Linux":
            default = Path(os.environ["HOME"]) / ".config"
            conf_dir = Path(os.environ.get("XDG_CONFIG_HOME", default))
        case "Windows":
            conf_dir = Path(os.environ["APPDATA"])
        case "Darwin":
            conf_dir = Path(os.environ["HOME"]) / "Library"
        case _:
            raise SmwMusicException(f"Unknown OS {sys}")

    return conf_dir / app


###############################################################################


def _create_config_dir() -> None:
    os.makedirs(_CONFIG_DIR, exist_ok=True)


###############################################################################


def _remove_old_config_dir() -> None:
    # Do this carefully and deliberately rather than using shutil.rmtree
    if _CONFIG_DIR_OLD.exists():
        with suppress(FileNotFoundError):
            os.remove(_PREFS_FNAME_OLD)
        with suppress(FileNotFoundError):
            os.remove(_RECENT_PROJECTS_FNAME_OLD)
        with suppress(FileNotFoundError):
            os.rmdir(_CONFIG_DIR_OLD)


###############################################################################
# API variable definitions
###############################################################################


_CONFIG_DIR = _config_dir()
_CONFIG_DIR_OLD = _config_dir(False)
_PREFS_FNAME = _CONFIG_DIR / "preferences.yaml"
_PREFS_FNAME_OLD = _CONFIG_DIR_OLD / "preferences.yaml"
_RECENT_PROJECTS_FNAME = _CONFIG_DIR / "projects.yaml"
_RECENT_PROJECTS_FNAME_OLD = _CONFIG_DIR_OLD / "projects.yaml"

###############################################################################
# API function definitions
###############################################################################


def create_project(path: Path, info: ProjectInfo) -> Project:
    amk.create_project(path, info.project_name, get_preferences().amk_fname)
    return Project(path, info)


###############################################################################


def first_use() -> bool:
    return not (_PREFS_FNAME.exists() or _PREFS_FNAME_OLD.exists())


###############################################################################


def get_preferences() -> Preferences:
    if _PREFS_FNAME.exists():
        rv = Preferences.from_file(_PREFS_FNAME)
    elif _PREFS_FNAME_OLD.exists():
        rv = Preferences.from_file(_PREFS_FNAME_OLD)
    else:
        rv = Preferences()

    return rv


###############################################################################


def get_recent_projects() -> list[Path]:
    projects = None
    for fname in [_RECENT_PROJECTS_FNAME, _RECENT_PROJECTS_FNAME_OLD]:
        with suppress(FileNotFoundError):
            with open(fname, "r", encoding="utf8") as fobj:
                projects = yaml.safe_load(fobj)
                break

    if projects is None:
        projects = []

    return [Path(project).resolve() for project in projects]


###############################################################################


def save_preferences(preferences: Preferences) -> None:
    _create_config_dir()
    _remove_old_config_dir()
    preferences.to_file(_PREFS_FNAME)


###############################################################################


def save_recent_projects(projects: list[Path], project_limit: int = 5) -> None:
    if project_limit:
        projects = projects[-project_limit:]

    _create_config_dir()
    with open(_RECENT_PROJECTS_FNAME, "w", encoding="utf8") as fobj:
        yaml.safe_dump([str(project.resolve()) for project in projects], fobj)
