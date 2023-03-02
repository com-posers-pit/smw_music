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

# Package imports
from smw_music.music_xml.shared import CRLF, notelen_str
from smw_music.music_xml.tokens import (
    Annotation,
    Artic,
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
# API constant definitions
###############################################################################

# Weinberg:
# http://www.normanweinberg.com/uploads/8/1/6/4/81640608/940506pn_guildines_for_drumset.pdf
PERCUSSION_MAP = {
    "x": {
        "c6": "CR3_",
        "b5": "CR2_",
        "a5": "CR",
        "g5": "CH",
        "f5": "RD",
        "e5": "OH",
        "d5": "RD2_",
    },
    "normal": {
        "e5": "HT",
        "d5": "MT",
        "c5": "SN",
        "a4": "LT",
        "f4": "KD",
    },
}

###############################################################################
# API class definitions
###############################################################################


class Exporter:
    directives: list[str]

    def _append(self, directive: str) -> None:
        self.directives.append(directive)

    # This needs to be included to keep mypy from complaining in subclasses
    @singledispatchmethod
    def _emit(self, token: Token) -> None:
        raise NotImplementedError

    def generate(self, tokens: list[Token]) -> None:
        for token in tokens:
            self._emit(token)


###############################################################################


class SlurState(Enum):
    SLUR_IDLE = auto()
    SLUR_ACTIVE = auto()
    SLUR_END = auto()


###############################################################################


@dataclass
class MmlExporter(Exporter):  # pylint: disable=too-many-instance-attributes
    instr_octave_map: dict[str, int]
    octave: int = 4
    default_note_len: int = 8
    grace: bool = False
    measure_numbers: bool = False
    slur: SlurState = SlurState.SLUR_IDLE
    tie: bool = False
    legato: bool = False
    percussion: bool = False
    articulation: Artic = Artic.NORMAL
    optimize_percussion: bool = False
    last_percussion: str = ""
    directives: list[str] = field(default_factory=list)
    _in_loop: bool = field(default=False, init=False)
    _in_triplet: bool = False

    ###########################################################################

    @singledispatchmethod
    def _emit(self, token: Token) -> None:
        raise NotImplementedError

    ###########################################################################

    @_emit.register
    def _(self, token: Annotation) -> None:
        self._append(token.text)

    ###########################################################################

    @_emit.register
    def _(self, token: CrescDelim) -> None:
        pass

    ###########################################################################

    @_emit.register
    def _(self, token: Crescendo) -> None:
        cmd = "CRESC" if token.cresc else "DIM"
        self._append(f"{cmd}${token.duration:02X}$_{token.target.upper()}")

    ###########################################################################

    @_emit.register
    def _(self, token: Dynamic) -> None:
        self._append(f"v{token.level.upper()}")

    ###########################################################################

    @_emit.register
    def _(self, token: Instrument) -> None:
        instr = token.name
        self._append(f"@{instr}")
        self.octave = self.instr_octave_map.get(instr, 3)

    ###########################################################################

    @_emit.register
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

    @_emit.register
    def _(self, token: LoopDelim) -> None:
        pass

    ###########################################################################

    @_emit.register
    def _(self, token: LoopRef) -> None:
        repeats = f"{token.repeats}" if token.repeats > 1 else ""
        self._append(f"({token.loop_id}){repeats}")

    ###########################################################################

    @_emit.register
    def _(self, token: Measure) -> None:
        comment = ""
        if self.measure_numbers:
            if len(token.range) == 1:
                comment = f"; Measure {token.number}"
            else:
                comment = f"; Measures {token.range[0]}-{token.range[-1]}"

        self._append(f"{comment}{CRLF}")

    ###########################################################################

    @_emit.register
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

    @_emit.register
    def _(self, token: Repeat) -> None:
        if token.start:
            self._append("/")

    ###########################################################################

    @_emit.register
    def _(self, token: Rest) -> None:
        directive = "r"
        if token.duration != self.default_note_len:
            directive += str(token.duration)
        directive += token.dots * "."

        self._append(directive)

    ###########################################################################

    @_emit.register
    def _(self, token: Slur) -> None:
        self.slur = (
            SlurState.SLUR_ACTIVE if token.start else SlurState.SLUR_END
        )

    ###########################################################################

    @_emit.register
    def _(self, token: Tempo) -> None:
        # Magic BPM -> MML/SPC tempo conversion
        tempo = int(token.bpm * 255 / 625)
        self._append(f"t{tempo}")

    ###########################################################################

    @_emit.register
    def _(self, token: Triplet) -> None:
        self._in_triplet = token.start
        self._append("{" if token.start else "}")

    ###########################################################################

    @_emit.register
    def _(self, token: Vibrato) -> None:
        self._append("$DE$01$23$45" if token.start else "VIB_OFF")

    ###########################################################################

    @_emit.register
    def _(self, token: Note) -> None:
        if token.grace:
            self.grace = True

        if not self.percussion:
            self._emit_octave(token)

        if self.tie:
            directive = "^"
        else:
            if not self.percussion:
                directive = token.name
            else:
                directive = PERCUSSION_MAP[token.head][
                    token.name + str(token.octave + 1)
                ]
                if self.optimize_percussion:
                    if (
                        directive == self.last_percussion
                    ) and not self._in_loop:
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

    def _emit_octave(self, token: Note) -> None:
        cur_octave = self.octave
        octave = token.octave
        octave_diff = octave - cur_octave

        directive = ""
        if octave_diff > 0:
            directive = octave_diff * ">"
        else:
            directive = (-octave_diff) * "<"

        self.octave = octave
        if directive:
            self._append(directive)
