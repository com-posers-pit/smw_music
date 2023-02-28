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
from pathlib import Path

# Package imports
from smw_music.music_xml.echo import EchoConfig
from smw_music.music_xml.instrument import InstrumentConfig

###############################################################################
# API class definitions
###############################################################################


@dataclass
class PreferencesState:
    amk_fname: Path = Path("")
    spcplay_fname: Path = Path("")
    sample_pack_dname: Path = Path("")
    advanced_mode: bool = False


###############################################################################


@dataclass
class State:
    musicxml_fname: str = ""
    mml_fname: str = ""
    loop_analysis: bool = False
    superloop_analysis: bool = False
    measure_numbers: bool = True
    global_instrument: InstrumentConfig = field(
        default_factory=lambda: InstrumentConfig("")
    )
    instruments: list[InstrumentConfig] = field(default_factory=lambda: [])
    instrument_idx: int | None = None
    global_volume: int = 128
    global_legato: bool = True
    global_echo_enable: bool = True
    echo: EchoConfig = field(
        default_factory=lambda: EchoConfig(
            set(), (0, 0), (False, False), 0, 0, False, 0
        )
    )
    unsaved: bool = True
    project_name: str | None = None
    porter: str = ""
    game: str = ""
    start_measure: int = 1
    mute_percussion: bool = False
    solo_percussion: bool = False

    ###########################################################################
    # Property definitions
    ###########################################################################

    @property
    def inst(self) -> InstrumentConfig:
        idx = self.instrument_idx
        if idx is None or not 0 <= idx < len(self.instruments):
            return self.global_instrument
        return self.instruments[idx]

    ###########################################################################

    @inst.setter
    def inst(self, inst: InstrumentConfig) -> None:
        idx = self.instrument_idx
        if idx is None or not 0 <= idx < len(self.instruments):
            self.global_instrument = inst
        else:
            self.instruments[idx] = inst
