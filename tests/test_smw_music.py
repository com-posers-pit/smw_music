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
from smw_music.scripts import convert


###############################################################################
# Test definitions
###############################################################################


@pytest.mark.parametrize(
    "src, dst",
    [
        ("Dots.mxl", "Dots.txt"),
        ("Dynamics.mxl", "Dynamics.txt"),
        ("Grace_Notes.mxl", "Grace_Notes.txt"),
        ("Loop_Point.mxl", "Loop_Point.txt"),
        ("SMB_Castle_Theme.mxl", "SMB_Castle_Theme.txt"),
        ("Ties.mxl", "Ties.txt"),
        ("Triplets.mxl", "Triplets.txt"),
        ("SMB_Castle_Theme.musicxml", "SMB_Castle_Theme.txt"),
    ],
    ids=[
        "Dots",
        "Dynamics",
        "Grace Notes",
        "Loop Point",
        "SMB Castle Theme (compressed)",
        "Ties",
        "Triplets",
        "SMB Castle Theme (uncompressed)",
    ],
)
def test_conversion(src, dst):
    test_dir = pathlib.Path("tests")
    fname = test_dir / "dst" / dst

    with open(fname, "r") as fobj:
        target = fobj.readlines()

    fname = test_dir / "src" / src

    with tempfile.NamedTemporaryFile("r") as fobj:
        convert.main([str(fname), str(fobj.name)])
        written = fobj.readlines()

    assert target == written


###############################################################################


def test_version():
    """Verify correct version number."""
    assert __version__ == "0.1.2"
