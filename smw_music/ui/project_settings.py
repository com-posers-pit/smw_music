# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Project settings."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from pathlib import Path

# Library imports
from PyQt6 import uic
from PyQt6.QtWidgets import QFileDialog

# Package imports
from smw_music import RESOURCES
from smw_music.spcmw import ProjectInfo
from smw_music.ui.project_settings_view import ProjectSettingsView

###############################################################################
# API class definitions
###############################################################################


class ProjectSettingsDlg:
    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self) -> None:
        self._dialog: ProjectSettingsView = uic.loadUi(
            RESOURCES / "project_settings.ui"
        )

        self._dialog.select_musicxml_fname.released.connect(
            self._on_musicxml_fname_clicked
        )

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

    def exec(self, settings: ProjectInfo) -> ProjectInfo | None:
        d = self._dialog  # pylint: disable=invalid-name

        d.composer.setText(settings.composer)
        d.game_name.setText(settings.game)
        d.musicxml_fname.setText(str(settings.musicxml_fname))
        d.porter_name.setText(settings.porter)
        d.title.setText(settings.title)

        if self._dialog.exec():
            musicxml_fname = Path(d.musicxml_fname.text())
            if not musicxml_fname.exists():
                musicxml_fname = Path("")

            return ProjectInfo(
                musicxml_fname,
                settings.project_name,
                d.composer.text(),
                d.title.text(),
                d.porter_name.text(),
                d.game_name.text(),
            )

        return None
