from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

class _BarVisualizer(QtWidgets.QWidget):
    """Custom widget for a stacked bar visualization"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding
        )

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
        vmin, vmax = 1, 10
        value = 5
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

class MainWindow(QtWidgets.QMainWindow):
    """Main application window for Dills Badass Thingy."""
    def __init__(self):
        super().__init__()
        self.file_path = None
        self.text = QtWidgets.QPlainTextEdit()
        self.setWindowTitle("Dills Badass Thingy")
        self._setup_palette()
        self._setup_layout()
        self._setup_menu()

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
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(_BarVisualizer())
        left_widget = QtWidgets.QWidget()
        left_widget.setLayout(left_layout)

        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(self.text)
        right_widget = QtWidgets.QWidget()
        right_widget.setLayout(right_layout)

        splitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        self.setCentralWidget(splitter)

    def _setup_menu(self):
        """Set up menu bar and actions."""
        menu = self.menuBar().addMenu("&File")
        open_action = QtGui.QAction("&Open", self)
        open_action.triggered.connect(self.open_file)
        open_action.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        menu.addAction(open_action)

        save_action = QtGui.QAction("&Save", self)
        save_action.triggered.connect(self.save)
        save_action.setShortcut(QtGui.QKeySequence.StandardKey.Save)
        menu.addAction(save_action)

        save_as_action = QtGui.QAction("Save &As...", self)
        save_as_action.triggered.connect(self.save_as)
        menu.addAction(save_as_action)

        close_action = QtGui.QAction("&Close", self)
        close_action.triggered.connect(self.close)
        menu.addAction(close_action)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QtGui.QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def open_file(self):
        """Open a file and load its contents into the text editor."""
        path = QtWidgets.QFileDialog.getOpenFileName(self, "Open")[0]
        if path:
            with open(path) as f:
                self.text.setPlainText(f.read())
            self.file_path = path

    def save(self):
        """Save the contents of the text editor to file."""
        if self.file_path is None:
            self.save_as()
        else:
            with open(self.file_path, "w") as f:
                f.write(self.text.toPlainText())
            self.text.document().setModified(False)

    def save_as(self):
        """Save the contents to a new file."""
        path = QtWidgets.QFileDialog.getSaveFileName(self, "Save As")[0]
        if path:
            self.file_path = path
            self.save()

    def show_about_dialog(self):
        """Show the About dialog."""
        text = (
            "<center>"
            "<h1>Text Editor</h1>"
            "&#8291;"
            "<img src=icon.svg>"
            "</center>"
            "<p>Version 31.4.159.265358<br/>"
            "Copyright &copy; Company Inc.</p>"
        )
        QtWidgets.QMessageBox.about(self, "About Text Editor", text)

    def closeEvent(self, a0):
        """Prompt to save if there are unsaved changes."""
        if not self.text.document().isModified():
            return
        answer = QtWidgets.QMessageBox.question(
            self, None,
            "You have unsaved changes. Save before closing?",
            QtWidgets.QMessageBox.StandardButton.Save |
            QtWidgets.QMessageBox.StandardButton.Discard |
            QtWidgets.QMessageBox.StandardButton.Cancel
        )
        if answer & QtWidgets.QMessageBox.StandardButton.Save:
            self.save()
        elif answer & QtWidgets.QMessageBox.StandardButton.Cancel:
            a0.ignore()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    app.exec()
