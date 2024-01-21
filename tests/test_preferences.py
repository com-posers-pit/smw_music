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

# Library imports
import pytest

# Package imports
from smw_music import SmwMusicException
from smw_music.ui.preferences import PreferencesState

from . import RESOURCES

###############################################################################
# Test definitions
###############################################################################


def test_custom(tmp_path):
    # Grab the reference file
    custom = PreferencesState.from_file(
        RESOURCES / "preferences" / "custom.yaml"
    )

    assert custom.amk_fname == Path("addmusick.zip")
    assert custom.spcplay_fname == Path("spcplayer.exe")
    assert custom.sample_pack_dname == Path("samples")
    assert custom.advanced_mode is True
    assert custom.dark_mode is True
    assert custom.release_check is False
    assert custom.confirm_render is False
    assert custom.convert_timeout == 5


###############################################################################


def test_default(tmp_path):
    # Generate a default preferences object
    prefs = PreferencesState()

    # Test default values
    assert prefs.amk_fname == Path("")
    assert prefs.spcplay_fname == Path("")
    assert prefs.sample_pack_dname == Path("")
    assert prefs.advanced_mode is False
    assert prefs.dark_mode is False
    assert prefs.release_check is True
    assert prefs.confirm_render is True
    assert prefs.convert_timeout == 10

    # Write default preferences to a file
    fname = tmp_path / "default.prefs"
    prefs.to_file(fname)

    # Read them back and compare to the original object
    readback = PreferencesState.from_file(fname)
    assert prefs == readback

    # Verify what's written is what's expected
    reference = PreferencesState.from_file(
        RESOURCES / "preferences" / "default.yaml"
    )

    assert readback == reference


###############################################################################


def test_minimal(tmp_path):
    # Grab the reference file
    minimal = PreferencesState.from_file(
        RESOURCES / "preferences" / "minimal.yaml"
    )

    assert minimal.advanced_mode is False
    assert minimal.confirm_render is True
    assert minimal.dark_mode is False
    assert minimal.release_check is True
    assert minimal.convert_timeout == 10


###############################################################################


def test_wrong_version():
    with pytest.raises(SmwMusicException, match="version only supports"):
        PreferencesState.from_file(
            RESOURCES / "preferences" / "wrong_version.yaml"
        )
