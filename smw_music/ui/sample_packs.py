# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Sample Pack Handling Logic"""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from pathlib import Path
from typing import Callable

# Library imports
from watchdog import events, observers

###############################################################################
# API Class Definitions
###############################################################################


class SamplePackWatcher(events.FileSystemEventHandler):
    def __init__(self, hdlr: Callable[[str], None]) -> None:
        super().__init__()
        self._hdlr = hdlr

    ###########################################################################

    def on_created(
        self, event: events.FileCreatedEvent | events.DirCreatedEvent
    ) -> None:
        fname = Path(event.src_path).name
        self._hdlr(f"Sample pack {fname} added")
        return
        self._model.update_status(f"Sample pack {fname} added")
        self._model.update_sample_packs()

    ###########################################################################

    def on_deleted(
        self, event: events.FileDeletedEvent | events.DirDeletedEvent
    ) -> None:
        fname = Path(event.src_path).name
        self._hdlr(f"Sample pack {fname} removed")
        return
        self._model.update_status(f"Sample pack {fname} removed")
        self._model.update_sample_packs()

    ###########################################################################

    def start(self) -> None:
        pass
