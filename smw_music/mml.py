# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

###############################################################################
# Standard Library imports
###############################################################################

from typing import Dict, List, Optional

###############################################################################
# Library imports
###############################################################################

from lark import Lark, Transformer

###############################################################################
# API class definitions
###############################################################################

GRAMMAR = r"""
    channel: ( directives | loop )+

    loop: "[" directives "]" INT
    directives: (directive | _WS)+

    directive: NOTE | REST | OCTAVE
    _WS: WS
    NOTE: ("a".."g" | "A".."G") ("-" | "+")? INT?
    OCTAVE: ">" | "<"
    REST: "r"i

    int: INT | REPL

    %import common.INT
    %import common.WS
"""

parser = Lark(GRAMMAR, start="channel", parser="lalr")


class MmlTransformer(Transformer):
    def octave(self, value):
        return value

    def NOTE(self, value):
        print(type(value))
        return value


data = """
d < g > c+ < g > c < g > c+ < g > d < g > d+ < g > d < g > c+ < g
> d < g > c+ < g > c < g > c+ < g > d < g > d+ < g > d < g > c+ < g
> c+ < f+ > c < f+ > c+ < f+ > d < f+ > c+ < f+ > d < f+ > c+ < f+ > c < f+
> c+ < f+ > c < f+ > c+ < f+ > d < f+ > c+ < f+ > d < f+ > c+ < f+ > c < f+
> f < a+ > f+ < a+ > f < a+ > e < a+ > f < a+ > e < a+ > d+ < a+ > e < a+
> f < a+ > f+ < a+ > f < a+ > e < a+ > f < a+ > e < a+ > d+ < a+ > e < a+
"""


parsed = parser.parse(data)
# print(parsed.pretty())

# compileMusic() -> Music::compile()
#
# init()
#   Look for ";title=" in the text, set everything after the equals-sign to the
#     end of the line to "title"
#   Otherwise, set the title to everything in the file name between the last
#     '/' or '\' and '.'
#
#   preprocess()
#     Look for "#amk=1"
#     Otherwise, look for "#XXX ", where XXX is delimited by a space
#       XXX can be one of: {define, undef, ifdef, ifndef, if, endif, amk, amm,
#       am4---otherwise append to newstr
#     Comment erasing happens
#
#
#
#
#
# Grammar:
#
# program :=
