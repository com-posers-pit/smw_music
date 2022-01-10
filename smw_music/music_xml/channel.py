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
from typing import Dict, Iterable, List, Tuple, TypeVar, Union

###############################################################################
# Project imports
###############################################################################

from .shared import CRLF
from .tokens import (
    Annotation,
    ChannelElem,
    Dynamic,
    Loop,
    Measure,
    Note,
    Repeat,
    Rest,
)

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
    elems: list
        A list of valid channel elements (currently `Annotation`, `Dynamic`,
        `Measure`, `Note`, `Repeat`, and `Rest`)

    Attributes
    ----------
    elems: list
        A list of elements in this channel

    Todo
    ----
    Parameterize grace note length?
    """

    elems: List[ChannelElem]
    _accent: bool = field(init=False, repr=False, compare=False)
    _cur_octave: int = field(init=False, repr=False, compare=False)
    _directives: List[str] = field(init=False, repr=False, compare=False)
    _grace: bool = field(init=False, repr=False, compare=False)
    _legato: bool = field(init=False, repr=False, compare=False)
    _loops: Dict[int, List[ChannelElem]] = field(
        init=False, repr=False, compare=False
    )
    _slur: bool = field(init=False, repr=False, compare=False)
    _staccato: bool = field(init=False, repr=False, compare=False)
    _tie: bool = field(init=False, repr=False, compare=False)
    _triplet: bool = field(init=False, repr=False, compare=False)

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __getitem__(self, n: int) -> ChannelElem:
        return self.elems[n]

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _calc_note_length(self, note: "Note") -> str:
        grace_length = 8
        note_length = ""

        if note.slur is False:
            self._slur = False
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

    def _emit_measure(self, _: "Measure"):
        self._directives.append(CRLF)

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

    def _emit_note(self, note: "Note"):

        self._handle_triplet(note)

        if note.grace:
            self._grace = True
        if note.slur:
            self._slur = True

        self._emit_octave(note)

        directive = "^" if self._tie else note.name
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
        self._handle_triplet(rest)

        directive = "r"
        if rest.duration != self.base_note_length:
            directive += str(rest.duration)
        directive += rest.dots * "."

        self._directives.append(directive)

    ###########################################################################

    def _handle_triplet(self, elem: Union["Rest", "Note"]):
        if not self._triplet and elem.triplet:
            self._directives.append("{")
        if self._triplet and not elem.triplet:
            self._directives.append("}")
        self._triplet = elem.triplet

    ###########################################################################

    def _loop_analysis(self, idx: int) -> int:
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
                self._directives.append(
                    f"({label}){loops if loops > 1 else ''}"
                )
                break

            skip_count = 0

        return skip_count

    ###########################################################################

    def _repeat_analysis(self, idx: int) -> Tuple[int, int]:
        repeat_count = 0
        skip_count = 0

        elem = self.elems[idx]

        # Look for repeats
        if isinstance(elem, (Note, Rest)):
            repeat_count = 1
            skip_count = 0
            for rep_cand in self.elems[idx + 1 :]:
                if rep_cand == elem:
                    repeat_count += 1
                    skip_count += 1
                elif isinstance(rep_cand, Measure):
                    skip_count += 1
                elif (
                    isinstance(rep_cand, Annotation)
                    and not rep_cand.amk_annotation
                ):
                    skip_count += 1
                else:
                    break

        if repeat_count >= 3:
            self._directives.append("[")
        else:
            skip_count = 0

        return (skip_count, repeat_count)

    ###########################################################################

    def _reset_state(self):
        self._accent = False
        self._cur_octave = self.base_octave
        self._grace = False
        self._legato = False
        self._loops = {}
        self._slur = False
        self._staccato = False
        self._tie = False
        self._triplet = False

    ###########################################################################

    def _start_legato(self):
        if not self._legato:
            if self._slur or self._grace:
                self._legato = True
                self._directives.append("LEGATO_ON")

    ###########################################################################

    def _stop_legato(self):
        if self._legato:
            if not (self._grace or self._slur or self._tie):
                self._legato = False
                self._directives.append("LEGATO_OFF")

    ###########################################################################
    # API method definitions
    ###########################################################################

    def generate_mml(  # pylint: disable=too-many-branches
        self, loop_analysis: bool = True
    ) -> str:
        """
        Generate this channel's AddMusicK MML text.

        Parameters
        ----------
        loop_analysis: bool
            True iff loop analysis should be enabled


        Return
        ------
        str
            The MML text for this channel
        """
        self._reset_state()
        self._directives = [f"o{self._cur_octave}"]
        self._directives.append(f"l{self.base_note_length}")

        skip_count = 0
        repeat_count = 0
        in_loop = False

        loop: List[ChannelElem] = []
        do_measure = False

        # In desperate need of a refactor
        for n, elem in enumerate(self.elems):
            if skip_count:
                skip_count -= 1
                if isinstance(elem, Measure):
                    do_measure = True
                continue

            if do_measure:
                do_measure = False
                if not isinstance(elem, Measure):
                    self._emit_measure(Measure())

            if isinstance(elem, Loop) and elem.start:
                in_loop = True
                loop = []
                self._loops[elem.label] = loop
                self._directives.append(f"({elem.label})[")

            if in_loop and isinstance(elem, (Rest, Dynamic, Note)):
                loop.append(elem)

            if loop_analysis and not in_loop:
                skip_count = self._loop_analysis(n)
                if skip_count:
                    continue

                skip_count, repeat_count = self._repeat_analysis(n)

            if isinstance(elem, Repeat):
                self._emit_repeat(elem)

            if isinstance(elem, Rest):
                self._emit_rest(elem)

            if isinstance(elem, Dynamic):
                self._emit_dynamic(elem)

            if isinstance(elem, Note):
                self._emit_note(elem)

            if isinstance(elem, Measure):
                self._emit_measure(elem)

            if isinstance(elem, Annotation):
                self._emit_annotation(elem)

            if repeat_count >= 3:
                self._directives.append(f"]{repeat_count}")
                repeat_count = 0

            if isinstance(elem, Loop) and not elem.start:
                in_loop = False
                self._directives.append("]")

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
