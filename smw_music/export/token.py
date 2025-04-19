# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

from dataclasses import dataclass


class Directive:
    pass


@dataclass
class Channel(Directive):
    arg: int


@dataclass
class DefaultLength(Directive):
    length: int


@dataclass
class GlobalVolume(Directive):
    vol: int


@dataclass
class Hex(Directive):
    args: list[int]


@dataclass
class Instrument(Directive):
    idx: int


@dataclass
class Intro(Directive):
    pass


@dataclass
class LabelLoop(Directive):
    label: int
    directives: list[Directive]
    repeats: int


@dataclass
class LabelLoopCall(Directive):
    label: int
    repeats: int


@dataclass
class Loop(Directive):
    directives: list[Directive]
    repeats: int


@dataclass
class LoopRecall(Directive):
    pass


@dataclass
class Noise(Directive):
    value: int


@dataclass
class Note(Directive):
    note: str
    duration: int


@dataclass
class Octave(Directive):
    octave: int


@dataclass
class OctaveChange(Directive):
    up: bool


@dataclass
class Pan(Directive):
    setting: int


@dataclass
class PitchSlide(Directive):
    pass


@dataclass
class Quantize(Directive):
    setting: int


@dataclass
class Rest(Directive):
    duration: int


@dataclass
class SuperLoop(Directive):
    directives: list[Directive]
    repeats: int


@dataclass
class Replacement(Directive):
    lhs: str
    rhs: list[Directive]


@dataclass
class Tempo(Directive):
    tempo: int


@dataclass
class Tie(Directive):
    pass


@dataclass
class Triplet(Directive):
    start: bool


@dataclass
class Vibrato(Directive):
    rate: int
    extent: int
    duration: int = -1


@dataclass
class Volume(Directive):
    vol: int
