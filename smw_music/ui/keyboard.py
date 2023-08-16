# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Keyboard library"""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from contextlib import suppress
from functools import partial
from typing import Callable

# Library imports
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QKeyEvent, QPen
from PyQt6.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneDragDropEvent,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
)

###############################################################################
# Private constant definitions
###############################################################################

_KEY_TABLE = {
    Qt.Key.Key_Z: ("c", 0),
    Qt.Key.Key_S: ("c#", 0),
    Qt.Key.Key_X: ("d", 0),
    Qt.Key.Key_D: ("d#", 0),
    Qt.Key.Key_C: ("e", 0),
    Qt.Key.Key_V: ("f", 0),
    Qt.Key.Key_G: ("f#", 0),
    Qt.Key.Key_B: ("g", 0),
    Qt.Key.Key_H: ("g#", 0),
    Qt.Key.Key_N: ("a", 0),
    Qt.Key.Key_J: ("a#", 0),
    Qt.Key.Key_M: ("b", 0),
    #
    Qt.Key.Key_Comma: ("c", 1),
    Qt.Key.Key_L: ("c#", 1),
    Qt.Key.Key_Period: ("d", 1),
    Qt.Key.Key_Semicolon: ("d#", 1),
    Qt.Key.Key_Slash: ("e", 1),
    #
    Qt.Key.Key_Q: ("c", 1),
    Qt.Key.Key_2: ("c#", 1),
    Qt.Key.Key_W: ("d", 1),
    Qt.Key.Key_3: ("d#", 1),
    Qt.Key.Key_E: ("e", 1),
    Qt.Key.Key_R: ("f", 1),
    Qt.Key.Key_5: ("f#", 1),
    Qt.Key.Key_T: ("g", 1),
    Qt.Key.Key_6: ("g#", 1),
    Qt.Key.Key_Y: ("a", 1),
    Qt.Key.Key_7: ("a#", 1),
    Qt.Key.Key_U: ("b", 1),
    #
    Qt.Key.Key_I: ("c", 2),
    Qt.Key.Key_9: ("c#", 2),
    Qt.Key.Key_O: ("d", 2),
    Qt.Key.Key_0: ("d#", 2),
    Qt.Key.Key_P: ("e", 2),
    Qt.Key.Key_BracketLeft: ("f", 2),
    Qt.Key.Key_Equal: ("f#", 2),
    Qt.Key.Key_BracketRight: ("g", 2),
}


###############################################################################
# Private class definitions
###############################################################################


class _Key(QGraphicsRectItem):
    def __init__(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        white: bool,
        key_on: Callable[[], None],
        key_off: Callable[[], None],
    ) -> None:
        super().__init__(x0, y0, x1, y1)
        self.white = white
        self._brush = QBrush(self.color)
        self._key_on = key_on
        self._key_off = key_off
        self.pressed = QBrush(Qt.GlobalColor.cyan)
        self.setBrush(self._brush)
        self.setAcceptDrops(True)

    ###########################################################################
    # API method definitions
    ###########################################################################

    def activate(self) -> None:
        self.setBrush(self.pressed)
        self._key_on()
        self.update()

    ###########################################################################

    def deactivate(self) -> None:
        self.setBrush(self._brush)
        self._key_off()
        self.update()

    ###########################################################################
    # Event handler definitions
    ###########################################################################

    def dragEnterEvent(self, _: QGraphicsSceneDragDropEvent) -> None:
        self.activate()

    ###########################################################################

    def dragLeaveEvent(self, _: QGraphicsSceneDragDropEvent) -> None:
        self.deactivate()

    ###########################################################################

    def dragMoveEvent(self, _: QGraphicsSceneDragDropEvent) -> None:
        self.deactivate()

    ###########################################################################

    def mousePressEvent(self, _: QGraphicsSceneMouseEvent) -> None:
        self.activate()

    ###########################################################################

    def mouseReleaseEvent(self, _: QGraphicsSceneMouseEvent) -> None:
        self.deactivate()

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def color(self) -> Qt.GlobalColor:
        return Qt.GlobalColor.white if self.white else Qt.GlobalColor.black


###############################################################################
# API class definitions
###############################################################################


