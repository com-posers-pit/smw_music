# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Logic for generating MML files."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import singledispatchmethod

# Library imports
from music21.pitch import Pitch

# Package imports
from smw_music.music_xml.instrument import InstrumentConfig, InstrumentSample
from smw_music.music_xml.shared import CRLF, notelen_str
from smw_music.music_xml.tokens import (
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
    Vibrato,
)

###############################################################################
# API class definitions
###############################################################################


class Exporter:
    directives: list[str]

    def _append(self, directive: str) -> None:
        self.directives.append(directive)

    # This needs to be included to keep mypy from complaining in subclasses
    @singledispatchmethod
    def emit(self, token: Token) -> None:
        raise NotImplementedError

    def generate(self, tokens: list[Token]) -> None:
        for token in tokens:
            self.emit(token)


###############################################################################


class SlurState(Enum):
    SLUR_IDLE = auto()
    SLUR_ACTIVE = auto()
    SLUR_END = auto()


###############################################################################


@dataclass
class MmlExporter(Exporter):  # pylint: disable=too-many-instance-attributes
    instruments: dict[str, InstrumentConfig]
    octave: int = 4
    default_note_len: int = 8
    grace: bool = False
    measure_numbers: bool = False
    slur: SlurState = SlurState.SLUR_IDLE
    tie: bool = False
    legato: bool = False
    articulation: Artic = Artic.NORMAL
    last_percussion: str = ""
    directives: list[str] = field(default_factory=list)

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
    def _(self, token: Vibrato) -> None:
        self._append("$DE$01$23$45" if token.start else "VIB_OFF")

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
        octave = pitch.octave + self._active_sample.octave_shift
        octave_diff = octave - cur_octave

        directive = ""
        if octave_diff > 0:
            directive = octave_diff * ">"
        else:
            directive = (-octave_diff) * "<"

        self.octave = octave
        if directive:
            self._append(directive)
