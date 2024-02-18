# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Advanced notation support"""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass
from enum import IntEnum, auto

###############################################################################
# Imports
###############################################################################


class AdvType(IntEnum):
    NOP = auto()
    ECHO_FADE = auto()
    GLISSANDO = auto()
    GVOLUME_FADE = auto()
    PAN_FADE = auto()
    PITCH_BEND = auto()
    PITCH_ENV_ATT = auto()
    PITCH_ENV_REL = auto()
    TREMOLO = auto()
    VIBRATO = auto()
    VOLUME_FADE = auto()


###############################################################################


@dataclass
class Advanced:
    pass


###############################################################################


@dataclass
class EchoFade(Advanced):
    duration: int
    final_volume: tuple[int, int]


###############################################################################


@dataclass
class Glissando(Advanced):
    duration: int
    semitones: int


###############################################################################


@dataclass
class GVolumeFade(Advanced):
    duration: int
    volume: int


###############################################################################


@dataclass
class Nop(Advanced):
    pass


###############################################################################


@dataclass
class PanFade(Advanced):
    duration: int
    pan: int


###############################################################################


@dataclass
class PitchBend(Advanced):
    delay: int
    duration: int
    offset: int


###############################################################################


@dataclass
class PitchEnvAtt(Advanced):
    delay: int
    duration: int
    semitones: int


###############################################################################


@dataclass
class PitchEnvRel(Advanced):
    delay: int
    duration: int
    semitones: int


###############################################################################


@dataclass
class Tremolo(Advanced):
    delay: int
    duration: int
    amplitude: int


###############################################################################


@dataclass
class Vibrato(Advanced):
    delay: int
    duration: int
    amplitude: int


###############################################################################


@dataclass
class VolumeFade(Advanced):
    duration: int
    volume: int
