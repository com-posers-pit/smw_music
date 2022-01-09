# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Utilities for handling Music XML conversions."""

###############################################################################
# Standard Library imports
###############################################################################

import pkgutil

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, TypeVar, Union

###############################################################################
# Library imports
###############################################################################

import music21  # type: ignore

from mako.template import Template  # type: ignore

###############################################################################
# Project imports
###############################################################################

from . import __version__

###############################################################################
# Private variable/constant definitions
###############################################################################

# Valid music channel element classes
_ChannelElem = Union[
    "Annotation", "Dynamic", "Measure", "Note", "Repeat", "Rest"
]

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


def _is_slur(elem: music21.stream.Stream) -> bool:
    """
    Test to see if a music21 stream element is a Slur object.

    Parameters
    ----------
    elem : music21.stream.Stream
        A music21 Stream element

    Return
    ------
    bool
        True iff `elem` is of type `music21.spanner.Slur`
    """
    return isinstance(elem, music21.spanner.Slur)


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
class Channel:  # pylint: disable=too-many-instance-attributes
    """
    Single music channel.

    Parameters
    ----------
    elems: list
        A list of valid channel elements (currently `Annotation`, `Dynamic`,
        `Measure`, `Note`, `Repeat`, and `Rest`)

    Attributes
    ----------
    elems: list
        A list of elements in this channel

    Todo
    ----
    Parameterize grace note length?
    """

    elems: List[_ChannelElem]
    _accent: bool = field(init=False, repr=False, compare=False)
    _cur_octave: int = field(init=False, repr=False, compare=False)
    _directives: List[str] = field(init=False, repr=False, compare=False)
    _grace: bool = field(init=False, repr=False, compare=False)
    _legato: bool = field(init=False, repr=False, compare=False)
    _slur: bool = field(init=False, repr=False, compare=False)
    _staccato: bool = field(init=False, repr=False, compare=False)
    _tie: bool = field(init=False, repr=False, compare=False)
    _triplet: bool = field(init=False, repr=False, compare=False)

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __getitem__(self, n: int) -> _ChannelElem:
        return self.elems[n]

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _calc_note_length(self, note: "Note") -> str:
        grace_length = 8
        note_length = ""

        if note.slur is False:
            self._slur = False
            duration = 192 // note.duration
            duration = int(duration * (2 - 0.5 ** note.dots))
            self._legato = False
            note_length = f"=1 LEGATO_OFF ^={duration - 1}"
        else:
            if not self._grace and not note.grace:
                if note.duration != self.base_note_length:
                    note_length = str(note.duration)
                note_length += note.dots * "."
            else:
                if note.grace:
                    note_length = f"={grace_length}"
                else:
                    duration = 192 // note.duration
                    duration = int(duration * (2 - 0.5 ** note.dots))
                    note_length = f"={duration - grace_length}"

        return note_length

    ###########################################################################

    def _emit_annotation(self, annotation: Annotation):
        if annotation.amk_annotation:
            self._directives.append(annotation.amk_text)

    ###########################################################################

    def _emit_dynamic(self, dyn: "Dynamic"):
        volmap = {
            "pppp": "vPPPP",
            "ppp": "vPPP",
            "pp": "vPP",
            "p": "vP",
            "mp": "vMP",
            "mf": "vMF",
            "f": "vF",
            "ff": "vFF",
            "fff": "vFFF",
            "ffff": "vFFFF",
        }
        self._directives.append(volmap[dyn.level])

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

        if note.grace:
            self._grace = True
        if note.slur:
            self._slur = True

        self._emit_octave(note)

        directive = "^" if self._tie else note.name
        directive += self._calc_note_length(note)

        if note.tie == "start":
            self._tie = True

        self._start_legato()

        if not note.accent and self._accent:
            self._accent = False
            self._directives.append("qACC_OFF")
        if not note.staccato and self._staccato:
            self._staccato = False
            self._directives.append("qSTAC_OFF")

        if note.accent and not self._accent:
            self._accent = True
            self._directives.append("qACC_ON")

        if note.staccato and not self._staccato:
            self._staccato = True
            self._directives.append("qSTAC_ON")

        self._directives.append(directive)

        if note.tie == "stop":
            self._tie = False

        if not note.grace:
            self._grace = False

        self._stop_legato()

    ###########################################################################

    def _emit_repeat(self, repeat: "Repeat"):
        if repeat.start:
            self._directives.append("/")

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
        self._accent = False
        self._cur_octave = self.base_octave
        self._grace = False
        self._legato = False
        self._slur = False
        self._staccato = False
        self._tie = False
        self._triplet = False

    ###########################################################################

    def _start_legato(self):
        if not self._legato:
            if self._slur or self._grace:
                self._legato = True
                self._directives.append("LEGATO_ON")

    ###########################################################################

    def _stop_legato(self):
        if self._legato:
            if not (self._grace or self._slur or self._tie):
                self._legato = False
                self._directives.append("LEGATO_OFF")

    ###########################################################################
    # API method definitions
    ###########################################################################

    def generate_mml(self, loop_analysis: bool = True) -> str:
        """
        Generate this channel's AddMusicK MML text.

        Parameters
        ----------
        loop_analysis: bool
            True iff loop analysis should be enabled


        Return
        ------
        str
            The MML text for this channel

        """
        self._reset_state()
        self._directives = [f"o{self._cur_octave}"]
        self._directives.append(f"l{self.base_note_length}")

        skip_count = 0
        repeat_count = 0

        for n, elem in enumerate(self.elems):
            if skip_count:
                skip_count -= 1
                continue

            if loop_analysis:
                # Look for repeats
                if isinstance(elem, (Note, Rest)):
                    repeat_count = 1
                    skip_count = 0
                    for cand in self.elems[n + 1 :]:
                        if cand == elem:
                            repeat_count += 1
                            skip_count += 1
                        elif isinstance(cand, Measure):
                            skip_count += 1
                        elif (
                            isinstance(cand, Annotation)
                            and not cand.amk_annotation
                        ):
                            skip_count += 1
                        else:
                            break

            if repeat_count >= 3:
                self._directives.append("[")
            else:
                skip_count = 0

            if isinstance(elem, Repeat):
                self._emit_repeat(elem)

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

            if repeat_count >= 3:
                self._directives.append(f"]{repeat_count}")
                repeat_count = 0

        lines = " ".join(self._directives).splitlines()
        return _CRLF.join(x.strip() for x in lines)

    ###########################################################################
    # API property definitions
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
class Measure:
    """An object representing the start of a new measure of music."""


