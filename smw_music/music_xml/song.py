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
from typing import cast, Optional

###############################################################################
# Library imports
###############################################################################

import music21  # type: ignore

from mako.template import Template  # type: ignore

###############################################################################
# Project imports
###############################################################################

from .channel import Channel
from .echo import EchoConfig
from .instrument import DEFAULT_DYN, inst_from_name, InstrumentConfig
from .reduction import reduce, remove_unused_instruments
from .shared import CRLF, MusicXmlException
from .tokens import (
    Annotation,
    CrescDelim,
    Crescendo,
    Dynamic,
    Error,
    Instrument,
    LoopDelim,
    Measure,
    Note,
    RehearsalMark,
    Repeat,
    Rest,
    Slur,
    Tempo,
    Token,
    Triplet,
)
from .. import __version__

###############################################################################
# Private function definitions
###############################################################################


def _get_cresc(
    part: music21.stream.Part,
) -> tuple[list[list[int]], list[bool]]:
    cresc: list[list[int]] = [[], []]
    cresc_list = list(filter(_is_crescendo, part))
    cresc[0] = [x.getFirst().id for x in cresc_list]
    cresc[1] = [x.getLast().id for x in cresc_list]
    cresc_type = [
        isinstance(x, music21.dynamics.Crescendo) for x in cresc_list
    ]

    return (cresc, cresc_type)


###############################################################################


def _get_lines(part: music21.stream.Part) -> list[list[int]]:
    lines: list[list[int]] = [[], []]
    line_list = list(filter(_is_line, part))
    lines[0] = [x.getFirst().id for x in line_list]
    lines[1] = [x.getLast().id for x in line_list]

    return lines


###############################################################################


def _get_slurs(part: music21.stream.Part) -> list[list[int]]:
    slurs: list[list[int]] = [[], []]
    slur_list = list(filter(_is_slur, part))
    slurs[0] = [x.getFirst().id for x in slur_list]
    slurs[1] = [x.getLast().id for x in slur_list]

    return slurs


###############################################################################


