# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Token classes extracted from MusicXML files."""

###############################################################################
# Standard Library imports
###############################################################################

from dataclasses import dataclass
from typing import Callable, ClassVar, List, Optional, Tuple, Union

###############################################################################
# Library imports
###############################################################################

import music21  # type: ignore

###############################################################################
# Project imports
###############################################################################

from .context import MmlState, SlurState
from .shared import CRLF, MusicXmlException, octave_notelen_str

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
# API constant definitions
###############################################################################

# Weinberg:
# http://www.normanweinberg.com/uploads/8/1/6/4/81640608/940506pn_guildines_for_drumset.pdf
PERCUSSION_MAP = {
    "x": {
        "c6": "CR3",
        "b5": "CR2",
        "a5": "CR",
        "g5": "CH",
        "f5": "RD",
        "e5": "OH",
        "d5": "RD2",
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


def flatten(tokens: List["Token"]) -> List["Token"]:
    rv: List["Token"] = []
    for token in tokens:
        if isinstance(token, Loop):
            rv.extend(token.tokens)
        else:
            rv.append(token)
    return rv


###############################################################################
# API class definitions
###############################################################################


class Token:
    """Base class for MusicXML->MML tokens."""

    ###########################################################################
    # API method definitions
    ###########################################################################

    def emit(self, state: MmlState, directives: List[str]):
        raise NotImplementedError


###############################################################################


class Playable:
    measure_num: int
    note_num: int
    duration: int


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
    matches: ClassVar[
        List[Tuple[Callable[[str], bool], Callable[[str], str]]]
    ] = [
        (
            lambda x: x.startswith("AMK: "),
            lambda x: x.removeprefix("AMK:").strip(),
        )
    ]

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_music_xml(
        cls, elem: music21.expressions.TextExpression
    ) -> Optional["Annotation"]:
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
            `elem`'s text content, or None.
        """
        text = elem.content
        rv = None
        for match, proc in cls.matches:
            if match(text):
                rv = cls(proc(text))
        return rv

    ###########################################################################
    # API method definitions
    ###########################################################################

    def emit(self, _: MmlState, directives: List[str]):
        directives.append(self.text)


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
    # API method definitions
    ###########################################################################

    def emit(self, _: MmlState, directives: List[str]):
        directives.append(f"v{self.level.upper()}")


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

    ###########################################################################
    # API method definitions
    ###########################################################################

    def emit(self, state: MmlState, directives: List[str]):
        directives.append(CRLF)
        directives.append(f";===================={CRLF}")
        directives.append(f"; Section {self.mark}{CRLF}")
        directives.append(f";===================={CRLF}")
        directives.append(CRLF)
        directives.append(
            octave_notelen_str(state.octave, state.default_note_len)
        )
        directives.append(CRLF)


###############################################################################


@dataclass
class Loop(Token):
    tokens: List[Token]
    loop_id: int
    repeats: int
    superloop: bool

    ###########################################################################
    # API method definitions
    ###########################################################################

    def emit(self, state: MmlState, directives: List[str]):
        if self.superloop:
            open_dir = "[["
            close_dir = "]]"
        else:
            open_dir = f"({self.loop_id})["
            close_dir = "]"
        if self.repeats > 1:
            close_dir += str(self.repeats)

        directives.append(open_dir)

        for token in self.tokens:
            token.emit(state, directives)

        directives.append(close_dir)


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

    ###########################################################################
    # API method definitions
    ###########################################################################

    def emit(self, state: MmlState, directives: List[str]):
        pass


###############################################################################


@dataclass
class LoopRef(Token):
    loop_id: int
    repeats: int

    ###########################################################################
    # API method definitions
    ###########################################################################

    def emit(self, _: MmlState, directives: List[str]):
        repeats = f"{self.repeats}" if self.repeats > 1 else ""
        directives.append(f"({self.loop_id}){repeats}")


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

    ###########################################################################
    # API method definitions
    ###########################################################################

    def emit(self, state: MmlState, directives: List[str]):
        comment = ""
        if state.measure_numbers:
            comment = f"; Measure {self.number}"

        directives.append(f"{comment}{CRLF}")


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

    ###########################################################################

    def check(self, percussion: bool):
        note = self.note_num
        measure = self.measure_num
        if percussion:
            try:
                PERCUSSION_MAP[self.head][self.name + str(self.octave + 1)]
            except KeyError as e:
                raise MusicXmlException(
                    f"Bad percussion note #{note} in measure {measure}"
                ) from e
        else:
            if not 0 <= self.octave <= 6:
                raise MusicXmlException(
                    f"Bad note #{note} in measure {measure}"
                )

    ###########################################################################

    def _start_legato(self, state: MmlState, directives: List[str]):
        if not state.legato:
            if (state.slur == SlurState.SLUR_ACTIVE) or state.grace:
                state.legato = True
                directives.append("LEGATO_ON")

    ###########################################################################

    def _stop_legato(self, state: MmlState, directives: List[str]):
        if state.legato:
            if not (
                state.grace
                or (state.slur == SlurState.SLUR_ACTIVE)
                or state.tie
            ):
                state.legato = False
                directives.append("LEGATO_OFF")

    ###########################################################################

    def _calc_note_length(self, state: MmlState) -> str:
        grace_length = 8
        note_length = ""

        if state.slur == SlurState.SLUR_END:
            state.slur = SlurState.SLUR_IDLE
            duration = 192 // self.duration
            duration = int(duration * (2 - 0.5 ** self.dots))
            state.legato = False
            note_length = f"=1 LEGATO_OFF ^={duration - 1}"
        else:
            if not state.grace and not self.grace:
                if self.duration != state.default_note_len:
                    note_length = str(self.duration)
                note_length += self.dots * "."
            else:
                if self.grace:
                    note_length = f"={grace_length}"
                else:
                    duration = 192 // self.duration
                    duration = int(duration * (2 - 0.5 ** self.dots))
                    note_length = f"={duration - grace_length}"

        return note_length

    ###########################################################################

    def _emit_octave(self, state: MmlState, directives: List[str]):
        cur_octave = state.octave
        octave = self.octave
        if octave != cur_octave:
            if octave == cur_octave - 1:
                directive = "<"
            elif octave == cur_octave + 1:
                directive = ">"
            else:
                directive = f"o{octave}"
            directives.append(directive)
            state.octave = octave

    ###########################################################################

    def emit(self, state: MmlState, directives: List[str]):
        if self.grace:
            state.grace = True

        if not state.percussion:
            self._emit_octave(state, directives)

        if state.tie:
            directive = "^"
        else:
            if not state.percussion:
                directive = self.name
            else:
                directive = (
                    PERCUSSION_MAP[self.head][self.name + str(self.octave + 1)]
                    + " c"
                )

        directive += self._calc_note_length(state)

        if not state.tie:
            if not self.accent and state.accent:
                state.accent = False
                directives.append("qACC_OFF")
            if not self.staccato and state.staccato:
                state.staccato = False
                directives.append("qSTAC_OFF")

            if self.accent and not state.accent:
                state.accent = True
                directives.append("qACC_ON")

            if self.staccato and not state.staccato:
                state.staccato = True
                directives.append("qSTAC_ON")

        if self.tie == "start":
            state.tie = True

        self._start_legato(state, directives)

        directives.append(directive)

        if self.tie == "stop":
            state.tie = False

        if not self.grace:
            state.grace = False

        self._stop_legato(state, directives)


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

    ###########################################################################
    # API method definitions
    ###########################################################################

    def emit(self, _: MmlState, directives: List[str]):
        if self.start:
            directives.append("/")


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

    ###########################################################################
    # API method definitions
    ###########################################################################

    def emit(self, state: MmlState, directives: List[str]):
        directive = "r"
        if self.duration != state.default_note_len:
            directive += str(self.duration)
        directive += self.dots * "."

        directives.append(directive)


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

    ###########################################################################
    # API method definitions
    ###########################################################################

    def emit(self, state: MmlState, directives: List[str]):
        state.slur = (
            SlurState.SLUR_ACTIVE if self.start else SlurState.SLUR_END
        )


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

    ###########################################################################
    # API method definitions
    ###########################################################################

    def emit(self, _: MmlState, directives: List[str]):
        directives.append("{" if self.start else "}")
