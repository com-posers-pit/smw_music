# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SMW Music Module Tests."""

###############################################################################
# Standard library imports
###############################################################################

import pathlib
import re
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


def _set_dyn_slider(qtbot, dut: Dashboard, dyn: str, ticks: int) -> str:
    widget = dut._controller._dynamics._sliders[dyn]
    slider = widget._slider
    key = Qt.Key.Key_Up if ticks > 0 else Qt.Key.Key_Down
    for _ in range(abs(ticks)):
        qtbot.keyPress(slider, key)
        qtbot.keyRelease(slider, key)

    return widget._display.text(), widget._control.text()


###############################################################################
# Fixture definitions
###############################################################################


@pytest.fixture
def setup(request, tmp_path, qtbot, monkeypatch):
    tgt = request.param

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

    return (dashboard, target, dst_fname)


###############################################################################
# Test definitions
###############################################################################


@pytest.mark.skipif(sys.platform == "win32", reason="No qtbot on Windows")
@pytest.mark.parametrize(
    "setup, func",
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
    indirect=["setup"],
)
def test_controls(setup, func, qtbot):
    dashboard, target, dst_fname = setup

    if func is not None:
        func(qtbot, dashboard)

    _generate(qtbot, dashboard)

    # Read the result and strip out the build date/time before comparing
    with dst_fname.open(encoding="ascii") as fobj:
        actual = [x for x in fobj.readlines() if not x.startswith("; Built:")]

    assert target == actual


###############################################################################


@pytest.mark.skipif(sys.platform == "win32", reason="No qtbot on Windows")
@pytest.mark.parametrize(
    "setup, instr, dyn, ticks, expected",
    [
        ("vanilla.mml", "Harpsichord", "PPPP", 0, 0x1A),
        ("vanilla.mml", "Harpsichord", "PPP", 0, 0x26),
        ("vanilla.mml", "Harpsichord", "PP", 0, 0x40),
        ("vanilla.mml", "Harpsichord", "P", 0, 0x5A),
        ("vanilla.mml", "Harpsichord", "MP", 0, 0x73),
        ("vanilla.mml", "Harpsichord", "MF", 0, 0x8D),
        ("vanilla.mml", "Harpsichord", "F", 0, 0xB3),
        ("vanilla.mml", "Harpsichord", "FF", 0, 0xD9),
        ("vanilla.mml", "Harpsichord", "FFF", 0, 0xE6),
        ("vanilla.mml", "Harpsichord", "FFFF", 0, 0xF5),
        ("vanilla.mml", "Harpsichord", "MP", 0, 0x73),
        ("vanilla.mml", "Harpsichord", "MP", 1, 0x74),
        ("vanilla.mml", "Harpsichord", "MP", -1, 0x72),
        ("vanilla.mml", "Harpsichord", "MP", 10, 0x7D),
        ("vanilla.mml", "Harpsichord", "MP", -10, 0x69),
        ("vanilla.mml", "Harpsichord", "MP", 120, 235),
        ("vanilla.mml", "Harpsichord", "MP", -120, 0),
        ("vanilla.mml", "Harpsichord", "MP", 150, 255),
        ("vanilla.mml", "Harpsichord", "MF", 0, 141),
        ("vanilla.mml", "Harpsichord", "MF", 20, 161),
        ("vanilla.mml", "Harpsichord", "MF", -40, 101),
        ("vanilla.mml", "Harpsichord", "F", 0, 179),
        ("vanilla.mml", "Harpsichord", "F", 10, 179),
        ("vanilla.mml", "Harpsichord", "F", -10, 179),
        ("vanilla.mml", "Piano", "MP", 0, 0x73),
        ("vanilla.mml", "Piano", "MP", 1, 0x74),
        ("vanilla.mml", "Piano", "MP", -1, 0x72),
        ("vanilla.mml", "Piano", "MP", 10, 0x7D),
        ("vanilla.mml", "Piano", "MP", -10, 0x69),
        ("vanilla.mml", "Piano", "MP", 120, 235),
        ("vanilla.mml", "Piano", "MP", -120, 0),
        ("vanilla.mml", "Piano", "MP", 150, 255),
        ("vanilla.mml", "Piano", "MF", 0, 141),
        ("vanilla.mml", "Piano", "MF", 20, 161),
        ("vanilla.mml", "Piano", "MF", -40, 101),
        ("vanilla.mml", "Piano", "F", 0, 179),
        ("vanilla.mml", "Piano", "F", 10, 189),
        ("vanilla.mml", "Piano", "F", -10, 169),
    ],
    ids=[
        "Harp. Base PPPP",
        "Harp. Base PPP",
        "Harp. Base PP",
        "Harp. Base P",
        "Harp. Base MP",
        "Harp. Base MF",
        "Harp. Base F",
        "Harp. Base FF",
        "Harp. Base FFF",
        "Harp. Base FFFF",
        "Harp. MP No change",
        "Harp. MP +1",
        "Harp. MP -1",
        "Harp. MP +10",
        "Harp. MP -10",
        "Harp. MP +120",
        "Harp. MP -120 (saturate at 0)",
        "Harp. MP +150 (saturate at k55)",
        "Harp. MF No change",
        "Harp. MF +20",
        "Harp. MF -40",
        "Harp. F No change",
        "Harp. F +10 (Unused)",
        "Harp. F -10 (Unused)",
        "Piano. MP No change",
        "Piano. MP +1",
        "Piano. MP -1",
        "Piano. MP +10",
        "Piano. MP -10",
        "Piano. MP +120",
        "Piano. MP -120 (saturate at 0)",
        "Piano. MP +150 (saturate at k55)",
        "Piano. MF No change",
        "Piano. MF +20",
        "Piano. MF -40",
        "Piano. F No change",
        "Piano. F +10",
        "Piano. F -10",
    ],
    indirect=["setup"],
)
def test_dynamics_slider(setup, instr, dyn, ticks, expected, qtbot):
    dashboard, target, dst_fname = setup

    instrs = dashboard._controller._instruments
    idxs = instrs.findItems(instr, Qt.MatchFlag.MatchExactly)
    instrs.setCurrentItem(idxs[0])

    disp, control = _set_dyn_slider(qtbot, dashboard, dyn, ticks)

    _generate(qtbot, dashboard)

    # Pick off only the dynamics settings from the target and generated output
    target = [x for x in target if x.startswith(f'"{instr}_dyn')][0]
    with dst_fname.open(encoding="ascii") as fobj:
        act = [x for x in fobj.readlines() if x.startswith(f'"{instr}_dyn')][0]

    # Confirm the displayed hex value, percent edit value, and MML output are
    # correct
    assert int("0" + disp, 16) == expected
    assert float(control) == pytest.approx(100 * expected / 255, rel=1e-3)
    assert re.sub(f"_{dyn}=..", f"_{dyn}={expected:02X}", target) == act
