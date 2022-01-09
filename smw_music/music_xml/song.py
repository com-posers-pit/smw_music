# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Song from MusicXML file."""

###############################################################################
# Standard Library imports
###############################################################################

import pkgutil

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
from .shared import CRLF
from .tokens import (
    Annotation,
    ChannelElem,
    Dynamic,
    Measure,
    Note,
    Repeat,
    Rest,
)
from .. import __version__

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
        parts: List[List[ChannelElem]] = []
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
    def _parse_part(cls, part: music21.stream.Part) -> List[ChannelElem]:
        channel_elem: List[ChannelElem] = []
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
        rv = rv.replace(CRLF + "} ", " }" + CRLF)

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
