# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard preferences."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

# Library imports
import yaml
from PyQt6 import uic
from PyQt6.QtWidgets import QFileDialog

# Package imports
from smw_music import RESOURCES, SmwMusicException, __version__
from smw_music.ui.preferences_view import PreferencesView
from smw_music.ui.utils import is_checked

###############################################################################
# Private constant definitions
###############################################################################

_CURRENT_PREFS_VERSION = 0

###############################################################################
# API class definitions
###############################################################################


@dataclass
class PreferencesState:
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
    def from_file(cls, fname: Path) -> "PreferencesState":
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


###############################################################################


class Preferences:
    _dialog: PreferencesView

    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self) -> None:
        ui_contents = RESOURCES / "preferences.ui"
        dialog: PreferencesView = uic.loadUi(ui_contents)
        self._dialog = dialog

        connections = [
            (dialog.select_amk_fname, self.on_amk_select_clicked),
            (
                dialog.select_sample_pack_dirname,
                self.on_select_sample_pack_clicked,
            ),
            (dialog.select_spcplay, self.on_select_spcplay_clicked),
        ]

        for button, slot in connections:
            button.released.connect(slot)

    ###########################################################################
    # Slot definitions
    ###########################################################################

    def on_amk_select_clicked(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(
            self._dialog, caption="AMK Zip File", filter="Zip Files (*.zip)"
        )
        if fname:
            self._dialog.amk_fname.setText(fname)

    ###########################################################################

    def on_select_sample_pack_clicked(self) -> None:
        fname = QFileDialog.getExistingDirectory(
            self._dialog,
            caption="Sample Pack Directory",
        )
        if fname:
            self._dialog.sample_pack_dirname.setText(fname)

    ###########################################################################

    def on_select_spcplay_clicked(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(
            self._dialog,
            caption="SPC Player Executable",
            filter="Executable (spcplay.exe)",
        )
        if fname:
            self._dialog.spcplay_fname.setText(fname)

    ###########################################################################
    # API function definitions
    ###########################################################################

    def exec(self, preferences: PreferencesState) -> PreferencesState | None:
        d = self._dialog  # pylint: disable=invalid-name

        fname = preferences.amk_fname
        text = str(fname) if fname.parts else ""
        d.amk_fname.setText(text)

        fname = preferences.spcplay_fname
        text = str(fname) if fname.parts else ""
        d.spcplay_fname.setText(text)

        fname = preferences.sample_pack_dname
        text = str(fname) if fname.parts else ""
        d.sample_pack_dirname.setText(text)

        d.advanced_mode.setChecked(preferences.advanced_mode)
        d.dark_mode.setChecked(preferences.dark_mode)
        d.release_check.setChecked(preferences.release_check)
        d.confirm_render.setChecked(preferences.confirm_render)
        d.convert_timeout.setValue(preferences.convert_timeout)

        if self._dialog.exec():
            amk_fname = Path(d.amk_fname.text())
            spcplay_fname = Path(d.spcplay_fname.text())
            pack_dir = Path(d.sample_pack_dirname.text())
            advanced_mode = is_checked(d.advanced_mode)
            dark_mode = is_checked(d.dark_mode)
            release_check = is_checked(d.release_check)
            confirm_render = is_checked(d.confirm_render)
            convert_timeout = d.convert_timeout.value()

            return PreferencesState(
                amk_fname,
                spcplay_fname,
                pack_dir,
                advanced_mode,
                dark_mode,
                release_check,
                confirm_render,
                convert_timeout,
            )

        return None
