# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Utilities for handling Music XML conversions."""

###############################################################################
# Standard Library imports
###############################################################################

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, TypeVar, Union

###############################################################################
# Library imports
###############################################################################

import music21  # type: ignore

###############################################################################
# Project imports
###############################################################################

from . import __version__

###############################################################################
# Private variable/constant definitions
###############################################################################

# Valid music channel element classes
_ChannelElem = Union["Annotation", "Dynamic", "Measure", "Note", "Rest"]

###############################################################################

# AMK files are used in windows and need the right line ending.
_CRLF = "\r\n"

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

# Generic type variable
_T = TypeVar("_T")

###############################################################################
# Private function definitions
###############################################################################


def _is_measure(elem: music21.stream.Stream) -> bool:
    """
    Test to see if a music21 stream element is a Measure object.

    Parameters
    ----------
    elem : music21.stream.Stream
        A music21 Stream element

    Return
    ------
    bool
        True iff `elem` is of type `music21.stream.Measure`
    """
    return isinstance(elem, music21.stream.Measure)


###############################################################################


def _most_common(container: Iterable[_T]) -> _T:
    """
    Get the most common element in an iterable.

    Parameters
    ----------
    container : iterable
        A list/dictionary/... containing duplicate elements

    Return
    ------
    object
        The most common element in `container`
    """
    return Counter(container).most_common(1)[0][0]


###############################################################################
# API class definitions
###############################################################################


@dataclass
class Annotation:
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
class Channel:
    """
    Single music channel.

    Parameters
    ----------
    elems: list
        A list of valid channel elements (currently `Annotation`, `Dynamic`,
        `Measure`, `Note`, and `Rest`)

    Attributes
    ----------
    elems: list
        A list of elements in this channel

    Todo
    ----
    Parameterize grace note length?
    """

    elems: List[_ChannelElem]
    _cur_octave: int = field(init=False, repr=False, compare=False)
    _directives: List[str] = field(init=False, repr=False, compare=False)
    _legato: bool = field(init=False, repr=False, compare=False)
    _tie: bool = field(init=False, repr=False, compare=False)
    _triplet: bool = field(init=False, repr=False, compare=False)
    _grace: bool = field(init=False, repr=False, compare=False)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _calc_note_length(self, note: "Note") -> str:
        grace_length = 8
        note_length = ""

        if not self._grace and not note.grace:
            if note.duration != self.base_note_length:
                note_length = str(note.duration)
            note_length += note.dots * "."
        else:
            if note.grace:
                note_length = f"={grace_length}"
            else:
                note_length = f"={192//note.duration - grace_length}"

        return note_length

    ###########################################################################

    def _emit_annotation(self, annotation: Annotation):
        prefix = "AMK:"
        text = annotation.text
        if text.startswith(prefix):
            self._directives.append(text.removeprefix(prefix).strip())

    ###########################################################################

    def _emit_dynamic(self, dyn: "Dynamic"):
        self._directives.append(f"v{dyn.level}")

    ###########################################################################

    def _emit_measure(self, _: "Measure"):
        self._directives.append(_CRLF)

    ###########################################################################

    def _emit_octave(self, note: "Note"):
        octave = note.octave
        if octave != self._cur_octave:
            if octave == self._cur_octave - 1:
                directive = "<"
            elif octave == self._cur_octave + 1:
                directive = ">"
            else:
                directive = f"o{octave}"
            self._directives.append(directive)
            self._cur_octave = octave

    ###########################################################################

    def _emit_note(self, note: "Note"):

        self._handle_triplet(note)

        if note.tie == "start":
            self._tie = True
        if note.grace:
            self._grace = True

        self._emit_octave(note)

        directive = note.name + self._calc_note_length(note)

        self._start_legato()
        self._directives.append(directive)

        if note.tie == "stop":
            self._tie = False

        if not note.grace:
            self._grace = False

        self._stop_legato()

    ###########################################################################

    def _emit_rest(self, rest: "Rest"):
        self._handle_triplet(rest)

        directive = "r"
        if rest.duration != self.base_note_length:
            directive += str(rest.duration)
        directive += rest.dots * "."

        self._directives.append(directive)

    ###########################################################################

    def _handle_triplet(self, elem: Union["Rest", "Note"]):
        if not self._triplet and elem.triplet:
            self._directives.append("{")
        if self._triplet and not elem.triplet:
            self._directives.append("}")
        self._triplet = elem.triplet

    ###########################################################################

    def _reset_state(self):
        self._cur_octave = self.base_octave
        self._grace = False
        self._legato = False
        self._tie = False
        self._triplet = False

    ###########################################################################

    def _start_legato(self):
        if not self._legato:
            if self._tie or self._grace:
                self._legato = True
                self._directives.append("LEGATO_ON")

    ###########################################################################

    def _stop_legato(self):
        if self._legato:
            if not self._tie and not self._grace:
                self._legato = False
                self._directives.append("LEGATO_OFF")

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def amk(self) -> str:
        """Return this channel's AddmusicK's text."""
        self._reset_state()
        self._directives = [f"o{self._cur_octave}"]
        self._directives.append(f"l{self.base_note_length}")

        for elem in self.elems:
            if isinstance(elem, Rest):
                self._emit_rest(elem)

            if isinstance(elem, Dynamic):
                self._emit_dynamic(elem)

            if isinstance(elem, Note):
                self._emit_note(elem)

            if isinstance(elem, Measure):
                self._emit_measure(elem)

            if isinstance(elem, Annotation):
                self._emit_annotation(elem)

        lines = " ".join(self._directives).splitlines()
        return _CRLF.join(x.strip() for x in lines)

    ###########################################################################

    @property
    def base_note_length(self) -> int:
        """Return this channel's most common note/rest length."""
        return _most_common(
            x.duration for x in self.elems if isinstance(x, (Note, Rest))
        )

    ###########################################################################

    @property
    def base_octave(self) -> int:
        """Return this channel's most common octave."""
        return _most_common(
            x.octave for x in self.elems if isinstance(x, Note)
        )


