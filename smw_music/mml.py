# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

###############################################################################
# Library imports
###############################################################################

import sly

###############################################################################
# API class definitions
###############################################################################


class MmlLexer(sly.Lexer):
    tokens = {}

    ignore = ""

    HASH = r"#"
    LBRACE = r"{"
    RBRACE = r"}"
