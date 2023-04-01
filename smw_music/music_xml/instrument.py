# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only


###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum, auto
from functools import cache
from pathlib import Path

# Library imports
from music21.pitch import Pitch

# Package imports
from smw_music.music_xml.tokens import Note
from smw_music.utils import hexb

###############################################################################
# Private variable definitions
###############################################################################


@cache
def _symbol_map() -> dict[str, "NoteHead"]:
    return {
        "normal": NoteHead.NORMAL,
        "x": NoteHead.X,
        "o": NoteHead.O,
        "+": NoteHead.PLUS,
        "⮾": NoteHead.TENSOR,
        "▲": NoteHead.TRIUP,
        "▼": NoteHead.TRIDOWN,
        "/": NoteHead.SLASH,
        "◆": NoteHead.DIAMOND,
    }


###############################################################################


@cache
def _symbol_unmap() -> dict["NoteHead", str]:
    return {v: k for k, v in _symbol_map().items()}


###############################################################################
# API class definitions
###############################################################################


class Artic(IntEnum):
    STAC = auto()
    ACC = auto()
    DEF = auto()
    ACCSTAC = auto()

    ###########################################################################

    def __str__(self) -> str:
        return self.name


###############################################################################


@dataclass
class ArticSetting:
    length: int
    volume: int

    ###########################################################################

    @property
    def setting(self) -> int:
        return (0x7 & self.length) << 4 | (0xF & self.volume)


###############################################################################


class Dynamics(IntEnum):
    PPPP = auto()
    PPP = auto()
    PP = auto()
    P = auto()
    MP = auto()
    MF = auto()
    F = auto()
    FF = auto()
    FFF = auto()
    FFFF = auto()

    ###########################################################################

    def __str__(self) -> str:
        return self.name


###############################################################################


class GainMode(IntEnum):
    DIRECT = auto()
    INCLIN = auto()
    INCBENT = auto()
    DECLIN = auto()
    DECEXP = auto()


###############################################################################


class NoteHead(StrEnum):
    NORMAL = "normal"
    X = "x"
    O = "o"
    PLUS = "cross"
    TENSOR = "circle-x"
    TRIUP = "arrow up"
    TRIDOWN = "arrow down"
    SLASH = "slash"
    DIAMOND = "diamond"

    ###########################################################################

    @classmethod
    def from_symbol(cls, symbol: str) -> "NoteHead":
        return _symbol_map()[symbol]

    ###########################################################################

    @property
    def symbol(self) -> str:
        return _symbol_unmap()[self]


###############################################################################


class SampleSource(IntEnum):
    BUILTIN = auto()
    SAMPLEPACK = auto()
    BRR = auto()
    OVERRIDE = auto()


###############################################################################


