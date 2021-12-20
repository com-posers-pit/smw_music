"""SMW Music Module Tests."""

###############################################################################
# Standard library imports
###############################################################################

import os
import tempfile
import pathlib

###############################################################################
# Library imports
###############################################################################

import pytest

###############################################################################
# Project imports
###############################################################################

from smw_music import music_xml, __version__


###############################################################################
# Fixture definitions
###############################################################################


@pytest.fixture
def constants():
    return {"test_dir": pathlib.Path("tests")}


###############################################################################
# Test definitions
###############################################################################


def test_version():
    """Verify correct version number."""
    assert __version__ == "0.0.0"


###############################################################################


def test_smb_castle(constants):
    test_dir = constants["test_dir"]
    fname = test_dir / "dst" / "SMB_Castle_Theme.txt"

    with open(fname, "r") as fobj:
        target = fobj.readlines()

    for fname in ["SMB_Castle_Theme.mxl", "SMB_Castle_Theme.musicxml"]:
        fname = test_dir / "src" / fname

        with tempfile.NamedTemporaryFile("r") as fobj:
            music_xml.convert(fname, fobj.name)
            written = fobj.readlines()

        assert target == written
