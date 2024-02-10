# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Utilities for handling Music XML conversions."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from enum import IntEnum, StrEnum, auto, nonmember

# Library imports
from music21.pitch import Pitch

###############################################################################
# API class definitions
###############################################################################


class Dynamics(IntEnum):
    PPPP = auto()
    PPP = auto()
    PP = auto()
    P = auto()
    MP = auto()
    MF = auto()
    F = auto()
    FF = auto()
    FFF = auto()
    FFFF = auto()

    ###########################################################################

    def __str__(self) -> str:
        return self.name


###############################################################################


class NoteHead(StrEnum):
    NORMAL = "normal"
    X = "x"
    O = "o"  # noqa: E741
    PLUS = "cross"
    TENSOR = "circle-x"
    TRIUP = "triangle"
    TRIDOWN = "inverted triangle"
    SLASH = "slashed"
    BACKSLASH = "back slashed"
    DIAMOND = "diamond"

    ###########################################################################

    _SYMBOL_MAP = nonmember(
        {
            "normal": NORMAL,
            "x": X,
            "o": O,
            "+": PLUS,
            "⮾": TENSOR,
            "▲": TRIUP,
            "▼": TRIDOWN,
            "/": SLASH,
            "\\": BACKSLASH,
            "◆": DIAMOND,
        }
    )
    _SYMBOL_UNMAP = nonmember({v: k for k, v in _SYMBOL_MAP.items()})

    ###########################################################################

    @classmethod
    def from_symbol(cls, symbol: str) -> "NoteHead":
        return cls._SYMBOL_MAP[symbol]

    ###########################################################################

    @property
    def symbol(self) -> str:
        return self._SYMBOL_UNMAP[self]


###############################################################################


class SongException(Exception):
    """Parent class for MusicXML exceptions."""


###############################################################################
# API function definitions
###############################################################################


def dedupe_notes(
    notes: list[tuple[Pitch, NoteHead]]
) -> list[tuple[Pitch, NoteHead]]:
    rv: list[tuple[Pitch, NoteHead]] = []
    for in_note in notes:
        in_pitch, in_head = in_note
        for out_note in rv:
            out_pitch, out_head = out_note
            if in_pitch.isEnharmonic(out_pitch) and in_head == out_head:
                break
        else:
            rv.append(in_note)

    return rv