@dataclass
class InstrumentSample:
    default_octave: int = 3
    octave_shift: int = -1
    dynamics: dict[Dynamics, int] = field(
        default_factory=lambda: {
            Dynamics.PPPP: 26,
            Dynamics.PPP: 38,
            Dynamics.PP: 64,
            Dynamics.P: 90,
            Dynamics.MP: 115,
            Dynamics.MF: 141,
            Dynamics.F: 179,
            Dynamics.FF: 217,
            Dynamics.FFF: 230,
            Dynamics.FFFF: 245,
        }
    )
    dyn_interpolate: bool = False
    artics: dict[Artic, ArticSetting] = field(
        default_factory=lambda: {
            Artic.DEF: ArticSetting(0x7, 0xE),
            Artic.STAC: ArticSetting(0x6, 0xE),
            Artic.ACC: ArticSetting(0x7, 0xF),
            Artic.ACCSTAC: ArticSetting(0x6, 0xF),
        }
    )
    pan_enabled: bool = False
    pan_setting: int = 10
    pan_invert: tuple[bool, bool] = (False, False)
    sample_source: SampleSource = SampleSource.BUILTIN
    builtin_sample_index: int = 0
    pack_sample: tuple[str, Path] = ("", Path())
    brr_fname: Path = field(default_factory=Path)
    # TODO: see if the following settings can be rolled into a Sample object
    adsr_mode: bool = True
    attack_setting: int = 0
    decay_setting: int = 0
    sus_level_setting: int = 0
    sus_rate_setting: int = 0
    gain_mode: GainMode = GainMode.DIRECT
    gain_setting: int = 0
    tune_setting: int = 0
    subtune_setting: int = 0
    mute: bool = False
    solo: bool = False
    llim: Pitch = field(default_factory=lambda: Pitch("A", octave=0))
    ulim: Pitch = field(default_factory=lambda: Pitch("C", octave=7))
    notehead: NoteHead = NoteHead.NORMAL
    start: Pitch = field(default_factory=lambda: Pitch("A", octave=0))

    _instrument_idx: int = field(default=0, init=False)

    ###########################################################################
    # API method definitions
    ###########################################################################

    def emit(
        self, note: Pitch, notehead: NoteHead | None = None
    ) -> Pitch | None:
        match = True
        match &= self.llim <= note <= self.ulim
        if notehead is not None:
            match &= self.notehead == notehead

        if match:
            return Pitch(note.ps - self.llim.ps + self.start.ps)
        return None

    ###########################################################################
    # Property definitions
    ###########################################################################

    @property
    def brr_setting(self) -> tuple[int, int, int, int, int]:
        vxadsr1 = int(self.adsr_mode) << 7
        vxadsr1 |= self.decay_setting << 4
        vxadsr1 |= self.attack_setting
        vxadsr2 = (self.sus_level_setting << 5) | self.sus_rate_setting

        match self.gain_mode:
            case GainMode.DIRECT:
                vxgain = 0x80 | self.gain_setting
            case GainMode.INCLIN:
                vxgain = 0x40 | self.gain_setting
            case GainMode.INCBENT:
                vxgain = 0x60 | self.gain_setting
            case GainMode.DECLIN:
                vxgain = 0x00 | self.gain_setting
            case GainMode.DECEXP:
                vxgain = 0x20 | self.gain_setting

        return (
            vxadsr1,
            vxadsr2,
            vxgain,
            self.tune_setting,
            self.subtune_setting,
        )

    ###########################################################################

    @brr_setting.setter
    def brr_setting(self, val: str) -> None:
        val = val.strip()
        # The [1:] drops the initial '$'
        regs = [int(x[1:], 16) for x in val.split(" ")]

        self.adsr_mode = bool(regs[0] >> 7)
        self.decay_setting = 0x7 & (regs[0] >> 4)
        self.attack_setting = 0xF & regs[0]
        self.sus_level_setting = regs[1] >> 5
        self.sus_rate_setting = 0x1F & regs[1]
        if regs[2] & 0x80:
            self.gain_mode = GainMode.DIRECT
            self.gain_setting = regs[2] & 0x7F
        else:
            self.gain_setting = regs[2] & 0x1F
            match regs[2] >> 5:
                case 0b00:
                    self.gain_mode = GainMode.DECLIN
                case 0b01:
                    self.gain_mode = GainMode.DECEXP
                case 0b10:
                    self.gain_mode = GainMode.INCLIN
                case 0b11:
                    self.gain_mode = GainMode.INCBENT

        self.tune_setting = regs[3]
        self.subtune_setting = regs[4]

    ###########################################################################

    @property
    def brr_str(self) -> str:
        return " ".join(map(hexb, self.brr_setting))

    ###########################################################################

    @property
    def instrument_idx(self) -> int:
        if self.sample_source == SampleSource.BUILTIN:
            return self.builtin_sample_index
        return self._instrument_idx

    ###########################################################################

    @instrument_idx.setter
    def instrument_idx(self, idx: int) -> None:
        if self.sample_source != SampleSource.BUILTIN:
            self._instrument_idx = idx

    ###########################################################################

    @property
    def pan_description(self) -> str:
        pan = self.pan_setting
        if pan == 10:
            text = "C"
        elif pan < 10:
            text = f"{10*(10 - pan)}% R"
        else:
            text = f"{10*(pan - 10)}% L"

        return text

    ###########################################################################

    @property
    def pan_str(self) -> str:
        inv = self.pan_invert
        rv = f"y{self.pan_setting}"
        if any(inv):
            rv += f",{int(inv[0])},{int(inv[1])}"
        return rv

    ###########################################################################

    @property
    def percussion(self) -> bool:
        return self.ulim == self.llim

    ###########################################################################

    @property
    def percussion_note(self) -> int:
        return self.start.name.lower().replace("#", "-")

    ###########################################################################

    @property
    def percussion_octave(self) -> int:
        return self.start.octave


