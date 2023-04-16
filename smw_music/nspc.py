# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

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


def word(msb: int, lsb: int) -> int:
    return (msb << 8) | lsb


def set_pitch(
    channel: int, r11: int, r10: int, tune: int, subtune: int
) -> int:
    stack = []
    x = channel
    stack.append(x)  # push x
    a = r11  # mov    a, $11
    c, a = divmod(2 * a, 256)  # asl    a
    y = 0  # mov    y, #$00
    x = 0x18  # mov    x, #$18
    a, y = divmod(word(y, a), x)  # div    ya, x
    x = a  # mov    x, a
    a = _PITCH_TABLE[y] >> 8  # mov    a, PitchTable+1+y
    r15 = a  # mov    $15, a
    a = _PITCH_TABLE[y] & 0xFF  # mov    a, PitchTable+0+y
    r14 = a  # mov    $14, a             ; set $14/5 from pitch table
    a = _PITCH_TABLE[y + 1] >> 8  # mov    a, PitchTable+3+y
    stack.append(a)  # push    a
    a = _PITCH_TABLE[y + 1] & 0xFF  # mov    a, PitchTable+2+y
    y = stack.pop()  # pop    y
    y, a = divmod(word(y, a) - word(r15, r14), 256)  # subw    ya, $14
    y = r10  # mov    y, $10
    y, a = divmod(y * a, 256)  # mul    ya
    a = y  # mov    a, y
    y = 0  # mov    y, #$00
    y, a = divmod(word(y, a) + word(r15, r14), 256)  # addw    ya, $14
    r15 = y  # mov    $15, y
    c, a = divmod(2 * a, 256)  # asl    a
    c, r15 = divmod(2 * r15 + c, 256)  # rol    $15
    r14 = a  # mov    $14, a
    # bra    +
    while x != 6:
        # +    cmp    x, #$06
        # bne    -
        r15, c = divmod(r15, 2)  # -    lsr    $15
        a, c = divmod(word(c, a), 2)  # ror    a
        x += 1  # inc    x

    r14 = a  # mov    $14, a
    x = stack.pop()  # pop    x
    a = subtune  # mov    a, $02f0+x
    y = r15  # mov    y, $15
    y, a = divmod(y * a, 256)  # mul    ya
    r17, r16 = y, a  # movw    $16, ya
    a = subtune  # mov    a, $02f0+x
    y = r14  # mov    y, $14
    y, a = divmod(y * a, 256)  # mul    ya
    stack.append(y)  # push    y
    a = tune  # mov    a, $0210+x
    y = r14  # mov    y, $14
    y, a = divmod(y * a, 256)  # mul    ya
    y, a = divmod(word(y, a) + word(r17, r16), 256)  # addw    ya, $16
    r17, r16 = y, a  # movw    $16, ya
    a = tune  # mov    a, $0210+x
    y = r15  # mov    y, $15
    y, a = divmod(y * a, 256)  # mul    ya
    y = a  # mov    y, a
    a = stack.pop()  # pop    a
    y, a = divmod(word(y, a) + word(r17, r16), 256)  # addw    ya, $16
    r17, r16 = y, a  #         movw    $16, ya

    return word(r17, r16)
    #    a = x  # mov    a, x               ; set voice X pitch DSP reg from $16/7
    #    a = ((0x0F & a) << 4) | (
    #        a >> 4
    #    )  # xcn    a                 ;  (if vbit clear in $1a)
    #    a, c = divmod(a, 2)  # lsr    a
    #    a |= 2  #  or    a, #$02
    #    y = a  #  mov    y, a               ; Y = voice X pitch DSP reg
    #    a = r16  #         mov    a, $16
    #    # call    DSPWriteWithCheck
    #    y += 1  # inc    y
    #    a = r17  # mov    a, $17
    #    #                     ; write A to DSP reg Y if vbit clear in $1d
    #    # DSPWriteWithCheck:
    #    stack.append(a)  # push    a
    #    a = r48  # mov    a, $48
    #    a &= r1d  # and    a, $1d
    #    if
    #         pop    a
    #         bne    +
    #                     ; write A to DSP reg Y
    #     DSPWrite:
    #         mov    $f2, y
    #         mov    $f3, a
    #     +
    #         ret

    return 0
