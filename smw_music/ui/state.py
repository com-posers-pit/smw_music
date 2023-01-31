# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard UI state."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass
from enum import IntEnum, auto

###############################################################################
# API class definitions
###############################################################################


class Artic(IntEnum):
    ACCENT = auto()
    ACCSTAC = auto()
    DEFAULT = auto()
    STACCATO = auto()


###############################################################################


@dataclass
class ArticSetting:
    length: int
    volume: int


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


###############################################################################


class EchoCh(IntEnum):
    GLOBAL = auto()
    CH0 = auto()
    CH1 = auto()
    CH2 = auto()
    CH3 = auto()
    CH4 = auto()
    CH5 = auto()
    CH6 = auto()
    CH7 = auto()


###############################################################################


class GainMode(IntEnum):
    DIRECT = auto()
    INCLIN = auto()
    INCBENT = auto()
    DECLIN = auto()
    DECEXP = auto()


###############################################################################


class SampleSource(IntEnum):
    BUILTIN = auto()
    SAMPLEPACK = auto()
    BRR = auto()


###############################################################################


@dataclass
class State:
    musicxml_fname: str = ""
    mml_fname: str = ""
    loop_analysis: bool = False
    superloop_analysis: bool = False
    measure_numbers: bool = True
    dynamics_settings: dict[Dynamics, int] = {
        Dynamics.PPPP: 0,
        Dynamics.PPP: 0,
        Dynamics.PP: 0,
        Dynamics.P: 0,
        Dynamics.MP: 0,
        Dynamics.MF: 0,
        Dynamics.F: 0,
        Dynamics.FF: 0,
        Dynamics.FFF: 0,
        Dynamics.FFFF: 0,
    }
    dyn_interpolate: bool = False
    artic_settings: dict[Artic, ArticSetting] = {
        Artic.ACCENT: ArticSetting(0, 0),
        Artic.ACCSTAC: ArticSetting(0, 0),
        Artic.DEFAULT: ArticSetting(0, 0),
        Artic.STACCATO: ArticSetting(0, 0),
    }
    pan_enabled: bool = False
    pan_setting: int = 0
    sample_source: SampleSource = SampleSource.BUILTIN
    builtin_sample_index: int = 0
    pack_sample_index: int = 0
    brr_fname: str = ""
    adsr_mode: bool = True
    attack_setting: int = 0
    decay_setting: int = 0
    sus_level_setting: int = 0
    sus_rate_setting: int = 0
    gain_mode: GainMode = GainMode.DIRECT
    gain_setting: int = 0
    tune_setting: int = 0
    subtune_setting: int = 0
    global_volume: int = 0
    global_legato: bool = True
    echo_enable: dict[EchoCh, bool] = {
        EchoCh.GLOBAL: False,
        EchoCh.CH0: False,
        EchoCh.CH1: False,
        EchoCh.CH2: False,
        EchoCh.CH3: False,
        EchoCh.CH4: False,
        EchoCh.CH5: False,
        EchoCh.CH6: False,
        EchoCh.CH7: False,
    }
    echo_filter0: bool = True
    echo_left_setting: int = 0
    echo_right_setting: int = 0
    echo_feedback_setting: int = 0
    echo_delay_setting: int = 0

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
                vxgain = self.gain_setting
            case GainMode.INCLIN:
                vxgain = 0xC0 | self.gain_setting
            case GainMode.INCBENT:
                vxgain = 0xE0 | self.gain_setting
            case GainMode.DECLIN:
                vxgain = 0x80 | self.gain_setting
            case GainMode.DECEXP:
                vxgain = 0xA0 | self.gain_setting

        # The register values for the mode we're not in are don't care; exo
        # likes the convention of setting them to 0.  Who am I to argue?
        if self.adsr_mode:
            vxgain = 0
        else:
            vxadsr1 = 0
            vxadsr2 = 0

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
