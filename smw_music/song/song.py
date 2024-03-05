# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Song from MusicXML file."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from functools import cached_property
from pathlib import Path

# Library imports
import music21 as m21

# Package imports
from smw_music.utils import filter_type

from .common import Dynamics
from .reduction import remove_unused_instruments
from .tokens import (
    Annotation,
    ChannelDelim,
    Clef,
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
    SongException,
    Tempo,
    Token,
    Triplet,
)

###############################################################################
# Private function definitions
###############################################################################


def _extract_channels(stream: m21.stream.base.Score) -> list[list[Token]]:
    parts: list[list[Token]] = []

    sections = _find_rehearsal_marks(stream)

    for elem in filter_type(m21.stream.Part, stream[:]):
        part = _parse_part(elem, sections, len(parts))
        part = remove_unused_instruments(part)
        parts.append(part)

    return parts


###############################################################################


def _extract_metadata(stream: m21.stream.base.Score) -> dict[str, str]:
    metadata = {}
    for elem in filter_type(m21.metadata.Metadata, stream.flat):
        metadata["composer"] = elem.composer or ""
        metadata["title"] = elem.title or ""
        metadata["porter"] = elem.lyricist or ""
        metadata["game"] = elem.copyright or ""

    return metadata


###############################################################################


def _find_rehearsal_marks(
    stream: m21.stream.Score,
) -> dict[int, RehearsalMark]:
    marks = {}
    for elem in filter_type(m21.stream.Part, stream[:]):
        for measure in filter_type(m21.stream.Measure, elem[:]):
            for subelem in filter_type(
                m21.expressions.RehearsalMark, measure[:]
            ):
                marks[measure.number] = RehearsalMark.from_music_xml(subelem)
            break
    return marks


###############################################################################


def _get_cresc(
    part: m21.stream.Part,
) -> tuple[list[list[int]], list[bool]]:
    cresc: list[list[int]] = [[], []]
    # DynamicWedge is a parent class for Crescendo and Diminuendo, which is
    # what we want to pull out of the token list
    cresc_list = filter_type(m21.dynamics.DynamicWedge, part[:])

    cresc[0] = [x.getFirst().id for x in cresc_list]
    cresc[1] = [x.getLast().id for x in cresc_list]
    cresc_type = [isinstance(x, m21.dynamics.Crescendo) for x in cresc_list]

    return (cresc, cresc_type)


###############################################################################


def _get_lines(part: m21.stream.Part) -> list[list[int]]:
    lines: list[list[int]] = [[], []]
    line_list = [x for x in part if isinstance(x, m21.spanner.Line)]
    lines[0] = [x.getFirst().id for x in line_list]
    lines[1] = [x.getLast().id for x in line_list]

    return lines


###############################################################################


def _get_slurs(part: m21.stream.Part) -> list[list[int]]:
    slurs: list[list[int]] = [[], []]
    slur_list = filter_type(m21.spanner.Slur, part[:])

    slurs[0] = [x.getFirst().id for x in slur_list]
    slurs[1] = [x.getLast().id for x in slur_list]

    return slurs


###############################################################################


def _parse_part(
    part: m21.stream.Part,
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
        if isinstance(subpart, m21.instrument.Instrument):
            # This used to be .instrumentName, but that behaves...
            # unintuitively... on percussion channels
            name = subpart.partName or ""
            name = name.replace("\u266d", "b")  # Replace flats
            name = name.replace(" ", "")  # Replace spaces

            # Pick off the instrument transposition
            transpose = subpart.transposition
            semitones = transpose.semitones if transpose is not None else 0

            if not isinstance(semitones, int):
                raise SongException(f"Non-integer transposition {semitones}")

            semitones %= 12

            channel_elem.append(Instrument(name, semitones))
        if not isinstance(subpart, m21.stream.Measure):
            continue

        measure = subpart
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
                (m21.chord.Chord, m21.percussion.PercussionChord),
            ):
                msg = f"Chord found, #{note_no + 1} "
                msg += f"in measure {measure.number}"
                channel_elem.append(Error(msg))

            if isinstance(subelem, (m21.stream.Voice)):
                msg = f"Multiple voices in measure {measure.number}"
                channel_elem.append(Error(msg))

            if isinstance(subelem, m21.note.GeneralNote):
                note_no += 1
                if not triplets and bool(subelem.duration.tuplets):
                    channel_elem.append(Triplet(True))
                    triplets = True

                if triplets and not bool(subelem.duration.tuplets):
                    channel_elem.append(Triplet(False))
                    triplets = False

            if isinstance(subelem, m21.dynamics.Dynamic):
                try:
                    channel_elem.append(Dynamic.from_music_xml(subelem))
                except SongException as e:
                    msg = f"{e} in measure {measure.number}"
                    channel_elem.append(Error(msg))
            if isinstance(subelem, (m21.note.Note, m21.note.Unpitched)):
                note = Note.from_music_xml(subelem)
                if subelem.id in slurs[0]:
                    channel_elem.append(Slur(True))
                # It seems weird to put slur-ends before the actual last
                # slur note.  But the note that comes at the slur-end needs
                # to know it so the legato can be put in the right place.
                if subelem.id in slurs[1]:
                    channel_elem.append(Slur(False))

                # Gross, fix this
                subelem_id = subelem.id
                if not isinstance(subelem_id, int):
                    raise SongException(f"Non-integer element ID {subelem_id}")

                if subelem_id in cresc[0]:
                    channel_elem.append(
                        CrescDelim(
                            True, cresc_type[cresc[0].index(subelem_id)]
                        )
                    )

                note.measure_num = measure.number
                note.note_num = note_no
                channel_elem.append(note)

                # Also gross, fix this
                subelem_id = subelem.id
                if not isinstance(subelem_id, int):
                    raise SongException(f"Non-integer element ID {subelem_id}")

                if subelem_id in cresc[1]:
                    channel_elem.append(
                        CrescDelim(
                            False, cresc_type[cresc[1].index(subelem_id)]
                        )
                    )

            if isinstance(subelem, m21.bar.Repeat):
                channel_elem.append(Repeat.from_music_xml(subelem))
            if isinstance(subelem, m21.note.Rest):
                rest = Rest.from_music_xml(subelem)
                rest.measure_num = measure.number
                rest.note_num = note_no
                channel_elem.append(rest)
            if isinstance(subelem, m21.expressions.TextExpression):
                channel_elem.append(Annotation.from_music_xml(subelem))
            if isinstance(subelem, m21.tempo.MetronomeMark):
                channel_elem.append(Tempo.from_music_xml(subelem))
            if isinstance(subelem, m21.clef.Clef):
                channel_elem.append(Clef.from_music_xml(subelem))

            if subelem.id in lines[1]:
                channel_elem.append(
                    LoopDelim(False, loop_nos[lines[1].index(subelem.id)])
                )
    if triplets:
        channel_elem.append(Triplet(False))

    return channel_elem


