# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard Panels."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from typing import cast

# Library imports
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QBoxLayout,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

# Package imports
from smw_music.log import debug, info
from smw_music.music_xml.echo import EchoConfig
from smw_music.ui.widgets import (
    ArticSlider,
    FilePicker,
    PanControl,
    PctSlider,
    VolSlider,
)

###############################################################################
# API Class Definitions
###############################################################################


class ArticPanel(QWidget):
    artic_changed = pyqtSignal(str, int)  # arguments=["artic", "quant"]
    pan_changed = pyqtSignal(bool, int)  # arguments=["enable", "pan"]
    _sliders: dict[str, ArticSlider]
    _pan: PanControl

    ###########################################################################

    @debug()
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        artics = [
            ("Default", "DEF"),
            ("Accent", "ACC"),
            ("Staccato", "STAC"),
            ("Accent+Staccato", "ACCSTAC"),
        ]

        self._sliders = {key: ArticSlider(artic) for artic, key in artics}
        self._pan = PanControl()

        self._attach_signals()
        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info()
    def update_ui(self, artics: dict[str, int]) -> None:
        for artic, val in artics.items():
            self._sliders[artic].update_ui(val)

    ###########################################################################

    @info()
    def update_pan(self, pan: int | None) -> None:
        if pan is None:
            self._pan.set_pan(False, 10)
        else:
            self._pan.set_pan(True, pan)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _attach_signals(self) -> None:
        for artic, slider in self._sliders.items():
            slider.artic_changed.connect(
                lambda quant, artic=artic: self.artic_changed.emit(
                    artic, quant
                )
            )
        self._pan.pan_changed.connect(self.pan_changed)

    ###########################################################################

    @debug()
    def _do_layout(self) -> None:
        layout = QHBoxLayout()
        for slider in self._sliders.values():
            layout.addWidget(slider)
        layout.addWidget(self._pan)
        self.setLayout(layout)


###############################################################################


class ControlPanel(QWidget):
    config_changed = pyqtSignal([bool, bool, bool, bool, bool, bool])
    # arguments=[ "global_legato", "loop_analysis", "superloop_analysis",
    # "measure_numbers", "custom_samples", "custom_percussion", ]
    mml_converted = pyqtSignal()
    mml_requested = pyqtSignal(str)  # arguments=["fname"]
    quicklook_opened = pyqtSignal()
    song_changed = pyqtSignal(str)  # arguments=["fname"]
    spc_played = pyqtSignal()

    _musicxml_picker: FilePicker
    _mml_picker: FilePicker
    _play: QPushButton
    _convert: QPushButton
    _generate: QPushButton
    _global_legato: QCheckBox
    _loop_analysis: QCheckBox
    _superloop_analysis: QCheckBox
    _measure_numbers: QCheckBox
    _custom_samples: QCheckBox
    _custom_percussion: QCheckBox
    _open_quicklook: QPushButton

    ###########################################################################

    @debug()
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._musicxml_picker = FilePicker(
            "MusicXML",
            False,
            "Input MusicXML File",
            "MusicXML (*.mxl *.musicxml);;Any (*)",
            self,
        )
        self._mml_picker = FilePicker("MML", True, "Output MML File", "", self)
        self._play = QPushButton("Play SPC")
        self._convert = QPushButton("Convert MML")
        self._generate = QPushButton("Generate MML")
        self._open_quicklook = QPushButton("Open Quicklook")
        self._global_legato = QCheckBox("Global Legato")
        self._loop_analysis = QCheckBox("Loop Analysis")
        self._superloop_analysis = QCheckBox("Superloop Analysis")
        self._measure_numbers = QCheckBox("Measure Numbers")
        self._custom_samples = QCheckBox("Custom Samples")
        self._custom_percussion = QCheckBox("Custom Percussion")

        self._attach_signals()
        self._do_layout()

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _attach_signals(self) -> None:
        self._global_legato.stateChanged.connect(self._update_config)
        self._loop_analysis.stateChanged.connect(self._update_config)
        self._superloop_analysis.stateChanged.connect(self._update_config)
        self._measure_numbers.stateChanged.connect(self._update_config)
        self._custom_samples.stateChanged.connect(self._update_config)
        self._custom_percussion.stateChanged.connect(self._update_config)

        self._musicxml_picker.file_changed.connect(self._load_musicxml)
        self._generate.clicked.connect(self._generate_mml)
        self._open_quicklook.clicked.connect(self.quicklook_opened)
        self._convert.clicked.connect(self.mml_converted)
        self._play.clicked.connect(self.spc_played)

    ###########################################################################

    @debug()
    def _do_layout(self) -> None:
        layout = QVBoxLayout()

        layout.addWidget(self._musicxml_picker)
        layout.addWidget(self._global_legato)
        layout.addWidget(self._loop_analysis)
        layout.addWidget(self._superloop_analysis)
        layout.addWidget(self._measure_numbers)
        layout.addWidget(self._custom_samples)
        layout.addWidget(self._custom_percussion)
        layout.addWidget(self._mml_picker)
        layout.addWidget(self._open_quicklook)
        layout.addWidget(self._generate)
        layout.addWidget(self._convert)
        layout.addWidget(self._play)

        self.setLayout(layout)

    ###########################################################################

    @debug()
    def _generate_mml(self, _: bool) -> None:
        fname = self._mml_picker.fname
        self.mml_requested.emit(fname)

    ###########################################################################

    @debug()
    def _load_musicxml(self, fname: str) -> None:
        if fname:
            self.song_changed.emit(fname)

    ###########################################################################

    @debug()
    def _update_config(self, _: int) -> None:
        self.config_changed.emit(
            self._global_legato.isChecked(),
            self._loop_analysis.isChecked(),
            self._superloop_analysis.isChecked(),
            self._measure_numbers.isChecked(),
            self._custom_samples.isChecked(),
            self._custom_percussion.isChecked(),
        )


