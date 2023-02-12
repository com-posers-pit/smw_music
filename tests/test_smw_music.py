# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SMW Music Module Tests."""

###############################################################################
# Import
###############################################################################

# Standard library imports
import pathlib

# Library imports
import pytest

# Package imports
from smw_music import __version__
from smw_music.music_xml import MusicXmlException
from smw_music.scripts import convert

###############################################################################
# Test definitions
###############################################################################


@pytest.mark.parametrize(
    "src, dst, args",
    [
        ("Articulations.mxl", "Articulations.txt", []),
        ("Crescendos.mxl", "Crescendos.txt", []),
        (
            "Crescendo_Triplet_Loops.mxl",
            "Crescendo_Triplet_Loops.txt",
            ["--loop_analysis"],
        ),
        ("Dots.mxl", "Dots.txt", []),
        ("Dynamics.mxl", "Dynamics.txt", []),
        ("Empty_Section.mxl", "Empty_Section.txt", ["--loop_analysis"]),
        ("EndingTriplet.mxl", "EndingTriplet.txt", []),
        ("ExtraInstruments.mxl", "ExtraInstruments.txt", []),
        ("Grace_Notes.mxl", "Grace_Notes.txt", []),
        ("Headers.mxl", "Headers.txt", []),
        ("Instruments.mxl", "Instruments_parse_to.txt", []),
        ("Loop_Point.mxl", "Loop_Point.txt", []),
        (
            "Loops.mxl",
            "Loops.txt",
            [
                "--loop_analysis",
            ],
        ),
        ("Metadata.mxl", "Metadata.txt", []),
        ("No_Metadata.mxl", "No_Metadata.txt", []),
        (
            "Percussion.mxl",
            "Percussion.txt",
            [],
        ),
        (
            "Percussion.mxl",
            "Percussion_opt.txt",
            ["--optimize_percussion"],
        ),
        (
            "Pickup_Measure.mxl",
            "Pickup_Measure.txt",
            [
                "--measure_numbers",
            ],
        ),
        (
            "Repeats.mxl",
            "Repeats.txt",
            [
                "--loop_analysis",
            ],
        ),
        ("Slurs.mxl", "Slurs.txt", []),
        ("SMB_Castle_Theme.mxl", "SMB_Castle_Theme.txt", []),
        ("SwapRepeatAnnotation.mxl", "SwapRepeatAnnotation.txt", []),
        ("Tempos.mxl", "Tempos.txt", []),
        ("TiedArticulations.mxl", "TiedArticulations.txt", []),
        ("Ties.mxl", "Ties.txt", []),
        # ("Transposing_Instrument.mxl", "Transposing_Instrument.txt", []), #
        # Disabled due to breakage in music21
        ("Triplets.mxl", "Triplets.txt", []),
        ("Vibrato.mxl", "Vibrato.txt", []),
        (
            "SMB_Castle_Theme.musicxml",
            "SMB_Castle_Theme.txt",
            [],
        ),
        (
            "SMB_Castle_Theme.musicxml",
            "SMB_Castle_Theme_full.txt",
            [
                "--measure_numbers",
                "--loop_analysis",
                "--optimize_percussion",
            ],
        ),
        (
            "SMB_Castle_Theme.musicxml",
            "SMB_Castle_Theme_measures.txt",
            [
                "--measure_numbers",
            ],
        ),
        (
            "SMB_Castle_Theme.musicxml",
            "SMB_Castle_Theme_Echo.txt",
            [
                "--echo",
                "2,3,4,0.109,Y,0.189,N,11,0.323,N,1",
            ],
        ),
    ],
    ids=[
        "Articulations",
        "Crescendos",
        "Crescendo+Triplet+Loop",
        "Dots",
        "Dynamics",
        "Empty Section",
        "Ending Triplet",
        "Extra Instruments",
        "Grace Notes",
        "Headers",
        "Instruments (w/ To parsing)",
        "Loop Point",
        "Loops",
        "Metadata",
        "No Metadata",
        "Percussion",
        "Percussion (optimized)",
        "Pickup Measure",
        "Repeats",
        "Slurs",
        "SMB Castle Theme (compressed)",
        "Swap Repeat & Annotation",
        "Tempos",
        "TiedArticulations",
        "Ties",
        # "Transposing Instrument",
        "Triplets",
        "Vibrato",
        "SMB Castle Theme (uncompressed)",
        "SMB Castle Theme (kitchen sink)",
        "SMB Castle Theme (measure #s)",
        "SMB Castle Theme (echo enabled)",
    ],
)
def test_conversion(src, dst, args, tmp_path):
    test_dir = pathlib.Path("tests")
    fname = test_dir / "dst" / dst

    with open(fname, "r") as fobj:
        target = fobj.readlines()

    src_fname = test_dir / "src" / src
    dst_fname = tmp_path / dst

    # We always want the datetime stamp disabled for these tests
    args += ["--disable_dt"]
    convert.main([str(src_fname), str(dst_fname)] + args)

    with open(dst_fname, "r") as fobj:
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
        ("Chords.mxl", r"Chord found, #2 in measure 2 in staff 1"),
        ("Chords.mxl", r"Chord found, #3 in measure 2 in staff 1"),
        (
            "ComplexNoteLength.mxl",
            r"Unsupported note #1 in Measure 2 in staff 1",
        ),
        (
            "ComplexNoteLength.mxl",
            r"Unsupported note #1 in Measure 7 in staff 1",
        ),
        ("Percussion_Chords.mxl", r"Chord found, #3 in measure 2 in staff 1"),
        ("TooHigh.mxl", r"Unsupported note c7 #3 in measure 1 in staff 1"),
        ("TooLow.mxl", r"Unsupported note a0 #2 in measure 1 in staff 1"),
        ("Voices.mxl", r"Multiple voices in measure 2 in staff 1"),
    ],
    ids=[
        "Bad percussion",
        "Chord 1",
        "Chord 2",
        "Chord 3",
        "Bad 5/4 whole rest",
        "Bad 5/8 whole rest",
        "Percussion Chord",
        "Note too high",
        "Note too low",
        "Multiple Voices",
    ],
)
def test_invalid(src, text, tmp_path):
    test_dir = pathlib.Path("tests")
    fname = test_dir / "src" / "bad" / src
    dst = tmp_path / src

    with pytest.raises(MusicXmlException, match=text):
        convert.main([str(fname), str(dst)])


###############################################################################


@pytest.mark.parametrize(
    "text",
    [
        (r"Chord found, #1 in measure 2 in staff 1"),
        (r"Chord found, #2 in measure 2 in staff 1"),
        (r"Chord found, #3 in measure 2 in staff 1"),
        (r"Multiple voices in measure 6 in staff 1"),
        (r"Unsupported note c7 #3 in measure 3 in staff 1"),
        (r"Unsupported note a0 #2 in measure 4 in staff 1"),
        (r"Chord found, #3 in measure 3 in staff 2"),
        (r"Unsupported percussion note #3 in measure 1 in staff 2"),
    ],
    ids=[
        "Chord 1",
        "Chord 2",
        "Chord 3",
        "Multiple Voices",
        "Note too high",
        "Note too low",
        "Percussion Chord",
        "Bad percussion",
    ],
)
def test_multiple_invalid(text, tmp_path):
    test_dir = pathlib.Path("tests")
    fname = test_dir / "src" / "bad" / "Errors.mxl"
    dst = tmp_path / "Errors.mml"

    with pytest.raises(MusicXmlException, match=text):
        convert.main([str(fname), str(dst)])


###############################################################################


def test_version():
    """Verify correct version number."""
    assert __version__ == "0.2.3"
