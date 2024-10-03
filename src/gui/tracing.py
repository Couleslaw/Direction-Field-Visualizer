from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QSlider,
    QLineEdit,
    QMessageBox,
    QSizePolicy,
    QDialog,
    QDialogButtonBox,
    QColorDialog,
    QGroupBox,
    QRadioButton,
)

from src.numerical_methods import TraceSettings
from src.default_constants import *


class CoordinateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Input Coordinates")

        # Layout for dialog window
        layout = QVBoxLayout()

        # X coordinate input
        self.x_label = QLabel("Enter X coordinate:")
        self.x_input = QLineEdit(self)
        layout.addWidget(self.x_label)
        layout.addWidget(self.x_input)

        # Y coordinate input
        self.y_label = QLabel("Enter Y coordinate:")
        self.y_input = QLineEdit(self)
        layout.addWidget(self.y_label)
        layout.addWidget(self.y_input)

        # OK and Cancel buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_coordinates(self):
        """Return the X and Y coordinates as a tuple"""
        x = self.x_input.text()
        y = self.y_input.text()
        return x, y


class TraceSettingsDialog(QDialog):
    def __init__(self, parent, trace_settings: TraceSettings, slope_function: str, xlim, ylim):
        super().__init__(parent)

        self.setWindowTitle("Trace Settings")
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.setFixedWidth(250)
        self.settings = trace_settings
        self.slope_function_str = slope_function
        self.xlim = xlim
        self.ylim = ylim
        self.selected_color = QColor(self.settings.line_color)

        # Layout for dialog window
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Basic-settings section
        self.create_basic_settings(layout)

        # Show/Hide button for advanced settings
        self.toggle_button = QPushButton(
            "Hide advanced settings"
            if self.settings.show_advanced_settings
            else "Show advanced settings"
        )
        self.toggle_button.clicked.connect(self.toggle_advanced_settings)
        layout.addWidget(self.toggle_button)

        # Advanced settings
        self.create_advanced_settings(layout)

        # OK and Cancel buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def create_basic_settings(self, layout):
        """Creates the trace-line-width slider and color-picker button."""
        # create the 'trace line width' slider
        self.slider_w = QSlider(Qt.Orientation.Horizontal)
        self.slider_w.setMinimum(MIN_TRACE_LINES_WIDTH)
        self.slider_w.setMaximum(MAX_TRACE_LINES_WIDTH)
        self.slider_w.setValue(self.settings.line_width)
        self.slider_w.setMinimumWidth(150)
        self.slider_w.setTickInterval(1)
        self.slider_w.setSingleStep(1)
        self.slider_w.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_w.valueChanged.connect(self.changed_trace_lines_width)
        self.label_w = QLabel()
        self.label_w.setToolTip("Width of the trace lines.")
        self.label_w.setText(f"  &Trace line width: {self.settings.line_width}   ")
        self.label_w.setBuddy(self.slider_w)
        form = QVBoxLayout()
        form.addWidget(self.label_w)
        form.addWidget(self.slider_w)
        layout.addLayout(form)

        # Horizontal layout for color button and color box
        color_layout = QHBoxLayout()

        # Button to open color picker dialog
        self.color_button = QPushButton("Choose color", self)
        self.color_button.clicked.connect(self.open_color_dialog)
        color_layout.addWidget(self.color_button)

        # Color box (QLabel) to display the current color
        self.color_box = QLabel(self)
        self.color_box.setFixedSize(50, 20)  # Size of the color box
        self.update_color_box()  # Set initial color to red
        color_layout.addWidget(self.color_box)

        layout.addLayout(color_layout)

    def create_advanced_settings(self, layout):
        """Creates the advanced settings section.
        - trace precision slider
        - singularity detection radio buttons
            - automatic: Y offscreen margin, singularity slope
            - manual: singularity equation
        """

        # trace precision slider
        self.slider_p = QSlider(Qt.Orientation.Horizontal)
        self.slider_p.setMinimum(MIN_TRACE_PRECISION)
        self.slider_p.setMaximum(MAX_TRACE_PRECISION)
        self.slider_p.setValue(self.settings.trace_precision)
        self.slider_p.setMinimumWidth(150)
        self.slider_p.setTickInterval(1)
        self.slider_p.setSingleStep(1)
        self.slider_p.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_p.valueChanged.connect(self.changed_trace_precision)
        self.slider_p.setVisible(self.settings.show_advanced_settings)
        self.label_p = QLabel()
        self.label_p.setToolTip(
            """Trace precision directly affects the size of the dx step used 
to trace the solution curve. Higher precision means exponentially
smaller dx and exponentially higher calculation time. It is preferred
to use equational singularity detection over increasing precision.
Increase precision only if a singularity is not detected correctly.
"""
        )
        self.label_p.setText(f"  &Trace precision: {self.settings.trace_precision}   ")
        self.label_p.setBuddy(self.slider_p)
        self.label_p.setVisible(self.settings.show_advanced_settings)
        layout.addWidget(self.label_p)
        layout.addWidget(self.slider_p)

        # Singularity detection settings
        self.singularity_strategy_group_box = QGroupBox("Singularity detection strategy")
        singularity_layout = QVBoxLayout()
        self.singularity_strategy_group_box.setLayout(singularity_layout)
        self.singularity_strategy_group_box.setVisible(self.settings.show_advanced_settings)
        layout.addWidget(self.singularity_strategy_group_box)

        # Create singularity detection strategy radio buttons
        self.radio_automatic_settings = QRadioButton("Automatic")
        self.radio_manual_settings = QRadioButton("Equational")

        # Create settings layout
        automatic_settings_layout = QVBoxLayout()
        self.create_automatic_settings(automatic_settings_layout)

        manual_detection_layout = QVBoxLayout()
        self.create_manual_detection_settings(manual_detection_layout)

        # Wrap the settings layouts in QWidget objects for hiding/showing
        self.automatic_settings_widget = QWidget()
        self.automatic_settings_widget.setLayout(automatic_settings_layout)

        self.manual_detection_widget = QWidget()
        self.manual_detection_widget.setLayout(manual_detection_layout)

        # Add radio buttons and settings to the main layout
        radio_buttons_layout = QHBoxLayout()
        radio_buttons_layout.addWidget(self.radio_automatic_settings)
        radio_buttons_layout.addWidget(self.radio_manual_settings)

        singularity_layout.addLayout(radio_buttons_layout)
        singularity_layout.addWidget(self.automatic_settings_widget)
        singularity_layout.addWidget(self.manual_detection_widget)

        # Connect radio button signals to switch function
        self.radio_automatic_settings.toggled.connect(self.switch_detection_settings)
        self.radio_manual_settings.toggled.connect(self.switch_detection_settings)

        # Set initial state
        manual = self.settings.has_singularity_for(self.slope_function_str)
        self.radio_automatic_settings.setChecked(not manual)
        self.radio_manual_settings.setChecked(manual)
        self.switch_detection_settings()  # Ensure correct initial state

    def create_automatic_settings(self, layout):
        """Creates the automatic singularity detection settings."""

        # 'singularity slope' slider
        self.slider_s = QSlider(Qt.Orientation.Horizontal)
        self.slider_s.setMinimum(MIN_SINGULARITY_MIN_SLOPE)
        self.slider_s.setMaximum(MAX_SINGULARITY_MIN_SLOPE)
        self.slider_s.setValue(self.settings.singularity_min_slope)
        self.slider_s.setMinimumWidth(150)
        self.slider_s.setTickInterval(
            (MAX_SINGULARITY_MIN_SLOPE - MIN_SINGULARITY_MIN_SLOPE) // 15
        )
        self.slider_s.setSingleStep(5)
        self.slider_s.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_s.valueChanged.connect(self.changed_singularity_min_slope)
        self.label_s = QLabel()
        self.label_s.setToolTip(
            """This settings determines the minimum slope the function must have 
in order for the singularity detection to kick in."""
        )
        self.label_s.setText(f"  &Singularity slope: {self.settings.singularity_min_slope}   ")
        self.label_s.setBuddy(self.slider_s)
        layout.addWidget(self.label_s)
        layout.addWidget(self.slider_s)

        # the 'trace y margin' input line
        self.y_margin_input = QLineEdit()
        self.y_margin_input.setText(str(self.settings.y_margin))
        self.y_margin_input.textChanged.connect(self.update_y_margin)
        label = QLabel("  Y offscreen margin:")
        label.setToolTip(
            """When the solution curve goes offscreen when tracing, it is cut off
if it gets too far to save calculation time. This setting determines
how many screen heights the curve can go offscreen before it is cut off.
You can make this 0 if you know that the curve doesn't go offscreen.
Or if the curve goes really far offscreen, but you know that it will
come back, you can set this to a higher value."""
        )
        form = QFormLayout()
        form.addRow(label, self.y_margin_input)
        layout.addLayout(form)

    def create_manual_detection_settings(self, layout):
        """Creates the manual singularity detection settings."""

        # 'enter singular equation' line input
        self.equation_input = QLineEdit()
        self.equation_input.setText(
            self.settings.singularity_equations.get(self.slope_function_str, "")
        )
        self.equation_input.setPlaceholderText("Enter singularity equation")
        form = QHBoxLayout()
        form.addWidget(QLabel("  0 ="))
        form.addWidget(self.equation_input)
        layout.addLayout(form)

    def toggle_advanced_settings(self):
        """Toggles the visibility of the advanced settings."""
        if self.singularity_strategy_group_box.isVisible():
            self.label_p.setVisible(False)
            self.slider_p.setVisible(False)
            self.singularity_strategy_group_box.setVisible(False)
            self.toggle_button.setText("Show advanced settings")
        else:
            self.label_p.setVisible(True)
            self.slider_p.setVisible(True)
            self.singularity_strategy_group_box.setVisible(True)
            self.toggle_button.setText("Hide advanced settings")
        self.settings.show_advanced_settings = not self.settings.show_advanced_settings
        self.adjustSize()

    def switch_detection_settings(self):
        """Switches displayed detection settings based on the selected radio button"""
        if self.radio_automatic_settings.isChecked():
            self.manual_detection_widget.setVisible(False)
            self.automatic_settings_widget.setVisible(True)
        elif self.radio_manual_settings.isChecked():
            self.automatic_settings_widget.setVisible(False)
            self.manual_detection_widget.setVisible(True)
        self.adjustSize()

    def accept(self):
        """
        Accepts the dialog, and updates singularity detection settings.
        Shows an error message if the manual singularity equation is invalid and denys the accept.
        """

        # auto detection --> accept
        if self.radio_automatic_settings.isChecked():
            self.settings.auto_singularity_detection = True
            super().accept()
            return

        # manual detection
        equation = self.equation_input.text()

        # if no equation --> switch to auto and accept
        if equation == "":
            self.settings.auto_singularity_detection = True
            super().accept()
            return

        previous_equation = self.settings.singularity_equations.get(
            self.slope_function_str, None
        )

        # if same equation --> accept
        if equation == previous_equation:
            self.settings.auto_singularity_detection = False
            super().accept()
            return

        # if different equation --> check if it is valid
        if self.settings.set_new_singularity_equation(
            self.slope_function_str, equation, self.xlim, self.ylim
        ):
            super().accept()
        else:
            QMessageBox.critical(self, "Error", f"Invalid singularity equation.")

    def changed_trace_lines_width(self):
        """Updates the trace lines width according to the slider."""
        width = self.slider_w.value()
        self.label_w.setText(f"  &Trace lines width: {width}")
        self.settings.line_width = width

    def changed_trace_precision(self):
        """Updates the trace precision according to the slider."""
        precision = self.slider_p.value()
        self.label_p.setText(f"  &Trace precision: {precision}")
        self.settings.trace_precision = precision

    def changed_singularity_min_slope(self):
        """Updates the min_slope according to the slider."""
        min_slope = self.slider_s.value()
        self.label_s.setText(f"  &Singularity slope: {min_slope}")
        self.settings.singularity_min_slope = min_slope

    def update_y_margin(self):
        """Updates y margin according to the y_margin input line."""
        y_margin = self.y_margin_input.text()
        try:
            y_margin = float(y_margin)
            if y_margin < 0:
                y_margin = 0
                self.y_margin_input.setText(str(y_margin))
            if y_margin > MAX_TRACE_Y_MARGIN:
                y_margin = MAX_TRACE_Y_MARGIN
                self.y_margin_input.setText(str(y_margin))
        except ValueError:  # don't change anything if the input is not valid
            return
        self.settings.y_margin = y_margin

    def open_color_dialog(self):
        """Opens a QColorDialog to select a color."""
        color_dialog = QColorDialog(self.selected_color, self)
        color_dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)

        # Applying a custom stylesheet to QColorDialog
        color_dialog.setStyleSheet(
            """
            QSpinBox {
                width : 45px;
                padding-left: -3px;
                padding-right: 15px;
            }
            """
        )

        if color_dialog.exec() == QColorDialog.DialogCode.Accepted:
            self.settings.line_color = color_dialog.selectedColor().name()
            self.update_color_box()  # Update the color box with the new color

    def update_color_box(self):
        """Updates the background color of the color box (QLabel)."""
        self.color_box.setStyleSheet(
            f"background-color: {self.settings.line_color}; border: 1px solid #626262; border-radius: 5px;"
        )
