import sys
import os

from PyQt6.QtWidgets import QPushButton, QWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt


class StopButton(QPushButton):
    """A red button that disappears when clicked."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        icon_path = "assets/graphics/stop_red.png"
        if getattr(sys, "frozen", False):
            icon_path = os.path.join(sys._MEIPASS, icon_path)

        self.setIcon(QIcon(icon_path))
        self.setFixedSize(50, 50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self.on_clicked)
        self.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 255, 255, 0);
                padding: 0px;
                margin: 5px;
                icon-size: 30px;
            }
            """
        )

    def on_clicked(self) -> None:
        """Hides the button."""
        self.setVisible(False)
