from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt


class StopButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon("assets/graphics/stop_red.png"))
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

    def on_clicked(self):
        self.setVisible(False)
