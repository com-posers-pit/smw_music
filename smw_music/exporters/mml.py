# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Logic for generating MML files."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import os
import shutil
from copy import deepcopy
from datetime import datetime
from enum import Enum, auto
from functools import singledispatchmethod
from pathlib import PurePosixPath

# Library imports
from mako.template import Template  # type: ignore
from music21.pitch import Pitch

# Package imports
from smw_music import RESOURCES, __version__, amk
from smw_music.song import (
    Annotation,
    Artic,
    Clef,
    CrescDelim,
    Crescendo,
    Dynamic,
    Instrument,
    Loop,
    LoopDelim,
    LoopRef,
    Measure,
    Note,
    RehearsalMark,
    Repeat,
    Rest,
    Slur,
    Song,
    Tempo,
    Token,
    Triplet,
)
from smw_music.spcmw import (
    InstrumentConfig,
    InstrumentSample,
    Project,
    SampleSource,
)

from .common import Exporter

###############################################################################
# Private function definitions
###############################################################################


def notelen_str(notelen: int) -> str:
    rv = f"l{notelen}"
    return rv


###############################################################################
# API class definitions
###############################################################################


class SlurState(Enum):
    SLUR_IDLE = auto()
    SLUR_ACTIVE = auto()
    SLUR_END = auto()


###############################################################################


