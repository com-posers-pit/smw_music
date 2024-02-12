# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Logic for generating MML files."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import singledispatchmethod
from pathlib import Path

# Library imports
from music21.pitch import Pitch

# Package imports
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
    Tempo,
    Token,
    Triplet,
)
from smw_music.spcmw import InstrumentConfig, InstrumentSample

from .common import CRLF, Exporter, notelen_str

###############################################################################
# API class definitions
###############################################################################


class SlurState(Enum):
    SLUR_IDLE = auto()
    SLUR_ACTIVE = auto()
    SLUR_END = auto()


###############################################################################


class MmlExporter(Exporter):  # pylint: disable=too-many-instance-attributes
    instruments: dict[str, InstrumentConfig] = field(default_factory=dict)
    octave: int = 4
    default_note_len: int = 8
    grace: bool = False
    measure_numbers: bool = False
    slur: SlurState = SlurState.SLUR_IDLE
    tie: bool = False
    legato: bool = False
    articulation: Artic = Artic.NORMAL
    last_percussion: str = ""

    _instrument: InstrumentConfig = field(init=False)
    _active_sample_name: str = field(init=False)
    _active_sample: InstrumentSample = field(init=False)
    _in_loop: bool = field(default=False, init=False)
    _in_triplet: bool = field(default=False, init=False)

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

        self._append(f"{comment}{CRLF}")

    ###########################################################################

    @emit.register
    def _(self, token: RehearsalMark) -> None:
        self._append(CRLF)
        self._append(f";===================={CRLF}")
        self._append(f"; {token.mark}{CRLF}")
        self._append(f";===================={CRLF}")
        self._append(CRLF)
        if self.default_note_len:
            self._append(notelen_str(self.default_note_len))
            self._append(CRLF)

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

    def export(self) -> str:
        proj = deepcopy(self.project)

        # If starting after the first measure, disable loop analysis because
        # things might be badly broken
        if proj.start_measure != 1:
            proj.loop_analysis = False
            proj.superloop_analysis = False

        self._reduce(proj.loop_analysis, proj.superloop_analysis)

        # TODO: A bit of a hack to allow starting at a later measure
        if proj.start_measure != 1:
            for channel in self._reduced_channels:
                to_drop = proj.start_measure - 1
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

        instruments = copy.deepcopy(self.instruments)
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
        rv = str(rv).rstrip() + CRLF

        if fname is not None:
            with open(fname, "wb") as fobj:
                fobj.write(rv.encode("ascii", "ignore"))

        return rv

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
