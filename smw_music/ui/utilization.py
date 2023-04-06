# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only


###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Library imports
import numpy as np
import numpy.typing as npt
from PIL import Image
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QLabel

###############################################################################
# Private Class Definitions
###############################################################################


# https://www.oberlo.com/blog/color-combinations-cheat-sheet
class _Color(Enum):
    BLACK = QColor("#000000")

    GOLD = QColor("#E1A730")
    IVORY = QColor("#E0E3D7")
    BLUE_GROTTO = QColor("#2879C0")
    CHILI_PEPPER = QColor("#AB3910")

    MIDNIGHT_BLUE = QColor("#284E60")
    ORANGE = QColor("#F99845")
    BLUE_GRAY = QColor("#63AAC0")
    HOT_PINK = QColor("#D95980")


###############################################################################


class _UsageType(Enum):
    VARIABLES = (255, 0, 0)
    ENGINE = (255, 255, 0)
    SONG = (0, 128, 0)
    SAMPLE_TABLE = (0, 255, 0)
    ECHO = (160, 0, 160)
    ECHO_PAD = (63, 63, 63)
    FREE = (0, 0, 0)


###############################################################################
# Private Function Definitions
###############################################################################


def _count_matches(arr: npt.NDArray[np.uint8], val: _UsageType) -> int:
    (matches,) = np.where((arr == val.value).all(axis=1))
    return len(matches)


###############################################################################
# Private variable Definitions
###############################################################################

_DARK_MODE = {
    "ENGINE": _Color.GOLD,
    "SONG": _Color.IVORY,
    "SAMPLES": _Color.BLUE_GROTTO,
    "ECHO": _Color.CHILI_PEPPER,
    "FREE": _Color.BLACK,
}

###############################################################################

_LIGHT_MODE = {
    "ENGINE": _Color.MIDNIGHT_BLUE,
    "SONG": _Color.ORANGE,
    "SAMPLES": _Color.BLUE_GRAY,
    "ECHO": _Color.HOT_PINK,
    "FREE": _Color.IVORY,
}

###############################################################################

_colors = _DARK_MODE

###############################################################################
# API Class Definitions
###############################################################################


@dataclass
class Utilization:
    variables: int
    engine: int
    song: int
    sample_table: int
    samples: int
    echo: int
    echo_pad: int

    size: int = field(init=False, default=65536)

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def free(self) -> int:
        return self.size - self.util

    ###########################################################################

    @property
    def util(self) -> int:
        return (
            self.variables
            + self.engine
            + self.song
            + self.sample_table
            + self.samples
            + self.echo
            + self.echo_pad
        )


###############################################################################
# API Function Definitions
###############################################################################


def decode_utilization(png_name: Path) -> Utilization:
    with Image.open(png_name) as png:
        img = np.array(png.convert("RGB").getdata())

    variables = _count_matches(img, _UsageType.VARIABLES)
    engine = _count_matches(img, _UsageType.ENGINE)
    song = _count_matches(img, _UsageType.SONG)
    sample_table = _count_matches(img, _UsageType.SAMPLE_TABLE)
    echo = _count_matches(img, _UsageType.ECHO)
    echo_pad = _count_matches(img, _UsageType.ECHO_PAD)
    free = _count_matches(img, _UsageType.FREE)
    samples = (
        len(img)
        - variables
        - engine
        - song
        - sample_table
        - echo
        - echo_pad
        - free
    )

    return Utilization(
        variables=variables,
        engine=engine,
        song=song,
        sample_table=sample_table,
        samples=samples,
        echo=echo,
        echo_pad=echo_pad,
    )


###############################################################################


def default_utilization() -> Utilization:
    return Utilization(
        variables=1102,
        engine=9938,
        song=119,
        sample_table=80,
        samples=12815,
        echo=4,
        echo_pad=252,
    )


###############################################################################


def echo_bytes(delay: int) -> tuple[int, int]:
    if delay == 0:
        rv = (4, 252)
    else:
        rv = (2048 * delay, 0)

    return rv


###############################################################################


def paint_utilization(
    util: Utilization, util_label: QLabel, free_label: QLabel
) -> None:
    fixed_b = util.variables + util.engine
    song_b = util.song
    samples_b = util.samples + util.sample_table
    echo_b = util.echo + util.echo_pad
    free_b = util.free
    total_b = util.size

    fixed_pct = fixed_b / total_b
    song_pct = song_b / total_b
    samples_pct = samples_b / total_b
    echo_pct = echo_b / total_b
    free_pct = free_b / total_b

    canvas = util_label.pixmap()

    rect = canvas.rect()
    start_x = rect.x()
    start_y = rect.y()
    width = rect.width()
    height = rect.height()

    painter = QPainter()
    painter.begin(canvas)

    start, end = start_x, int(fixed_pct * width)
    painter.fillRect(start, start_y, end, height, _colors["ENGINE"].value)

    start, end = end, end + int(song_pct * width)
    painter.fillRect(start, start_y, end, height, _colors["SONG"].value)

    start, end = end, end + int(samples_pct * width)
    painter.fillRect(start, start_y, end, height, _colors["SAMPLES"].value)

    start, end = end, end + int(echo_pct * width)
    painter.fillRect(start, start_y, end, height, _colors["ECHO"].value)

    start, end = end, width
    painter.fillRect(start, start_y, end, height, _colors["FREE"].value)

    painter.end()

    util_label.setPixmap(canvas)

    usage_b = ", ".join(
        [
            f"{fixed_b}B Engine",
            f"{song_b}B Song",
            f"{samples_b}B Samples",
            f"{echo_b}B Echo",
            f"{free_b}B Free",
        ]
    )
    usage_pct = ", ".join(
        [
            f"{100*fixed_pct:2.0f}% Engine",
            f"{100*song_pct:2.0f}% Song",
            f"{100*samples_pct:2.0f}% Samples",
            f"{100*echo_pct:2.0f}% Echo",
            f"{100*free_pct:2.0f}% Free",
        ]
    )

    util_label.setToolTip(f"{usage_pct}\n{usage_b}")
    free_label.setText(f"{100*free_pct:+3.0f}%")

    # There's something not quite right in our ARAM estimates, smells like
    # alignment, so for now make this red if we're under 1k
    free_color = "#ff0000" if free_b < 1024 else "#00AA00"
    free_label.setStyleSheet(f"color: {free_color}")


###############################################################################


# TODO: This is hiding state in the module, kinda gross and suggests a class
def setup_utilization(
    dark: bool, engine: QLabel, song: QLabel, samples: QLabel, echo: QLabel
) -> None:

    global _colors
    _colors = _DARK_MODE if dark else _LIGHT_MODE

    engine.setStyleSheet(f"color: {_colors['ENGINE'].value.name()}")
    song.setStyleSheet(f"color: {_colors['SONG'].value.name()}")
    samples.setStyleSheet(f"color: {_colors['SAMPLES'].value.name()}")
    echo.setStyleSheet(f"color: {_colors['ECHO'].value.name()}")