class Keyboard(QGraphicsView):
    key_on = pyqtSignal(str, int)
    key_off = pyqtSignal(str, int)

    keys: dict[str, _Key]

    _active: bool
    _bg = QGraphicsRectItem
    _octave: int
    _pen: QPen

    ###########################################################################

    def __init__(self) -> None:
        super().__init__()

        self._setup_graphics()

        self.octave = 2
        self.active = False

        self.show()

    ###########################################################################
    # API method definitions
    ###########################################################################

    def press_key(self, letter: str, octave: int, offset: int = 0) -> None:
        octave = max(min(octave + offset, 10), 0)

        with suppress(KeyError):
            self.keys[f"{letter}{octave}"].activate()

    ###########################################################################

    def release_key(self, letter: str, octave: int, offset: int = 0) -> None:
        octave = max(min(octave + offset, 10), 0)

        with suppress(KeyError):
            self.keys[f"{letter}{octave}"].deactivate()

    ###########################################################################
    # Event handler definitions
    ###########################################################################

    def keyPressEvent(self, evt: QKeyEvent) -> None:
        if evt.isAutoRepeat():
            return

        keyval = evt.key()

        if keyval == Qt.Key.Key_Escape:
            self.active = not self.active

        if self.active:
            if evt.modifiers() & Qt.KeyboardModifier.KeypadModifier:
                if keyval == Qt.Key.Key_Asterisk:
                    self.octave += 1
                if keyval == Qt.Key.Key_Slash:
                    self.octave -= 1
            else:
                with suppress(KeyError):
                    key, offset = _KEY_TABLE[Qt.Key(keyval)]
                    self.press_key(key, self.octave, offset)

    ###########################################################################

    def keyReleaseEvent(self, evt: QKeyEvent) -> None:
        if evt.isAutoRepeat():
            return

        if self.active:
            if not (evt.modifiers() & Qt.KeyboardModifier.KeypadModifier):
                with suppress(KeyError):
                    key, offset = _KEY_TABLE[Qt.Key(evt.key())]
                    self.release_key(key, self.octave, offset)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _setup_bg(self) -> None:
        white_keys = 36
        key_width = 16
        key_height = 50

        bg_pen = QPen(Qt.GlobalColor.red)
        bg_pen.setWidth(5)

        self._bg = QGraphicsRectItem(
            2, 0, 5 + white_keys * key_width, key_height
        )
        self._bg.setPen(bg_pen)
        self.scene().addItem(self._bg)

    ###########################################################################

    def _setup_graphics(self) -> None:
        white_keys = 36
        key_width = 16
        key_height = 50

        scene = QGraphicsScene(0, 0, 30 + white_keys * key_width, key_height)
        self.setScene(scene)

        self._setup_bg()

        self._pen = QPen(Qt.GlobalColor.black)
        self._pen.setWidth(1)

        self.keys = {}
        letter = "c"
        octave = 0
        for n in range(white_keys):
            key_on = partial(self.key_on.emit, letter, octave)
            key_off = partial(self.key_off.emit, letter, octave)
            key = _Key(0, 0, key_width, key_height, True, key_on, key_off)
            key.setPos(5 + n * key_width, 0)
            key.setPen(self._pen)

            scene.addItem(key)
            self.keys[f"{letter}{octave}"] = key
            letter = chr(ord(letter) + 1)
            if letter == "h":
                letter = "a"
            if letter == "c":
                octave += 1

        offset = 0
        letter = "c"
        octave = 0
        for n in range(white_keys - 1):
            offset += key_width

            if (n % 7) not in [2, 6]:
                left = -key_width // 4
                width = key_width // 2
                height = 3 * key_height // 5
                key_on = partial(self.key_on.emit, letter, octave)
                key_off = partial(self.key_off.emit, letter, octave)

                key = _Key(left, 0, width, height, False, key_on, key_off)
                key.setPos(5 + offset, 0)
                key.setPen(self._pen)

                scene.addItem(key)
                self.keys[f"{letter}#{octave}"] = key

            letter = chr(ord(letter) + 1)
            if letter == "h":
                letter = "a"
            if letter == "c":
                octave += 1

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def active(self) -> bool:
        return self._active

    ###########################################################################

    @active.setter
    def active(self, val: bool) -> None:
        self._active = val
        self._bg.setVisible(val)

    ###########################################################################

    @property
    def octave(self) -> int:
        return self._octave

    ###########################################################################

    @octave.setter
    def octave(self, val: int) -> None:
        self._octave = max(min(val, 6), 0)
