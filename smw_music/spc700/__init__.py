# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SPC700 Logic"""

###############################################################################
# Imports
###############################################################################

from .brr import BLOCK_SIZE, SAMPLES_PER_BLOCK, Brr, BrrException, extract_brrs
from .echo import EchoConfig, echo_bytes
from .nspc import calc_tune, midi_to_nspc, set_pitch
from .sample_player import SamplePlayer
from .spc700 import (
    PITCH_REG_SCALE,
    SAMPLE_FREQ,
    Envelope,
    GainMode,
    generate_adsr,
    generate_decexp,
    generate_declin,
    generate_direct_gain,
    generate_incbent,
    generate_inclin,
)

###############################################################################
# API declaration
###############################################################################

__all__ = [
    "BLOCK_SIZE",
    "SAMPLES_PER_BLOCK",
    "Brr",
    "BrrException",
    "extract_brrs",
    "EchoConfig",
    "echo_bytes",
    "calc_tune",
    "midi_to_nspc",
    "set_pitch",
    "SamplePlayer",
    "PITCH_REG_SCALE",
    "SAMPLE_FREQ",
    "Envelope",
    "GainMode",
    "generate_adsr",
    "generate_decexp",
    "generate_declin",
    "generate_direct_gain",
    "generate_incbent",
    "generate_inclin",
]
