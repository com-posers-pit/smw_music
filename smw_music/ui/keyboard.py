# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
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

KEY_TABLE: dict[Qt.Key, str] = {
    Qt.Key.Key_Q: "c",
    Qt.Key.Key_2: "c#",
    Qt.Key.Key_W: "d",
    Qt.Key.Key_3: "d#",
    Qt.Key.Key_E: "e",
    Qt.Key.Key_R: "f",
    Qt.Key.Key_5: "f#",
    Qt.Key.Key_T: "g",
    Qt.Key.Key_6: "g#",
    Qt.Key.Key_Y: "a",
    Qt.Key.Key_7: "a#",
    Qt.Key.Key_U: "b",
}


class Keyboard(QGraphicsView):
    keys: dict[str, Key]
    _active: bool

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
            if keyval == Qt.Key.Key_Up:
                self.octave = min(self.octave + 1, 10)
            if keyval == Qt.Key.Key_Down:
                self.octave = max(self.octave - 1, 0)

            with suppress(KeyError):
                key = KEY_TABLE[keyval]
                self.press_key(key, self.octave)

    ###########################################################################

    def keyReleaseEvent(self, evt: QKeyEvent) -> None:
        if self.active:
            with suppress(KeyError):
                key = KEY_TABLE[evt.key()]
                self.release_key(key, self.octave)

    ###########################################################################

    def press_key(self, letter: str, octave: int):
        with suppress(KeyError):
            self.keys[f"{letter}{octave}"].activate()

    ###########################################################################

    def release_key(self, letter: str, octave: int):
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
    fname = ""

    with mido.open_input(fname) as inport:
        for msg in inport:
            if msg.type == "note_on":
                keyboard.press_key(*convert(msg.note))
            elif msg.type == "note_off":
                keyboard.release_key(*convert(msg.note))


thread = threading.Thread(target=poll, args=(keyboard,), daemon=True)
thread.start()

app.exec()
