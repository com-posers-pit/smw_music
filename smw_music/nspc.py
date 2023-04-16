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
assert set_pitch(0x2F4, c4) == 0x62B
assert set_pitch(0x2F4, c4 + 12) == 0xC5A
assert set_pitch(0x3F4, c4) == 0x842
