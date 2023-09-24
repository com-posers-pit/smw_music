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
from PyQt6.QtCore import QEvent, QObject, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QKeyEvent, QPen
from PyQt6.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneDragDropEvent,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
    QWidget,
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

_KEYS_PER_OCTAVE = 12

###############################################################################
# Private function definitions
###############################################################################


def _decode_key_idx(idx: int) -> tuple[str, int]:
    octave, key = divmod(idx, _KEYS_PER_OCTAVE)
    names = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]
    return (names[key], octave + 1)


###############################################################################


def _is_key_white(idx: int) -> bool:
    _, key = divmod(idx, _KEYS_PER_OCTAVE)
    return key in [0, 2, 4, 5, 7, 9, 11]


###############################################################################
# Private class definitions
###############################################################################


class _Key(QGraphicsRectItem):
    is_white: bool

    _brush: QBrush
    _key_off: Callable[[], None]
    _key_on: Callable[[], None]
    _pressed_brush: QBrush

    ###########################################################################

    def __init__(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        is_white: bool,
        key_on: Callable[[], None],
        key_off: Callable[[], None],
    ) -> None:
        super().__init__(x0, y0, x1, y1)

        self.is_white = is_white
        self._brush = QBrush(self.color)
        self._key_off = key_off
        self._key_on = key_on
        self._pressed_brush = QBrush(Qt.GlobalColor.cyan)

        self.setBrush(self._brush)
        self.setAcceptDrops(True)

    ###########################################################################
    # API method definitions
    ###########################################################################

    def press(self) -> None:
        self.setBrush(self._pressed_brush)
        self.update()

    ###########################################################################

    def release(self) -> None:
        self.setBrush(self._brush)
        self.update()

    ###########################################################################
    # Event handler definitions
    ###########################################################################

    def dragEnterEvent(self, _: QGraphicsSceneDragDropEvent) -> None:
        self._key_on()

    ###########################################################################

    def dragLeaveEvent(self, _: QGraphicsSceneDragDropEvent) -> None:
        self._key_off()

    ###########################################################################

    def dragMoveEvent(self, _: QGraphicsSceneDragDropEvent) -> None:
        self._key_off()

    ###########################################################################

    def mousePressEvent(self, _: QGraphicsSceneMouseEvent) -> None:
        self._key_on()

    ###########################################################################

    def mouseReleaseEvent(self, _: QGraphicsSceneMouseEvent) -> None:
        self._key_off()

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def color(self) -> Qt.GlobalColor:
        return Qt.GlobalColor.white if self.is_white else Qt.GlobalColor.black


###############################################################################
# API class definitions
###############################################################################


