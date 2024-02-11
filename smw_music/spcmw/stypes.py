# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""TypedDict definitions used in serialization."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from typing import TypedDict

###############################################################################
# API type definitions
###############################################################################


class EchoDict(TypedDict):
    vol_mag: list[float]
    vol_inv: list[bool]
    delay: int
    fb_mag: float
    fb_inv: bool
    fir_filt: int


###############################################################################


class InstrumentDict(TypedDict):
    mute: bool
    solo: bool
    samples: dict[str, "SampleDict"]


###############################################################################


class SampleDict(TypedDict):
    octave_shift: int
    dynamics: dict[str, int]
    interpolate_dynamics: bool
    articulations: dict[int, list[int]]
    pan_enabled: bool
    pan_setting: int
    pan_l_invert: bool
    pan_r_invert: bool
    sample_source: int
    builtin_sample_index: int
    pack_sample: list[str]
    brr_fname: str
    adsr_mode: bool
    attack_setting: int
    decay_setting: int
    sus_level_setting: int
    sus_rate_setting: int
    gain_mode: int
    gain_setting: int
    tune_setting: int
    subtune_setting: int
    mute: bool
    solo: bool
    llim: str
    ulim: str
    notehead: str
    start: str
    track: bool


###############################################################################


class ProjectDict(TypedDict):
    tool_version: str
    save_version: int
    time: str
    musicxml: str
    project_name: str
    composer: str
    title: str
    porter: str
    game: str
    loop_analysis: bool
    superloop_analysis: bool
    measure_numbers: bool
    global_volume: int
    global_legato: bool
    global_echo: bool
    echo: EchoDict
    instruments: dict[str, InstrumentDict]
    builtin_sample_group: int
    builtin_sample_sources: list[int]
