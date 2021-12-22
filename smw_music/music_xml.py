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

###############################################################################
# Private function definitions
###############################################################################


def _most_common(container: Iterable[_T]) -> _T:
    return Counter(container).most_common(1)[0][0]


###############################################################################
# API class definitions
###############################################################################


class Note:
    ###########################################################################

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
        parts: List[List[Union[Note, Rest]]] = []
        for elem in music21.converter.parseFile(fname):
            if isinstance(elem, music21.metadata.Metadata):
                metadata["composer"] = elem.composer
                metadata["title"] = elem.title
            elif isinstance(elem, music21.stream.Part):
                parts.append([])
                notes = parts[-1]
                for subelem in elem.flatten():
                    if isinstance(subelem, music21.tempo.MetronomeMark):
                        metadata["bpm"] = subelem.getQuarterBPM()
                    if isinstance(subelem, music21.note.Note):
                        notes.append(Note.from_music_xml(subelem))
                    if isinstance(subelem, music21.note.Rest):
                        notes.append(Rest.from_music_xml(subelem))

        return cls(metadata, map(Track, parts))

    ###########################################################################

    def to_amk(self, fname: str):
        with open(fname, "w", encoding="ascii") as fobj:
            print(self.amk, end="\r\n", file=fobj)

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
            amk.append(f"#{n} w255 t{amk_tempo}")
            amk.append("@9 v150")
            amk.append(track.amk)

        return "\r\n".join(amk)


###############################################################################


class Track:
    def __init__(self, notes: List[Union[Note, Rest]]):
        self.notes = notes

    @property
    def base_note_length(self) -> int:
        return _most_common(x.duration for x in self.notes)

    @property
    def base_octave(self) -> int:
        return _most_common(
            x.octave for x in self.notes if isinstance(x, Note)
        )

    @property
    def amk(self) -> str:
        cur_octave = self.base_octave
        base_dur = self.base_note_length
        rv = [f"o{cur_octave}", ""]
        rv.append(f"l{base_dur}")

        for note in self.notes:
            if isinstance(note, Rest):
                directive = "r"

            if isinstance(note, Note):
                octave = note.octave

                if octave != cur_octave:
                    if octave == cur_octave - 1:
                        directive = "<"
                    elif octave == cur_octave + 1:
                        directive = ">"
                    else:
                        directive = f"o{octave}"
                    rv.append(directive)
                    cur_octave = octave

                directive = note.name

            if note.duration != base_dur:
                directive += str(note.duration)

            rv.append(directive)

        return " ".join(rv)
