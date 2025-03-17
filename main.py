import sys
import os
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow


def main():
    # magic for pyinstaller to find the icon
    icon_path = "assets/icon.ico"
    if getattr(sys, "frozen", False):
        icon_path = os.path.join(sys._MEIPASS, icon_path)

    # create the application
    app = QApplication(sys.argv)
    app.setApplicationName("Direction Field Visualizer")

    # custom ToolTip css
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
    main_win = MainWindow()
    main_win.setWindowIcon(QIcon(icon_path))
    main_win.show()

    # run the application
    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")


if __name__ == "__main__":
    main()
