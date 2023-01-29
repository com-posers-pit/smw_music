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
    pppp_setting: int = 0
    ppp_setting: int = 0
    pp_setting: int = 0
    p_setting: int = 0
    mp_setting: int = 0
    mf_setting: int = 0
    f_setting: int = 0
    ff_setting: int = 0
    fff_setting: int = 0
    ffff_setting: int = 0
    dyn_interpolate: bool = False
    default_artic_length: int = 0
    default_artic_volume: int = 0
    accent_length: int = 0
    accent_volume: int = 0
    staccato_length: int = 0
    staccato_volume: int = 0
    accstacc_length: int = 0
    accstacc_volume: int = 0
    pan_enabled: bool = False
    pan_setting: int = 0
    sample_source: SampleSource = SampleSource.BUILTIN
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
    echo_enable: bool = False
    echo_ch0_enable: bool = False
    echo_ch1_enable: bool = False
    echo_ch2_enable: bool = False
    echo_ch3_enable: bool = False
    echo_ch4_enable: bool = False
    echo_ch5_enable: bool = False
    echo_ch6_enable: bool = False
    echo_ch7_enable: bool = False
    echo_filter0: bool = True
    echo_left_setting: int = 0
    echo_right_setting: int = 0
    echo_feedback_setting: int = 0
    echo_delay_setting: int = 0

    @property
    def brr_setting(self) -> tuple[int, int, int, int, int]:
        return (0, 0, 0, 0, 0)
