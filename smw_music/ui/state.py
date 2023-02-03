# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard UI state."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass, field
from enum import IntEnum, auto

# Package imports
from smw_music.music_xml.instrument import InstrumentConfig

###############################################################################
# API class definitions
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


@dataclass
class State:
    musicxml_fname: str = ""
    mml_fname: str = ""
    loop_analysis: bool = False
    superloop_analysis: bool = False
    measure_numbers: bool = True
    global_instrument: InstrumentConfig = InstrumentConfig("")
    instrument_settings: list[InstrumentConfig] = field(
        default_factory=lambda: []
    )
    instrument_idx: int | None = None
    global_volume: int = 0
    global_legato: bool = True
    echo_enable: dict[EchoCh, bool] = field(
        default_factory=lambda: {
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
    )
    echo_filter0: bool = True
    echo_left_setting: int = 0
    echo_right_setting: int = 0
    echo_feedback_setting: int = 0
    echo_delay_setting: int = 0

    ###########################################################################
    # Property definitions
    ###########################################################################

    @property
    def inst(self) -> InstrumentConfig:
        idx = self.instrument_idx
        if idx is None or not 0 <= idx < len(self.instrument_settings):
            return self.global_instrument
        return self.instrument_settings[idx]

    ###########################################################################

    @inst.setter
    def inst(self, inst: InstrumentConfig) -> None:
        idx = self.instrument_idx
        if idx is None or not 0 <= idx < len(self.instrument_settings):
            self.global_instrument = inst
        else:
            self.instrument_settings[idx] = inst
