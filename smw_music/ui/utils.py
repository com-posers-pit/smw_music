# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

###############################################################################
# Imports
###############################################################################

# Standard library imports
from enum import Enum

# Library imports
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QCheckBox

###############################################################################
# API class definitions
###############################################################################


# https://www.oberlo.com/blog/color-combinations-cheat-sheet
class Color(Enum):
    BLACK = QColor("#000000")

    GOLD = QColor("#E1A730")
    IVORY = QColor("#E0E3D7")
    BLUE_GROTTO = QColor("#2879C0")
    CHILI_PEPPER = QColor("#AB3910")

    MIDNIGHT_BLUE = QColor("#284E60")
    ORANGE = QColor("#F99845")
    BLUE_GRAY = QColor("#63AAC0")
    HOT_PINK = QColor("#D95980")


###############################################################################
# API function definitions
###############################################################################


def is_checked(checkbox: QCheckBox) -> bool:
    return checkbox.checkState() == Qt.CheckState.Checked


###############################################################################


def to_checkstate(checked: bool) -> Qt.CheckState:
    return Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
