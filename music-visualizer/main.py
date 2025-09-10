from PyQt6 import QtCore, QtGui, QtWidgets, QtMultimedia
from PyQt6.QtCore import Qt

import numpy as np
import soundfile as sf

class BaseVisualizer(QtWidgets.QWidget):
    """Base class for all visualizers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def update_visualization(self, samples):
        """Update the visualizer with new audio samples (to be implemented by subclasses)."""
        pass

class SpectrogramVisualizer(BaseVisualizer):
    """Static spectrogram visualizer (shows entire audio as a 2D heatmap)."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding
        )
        self.spectrogram = None
        self.samplerate = 44100
        self.n_bands = 40
        self.n_windows = 100
        self._running_max = 1.0

    def sizeHint(self):
        return QtCore.QSize(400, 200)

    def update_visualization(self, samples):
        # This method expects the full audio data, not just a single FFT window
        # For real-time, we can accumulate windows, but here we just show the latest
        # For demo, treat samples as a rolling buffer of shape (n_windows, window_size)
        # We'll use a waterfall-like approach for now
        if samples.ndim == 1:
            # If only one window, expand dims
            samples = samples[np.newaxis, :]
        n_windows = min(self.n_windows, samples.shape[0])
        n_fft = samples.shape[1]
        min_freq = 20
        max_freq = 20000
        samplerate = getattr(self, 'samplerate', 44100)
        freqs = np.fft.rfftfreq(n_fft * 2 - 1, 1.0 / samplerate)
        band_edges = np.logspace(np.log10(min_freq), np.log10(max_freq), self.n_bands + 1)
        spec = np.zeros((n_windows, self.n_bands))
        for t in range(n_windows):
            fft = np.abs(np.fft.rfft(samples[t]))
            prev_energy = 0
            for i in range(self.n_bands):
                idx = np.where((freqs >= band_edges[i]) & (freqs < band_edges[i+1]))[0]
                # Clamp indices to valid range
                idx = idx[idx < len(fft)]
                if len(idx) > 0:
                    band_energy = np.mean(fft[idx])
                    prev_energy = band_energy
                else:
                    band_energy = prev_energy
                spec[t, i] = np.log10(band_energy + 1e-3)
        # Normalize
        current_max = np.max(spec)
        self._running_max = max(self._running_max * 0.95, current_max)
        norm_spec = np.clip(spec / (self._running_max + 1e-6), 0.05, 1.0)
        self.spectrogram = norm_spec
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        rect = self.rect()
        painter.fillRect(rect, QtGui.QColor('black'))
        if self.spectrogram is None:
            painter.end()
            return
        h, w = rect.height(), rect.width()
        n_windows, n_bands = self.spectrogram.shape
        band_width = w / n_bands
        time_height = h / n_windows
        for t in range(n_windows):
            for b in range(n_bands):
                value = self.spectrogram[t, b]
                color = QtGui.QColor.fromHsv(int(240 - value * 240), 255, int(50 + value * 205))
                x = int(b * band_width)
                y = int(t * time_height)
                bw = int(band_width) if b < n_bands - 1 else w - int(b * band_width)
                th = int(time_height) if t < n_windows - 1 else h - int(t * time_height)
                painter.fillRect(x, y, bw, th, color)
        painter.end()

class VisualizerState(QtCore.QObject):
    """State object for the visualizer to manage its data and notify changes."""
    state_changed = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self._value = 0
        self._vmin = 0
        self._vmax = 100

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if new_value != self._value:
            self._value = new_value
            self.state_changed.emit()

    @property
    def vmin(self):
        return self._vmin

    @vmin.setter
    def vmin(self, new_vmin):
        if new_vmin != self._vmin:
            self._vmin = new_vmin
            self.state_changed.emit()

    @property
    def vmax(self):
        return self._vmax

    @vmax.setter
    def vmax(self, new_vmax):
        if new_vmax != self._vmax:
            self._vmax = new_vmax
            self.state_changed.emit()

