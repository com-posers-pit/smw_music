# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Song reduction logic."""

###############################################################################
# Standard Library imports
###############################################################################

from collections import deque
from typing import List

###############################################################################
# Project imports
###############################################################################

from .tokens import (
    Annotation,
    Dynamic,
    Loop,
    Measure,
    Playable,
    RehearsalMark,
    Repeat,
    Slur,
    Token,
    Triplet,
)

###############################################################################
# Private function definitions
###############################################################################


def _adjust_triplets(tokens: List[Token]) -> List[Token]:
    """
    Address idiosyncrasies the triplet parsing order.


    There are two quirks about how the parser handles triplets:
        - it finds triplet starts before slur starts, it makes more
          sense for triplet starts to come after slur starts.
        - it emits triplet ends at the start of the first non-triplet note
          after a triplet set.  This means a number of things that should come
          after a triplet-end show up before it.
    This logic corrects both of those.

    Parameters
    ----------
    tokens : List[Token]
        A list of parsed tokens

    Returns
    -------
    List[Token]
        The input token list, but with triplet reordering applied.
    """
    # Copy the input list (we're modifying, don't want to upset the caller)
    tokens = list(tokens)
    rv: List[Token] = []

    pushable = (Annotation, Dynamic, RehearsalMark, Loop, Measure, Repeat)

    # Logic probably isn't immediatley obvious.  We push Triplet.start tokens
    # later (right) in the list if they're before a Slur.start, so we should
    # walk the list from the left (start).  But we push Triplet.stop tokens
    # earlier (left) in the list if they're after one of several other tokens,
    # so we should walk the list from the right (end).  Since there won't ever
    # be two Slur.start tokens next to each other, we're only ever going to
    # push a Triplet.start right by one.  This can be handled while walking the
    # list from the right, so that's what we'll do.
    while len(tokens) > 1:
        curr = tokens.pop()  # Pops from the right.  I always forget this
        prev = tokens[-1]

        swap = False
        if isinstance(prev, Triplet) and prev.start:
            if isinstance(curr, Slur) and curr.start:
                swap = True

        if isinstance(prev, pushable):
            if isinstance(curr, Triplet) and not curr.start:
                swap = True

        if swap:
            rv.append(prev)
            tokens.pop()

        rv.append(curr)

    # The previous logic walked the input list as long as there were >= 2
    # elements.  There might be one left over, this handles that case
    rv.extend(tokens)

    # We walked the input list from the end, appending as we went, so the
    # output is is backwards.  Correct that.  (consider switching to a deque if
    # it's faster and we care?)
    rv.reverse()
    return rv


###############################################################################


def _deduplicate(tokens: List[Token]) -> List[Token]:
    # Copy the input list (we're modifying, don't want to upset the caller)
    tokens = list(tokens)

    rv = []

    while tokens:
        drop = False
        token = tokens.pop(0)

        if isinstance(token, Measure):
            if tokens:
                drop = isinstance(tokens[0], Measure)

        if not drop:
            rv.append(token)

    return rv


###############################################################################


def _repeat_analysis(tokens: List[Token]) -> List[Token]:
    # Copy the input list (we're modifying, don't want to upset the caller)
    tokens = list(tokens)

    rv = []

    repeat_count = 0

    while tokens:
        token = tokens.pop(0)
        skipped = []

        if isinstance(token, Playable):
            repeat_count = 1
            for nxt in tokens:
                if nxt == token:
                    repeat_count += 1
                elif isinstance(nxt, Measure):
                    skipped.append(nxt)
                elif isinstance(nxt, Annotation) and not nxt.amk_annotation:
                    skipped.append(nxt)
                else:
                    break
            if repeat_count >= 3:
                token = Loop([token], -1, repeat_count, True)
                for _ in range(repeat_count + len(skipped) - 1):
                    tokens.pop(0)
            else:
                skipped = []

        rv.append(token)
        rv.extend(skipped)

    return rv


###############################################################################
# API function definitions
###############################################################################


def reduce(tokens: list[Token], loop_analysis: bool) -> List[Token]:
    tokens = _adjust_triplets(tokens)
    if loop_analysis:
        tokens = _repeat_analysis(tokens)
    tokens = _deduplicate(tokens)
    return tokens
