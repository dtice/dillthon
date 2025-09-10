from PyQt6 import QtWidgets, QtMultimedia
from PyQt6.QtCore import Qt

class MusicControls(QtWidgets.QWidget):
    """Music player controls: play/pause, seek bar, file select, output device select."""
    def __init__(self, player: 'QtMultimedia.QMediaPlayer', audio_output: 'QtMultimedia.QAudioOutput', open_file_callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player = player
        self.audio_output = audio_output
        self.open_file_callback = open_file_callback
        self._setup_layout()

    def _setup_layout(self):
        layout = QtWidgets.QHBoxLayout()

        self.open_button = QtWidgets.QPushButton("Open File")
        self.open_button.clicked.connect(self.open_file_callback)
        layout.addWidget(self.open_button)

        self.play_button = QtWidgets.QPushButton("Play")
        self.play_button.setCheckable(True)
        self.play_button.clicked.connect(self._toggle_play)
        layout.addWidget(self.play_button)

        self.seek_slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setMinimum(0)
        self.seek_slider.setMaximum(100)
        self.seek_slider.sliderMoved.connect(self._on_slider_moved)
        self.seek_slider.sliderPressed.connect(self._on_slider_pressed)
        self.seek_slider.sliderReleased.connect(self._on_slider_released)
        layout.addWidget(self.seek_slider)
        self._is_seeking = False


        self.device_combo = QtWidgets.QComboBox()
        self.device_combo.setMinimumWidth(150)
        self._populate_devices()
        self.device_combo.currentIndexChanged.connect(self._change_device)
        layout.addWidget(self.device_combo)

        self.setLayout(layout)

    def _populate_devices(self):
        self.device_combo.clear()
        self.devices = QtMultimedia.QMediaDevices.audioOutputs()
        for device in self.devices:
            self.device_combo.addItem(device.description())
        # Set current device to default
        default_device = QtMultimedia.QMediaDevices.defaultAudioOutput()
        for i, device in enumerate(self.devices):
            if device == default_device:
                self.device_combo.setCurrentIndex(i)
                self.audio_output.setDevice(device)
                break

    def _change_device(self, idx):
        if 0 <= idx < len(self.devices):
            self.audio_output.setDevice(self.devices[idx])

    def _toggle_play(self):
        if self.play_button.isChecked():
            self.player.play()
            self.play_button.setText("Pause")
        else:
            self.player.pause()
            self.play_button.setText("Play")

    def _on_slider_pressed(self):
        self._is_seeking = True

    def _on_slider_moved(self, position):
        # Optionally, update UI or show preview, but do not seek yet
        pass

    def _on_slider_released(self):
        position = self.seek_slider.value()
        duration = self.player.duration()
        if duration > 0:
            self.player.setPosition(int(position / 100 * duration))
        self._is_seeking = False

    def update_seek(self):
        if self._is_seeking:
            return
        duration = self.player.duration()
        if duration > 0:
            pos = self.player.position()
            self.seek_slider.setValue(int(pos / duration * 100))
