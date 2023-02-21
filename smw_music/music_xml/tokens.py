# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Token classes extracted from MusicXML files."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass
from enum import Enum, auto

# Library imports
import music21

# Package imports
from smw_music.music_xml.shared import MusicXmlException

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
# Private function definitions
###############################################################################


def _get_duration(elem: music21.note.GeneralNote) -> int:
    duration = elem.duration.ordinal
    if isinstance(duration, int):
        rv = _MUSIC_XML_DURATION.get(duration, 0)
    else:
        rv = 0

    return rv


###############################################################################
# API constant definitions
###############################################################################

# Weinberg:
# http://www.normanweinberg.com/uploads/8/1/6/4/81640608/940506pn_guildines_for_drumset.pdf
PERCUSSION_MAP = {
    "x": {
        "c6": "CR3_",
        "b5": "CR2_",
        "a5": "CR",
        "g5": "CH",
        "f5": "RD",
        "e5": "OH",
        "d5": "RD2_",
    },
    "normal": {
        "e5": "HT",
        "d5": "MT",
        "c5": "SN",
        "a4": "LT",
        "f4": "KD",
    },
}

###############################################################################
# API function definitions
###############################################################################


def flatten(tokens: list["Token"]) -> list["Token"]:
    rv: list["Token"] = []
    for token in tokens:
        if isinstance(token, Loop):
            rv.extend(flatten(token.tokens))
        else:
            rv.append(token)
    return rv


###############################################################################
# API class definitions
###############################################################################


class Artic(Enum):
    NORMAL = auto()
    ACCENT = auto()
    STACCATO = auto()
    ACCSTAC = auto()


###############################################################################


class Comment:
    pass


###############################################################################


class Playable:
    measure_num: int
    note_num: int
    duration: int

    ###########################################################################

    def duration_check(self) -> list[str]:
        msgs = []
        if self.duration == 0:
            msg = f"Unsupported note #{self.note_num} in "
            msg += f"Measure {self.measure_num}"
            msgs.append(msg)

        return msgs


###############################################################################


class Token:
    """Base class for MusicXML->MML tokens."""


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


###############################################################################


@dataclass
class CrescDelim(Token):
    """
    A crescendo delimiter.

    Parameters
    ----------
    start : bool
        True iff this is the start of a loop
    cresc: bool
        True if this is a crescendo; False if a diminuendo.

    Attributes
    ----------
    start : bool
        True iff this is the start of a loop
    cresc: bool
        True if this is a crescendo; False if a diminuendo.
    """

    start: bool
    cresc: bool


###############################################################################


@dataclass
class Crescendo(Token):
    """
    Crescendo/decrescendo

    Parameters
    ----------
    duration: int
        Crecendo length, in beats
    target: str
        Target dynamic
    cresc: bool
        True if this is a crescendo; False if a diminuendo.


    Attributes
    ----------
    duration: int
        Crecendo length, in beats
    target: str
        Target dynamic
    cresc: bool
        True if this is a crescendo; False if a diminuendo.
    """

    duration: int
    target: str
    cresc: bool


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

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __post_init__(self) -> None:
        dyn = self.level
        if dyn.lower() not in [
            "pppp",
            "ppp",
            "pp",
            "p",
            "mp",
            "mf",
            "f",
            "ff",
            "fff",
            "ffff",
        ]:
            raise MusicXmlException(f"Invalid dynamic level {dyn}")

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def down(self) -> str:
        return {
            "pppp": "pppp",
            "ppp": "pppp",
            "pp": "ppp",
            "p": "pp",
            "mp": "p",
            "mf": "mp",
            "f": "mf",
            "ff": "f",
            "fff": "ff",
            "ffff": "fff",
        }[self.level]

    ###########################################################################

    @property
    def up(self) -> str:
        return {
            "pppp": "ppp",
            "ppp": "pp",
            "pp": "p",
            "p": "mp",
            "mp": "mf",
            "mf": "f",
            "f": "ff",
            "ff": "fff",
            "fff": "ffff",
            "ffff": "ffff",
        }[self.level]


###############################################################################


@dataclass
class Error(Token):
    msg: str


###############################################################################


@dataclass(order=True)
class Instrument(Token):
    name: str
    transpose: int = 0


###############################################################################


@dataclass
class Loop(Token):
    tokens: list[Token]
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
    loop_id : int
        Loop ID #

    Attributes
    ----------
    start : bool
        True iff this is the start of a loop
    loop_id : int
        Loop ID #
    """

    start: bool
    loop_id: int


###############################################################################


@dataclass
class LoopRef(Token):
    loop_id: int
    repeats: int


###############################################################################


@dataclass
class Measure(Token, Comment):
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

    number: list[int] | int = 0

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def range(self) -> list[int]:
        if isinstance(self.number, list):
            rv = self.number
        else:
            rv = [self.number]
        return rv

    ###########################################################################
    # API method definitions
    ###########################################################################

    def left_join(self, prev: "Measure") -> None:
        self.number = [prev.range[0], self.range[-1]]


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
    articulation: Artic
        Articulation style

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
    articulation: Artic
        Articulation style

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
    articulation: Artic = Artic.NORMAL

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_music_xml(
        cls, elem: music21.note.Note | music21.note.Unpitched
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
        if accent:
            articulation = Artic.ACCSTAC if staccato else Artic.ACCENT
        else:
            articulation = Artic.STACCATO if staccato else Artic.NORMAL

        return cls(
            name.lower().replace("#", "+"),
            _get_duration(elem),
            octave - 1,
            elem.notehead,
            elem.duration.dots,
            elem.tie.type if elem.tie is not None else "",
            elem.duration.isGrace,
            articulation,
        )

    ###########################################################################

    def check(self, percussion: bool) -> list[str]:
        msgs = []
        note = self.note_num
        measure = self.measure_num
        if percussion:
            try:
                PERCUSSION_MAP[self.head][self.name + str(self.octave + 1)]
            except KeyError:
                msgs.append(
                    f"Unsupported percussion note #{note} in measure {measure}"
                )
        else:
            octave = self.octave
            name = self.name
            bad = octave < 1
            bad |= octave > 6
            bad |= octave == 0 and name in ["a+", "b-", "b"]
            if bad:
                msg = f"Unsupported note {name}{octave} #{note} in "
                msg += f"measure {measure}"
                msgs.append(msg)
        return msgs


###############################################################################


@dataclass
class RehearsalMark(Token, Comment):
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
            _get_duration(elem),
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
class Tempo(Token):
    bpm: int

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_music_xml(cls, elem: music21.tempo.MetronomeMark) -> "Tempo":
        bpm = int(elem.getQuarterBPM())
        return cls(bpm)


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


###############################################################################


@dataclass
class Vibrato(Token):
    start: bool
