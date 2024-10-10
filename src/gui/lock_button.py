from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt


class LockState:
    Locked = 0
    Unlocked = 1


class LockButton(QPushButton):

    def __init__(self, parent=None):
        super().__init__(parent)

        # icons
        self.unlocked_icon = QIcon("assets/graphics/lock_open.png")
        self.locked_icon = QIcon("assets/graphics/lock_closed.png")

        # tool tip
        self.shortcut_str = ""
        self.locked_tooltip = "Unlock canvas to allow movement"
        self.unlocked_tooltip = "Lock canvas to prevent accidental movement"

        self.setFixedSize(50, 50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self.on_clicked)
        self.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 255, 255, 0);
                padding: 0px;
                margin: 5px;
                border: 2px solid black;
                border-radius: 10px;
                icon-size: 30px;
            }
            """
        )

    def setShortcut(self, key):
        super().setShortcut(key)
        # make the shortcut visible in the tooltip
        self.shortcut_str = f"\n{key}"
        self.setState(self.state)

    def setState(self, state):
        """Lock or unlock the lock."""
        assert state in [LockState.Locked, LockState.Unlocked]
        self.state = state
        if state == LockState.Locked:
            self.setIcon(self.locked_icon)
            self.setToolTip(self.locked_tooltip + self.shortcut_str)
        else:
            self.setIcon(self.unlocked_icon)
            self.setToolTip(self.unlocked_tooltip + self.shortcut_str)

    def on_clicked(self):
        if self.state == LockState.Locked:
            self.setState(LockState.Unlocked)
        else:
            self.setState(LockState.Locked)
