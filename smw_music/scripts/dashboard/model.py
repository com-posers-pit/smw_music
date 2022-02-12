#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Music XML -> AMK Converter."""

###############################################################################
# Standard library imports
###############################################################################

from dataclasses import dataclass
from typing import Optional

###############################################################################
# Library imports
###############################################################################

from PyQt6.QtCore import pyqtSignal, QObject  # type: ignore

###############################################################################
# Package imports
###############################################################################

from ...log import debug, info
from ...music_xml import InstrumentConfig, MusicXmlException
from ...music_xml.song import Song

###############################################################################
# API Class Definitions
###############################################################################


class Model(QObject):
    inst_config_changed: pyqtSignal = pyqtSignal(
        InstrumentConfig, arguments=["config"]
    )
    mml_generated: pyqtSignal = pyqtSignal(str, arguments=["response"])
    song_changed: pyqtSignal = pyqtSignal(Song)

    song: Optional[Song]
    mml_fname: str
    global_legato: bool
    loop_analysis: bool
    superloop_analysis: bool
    measure_numbers: bool
    custom_samples: bool
    custom_percussion: bool
    active_instrument: InstrumentConfig

    ###########################################################################

    @debug()
    def __init__(self) -> None:
        super().__init__()
        self.song = None
        self.mml_fname = ""
        self.global_legato = False
        self.loop_analysis = False
        self.superloop_analysis = False
        self.measure_numbers = False
        self.custom_samples = False
        self.custom_percussion = False
        self.instruments = None
        self.active_instrument = InstrumentConfig("")

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info()
    def generate_mml(self, fname: str) -> None:
        if self.song is None:
            msg = "Song not loaded"
        else:
            try:
                self.song.to_mml_file(
                    fname,
                    self.global_legato,
                    self.loop_analysis,
                    self.superloop_analysis,
                    self.measure_numbers,
                    True,
                    None,
                    self.custom_samples,
                    self.custom_percussion,
                )
            except MusicXmlException as e:
                msg = str(e)
            else:
                msg = ""
        self.mml_generated.emit(msg)

    ###########################################################################

    @info(True)
    def set_instrument(self, name: str) -> None:
        if self.song is not None:
            for inst in self.song.instruments:
                if inst.name == name:
                    self.active_instrument = inst
                    self.inst_config_changed.emit(inst)
                    break

    ###########################################################################

    @info()
    def set_config(
        self,
        global_legato: bool,
        loop_analysis: bool,
        superloop_analysis: bool,
        measure_numbers: bool,
        custom_samples: bool,
        custom_percussion: bool,
    ) -> None:
        self.global_legato = global_legato
        self.loop_analysis = loop_analysis
        self.superloop_analysis = superloop_analysis
        self.measure_numbers = measure_numbers
        self.custom_samples = custom_samples
        self.custom_percussion = custom_percussion

    ###########################################################################

    @info()
    def set_song(self, fname: str) -> None:
        self.song = Song.from_music_xml(fname)
        self._signal()

    ###########################################################################

    @info()
    def update_artic(self, artic: str, val: int) -> None:
        if self.song is not None:
            self.active_instrument.quant[artic] = val

    ###########################################################################

    @info()
    def update_dynamics(self, dyn: str, val: int) -> None:
        if self.song is not None:
            self.active_instrument.dynamics[dyn] = val

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _signal(self) -> None:
        self.song_changed.emit(self.song)