###############################################################################


class DynamicsPanel(QWidget):
    volume_changed = pyqtSignal(
        str, int, bool
    )  # arguments=["dynamics", "vol", "interp"]
    _sliders: dict[str, VolSlider]
    _interpolate: QCheckBox

    ###########################################################################

    @debug()
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        dynamics = [
            "PPPP",
            "PPP",
            "PP",
            "P",
            "MP",
            "MF",
            "F",
            "FF",
            "FFF",
            "FFFF",
        ]

        self._sliders = {}
        for dyn in dynamics:
            slider = VolSlider(dyn)
            self._sliders[dyn] = slider

        self._interpolate = QCheckBox("Interpolate")
        self._interpolate.setToolTip(
            "Adjust all dynamics settings based on the extreme values",
        )

        self._attach_signals()
        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info()
    def update_ui(self, config: dict[str, int], present: set[str]) -> None:
        for dyn, vol in config.items():
            self._sliders[dyn].set_volume(vol)
            self._sliders[dyn].setEnabled(dyn in present)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _attach_signals(self) -> None:
        for dyn, slider in self._sliders.items():
            slider.volume_changed.connect(
                lambda x, dyn=dyn: self.volume_changed.emit(
                    dyn, x, self._interpolate.isChecked()
                )
            )

    ###########################################################################

    @debug()
    def _do_layout(self) -> None:
        layout = QHBoxLayout()

        for slider in self._sliders.values():
            layout.addWidget(slider)

        layout.addWidget(self._interpolate)

        self.setLayout(layout)


###############################################################################


