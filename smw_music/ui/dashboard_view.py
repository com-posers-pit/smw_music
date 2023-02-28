# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

# Generated from a tool, do not manually update.

# Library imports
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDial,
    QFrame,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTabWidget,
    QTreeWidget,
    QWidget,
)


class DashboardView(QMainWindow):
    actionClearRecentProjects: QAction
    adsr_box: QFrame
    artic_acc_group: QGroupBox
    artic_acc_length_label: QLabel
    artic_acc_length_setting: QLineEdit
    artic_acc_length_slider: QSlider
    artic_acc_setting_label: QLabel
    artic_acc_volume_label: QLabel
    artic_acc_volume_setting: QLineEdit
    artic_acc_volume_slider: QSlider
    artic_accstacc_group: QGroupBox
    artic_accstacc_length_label: QLabel
    artic_accstacc_length_setting: QLineEdit
    artic_accstacc_length_slider: QSlider
    artic_accstacc_setting_label: QLabel
    artic_accstacc_volume_label: QLabel
    artic_accstacc_volume_setting: QLineEdit
    artic_accstacc_volume_slider: QSlider
    artic_default_group: QGroupBox
    artic_default_length_label: QLabel
    artic_default_length_setting: QLineEdit
    artic_default_length_slider: QSlider
    artic_default_setting_label: QLabel
    artic_default_volume_label: QLabel
    artic_default_volume_setting: QLineEdit
    artic_default_volume_slider: QSlider
    artic_stacc_group: QGroupBox
    artic_stacc_length_label: QLabel
    artic_stacc_length_setting: QLineEdit
    artic_stacc_length_slider: QSlider
    artic_stacc_setting_label: QLabel
    artic_stacc_volume_label: QLabel
    artic_stacc_volume_setting: QLineEdit
    artic_stacc_volume_slider: QSlider
    attack_eu_label: QLabel
    attack_label: QLabel
    attack_setting: QLineEdit
    attack_slider: QSlider
    brr_fname: QLineEdit
    brr_setting: QLineEdit
    brr_setting_label: QLabel
    builtin_sample: QComboBox
    centralwidget: QWidget
    close_project: QAction
    control_groupBox: QGroupBox
    decay_eu_label: QLabel
    decay_label: QLabel
    decay_setting: QLineEdit
    decay_slider: QSlider
    dynamics_spacer: QWidget
    dynamics_widget: QWidget
    echo_ch0: QCheckBox
    echo_ch1: QCheckBox
    echo_ch2: QCheckBox
    echo_ch3: QCheckBox
    echo_ch4: QCheckBox
    echo_ch5: QCheckBox
    echo_ch6: QCheckBox
    echo_ch7: QCheckBox
    echo_channels_label: QLabel
    echo_control_widget: QWidget
    echo_delay_label: QLabel
    echo_delay_setting: QLineEdit
    echo_delay_setting_label: QLabel
    echo_delay_slider: QSlider
    echo_enable: QCheckBox
    echo_feedback_label: QLabel
    echo_feedback_setting: QLineEdit
    echo_feedback_setting_label: QLabel
    echo_feedback_slider: QSlider
    echo_feedback_surround: QCheckBox
    echo_filter_0: QRadioButton
    echo_filter_1: QRadioButton
    echo_filter_label: QLabel
    echo_left_label: QLabel
    echo_left_setting: QLineEdit
    echo_left_setting_label: QLabel
    echo_left_slider: QSlider
    echo_left_surround: QCheckBox
    echo_right_label: QLabel
    echo_right_setting: QLineEdit
    echo_right_setting_label: QLabel
    echo_right_slider: QSlider
    echo_right_surround: QCheckBox
    echo_settings_box: QGroupBox
    echo_sliders_widget: QWidget
    envelope_tab: QWidget
    exit_dashboard: QAction
    f_label: QLabel
    f_setting: QLineEdit
    f_setting_label: QLabel
    f_slider: QSlider
    ff_label: QLabel
    ff_setting: QLineEdit
    ff_setting_label: QLabel
    ff_slider: QSlider
    fff_label: QLabel
    fff_setting: QLineEdit
    fff_setting_label: QLabel
    fff_slider: QSlider
    ffff_label: QLabel
    ffff_setting: QLineEdit
    ffff_setting_label: QLabel
    ffff_slider: QSlider
    gain_box: QFrame
    gain_eu_label: QLabel
    gain_frame: QFrame
    gain_label: QLabel
    gain_mode_decexp: QRadioButton
    gain_mode_declin: QRadioButton
    gain_mode_direct: QRadioButton
    gain_mode_frame: QFrame
    gain_mode_incbent: QRadioButton
    gain_mode_inclin: QRadioButton
    gain_mode_label: QLabel
    gain_setting: QLineEdit
    gain_setting_label: QLabel
    gain_slider: QSlider
    game_name: QLineEdit
    game_name_label: QLabel
    generate_and_play: QPushButton
    generate_mml: QPushButton
    generate_spc: QPushButton
    global_legato: QCheckBox
    global_settings_tab: QWidget
    global_volume_box: QGroupBox
    global_volume_setting: QLineEdit
    global_volume_setting_label: QLabel
    global_volume_slider: QSlider
    instrument_articulation_tab: QWidget
    instrument_config_tab: QTabWidget
    instrument_dynamics_tab: QWidget
    instrument_list: QTableWidget
    instrument_list_box: QGroupBox
    instrument_sample_group: QGroupBox
    instrument_sample_tab: QWidget
    instrument_settings_tab: QWidget
    interpolate: QCheckBox
    loop_analysis: QCheckBox
    measure_numbers: QCheckBox
    menuEdit: QAction
    menuFile: QAction
    menuHelp: QAction
    menuRecent_Projects: QAction
    menubar: QMenuBar
    mf_label: QLabel
    mf_setting: QLineEdit
    mf_setting_label: QLabel
    mf_slider: QSlider
    mml_fname: QLineEdit
    mp_label: QLabel
    mp_setting: QLineEdit
    mp_setting_label: QLabel
    mp_slider: QSlider
    multisample_fname: QLineEdit
    musicxml_fname: QLineEdit
    mute_percussion: QCheckBox
    new_project: QAction
    octave: QSpinBox
    octave_label: QLabel
    open_history: QPushButton
    open_preferences: QAction
    open_project: QAction
    open_quicklook: QPushButton
    other_settings_box: QGroupBox
    p_label: QLabel
    p_setting: QLineEdit
    p_setting_label: QLabel
    p_slider: QSlider
    pan_enable: QCheckBox
    pan_group: QGroupBox
    pan_invert_label: QLabel
    pan_l_invert: QCheckBox
    pan_r_invert: QCheckBox
    pan_setting: QDial
    pan_setting_label: QLabel
    percussion_label: QLabel
    play_spc: QPushButton
    porter_name: QLineEdit
    porter_name_label: QLabel
    pp_label: QLabel
    pp_setting: QLineEdit
    pp_setting_label: QLabel
    pp_slider: QSlider
    ppp_label: QLabel
    ppp_setting: QLineEdit
    ppp_setting_label: QLabel
    ppp_slider: QSlider
    pppp_label: QLabel
    pppp_setting: QLineEdit
    pppp_setting_label: QLabel
    pppp_slider: QSlider
    preview_envelope: QPushButton
    redo: QAction
    reload_musicxml: QPushButton
    sample_pack_list: QTreeWidget
    sample_settings_box: QGroupBox
    sample_settings_tabs: QTabWidget
    sample_settings_widget: QWidget
    save_project: QAction
    select_adsr_mode: QRadioButton
    select_brr_fname: QPushButton
    select_brr_sample: QRadioButton
    select_builtin_sample: QRadioButton
    select_gain_mode: QRadioButton
    select_mml_fname: QPushButton
    select_multisample_fname: QPushButton
    select_multisample_sample: QRadioButton
    select_musicxml_fname: QPushButton
    select_pack_sample: QRadioButton
    separator: QAction
    settings_tab_widget: QTabWidget
    show_about: QAction
    show_about_qt: QAction
    solo_percussion: QCheckBox
    splitter: QSplitter
    splitter_2: QSplitter
    splitter_3: QSplitter
    splitter_4: QSplitter
    splitter_5: QSplitter
    start_measure: QSpinBox
    start_measure_label: QLabel
    statusbar: QStatusBar
    subtune_label: QLabel
    subtune_setting: QLineEdit
    subtune_setting_label: QLabel
    subtune_slider: QSlider
    superloop_analysis: QCheckBox
    sus_level_eu_label: QLabel
    sus_level_label: QLabel
    sus_level_setting: QLineEdit
    sus_level_slider: QSlider
    sus_rate_eu_label: QLabel
    sus_rate_label: QLabel
    sus_rate_setting: QLineEdit
    sus_rate_slider: QSlider
    tune_label: QLabel
    tune_setting: QLineEdit
    tune_setting_label: QLabel
    tune_slider: QSlider
    tuning_tab: QWidget
    undo: QAction
