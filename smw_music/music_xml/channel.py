# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Single part/channel in a MusicXML file."""

###############################################################################
# Standard Library imports
###############################################################################

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, TypeVar

###############################################################################
# Project imports
###############################################################################

from .context import MmlState, SlurState
from .shared import CRLF, MusicXmlException
from .tokens import (
    Token,
    Dynamic,
    Note,
    Rest,
    Slur,
)

###############################################################################
# Private variable/constant definitions
###############################################################################

# Generic type variable
_T = TypeVar("_T")

# Weinberg:
# http://www.normanweinberg.com/uploads/8/1/6/4/81640608/940506pn_guildines_for_drumset.pdf
_PERCUSSION_MAP = {
    "x": {
        "c6": "CR3",
        "b5": "CR2",
        "a5": "CR",
        "g5": "CH",
        "f5": "RD",
        "e5": "OH",
        "d5": "RD2",
    },
    "normal": {
        "e5": "HT",
        "d5": "MT",
        "c5": "SN",
        "a4": "LT",
        "f4": "KD",
    },
}

###############################################################################
# Private function definitions
###############################################################################


def _most_common(container: Iterable[_T]) -> _T:
    """
    Get the most common element in an iterable.

    Parameters
    ----------
    container : iterable
        A list/dictionary/... containing duplicate elements

    Return
    ------
    object
        The most common element in `container`
    """
    return Counter(container).most_common(1)[0][0]


###############################################################################
# API class definitions
###############################################################################


@dataclass
class Channel:  # pylint: disable=too-many-instance-attributes
    """
    Single music channel.

    Parameters
    ----------
    elems: list
        A list of valid channel elements
    percussion: bool
        Ture iff this is a percussion channel

    Attributes
    ----------
    elems: list
        A list of elements in this channel
    percussion: bool
        Ture iff this is a percussion channel

    Todo
    ----
    Parameterize grace note length?
    """

    elems: List[Token]
    percussion: bool
    _accent: bool = field(init=False, repr=False, compare=False)
    _directives: List[str] = field(init=False, repr=False, compare=False)
    _loops: Dict[int, List[Token]] = field(
        init=False, repr=False, compare=False
    )
    _measure_numbers: bool = field(init=False, repr=False, compare=False)
    _staccato: bool = field(init=False, repr=False, compare=False)
    _mml_state: MmlState = MmlState()

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __getitem__(self, n: int) -> Token:
        return self.elems[n]

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _loop_analysis(self, idx: int, last_loop: Optional[int] = None) -> int:
        skip_count = 0

        for label, loop in self._loops.items():
            cand_skip_count = 0
            match_count = 0
            loops = 0

            for elem in self.elems[idx:]:
                cand_skip_count += 1
                if isinstance(elem, (Note, Rest, Dynamic)):
                    if elem == loop[match_count]:
                        match_count += 1
                        if match_count == len(loop):
                            loops += 1
                            skip_count += cand_skip_count
                            cand_skip_count = 0
                            match_count = 0
                    else:
                        break

            if loops >= 1:
                skip_count -= 1
                if label != last_loop:
                    self._directives.append(
                        f"({label}){loops if loops > 1 else ''}"
                    )
                else:
                    self._directives[-1] += f"{loops + 1}"
                break

            skip_count = 0

        return skip_count

    ###########################################################################

    def _reset_state(self):
        self._mml_state = MmlState(self.base_octave, self.base_note_length)

        self._accent = False
        self._loops = {}
        self._staccato = False

    ###########################################################################
    # API method definitions
    ###########################################################################

    def check(self):
        """
        Confirm that the channel's notes are acceptable.

        Raises
        ------
        MusicXmlException :
            Whenever an invalid percussion note is used, or when a musical note
            outside octaves 1-6  is used.
        """
        for token in self[:]:
            if isinstance(token, Note):
                note = token.note_num
                measure = token.measure_num
                if self.percussion:
                    try:
                        _PERCUSSION_MAP[token.head][
                            token.name + str(token.octave + 1)
                        ]
                    except KeyError as e:
                        raise MusicXmlException(
                            f"Bad percussion note #{note} in measure {measure}"
                        ) from e
                else:
                    if not 0 <= token.octave <= 6:
                        raise MusicXmlException(
                            f"Bad note #{note} in measure {measure}"
                        )

    ###########################################################################

    def generate_mml(self, measure_numbers: bool = True) -> str:
        """
        Generate this channel's AddMusicK MML text.

        Parameters
        ----------
        measure_numbers: bool
            True iff measure numbers should be included in MML

        Return
        ------
        str
            The MML text for this channel
        """
        self._reset_state()
        self._directives = [f"o{self._mml_state.octave}"]
        self._directives.append(f"l{self._mml_state.default_note_len}")
        self._mml_state.measure_numbers = measure_numbers

        for elem in self.elems:
            elem.emit(self._mml_state, self._directives)

        lines = " ".join(self._directives).splitlines()
        return CRLF.join(x.strip() for x in lines)

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def base_note_length(self) -> int:
        """Return this channel's most common note/rest length."""
        return _most_common(
            x.duration for x in self.elems if isinstance(x, (Note, Rest))
        )

    ###########################################################################

    @property
    def base_octave(self) -> int:
        """Return this channel's most common octave."""
        return _most_common(
            x.octave for x in self.elems if isinstance(x, Note)
        )
