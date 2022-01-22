# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SMW Music Module Tests."""

###############################################################################
# Standard library imports
###############################################################################

import tempfile
import pathlib

###############################################################################
# Library imports
###############################################################################

import pytest

###############################################################################
# Project imports
###############################################################################

from smw_music import __version__
from smw_music.music_xml import MusicXmlException
from smw_music.scripts import convert


###############################################################################
# Test definitions
###############################################################################


@pytest.mark.parametrize(
    "src, dst, args",
    [
        ("Articulations.mxl", "Articulations.txt", ["--disable_dt"]),
        ("Crescendos.mxl", "Crescendos.txt", ["--disable_dt"]),
        (
            "Crescendos.mxl",
            "Crescendos_single_volume.txt",
            ["--disable_dt", "--single_volume"],
        ),
        ("Dots.mxl", "Dots.txt", ["--disable_dt"]),
        ("Dynamics.mxl", "Dynamics.txt", ["--disable_dt"]),
        ("Grace_Notes.mxl", "Grace_Notes.txt", ["--disable_dt"]),
        ("Headers.mxl", "Headers.txt", ["--disable_dt"]),
        (
            "Instruments.mxl",
            "Instruments_no_parse_to.txt",
            ["--disable_dt", "--disable_to_instruments"],
        ),
        ("Instruments.mxl", "Instruments_parse_to.txt", ["--disable_dt"]),
        ("Loop_Point.mxl", "Loop_Point.txt", ["--disable_dt"]),
        ("Loops.mxl", "Loops.txt", ["--loop_analysis", "--disable_dt"]),
        (
            "Percussion.mxl",
            "Percussion.txt",
            ["--disable_dt"],
        ),
        (
            "Percussion.mxl",
            "Percussion_opt.txt",
            ["--disable_dt", "--optimize_percussion"],
        ),
        (
            "Pickup_Measure.mxl",
            "Pickup_Measure.txt",
            ["--measure_numbers", "--disable_dt"],
        ),
        ("Repeats.mxl", "Repeats.txt", ["--loop_analysis", "--disable_dt"]),
        ("Slurs.mxl", "Slurs.txt", ["--disable_dt"]),
        ("SMB_Castle_Theme.mxl", "SMB_Castle_Theme.txt", ["--disable_dt"]),
        ("TiedArticulations.mxl", "TiedArticulations.txt", ["--disable_dt"]),
        ("Ties.mxl", "Ties.txt", ["--disable_dt"]),
        ("Triplets.mxl", "Triplets.txt", ["--disable_dt"]),
        (
            "SMB_Castle_Theme.musicxml",
            "SMB_Castle_Theme.txt",
            ["--disable_dt"],
        ),
        (
            "SMB_Castle_Theme.musicxml",
            "SMB_Castle_Theme_measures.txt",
            ["--measure_numbers", "--disable_dt"],
        ),
        (
            "SMB_Castle_Theme.musicxml",
            "SMB_Castle_Theme_Echo.txt",
            [
                "--disable_dt",
                "--echo",
                "2,3,4,0.109,Y,0.189,N,11,0.323,N,1",
            ],
        ),
        (
            "SMB_Castle_Theme.musicxml",
            "SMB_Castle_Theme_custom_samples.txt",
            ["--disable_dt", "--custom_samples"],
        ),
    ],
    ids=[
        "Articulations",
        "Crescendos",
        "Crescendos (single volume)",
        "Dots",
        "Dynamics",
        "Grace Notes",
        "Headers",
        "Instruments (w/o To parsing)",
        "Instruments (w/ To parsing)",
        "Loop Point",
        "Loops",
        "Percussion",
        "Percussion (optimized)",
        "Pickup Measure",
        "Repeats",
        "Slurs",
        "SMB Castle Theme (compressed)",
        "TiedArticulations",
        "Ties",
        "Triplets",
        "SMB Castle Theme (uncompressed)",
        "SMB Castle Theme (measure #s)",
        "SMB Castle Theme (echo enabled)",
        "SMB Castle Theme (custom samples)",
    ],
)
def test_conversion(src, dst, args):
    test_dir = pathlib.Path("tests")
    fname = test_dir / "dst" / dst

    with open(fname, "r") as fobj:
        target = fobj.readlines()

    fname = test_dir / "src" / src

    with tempfile.NamedTemporaryFile("r") as fobj:
        convert.main([str(fname), str(fobj.name)] + args)
        written = fobj.readlines()

    assert target == written


###############################################################################


@pytest.mark.parametrize(
    "src, text",
    [
        (
            "Bad_Percussion.mxl",
            r"Unsupported percussion note #3 in measure 1 in staff 1",
        ),
        ("Chords.mxl", r"Chord found, #1 in measure 2 in staff 1"),
        ("Percussion_Chords.mxl", r"Chord found, #3 in measure 2 in staff 1"),
        ("TooHigh.mxl", r"Unsupported note c7 #3 in measure 1 in staff 1"),
        ("TooLow.mxl", r"Unsupported note a0 #2 in measure 1 in staff 1"),
        ("Voices.mxl", r"Multiple voices in measure 2 in staff 1"),
    ],
    ids=[
        "Bad percussion",
        "Chord",
        "Percussion Chord",
        "Note too high",
        "Note too low",
        "Multiple Voices",
    ],
)
def test_invalid(src, text):
    test_dir = pathlib.Path("tests")
    fname = test_dir / "src" / "bad" / src

    with tempfile.NamedTemporaryFile("r") as fobj:
        with pytest.raises(MusicXmlException, match=text):
            convert.main([str(fname), str(fobj.name)])


###############################################################################


def test_version():
    """Verify correct version number."""
    assert __version__ == "0.1.2"
