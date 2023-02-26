# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Keyboard library"""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import sys
import threading
from contextlib import suppress

# Library imports
import mido
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QKeyEvent, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
)

###############################################################################


class Key(QGraphicsRectItem):
    def __init__(self, x0, y0, x1, y1, white):
        super().__init__(x0, y0, x1, y1)
        self.white = white
        self.brush = QBrush(self.color)
        self.pressed = QBrush(Qt.GlobalColor.magenta)
        self.setBrush(self.brush)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, evt):
        print(f"{self} drag enter")
        self.activate()

    def dragLeaveEvent(self, evt):
        print(f"{self} drag leave")
        self.deactivate()

    def dragMoveEvent(self, evt):
        print(f"{self} drag move")
        self.deactivate()

    def mousePressEvent(self, evt):
        print(f"{self} mouse press")
        self.activate()

    def mouseReleaseEvent(self, evt):
        print(f"{self} mouse release")
        self.deactivate()

    def activate(self):
        self.setBrush(self.pressed)
        self.update()

    def deactivate(self):
        self.setBrush(self.brush)
        self.update()

    @property
    def color(self):
        return Qt.GlobalColor.white if self.white else Qt.GlobalColor.black


###############################################################################

KEY_TABLE: dict[Qt.Key, tuple[str, int]] = {
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


class Keyboard(QGraphicsView):
    keys: dict[str, Key]
    _active: bool
    _octave: int

    ###########################################################################

    def __init__(self):
        super().__init__()

        self._setup_graphics()
        self.octave = 3
        self._active = False
        self.show()

    ###########################################################################

    def _setup_graphics(self):
        scene = QGraphicsScene(0, 0, 1500, 200)
        self.setScene(scene)

        self.pen = QPen(Qt.GlobalColor.black)
        self.pen.setWidth(1)

        dx = 16

        self.keys = {}
        letter = "c"
        octave = 0
        for n in range(75):
            key = Key(0, 0, dx, 50, True)
            key.setPos(n * dx, 0)
            key.setPen(self.pen)

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
        for n in range(74):
            offset += dx

            if (n % 7) not in [2, 6]:
                key = Key(-dx / 4, 0, dx / 2, 30, False)
                key.setPos(offset, 0)
                key.setPen(self.pen)

                scene.addItem(key)
                self.keys[f"{letter}#{octave}"] = key

            letter = chr(ord(letter) + 1)
            if letter == "h":
                letter = "a"
            if letter == "c":
                octave += 1

    ###########################################################################

    def keyPressEvent(self, evt: QKeyEvent) -> None:
        keyval = evt.key()

        if keyval == Qt.Key.Key_Escape:
            self.active = not self.active

        if self.active:
            if evt.modifiers() & Qt.KeyboardModifier.KeypadModifier:
                if keyval == Qt.Key.Key_Asterisk:
                    self.octave = min(self.octave + 1, 10)
                if keyval == Qt.Key.Key_Slash:
                    self.octave = max(self.octave - 1, 0)
            else:
                with suppress(KeyError):
                    key, offset = KEY_TABLE[Qt.Key(keyval)]
                    self.press_key(key, self.octave, offset)

    ###########################################################################

    def keyReleaseEvent(self, evt: QKeyEvent) -> None:
        if self.active:
            if not (evt.modifiers() & Qt.KeyboardModifier.KeypadModifier):
                with suppress(KeyError):
                    key, offset = KEY_TABLE[Qt.Key(evt.key())]
                    self.release_key(key, self.octave, offset)

    ###########################################################################

    def press_key(self, letter: str, octave: int, offset: int = 0):
        octave = max(min(octave + offset, 10), 0)

        with suppress(KeyError):
            self.keys[f"{letter}{octave}"].activate()

    ###########################################################################

    def release_key(self, letter: str, octave: int, offset: int = 0):
        octave = max(min(octave + offset, 10), 0)

        with suppress(KeyError):
            self.keys[f"{letter}{octave}"].deactivate()

    ###########################################################################

    @property
    def active(self) -> bool:
        return self._active

    ###########################################################################

    @active.setter
    def active(self, val: bool) -> None:
        self._active = val

    ###########################################################################

    @property
    def octave(self) -> int:
        return self._octave

    ###########################################################################

    @octave.setter
    def octave(self, val: int) -> None:
        self._octave = max(min(val, 10), 0)


###############################################################################

app = QApplication(sys.argv)
keyboard = Keyboard()


def convert(ival: int) -> (str, int):
    octave, key = divmod(ival, 12)
    keyname = [
        "c",
        "c#",
        "d",
        "d#",
        "e",
        "f",
        "f#",
        "g",
        "g#",
        "a",
        "a#",
        "b",
    ][key]
    return keyname, octave


def poll(keyboard: Keyboard) -> None:
    in_fname = ""
    out_fname = "beer"

    with mido.open_input(in_fname) as inport, mido.open_output(
        out_fname, virtual=True
    ) as outport:
        for msg in inport:
            outport.send(msg)
            if msg.type == "note_on":
                keyboard.press_key(*convert(msg.note))
            elif msg.type == "note_off":
                keyboard.release_key(*convert(msg.note))


thread = threading.Thread(target=poll, args=(keyboard,), daemon=True)
# thread.start()

app.exec()
