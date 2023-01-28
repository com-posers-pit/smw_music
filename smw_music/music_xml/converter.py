# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass, field
from pathlib import Path

###############################################################################
# API class definitions
###############################################################################


@dataclass
class ArticState:
    length: int
    volume: int


@dataclass
class ConverterState:
    musicxml_fname: Path | None
    mml_fname: Path | None
    loop_analysis: bool
    superloop_analysis: bool
    measure_numbers: bool
    volume: int
    global_legato: bool
    echo_config: "EchoState"
    instrument: dict[str, "InstrumentState"]


@dataclass
class DynamicsState:
    interpolate: bool
    pppp_dyn: int
    ppp_dyn: int
    pp_dyn: int
    p_dyn: int
    mp_dyn: int
    mf_dyn: int
    f_dyn: int
    ff_dyn: int
    fff_dyn: int
    ffff_dyn: int


@dataclass
class EchoState:
    enabled: bool
    ch0_enabled: bool
    ch1_enabled: bool
    ch2_enabled: bool
    ch3_enabled: bool
    ch4_enabled: bool
    ch5_enabled: bool
    ch6_enabled: bool
    ch7_enabled: bool
    filter0: bool
    left_volume: int
    right_volume: int
    fb_volume: int
    delay: int


@dataclass
class InstrumentState:
    dynamics: DynamicsState
    default_artic: ArticState
    acc_artic: ArticState
    stacc_artic: ArticState
    accstacc_artic: ArticState
    pan_enabled: bool
    pan_val: int
    sample: "SampleState"


@dataclass
class SampleState:
    builtin_sample: int | None
    sample_pack_sample: tuple[str, str] | None
    brr_fname: Path | None
    use_adsr: bool
    source: int
    attack: int
    delay: int
    sustain: int
    release: int
    gain_mode: int
    gain: int
    tune: int
    subtune: int