class EchoPanel(QWidget):
    _chan_enables: list[QCheckBox]
    _delay: QSlider
    _delay_display: QLabel
    _delay_panel: QWidget
    _lvol: PctSlider
    _rvol: PctSlider
    _fbvol: PctSlider
    _filter: tuple[QRadioButton, QRadioButton]
    _enable: QCheckBox

    ###########################################################################

    @debug()
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._enable = QCheckBox("Echo Enabled")
        self._chan_enables = [QCheckBox(str(n)) for n in range(8)]
        self._lvol = PctSlider("Left Volume")
        self._rvol = PctSlider("Right Volume")
        self._fbvol = PctSlider("Feedback")
        self._delay_panel = QWidget()
        self._delay = QSlider()
        self._delay_display = QLabel()
        self._filter = (QRadioButton("0"), QRadioButton("1"))

        self._attach_signals()

        self._delay.setRange(0, 15)
        self._delay.setValue(0)
        self._update_delay_display(0)
        self._filter[1].click()
        self._update_enables(False)
        self.update_ui(None)

        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info(True)
    def update_ui(self, config: EchoConfig | None) -> None:
        enable = config is not None
        self._enable.setChecked(enable)

        if enable:
            config = cast(EchoConfig, config)
            for n, widget in enumerate(self._chan_enables):
                widget.setChecked(n in config.chan_list)
            self._lvol.set_pct(config.vol_mag[0], config.vol_inv[0])
            self._rvol.set_pct(config.vol_mag[1], config.vol_inv[1])
            self._fbvol.set_pct(config.fb_mag, config.fb_inv)

            if config.fir_filt == 0:
                self._filter[0].setChecked(True)
            else:
                self._filter[1].setChecked(True)

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def config(self) -> EchoConfig | None:
        rv = None
        if self._enable.isChecked():
            channels = set()
            for n, enable in enumerate(self._chan_enables):
                if enable.isChecked():
                    channels.add(n)

            lvol = self._lvol.state
            rvol = self._rvol.state
            fbvol = self._fbvol.state
            delay = self._delay.value()
            fir_filt = 0 if self._filter[0].isChecked() else 1

            rv = EchoConfig(
                channels,
                (lvol[0] / 100, rvol[0] / 100),
                (lvol[1], rvol[1]),
                delay,
                fbvol[0] / 100,
                fbvol[1],
                fir_filt,
            )

        return rv

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _attach_signals(self) -> None:
        self._delay.valueChanged.connect(self._update_delay_display)
        self._enable.stateChanged.connect(self._update_enables)

    ###########################################################################

    @debug()
    def _do_layout(self) -> None:
        # Enable check boxes
        enable_widget = QWidget()
        grid_layout = QGridLayout()

        grid_layout.addWidget(self._enable, 0, 0, 1, 2)
        grid_layout.addWidget(QLabel("Channel Enables"), 1, 0, 1, 2)

        for n, enable in enumerate(self._chan_enables):
            grid_layout.addWidget(enable, 2 + n // 2, n % 2)

        row = 3 + len(self._chan_enables) // 2
        grid_layout.addWidget(QLabel("Filter"), row, 0, 1, 2)
        grid_layout.addWidget(self._filter[0], row + 1, 0)
        grid_layout.addWidget(self._filter[1], row + 1, 1)

        enable_widget.setLayout(grid_layout)

        # Delay group
        layout: QBoxLayout = QVBoxLayout()

        layout.addWidget(QLabel("Delay"))
        layout.addWidget(self._delay)
        layout.addWidget(self._delay_display)

        self._delay_panel.setLayout(layout)

        # Panel
        layout = QHBoxLayout()

        layout.addWidget(enable_widget)
        layout.addWidget(self._lvol)
        layout.addWidget(self._rvol)
        layout.addWidget(self._fbvol)
        layout.addWidget(self._delay_panel)

        self.setLayout(layout)

    ###########################################################################

    @debug()
    def _update_delay_display(self, val: int) -> None:
        self._delay_display.setText(f"{16*val}ms")

    ###########################################################################

    @debug()
    def _update_enables(self, enable: bool | int) -> None:
        enable = bool(enable)
        widgets: list[QWidget] = list(self._chan_enables)
        widgets.extend(
            [self._lvol, self._rvol, self._fbvol, self._delay_panel]
        )
        widgets.extend(self._filter)

        for widget in widgets:
            widget.setEnabled(enable)


###############################################################################


class SamplePanel(QWidget):
    _file: FilePicker
    _attack: QSlider
    _delay: QSlider
    _sustain: QSlider
    _release: QSlider
    _gain: QSlider
    _tune: QSlider
    _smw_sample: QComboBox
    _subtune: QSlider
    _parameters: QLabel

    ###########################################################################

    @debug()
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._file = FilePicker("brr", False, "BRR Sample File", "*.brr", self)
        self._attack = QSlider(Qt.Orientation.Vertical)
        self._decay = QSlider(Qt.Orientation.Vertical)
        self._sustain = QSlider(Qt.Orientation.Vertical)
        self._release = QSlider(Qt.Orientation.Vertical)
        self._gain = QSlider(Qt.Orientation.Vertical)
        self._tune = QSlider(Qt.Orientation.Vertical)
        self._subtune = QSlider(Qt.Orientation.Vertical)
        self._parameters = QLabel()
        self._smw_sample = QComboBox()

        self._attach_signals()

        self._attack.setRange(0, 15)
        self._decay.setRange(0, 7)
        self._sustain.setRange(0, 7)
        self._release.setRange(0, 31)
        self._gain.setRange(0, 127)
        self._tune.setRange(0, 255)
        self._subtune.setRange(0, 255)

        self._populate_smw_samples()

        self.update_ui()

        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info(True)
    def update_ui(self) -> None:
        pass

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def config(self) -> None:
        pass

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _attach_signals(self) -> None:
        pass

    ###########################################################################

    @debug()
    def _do_layout(self) -> None:
        # Enable check boxes
        grid_layout = QGridLayout()

        col = 0
        grid_layout.addWidget(self._smw_sample, 0, col)
        grid_layout.addWidget(self._file, 1, col)

        col = 1
        grid_layout.addWidget(QLabel("Attack"), 0, col)
        grid_layout.addWidget(self._attack, 1, col, 1, 2)

        col = 2
        grid_layout.addWidget(QLabel("Decay"), 0, col)
        grid_layout.addWidget(self._decay, 1, col, 1, 2)

        col = 3
        grid_layout.addWidget(QLabel("Sustain"), 0, col)
        grid_layout.addWidget(self._sustain, 1, col, 1, 2)

        col = 4
        grid_layout.addWidget(QLabel("Release"), 0, col)
        grid_layout.addWidget(self._release, 1, col, 1, 2)

        col = 5
        grid_layout.addWidget(QLabel("Gain"), 0, col)
        grid_layout.addWidget(self._gain, 1, col, 1, 2)

        col = 6
        grid_layout.addWidget(QLabel("Tune"), 0, col)
        grid_layout.addWidget(self._tune, 1, col, 1, 2)

        col = 7
        grid_layout.addWidget(QLabel("Sub-tune"), 0, col)
        grid_layout.addWidget(self._subtune, 1, col, 1, 2)

        grid_layout.addWidget(self._parameters, 2, 0, 1, 2)

        self.setLayout(grid_layout)

    ###########################################################################

    @debug()
    def _populate_smw_samples(self) -> None:
        # Names taken from Wakana's tutorial
        self._smw_sample.addItem(" 0: Flute")
        self._smw_sample.addItem(" 1: String")
        self._smw_sample.addItem(" 2: Bling/Glockenspiel")
        self._smw_sample.addItem(" 3: Marimba")
        self._smw_sample.addItem(" 4: Cello")
        self._smw_sample.addItem(" 5: Acoustic steel guitar")
        self._smw_sample.addItem(" 6: Trumpet")
        self._smw_sample.addItem(" 7: Steel drums")
        self._smw_sample.addItem(" 8: Acoustic bass")
        self._smw_sample.addItem(" 9: Piano")
        self._smw_sample.addItem("10: Snare drum")
        self._smw_sample.addItem("11: String 2")
        self._smw_sample.addItem("12: Bongo")
        self._smw_sample.addItem("13: Electric piano")
        self._smw_sample.addItem("14: Slap bass")
        self._smw_sample.addItem("15: Orchestra hit")
        self._smw_sample.addItem("16: Harp")
        self._smw_sample.addItem("17: Distortion guitar")
        self._smw_sample.addItem("21: Bass drum")
        self._smw_sample.addItem("22: Light cymbal")
        self._smw_sample.addItem("23: Maracas")
        self._smw_sample.addItem("24: Wood block")
        self._smw_sample.addItem("25: Higher wood block")
        self._smw_sample.addItem("28: Generic drums")
        self._smw_sample.addItem("29: Power set")
