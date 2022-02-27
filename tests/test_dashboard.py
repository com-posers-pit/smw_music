# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SMW Music Module Tests."""

# Functions in this module aren't part of the API, so docstrings aren't needed
# pylint: disable=missing-function-docstring

# Testing requires access to protected members to simulate UI interactions.
# pylint: disable=protected-access

# Fixtures are referenced as arguments
# pylint: disable=redefined-outer-name

# Most of the "too many arguments" errors are because of fixtures
# pylint: disable=too-many-arguments

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

from PyQt6.QtCore import Qt  # pylint: disable=import-error
from PyQt6.QtWidgets import (  # pylint: disable=import-error
    QLineEdit,
    QMessageBox,
    QSlider,
)

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


def _load_mml(fname: pathlib.Path) -> list[str]:
    # Read the result and strip out the build date/time before comparing
    with fname.open(encoding="ascii") as fobj:
        contents = fobj.readlines()

    return [x for x in contents if not x.startswith("; Built:")]


###############################################################################


def _move_dyn_slider(
    qtbot, dut: Dashboard, dyn: str, ticks: int
) -> tuple[str, str]:
    widget = dut._controller._dynamics._sliders[dyn]
    _move_slider(qtbot, widget._slider, ticks)

    return widget._display.text(), widget._control.text()


###############################################################################


def _move_slider(qtbot, slider: QSlider, ticks: int) -> None:
    key = Qt.Key.Key_Up if ticks > 0 else Qt.Key.Key_Down
    for _ in range(abs(ticks)):
        qtbot.keyPress(slider, key)
        qtbot.keyRelease(slider, key)


###############################################################################


def _panel(dut: Dashboard) -> ControlPanel:
    return dut._controller._control_panel


###############################################################################


def _set_dyn_control(
    qtbot, dut: Dashboard, dyn: str, pct: float
) -> tuple[str, int]:
    widget = dut._controller._dynamics._sliders[dyn]
    _set_edit(qtbot, widget._control, f"{pct:0.1f}\r")

    return widget._display.text(), widget._slider.value()


###############################################################################


def _set_edit(qtbot, edit: QLineEdit, txt: str) -> None:
    qtbot.keyClicks(edit, "a", modifier=Qt.KeyboardModifier.ControlModifier)
    qtbot.keyClick(edit, Qt.Key.Key_Backspace)
    qtbot.keyClicks(edit, f"{txt}\r")


###############################################################################


def _set_instr(qtbot, dashboard: Dashboard, instr: str) -> None:
    instrs = dashboard._controller._instruments
    row = instrs.currentRow()
    idx = instrs.row(instrs.findItems(instr, Qt.MatchFlag.MatchExactly)[0])
    delta = idx - row
    key = Qt.Key.Key_Down if delta > 0 else Qt.Key.Key_Up
    for _ in range(abs(delta)):
        qtbot.keyClick(instrs, key)


###############################################################################


def _set_files(
    qtbot, dut: Dashboard, src: pathlib.Path, dst: pathlib.Path
) -> None:
    _set_edit(qtbot, _panel(dut)._musicxml_picker._edit, str(src))
    _set_edit(qtbot, _panel(dut)._mml_picker._edit, str(dst))


###############################################################################


def _setup(tgt, tmp_path, qtbot, fname="GUI_Test.mxl"):
    test_dir = pathlib.Path("tests")

    src_fname = test_dir / "src" / fname
    tgt_fname = test_dir / "dst" / "ui" / tgt
    dst_fname = tmp_path / "test.mml"

    with tgt_fname.open(encoding="ascii") as fobj:
        target = fobj.readlines()

    dashboard = Dashboard()
    dashboard.show()
    qtbot.addWidget(dashboard)

    _set_files(qtbot, dashboard, src_fname, dst_fname)

    return (dashboard, target, dst_fname)


###############################################################################
# Fixture definitions
###############################################################################