class MmlExporter(Exporter):
    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self, project: Project, song: Song | None = None) -> None:
        super().__init__(project, song)

        self.instruments: dict[str, InstrumentConfig]
        self.octave: int = 4
        self.default_note_len: int = 8
        self.grace: bool = False
        self.measure_numbers: bool = False
        self.slur: SlurState = SlurState.SLUR_IDLE
        self.tie: bool = False
        self.legato: bool = False
        self.articulation: Artic = Artic.NORMAL
        self.last_percussion: str = ""
        self.directives: list[str] = []

        self._instrument: InstrumentConfig
        self._active_sample_name: str
        self._active_sample: InstrumentSample
        self._in_loop: bool
        self._in_triplet: bool

    ###########################################################################

    def _append(self, directive: str = "\n") -> None:
        self.directives.append(directive)

    ###########################################################################

    @singledispatchmethod
    def emit(self, token: Token) -> None:
        raise NotImplementedError

    ###########################################################################

    @emit.register
    def _(self, token: Annotation) -> None:
        self._append(token.text)

    ###########################################################################

    @emit.register
    def _(self, token: CrescDelim) -> None:
        pass

    ###########################################################################

    @emit.register
    def _(self, token: Clef) -> None:
        self.percussion = token.percussion

    ###########################################################################

    @emit.register
    def _(self, token: Crescendo) -> None:
        cmd = "CRESC" if token.cresc else "DIM"
        self._append(f"{cmd}${token.duration:02X}$_{token.target.upper()}")

    ###########################################################################

    @emit.register
    def _(self, token: Dynamic) -> None:
        self._append(f"v{token.level.upper()}")

    ###########################################################################

    @emit.register
    def _(self, token: Instrument) -> None:
        name = token.name
        self._instrument = self.instruments[name]
        self._active_sample_name = ""

        if not self._instrument.multisample:
            self.octave = self._instrument.samples[""].default_octave
            self._append(f"@{name}")

    ###########################################################################

    @emit.register
    def _(self, token: Loop) -> None:
        if token.superloop:
            open_dir = "[["
            close_dir = "]]"
        else:
            open_dir = f"({token.loop_id})["
            close_dir = "]"
        if token.repeats > 1:
            close_dir += str(token.repeats)

        self._append(open_dir)
        self._in_loop = True

        self.generate(token.tokens)

        self._in_loop = False
        self._append(close_dir)

    ###########################################################################

    @emit.register
    def _(self, token: LoopDelim) -> None:
        pass

    ###########################################################################

    @emit.register
    def _(self, token: LoopRef) -> None:
        repeats = f"{token.repeats}" if token.repeats > 1 else ""
        self._append(f"({token.loop_id}){repeats}")

    ###########################################################################

    @emit.register
    def _(self, token: Measure) -> None:
        comment = ""
        if self.measure_numbers:
            if len(token.range) == 1:
                comment = f"; Measure {token.number}"
            else:
                comment = f"; Measures {token.range[0]}-{token.range[-1]}"

        self._append(f"{comment}\n")

    ###########################################################################

    @emit.register
    def _(self, token: RehearsalMark) -> None:
        self._append()
        self._append(";====================\n")
        self._append(f"; {token.mark}\n")
        self._append(";====================\n")
        self._append()
        if self.default_note_len:
            self._append(notelen_str(self.default_note_len))
            self._append()

    ###########################################################################

    @emit.register
    def _(self, token: Repeat) -> None:
        if token.start:
            self._append("/")

    ###########################################################################

    @emit.register
    def _(self, token: Rest) -> None:
        directive = "r"
        if token.duration != self.default_note_len:
            directive += str(token.duration)
        directive += token.dots * "."

        self._append(directive)

    ###########################################################################

    @emit.register
    def _(self, token: Slur) -> None:
        self.slur = (
            SlurState.SLUR_ACTIVE if token.start else SlurState.SLUR_END
        )

    ###########################################################################

    @emit.register
    def _(self, token: Tempo) -> None:
        # Magic BPM -> MML/SPC tempo conversion
        tempo = int(token.bpm * 255 / 625)
        self._append(f"t{tempo}")

    ###########################################################################

    @emit.register
    def _(self, token: Triplet) -> None:
        self._in_triplet = token.start
        self._append("{" if token.start else "}")

    ###########################################################################

    @emit.register
    def _(self, token: Note) -> None:
        inst = self._instrument
        if token.grace:
            self.grace = True

        note = inst.emit_note(token)

        pitch, sample = note
        percussion = inst.samples[sample].percussion

        if (self._active_sample_name != sample) and not percussion:
            if sample:
                self._append(f"@{sample}")
                self.octave = inst.samples[sample].default_octave
            else:
                # This is a fallback for when a sample isn't found
                self.octave = inst.sample.default_octave
                self._append(
                    f"@{inst.sample.builtin_sample_index} o{self.octave}"
                )

        self._active_sample_name = sample
        self._active_sample = inst.samples[sample]

        if not percussion:
            self._emit_octave(pitch)
            self.last_percussion = ""

        if self.tie:
            directive = "^"
        else:
            if not percussion:
                directive = pitch.name.lower().replace("#", "+")
            else:
                directive = sample
                # This exclusion is related to some special logic in N-SPC
                # where these percussion samples triggered on @ rather than on
                # a note being used
                if 18 < inst.samples[sample].builtin_sample_index < 30:
                    self.last_percussion = directive
                elif (directive == self.last_percussion) and not self._in_loop:
                    self.last_percussion = directive
                    directive += "n"
                else:
                    self.last_percussion = directive

        directive += self._calc_note_length(token)

        if not self.tie and (token.articulation != self.articulation):
            lut = {
                Artic.NORMAL: "qDEF",
                Artic.ACCENT: "qACC",
                Artic.STACCATO: "qSTAC",
                Artic.ACCSTAC: "qACCSTAC",
            }
            self._append(lut[token.articulation])
            self.articulation = token.articulation

        if token.tie == "start":
            self.tie = True

        self._start_legato()

        self._append(directive)

        if token.tie == "stop":
            self.tie = False

        if not token.grace:
            self.grace = False

        self._stop_legato()
        self._in_loop = False

    ###########################################################################

    def do_export(self) -> str:
        proj = self.project
        sets = self.project.settings

        # If starting after the first measure, disable loop analysis because
        # things might be badly broken
        if sets.start_measure != 1:
            sets.loop_analysis = False
            sets.superloop_analysis = False

        self._reduce(sets.loop_analysis, sets.superloop_analysis)

        # TODO: A bit of a hack to allow starting at a later measure
        if sets.start_measure != 1:
            for channel in self._reduced_channels:
                to_drop = sets.start_measure - 1
                tokens: list[Token] = []
                for n, token in enumerate(channel.tokens):
                    if isinstance(
                        token, (Dynamic, Instrument, Measure, Tempo, Repeat)
                    ):
                        tokens.append(token)
                        if isinstance(token, Measure):
                            to_drop -= 1
                    if to_drop == 0:
                        tokens.extend(channel.tokens[n + 1 :])
                        break
                channel.tokens = tokens

        self._validate()
        channels = [
            x.generate_mml(self.instruments, proj.measure_numbers)
            for x in self._reduced_channels
        ]

        build_dt = ""
        if include_dt:
            build_dt = datetime.utcnow().isoformat(" ", "seconds") + " UTC"

        instruments = deepcopy(self.instruments)
        inst_samples: dict[str, InstrumentSample] = {}

        for inst_name, inst in instruments.items():
            if inst.multisample:
                inst_samples.update(inst.multisamples)
            else:
                inst_samples[inst_name] = inst.samples[""]

        samples: list[tuple[str, str, int]] = []
        sample_id = 30

        for sample in inst_samples.values():
            if sample.sample_source == SampleSource.SAMPLEPACK:
                fname = str(
                    PurePosixPath(sample.pack_sample[0])
                    / sample.pack_sample[1]
                )
                samples.append((fname, sample.brr_str, sample_id))
                sample.instrument_idx = sample_id
                sample_id += 1
            if sample.sample_source == SampleSource.BRR:
                fname = sample.brr_fname.name
                samples.append((fname, sample.brr_str, sample_id))
                sample.instrument_idx = sample_id
                sample_id += 1

        # Overwrite muted/soloed instrument sample numbers
        solo = any(sample.solo for sample in inst_samples.values())
        mute = any(sample.mute for sample in inst_samples.values())
        solo |= any(inst.solo for inst in instruments.values())
        mute |= any(inst.mute for inst in instruments.values())

        if solo or mute:
            samples.append(("../EMPTY.brr", "$00 $00 $00 $00 $00", sample_id))

            for inst_sample in inst_samples.values():
                if inst_sample.mute or (solo and not inst_sample.solo):
                    inst_sample.sample_source = SampleSource.OVERRIDE
                    inst_sample.instrument_idx = sample_id

            # Not necessary, but we keep it for consistency's sake
            sample_id += 1

        tmpl = Template(RESOURCES / "mml.txt")  # nosec B702

        rv = tmpl.render(
            version=__version__,
            global_legato=global_legato,
            song=self,
            channels=channels,
            datetime=build_dt,
            echo_config=echo_config,
            inst_samples=inst_samples,
            custom_samples=samples,
            dynamics=list(Dynamics),
            sample_path=str(sample_path),
            sample_groups=sample_groups,
        )

        rv = rv.replace(" ^", "^")
        rv = rv.replace(" ]", "]")

        # This last bit removes any empty lines at the end (these don't
        # normally show up, but can if the last section in the last staff is
        # empty.
        rv = str(rv).rstrip() + "\n"

        if fname is not None:
            with open(fname, "w", newline="\r\n") as fobj:
                fobj.write(rv.encode("ascii", "ignore"))

        return rv

    ###########################################################################

    def finalize(self) -> None:
        bad_samples = self._check_bad_tune()
        if bad_samples:
            msg = "\n".join(
                f"{inst}{f':{samp}' if samp else ''} has 0.0 tuning"
                for inst, samp in bad_samples
            )

            # TODO: Report errors from bad samples
            msg

    ###########################################################################

    def prepare(self) -> None:
        state = self.state
        fname = self.state.mml_fname  # use self.state so assert is captured

        amk.update_sample_groups_file(
            self._project_path,
            state.builtin_sample_group,
            state.builtin_sample_sources,
        )

        if os.path.exists(fname):
            shutil.copy2(fname, f"{fname}.bak")

        # TODO Move this into the to_mml_file
        sample_group = "optimized"
        match state.builtin_sample_group:
            case amk.BuiltinSampleGroup.DEFAULT:
                sample_group = "default"
            case amk.BuiltinSampleGroup.OPTIMIZED:
                sample_group = "optimized"
            case amk.BuiltinSampleGroup.REDUX1:
                sample_group = "redux1"
            case amk.BuiltinSampleGroup.REDUX2:
                sample_group = "redux2"
            case amk.BuiltinSampleGroup.CUSTOM:
                sample_group = "custom"

        # TODO: Feed sample group back into export logic
        self.do_export()

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _start_legato(self) -> None:
        if not self.legato:
            if (self.slur == SlurState.SLUR_ACTIVE) or self.grace:
                self.legato = True
                self._append("LEGATO_ON")

    ###########################################################################

    def _stop_legato(self) -> None:
        if self.legato:
            if not (
                self.grace or (self.slur == SlurState.SLUR_ACTIVE) or self.tie
            ):
                self.legato = False
                self._append("LEGATO_OFF")

    ###########################################################################

    def _calc_note_length(self, token: Note) -> str:
        grace_length = 8
        note_length = ""

        if self.slur == SlurState.SLUR_END:
            self.slur = SlurState.SLUR_IDLE
            duration = 192 // token.duration
            duration = int(duration * (2 - 0.5**token.dots))
            self.legato = False
            if not self._in_triplet:
                note_length = f"=1 LEGATO_OFF ^={duration - 1}"
            else:
                note_length = f"=1 LEGATO_OFF ^={duration*2//3 - 1}"
        else:
            if not self.grace and not token.grace:
                if token.duration != self.default_note_len:
                    note_length = str(token.duration)
                note_length += token.dots * "."
            else:
                if token.grace:
                    if not self._in_triplet:
                        note_length = f"={grace_length}"
                else:
                    duration = 192 // token.duration
                    duration = int(duration * (2 - 0.5**token.dots))
                    note_length = f"={duration - grace_length}"

        return note_length

    ###########################################################################

    def _check_bad_tune(self) -> list[tuple[str, str]]:
        bad_samples = []
        for inst_name, inst in self.project.settings.instruments.items():
            for sample_name, sample in inst.samples.items():
                check_tune = sample.sample_source in [
                    SampleSource.BRR,
                    SampleSource.SAMPLEPACK,
                ]
                zero_tune = (sample.tune_setting, sample.subtune_setting) == (
                    0,
                    0,
                )
                if zero_tune and check_tune:
                    bad_samples.append((inst_name, sample_name))

        return bad_samples

    ###########################################################################

    def _emit_octave(self, pitch: Pitch) -> None:
        cur_octave = self.octave
        octave = pitch.implicitOctave + self._active_sample.octave_shift
        octave_diff = octave - cur_octave

        directive = ""
        if octave_diff > 0:
            directive = octave_diff * ">"
        else:
            directive = (-octave_diff) * "<"

        self.octave = octave
        if directive:
            self._append(directive)