###############################################################################


@dataclass
class Dynamic:
    """
    Dynamics marking.

    Parameters
    ----------
    level: int
        Volume level from 0-255

    Attributes
    ----------
    level: int
        Volume level from 0-255
    """

    level: int

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
        return cls(int(255 * elem.volumeScalar ** 2))


###############################################################################


@dataclass
class Measure:
    """An object representing the start of a new measure of music."""


###############################################################################


@dataclass
class Note:
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
    dots: int
        The number of dots
    tie: str
        "start" to start a tie, "stop" to end a tie, "" if no tie
    triplet: bool
        True iff this note is a triplet
    grace: bool
        True iff this is a grace note

    Attributes
    ----------
    note: str
        The note's name (a-g) with '+'/'-' appended for sharp/flat,
        respectively.
    duration: int
        The note's length
    octave: int
        The note's octave
    dots: int
        The number of dots
    tie: str
        "start" to start a tie, "stop" to end a tie, "" if no tie
    triplet: bool
        True iff this note is a triplet
    grace: bool
        True iff this is a grace note

    Todo
    ----
    Duration, octave, tie, and triplet are poorly implemented, clean this up.
    """

    name: str
    duration: int
    octave: int
    dots: int = 0
    tie: str = ""
    triplet: bool = False
    grace: bool = False

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_music_xml(cls, elem: music21.note.Note) -> "Note":
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
        return cls(
            elem.name.lower().replace("#", "+"),
            _MUSIC_XML_DURATION[elem.duration.ordinal],
            elem.octave - 1,
            elem.duration.dots,
            elem.tie.type if elem.tie is not None else "",
            bool(elem.duration.tuplets),
            isinstance(elem.duration, music21.duration.GraceDuration),
        )


###############################################################################


@dataclass
class Rest:
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
    triplet: bool
        True if this note is a triplet, false otherwise
    """

    duration: int
    dots: int = 0
    triplet: bool = False

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
            bool(elem.duration.tuplets),
        )


