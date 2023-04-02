# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

###############################################################################
# Imports
###############################################################################

# Library imports
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox

###############################################################################
# API function definitions
###############################################################################


def is_checked(checkbox: QCheckBox) -> bool:
    return checkbox.checkState() == Qt.CheckState.Checked


###############################################################################


def to_checkstate(checked: bool) -> Qt.CheckState:
    return Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
