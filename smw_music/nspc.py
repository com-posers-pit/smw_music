# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
Logic related to the N-SPC SPC700 music engine
"""

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
    """
    Calculate the N-SPC "tune" value for a sample

    Parameters
    ----------
    fundamental : float
        The fundamental frequency for a sample
    note : int
        The desired N-SPC note command
    freq : int
        The desired audio frequency generated when `note` is keyed

    Returns
    -------
    tuple
        First element is the "tune" value given to N-SPC, second element is the
        actual frequency generated when `note` is keyed

    Notes
    -----
    This function helps with setting the sample tuning parameters that go with
    a BRR file's entry in MML (which is really just a prescalar).  The idea is
    that whenever the `note` command is keyed in N-SPC, a BRR sample that has
    a fundamental frequency `fundamental` will be pitch shifted to play `freq`.
    """
    # "fundamental" is from the "Fundamental" input
    # "note" is from the "SNES Note" input
    # "freq" is from the "Output Note" input
    scale = 2**12

    # This is how N-SPC calculates a pitch register setting (see set_pitch)
    octave, idx = divmod(note, 12)
    pitch = _PITCH_TABLE[idx] >> (5 - octave)

    # Look at the comment for "actual", set actual to freq (since we want them
    # to be the same), solve for tune, and be aware that tune is a Q15.8 fixed
    # point value.
    tune = round((scale * (freq / fundamental) / pitch) * 256)

    # This is what actually plays.  fundamental is the default frequency of the
    # sample.  tune/256 is what N-SPC does with the tuning parameter.  pitch is
    # the frequency register setting that N-SPC uses when the note is keyed.
    # Divide by the scale because if pitch == scale, the sample is played at
    # the default frequency.
    actual = fundamental * (tune / 256) * pitch / scale

    return tune, actual


###############################################################################


def midi_to_nspc(midi_number: int) -> int:
    """
    Convert a midi note number to an N-SPC command number

    Parameters
    ----------
    midi_number : int
        A midi note number

    Returns
    -------
    int
        the corresponding N-SPC note command
    """
    # C4 is 60 in MIDI, a 0xA4 in AMK/N-SPC
    midi_c4 = 60
    nspc_c4 = 0xA4

    # Within N-SPC, the most significant bit is masked away prior to any
    # calculations
    return midi_number - midi_c4 + (nspc_c4 & 0x7F)


###############################################################################


def set_pitch(tune: int, note: int, subnote: int = 0) -> int:
    """
    Compute a note's SPC700 pitch value

    Parameters
    ----------
    tune : int
        N-SPC BRR prescalar
    note : int
        N-SPC note number
    subnote : int
        Fractional part of the input note when treated as a Q15.8 number

    Returns
    -------
    int
        SPC700 pitch register setting for the given note

    Notes
    -----
    This is a reimplementation of SetPitch from AddMusicK's main.asm
    """
    note = 0x7F & note

    octave, idx = divmod(note, 12)

    pitch = _PITCH_TABLE[idx]
    next_pitch = _PITCH_TABLE[idx + 1]

    delta = next_pitch - pitch

    pitch += (subnote * delta) >> 8
    pitch >>= 5 - octave

    return pitch * tune >> 8
