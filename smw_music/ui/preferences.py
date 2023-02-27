# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard preferences."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import io
import pkgutil
from pathlib import Path

# Library imports
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog

# Package imports
from smw_music.ui.preferences_view import PreferencesView
from smw_music.ui.state import PreferencesState

###############################################################################
# API class definitions
###############################################################################


class Preferences:
    _dialog: PreferencesView

    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self) -> None:
        ui_contents = pkgutil.get_data("smw_music", "/data/preferences.ui")
        if ui_contents is None:
            raise Exception("Can't locate preferences")
        dialog: PreferencesView = uic.loadUi(io.BytesIO(ui_contents))
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

        if self._dialog.exec():
            amk_fname = Path(d.amk_fname.text())
            spcplay_fname = Path(d.spcplay_fname.text())
            pack_dir = Path(d.sample_pack_dirname.text())
            advanced_mode = (
                d.advanced_mode.checkState() == Qt.CheckState.Checked
            )

            return PreferencesState(
                amk_fname, spcplay_fname, pack_dir, advanced_mode
            )

        return None
