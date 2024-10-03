import sys
import os
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
)

from src.gui.visualizer_app import VisualizerApp


def main():
    # magic for pyinstaller to find the icon
    if getattr(sys, "frozen", False):
        icon = os.path.join(sys._MEIPASS, "src/icon.ico")
    else:
        icon = "src/icon.ico"

    # create the application
    app = QApplication(sys.argv)
    app.setApplicationName("Direction Field Visualizer")
    app.setStyleSheet(
        """
            QToolTip {
                background-color: #f0f0f0;
                color: black;
                border: 2px solid black;
                padding: 4px;
            }
        """
    )

    # create the main window
    myApp = VisualizerApp()
    main_win = QMainWindow()
    main_win.setCentralWidget(myApp)
    main_win.setWindowIcon(QIcon(icon))
    main_win.show()

    # run the application
    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")


if __name__ == "__main__":
    main()
