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


@pytest.mark.parametrize(
    "csv, exp",
    [
        (
            "0,1,2,3,4,5,6,7,127,0,127,0,0,127,0,0",
            (
                set(range(8)),
                (127, 127),
                (False, False),
                0,
                127,
                False,
                0,
                255,
                127,
                127,
                127,
            ),
        ),
        (
            "127,0,127,0,0,127,0,0",
            (
                set(),
                (127, 127),
                (False, False),
                0,
                127,
                False,
                0,
                0,
                127,
                127,
                127,
            ),
        ),
        (
            "2,5,1,4,10,0,20,0,0,30,0,0",
            (
                set((1, 2, 4, 5)),
                (10, 20),
                (False, False),
                0,
                30,
                False,
                0,
                0x36,
                10,
                20,
                30,
            ),
        ),
        (
            "0,1,2,11,1,21,0,0,31,0,0",
            (
                set((0, 1, 2)),
                (11, 21),
                (True, False),
                0,
                31,
                False,
                0,
                0x7,
                0xF5,
                21,
                31,
            ),
        ),
        (
            "4,5,6,12,0,22,1,0,32,0,0",
            (
                set((4, 5, 6)),
                (12, 22),
                (False, True),
                0,
                32,
                False,
                0,
                0x70,
                12,
                0xEA,
                32,
            ),
        ),
        (
            "7,0,1,13,0,23,0,0,33,1,0",
            (
                set((0, 1, 7)),
                (13, 23),
                (False, False),
                0,
                33,
                True,
                0,
                0x83,
                13,
                23,
                0xDF,
            ),
        ),
        (
            "2,3,4,14,0,24,0,5,34,0,0",
            (
                set((2, 3, 4)),
                (14, 24),
                (False, False),
                5,
                34,
                False,
                0,
                0x1C,
                14,
                24,
                34,
            ),
        ),
        (
            "5,6,7,15,0,25,0,0,35,0,1",
            (
                set((5, 6, 7)),
                (15, 25),
                (False, False),
                0,
                35,
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
    assert cfg.chan_list == exp[0]
    assert cfg.vol_mag == exp[1]
    assert cfg.vol_inv == exp[2]
    assert cfg.delay == exp[3]
    assert cfg.fb_mag == exp[4]
    assert cfg.fb_inv == exp[5]
    assert cfg.fir_filt == exp[6]
    assert cfg.channel_reg == exp[7]
    assert cfg.left_vol_reg == exp[8]
    assert cfg.right_vol_reg == exp[9]
    assert cfg.fb_reg == exp[10]
