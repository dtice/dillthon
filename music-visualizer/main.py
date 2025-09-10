from PyQt6 import QtCore, QtGui, QtWidgets, QtMultimedia
from PyQt6.QtCore import Qt
from visualizers import WaterfallVisualizer, SpectrogramVisualizer, _BarVisualizer, VisualizerState

import numpy as np
import soundfile as sf

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
        self.seek_slider.sliderMoved.connect(self._seek)
        layout.addWidget(self.seek_slider)

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

    def _seek(self, position):
        duration = self.player.duration()
        if duration > 0:
            self.player.setPosition(int(position / 100 * duration))

    def update_seek(self):
        duration = self.player.duration()
        if duration > 0:
            pos = self.player.position()
            self.seek_slider.setValue(int(pos / duration * 100))

class MainWindow(QtWidgets.QMainWindow):
    """Main application window for Dills Badass Thingy."""
    def __init__(self):
        super().__init__()
        self.file_path = None
        self.audio_data = None
        self.samplerate = None
        self.visualizer_type = 'waterfall'
        self.setWindowTitle("Dills Badass Thingy")
        self._setup_palette()
        self._setup_visualizer(self.visualizer_type)
        self._setup_player()
        self._setup_layout()
        self._setup_menu()
        self._setup_visualizer_timer()

    def _setup_visualizer(self, visualizer_type='waterfall'):
        """Set up the visualizer state and connect it to the chosen visualizer."""
        self.state = VisualizerState()
        if visualizer_type == 'waterfall':
            self.bar = WaterfallVisualizer()
        elif visualizer_type == 'spectrogram':
            self.bar = SpectrogramVisualizer()
        else:
            self.bar = _BarVisualizer()

    def _setup_player(self):
        """Set up the audio player and output device."""
        self.audio_output = QtMultimedia.QAudioOutput()
        self.player = QtMultimedia.QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)

    def _setup_palette(self):
        """Set up dark Fusion palette."""
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(53, 53, 53))
        palette.setColor(QtGui.QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(25, 25, 25))
        palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(53, 53, 53))
        palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QtGui.QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(53, 53, 53))
        palette.setColor(QtGui.QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QtGui.QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QtGui.QPalette.ColorRole.Link, QtGui.QColor(42, 130, 218))
        palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(42, 130, 218))
        palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        QtWidgets.QApplication.instance().setPalette(palette)

    def _setup_layout(self):
        """Set up main window layout with stacked visualizer, controls, and visualizer selector."""
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        layout = QtWidgets.QVBoxLayout(central_widget)

        # Visualizer selector dropdown
        self.vis_selector = QtWidgets.QComboBox()
        self.vis_selector.addItems(["Waterfall", "Spectrogram", "Bars"])
        self.vis_selector.setCurrentIndex(0)
        self.vis_selector.currentIndexChanged.connect(self._on_vis_type_changed)
        layout.addWidget(self.vis_selector)

        # Visualizer widget
        self.vis_container = QtWidgets.QWidget()
        self.vis_layout = QtWidgets.QVBoxLayout(self.vis_container)
        self.vis_layout.setContentsMargins(0, 0, 0, 0)
        self.vis_layout.addWidget(self.bar)
        layout.addWidget(self.vis_container)

        self.music_controls = MusicControls(self.player, self.audio_output, self.open_file)
        layout.addWidget(self.music_controls)

    def _on_vis_type_changed(self, idx):
        types = ['waterfall', 'spectrogram', 'bars']
        self.visualizer_type = types[idx]
        # Remove old visualizer
        old_bar = self.bar
        self.vis_layout.removeWidget(old_bar)
        old_bar.setParent(None)
        # Create new visualizer
        self._setup_visualizer(self.visualizer_type)
        self.vis_layout.addWidget(self.bar)
        # Pass samplerate if available
        if hasattr(self.bar, 'samplerate') and self.samplerate:
            self.bar.samplerate = self.samplerate

    def _setup_menu(self):
        """Set up menu bar and actions."""
        menu = self.menuBar().addMenu("&File")
        open_action = QtGui.QAction("&Open", self)
        open_action.triggered.connect(self.open_file)
        open_action.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        menu.addAction(open_action)

        close_action = QtGui.QAction("&Close", self)
        close_action.triggered.connect(self.close)
        menu.addAction(close_action)

    def open_file(self):
        """Open a sound file and load it into the player and for visualization."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Sound File", filter="Audio Files (*.mp3 *.wav *.ogg)")
        if path:
            self.player.setSource(QtCore.QUrl.fromLocalFile(path))
            self.file_path = path
            self.player.play()
            self.music_controls.play_button.setChecked(True)
            self.music_controls.play_button.setText("Pause")
            # Load audio data for visualization
            try:
                data, samplerate = sf.read(path)
                if len(data.shape) > 1:
                    data = data.mean(axis=1)  # Convert to mono
                self.audio_data = data
                self.samplerate = samplerate
            except Exception as e:
                print(f"Error loading audio for visualization: {e}")

    def _on_position_changed(self, position):
        self.music_controls.update_seek()
        # Visualization update handled by timer

    def _setup_visualizer_timer(self):
        self.vis_timer = QtCore.QTimer(self)
        self.vis_timer.timeout.connect(self._update_visualizer)
        self.vis_timer.start(50)  # update every 50ms

    def _update_visualizer(self):
        if self.audio_data is not None and self.player.playbackState() == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState:
            # Get current playback position in samples
            pos_ms = self.player.position()
            pos_samples = int((pos_ms / 1000.0) * self.samplerate)
            window_size = 2048
            start = max(0, pos_samples - window_size // 2)
            end = min(len(self.audio_data), start + window_size)
            samples = self.audio_data[start:end]
            if len(samples) < window_size:
                samples = np.pad(samples, (0, window_size - len(samples)))
            # FFT
            fft = np.abs(np.fft.rfft(samples))
            # Pass samplerate to visualizer for correct frequency mapping
            if hasattr(self.bar, 'update_visualization'):
                self.bar.samplerate = self.samplerate
                self.bar.update_visualization(fft)

    def _on_duration_changed(self, duration):
        self.music_controls.seek_slider.setMaximum(100)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    window.raise_()
    app.exec()
