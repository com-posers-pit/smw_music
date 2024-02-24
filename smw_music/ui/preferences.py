# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard preferences."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from pathlib import Path

# Library imports
from PyQt6 import uic
from PyQt6.QtWidgets import QFileDialog

# Package imports
from smw_music.common import RESOURCES
from smw_music.spcmw import Preferences

from .preferences_view import PreferencesView
from .utils import is_checked

###############################################################################
# Private constant definitions
###############################################################################

_CURRENT_PREFS_VERSION = 0

###############################################################################
# API class definitions
###############################################################################


class PreferencesDlg:
    _dialog: PreferencesView

    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self) -> None:
        dialog: PreferencesView = uic.loadUi(RESOURCES / "preferences.ui")
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

    def exec(self, preferences: Preferences) -> Preferences | None:
        d = self._dialog

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

            return Preferences(
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