###############################################################################
# API class definitions
###############################################################################


class Song:
    """
    A complete song.

    Parameters
    ----------
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
        A list of instrument names for each detected instrument
    """

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    def __init__(
        self,
        channels: list[list[Token]],
        title: str = "",
        composer: str = "",
        porter: str = "",
        game: str = "",
    ):
        self.title = title
        self.composer = composer
        self.porter = porter
        self.game = game
        self.channels = channels[:8]

        # TODO: Remove
        # self._collect_instruments()

    ###########################################################################

    @classmethod
    def from_music_xml(cls, fname: Path) -> "Song":
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
        SongException:
            Whenever a conversion is not possible
        """
        try:
            stream = m21.converter.parseFile(fname)
        except m21.converter.ConverterFileException as e:
            raise SongException(str(e)) from e

        if not isinstance(stream, m21.stream.Score):
            raise SongException(
                f"Can only operate on Scores, not {type(stream)}s"
            )

        metadata = _extract_metadata(stream)
        channels = _extract_channels(stream)

        return cls(channels, **metadata)

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __getitem__(self, n: int) -> list[Token]:
        return self.channels[n]

    ###########################################################################
    # API property definitions
    ###########################################################################

    @cached_property
    def instruments(self) -> list[str]:
        instruments = set()
        for channel in self.channels:
            for inst in filter_type(Instrument, channel):
                instruments.add(inst.name)

        return sorted(instruments)

    ###########################################################################

    @cached_property
    def rehearsal_marks(self) -> dict[str, int]:
        """A dictionary mapping rehearsal marks to measure numbers"""

        rv: dict[str, int] = {}
        for token in self.channels[0]:
            if isinstance(token, Measure):
                measure = token.range[0]
            if isinstance(token, RehearsalMark):
                rv[token.mark] = measure

        return rv

    ###########################################################################

    @cached_property
    def tokens(self) -> list[Token]:
        tokens: list[Token] = []

        for channel in self.channels:
            tokens.extend(channel)
            tokens.append(ChannelDelim())

        return tokens


###############################################################################
# API function definitions
###############################################################################


def dynamics(song: Song, inst: str) -> set[Dynamics]:
    rv: set[Dynamics] = set()
    match = False

    for channel in song.channels:
        # TODO: This is a hack,
        last_dyn = Dynamics.MF
        for token in channel:
            match token:
                case Instrument(name, _):
                    match = inst == name
                case Dynamic(level):
                    last_dyn = level
                case Crescendo(_, target, _):
                    last_dyn = Dynamics(target)
                case Note() if match:
                    rv.add(last_dyn)
    return rv


###############################################################################


def transpose(song: Song, inst: str) -> int:
    rv = 0
    for token in song.tokens:
        match token:
            case Instrument(name, _) if name == inst:
                rv = token.transpose
                break
    return rv


#    def unmapped_notes(
#        self, inst_name: str, inst: InstrumentConfig
#    ) -> list[tuple[music21.pitch.Pitch, NoteHead]]:
#        rv = list()
#
#        instrument = inst if inst.multisample else None
#        for channel in self.channels:
#            rv.extend(channel.unmapped(inst_name, instrument))
#
#        return dedupe_notes(rv)