def _is_crescendo(elem: music21.stream.Stream) -> bool:
    """
    Test to see if a music21 stream element is a crescendo or diminuendo
    object.

    Parameters
    ----------
    elem : music21.stream.Stream
        A music21 Stream element

    Return
    ------
    bool
        True iff `elem` is of type `music21.dynamics.Crescendo` or
        `music21.dynamics.Diminuendo`.
    """
    return isinstance(
        elem, (music21.dynamics.Crescendo, music21.dynamics.Diminuendo)
    )


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
        "composer"), porter (key "porter") game name (key "game"), and global
        volume (key "volume").
    channels: list
        A list of `Channel` objects, the first 8 of which are used in this
        song.

    Attributes
    ----------
    title : str
        The song's title, or '???' if one was not provided
    composer : str
        The song's composer, or '???' if one was not provided
    porter : str
        The song's porter, or '???' if one was not provided
    game : str
        The song's source game, or '???' if one was not provided
    channels : list
        A list of up to 8 channels of music in this song.
    instruments: list
        A list of InstrumentConfig objects for each detected instrument
    volume: int
        Global volume
    """

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    def __init__(self, metadata: dict[str, str], channels: list["Channel"]):
        self.title = metadata.get("title", "???")
        self.composer = metadata.get("composer", "???")
        self.porter = metadata.get("porter", "???")
        self.game = metadata.get("game", "???")
        self.volume = int(metadata.get("volume", 180))
        self.channels = channels[:8]
        self.instruments: list[InstrumentConfig] = []

        self._collect_instruments()

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

        Raises
        ------
        MusicXmlException:
            Whenever a conversion is not possible
        """
        metadata = {}
        parts: list[Channel] = []

        try:
            stream = music21.converter.parseFile(fname)
        except music21.converter.ConverterFileException as e:
            raise MusicXmlException(str(e)) from e

        for elem in stream.flat:
            if isinstance(elem, music21.metadata.Metadata):
                metadata["composer"] = elem.composer or "COMPOSER HERE"
                metadata["title"] = elem.title or "TITLE HERE"
                metadata["porter"] = elem.lyricist or "PORTER NAME HERE"
                metadata["game"] = elem.copyright or "GAME NAME HERE"

        sections = cls._find_rehearsal_marks(stream)

        for elem in stream:
            if isinstance(elem, music21.stream.Part):
                percussion = False
                for n in elem.flatten():
                    if isinstance(n, music21.clef.PercussionClef):
                        percussion = True
                        break

                part = cls._parse_part(elem, sections, len(parts))
                part = remove_unused_instruments(percussion, part)
                parts.append(Channel(part, percussion))

        return cls(metadata, parts)

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __getitem__(self, n: int) -> Channel:
        return self.channels[n]

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _collect_instruments(self):
        instruments: dict[str, set[str]] = {}
        inst: str = ""
        for channel in self.channels:
            for token in channel.tokens:
                if isinstance(token, Instrument):
                    inst = token.name
                    if inst not in instruments:
                        instruments[inst] = set()
                if isinstance(token, Dynamic):
                    instruments[inst].add(token.level.upper())
                if isinstance(token, Crescendo):
                    instruments[inst].add(token.level.upper())

        inst = sorted(instruments)

        self.instruments = [
            InstrumentConfig(
                x, inst_from_name(x), dynamics_present=instruments[x]
            )
            for x in inst
        ]

    ###########################################################################

    @classmethod
    def _find_rehearsal_marks(
        cls, stream: music21.stream.Score
    ) -> dict[int, RehearsalMark]:
        marks = {}
        for elem in stream:
            if isinstance(elem, music21.stream.Part):
                for measure in filter(_is_measure, elem):
                    for subelem in measure:
                        if isinstance(
                            subelem, music21.expressions.RehearsalMark
                        ):
                            marks[
                                measure.number
                            ] = RehearsalMark.from_music_xml(subelem)
                break
        return marks

    ###########################################################################

    @classmethod
    def _parse_part(
        cls,
        part: music21.stream.Part,
        sections: dict[int, RehearsalMark],
        part_no: int,
    ) -> list[Token]:
        channel_elem: list[Token] = []

        slurs = _get_slurs(part)
        lines = _get_lines(part)
        loop_nos = list((part_no + 1) * 100 + n for n in range(len(lines[0])))
        cresc, cresc_type = _get_cresc(part)

        triplets = False
        for subpart in part:
            if isinstance(subpart, music21.instrument.Instrument):
                channel_elem.append(
                    Instrument(subpart.instrumentName.replace(" ", ""))
                )
            if not isinstance(subpart, music21.stream.Measure):
                continue

            measure = cast(music21.stream.Measure, subpart)
            note_no = 0
            channel_elem.append(Measure(measure.number))
            if measure.number in sections:
                channel_elem.append(sections[measure.number])

            for subelem in measure:
                if subelem.id in lines[0]:
                    channel_elem.append(
                        LoopDelim(True, loop_nos[lines[0].index(subelem.id)])
                    )

                if isinstance(
                    subelem,
                    (music21.chord.Chord, music21.percussion.PercussionChord),
                ):
                    msg = f"Chord found, #{note_no + 1} "
                    msg += f"in measure {measure.number}"
                    channel_elem.append(Error(msg))

                if isinstance(subelem, (music21.stream.Voice)):
                    msg = f"Multiple voices in measure {measure.number}"
                    channel_elem.append(Error(msg))

                if isinstance(subelem, music21.note.GeneralNote):
                    note_no += 1
                    if not triplets and bool(subelem.duration.tuplets):
                        channel_elem.append(Triplet(True))
                        triplets = True

                    if triplets and not bool(subelem.duration.tuplets):
                        channel_elem.append(Triplet(False))
                        triplets = False

                if isinstance(subelem, music21.dynamics.Dynamic):
                    channel_elem.append(Dynamic.from_music_xml(subelem))
                if isinstance(
                    subelem, (music21.note.Note, music21.note.Unpitched)
                ):
                    note = Note.from_music_xml(subelem)
                    if subelem.id in slurs[0]:
                        channel_elem.append(Slur(True))
                    # It seems weird to put slur-ends before the actual last
                    # slur note.  But the note that comes at the slur-end needs
                    # to know it so the legato can be put in the right place.
                    if subelem.id in slurs[1]:
                        channel_elem.append(Slur(False))

                    # Gross, fix this
                    if subelem.id in cresc[0]:
                        channel_elem.append(
                            CrescDelim(
                                True, cresc_type[cresc[0].index(subelem.id)]
                            )
                        )

                    note.measure_num = measure.number
                    note.note_num = note_no
                    channel_elem.append(note)

                    # Also gross, fix this
                    if subelem.id in cresc[1]:
                        channel_elem.append(
                            CrescDelim(
                                False, cresc_type[cresc[1].index(subelem.id)]
                            )
                        )

                if isinstance(subelem, music21.bar.Repeat):
                    channel_elem.append(Repeat.from_music_xml(subelem))
                if isinstance(subelem, music21.note.Rest):
                    rest = Rest.from_music_xml(subelem)
                    rest.measure_num = measure.number
                    rest.note_num = note_no
                    channel_elem.append(rest)
                if isinstance(subelem, music21.expressions.TextExpression):
                    annotation = Annotation.from_music_xml(subelem)
                    if annotation is not None:
                        channel_elem.append(annotation)
                if isinstance(subelem, music21.tempo.MetronomeMark):
                    channel_elem.append(Tempo.from_music_xml(subelem))

                if subelem.id in lines[1]:
                    channel_elem.append(
                        LoopDelim(False, loop_nos[lines[1].index(subelem.id)])
                    )
        if triplets:
            channel_elem.append(Triplet(False))

        return channel_elem

    ###########################################################################

    def _reduce(
        self,
        loop_analysis: bool,
        superloop_analysis: bool,
    ):
        for n, chan in enumerate(self.channels):
            chan.tokens = reduce(
                chan.tokens,
                loop_analysis,
                superloop_analysis,
                chan.percussion,
                n != 0,
            )

    ###########################################################################

    def _validate(self):
        errors = []
        for n, channel in enumerate(self.channels):
            msgs = channel.check()
            for msg in msgs:
                errors.append(f"{msg} in staff {n + 1}")

        if errors:
            raise MusicXmlException("\n".join(errors))

    ###########################################################################
    # API method definitions
    ###########################################################################

    def generate_mml(
        self,
        global_legato: bool = True,
        loop_analysis: bool = True,
        superloop_analysis: bool = True,
        measure_numbers: bool = True,
        include_dt: bool = True,
        echo_config: Optional[EchoConfig] = None,
        custom_samples: bool = True,
        optimize_percussion: bool = True,
    ) -> str:
        """
        Return this song's AddmusicK's text.

        Parameters
        ----------
        global_legato : bool
            True iff global legato should be enabled
        loop_analysis : bool
            True iff loops should be detected and replaced with references
        superloop_analysis: bool
            True iff loops should be detected
        measure_numbers: bool
            True iff measure numbers should be included in MML
        include_dt: bool
            True iff current date/time is included in MML
        echo_config: EchoConfig
            Echo configuration
        custom_samples: bool
            True iff the custom samples header should be included in the MML
        optimize_percussion: bool
            True iff repeated percussion notes should not repeat their
            instrument
        """

        self._reduce(loop_analysis, superloop_analysis)

        self._validate()
        channels = [
            x.generate_mml({}, measure_numbers, optimize_percussion)
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
            song=self,
            channels=channels,
            datetime=build_dt,
            percussion=percussion,
            echo_config=echo_config,
            instruments=self.instruments,
            custom_samples=custom_samples,
            dynamics=list(DEFAULT_DYN.keys()),
        )

        rv = rv.replace(" ^", "^")
        rv = rv.replace(" ]", "]")

        # This last bit removes any empty lines at the end (these don't
        # normally show up, but can if the last section in the last staff is
        # empty.
        return rv.rstrip() + CRLF

    ###########################################################################

    def to_mml_file(  # pylint: disable=too-many-arguments
        self,
        fname: str,
        global_legato: bool = True,
        loop_analysis: bool = True,
        superloop_analysis: bool = True,
        measure_numbers: bool = True,
        include_dt: bool = True,
        echo_config: Optional[EchoConfig] = None,
        custom_samples: bool = False,
        optimize_percussion: bool = True,
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
        superloop_analysis: bool
            True iff loops should be detected
        measure_numbers: bool
            True iff measure numbers should be included in MML
        include_dt: bool
            True iff current date/time is included in MML
        echo_config: EchoConfig
            Echo configuration
        custom_samples: bool
            True iff the custom samples header should be included in the MML
        optimize_percussion: bool
            True iff repeated percussion notes should not repeat their
            instrument
        """
        with open(fname, "w", encoding="ascii") as fobj:
            print(
                self.generate_mml(
                    global_legato,
                    loop_analysis,
                    superloop_analysis,
                    measure_numbers,
                    include_dt,
                    echo_config,
                    custom_samples,
                    optimize_percussion,
                ),
                end="",
                file=fobj,
            )
