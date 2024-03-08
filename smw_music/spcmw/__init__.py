# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard preferences."""

from . import amk
from .instrument import (
    Artic,
    ArticSetting,
    Dynamics,
    InstrumentConfig,
    InstrumentSample,
    NoteHead,
    SampleSource,
    TuneSource,
    Tuning,
    extract_instruments,
    unmapped_notes,
)
from .preferences import Preferences
from .project import (
    EXTENSION,
    OLD_EXTENSION,
    Project,
    ProjectInfo,
    ProjectSettings,
)
from .sample import Sample, SamplePack, SampleParams
from .spcmw import (
    create_project,
    first_use,
    get_preferences,
    get_recent_projects,
    save_preferences,
    save_recent_projects,
)

###############################################################################

__all__ = [
    "amk",
    "Artic",
    "ArticSetting",
    "Dynamics",
    "InstrumentConfig",
    "InstrumentSample",
    "NoteHead",
    "SampleSource",
    "TuneSource",
    "Tuning",
    "extract_instruments",
    "unmapped_notes",
    "Preferences",
    "ProjectInfo",
    "ProjectSettings",
    "Project",
    "EXTENSION",
    "OLD_EXTENSION",
    "Sample",
    "SamplePack",
    "SampleParams",
    "create_project",
    "first_use",
    "get_preferences",
    "get_recent_projects",
    "save_preferences",
    "save_recent_projects",
]
