# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Song from MusicXML file."""

###############################################################################
# Standard Library imports
###############################################################################

import pkgutil

from datetime import datetime
from typing import Dict, List

###############################################################################
# Library imports
###############################################################################

import music21  # type: ignore

from mako.template import Template  # type: ignore

###############################################################################
# Project imports
###############################################################################

from .channel import Channel
from .shared import CRLF, MusicXmlException
from .tokens import (
    Annotation,
    Token,
    Dynamic,
    RehearsalMark,
    Loop,
    Measure,
    Note,
    Repeat,
    Rest,
    Slur,
)
from .. import __version__

###############################################################################
# Private function definitions
###############################################################################


def _is_line(elem: music21.stream.Stream) -> bool:
    """
    Test to see if a music21 stream element is a Line object.

    Parameters
    ----------
    elem : music21.stream.Stream
        A music21 Stream element

    Return
    ------
    bool
        True iff `elem` is of type `music21.spanner.Line`
    """
    return isinstance(elem, music21.spanner.Line)


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
# API class definitions
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
        parts: List[Channel] = []
        stream = music21.converter.parseFile(fname)
        for elem in stream.flat:
            if isinstance(elem, music21.metadata.Metadata):
                metadata["composer"] = elem.composer
                metadata["title"] = elem.title
            if isinstance(elem, music21.tempo.MetronomeMark):
                metadata["bpm"] = elem.getQuarterBPM()

        sections = cls._find_rehearsal_marks(stream)

        for elem in stream:
            if isinstance(elem, music21.stream.Part):
                percussion = False
                for n in elem.flatten():
                    if isinstance(n, music21.clef.PercussionClef):
                        percussion = True
                        break

                partno = len(parts)
                part = cls._parse_part(elem, partno, sections)
                parts.append(Channel(part, percussion))

        return cls(metadata, parts)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @classmethod
    def _find_rehearsal_marks(
        cls, stream: music21.stream.Score
    ) -> Dict[int, RehearsalMark]:
        marks = {}
        for elem in stream:
            if isinstance(elem, music21.stream.Part):
                for n, measure in enumerate(filter(_is_measure, elem)):
                    for subelem in measure:
                        if isinstance(
                            subelem, music21.expressions.RehearsalMark
                        ):
                            marks[n] = RehearsalMark.from_music_xml(subelem)
                break
        return marks

    ###########################################################################

    @classmethod
    def _parse_part(
        cls,
        part: music21.stream.Part,
        partno: int,
        sections: Dict[int, RehearsalMark],
    ) -> List[Token]:
        channel_elem: List[Token] = []
        slurs: List[List[int]] = [[], []]
        lines: List[List[int]] = [[], []]

        slur_list = list(filter(_is_slur, part))
        slurs[0] = [x.getFirst().id for x in slur_list]
        slurs[1] = [x.getLast().id for x in slur_list]

        line_list = list(filter(_is_line, part))
        lines[0] = [x.getFirst().id for x in line_list]
        lines[1] = [x.getLast().id for x in line_list]

        loopno = 100 * partno

        n = 0
        for n, measure in enumerate(filter(_is_measure, part)):
            channel_elem.append(Measure(n))
            if n in sections:
                channel_elem.append(sections[n])

            for subelem in measure:
                if subelem.id in lines[0]:
                    channel_elem.append(Loop(True, loopno))
                    loopno += 1

                if isinstance(subelem, music21.dynamics.Dynamic):
                    channel_elem.append(Dynamic.from_music_xml(subelem))
                if isinstance(
                    subelem, (music21.note.Note, music21.note.Unpitched)
                ):
                    note = Note.from_music_xml(subelem)
                    if subelem.id in slurs[0]:
                        channel_elem.append(Slur(True))
                    if subelem.id in slurs[1]:
                        channel_elem.append(Slur(False))
                    channel_elem.append(note)
                if isinstance(subelem, music21.bar.Repeat):
                    channel_elem.append(Repeat.from_music_xml(subelem))
                if isinstance(subelem, music21.note.Rest):
                    channel_elem.append(Rest.from_music_xml(subelem))
                if isinstance(subelem, music21.expressions.TextExpression):
                    channel_elem.append(Annotation.from_music_xml(subelem))
                if subelem.id in lines[1]:
                    channel_elem.append(Loop(False, -1))

        channel_elem.append(Measure(n + 1))

        return channel_elem

    ###########################################################################

    def _validate(self):
        for n, channel in enumerate(self.channels):
            try:
                channel.check()
            except MusicXmlException as e:
                raise MusicXmlException(
                    e.args[0] + f" in staff {n + 1}"
                ) from e

    ###########################################################################
    # API method definitions
    ###########################################################################

    def generate_mml(
        self,
        global_legato: bool = True,
        loop_analysis: bool = True,
        measure_numbers: bool = True,
        include_dt: bool = True,
    ) -> str:
        """
        Return this song's AddmusicK's text.

        Parameters
        ----------
        global_legato : bool
            True iff global legato should be enabled
        loop_analysis : bool
            True iff loops should be detected and replaced with references
        measure_numbers: bool
            True iff measure numbers should be included in MML
        include_dt: bool
            True iff current date/time is included in MML
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

        self._validate()
        channels = [
            x.generate_mml(loop_analysis, measure_numbers)
            for x in self.channels
        ]

        build_dt = ""
        if include_dt:
            build_dt = datetime.utcnow().isoformat(" ", "seconds") + " UTC"

        percussion = any(x.percussion for x in self.channels)

        tmpl = Template(  # nosec - generates a .txt output, no XSS concerns
            pkgutil.get_data("smw_music", "data/mml.txt")
        )

        rv = tmpl.render(
            version=__version__,
            global_legato=global_legato,
            tempo=mml_tempo,
            song=self,
            channels=channels,
            volmap=volmap,
            datetime=build_dt,
            percussion=percussion,
        )

        # This handles a quirk of where triplet end marks are inserted
        rv = rv.replace(CRLF + "} ", " }" + CRLF)

        rv = rv.replace(" ^", "^")
        rv = rv.replace("[ ", "[")
        rv = rv.replace(" ]", "]")

        return rv

    ###########################################################################

    def to_mml_file(  # pylint: disable=too-many-arguments
        self,
        fname: str,
        global_legato: bool = True,
        loop_analysis: bool = True,
        measure_numbers: bool = True,
        include_dt: bool = True,
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
        measure_numbers: bool
            True iff measure numbers should be included in MML
        include_dt: bool
            True iff current date/time is included in MML
        """
        with open(fname, "w", encoding="ascii") as fobj:
            print(
                self.generate_mml(
                    global_legato, loop_analysis, measure_numbers, include_dt
                ),
                end="",
                file=fobj,
            )
