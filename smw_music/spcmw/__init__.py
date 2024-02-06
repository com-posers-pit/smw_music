# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard preferences."""

from .preferences import Preferences
from .project import EXTENSION, Project, ProjectInfo, ProjectSettings
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
    "Preferences",
    "ProjectInfo",
    "ProjectSettings",
    "Project",
    "EXTENSION",
    "create_project",
    "first_use",
    "get_preferences",
    "get_recent_projects",
    "save_preferences",
    "save_recent_projects",
]
