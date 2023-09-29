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
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class ProjectSettingsView(QDialog):
    buttonBox: QDialogButtonBox
    composer: QLineEdit
    composer_label: QLabel
    control_widget: QWidget
    game_name: QLineEdit
    game_name_label: QLabel
    loop_analysis: QCheckBox
    measure_numbers: QCheckBox
    musicxml_fname: QLineEdit
    porter_name: QLineEdit
    porter_name_label: QLabel
    select_musicxml_fname: QPushButton
    superloop_analysis: QCheckBox
    title: QLineEdit
    title_label: QLabel