class WaterfallVisualizer(BaseVisualizer):
    """Scrolling spectrogram (waterfall) visualizer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding
        )
        self.samplerate = 44100
        self.n_bands = 40
        self.history_length = 100  # number of time slices to show
        self.spectrogram = np.zeros((self.history_length, self.n_bands))
        self._running_max = 1.0

    def sizeHint(self):
        return QtCore.QSize(400, 200)

    def update_visualization(self, samples):
        # Logarithmic frequency bands
        n_fft = len(samples)
        min_freq = 20
        max_freq = 20000
        samplerate = getattr(self, 'samplerate', 44100)
        freqs = np.fft.rfftfreq(n_fft * 2 - 1, 1.0 / samplerate)
        band_edges = np.logspace(np.log10(min_freq), np.log10(max_freq), self.n_bands + 1)
        band_energies = []
        prev_energy = 0
        for i in range(self.n_bands):
            idx = np.where((freqs >= band_edges[i]) & (freqs < band_edges[i+1]))[0]
            # Clamp indices to valid range
            idx = idx[idx < len(samples)]
            if len(idx) > 0:
                band_energy = np.mean(samples[idx])
                prev_energy = band_energy
            else:
                # Interpolate: use previous energy if no bins in this band
                band_energy = prev_energy
            band_energies.append(np.log10(band_energy + 1e-3))
        # Running max for normalization
        current_max = max(band_energies)
        self._running_max = max(self._running_max * 0.95, current_max)
        # Minimum threshold for color mapping
        norm_bands = [min(1.0, max(0.05, b / (self._running_max + 1e-6))) for b in band_energies]
        # Scroll spectrogram up and add new row
        self.spectrogram = np.roll(self.spectrogram, -1, axis=0)
        self.spectrogram[-1, :] = norm_bands
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        rect = self.rect()
        painter.fillRect(rect, QtGui.QColor('black'))
        h, w = rect.height(), rect.width()
        n_bands = self.n_bands
        history_length = self.history_length
        band_width = w / n_bands
        time_height = h / history_length
        for t in range(history_length):
            for b in range(n_bands):
                value = self.spectrogram[t, b]
                color = QtGui.QColor.fromHsv(int(240 - value * 240), 255, int(50 + value * 205))
                x = int(b * band_width)
                y = int(t * time_height)
                bw = int(band_width) if b < n_bands - 1 else w - int(b * band_width)
                th = int(time_height) if t < history_length - 1 else h - int(t * time_height)
                painter.fillRect(x, y, bw, th, color)
        painter.end()

class _BarVisualizer(BaseVisualizer):
    """Custom widget for a stacked bar visualization."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding
        )
        self.visualizer_state = VisualizerState()
        self.bar_values = [0] * 96  # 10 frequency bands
        self._running_max = 1.0

    def sizeHint(self):
        return QtCore.QSize(40, 120)

    def paintEvent(self, a0):
        painter = QtGui.QPainter(self)
        brush = QtGui.QBrush()
        brush.setColor(QtGui.QColor('black'))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        rect = QtCore.QRect(0, 0, painter.device().width(), painter.device().height())
        painter.fillRect(rect, brush)

        # Draw 10 vertical bars
        padding = 10
        d_height = painter.device().height() - (padding * 2)
        d_width = painter.device().width() - (padding * 2)
        n_bars = len(self.bar_values)
        bar_width = d_width // n_bars
        max_bar_height = d_height
        for i, value in enumerate(self.bar_values):
            # value is normalized between 0 and 1
            bar_h = int(value * max_bar_height)
            x = padding + i * bar_width
            y = padding + (max_bar_height - bar_h)
            bar_rect = QtCore.QRect(x, y, bar_width - 2, bar_h)
            brush.setColor(QtGui.QColor('red'))
            painter.fillRect(bar_rect, brush)
        painter.end()

    def _trigger_refresh(self):
        self.update()

    def minimumSizeHint(self):
        return QtCore.QSize(40, 120)

    def update_visualization(self, samples):
        """Update the bar visualizer with FFT samples using logarithmic frequency bands."""
        n_bars = len(self.bar_values)
        n_fft = len(samples)
        # Logarithmic frequency bands
        min_freq = 20
        max_freq = 20000
        samplerate = getattr(self, 'samplerate', 44100)
        # Calculate frequency for each FFT bin
        freqs = np.fft.rfftfreq(n_fft * 2 - 1, 1.0 / samplerate)
        # Logarithmically spaced frequency edges
        band_edges = np.logspace(np.log10(min_freq), np.log10(max_freq), n_bars + 1)
        band_energies = []
        for i in range(n_bars):
            # Find FFT bins within this band
            idx = np.where((freqs >= band_edges[i]) & (freqs < band_edges[i+1]))[0]
            # Clamp indices to valid range
            idx = idx[idx < len(samples)]
            if len(idx) > 0:
                band_energy = np.mean(samples[idx])
            else:
                band_energy = 0
            band_energies.append(np.log10(band_energy + 1e-3))
        # Running max for normalization
        current_max = max(band_energies)
        self._running_max = max(self._running_max * 0.95, current_max)
        for i in range(n_bars):
            norm = band_energies[i] / (self._running_max + 1e-6)
            self.bar_values[i] = min(1.0, max(0.0, norm))
        self.update()
    
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
