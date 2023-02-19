# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Single part/channel in a MusicXML file."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from collections import Counter
from dataclasses import dataclass, field
from itertools import takewhile
from typing import Iterable, TypeVar, cast

# Package imports
from smw_music.music_xml.mml import MmlExporter
from smw_music.music_xml.shared import CRLF, notelen_str
from smw_music.music_xml.tokens import (
    Error,
    Note,
    Playable,
    RehearsalMark,
    Token,
    flatten,
)

###############################################################################
# Private variable/constant definitions
###############################################################################

# Generic type variable
_T = TypeVar("_T")

###############################################################################
# Private function definitions
###############################################################################


def _default_notelen(tokens: list[Token], section: bool = True) -> int:
    if section:
        tokens = list(
            takewhile(lambda x: not isinstance(x, RehearsalMark), tokens)
        )
    playable = [x for x in flatten(tokens) if isinstance(x, Playable)]

    notelen = _most_common([x.duration for x in playable]) if playable else 0

    return notelen


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

    tokens: list[Token]
    percussion: bool
    _directives: list[str] = field(init=False, repr=False, compare=False)
    _exporter: MmlExporter = field(init=False, repr=False, compare=False)

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __getitem__(self, n: int) -> Token:
        return self.tokens[n]

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _reset_state(self, instr_octave_map: dict[str, int]) -> None:
        self._exporter = MmlExporter(instr_octave_map)
        self._exporter.percussion = self.percussion

        notelen = _default_notelen(flatten(self.tokens))
        self._update_state_defaults(notelen)

        if notelen:
            self._exporter.directives = [notelen_str(notelen), CRLF]

    ###########################################################################

    def _update_state_defaults(self, notelen: int) -> None:
        self._exporter.default_note_len = notelen

    ###########################################################################
    # API method definitions
    ###########################################################################

    def check(self) -> list[str]:
        """
        Confirm that the channel's notes are acceptable.

        Raises
        ------
        MusicXmlException :
            Whenever an invalid percussion note is used, or when a musical note
            outside octaves 1-6  is used.
        """
        msgs = []
        tokens = flatten(self.tokens)
        for token in filter(lambda x: isinstance(x, Error), tokens):
            msgs.append(cast(Error, token).msg)
        for token in filter(lambda x: isinstance(x, Note), tokens):
            msgs.extend(cast(Note, token).check(self.percussion))
        for token in filter(lambda x: isinstance(x, Playable), tokens):
            msgs.extend(cast(Playable, token).duration_check())
        return msgs

    ###########################################################################

    def generate_mml(
        self,
        instr_octave_map: dict[str, int],
        measure_numbers: bool = True,
        optimize_percussion: bool = True,
    ) -> str:
        """
        Generate this channel's AddMusicK MML text.

        Parameters
        ----------
        measure_numbers: bool
            True iff measure numbers should be included in MML
        optimize_percussion: bool
            True iff repeated percussion notes should not repeat their
            instrument

        Return
        ------
        str
            The MML text for this channel
        """
        self._reset_state(instr_octave_map)
        self._exporter.measure_numbers = measure_numbers
        self._exporter.optimize_percussion = optimize_percussion

        for n, token in enumerate(self.tokens):
            if isinstance(token, RehearsalMark):
                self._update_state_defaults(
                    _default_notelen(flatten(self.tokens[n + 1 :]))
                )
            self._exporter._emit(token)

        lines = " ".join(self._exporter.directives).splitlines()
        return CRLF.join(x.strip() for x in lines)
