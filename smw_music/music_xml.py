"""Utilities for handling Music XML conversions."""

###############################################################################
# Standard Library imports
###############################################################################

from typing import Dict, List, Union

###############################################################################
# Library imports
###############################################################################

import music21  # type: ignore


###############################################################################
# Private constant definitions
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

    ###########################################################################

    @property
    def amk(self) -> str:
        return f"o{self.octave} {self.name}{self.duration}"


###############################################################################


class Rest:
    ###########################################################################

    def __init__(self, duration: int):
        self.duration = duration

    ###########################################################################

    @classmethod
    def from_music_xml(cls, elem: music21.note.Rest) -> "Rest":
        return cls(_MUSIC_XML_DURATION[elem.duration.ordinal])

    ###########################################################################

    @property
    def amk(self) -> str:
        return f"r{self.duration}"


###############################################################################


class Song:
    def __init__(
        self, metadata: Dict[str, str], parts: List[List[Union[Note, Rest]]]
    ):
        self.title = metadata["title"]
        self.composer = metadata["composer"]
        self.bpm = int(metadata["bpm"])
        self.parts = parts

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

        return cls(metadata, parts)

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
        for n, part in enumerate(self.parts):
            amk.append("")
            amk.append(f"#{n} w255 t{amk_tempo}")
            amk.append("@9 v150 o5")
            amk.append(" ".join(note.amk for note in part))

        return "\r\n".join(amk)
