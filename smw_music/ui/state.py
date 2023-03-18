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
from itertools import chain
from pathlib import Path

# Package imports
from smw_music.music_xml.echo import EchoConfig
from smw_music.music_xml.instrument import InstrumentConfig, InstrumentSample

###############################################################################
# API class definitions
###############################################################################


@dataclass
class PreferencesState:
    amk_fname: Path = Path("")
    spcplay_fname: Path = Path("")
    sample_pack_dname: Path = Path("")
    advanced_mode: bool = False
    dark_mode: bool = False
    release_check: bool = True


###############################################################################


@dataclass
class State:
    musicxml_fname: Path = field(default_factory=lambda: Path(""))
    mml_fname: Path = field(default_factory=lambda: Path(""))
    loop_analysis: bool = False
    superloop_analysis: bool = False
    measure_numbers: bool = True
    instruments: list[InstrumentConfig] = field(default_factory=lambda: [])
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

    sample_idx: tuple[str, str] | None = None

    ###########################################################################
    # Property definitions
    ###########################################################################

    @property
    def samples(self) -> dict[tuple[str, str], InstrumentSample]:
        samples = {}
        for inst in self.instruments:
            for sample in inst.samples:
                samples[(inst.name, sample.name)] = sample

        return samples
