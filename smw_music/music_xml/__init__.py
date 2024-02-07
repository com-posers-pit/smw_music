# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Utilities for handling Music XML conversions."""

###############################################################################
# Imports
###############################################################################

from .shared import MusicXmlException
from .tokens import (
    Advanced,
    Annotation,
    Artic,
    Clef,
    Comment,
    CrescDelim,
    Crescendo,
    Dynamic,
    Error,
    Instrument,
    Loop,
    LoopDelim,
    LoopRef,
    Measure,
    Note,
    Playable,
    RehearsalMark,
    Repeat,
    Rest,
    Slur,
    Tempo,
    Token,
    Triplet,
    flatten,
)

###############################################################################
# API declaration
###############################################################################

__all__ = [
    "MusicXmlException",
    "Advanced",
    "Annotation",
    "Artic",
    "Clef",
    "Comment",
    "CrescDelim",
    "Crescendo",
    "Dynamic",
    "Error",
    "Instrument",
    "Loop",
    "LoopDelim",
    "LoopRef",
    "Measure",
    "Note",
    "Playable",
    "RehearsalMark",
    "Repeat",
    "Rest",
    "Slur",
    "Tempo",
    "Token",
    "Triplet",
    "flatten",
]
