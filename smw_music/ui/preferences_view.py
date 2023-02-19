# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

# Generated from a tool, do not manually update.

# Library imports
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
)


class PreferencesView(QDialog):
    add_sample_pack: QPushButton
    amk_fname: QLineEdit
    amk_group_box: QGroupBox
    buttonBox: QDialogButtonBox
    remove_sample_pack: QPushButton
    sample_pack_box: QGroupBox
    sample_pack_fname: QLineEdit
    sample_pack_list: QListWidget
    sample_pack_name: QLineEdit
    sample_pack_name_lbl: QLabel
    select_amk_fname: QPushButton
    select_sample_pack_fname: QPushButton
    select_spcplay: QPushButton
    spcplay_fname: QLineEdit
    spcplay_groupbox: QGroupBox