@pytest.fixture
def auto_ok(monkeypatch):
    monkeypatch.setattr(
        QMessageBox, "information", lambda *_: QMessageBox.StandardButton.Yes
    )


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
def test_controls(tgt, func, qtbot, tmp_path, auto_ok):
    dashboard, target, dst_fname = _setup(tgt, tmp_path, qtbot)

    if func is not None:
        func(qtbot, dashboard)

    _generate(qtbot, dashboard)

    actual = _load_mml(dst_fname)

    assert target == actual


###############################################################################


@pytest.mark.skipif(sys.platform == "win32", reason="No qtbot on Windows")
@pytest.mark.parametrize(
    "instr, dyn, pct, expected",
    [
        ("Harpsichord", "P", 0, 90),
        ("Harpsichord", "P", 50, 90),
        ("Harpsichord", "P", 100, 90),
        ("Piano", "P", 0, 0),
        ("Piano", "P", 50, 127),
        ("Piano", "P", 100, 255),
    ],
    ids=[
        "Harp. P 0% (disabled)",
        "Harp. P 50% (disabled)",
        "Harp. P 100% (disabled)",
        "Piano P 0%",
        "Piano P 50%",
        "Piano P 100%",
    ],
)
def test_dynamics_controls(
    instr, dyn, pct, expected, qtbot, tmp_path, auto_ok
):
    dashboard, target, dst_fname = _setup("vanilla.mml", tmp_path, qtbot)

    _set_instr(qtbot, dashboard, instr)

    disp, slider = _set_dyn_control(qtbot, dashboard, dyn, pct)

    _generate(qtbot, dashboard)

    actual = _load_mml(dst_fname)

    # Pick off only the dynamics settings from the target and generated output
    target = [x for x in target if x.startswith(f'"{instr}_dyn')][0]
    actual = [x for x in actual if x.startswith(f'"{instr}_dyn')][0]

    # Confirm the displayed hex value, percent edit value, and MML output are
    # correct
    assert int("0" + disp, 16) == expected
    assert slider == expected
    assert re.sub(f"_{dyn}=..", f"_{dyn}={expected:02X}", target) == actual


###############################################################################


@pytest.mark.skipif(sys.platform == "win32", reason="No qtbot on Windows")
@pytest.mark.parametrize(
    "instr, dyn, ticks, expected",
    [
        ("Harpsichord", "MP", 0, 0x73),
        ("Harpsichord", "MP", 1, 0x74),
        ("Harpsichord", "MP", -1, 0x72),
        ("Harpsichord", "MP", 10, 0x7D),
        ("Harpsichord", "MP", -10, 0x69),
        ("Harpsichord", "MP", 120, 235),
        ("Harpsichord", "MP", -120, 0),
        ("Harpsichord", "MP", 150, 255),
        ("Harpsichord", "MF", 0, 141),
        ("Harpsichord", "MF", 20, 161),
        ("Harpsichord", "MF", -40, 101),
        ("Harpsichord", "F", 0, 179),
        ("Harpsichord", "F", 10, 179),
        ("Harpsichord", "F", -10, 179),
        ("Piano", "MP", 0, 0x73),
        ("Piano", "MP", 1, 0x74),
        ("Piano", "MP", -1, 0x72),
        ("Piano", "MP", 10, 0x7D),
        ("Piano", "MP", -10, 0x69),
        ("Piano", "MP", 120, 235),
        ("Piano", "MP", -120, 0),
        ("Piano", "MP", 150, 255),
        ("Piano", "MF", 0, 141),
        ("Piano", "MF", 20, 161),
        ("Piano", "MF", -40, 101),
        ("Piano", "F", 0, 179),
        ("Piano", "F", 10, 189),
        ("Piano", "F", -10, 169),
    ],
    ids=[
        "Harp. MP No change",
        "Harp. MP +1",
        "Harp. MP -1",
        "Harp. MP +10",
        "Harp. MP -10",
        "Harp. MP +120",
        "Harp. MP -120 (sat. at 0)",
        "Harp. MP +150 (sat. at 255)",
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
        "Piano. MP -120 (sat. at 0)",
        "Piano. MP +150 (sat. at 255)",
        "Piano. MF No change",
        "Piano. MF +20",
        "Piano. MF -40",
        "Piano. F No change",
        "Piano. F +10",
        "Piano. F -10",
    ],
)
def test_dynamics_slider(
    instr, dyn, ticks, expected, qtbot, tmp_path, auto_ok
):
    dashboard, target, dst_fname = _setup("vanilla.mml", tmp_path, qtbot)

    _set_instr(qtbot, dashboard, instr)

    disp, control = _move_dyn_slider(qtbot, dashboard, dyn, ticks)

    _generate(qtbot, dashboard)

    actual = _load_mml(dst_fname)

    # Pick off only the dynamics settings from the target and generated output
    target = [x for x in target if x.startswith(f'"{instr}_dyn')][0]
    actual = [x for x in actual if x.startswith(f'"{instr}_dyn')][0]

    # Confirm the displayed hex value, percent edit value, and MML output are
    # correct
    assert int("0" + disp, 16) == expected
    assert float(control) == pytest.approx(100 * expected / 255, abs=0.05)
    assert re.sub(f"_{dyn}=..", f"_{dyn}={expected:02X}", target) == actual


