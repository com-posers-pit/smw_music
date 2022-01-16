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
from typing import Dict, Iterable, List, TypeVar

###############################################################################
# Project imports
###############################################################################

from .context import MmlState
from .shared import CRLF
from .tokens import Loop, Note, Playable, Rest, Token

###############################################################################
# Private variable/constant definitions
###############################################################################

# Generic type variable
_T = TypeVar("_T")

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
        self._mml_state = MmlState(self.base_octave, self.base_note_length)
        self._mml_state.percussion = self.percussion

        self._accent = False
        self._loops = {}
        self._staccato = False

    ###########################################################################
    # Private property definitions
    ###########################################################################

    @property
    def _playable(self) -> List[Playable]:
        playable: List[Playable] = []
        for token in self.tokens:
            if isinstance(token, Playable):
                playable.append(token)
            elif isinstance(token, Loop):
                for loop_tok in token.tokens:
                    if isinstance(loop_tok, Playable):
                        playable.append(loop_tok)
        return playable

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
        for token in [x for x in self._playable if isinstance(x, Note)]:
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
        self._directives = [f"o{self._mml_state.octave}"]
        self._directives.append(f"l{self._mml_state.default_note_len}")
        self._mml_state.measure_numbers = measure_numbers

        for elem in self.tokens:
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
            x.duration for x in self._playable if isinstance(x, (Note, Rest))
        )

    ###########################################################################

    @property
    def base_octave(self) -> int:
        """Return this channel's most common octave."""
        if self.percussion:
            octave = 4
        else:
            octave = _most_common(
                x.octave for x in self._playable if isinstance(x, Note)
            )

        return octave
