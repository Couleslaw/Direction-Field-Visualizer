from PyQt6.QtWidgets import (
    QWidget,
    QDialog,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QApplication,
    QStyleFactory,
    QDialogButtonBox,
)


class StyleSettings:
    """Stores the style settings of an application."""

    def __init__(self) -> None:
        self.__style: str | None = None

    @property
    def style(self) -> str | None:
        return self.__style

    @style.setter
    def style(self, style: str):
        self.__style = style


class StyleWindow(QDialog):
    """A dialog window for changing the style of an application."""

    def __init__(self, settings: StyleSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.__settings = settings

        # set window title
        self.setWindowTitle("Change Style")
        layout = QVBoxLayout()

        # add label
        label = QLabel("Select a style:")
        layout.addWidget(label)

        # add combo box for choosing style
        self.style_combo_box = QComboBox()
        self.style_combo_box.addItems(QStyleFactory.keys())  # get all available styles
        if (style := self.__settings.style) is not None:
            self.style_combo_box.setCurrentText(style)
        self.style_combo_box.currentTextChanged.connect(self.apply_style)
        layout.addWidget(self.style_combo_box)

        # add OK button
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.accept)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def apply_style(self) -> None:
        """Sets the style selected in the combo box."""
        self.__settings.style = self.style_combo_box.currentText()
        QApplication.setStyle(QStyleFactory.create(self.__settings.style))
