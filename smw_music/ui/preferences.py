#!/usr/bin/env python3

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
from PyQt6.QtGui import QStandardItem, QStandardItemModel
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
        dialog = uic.loadUi(io.BytesIO(ui_contents))
        self._dialog = dialog

        connections = [
            (dialog.select_amk_fname, self.on_amk_select_clicked),
            (
                dialog.select_sample_pack_fname,
                self.on_select_sample_pack_clicked,
            ),
            (dialog.select_spcplay, self.on_select_spcplay_clicked),
            (dialog.add_sample_pack, self.on_add_sample_pack_clicked),
            (dialog.remove_sample_pack, self.on_remove_sample_pack_clicked),
        ]

        for button, slot in connections:
            button.released.connect(slot)

    ###########################################################################
    # Slot definitions
    ###########################################################################

    def on_add_sample_pack_clicked(self) -> None:
        d = self._dialog  # pylint: disable=invalid-name
        name = d.sample_pack_name.text()
        path = d.sample_pack_fname.text()

        if name and path:
            self._add_sample_pack(name, Path(path))

    ###########################################################################

    def on_amk_select_clicked(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(
            self._dialog, caption="AMK Zip File", filter="Zip Files (*.zip)"
        )
        if fname:
            self._dialog.amk_fname.setText(fname)

    ###########################################################################

    def on_remove_sample_pack_clicked(self) -> None:
        packs = self._dialog.sample_pack_list
        for item in packs.selectedItems():
            packs.takeItem(packs.row(item))
            del item

    ###########################################################################

    def on_select_sample_pack_clicked(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(
            self._dialog, caption="Sample Pack", filter="Zip Files (*.zip)"
        )
        if fname:
            self._dialog.sample_pack_fname.setText(fname)

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

        d.sample_pack_name.setText("")
        d.sample_pack_fname.setText("")
        d.sample_pack_list.clear()

        for name, pack in preferences.sample_packs.items():
            self._add_sample_pack(name, pack)

        if self._dialog.exec():
            amk_fname = Path(d.amk_fname.text())
            spcplay_fname = Path(d.spcplay_fname.text())

            packs = {}
            widget = d.sample_pack_list
            for row in range(widget.count()):
                item = widget.item(row)
                item_text = item.text().split(":")
                packs[item_text[0]] = Path(":".join(item_text[1:]))

            return PreferencesState(amk_fname, packs, spcplay_fname)

        return None

    ###########################################################################
    # Private function definitions
    ###########################################################################

    def _add_sample_pack(self, name: str, path: Path) -> None:
        self._dialog.sample_pack_list.addItem(f"{name}:{str(path)}")
