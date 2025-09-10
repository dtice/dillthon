from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

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

class _BarVisualizer(QtWidgets.QWidget):
    """Custom widget for a stacked bar visualization"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding
        )
        self.visualizer_state = VisualizerState()


    def sizeHint(self):
        return QtCore.QSize(40, 120)

    def paintEvent(self, a0):
        painter = QtGui.QPainter(self)
        brush = QtGui.QBrush()
        brush.setColor(QtGui.QColor('black'))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        rect = QtCore.QRect(0, 0, painter.device().width(), painter.device().height())
        painter.fillRect(rect, brush)

        # Placeholder state
        value = self.visualizer_state.value
        vmin = self.visualizer_state.vmin
        vmax = self.visualizer_state.vmax
        if vmax <= vmin:
            vmax = vmin + 1

        if value < vmin:
            value = vmin
        
        if value > vmax:
            value = vmax

        padding = 5
        d_height = painter.device().height() - (padding * 2)
        d_width = painter.device().width() - (padding * 2)
        step_size = d_height / 5
        bar_height = step_size * 0.6
        bar_spacer = step_size * 0.4 / 2
        pc = (value - vmin) / (vmax - vmin)
        n_steps_to_draw = int(pc * 5)
        brush.setColor(QtGui.QColor('red'))
        for n in range(n_steps_to_draw):
            rect = QtCore.QRect(
                padding,
                int(padding + d_height - ((n+1) * step_size) + bar_spacer),
                d_width,
                int(bar_height)
            )
            painter.fillRect(rect, brush)
        painter.end()

    def _trigger_refresh(self):
        self.update()

    def minimumSizeHint(self):
        return QtCore.QSize(40, 120)
    
class VisualizerControls(QtWidgets.QWidget):
    """Controls for adjusting the visualizer state."""
    def __init__(self, visualizer_state: VisualizerState, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visualizer_state = visualizer_state
        self._setup_layout()

    def _setup_layout(self):
        layout = QtWidgets.QFormLayout()
        
        self.value_slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.value_slider.setMinimum(0)
        self.value_slider.setMaximum(100)
        self.value_slider.valueChanged.connect(self._on_value_changed)
        layout.addRow("Value:", self.value_slider)

        self.setLayout(layout)

    def _on_value_changed(self, value):
        self.visualizer_state.value = value

class MainWindow(QtWidgets.QMainWindow):
    """Main application window for Dills Badass Thingy."""
    def __init__(self):
        super().__init__()
        self.file_path = None
        self.text = QtWidgets.QPlainTextEdit()
        self.setWindowTitle("Dills Badass Thingy")
        self._setup_palette()
        self._setup_visualizer()
        self._setup_layout()
        self._setup_menu()

    def _setup_visualizer(self):
        """Set up the visualizer state and connect it to the bar visualizer."""
        self.state = VisualizerState()
        self.bar = _BarVisualizer()
        self.bar.visualizer_state = self.state
        self.state.state_changed.connect(self.bar._trigger_refresh)

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
        """Set up main window layout with a splitter."""
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        layout = QtWidgets.QVBoxLayout(central_widget)
        splitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal)

        self.visControls = VisualizerControls(self.state)
        splitter.addWidget(self.bar)
        splitter.addWidget(self.visControls)

        layout.addWidget(splitter)

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
        """Open a file and load its contents into the text editor."""
        path = QtWidgets.QFileDialog.getOpenFileName(self, "Open")[0]
        if path:
            with open(path) as f:
                self.text.setPlainText(f.read())
            self.file_path = path

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    app.exec()