###############################################################################


def test_multiple_exports(qtbot, tmp_path, auto_ok):
    dashboard, target, dst_fname = _setup(
        "../Repeats.txt", tmp_path, qtbot, "Repeats.mxl"
    )
    _enable_loop_analysis(qtbot, dashboard)
    _enable_legato(qtbot, dashboard)

    for _ in range(4):
        _generate(qtbot, dashboard)

        actual = _load_mml(dst_fname)

        assert actual == target


###############################################################################


@pytest.mark.skipif(sys.platform == "win32", reason="No qtbot on Windows")
@pytest.mark.parametrize(
    "pct, expected",
    [
        (0, 0),
        (33, 84),
        (50, 127),
        (100, 255),
    ],
    ids=["0%", "33%", "50%", "100%"],
)
def test_volume_control(pct, expected, qtbot, tmp_path, auto_ok):
    dashboard, _, dst_fname = _setup("vanilla.mml", tmp_path, qtbot)
    widget = dashboard._controller._volume

    _set_edit(qtbot, widget._control, str(pct))
    _generate(qtbot, dashboard)

    disp = widget._display.text()
    slider = widget._slider.value()

    actual = [x for x in _load_mml(dst_fname) if x.startswith("w")][0]

    # Confirm the displayed hex value, percent edit value, and MML output are
    # correct
    assert int(disp) == expected
    assert slider == expected
    assert actual.strip() == f"w{expected}"


###############################################################################


@pytest.mark.skipif(sys.platform == "win32", reason="No qtbot on Windows")
@pytest.mark.parametrize(
    "ticks, expected",
    [
        (0, 180),
        (1, 181),
        (-1, 179),
        (10, 190),
        (-10, 170),
        (120, 255),
        (-120, 60),
        (-200, 0),
    ],
    ids=[
        "No change",
        "+1",
        "-1",
        "+10",
        "-10",
        "+120 (sat. at 255)",
        "-120",
        "-200 (sat. at 0)",
    ],
)
def test_volume_slider(ticks, expected, qtbot, tmp_path, auto_ok):
    dashboard, _, dst_fname = _setup("vanilla.mml", tmp_path, qtbot)
    widget = dashboard._controller._volume

    _move_slider(qtbot, widget._slider, ticks)
    disp = widget._display.text()
    control = widget._control.text()

    _generate(qtbot, dashboard)

    actual = [x for x in _load_mml(dst_fname) if x.startswith("w")][0]

    # Confirm the displayed hex value, percent edit value, and MML output are
    # correct
    assert int(disp) == expected
    assert float(control) == pytest.approx(100 * expected / 255, abs=0.05)
    assert actual.strip() == f"w{expected}"
