# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SMW Music Echo Configuration Tests."""

###############################################################################
# Library imports
###############################################################################

import pytest

###############################################################################
# Project imports
###############################################################################

from smw_music.music_xml import EchoConfig


###############################################################################
# Test definitions
###############################################################################

# Here we go - vertigo
# Video vertigo
# Test for echo
# https://www.youtube.com/watch?v=VaDLxSHVsVo


@pytest.mark.parametrize(
    "csv, exp",
    [
        (
            "0,1,2,3,4,5,6,7,1.0,0,1.0,0,0,1.0,0,0",
            (
                set(range(8)),
                (1.0, 1.0),
                (False, False),
                0,
                1.0,
                False,
                0,
                255,
                127,
                127,
                127,
            ),
        ),
        (
            "1.0,0,1.0,0,0,1.0,0,0",
            (
                set(),
                (1.0, 1.0),
                (False, False),
                0,
                1.0,
                False,
                0,
                0,
                127,
                127,
                127,
            ),
        ),
        (
            "2,5,1,4,0.0787,0,0.157,0,0,0.236,0,0",
            (
                set((1, 2, 4, 5)),
                (0.0787, 0.157),
                (False, False),
                0,
                0.236,
                False,
                0,
                0x36,
                10,
                20,
                30,
            ),
        ),
        (
            "0,1,2,0.0859,1,0.165,0,0,0.244,0,0",
            (
                set((0, 1, 2)),
                (0.0859, 0.165),
                (True, False),
                0,
                0.244,
                False,
                0,
                0x7,
                0xF5,
                21,
                31,
            ),
        ),
        (
            "4,5,6,0.0945,0,0.172,1,0,0.252,0,0",
            (
                set((4, 5, 6)),
                (0.0945, 0.172),
                (False, True),
                0,
                0.252,
                False,
                0,
                0x70,
                12,
                0xEA,
                32,
            ),
        ),
        (
            "7,0,1,0.102,0,0.181,0,0,0.258,1,0",
            (
                set((0, 1, 7)),
                (0.102, 0.181),
                (False, False),
                0,
                0.258,
                True,
                0,
                0x83,
                13,
                23,
                0xDF,
            ),
        ),
        (
            "2,3,4,0.110,0,0.189,0,5,0.268,0,0",
            (
                set((2, 3, 4)),
                (0.110, 0.189),
                (False, False),
                5,
                0.268,
                False,
                0,
                0x1C,
                14,
                24,
                34,
            ),
        ),
        (
            "5,6,7,0.118,0,0.197,0,0,0.276,0,1",
            (
                set((5, 6, 7)),
                (0.118, 0.197),
                (False, False),
                0,
                0.276,
                False,
                1,
                0xE0,
                15,
                25,
                35,
            ),
        ),
    ],
    ids=[
        "Base",
        "Nochannels",
        "Adjusted Magnitudes",
        "Inv Left",
        "Inv Right",
        "Inv Feedback",
        "Delay",
        "FIR filter",
    ],
)
def test_echo(csv, exp):
    cfg = EchoConfig.from_csv(csv)
    assert cfg.chan_list == exp[0], "Channel list"
    assert cfg.vol_mag[0] == pytest.approx(exp[1][0]), "Left Volume"
    assert cfg.vol_mag[1] == pytest.approx(exp[1][1]), "Right Volume"
    assert cfg.vol_inv == exp[2], "Volume phase invert"
    assert cfg.delay == exp[3], "Delay"
    assert cfg.fb_mag == pytest.approx(exp[4]), "Feedback magnitude"
    assert cfg.fb_inv == exp[5], "Feedback phase invert"
    assert cfg.fir_filt == exp[6], "FIR filter selection"
    assert cfg.channel_reg == exp[7], "Channel register"
    assert cfg.left_vol_reg == exp[8], "Left volume register"
    assert cfg.right_vol_reg == exp[9], "Right volume register"
    assert cfg.fb_reg == exp[10], "Feedback register"
