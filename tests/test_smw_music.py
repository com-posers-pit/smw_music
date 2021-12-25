# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

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
# Private function definitions
###############################################################################


def _compare(src, dst, constants):
    test_dir = constants["test_dir"]
    fname = test_dir / "dst" / dst

    with open(fname, "r") as fobj:
        target = fobj.readlines()

    fname = test_dir / "src" / src

    with tempfile.NamedTemporaryFile("r") as fobj:
        music_xml.Song.from_music_xml(fname).to_amk(fobj.name)
        written = fobj.readlines()

    assert target == written


###############################################################################
# Fixture definitions
###############################################################################


@pytest.fixture
def constants():
    return {"test_dir": pathlib.Path("tests")}


###############################################################################
# Test definitions
###############################################################################


def test_dotted(constants):
    _compare("Dots.mxl", "Dots.txt", constants)


###############################################################################


def test_smb_castle(constants):
    _compare("SMB_Castle_Theme.mxl", "SMB_Castle_Theme.txt", constants)


###############################################################################


def test_triplets(constants):
    _compare("Triplets.mxl", "Triplets.txt", constants)


###############################################################################


def test_uncompressed_smb_castle(constants):
    _compare("SMB_Castle_Theme.musicxml", "SMB_Castle_Theme.txt", constants)


###############################################################################


def test_version():
    """Verify correct version number."""
    assert __version__ == "0.1.1"
