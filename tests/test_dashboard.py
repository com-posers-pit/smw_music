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
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

###############################################################################
# Project imports
###############################################################################

from smw_music.ui.dashboard import Dashboard
from smw_music.ui.panels import ControlPanel

###############################################################################
# Private function definitions
###############################################################################


def _custom_percussion(qtbot, dut: Dashboard) -> None:
    qtbot.mouseClick(_panel(dut)._custom_percussion, Qt.MouseButton.LeftButton)


###############################################################################


def _custom_samples(qtbot, dut: Dashboard) -> None:
    qtbot.mouseClick(_panel(dut)._custom_samples, Qt.MouseButton.LeftButton)


###############################################################################


def _enable_legato(qtbot, dut: Dashboard) -> None:
    qtbot.mouseClick(_panel(dut)._global_legato, Qt.MouseButton.LeftButton)


###############################################################################


def _enable_loop_analysis(qtbot, dut: Dashboard) -> None:
    qtbot.mouseClick(_panel(dut)._loop_analysis, Qt.MouseButton.LeftButton)


###############################################################################


def _enable_measure_numbers(qtbot, dut: Dashboard) -> None:
    qtbot.mouseClick(_panel(dut)._measure_numbers, Qt.MouseButton.LeftButton)


###############################################################################


def _generate(qtbot, dut: Dashboard) -> None:
    qtbot.mouseClick(_panel(dut)._generate, Qt.MouseButton.LeftButton)


###############################################################################


def _panel(dut: Dashboard) -> ControlPanel:
    return dut._controller._control_panel


###############################################################################


def _set_files(
    qtbot, dut: Dashboard, src: pathlib.Path, dst: pathlib.Path
) -> None:
    qtbot.keyClicks(_panel(dut)._musicxml_picker._edit, f"{src}\r")
    qtbot.keyClicks(_panel(dut)._mml_picker._edit, f"{dst}\r")


###############################################################################
# Test definitions
###############################################################################


@pytest.mark.skipif(sys.platform == "win32", reason="No qtbot on Windows")
@pytest.mark.parametrize(
    "tgt, func",
    [
        ("vanilla.mml", None),
        ("global_legato.mml", _enable_legato),
        ("loop.mml", _enable_loop_analysis),
        ("measure_numbers.mml", _enable_measure_numbers),
        ("custom_samples.mml", _custom_samples),
        ("custom_percussion.mml", _custom_percussion),
    ],
    ids=[
        "Vanilla Conversion",
        "Enable Legato",
        "Loop Analysis",
        "Measure Numbers",
        "Custom Samples",
        "Custom Percussion",
    ],
)
def test_gui(tgt, func, qtbot, monkeypatch, tmp_path):
    fname = "GUI_Test.mxl"
    test_dir = pathlib.Path("tests")

    src_fname = test_dir / "src" / fname
    tgt_fname = test_dir / "dst" / "ui" / tgt
    dst_fname = tmp_path / "test.mml"

    with tgt_fname.open(encoding="ascii") as fobj:
        target = fobj.readlines()

    monkeypatch.setattr(
        QMessageBox, "information", lambda *_: QMessageBox.StandardButton.Yes
    )

    dashboard = Dashboard()
    dashboard.show()
    qtbot.addWidget(dashboard)

    _set_files(qtbot, dashboard, src_fname, dst_fname)
    if func is not None:
        func(qtbot, dashboard)
    _generate(qtbot, dashboard)

    with dst_fname.open(encoding="ascii") as fobj:
        actual = [x for x in fobj.readlines() if not x.startswith("; Built:")]

    assert target == actual
