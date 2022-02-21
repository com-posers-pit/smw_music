# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard Panels."""

###############################################################################
# Standard library imports
###############################################################################

from typing import cast, Optional, Union

###############################################################################
# Library imports
###############################################################################

from PyQt6.QtCore import pyqtSignal  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

###############################################################################
# Package imports
###############################################################################

from ..log import debug, info
from ..music_xml.echo import EchoConfig
from .widgets import ArticSlider, FilePicker, PanControl, PctSlider, VolSlider

###############################################################################
# API Class Definitions
###############################################################################


class ArticPanel(QWidget):
    artic_changed: pyqtSignal = pyqtSignal(
        str, int, arguments=["artic", "quant"]
    )
    pan_changed: pyqtSignal = pyqtSignal(
        bool, int, arguments=["enable", "pan"]
    )
    _sliders: dict[str, ArticSlider]
    _pan: PanControl

    ###########################################################################

    @debug()
    def __init__(self, parent: QWidget = None) -> None:
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
    def update(self, artics: dict[str, int]) -> None:
        for artic, val in artics.items():
            self._sliders[artic].update(val)

    ###########################################################################

    @info()
    def update_pan(self, pan: Optional[int]) -> None:
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
    config_changed = pyqtSignal(
        [bool, bool, bool, bool, bool, bool],
        arguments=[
            "global_legato",
            "loop_analysis",
            "superloop_analysis",
            "measure_numbers",
            "custom_samples",
            "custom_percussion",
        ],
    )
    mml_requested = pyqtSignal(str, arguments=["fname"])
    song_changed = pyqtSignal(str, arguments=["fname"])

    _musicxml_picker: FilePicker
    _mml_picker: FilePicker
    _generate: QPushButton
    _global_legato: QCheckBox
    _loop_analysis: QCheckBox
    _superloop_analysis: QCheckBox
    _measure_numbers: QCheckBox
    _custom_samples: QCheckBox
    _custom_percussion: QCheckBox

    ###########################################################################

    @debug()
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._musicxml_picker = FilePicker(
            "MusicXML",
            False,
            "Input MusicXML File",
            "MusicXML (*.mxl *.musicxml);;Any (*)",
            self,
        )
        self._mml_picker = FilePicker("MML", True, "Output MML File", "", self)
        self._generate = QPushButton("Generate MML")
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
        layout.addWidget(self._generate)
        # layout.addWidget(QPushButton("Convert"))
        # layout.addWidget(QPushButton("Playback"))

        self.setLayout(layout)

    ###########################################################################

    @debug()
    def _generate_mml(self, _: bool) -> None:
        fname = self._mml_picker.fname
        if not fname:
            QMessageBox.critical(self, "", "Please pick an MML output file")
        else:
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
    volume_changed: pyqtSignal = pyqtSignal(
        str, int, bool, arguments=["dynamics", "vol", "interp"]
    )
    _sliders: dict[str, VolSlider]
    _interpolate: QCheckBox

    ###########################################################################

    @debug()
    def __init__(self, parent: QWidget = None) -> None:
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

        self._interpolate = QCheckBox(
            "Interpolate",
            toolTip="Adjust all dynamics settings based on the extreme values",
        )

        self._attach_signals()
        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info()
    def update(self, config: dict[str, int], present: set[str]) -> None:
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
    def __init__(self, parent: QWidget = None) -> None:
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
        self.update(None)

        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info(True)
    def update(self, config: Optional[EchoConfig]) -> None:
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
    def config(self) -> Optional[EchoConfig]:
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
        layout = QGridLayout()

        layout.addWidget(self._enable, 0, 0, 1, 2)
        layout.addWidget(QLabel("Channel Enables"), 1, 0, 1, 2)

        for n, enable in enumerate(self._chan_enables):
            layout.addWidget(enable, 2 + n // 2, n % 2)

        row = 3 + len(self._chan_enables) // 2
        layout.addWidget(QLabel("Filter"), row, 0, 1, 2)
        layout.addWidget(self._filter[0], row + 1, 0)
        layout.addWidget(self._filter[1], row + 1, 1)

        enable_widget.setLayout(layout)

        # Delay group
        layout = QVBoxLayout()

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
    def _update_enables(self, enable: Union[bool, int]) -> None:
        enable = bool(enable)
        widgets = (
            self._chan_enables
            + [
                self._lvol,
                self._rvol,
                self._fbvol,
                self._delay_panel,
            ]
            + list(self._filter)
        )

        for widget in widgets:
            widget.setEnabled(enable)
