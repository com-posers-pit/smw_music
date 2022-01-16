# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Song reduction logic."""

###############################################################################
# Standard Library imports
###############################################################################

from typing import List

###############################################################################
# Project imports
###############################################################################

from .tokens import (
    Annotation,
    Dynamic,
    Loop,
    LoopDelim,
    LoopRef,
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
    tokens = _deduplicate_loops(tokens)
    tokens = _deduplicate_measures(tokens)
    return tokens


###############################################################################


def _deduplicate_loops(tokens: List[Token]) -> List[Token]:
    # Copy the input list (we're modifying, don't want to upset the caller)
    tokens = list(tokens)
    rv = []

    while tokens:
        drop = False
        token = tokens.pop()

        if isinstance(token, LoopRef):
            prev = tokens[-1]
            if isinstance(prev, Loop) and prev.loop_id == token.loop_id:
                prev.repeats += token.repeats
                drop = True

        if not drop:
            rv.append(token)

    rv.reverse()
    return rv


###############################################################################


def _deduplicate_measures(tokens: List[Token]) -> List[Token]:
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


def _reference_loop(tokens: List[Token], loop: Loop) -> List[Token]:
    # Copy the input list (we're modifying, don't want to upset the caller)
    tokens = list(tokens)
    rv = []

    pushable = (RehearsalMark, Measure)

    # Copy everythign before the loop to the output
    while tokens[0] != loop:
        rv.append(tokens.pop(0))
    rv.append(tokens.pop(0))

    while tokens:
        repeats = 0
        match_count = 0
        cand_skipped: List[Token] = []
        skipped = []
        for token in tokens:
            if token == loop.tokens[match_count]:
                match_count += 1
                if match_count == len(loop.tokens):
                    repeats += 1
                    skipped.extend(cand_skipped)
                    cand_skipped = []
                    match_count = 0
            elif isinstance(token, pushable):
                cand_skipped.append(token)
            else:
                break

        if repeats:
            tokens = tokens[repeats * len(loop.tokens) + len(skipped) :]
            rv.append(LoopRef(loop.loop_id, repeats))
            rv.extend(skipped)
        else:
            rv.append(tokens.pop(0))

    return rv


###############################################################################


def _reference_loops(tokens: List[Token]) -> List[Token]:
    loops = [token for token in tokens if isinstance(token, Loop)]

    for loop in loops:
        tokens = _reference_loop(tokens, loop)

    return tokens


###############################################################################


def _loopify(tokens: List[Token]) -> List[Token]:
    # Copy the input list (we're modifying, don't want to upset the caller)
    tokens = list(tokens)
    rv = []

    while tokens:
        token = tokens.pop(0)
        skipped = []
        if isinstance(token, LoopDelim) and token.start:
            loop_id = token.loop_id
            loop_tokens: List[Token] = []
            while tokens:
                nxt = tokens.pop(0)

                if isinstance(nxt, LoopDelim) and not nxt.start:
                    token = Loop(loop_tokens, loop_id, 1, False)
                    break

                if isinstance(nxt, (Dynamic, Playable, Triplet, Slur)):
                    loop_tokens.append(nxt)
                elif isinstance(nxt, Annotation) and nxt.amk_annotation:
                    loop_tokens.append(nxt)
                else:
                    skipped.append(nxt)

        rv.append(token)
        rv.extend(skipped)

    return rv


###############################################################################


def _repeat_analysis(tokens: List[Token]) -> List[Token]:
    # Copy the input list (we're modifying, don't want to upset the caller)
    tokens = list(tokens)

    rv = []

    repeat_count = 0

    while tokens:
        token = tokens.pop(0)
        skipped: List[Token] = []

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
                tokens = tokens[repeat_count + len(skipped) - 1 :]
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
        tokens = _loopify(tokens)
        tokens = _reference_loops(tokens)
        tokens = _repeat_analysis(tokens)
    tokens = _deduplicate(tokens)
    return tokens
