#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Link a file selector button with a line editor."""

###############################################################################
# Imports
###############################################################################

# Library imports
from PyQt6.QtWidgets import QFileDialog, QLineEdit, QPushButton

###############################################################################
# API function definitions
###############################################################################


def file_picker(
    button: QPushButton, edit: QLineEdit, save: bool, caption: str, filt: str
) -> None:
    def callback():
        if save:
            dlg = QFileDialog.getSaveFileName
        else:
            dlg = QFileDialog.getOpenFileName
        fname, _ = dlg(button, caption=caption, filter=filt)
        if fname:
            edit.setText(fname)

    button.clicked.connect(callback)
