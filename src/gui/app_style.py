from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QApplication,
    QStyleFactory,
    QDialogButtonBox,
)


class StyleSettings:
    def __init__(self):
        self.style = None

    def get_style(self):
        return self.style

    def set_style(self, style):
        self.style = style


class StyleWindow(QDialog):
    def __init__(self, settings: StyleSettings, parent=None):
        super().__init__(parent)

        self.settings = settings

        self.setWindowTitle("Change Style")
        layout = QVBoxLayout()

        label = QLabel("Select a style:")
        layout.addWidget(label)

        self.style_combo = QComboBox()
        self.style_combo.addItems(QStyleFactory.keys())
        if self.settings.get_style():
            self.style_combo.setCurrentText(self.settings.get_style())
        self.style_combo.currentTextChanged.connect(self.apply_style)
        layout.addWidget(self.style_combo)

        # add OK button
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.accept)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def apply_style(self):
        selected_style = self.style_combo.currentText()
        self.settings.set_style(selected_style)
        QApplication.setStyle(QStyleFactory.create(selected_style))
