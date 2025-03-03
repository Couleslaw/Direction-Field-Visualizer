from __future__ import annotations

import sys
import os

from PyQt6.QtWidgets import QPushButton, QWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from typing import override
from enum import Enum


class LockButton(QPushButton):
    """A button that represents a two state lock."""

    class LockState(Enum):
        """Class to represent the state of the lock button."""

        LOCKED = 0
        UNLOCKED = 1

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # paths to icons
        unlocked_icon_path = "assets/graphics/lock_open.png"
        locked_icon_path = "assets/graphics/lock_closed.png"
        if getattr(sys, "frozen", False):
            unlocked_icon_path = os.path.join(sys._MEIPASS, unlocked_icon_path)
            locked_icon_path = os.path.join(sys._MEIPASS, locked_icon_path)

        # set icons
        self.__unlocked_icon = QIcon(unlocked_icon_path)
        self.__locked_icon = QIcon(locked_icon_path)

        # set tool tips
        self.__shortcut_str = ""
        self.__locked_tooltip = "Unlock canvas to allow movement"
        self.__unlocked_tooltip = "Lock canvas to prevent accidental movement"

        # set style
        self.setFixedSize(50, 50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self.__on_clicked)
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
        self.__shortcut_str = f"\n{key}"

    def setState(self, state: LockState) -> None:
        """Lock or unlock the button."""
        assert state in [self.LockState.LOCKED, self.LockState.UNLOCKED]
        self.state = state
        if state == self.LockState.LOCKED:
            self.setIcon(self.__locked_icon)
            self.setToolTip(self.__locked_tooltip + self.__shortcut_str)
        else:
            self.setIcon(self.__unlocked_icon)
            self.setToolTip(self.__unlocked_tooltip + self.__shortcut_str)

    def __on_clicked(self) -> None:
        """Changes the state of the button."""
        if self.state == self.LockState.LOCKED:
            self.setState(self.LockState.UNLOCKED)
        else:
            self.setState(self.LockState.LOCKED)
