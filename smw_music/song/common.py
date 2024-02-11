# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Utilities for handling Music XML conversions."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from enum import StrEnum, auto, nonmember
from typing import cast

# Library imports
from music21.pitch import Pitch

###############################################################################
# API class definitions
###############################################################################


class Dynamics(StrEnum):
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

    _NEXT = cast(
        dict["Dynamics", "Dynamics"],
        nonmember(
            {
                PPPP: PPP,
                PPP: PP,
                PP: P,
                P: MP,
                MP: MF,
                MF: F,
                F: FF,
                FF: FFF,
                FFF: FFFF,
                FFFF: FFFF,
            }
        ),
    )
    _PREV = cast(
        dict["Dynamics", "Dynamics"],
        nonmember(
            {
                PPPP: PPPP,
                PPP: PPPP,
                PP: PPP,
                P: PP,
                MP: P,
                MF: MP,
                F: MF,
                FF: F,
                FFF: FF,
                FFFF: FFF,
            }
        ),
    )

    ###########################################################################

    @property
    def next(self) -> "Dynamics":
        return self._NEXT[self]

    ###########################################################################

    @property
    def prev(self) -> "Dynamics":
        return self._PREV[self]


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

    _SYMBOL_MAP = cast(
        dict[str, "NoteHead"],
        nonmember(
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
        ),
    )
    _SYMBOL_UNMAP = cast(
        dict["NoteHead", "str"],
        nonmember({v: k for k, v in _SYMBOL_MAP.items()}),
    )

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