###############################################################################


@dataclass
class InstrumentConfig:
    transpose: int = 0
    dynamics_present: set[Dynamics] = field(
        default_factory=lambda: set(Dynamics)
    )
    mute: bool = False
    solo: bool = False
    multisamples: dict[str, InstrumentSample] = field(
        default_factory=lambda: {}
    )

    sample: InstrumentSample = field(default_factory=InstrumentSample)

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_name(
        cls, name: str, **kwargs: int | set[Dynamics] | bool
    ) -> "InstrumentConfig":
        name = name.lower()

        if name == "drumset":
            # Weinberg:
            # http://www.normanweinberg.com/uploads/8/1/6/4/81640608/940506pn_guildines_for_drumset.pdf
            sample_defs = [
                ("CR3_", Pitch("C6"), NoteHead.X, 22),
                ("CR2_", Pitch("B5"), NoteHead.X, 22),
                ("CR", Pitch("A5"), NoteHead.X, 22),
                ("CH", Pitch("G5"), NoteHead.X, 22),
                ("RD", Pitch("F5"), NoteHead.X, 22),
                ("OH", Pitch("E5"), NoteHead.X, 22),
                ("RD2_", Pitch("D5"), NoteHead.X, 22),
                ("HT", Pitch("E5"), NoteHead.NORMAL, 24),
                ("MT", Pitch("D5"), NoteHead.NORMAL, 23),
                ("SN", Pitch("C5"), NoteHead.NORMAL, 10),
                ("LT", Pitch("A4"), NoteHead.NORMAL, 21),
                ("KD", Pitch("F4"), NoteHead.NORMAL, 21),
            ]

            multisamples = {
                name: InstrumentSample(
                    llim=pitch,
                    ulim=pitch,
                    start=pitch,
                    notehead=notehead,
                    builtin_sample_index=idx,
                )
                for name, pitch, notehead, idx in sample_defs
            }

            inst = cls(multisamples=multisamples, **kwargs)
        else:
            # Default instrument mapping, from Wakana's tutorial
            inst_map = {
                "flute": 0,
                "marimba": 3,
                "cello": 4,
                "trumpet": 6,
                "bass": 8,
                "bassguitar": 8,
                "electricbass": 8,
                "piano": 13,
                "guitar": 17,
                "electricguitar": 17,
            }

            inst = cls(**kwargs)
            inst.sample.builtin_sample_index = inst_map.get(name, 0)

        return inst

    ###########################################################################
    # API method definitions
    ###########################################################################

    def emit_note(self, note: Note) -> tuple[Pitch, str]:
        head = NoteHead(note.head)

        if self.multisample:
            for name, sample in self.multisamples.items():
                sample_out = sample.emit(note.pitch, head)
                if sample_out is not None:
                    return (sample_out, name)

        return (self.sample.emit(note.pitch, None), "")

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def multisample(self) -> bool:
        return bool(len(self.multisamples))

    ###########################################################################

    @property
    def samples(self) -> dict[str, InstrumentSample]:
        samples = {"": self.sample}
        samples.update(self.multisamples)
        return samples

    ###########################################################################

    @samples.setter
    def samples(self, value: dict[str, InstrumentSample]) -> None:
        self.multisamples = dict(value)
        self.sample = self.multisamples.pop("")