# TODO: finish this
# # Standard library imports
# from collections import Counter
# from dataclasses import dataclass, field
# from itertools import takewhile
# from typing import Iterable, Iterator, TypeVar, cast
#
# # Library imports
# from music21.pitch import Pitch
#
# # Package imports
# from smw_music.song import (
#     Clef,
#     Error,
#     Instrument,
#     Note,
#     Playable,
#     RehearsalMark,
#     Token,
#     flatten,
# )
# from smw_music.spcmw.instrument import InstrumentConfig, NoteHead, dedupe_notes
#
# from .common import CRLF, notelen_str
# from .mml import MmlExporter
#
# ###############################################################################
# # Private variable/constant definitions
# ###############################################################################
#
# # Generic type variable
# _T = TypeVar("_T")
#
# ###############################################################################
# # Private function definitions
# ###############################################################################
#
#
# def _default_notelen(tokens: list[Token], section: bool = True) -> int:
#     if section:
#         tokens = list(
#             takewhile(lambda x: not isinstance(x, RehearsalMark), tokens)
#         )
#     playable = [x for x in flatten(tokens) if isinstance(x, Playable)]
#
#     notelen = _most_common([x.duration for x in playable]) if playable else 0
#
#     return notelen
#
#
# ###############################################################################
#
#
# def _most_common(container: Iterable[_T]) -> _T:
#     return Counter(container).most_common(1)[0][0]
#
# ###############################################################################
# # API class definitions
# ###############################################################################
#
#
# @dataclass
# class Channel:  # pylint: disable=too-many-instance-attributes
#     """
#     Single music channel.
#
#     Parameters
#     ----------
#     tokens: list
#         A list of valid channel tokens
#
#     Attributes
#     ----------
#     tokens: list
#         A list of elements in this tokens
#
#     Todo
#     ----
#     Parameterize grace note length?
#     """
#
#     tokens: list[Token]
#     _directives: list[str] = field(init=False, repr=False, compare=False)
#     _exporter: MmlExporter = field(init=False, repr=False, compare=False)
#
#     ###########################################################################
#     # Data model method definitions
#     ###########################################################################
#
#     def __getitem__(self, n: int) -> Token:
#         return self.tokens[n]
#
#     ###########################################################################
#
#     def __iter__(self) -> Iterator[Token]:
#         return iter(self.tokens)
#
#     ###########################################################################
#     # Private method definitions
#     ###########################################################################
#
#     def _reset_state(self, instruments: dict[str, InstrumentConfig]) -> None:
#         self._exporter = MmlExporter(instruments)
#
#         notelen = _default_notelen(flatten(self.tokens))
#         self._update_state_defaults(notelen)
#
#         if notelen:
#             self._exporter.directives = [notelen_str(notelen), CRLF]
#
#     ###########################################################################
#
#     def _update_state_defaults(self, notelen: int) -> None:
#         self._exporter.default_note_len = notelen
#
#     ###########################################################################
#     # API method definitions
#     ###########################################################################
#
#     def check(self, instruments: dict[str, InstrumentConfig]) -> list[str]:
#         """
#         Confirm that the channel's notes are acceptable.
#
#         Raises
#         ------
#         MusicXmlException :
#             Whenever an invalid percussion note is used, or when a musical note
#             outside octaves 1-6  is used.
#         """
#         msgs = []
#         tokens = flatten(self.tokens)
#         percussion = False
#
#         for token in filter(lambda x: isinstance(x, Error), tokens):
#             msgs.append(cast(Error, token).msg)
#         for token in filter(
#             lambda x: isinstance(x, (Clef, Instrument, Note)), tokens
#         ):
#             if isinstance(token, Clef):
#                 percussion = token.percussion
#             elif isinstance(token, Instrument):
#                 inst = instruments[token.name]
#             else:
#                 note = cast(Note, token)
#                 _, sample = inst.emit_note(note)
#                 octave_shift = (
#                     0 if percussion else inst.samples[sample].octave_shift
#                 )
#                 msgs.extend(note.check(octave_shift))
#         for token in filter(lambda x: isinstance(x, Playable), tokens):
#             msgs.extend(cast(Playable, token).duration_check())
#         return msgs
#
#     ###########################################################################
#
#     def generate_mml(
#         self,
#         instruments: dict[str, InstrumentConfig],
#         measure_numbers: bool = True,
#     ) -> str:
#         """
#         Generate this channel's AddMusicK MML text.
#
#         Parameters
#         ----------
#         measure_numbers: bool
#             True iff measure numbers should be included in MML
#
#         Return
#         ------
#         str
#             The MML text for this channel
#         """
#         self._reset_state(instruments)
#         self._exporter.measure_numbers = measure_numbers
#
#         for n, token in enumerate(self.tokens):
#             if isinstance(token, RehearsalMark):
#                 self._update_state_defaults(
#                     _default_notelen(flatten(self.tokens[n + 1 :]))
#                 )
#             self._exporter.emit(token)
#
#         lines = " ".join(self._exporter.directives).splitlines()
#         return CRLF.join(x.strip() for x in lines)
#
#     ###########################################################################
#
#     def unmapped(
#         self, inst_name: str, inst: InstrumentConfig | None
#     ) -> list[tuple[Pitch, NoteHead]]:
#         last_inst = ""
#         notes = list()
#         for token in self.tokens:
#             if isinstance(token, Instrument):
#                 last_inst = token.name
#             if isinstance(token, Note) and (last_inst == inst_name):
#                 if (inst is None) or (not inst.emit_note(token)[1]):
#                     notes.append((token.pitch, NoteHead(token.head)))
#
#         return dedupe_notes(notes)
