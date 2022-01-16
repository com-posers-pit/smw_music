# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Token classes extracted from MusicXML files."""

###############################################################################
# Standard Library imports
###############################################################################

from dataclasses import dataclass
from typing import List, Union

###############################################################################
# Library imports
###############################################################################

import music21  # type: ignore

###############################################################################
# Private variable/constant definitions
###############################################################################

# Music XML uses 4 for a whole note, 5 for a half note, etc.  AMK uses 1 for a
# whole note, 2 for a half note, etc.
_MUSIC_XML_DURATION = {
    4: 1,
    5: 2,
    6: 4,
    7: 8,
    8: 16,
    9: 32,
    10: 64,
}

###############################################################################
# API class definitions
###############################################################################


class Token:  # pylint: disable=too-few-public-methods
    """Base class for MusicXML->MML tokens."""


###############################################################################


class Playable:
    @property
    def measure_num(self):
        return self._measure_num

    @measure_num.setter
    def measure_num(self, val):
        self._measure_num = val

    @property
    def note_num(self):
        return self._note_num

    @note_num.setter
    def note_num(self, val):
        self._note_num = val


###############################################################################


@dataclass
class Annotation(Token):
    """
    Expressions attached to music notes.

    Parameters
    ----------
    text : str
        The expression's text

    Attributes
    ----------
    text : str
        The expression's text
    """

    text: str
    _amk_prefix = "AMK:"

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_music_xml(
        cls, elem: music21.expressions.TextExpression
    ) -> "Annotation":
        """
        Convert a Text Expression to an Annotation object.

        Parameters
        ----------
        elem : music21.expressions.TextExpression
            A music21 representation of a Text Expression.

        Return
        ------
        Annotation
            A new Annotation object with its `text` attribute set to the
            `elem`'s text content.
        """
        return cls(elem.content)

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def amk_annotation(self) -> bool:
        """Return True iff this is an annotation for AMK."""
        return self.text.startswith(self._amk_prefix)

    ###########################################################################

    @property
    def amk_text(self) -> str:
        """
        Return the text for AMK annotations, minus the AMK prefix.

        If this is not an AMK annotation, return ''.
        """
        if self.amk_annotation:
            rv = self.text.removeprefix(self._amk_prefix).strip()
        else:
            rv = ""
        return rv


###############################################################################


@dataclass
class Dynamic(Token):
    """
    Dynamics marking.

    Parameters
    ----------
    level: str
        dynamic level (pppp, ppp, pp, p, mp, mf, f, ff, fff, ffff)

    Attributes
    ----------
    level: str
        dynamic level
    """

    level: str

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_music_xml(cls, elem: music21.dynamics.Dynamic) -> "Dynamic":
        """
        Convert a MusicXML Dynamic to a Dynamic object.

        Parameters
        ----------
        elem : music21.dynamics.Dynamic
            A music21 representation of a dynamic level

        Return
        ------
        Dynamic
            A new Dynamic object with its level set to the volume scalare
            squared

        Todo
        ----
        Confirm this heuristic is good enough, or parameterize
        """
        return cls(elem.value)


###############################################################################


@dataclass
class RehearsalMark(Token):
    """
    An object representing a rehearsal mark.

    Parameters
    ----------
    mark : str
        The rehearsal mark's text

    Attributes
    ----------
    mark : str
        The rehearsal mark's text
    """

    mark: str

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_music_xml(
        cls, elem: music21.expressions.RehearsalMark
    ) -> "RehearsalMark":
        """
        Convert a music21 RehearsalMark to a RehearsalMark object.

        Parameters
        ----------
        elem : music21.expressions.RehearsalMark
            A music21 representation of a RehearsalMark

        Return
        ------
        RehearsalMark
            A new RehearsalMark object with its `mark` attribute set to the
            `elem`'s text content.
        """
        return cls(elem.content)


###############################################################################


@dataclass
class Loop(Token):
    elem: List[Token]
    loop_id: int
    repeats: int
    superloop: bool


###############################################################################


@dataclass
class LoopDelim(Token):
    """
    A user-defined loop token.

    Parameters
    ----------
    start : bool
        True iff this is the start of a loop

    Attributes
    ----------
    start : bool
        True iff this is the start of a loop
    """

    start: bool


###############################################################################


@dataclass
class LoopRef(Token):
    loop_id: int
    repeats: int


###############################################################################