###############################################################################


class Song:
    """
    A complete song.

    Parameters
    ----------
    metadata: dict
        A dictionary containing the song's title (key "title"), composer (key
        "composer"), and tempo (key "bpm").
    channel_list: list
        A list of `Channel` objects, the first 8 of which are used in this
        song.

    Attributes
    ----------
    title : str
        The song's title, or '???' if one was not provided
    composer : str
        The song's composer, or '???' if one was not provided
    bpm : int
        The song's tempo in beats per minute
    channel_list : list
        A list of up to 8 channels of music in this song.
    """

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    def __init__(
        self, metadata: Dict[str, str], channel_list: List["Channel"]
    ):
        self.title = metadata.get("title", "???")
        self.composer = metadata.get("composer", "???")
        self.bpm = int(metadata.get("bpm", 120))
        self.channel_list = channel_list[:8]

    ###########################################################################

    @classmethod
    def from_music_xml(cls, fname: str) -> "Song":
        """
        Convert a MusicXML file to a Song.

        Parameters
        ----------
        fname : str
            The (compressed or uncompressed) MusicXML file

        Return
        ------
        Song
            A new Song object representing the song described in `fname`
        """
        metadata = {}
        parts: List[List[_ChannelElem]] = []
        for elem in music21.converter.parseFile(fname):
            if isinstance(elem, music21.metadata.Metadata):
                metadata["composer"] = elem.composer
                metadata["title"] = elem.title
            elif isinstance(elem, music21.stream.Part):
                parts.append([])
                channel_elem = parts[-1]
                for measure in filter(_is_measure, elem):
                    channel_elem.append(Measure())

                    for subelem in measure:
                        if isinstance(subelem, music21.tempo.MetronomeMark):
                            metadata["bpm"] = subelem.getQuarterBPM()
                        if isinstance(subelem, music21.dynamics.Dynamic):
                            channel_elem.append(
                                Dynamic.from_music_xml(subelem)
                            )
                        if isinstance(subelem, music21.note.Note):
                            channel_elem.append(Note.from_music_xml(subelem))
                        if isinstance(subelem, music21.note.Rest):
                            channel_elem.append(Rest.from_music_xml(subelem))
                        if isinstance(
                            subelem, music21.expressions.TextExpression
                        ):
                            channel_elem.append(
                                Annotation.from_music_xml(subelem)
                            )

        return cls(metadata, list(map(Channel, parts)))

    ###########################################################################
    # API method definitions
    ###########################################################################

    def to_amk(self, fname: str):
        """
        Output the AMK representation of this Song to a file.

        Parameters
        ----------
        fname : str
            The output file to write to.
        """
        with open(fname, "w", encoding="ascii") as fobj:
            print(self.amk, end=_CRLF, file=fobj)

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def amk(self) -> str:
        """Return this song's AddmusicK's text."""
        # Magic BPM -> AMK/SPC tempo conversion
        amk_tempo = int(self.bpm * 255 / 625)

        amk = ["#amk 2"]
        amk.append("")
        amk.append(f"; MusicXML->AMK v{__version__}")
        amk.append("")
        amk.append('"LEGATO_ON=$F4$01"')
        amk.append('"LEGATO_OFF=$F4$01"')
        amk.append("")
        amk.append("#spc")
        amk.append("{")
        amk.append(f'#author  "{self.composer}"')
        amk.append(f'#title   "{self.title}"')
        amk.append("}")
        for n, channel in enumerate(self.channel_list):
            amk.append("")
            amk.append(80 * ";")
            amk.append("")
            amk.append(f"#{n} t{amk_tempo}")
            amk.append(channel.amk)

        rv = _CRLF.join(amk)
        # This handles a quirk of where triplet end marks are inserted
        return rv.replace(_CRLF + "} ", " }" + _CRLF)
