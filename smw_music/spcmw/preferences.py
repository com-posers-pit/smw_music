# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SPCMW preferences."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

# Library imports
import yaml

# Package imports
from smw_music import SmwMusicException, __version__

###############################################################################
# Private constant definitions
###############################################################################

_CURRENT_PREFS_VERSION = 0

###############################################################################
# API class definitions
###############################################################################


@dataclass
class Preferences:
    amk_fname: Path = Path("")
    spcplay_fname: Path = Path("")
    sample_pack_dname: Path = Path("")
    advanced_mode: bool = False
    dark_mode: bool = False
    release_check: bool = True
    confirm_render: bool = True
    convert_timeout: int = 10

    ###########################################################################

    @classmethod
    def from_file(cls, fname: Path) -> "Preferences":
        with open(fname, "r", encoding="utf8") as fobj:
            prefs = yaml.safe_load(fobj)

        prefs_version = prefs.get("version", _CURRENT_PREFS_VERSION)

        if prefs_version > _CURRENT_PREFS_VERSION:
            raise SmwMusicException(
                f"Preferences file version is {prefs_version}, tool "
                + f"version only supports up to {_CURRENT_PREFS_VERSION}"
            )

        preferences = cls()
        preferences.amk_fname = Path(prefs["amk"]["path"])
        preferences.spcplay_fname = Path(prefs["spcplay"]["path"])
        preferences.sample_pack_dname = Path(prefs["sample_packs"]["path"])
        with suppress(KeyError):
            preferences.advanced_mode = prefs["advanced"]
        with suppress(KeyError):
            preferences.dark_mode = prefs["dark_mode"]
        with suppress(KeyError):
            preferences.release_check = prefs["release_check"]
        with suppress(KeyError):
            preferences.confirm_render = prefs["confirm_render"]
        with suppress(KeyError):
            preferences.convert_timeout = prefs["convert_timeout"]

        return preferences

    ###########################################################################

    def to_file(self, fname: Path) -> None:
        prefs_dict = {
            "spacemusicw": __version__,
            "amk": {"path": str(self.amk_fname)},
            "spcplay": {"path": str(self.spcplay_fname)},
            "sample_packs": {"path": str(self.sample_pack_dname)},
            "advanced": self.advanced_mode,
            "dark_mode": self.dark_mode,
            "release_check": self.release_check,
            "confirm_render": self.confirm_render,
            "convert_timeout": self.convert_timeout,
            "version": _CURRENT_PREFS_VERSION,
        }

        with open(fname, "w", encoding="utf8") as fobj:
            yaml.safe_dump(prefs_dict, fobj)