@dataclass
class Measure(Token):
    """
    An object representing the start of a new measure of music.

    Parameters
    ----------
    number : int
        The measure number

    Attributes
    ----------
    number : int
        The measure number
    """

    number: int = 0


###############################################################################


@dataclass
class Note(Token, Playable):  # pylint: disable=too-many-instance-attributes
    """
    Music note.

    Parameters
    ----------
    note: str
        The note's name (a-g) with '+'/'-' appended for sharp/flat,
        respectively.
    duration: int
        The note's length
    octave: int
        The note's octave
    head: str
        Note head shape
    dots: int
        The number of dots
    tie: str
        "start" to start a tie, "stop" to end a tie, "" if no tie
    grace: bool
        True iff this is a grace note
    accent: bool
        True iff this is an accented note
    staccato: bool
        True iff this is an staccato note

    Attributes
    ----------
    note: str
        The note's name (a-g) with '+'/'-' appended for sharp/flat,
        respectively.
    duration: int
        The note's length
    octave: int
        The note's octave
    head: str
        Note head shape
    dots: int
        The number of dots
    tie: str
        "start" to start a tie, "stop" to end a tie, "" if no tie
    grace: bool
        True iff this is a grace note
    accent: bool
        True iff this is an accented note
    staccato: bool
        True iff this is an staccato note

    Todo
    ----
    Duration, octave, and tie are poorly implemented, clean this up.
    """

    name: str
    duration: int
    octave: int
    head: str
    dots: int = 0
    tie: str = ""
    grace: bool = False
    accent: bool = False
    staccato: bool = False

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_music_xml(
        cls, elem: Union[music21.note.Note, music21.note.Unpitched]
    ) -> "Note":
        """
        Convert a MusicXML note to a Note object.

        Parameters
        ----------
        elem : music21.note.Note
            A music21 representation of a musical note

        Return
        ------
        Note
            A new Note object with its attributes defined by `elem`
        """
        articulations = [type(x) for x in elem.articulations]

        if isinstance(elem, music21.note.Note):
            name = elem.name
            octave = elem.octave
        else:
            name = elem.displayPitch().name
            octave = elem.displayOctave

        accent = music21.articulations.Accent in articulations
        staccato = music21.articulations.Staccato in articulations

        return cls(
            name.lower().replace("#", "+"),
            _MUSIC_XML_DURATION[elem.duration.ordinal],
            octave - 1,
            elem.notehead,
            elem.duration.dots,
            elem.tie.type if elem.tie is not None else "",
            elem.duration.isGrace,
            accent,
            staccato,
        )


###############################################################################


@dataclass
class Repeat(Token):
    """
    A repeat bar.

    Parameters
    ----------
    start : bool
        True iff this is a "repeat start" bar

    Attributes
    ----------
    start : bool
        True iff this is a "repeat start" bar
    """

    start: bool

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_music_xml(cls, elem: music21.bar.Repeat) -> "Repeat":
        """
        Convert a MusicXML repeat to a Repeat object.

        Parameters
        ----------
        elem : music21.bar.Repeat
            A music21 representation of a repeat bar

        Return
        ------
        Repeat
            A new Repeat object with its attributes defined by `elem`
        """
        return cls(elem.direction == "start")


###############################################################################


@dataclass
class Rest(Token, Playable):
    """
    Music rest.

    Parameters
    ----------
    duration: int
        The rest's length (TODO: standardize this notion)
    dots: int
        The number of dots

    Attributes
    ----------
    duration: int
        The note's length
    dots: int
        The number of dots
    """

    duration: int
    dots: int = 0

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_music_xml(cls, elem: music21.note.Rest) -> "Rest":
        """
        Convert a MusicXML rest to a Rest object.

        Parameters
        ----------
        elem : music21.note.Rest
            A music21 representation of a musical rest

        Return
        ------
        Rest
            A new Rest object with its attributes defined by `elem`
        """
        return cls(
            _MUSIC_XML_DURATION[elem.duration.ordinal],
            elem.duration.dots,
        )


###############################################################################


@dataclass
class Slur(Token):
    """
    A slur start/stop.

    Parameters
    ----------
    start : bool
        True iff this is the start of a slur

    Attributes
    ----------
    start : bool
        True iff this is the start of a loop
    """

    start: bool


###############################################################################


@dataclass
class Triplet(Token):
    """
    A triplet start/stop.

    Parameters
    ----------
    start : bool
        True iff this is the start of a triplet

    Attributes
    ----------
    start : bool
        True iff this is the start of a triplet
    """

    start: bool
