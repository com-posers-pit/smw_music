# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Single part/channel in a MusicXML file."""

###############################################################################
# Standard Library imports
###############################################################################

from collections import Counter
from enum import auto, Enum
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, TypeVar

###############################################################################
# Project imports
###############################################################################

from .shared import CRLF, MusicXmlException
from .tokens import (
    Annotation,
    Token,
    Dynamic,
    RehearsalMark,
    Loop,
    Measure,
    Note,
    Repeat,
    Rest,
    Slur,
    Triplet,
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
# Private class definitions
###############################################################################


class _SlurState(Enum):
    SLUR_IDLE = auto()
    SLUR_ACTIVE = auto()
    SLUR_END = auto()


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
    _cur_octave: int = field(init=False, repr=False, compare=False)
    _directives: List[str] = field(init=False, repr=False, compare=False)
    _grace: bool = field(init=False, repr=False, compare=False)
    _legato: bool = field(init=False, repr=False, compare=False)
    _loops: Dict[int, List[Token]] = field(
        init=False, repr=False, compare=False
    )
    _measure_numbers: bool = field(init=False, repr=False, compare=False)
    _staccato: bool = field(init=False, repr=False, compare=False)
    _tie: bool = field(init=False, repr=False, compare=False)
    _slur_state: _SlurState = field(init=False, repr=False, compare=False)

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __getitem__(self, n: int) -> Token:
        return self.elems[n]

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _calc_note_length(self, note: "Note") -> str:
        grace_length = 8
        note_length = ""

        if self._slur_state == _SlurState.SLUR_END:
            self._slur_state = _SlurState.SLUR_IDLE
            duration = 192 // note.duration
            duration = int(duration * (2 - 0.5 ** note.dots))
            self._legato = False
            note_length = f"=1 LEGATO_OFF ^={duration - 1}"
        else:
            if not self._grace and not note.grace:
                if note.duration != self.base_note_length:
                    note_length = str(note.duration)
                note_length += note.dots * "."
            else:
                if note.grace:
                    note_length = f"={grace_length}"
                else:
                    duration = 192 // note.duration
                    duration = int(duration * (2 - 0.5 ** note.dots))
                    note_length = f"={duration - grace_length}"

        return note_length

    ###########################################################################

    def _emit_annotation(self, annotation: Annotation):
        if annotation.amk_annotation:
            self._directives.append(annotation.amk_text)

    ###########################################################################

    def _emit_dynamic(self, dyn: "Dynamic"):
        volmap = {
            "pppp": "vPPPP",
            "ppp": "vPPP",
            "pp": "vPP",
            "p": "vP",
            "mp": "vMP",
            "mf": "vMF",
            "f": "vF",
            "ff": "vFF",
            "fff": "vFFF",
            "ffff": "vFFFF",
        }
        self._directives.append(volmap[dyn.level])

    ###########################################################################

    def _emit_rehearsal_mark(self, mark: RehearsalMark):
        self._directives.append(CRLF)
        self._directives.append(f";===================={CRLF}")
        self._directives.append(f"; Section {mark.mark}{CRLF}")
        self._directives.append(f";===================={CRLF}")
        self._directives.append(CRLF)

    ###########################################################################

    def _emit_measure(self, measure: "Measure"):
        num = measure.number
        comment = ""
        if self._measure_numbers and num > 0:
            comment = f"; Measure {num}"

        self._directives.append(f"{comment}{CRLF}")

    ###########################################################################

    def _emit_octave(self, note: "Note"):
        octave = note.octave
        if octave != self._cur_octave:
            if octave == self._cur_octave - 1:
                directive = "<"
            elif octave == self._cur_octave + 1:
                directive = ">"
            else:
                directive = f"o{octave}"
            self._directives.append(directive)
            self._cur_octave = octave

    ###########################################################################

    def _emit_note(self, note: "Note"):  # pylint: disable=too-many-branches
        if note.grace:
            self._grace = True

        if not self.percussion:
            self._emit_octave(note)

        if self._tie:
            directive = "^"
        else:
            if not self.percussion:
                directive = note.name
            else:
                directive = (
                    _PERCUSSION_MAP[note.head][
                        note.name + str(note.octave + 1)
                    ]
                    + " c"
                )

        directive += self._calc_note_length(note)

        if note.tie == "start":
            self._tie = True

        self._start_legato()

        if not note.accent and self._accent:
            self._accent = False
            self._directives.append("qACC_OFF")
        if not note.staccato and self._staccato:
            self._staccato = False
            self._directives.append("qSTAC_OFF")

        if note.accent and not self._accent:
            self._accent = True
            self._directives.append("qACC_ON")

        if note.staccato and not self._staccato:
            self._staccato = True
            self._directives.append("qSTAC_ON")

        self._directives.append(directive)

        if note.tie == "stop":
            self._tie = False

        if not note.grace:
            self._grace = False

        self._stop_legato()

    ###########################################################################

    def _emit_repeat(self, repeat: "Repeat"):
        if repeat.start:
            self._directives.append("/")

    ###########################################################################

    def _emit_rest(self, rest: "Rest"):
        directive = "r"
        if rest.duration != self.base_note_length:
            directive += str(rest.duration)
        directive += rest.dots * "."

        self._directives.append(directive)

    ###########################################################################

    def _emit_token(self, elem: Token):
        if isinstance(elem, Repeat):
            self._emit_repeat(elem)

        if isinstance(elem, Rest):
            self._emit_rest(elem)

        if isinstance(elem, Dynamic):
            self._emit_dynamic(elem)

        if isinstance(elem, RehearsalMark):
            self._emit_rehearsal_mark(elem)

        if isinstance(elem, Note):
            self._emit_note(elem)

        if isinstance(elem, Measure):
            self._emit_measure(elem)

        if isinstance(elem, Annotation):
            self._emit_annotation(elem)

        if isinstance(elem, Slur):
            self._slur_state = (
                _SlurState.SLUR_ACTIVE if elem.start else _SlurState.SLUR_END
            )

        if isinstance(elem, Triplet):
            self._emit_triplet(elem)

        if isinstance(elem, Loop):
            if elem.superloop:
                open_dir = "[[ "
                close_dir = "]]"
            else:
                open_dir = f"({elem.loop_id})[ "
                close_dir = "]"
            if elem.repeats > 1:
                close_dir += str(elem.repeats)

            self._directives.append(open_dir)

            for loop_elem in elem.elem:
                if isinstance(loop_elem, Note):
                    self._emit_note(loop_elem)
                elif isinstance(loop_elem, Rest):
                    self._emit_rest(loop_elem)

            self._directives.append(close_dir)

    ###########################################################################

    def _emit_triplet(self, elem: Triplet):
        self._directives.append("{" if elem.start else "}")

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
        self._accent = False
        self._cur_octave = 3 if self.percussion else self.base_octave
        self._grace = False
        self._legato = False
        self._loops = {}
        self._measure_numbers = True
        self._slur_state = _SlurState.SLUR_IDLE
        self._staccato = False
        self._tie = False

    ###########################################################################

    def _start_legato(self):
        if not self._legato:
            if (self._slur_state == _SlurState.SLUR_ACTIVE) or self._grace:
                self._legato = True
                self._directives.append("LEGATO_ON")

    ###########################################################################

    def _stop_legato(self):
        if self._legato:
            if not (
                self._grace
                or (self._slur_state == _SlurState.SLUR_ACTIVE)
                or self._tie
            ):
                self._legato = False
                self._directives.append("LEGATO_OFF")

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
        self._directives = [f"o{self._cur_octave}"]
        self._directives.append(f"l{self.base_note_length}")
        self._measure_numbers = measure_numbers

        # In desperate need of a refactor
        for elem in self.elems:
            self._emit_token(elem)

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
