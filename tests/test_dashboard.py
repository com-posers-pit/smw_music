# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SMW Music Module Tests."""

###############################################################################
# Standard library imports
###############################################################################

import pathlib
import sys

###############################################################################
# Library imports
###############################################################################

import pytest

from PyQt6 import QtCore
from PyQt6.QtWidgets import QMessageBox

###############################################################################
# Project imports
###############################################################################

from smw_music.ui.dashboard import Dashboard

###############################################################################
# Test definitions
###############################################################################


@pytest.mark.skipif(sys.platform == "win32", reason="No qtbot on Windows")
def test_gui(qtbot, monkeypatch):
    src = "Articulations.mxl"
    dst = "Articulations.txt"

    test_dir = pathlib.Path("tests")
    fname = test_dir / "dst" / dst

    with open(fname, "r", encoding="ascii") as fobj:
        target = fobj.readlines()

    fname = test_dir / "src" / src

    monkeypatch.setattr(
        QMessageBox, "information", lambda *_: QMessageBox.StandardButton.Yes
    )

    dashboard = Dashboard()
    dashboard.show()
    qtbot.addWidget(dashboard)

    panel = dashboard._controller._control_panel
    qtbot.keyClicks(panel._musicxml_picker._edit, str(fname) + "\r")
    qtbot.keyClicks(panel._mml_picker._edit, "/tmp/test.mml\r")
    qtbot.mouseClick(panel._global_legato, QtCore.Qt.MouseButton.LeftButton)
    qtbot.mouseClick(panel._generate, QtCore.Qt.MouseButton.LeftButton)

    with open("/tmp/test.mml", encoding="ascii") as fobj:
        actual = [x for x in fobj.readlines() if not x.startswith("; Built:")]

    assert target == actual
