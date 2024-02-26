# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Project settings."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import replace
from pathlib import Path

# Library imports
from PyQt6 import uic
from PyQt6.QtWidgets import QFileDialog

# Package imports
from smw_music.common import RESOURCES
from smw_music.spcmw import ProjectInfo

from .project_settings_view import ProjectSettingsView

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
            self._dialog,
            caption="MusicXML Input File",
            filter="MusicXML Files (*.musicxml *.mxl)",
        )
        if fname:
            self._dialog.musicxml_fname.setText(fname)

    ###########################################################################
    # API function definitions
    ###########################################################################

    def exec(self, info: ProjectInfo) -> ProjectInfo | None:
        d = self._dialog

        d.composer.setText(info.composer)
        d.game_name.setText(info.game)
        d.musicxml_fname.setText(str(info.musicxml_fname))
        d.porter_name.setText(info.porter)
        d.title.setText(info.title)

        if self._dialog.exec():
            musicxml_fname = Path(d.musicxml_fname.text())
            if not musicxml_fname.exists():
                musicxml_fname = Path("")

            return replace(
                info,
                musicxml_fname=musicxml_fname,
                composer=d.composer.text(),
                title=d.title.text(),
                porter=d.porter_name.text(),
                game=d.game_name.text(),
            )

        return None
