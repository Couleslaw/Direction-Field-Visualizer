from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from src.gui.visualizer_app import VisualizerApp
from src.gui.app_style import StyleWindow, StyleSettings


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Direction Field Visualizer")

        self.app = VisualizerApp()
        self.setCentralWidget(self.app)
        self.setMinimumSize(928, 580)
        self.resize(1024, 640)

        self.style_settings = StyleSettings()

    def closeEvent(self, event):
        """Closes the application."""

        reply = QMessageBox.question(
            self,
            "Message",
            "Are you sure you want to quit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.app.stop_background_threads()
            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, event):
        """Opens the user guide on F1 press."""
        if event.key() == Qt.Key.Key_F1:
            self.open_user_guide()

        if event.key() == Qt.Key.Key_F2:
            self.open_style_window()

    def open_user_guide(self):
        """Opens the user guide in the default browser."""
        QDesktopServices.openUrl(
            QUrl("https://github.com/Couleslaw/Direction-Field-Visualizer/wiki/User-Guide")
        )

    def open_style_window(self):
        """Opens the style window."""
        style_window = StyleWindow(self.style_settings, self)
        style_window.exec()