###############################################################################


@dataclass
class Note:  # pylint: disable=too-many-instance-attributes
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
    accent: bool
        True iff this is an accented note
    staccato: bool
        True iff this is an staccato note
    slur: Optional[bool]
        True if this is the start of a slur, False if it's the end, None
        otherwise

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
    accent: bool
        True iff this is an accented note
    staccato: bool
        True iff this is an staccato note
    slur: Optional[bool]
        True if this is the start of a slur, False if it's the end, None
        otherwise

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
    accent: bool = False
    staccato: bool = False
    slur: Optional[bool] = None

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
        articulations = [type(x) for x in elem.articulations]

        accent = music21.articulations.Accent in articulations
        staccato = music21.articulations.Staccato in articulations

        return cls(
            elem.name.lower().replace("#", "+"),
            _MUSIC_XML_DURATION[elem.duration.ordinal],
            elem.octave - 1,
            elem.duration.dots,
            elem.tie.type if elem.tie is not None else "",
            bool(elem.duration.tuplets),
            elem.duration.isGrace,
            accent,
            staccato,
        )


###############################################################################


@dataclass
class Repeat:
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
    channels: list
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
    channels : list
        A list of up to 8 channels of music in this song.
    """

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    def __init__(self, metadata: Dict[str, str], channels: List["Channel"]):
        self.title = metadata.get("title", "???")
        self.composer = metadata.get("composer", "???")
        self.bpm = int(metadata.get("bpm", 120))
        self.channels = channels[:8]

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
        stream = music21.converter.parseFile(fname)
        for elem in stream.flat:
            if isinstance(elem, music21.metadata.Metadata):
                metadata["composer"] = elem.composer
                metadata["title"] = elem.title
            if isinstance(elem, music21.tempo.MetronomeMark):
                metadata["bpm"] = elem.getQuarterBPM()

        for elem in stream:
            if isinstance(elem, music21.stream.Part):
                parts.append(cls._parse_part(elem))

        return cls(metadata, list(map(Channel, parts)))

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @classmethod
    def _parse_part(cls, part: music21.stream.Part) -> List[_ChannelElem]:
        channel_elem: List[_ChannelElem] = []
        slurs: List[List[int]] = [[], []]

        slur_list = list(filter(_is_slur, part))
        slurs[0] = [x.getFirst().id for x in slur_list]
        slurs[1] = [x.getLast().id for x in slur_list]

        for measure in filter(_is_measure, part):
            channel_elem.append(Measure())

            for subelem in measure:
                if isinstance(subelem, music21.dynamics.Dynamic):
                    channel_elem.append(Dynamic.from_music_xml(subelem))
                if isinstance(subelem, music21.note.Note):
                    note = Note.from_music_xml(subelem)
                    if subelem.id in slurs[0]:
                        note.slur = True
                    if subelem.id in slurs[1]:
                        note.slur = False
                    channel_elem.append(note)
                if isinstance(subelem, music21.bar.Repeat):
                    channel_elem.append(Repeat.from_music_xml(subelem))
                if isinstance(subelem, music21.note.Rest):
                    channel_elem.append(Rest.from_music_xml(subelem))
                if isinstance(subelem, music21.expressions.TextExpression):
                    channel_elem.append(Annotation.from_music_xml(subelem))

        return channel_elem

    ###########################################################################
    # API method definitions
    ###########################################################################

    def generate_mml(
        self, global_legato: bool = True, loop_analysis: bool = True
    ) -> str:
        """
        Return this song's AddmusicK's text.

        Parameters
        ----------
        global_legato : bool
            True iff global legato should be enabled
        loop_analysis : bool
            True iff loops should be detected and replaced with references
        """
        # Magic BPM -> MML/SPC tempo conversion
        mml_tempo = int(self.bpm * 255 / 625)

        volmap = {
            "vPPPP": 26,
            "vPPP": 38,
            "vPP": 64,
            "vP": 90,
            "vMP": 115,
            "vMF": 141,
            "vF": 179,
            "vFF": 217,
            "vFFF": 230,
            "vFFFF": 225,
        }

        tmpl = Template(  # nosec - generates a .txt output, no XSS concerns
            pkgutil.get_data("smw_music", "data/mml.txt")
        )

        rv = tmpl.render(
            version=__version__,
            global_legato=global_legato,
            tempo=mml_tempo,
            song=self,
            loop_analysis=loop_analysis,
            volmap=volmap,
        )

        # This handles a quirk of where triplet end marks are inserted
        rv = rv.replace(_CRLF + "} ", " }" + _CRLF)

        rv = rv.replace(" ^", "^")
        rv = rv.replace("[ ", "[")
        rv = rv.replace(" ]", "]")

        return rv

    ###########################################################################

    def to_mml_file(
        self,
        fname: str,
        global_legato: bool = True,
        loop_analysis: bool = True,
    ):
        """
        Output the MML representation of this Song to a file.

        Parameters
        ----------
        fname : str
            The output file to write to.
        global_legato : bool
            True iff global legato should be enabled
        loop_analysis: bool
            True iff loops should be detected and replaced with references
        """
        with open(fname, "w", encoding="ascii") as fobj:
            print(
                self.generate_mml(global_legato, loop_analysis),
                end="",
                file=fobj,
            )
