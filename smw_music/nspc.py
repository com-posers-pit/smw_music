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


def calc_tune(fundamental: float, note: int, freq: float) -> tuple[int, float]:
    # "fundamental" is from the "Fundamental" input
    # "note" is from the "SNES Note" input
    # "freq" is from the "Output Note" input
    tune = 1.0
    scale = 2**12
    octave, idx = divmod(note, 12)

    pitch = _PITCH_TABLE[idx] >> (5 - octave)

    tune = round((scale * (freq / fundamental) / pitch) * 256)
    actual = fundamental * (tune / 256) * pitch / scale

    return tune, actual


###############################################################################


def midi_to_nspc(midi_number: int) -> int:
    # C4 is 60 in MIDI, a 0xA4 in AMK/N-SPC
    midi_c4 = 60
    nspc_c4 = 0xA4

    # Within N-SPC, the most significant bit is masked away prior to any
    # calculations
    return midi_number - midi_c4 + (nspc_c4 & 0x7F)


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