class Keyboard(QGraphicsView):
    key_on = pyqtSignal(
        (str, int), arguments=["note", "octave"]  # type: ignore[call-arg]
    )
    key_off = pyqtSignal(
        (str, int), arguments=["note", "octave"]  # type: ignore[call-arg]
    )

    nkeys: int

    _active: bool
    _bg: QGraphicsRectItem
    _keys: dict[tuple[str, int], _Key]
    _key_height: int
    _key_width: int
    _octave: int
    _padding: int
    _pressed: None | tuple[str, int]

    ###########################################################################

    def __init__(
        self,
        parent: QWidget | None = None,
        nkeys: int = 60,
        key_width: int = 16,
        key_height: int = 50,
        padding: int = 5,
    ) -> None:
        super().__init__(parent)

        self.nkeys = nkeys
        self._key_width = key_width
        self._key_height = key_height
        self._padding = padding

        self._setup_graphics()

        self.octave = 2
        self.active = False
        self._pressed = None

        self.show()

    ###########################################################################
    # API method definitions
    ###########################################################################

    def press_key(self, letter: str, octave: int) -> None:
        if self._pressed is None:
            self._pressed = (letter, octave)

            octave = self._clip_octave(octave)

            with suppress(KeyError):
                self._keys[(letter, octave)].press()
                self.key_on.emit(letter, octave)

    ###########################################################################

    def release_key(self, letter: str, octave: int) -> None:
        if self._pressed == (letter, octave):
            octave = self._clip_octave(octave)

            with suppress(KeyError):
                self._keys[(letter, octave)].release()
                self.key_off.emit(letter, octave)

            self._pressed = None

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _clip_octave(self, octave: int) -> int:
        return max(min(octave, self.octaves), 1)

    ###########################################################################

    def _setup_bg(self) -> None:
        # Creates the highlighted background when active
        active_width = 10
        pen = QPen(Qt.GlobalColor.red)
        pen.setWidth(active_width)

        width = self.white_keys * self._key_width
        self._bg = QGraphicsRectItem(0, 0, width, self._key_height)
        self._bg.setPen(pen)
        self._bg.setPos(self._padding, 0)
        self.scene().addItem(self._bg)

    ###########################################################################

    def _setup_graphics(self) -> None:
        # Scrollbars bad.  Go away.
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self._setup_scene()
        self._setup_bg()
        self._setup_keyboard()

    ###########################################################################

    def _setup_keyboard(self) -> None:
        pen = QPen(Qt.GlobalColor.black)
        pen.setWidth(1)

        self._keys = {}
        last_key: _Key | None = None

        width = self._key_width
        height = self._key_height

        key_pos = 0

        for n in range(self.nkeys):
            # Define key event callbacks
            letter, octave = _decode_key_idx(n)
            key_on = partial(self.press_key, letter, octave)
            key_off = partial(self.release_key, letter, octave)

            is_white = _is_key_white(n)

            # Lays out key geometry
            if is_white:
                x0, y0, x1, y1 = 0, 0, width, height
            else:
                x0, y0, x1, y1 = -width // 4, 0, width // 2, 3 * height // 5

            # Creates and draws a key
            key = _Key(x0, y0, x1, y1, is_white, key_on, key_off)
            key.setPos(self._padding + key_pos, 0)
            key.setPen(pen)

            self.scene().addItem(key)
            self._keys[(letter, octave)] = key

            # This shifts the key position every time a white key is placed and
            # sets the Z ordering so black keys are on top
            if is_white:
                key_pos += width
                if last_key:
                    key.stackBefore(last_key)

            last_key = key

    ###########################################################################

    def _setup_scene(self) -> None:
        width = 3 * self._padding + self.white_keys * self._key_width

        scene = QGraphicsScene(0, 0, width, self._key_height)
        self.setScene(scene)

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
        self._octave = self._clip_octave(val)

    ###########################################################################

    @property
    def octaves(self) -> int:
        return self.nkeys // _KEYS_PER_OCTAVE

    ###########################################################################

    @property
    def white_keys(self) -> int:
        octaves, leftover = divmod(self.nkeys, _KEYS_PER_OCTAVE)
        match leftover:
            case 0:
                leftover = 0
            case [1, 2]:
                leftover = 1
            case [3, 4]:
                leftover = 2
            case 5:
                leftover = 3
            case [6, 7]:
                leftover = 4
            case [8, 9]:
                leftover = 5
            case [10, 11]:
                leftover = 6

        return 7 * octaves + leftover


###############################################################################


class KeyboardEventFilter(QObject):
    def __init__(self, keyboard: Keyboard) -> None:
        super().__init__()
        self._kbd = keyboard
        self._playing = False

    ###########################################################################

    def eventFilter(self, obj: QObject, evt: QEvent) -> bool:
        # Guard clauses
        if not isinstance(evt, QKeyEvent):
            return False

        # Autorepeat is the devil
        if evt.isAutoRepeat():
            return True

        match evt.type():
            case QKeyEvent.Type.KeyPress:
                return self._handle_keypress(evt)
            case QKeyEvent.Type.KeyRelease:
                return self._handle_keyrelease(evt)

        return False

    ###########################################################################

    def _handle_keypress(self, evt: QKeyEvent) -> bool:
        if self._playing:
            return False

        handled = False
        keyval = evt.key()

        # Escape toggles keyboard active state
        if keyval == Qt.Key.Key_Escape:
            self._kbd.active = not self._kbd.active
            handled = True

        # While active
        if self._kbd.active:
            if evt.modifiers() & Qt.KeyboardModifier.KeypadModifier:
                # If it's a keypad '*' or '/', change the octave
                if keyval == Qt.Key.Key_Asterisk:
                    self._kbd.octave += 1
                    handled = True
                if keyval == Qt.Key.Key_Slash:
                    self._kbd.octave -= 1
                    handled = True
            else:
                # Otherwise try to play a note
                with suppress(KeyError):
                    key, offset = _KEY_TABLE[Qt.Key(keyval)]
                    self._playing = True
                    self._kbd.press_key(key, self._kbd.octave + offset)
                    handled = True

        return handled

    ###########################################################################

    def _handle_keyrelease(self, evt: QKeyEvent) -> bool:
        if not self._playing:
            return False

        handled = False

        if self._kbd.active:
            with suppress(KeyError):
                key, offset = _KEY_TABLE[Qt.Key(evt.key())]
                self._playing = False
                self._kbd.release_key(key, self._kbd.octave + offset)
                handled = True

        return handled
