# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Project settings."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from importlib import resources
from pathlib import Path

# Library imports
from PyQt6 import uic
from PyQt6.QtWidgets import QFileDialog

# Package imports
from smw_music.ui.project_settings_view import ProjectSettingsView
from smw_music.ui.state import PreferencesState
from smw_music.ui.utils import is_checked

###############################################################################
# API class definitions
###############################################################################


class ProjectSettings:
    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self) -> None:
        data_lib = resources.files("smw_music.data")
        ui_contents = data_lib / "project_settings.ui"
        dialog: ProjectSettingsView = uic.loadUi(ui_contents)

        dialog.select_musicxml_fname.released.connect(
            self._on_musicxml_fname_clicked
        )

        self._dialog = dialog

    ###########################################################################
    # Slot definitions
    ###########################################################################

    def _on_musicxml_fname_clicked(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(
            self._view,
            caption="MusicXML Input File",
            filter="MusicXML Files (*.musicxml *.mxl)",
        )
        if fname:
            self._dialog.musicxml_fname.setText(fname)

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

        if self._dialog.exec():
            amk_fname = Path(d.amk_fname.text())
            spcplay_fname = Path(d.spcplay_fname.text())
            pack_dir = Path(d.sample_pack_dirname.text())
            advanced_mode = is_checked(d.advanced_mode)
            dark_mode = is_checked(d.dark_mode)
            release_check = is_checked(d.release_check)
            confirm_render = is_checked(d.confirm_render)

            return PreferencesState(
                amk_fname,
                spcplay_fname,
                pack_dir,
                advanced_mode,
                dark_mode,
                release_check,
                confirm_render,
            )

        return None
