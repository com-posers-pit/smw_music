#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Music XML -> AMK Converter."""

###############################################################################
# Standard library imports
###############################################################################

from enum import auto, IntEnum
from typing import Optional

###############################################################################
# Library imports
###############################################################################

from PyQt6.QtCore import pyqtSignal, QObject  # type: ignore

###############################################################################
# Package imports
###############################################################################

from ..log import debug, info
from ..music_xml import InstrumentConfig, MusicXmlException
from ..music_xml.echo import EchoConfig
from ..music_xml.song import Song

###############################################################################
# Private Function Definitions
###############################################################################


def _dyn_to_str(dyn: "_DynEnum") -> str:
    lut = {
        _DynEnum.PPPP: "PPPP",
        _DynEnum.PPP: "PPP",
        _DynEnum.PP: "PP",
        _DynEnum.P: "P",
        _DynEnum.MP: "MP",
        _DynEnum.MF: "MF",
        _DynEnum.F: "F",
        _DynEnum.FF: "FF",
        _DynEnum.FFF: "FFF",
        _DynEnum.FFFF: "FFFF",
    }
    return lut[dyn]


###############################################################################


def _str_to_dyn(dyn: str) -> "_DynEnum":
    lut = {
        "PPPP": _DynEnum.PPPP,
        "PPP": _DynEnum.PPP,
        "PP": _DynEnum.PP,
        "P": _DynEnum.P,
        "MP": _DynEnum.MP,
        "MF": _DynEnum.MF,
        "F": _DynEnum.F,
        "FF": _DynEnum.FF,
        "FFF": _DynEnum.FFF,
        "FFFF": _DynEnum.FFFF,
    }
    return lut[dyn]


###############################################################################
# Private Class Definitions
###############################################################################


class _DynEnum(IntEnum):
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
# API Class Definitions
###############################################################################


class Model(QObject):
    inst_config_changed: pyqtSignal = pyqtSignal(
        InstrumentConfig, arguments=["config"]
    )
    response_generated: pyqtSignal = pyqtSignal(
        bool, str, str, arguments=["error", "title", "response"]
    )
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
    _disable_interp: bool

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
        self._disable_interp = False

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info(True)
    def generate_mml(self, fname: str, echo: Optional[EchoConfig]) -> None:
        title = "MML Generation"
        error = True
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
                    echo,
                    self.custom_samples,
                    self.custom_percussion,
                )
            except MusicXmlException as e:
                msg = str(e)
            else:
                error = False
                msg = "Done"
        self.response_generated.emit(error, title, msg)

    ###########################################################################

    @info(True)
    def set_instrument(self, name: str) -> None:
        if self.song is not None:
            for inst in self.song.instruments:
                if inst.name == name:
                    self.active_instrument = inst
                    self._disable_interp = True
                    self.inst_config_changed.emit(inst)
                    self._disable_interp = False
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

    @info(True)
    def set_pan(self, enabled: bool, pan: int) -> None:
        if self.song is not None:
            self.active_instrument.pan = pan if enabled else None

    ###########################################################################

    @info(True)
    def set_song(self, fname: str) -> None:
        try:
            self.song = Song.from_music_xml(fname)
        except MusicXmlException as e:
            self.response_generated.emit(True, "Song load", str(e))
        else:
            self._signal()

    ###########################################################################

    @info(True)
    def update_artic(self, artic: str, quant: int) -> None:
        if self.song is not None:
            self.active_instrument.quant[artic] = quant

    ###########################################################################

    @info(True)
    def update_dynamics(self, dyn: str, val: int, interp: bool) -> None:
        if self.song is not None:
            if dyn == "global":
                self.song.volume = val
            else:
                self.active_instrument.dynamics[dyn] = val
                if interp and not self._disable_interp:
                    self._interpolate(dyn, val)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _signal(self) -> None:
        self.song_changed.emit(self.song)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _interpolate(self, dyn_str: str, level: int) -> None:
        self._disable_interp = True

        moved_dyn = _str_to_dyn(dyn_str)
        dyns = [
            _str_to_dyn(x) for x in self.active_instrument.dynamics_present
        ]

        min_dyn = min(dyns)
        max_dyn = max(dyns)

        min_val = self.active_instrument.dynamics[_dyn_to_str(min_dyn).upper()]
        max_val = self.active_instrument.dynamics[_dyn_to_str(max_dyn).upper()]

        if moved_dyn != min_dyn:
            level = max(min_val, level)
        if moved_dyn != max_dyn:
            level = min(max_val, level)

        for dyn in dyns:
            if dyn == moved_dyn:
                val = level
            elif dyn in [min_dyn, max_dyn]:
                continue
            if dyn < moved_dyn:
                numer = 1 + sum(dyn < x < moved_dyn for x in dyns)
                denom = 1 + sum(min_dyn < x < moved_dyn for x in dyns)
                val = round(
                    min_val + (level - min_val) * (denom - numer) / denom
                )
            elif dyn > moved_dyn:
                numer = 1 + sum(moved_dyn < x < dyn for x in dyns)
                denom = 1 + sum(moved_dyn < x < max_dyn for x in dyns)
                val = round(level + (max_val - level) * numer / denom)

            self.active_instrument.dynamics[_dyn_to_str(dyn)] = val

        self.inst_config_changed.emit(self.active_instrument)

        self._disable_interp = False
