"""Utilities for handling Music XML conversions."""

###############################################################################
# Standard Library imports
###############################################################################

from collections import Counter
from typing import Dict, Iterable, List, TypeVar, Union

###############################################################################
# Library imports
###############################################################################

import music21  # type: ignore


###############################################################################
# Private constant definitions
###############################################################################

_T = TypeVar("_T")

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

_Track_Elem = Union["Annotation", "Measure", "Note", "Rest"]

_CRLF = "\r\n"

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


class Annotation:
    def __init__(self, text: str):
        self.text = text

    ###########################################################################

    @classmethod
    def from_music_xml(
        cls, elem: music21.expressions.TextExpression
    ) -> "Annotation":
        return cls(elem.content)


###############################################################################


class Measure:
    pass


###############################################################################


class Note:
    def __init__(self, name: str, duration: int, octave: int):
        self.name = name
        self.duration = duration
        self.octave = octave

    ###########################################################################

    @classmethod
    def from_music_xml(cls, elem: music21.note.Note) -> "Note":
        return cls(
            elem.name.lower().replace("#", "+"),
            _MUSIC_XML_DURATION[elem.duration.ordinal],
            elem.octave,
        )


###############################################################################


class Rest:
    def __init__(self, duration: int):
        self.duration = duration

    ###########################################################################

    @classmethod
    def from_music_xml(cls, elem: music21.note.Rest) -> "Rest":
        return cls(_MUSIC_XML_DURATION[elem.duration.ordinal])


###############################################################################


class Song:
    def __init__(self, metadata: Dict[str, str], track_list: List["Track"]):
        self.title = metadata["title"]
        self.composer = metadata["composer"]
        self.bpm = int(metadata["bpm"])
        self.track_list = track_list

    ###########################################################################

    @classmethod
    def from_music_xml(cls, fname: str) -> "Song":
        metadata = {}
        parts: List[List[_Track_Elem]] = []
        for elem in music21.converter.parseFile(fname):
            if isinstance(elem, music21.metadata.Metadata):
                metadata["composer"] = elem.composer
                metadata["title"] = elem.title
            elif isinstance(elem, music21.stream.Part):
                parts.append([])
                track_elem = parts[-1]
                for measure in filter(_is_measure, elem):
                    track_elem.append(Measure())

                    for subelem in measure:
                        if isinstance(subelem, music21.tempo.MetronomeMark):
                            metadata["bpm"] = subelem.getQuarterBPM()
                        if isinstance(subelem, music21.note.Note):
                            track_elem.append(Note.from_music_xml(subelem))
                        if isinstance(subelem, music21.note.Rest):
                            track_elem.append(Rest.from_music_xml(subelem))
                        if isinstance(
                            subelem, music21.expressions.TextExpression
                        ):
                            track_elem.append(
                                Annotation.from_music_xml(subelem)
                            )

        return cls(metadata, map(Track, parts))

    ###########################################################################

    def to_amk(self, fname: str):
        with open(fname, "w", encoding="ascii") as fobj:
            print(self.amk, end=_CRLF, file=fobj)

    ###########################################################################

    @property
    def amk(self) -> str:
        # Magic BPM -> AMK/SPC tempo conversion
        amk_tempo = int(self.bpm * 255 / 625)

        amk = ["#amk 2"]
        amk.append("")
        amk.append("#spc")
        amk.append("{")
        amk.append(f'#author  "{self.composer}"')
        amk.append(f'#title   "{self.title}"')
        amk.append("}")
        for n, track in enumerate(self.track_list):
            amk.append("")
            amk.append(80 * ";")
            amk.append("")
            amk.append(f"#{n} t{amk_tempo}")
            amk.append(track.amk)

        return _CRLF.join(amk)


###############################################################################


class Track:
    def __init__(self, elems: List[_Track_Elem]):
        self.elems = elems

    @property
    def base_note_length(self) -> int:
        return _most_common(
            x.duration for x in self.elems if isinstance(x, (Note, Rest))
        )

    @property
    def base_octave(self) -> int:
        return _most_common(
            x.octave for x in self.elems if isinstance(x, Note)
        )

    @property
    def amk(self) -> str:
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

            try:
                if elem.duration != base_dur:
                    directive += str(elem.duration)
            except AttributeError:
                # Only notes and rests have .duration attributes
                pass

            if directive:
                directives.append(directive)

        lines = " ".join(directives).splitlines()
        return _CRLF.join(x.strip() for x in lines)
