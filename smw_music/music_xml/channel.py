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
from itertools import takewhile
from typing import cast, Dict, Iterable, List, Tuple, TypeVar

###############################################################################
# Project imports
###############################################################################

from .context import MmlState
from .shared import CRLF, octave_notelen_str
from .tokens import flatten, Note, Playable, RehearsalMark, Token

###############################################################################
# Private variable/constant definitions
###############################################################################

# Generic type variable
_T = TypeVar("_T")

###############################################################################
# Private function definitions
###############################################################################


def _default_octave_notelen(
    tokens: List[Token], section: bool = True
) -> Tuple[int, int]:

    if section:
        tokens = list(
            takewhile(lambda x: not isinstance(x, RehearsalMark), tokens)
        )
    playable = [x for x in tokens if isinstance(x, Playable)]

    octaves = [cast(Note, x).octave for x in playable if isinstance(x, Note)]
    octave = _most_common(octaves) if octaves else 4
    notelen = _most_common([x.duration for x in playable]) if playable else 1

    return (octave, notelen)


###############################################################################


def _most_common(container: Iterable[_T]) -> _T:
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
    tokens: list
        A list of valid channel tokens
    percussion: bool
        Ture iff this is a percussion channel

    Attributes
    ----------
    tokens: list
        A list of elements in this tokens
    percussion: bool
        Ture iff this is a percussion channel

    Todo
    ----
    Parameterize grace note length?
    """

    tokens: List[Token]
    percussion: bool
    _accent: bool = field(init=False, repr=False, compare=False)
    _directives: List[str] = field(init=False, repr=False, compare=False)
    _loops: Dict[int, List[Token]] = field(
        init=False, repr=False, compare=False
    )
    _measure_numbers: bool = field(init=False, repr=False, compare=False)
    _staccato: bool = field(init=False, repr=False, compare=False)
    _mml_state: MmlState = field(init=False, repr=False, compare=False)

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __getitem__(self, n: int) -> Token:
        return self.tokens[n]

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _reset_state(self):
        self._mml_state = MmlState()
        self._update_state_defaults(
            *_default_octave_notelen(flatten(self.tokens))
        )
        self._mml_state.percussion = self.percussion

        self._accent = False
        self._loops = {}
        self._staccato = False

    ###########################################################################

    def _update_state_defaults(self, octave: int, notelen: int):
        if self.percussion:
            octave = 4  # Default percussion octave
        self._mml_state.octave = octave
        self._mml_state.default_note_len = notelen

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
        for token in [x for x in flatten(self.tokens) if isinstance(x, Note)]:
            token.check(self.percussion)

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
        self._mml_state.measure_numbers = measure_numbers

        octave_notelen = octave_notelen_str(
            self._mml_state.octave, self._mml_state.default_note_len
        )
        self._directives = [octave_notelen]

        for n, elem in enumerate(self.tokens):
            if isinstance(elem, RehearsalMark):
                self._update_state_defaults(
                    *_default_octave_notelen(flatten(self.tokens[n + 1 :]))
                )
            elem.emit(self._mml_state, self._directives)

        lines = " ".join(self._directives).splitlines()
        return CRLF.join(x.strip() for x in lines)
