# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""UI Preferences Module Tests."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from pathlib import Path

# Package imports
from smw_music.ui.preferences import PreferencesState

###############################################################################
# Test definitions
###############################################################################


def test_default():
    prefs = PreferencesState()
    assert prefs.amk_fname == Path("")
    assert prefs.spcplay_fname == Path("")
    assert prefs.sample_pack_dname == Path("")
    assert prefs.advanced_mode is False
    assert prefs.dark_mode is False
    assert prefs.release_check is True
    assert prefs.confirm_render is True
