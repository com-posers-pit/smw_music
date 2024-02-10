# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only


###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass, field
from enum import IntEnum, auto
from pathlib import Path
from typing import cast

# Library imports
from music21.pitch import Pitch

# Package imports
from smw_music.song import Note, NoteHead
from smw_music.spc700 import SAMPLE_FREQ, Envelope
from smw_music.utils import hexb

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


class SampleSource(IntEnum):
    BUILTIN = auto()
    SAMPLEPACK = auto()
    BRR = auto()
    OVERRIDE = auto()


###############################################################################


class TuneSource(IntEnum):
    AUTO = auto()
    MANUAL_NOTE = auto()
    MANUAL_FREQ = auto()


###############################################################################


@dataclass
class Tuning:
    source: TuneSource = TuneSource.AUTO
    semitone_shift: int = 0
    pitch: Pitch = field(default_factory=lambda: Pitch("C", octave=4))
    frequency: float = Pitch("C", octave=4).frequency
    sample_freq: float = SAMPLE_FREQ
    output: Pitch = field(default_factory=lambda: Pitch("C", octave=4))


###############################################################################


@dataclass
class InstrumentSample:
    default_octave: int = 3
    octave_shift: int = 0
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
    envelope: Envelope = field(default_factory=Envelope)
    tune_setting: int = 0
    subtune_setting: int = 0
    mute: bool = False
    solo: bool = False
    llim: Pitch = field(default_factory=lambda: Pitch("A", octave=0))
    ulim: Pitch = field(default_factory=lambda: Pitch("C", octave=7))
    notehead: NoteHead = NoteHead.NORMAL
    start: Pitch = field(default_factory=lambda: Pitch("A", octave=0))
    tuning: Tuning = field(default_factory=Tuning)
    track: bool = False
    echo: bool = False

    _instrument_idx: int = field(default=0, init=False)

    ###########################################################################
    # API method definitions
    ###########################################################################

    def emit(
        self, note: Pitch, notehead: NoteHead | None = None
    ) -> Pitch | None:
        # This is a check to see if llim <= note <= ulim.
        # Equality tests don't check for enharmonic equivalence (i.e.
        # "F3 natural" != "F3").  So we need to test the ends separately from
        # testing inside the interval
        llim_match = self.llim.isEnharmonic(note)
        ulim_match = self.ulim.isEnharmonic(note)
        between = self.llim < note < self.ulim

        match = llim_match or between or ulim_match

        if notehead is not None:
            match &= self.notehead == notehead

        if match:
            return Pitch(note.ps - self.llim.ps + self.start.ps)

        return None

    ###########################################################################

    def track_settings(self, other: "InstrumentSample") -> None:
        if self.track:
            self.dynamics = other.dynamics.copy()
            self.dyn_interpolate = other.dyn_interpolate
            self.artics = other.artics.copy()
            self.pan_enabled = other.pan_enabled
            self.pan_setting = other.pan_setting
            self.pan_invert = other.pan_invert

    ###########################################################################
    # Property definitions
    ###########################################################################

    @property
    def brr_setting(self) -> tuple[int, int, int, int, int]:
        return (
            self.envelope.adsr1_reg,
            self.envelope.adsr2_reg,
            self.envelope.gain_reg,
            self.tune_setting,
            self.subtune_setting,
        )

    ###########################################################################

    @brr_setting.setter
    def brr_setting(self, val: str) -> None:
        val = val.strip()
        # The [1:] drops the initial '$'
        regs = [int(x[1:], 16) for x in val.split(" ")]

        self.envelope = Envelope.from_regs(*regs[:3])
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
        return self.ulim.isEnharmonic(self.llim)

    ###########################################################################

    @property
    def percussion_note(self) -> str:
        return self.start.name.lower().replace("#", "-")

    ###########################################################################

    @property
    def percussion_octave(self) -> int:
        return self.start.implicitOctave


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
            inst = cls.make_percussion(name, **kwargs)
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

            # TODO: address this mypy error
            inst = cls(**kwargs)  # type: ignore
            inst.sample.builtin_sample_index = inst_map.get(name, 0)

        return inst

    ###########################################################################

    @classmethod
    def make_percussion(
        cls, name: str, **kwargs: int | set[Dynamics] | bool
    ) -> "InstrumentConfig":
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

        # TODO: address this mypy error
        return cls(multisamples=multisamples, **kwargs)  # type: ignore

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

        # Parent instrument is guaranteed to have the pitch
        pitch = cast(Pitch, self.sample.emit(note.pitch, None))
        return (pitch, "")

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


###############################################################################
# API function definitions
###############################################################################


def dedupe_notes(
    notes: list[tuple[Pitch, NoteHead]]
) -> list[tuple[Pitch, NoteHead]]:
    rv: list[tuple[Pitch, NoteHead]] = []
    for in_note in notes:
        in_pitch, in_head = in_note
        for out_note in rv:
            out_pitch, out_head = out_note
            if in_pitch.isEnharmonic(out_pitch) and in_head == out_head:
                break
        else:
            rv.append(in_note)

    return rv
