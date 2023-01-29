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

# Library imports
from PyQt6 import uic
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtWidgets import QDialog

###############################################################################
# API class definitions
###############################################################################


class Preferences:
    _dialog: QDialog
    _model: QStandardItemModel

    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self, model: QStandardItemModel):
        ui_contents = pkgutil.get_data("smw_music", "/data/preferences.ui")
        if ui_contents is None:
            raise Exception("Can't locate preferences")
        dialog = uic.loadUi(io.BytesIO(ui_contents))
        self._dialog = dialog

        pairs = [
            (dialog.select_amk_fname, dialog.amk_fname, "AMK Zip File"),
            (
                dialog.select_sample_pack_name,
                dialog.sample_pack_fname,
                "Sample pack",
            ),
        ]
        for btn, edit, caption in pairs:
            pass  # file_picker(btn, edit, False, caption, "Zip (*.zip)")

    ###########################################################################
    # API function definitions
    ###########################################################################

    def exec(self) -> None:
        self._dialog.exec()
