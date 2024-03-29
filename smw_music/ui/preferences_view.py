# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

# Generated from a tool, do not manually update.

# Library imports
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)


class PreferencesView(QDialog):
    advanced_mode: QCheckBox
    advanced_mode_label: QLabel
    amk_fname: QLineEdit
    amk_group_box: QGroupBox
    buttonBox: QDialogButtonBox
    confirm_render: QCheckBox
    confirm_render_label: QLabel
    convert_timeout: QSpinBox
    convert_timeout_label: QLabel
    dark_mode: QCheckBox
    dark_mode_label: QLabel
    release_check: QCheckBox
    release_check_update: QLabel
    sample_pack_box: QGroupBox
    sample_pack_dirname: QLineEdit
    select_amk_fname: QPushButton
    select_sample_pack_dirname: QPushButton
    select_spcplay: QPushButton
    spcplay_fname: QLineEdit
    spcplay_groupbox: QGroupBox
    widget: QWidget
