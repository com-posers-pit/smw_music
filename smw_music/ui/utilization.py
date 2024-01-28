# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only


###############################################################################
# Imports
###############################################################################

# Library imports
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QLabel

# Package imports
from smw_music.amk import Utilization
from smw_music.ui.utils import Color

###############################################################################
# Private variable Definitions
###############################################################################

_DARK_MODE = {
    "ENGINE": Color.GOLD,
    "SONG": Color.IVORY,
    "SAMPLES": Color.BLUE_GROTTO,
    "ECHO": Color.CHILI_PEPPER,
    "FREE": Color.BLACK,
}

###############################################################################

_LIGHT_MODE = {
    "ENGINE": Color.MIDNIGHT_BLUE,
    "SONG": Color.ORANGE,
    "SAMPLES": Color.BLUE_GRAY,
    "ECHO": Color.HOT_PINK,
    "FREE": Color.IVORY,
}

###############################################################################

_colors = _DARK_MODE

###############################################################################
# API Function Definitions
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
