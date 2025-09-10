from PyQt6 import QtCore, QtGui, QtWidgets, QtMultimedia
from PyQt6.QtCore import Qt
import numpy as np

class BaseVisualizer(QtWidgets.QWidget):
    """Base class for all visualizers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def update_visualization(self, samples):
        """Update the visualizer with new audio samples (to be implemented by subclasses)."""
        pass

class FlamesVisualizer(BaseVisualizer):
    """2D flames visualizer: vertical columns animated like flames based on FFT energy."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding
        )
        self.n_flames = 24
        self.flame_heights = np.zeros(self.n_flames)
        self.flame_flicker = np.random.uniform(0.2, 0.5, self.n_flames)
        self._running_max = 1.0
        self.samplerate = 44100
        self.flame_waves = np.random.uniform(0, 2 * np.pi, self.n_flames)
        self.phase = 0.0

    def sizeHint(self):
        return QtCore.QSize(500, 350)

    def update_visualization(self, samples):
        n_flames = self.n_flames
        n_fft = len(samples)
        min_freq = 40
        max_freq = 8000
        samplerate = getattr(self, 'samplerate', 44100)
        freqs = np.fft.rfftfreq(n_fft * 2 - 1, 1.0 / samplerate)
        band_edges = np.logspace(np.log10(min_freq), np.log10(max_freq), n_flames + 1)
        band_energies = []
        for i in range(n_flames):
            idx = np.where((freqs >= band_edges[i]) & (freqs < band_edges[i+1]))[0]
            idx = idx[idx < len(samples)]
            if len(idx) > 0:
                band_energy = np.mean(samples[idx])
            else:
                band_energy = 0
            band_energies.append(np.log10(band_energy + 1e-3))
        current_max = max(band_energies)
        self._running_max = max(self._running_max * 0.95, current_max)
        # Flicker base
        self.flame_flicker = 0.7 * self.flame_flicker + 0.3 * np.random.uniform(0.2, 0.5, n_flames)
        # FFT controls height
        for i in range(n_flames):
            norm = band_energies[i] / (self._running_max + 1e-6)
            # Height: base flicker + FFT, with some random wave
            wave = 0.15 * np.sin(self.phase + self.flame_waves[i] + i * 0.5)
            self.flame_heights[i] = np.clip(self.flame_flicker[i] + norm * 1.2 + wave, 0.05, 1.0)
        self.phase += 0.2
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        rect = self.rect()
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.fillRect(rect, QtGui.QColor('black'))
        h, w = rect.height(), rect.width()
        n_flames = self.n_flames
        flame_width = w / n_flames
        base_y = h - 10
        for i in range(n_flames):
            # Flame contour: wavy, organic
            height = self.flame_heights[i] * (h * 0.7)
            tip_x = int((i + 0.5) * flame_width + np.random.uniform(-flame_width * 0.2, flame_width * 0.2))
            tip_y = int(base_y - height)
            left_x = int(i * flame_width)
            right_x = int((i + 1) * flame_width)
            # Control points for curve
            ctrl1_x = int(left_x + flame_width * 0.3)
            ctrl1_y = int(base_y - height * np.random.uniform(0.3, 0.6))
            ctrl2_x = int(right_x - flame_width * 0.3)
            ctrl2_y = int(base_y - height * np.random.uniform(0.3, 0.6))
            path = QtGui.QPainterPath()
            path.moveTo(left_x, base_y)
            path.cubicTo(ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, tip_x, tip_y)
            path.lineTo(right_x, base_y)
            path.closeSubpath()
            # Color gradient: base red/orange, tip yellow/white
            grad = QtGui.QLinearGradient(left_x, base_y, tip_x, tip_y)
            grad.setColorAt(0.0, QtGui.QColor(180, 30, 10))
            grad.setColorAt(0.5, QtGui.QColor(255, 120, 10))
            grad.setColorAt(0.8, QtGui.QColor(255, 220, 80))
            grad.setColorAt(1.0, QtGui.QColor(255, 255, 220))
            painter.setBrush(QtGui.QBrush(grad))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.drawPath(path)
        # Optionally, add some glow at the base
        glow_rect = QtCore.QRect(0, base_y - 10, w, 20)
        glow_grad = QtGui.QLinearGradient(0, base_y, 0, base_y + 20)
        glow_grad.setColorAt(0.0, QtGui.QColor(255, 180, 60, 120))
        glow_grad.setColorAt(1.0, QtGui.QColor(0, 0, 0, 0))
        painter.setBrush(QtGui.QBrush(glow_grad))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawRect(glow_rect)
        painter.end()

class CircleVisualizer(BaseVisualizer):
    """Visualizer with FFT bars arranged radially around a central circle."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding
        )
        self.n_bars = 40
        self.bar_values = [0] * self.n_bars
        self._running_max = 1.0
        self.samplerate = 44100

    def sizeHint(self):
        return QtCore.QSize(400, 400)

    def update_visualization(self, samples):
        n_bars = self.n_bars
        n_fft = len(samples)
        min_freq = 20
        max_freq = 20000
        samplerate = getattr(self, 'samplerate', 44100)
        freqs = np.fft.rfftfreq(n_fft * 2 - 1, 1.0 / samplerate)
        band_edges = np.logspace(np.log10(min_freq), np.log10(max_freq), n_bars + 1)
        band_energies = []
        for i in range(n_bars):
            idx = np.where((freqs >= band_edges[i]) & (freqs < band_edges[i+1]))[0]
            idx = idx[idx < len(samples)]
            if len(idx) > 0:
                band_energy = np.mean(samples[idx])
            else:
                band_energy = 0
            band_energies.append(np.log10(band_energy + 1e-3))
        current_max = max(band_energies)
        self._running_max = max(self._running_max * 0.95, current_max)
        for i in range(n_bars):
            norm = band_energies[i] / (self._running_max + 1e-6)
            self.bar_values[i] = min(1.0, max(0.0, norm))
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        rect = self.rect()
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.fillRect(rect, QtGui.QColor('black'))

        # Circle parameters
        cx = rect.center().x()
        cy = rect.center().y()
        radius = min(rect.width(), rect.height()) // 4
        # Draw central circle
        painter.setBrush(QtGui.QColor(60, 60, 60))
        painter.setPen(QtGui.QColor(120, 120, 120))
        painter.drawEllipse(QtCore.QPoint(cx, cy), radius, radius)

        # Draw bars radially
        n_bars = self.n_bars
        bar_length = radius
        bar_width = max(2, int(np.pi * radius / n_bars // 2))
        for i, value in enumerate(self.bar_values):
            angle = 2 * np.pi * i / n_bars
            # Start/end points for each bar
            x0 = cx + int(np.cos(angle) * radius)
            y0 = cy + int(np.sin(angle) * radius)
            x1 = cx + int(np.cos(angle) * (radius + int(value * bar_length)))
            y1 = cy + int(np.sin(angle) * (radius + int(value * bar_length)))
            color = QtGui.QColor.fromHsv(int(240 - value * 240), 255, int(100 + value * 155))
            pen = QtGui.QPen(color, bar_width)
            painter.setPen(pen)
            painter.drawLine(x0, y0, x1, y1)
        painter.end()

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

class BarVisualizer(BaseVisualizer):
    """Custom widget for a stacked bar visualization."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding
        )
        self.visualizer_state = VisualizerState()
        self.bar_values = [0] * 10  # 10 frequency bands
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
    