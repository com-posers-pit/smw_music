# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""AMK-related logic"""

###############################################################################
# Imports
###############################################################################

from .amk import (
    N_BUILTIN_SAMPLES,
    BuiltinSampleGroup,
    BuiltinSampleSource,
    Utilization,
    create_project,
    decode_utilization,
    default_utilization,
    get_ticks,
    make_vis_dir,
    update_sample_groups_file,
)
from .echo import EchoConfig
from .song import Song

###############################################################################
# API declaration
###############################################################################

__all__ = [
    "N_BUILTIN_SAMPLES",
    "BuiltinSampleGroup",
    "BuiltinSampleSource",
    "Utilization",
    "create_project",
    "decode_utilization",
    "default_utilization",
    "get_ticks",
    "make_vis_dir",
    "update_sample_groups_file",
    "EchoConfig",
    "Song",
]
