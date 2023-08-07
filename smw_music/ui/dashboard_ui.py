# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard UI helper functions."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from typing import cast

# Library imports
from PyQt6.QtWidgets import QComboBox, QLabel

# Package imports
from smw_music.ui.dashboard_view import DashboardView
from smw_music.ui.state import BuiltinSampleGroup, BuiltinSampleSource, State

###############################################################################
# API function definitions
###############################################################################


def update_sample_opt(view: DashboardView, state: State) -> None:
    builtin_group = state.builtin_sample_group
    match builtin_group:
        case BuiltinSampleGroup.DEFAULT:
            view.sample_opt_default.setChecked(True)
        case BuiltinSampleGroup.OPTIMIZED:
            view.sample_opt_optimized.setChecked(True)
        case BuiltinSampleGroup.REDUX1:
            view.sample_opt_redux1.setChecked(True)
        case BuiltinSampleGroup.REDUX2:
            view.sample_opt_redux2.setChecked(True)
        case BuiltinSampleGroup.CUSTOM:
            view.sample_opt_custom.setChecked(True)

    enabled = state.builtin_sample_group == BuiltinSampleGroup.CUSTOM
    for n, source in enumerate(state.builtin_sample_sources):
        # This one's a little gross
        ctrl: QComboBox = cast(QComboBox, getattr(view, f"sample_opt_{n:02x}"))
        label = cast(QLabel, getattr(view, f"sample_opt_{n:02x}_label"))

        # TODO: Depends on the ordering in the dropdown, should be derivable
        idx = [
            BuiltinSampleSource.DEFAULT,
            BuiltinSampleSource.OPTIMIZED,
            BuiltinSampleSource.EMPTY,
        ].index(source)

        ctrl.setCurrentIndex(idx)
        ctrl.setEnabled(enabled)
        label.setEnabled(enabled)
