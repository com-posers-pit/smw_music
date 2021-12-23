"""Utilities for handling Music XML conversions."""

###############################################################################
# Standard Library imports
###############################################################################

from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List, TypeVar, Union

###############################################################################
# Library imports
###############################################################################

import music21  # type: ignore


###############################################################################
# Private variable/constant definitions
###############################################################################

# Valid music channel element classes
_ChannelElem = Union["Annotation", "Measure", "Note", "Rest"]

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
}

###############################################################################

# Generic type variable
_T = TypeVar("_T")

###############################################################################
# Private function definitions
###############################################################################


def _is_measure(elem: music21.stream.Stream) -> bool:
    return isinstance(elem, music21.stream.Measure)


###############################################################################


def _most_common(container: Iterable[_T]) -> _T:
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
        Annotation : A new Annotation object with its `text` attribute set to
        the `elem`'s text content.
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
        A list of valid channel elements (currently `Annotation`, `Measure,
        `Note`, and `Rest`)

    Attributes
    ----------
    amk
    base_note_length
    base_octave
    elems: list
        A list of elements in this channel
    """

    elems: List[_ChannelElem]

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def amk(self) -> str:
        """Return this channel's AddmusicK's text."""
        cur_octave = self.base_octave
        base_dur = self.base_note_length
        directives = [f"o{cur_octave}"]
        directives.append(f"l{base_dur}")

        for elem in self.elems:
            if isinstance(elem, Rest):
                directive = "r"

            if isinstance(elem, Note):
                octave = elem.octave

                if octave != cur_octave:
                    if octave == cur_octave - 1:
                        directive = "<"
                    elif octave == cur_octave + 1:
                        directive = ">"
                    else:
                        directive = f"o{octave}"
                    directives.append(directive)
                    cur_octave = octave

                directive = elem.name

            if isinstance(elem, Measure):
                directive = _CRLF

            if isinstance(elem, Annotation):
                text = elem.text
                if text.startswith("AMK:"):
                    directive = text.removeprefix("AMK:").strip()
                else:
                    directive = ""

            if isinstance(elem, (Note, Rest)):
                if elem.duration != base_dur:
                    directive += str(elem.duration)

            if directive:
                directives.append(directive)

        lines = " ".join(directives).splitlines()
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
        The note's length (TODO: standardize this notion)
    octave: int
        The note's octave (TODO: standardize this notion)

    Attributes
    ----------
    note: str
        The note's name (a-g) with '+'/'-' appended for sharp/flat,
        respectively.
    duration: int
        The note's length
    octave: int
        The note's octave
    """

    name: str
    duration: int
    octave: int

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
        Note : A new Note object with its attributes defined by `elem`
        """
        return cls(
            elem.name.lower().replace("#", "+"),
            _MUSIC_XML_DURATION[elem.duration.ordinal],
            elem.octave,
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

    Attributes
    ----------
    duration: int
        The note's length
    """

    duration: int

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
        Note : A new Rest object with its attributes defined by `elem`
        """
        return cls(_MUSIC_XML_DURATION[elem.duration.ordinal])


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
        Song : A new Song object representing the song described in `fname`
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

    @property
    def amk(self) -> str:
        """Return this song's AddmusicK's text."""
        # Magic BPM -> AMK/SPC tempo conversion
        amk_tempo = int(self.bpm * 255 / 625)

        amk = ["#amk 2"]
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

        return _CRLF.join(amk)
