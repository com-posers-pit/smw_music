# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

# Line 2469 in main.asm
_PITCH_TABLE = [
    0x085F,
    0x08DE,
    0x0965,
    0x09F4,
    0x0A8C,
    0x0B2C,
    0x0BD6,
    0x0C8B,
    0x0D4A,
    0x0E14,
    0x0EEA,
    0x0FCD,
    0x10BE,
]

###############################################################################


def set_pitch(tune: int, note: int, subnote: int = 0) -> int:
    """
    Reimplementation of SetPitch from main.asm
    """
    note = 0x7F & note

    octave, idx = divmod(note, 12)

    pitch = _PITCH_TABLE[idx]
    next_pitch = _PITCH_TABLE[idx + 1]

    delta = next_pitch - pitch

    pitch += subnote * delta >> 8
    pitch >>= 5 - octave

    return pitch * tune >> 8


###############################################################################


c4 = 0xA4
c5 = c4 + 12
c6 = c5 + 12
assert set_pitch(0x2F4, c4) == 0x62B
assert set_pitch(0x2F4, c4 + 1) == 0x68A
assert set_pitch(0x2F4, c4 + 2) == 0x6EE
assert set_pitch(0x2F4, c4 + 3) == 0x759
assert set_pitch(0x2F4, c4 + 4) == 0x7C9
assert set_pitch(0x2F4, c4 + 5) == 0x83F
assert set_pitch(0x2F4, c4 + 6) == 0x8BB
assert set_pitch(0x2F4, c4 + 7) == 0x940
assert set_pitch(0x2F4, c4 + 8) == 0x9CE
assert set_pitch(0x2F4, c4 + 9) == 0xA64
assert set_pitch(0x2F4, c4 + 10) == 0xB01
assert set_pitch(0x2F4, c4 + 11) == 0xBA9
assert set_pitch(0x2F4, c4 + 12) == 0xC5A

assert set_pitch(0x3F4, c4) == 0x842

assert set_pitch(0x2F4, c5) == 0xC5A
assert set_pitch(0x2F4, c6) == 0x18C1
