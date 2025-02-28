from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QSlider,
    QLineEdit,
)

from typing import Tuple, Callable, Any


class QtComponentBuilder:
    @staticmethod
    def add_slider_with_label(
        min_value: int,
        max_value: int,
        default_value: int,
        label_text: str,
        on_value_changed: Callable[[], Any],
        layout: QVBoxLayout | QHBoxLayout | None = None,
        tooltip: str = "",
        tick_interval: int = 1,
        single_step: int = 1,
        min_width: int = 150,
        slider_min_height: int = 10,
        label_min_height: int = 15,
    ) -> Tuple[QSlider, QLabel]:
        """Creates a slider with a label above it. If a layout is provided, the slider and label will be added to it embedded in a QVBoxLayout."""

        # Create the slider
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimumSize(min_width, slider_min_height)
        slider.setRange(min_value, max_value)
        slider.setValue(default_value)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setTickInterval(tick_interval)
        slider.setSingleStep(single_step)
        slider.valueChanged.connect(on_value_changed)

        # Create the label
        label = QLabel("  " + label_text)
        label.setToolTip(tooltip)
        label.setMinimumHeight(label_min_height)
        label.setBuddy(slider)

        if layout is None:
            return slider, label

        # Add the slider and label to the layout
        form = QVBoxLayout()
        form.addWidget(label)
        form.addWidget(slider)
        layout.addLayout(form)

        return slider, label

    @staticmethod
    def add_line_edit_with_label(
        default_text: str,
        label_text: str,
        on_text_changed: Callable[[], Any],
        tooltip: str = "",
        layout: QVBoxLayout | QHBoxLayout | None = None,
        line_edit_min_width: int = 10,
    ) -> Tuple[QLineEdit, QLabel]:
        """Creates a line edit with a label above it. If a layout is provided, the line edit and label will be added to it embedded in a form layout."""

        # Create the line edit
        line_edit = QLineEdit(default_text)
        line_edit.setMinimumWidth(line_edit_min_width)
        line_edit.textChanged.connect(on_text_changed)

        # Create the label
        label = QLabel(label_text)
        label.setToolTip(tooltip)
        label.setBuddy(line_edit)

        if layout is None:
            return line_edit, label

        # Add the line edit and label to the layout
        form = QFormLayout()
        form.addRow(label, line_edit)
        layout.addLayout(form)

        return line_edit, label
