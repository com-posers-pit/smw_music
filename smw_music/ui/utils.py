# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

###############################################################################
# Imports
###############################################################################

# Standard library imports
import os
from pathlib import Path

# Library imports
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox

###############################################################################
# API function definitions
###############################################################################


def is_checked(checkbox: QCheckBox) -> bool:
    return checkbox.checkState() == Qt.CheckState.Checked


###############################################################################


# https://www.smwcentral.net/?p=viewthread&t=98793&page=1&pid=1579851#p1579851
def make_vis_dir(path: Path) -> None:
    os.makedirs(path / "Visualizations", exist_ok=True)


###############################################################################


def to_checkstate(checked: bool) -> Qt.CheckState:
    return Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
