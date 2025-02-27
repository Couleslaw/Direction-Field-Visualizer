import sys
import os

from typing import override, TypeAlias

from PyQt6.QtWidgets import QPushButton, QWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt


class LockState:
    """Class to represent the state of the lock button."""

    Locked = 0
    Unlocked = 1


lock_state: TypeAlias = int


class LockButton(QPushButton):
    """A button that represents a two state lock."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # paths to icons
        unlocked_icon_path = "assets/graphics/lock_open.png"
        locked_icon_path = "assets/graphics/lock_closed.png"
        if getattr(sys, "frozen", False):
            unlocked_icon_path = os.path.join(sys._MEIPASS, unlocked_icon_path)
            locked_icon_path = os.path.join(sys._MEIPASS, locked_icon_path)

        # set icons
        self.unlocked_icon = QIcon(unlocked_icon_path)
        self.locked_icon = QIcon(locked_icon_path)

        # set tool tips
        self.shortcut_str = ""
        self.locked_tooltip = "Unlock canvas to allow movement"
        self.unlocked_tooltip = "Lock canvas to prevent accidental movement"

        # set style
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

    @override
    def setShortcut(self, key) -> None:
        """Set the shortcut key for the button."""
        super().setShortcut(key)
        # make the shortcut visible in the tooltip
        self.shortcut_str = f"\n{key}"

    def setState(self, state: lock_state) -> None:
        """Lock or unlock the button."""
        assert state in [LockState.Locked, LockState.Unlocked]
        self.state = state
        if state == LockState.Locked:
            self.setIcon(self.locked_icon)
            self.setToolTip(self.locked_tooltip + self.shortcut_str)
        else:
            self.setIcon(self.unlocked_icon)
            self.setToolTip(self.unlocked_tooltip + self.shortcut_str)

    def on_clicked(self) -> None:
        """Changes the state of the button."""
        if self.state == LockState.Locked:
            self.setState(LockState.Unlocked)
        else:
            self.setState(LockState.Locked)
