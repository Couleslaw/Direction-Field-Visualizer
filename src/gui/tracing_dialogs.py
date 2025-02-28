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
    QDialog,
    QDialogButtonBox,
    QColorDialog,
    QGroupBox,
    QRadioButton,
)

from src.tracing.trace_settings import TraceSettings
from src.default_constants import *

from typing import Tuple, override


class CoordinateDialog(QDialog):
    """Dialog window for inputting X and Y coordinates"""

    def __init__(self, parent: QWidget | None = None):
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
    """Dialog window for changing trace settings."""

    def __init__(
        self,
        parent: QWidget | None,
        trace_settings: TraceSettings,
        slope_function: str,
        xlim: Tuple[float, float],
        ylim: Tuple[float, float],
    ) -> None:
        """Creates the dialog window.

        Args:
            parent (QWidget | None): Parent widget.
            trace_settings (TraceSettings): Settings object which will be changed based on user input.
            slope_function (str): String representation of the current slope function.
            xlim (Tuple[float, float]): Limits of the x-axis.
            ylim (Tuple[float, float]): Limits of the y-axis.
        """
        super().__init__(parent)

        self.setWindowTitle("Trace Settings")
        self.setFixedWidth(265)
        self.__settings = trace_settings
        self.__slope_function_str = slope_function
        self.__xlim = xlim
        self.__ylim = ylim
        self.__selected_color = QColor(self.__settings.line_color)

        # Layout for dialog window
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Basic-settings section
        self.create_basic_settings(layout)

        # Show/Hide button for advanced settings
        self.toggle_button = QPushButton(
            "Hide advanced settings"
            if self.__settings.show_advanced_settings
            else "Show advanced settings"
        )
        self.toggle_button.clicked.connect(self.toggle_advanced_settings)
        self.toggle_button.setToolTip(
            "<h4>Hide/show settings for singularity detection</h4>Singularity is a point where the slope of the function goes to infinity. The function can either go to infinity (y = 1/x has a singularity at x=0), or it can abruptly stop (y = sqrt(1-x^2) has singularities at x=1 and x=-1)."
        )
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

    def create_basic_settings(self, layout: QVBoxLayout) -> None:
        """Creates the trace-line-width slider and color-picker button."""
        # create the 'trace line width' slider
        self.slider_w = QSlider(Qt.Orientation.Horizontal)
        self.slider_w.setMinimum(MIN_TRACE_LINES_WIDTH)
        self.slider_w.setMaximum(MAX_TRACE_LINES_WIDTH)
        self.slider_w.setValue(self.__settings.displayed_line_width)
        self.slider_w.setMinimumWidth(150)
        self.slider_w.setTickInterval(1)
        self.slider_w.setSingleStep(1)
        self.slider_w.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_w.valueChanged.connect(self.changed_trace_lines_width)
        self.label_w = QLabel()
        self.label_w.setText(f"  &Trace line width: {self.__settings.displayed_line_width}   ")
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

        # Color box to display the current color
        self.color_box = QPushButton(self)
        self.color_box.clicked.connect(self.open_color_dialog)
        self.color_box.setFixedSize(70, 20)  # Size of the color box
        self.update_color_box()  # Set initial color to red
        color_layout.addWidget(self.color_box)

        layout.addLayout(color_layout)

    def create_advanced_settings(self, layout: QVBoxLayout) -> None:
        """Creates the advanced settings section.
        - trace precision slider
        - singularity detection radio buttons
            - automatic: Y offscreen margin, singularity slope
            - manual: singularity equation
            - none
        """

        # trace precision slider
        self.slider_p = QSlider(Qt.Orientation.Horizontal)
        self.slider_p.setMinimum(MIN_TRACE_PRECISION)
        self.slider_p.setMaximum(MAX_TRACE_PRECISION)
        self.slider_p.setValue(self.__settings.trace_precision)
        self.slider_p.setMinimumWidth(150)
        self.slider_p.setTickInterval(1)
        self.slider_p.setSingleStep(1)
        self.slider_p.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_p.valueChanged.connect(self.changed_trace_precision)
        self.slider_p.setVisible(self.__settings.show_advanced_settings)
        self.label_p = QLabel()
        self.label_p.setToolTip(
            "Trace precision directly affects the step size used to trace the solution curve. This affects both Automatic and Equational detection. Higher precision means exponentially smaller step size and exponentially higher calculation time. It is preferred to use equational singularity detection over increasing precision. Increase precision only if a singularity is not being detected correctly."
        )
        self.label_p.setText(f"  &Trace precision: {self.__settings.trace_precision}   ")
        self.label_p.setBuddy(self.slider_p)
        self.label_p.setVisible(self.__settings.show_advanced_settings)
        layout.addWidget(self.label_p)
        layout.addWidget(self.slider_p)

        # Singularity detection settings
        self.singularity_strategy_group_box = QGroupBox("Singularity detection strategy")
        singularity_layout = QVBoxLayout()
        self.singularity_strategy_group_box.setLayout(singularity_layout)
        self.singularity_strategy_group_box.setVisible(self.__settings.show_advanced_settings)
        layout.addWidget(self.singularity_strategy_group_box)

        # Create singularity detection strategy radio buttons

        # automatic detection
        self.radio_automatic_settings = QRadioButton("Automatic")
        self.radio_automatic_settings.setToolTip(
            'Works fine in most cases, detects singularities based on the slope of the function.\nProbably will fail if the singularities appear "suddenly".\nWill be slow if the function has generally high slope.'
        )

        # manual detection
        self.radio_manual_settings = QRadioButton("Equation")
        self.radio_manual_settings.setToolTip(
            "Faster, more reliable and more accurate than automatic detection.\nYou have to enter an equation that gives the singularities of the function."
        )

        # no detection
        self.radio_none_settings = QRadioButton("None")
        self.radio_none_settings.setToolTip(
            "Chose this if you know that the function doesn't have any singularities.\nWill be faster than the other two methods."
        )

        # Add radio buttons
        radio_buttons_layout = QHBoxLayout()
        radio_buttons_layout.addWidget(self.radio_automatic_settings)
        radio_buttons_layout.addWidget(self.radio_manual_settings)
        radio_buttons_layout.addWidget(self.radio_none_settings)
        singularity_layout.addLayout(radio_buttons_layout)

        # Create settings layouts
        automatic_settings_layout = QVBoxLayout()
        manual_detection_layout = QVBoxLayout()
        self.create_automatic_settings(automatic_settings_layout)
        self.create_manual_detection_settings(manual_detection_layout)

        # Wrap the settings layouts in QWidget objects for hiding/showing
        self.automatic_settings_widget = QWidget()
        self.automatic_settings_widget.setLayout(automatic_settings_layout)

        self.manual_detection_widget = QWidget()
        self.manual_detection_widget.setLayout(manual_detection_layout)

        self.no_detection_widget = QWidget()

        singularity_layout.addWidget(self.automatic_settings_widget)
        singularity_layout.addWidget(self.manual_detection_widget)
        singularity_layout.addWidget(self.no_detection_widget)

        # Connect radio button signals to switch function
        self.radio_automatic_settings.toggled.connect(self.switch_detection_settings)
        self.radio_manual_settings.toggled.connect(self.switch_detection_settings)
        self.radio_none_settings.toggled.connect(self.switch_detection_settings)

        # Set initial state
        strategy = self.__settings.get_preferred_detection_for(self.__slope_function_str)
        self.radio_automatic_settings.setChecked(strategy == TraceSettings.Strategy.Automatic)
        self.radio_manual_settings.setChecked(strategy == TraceSettings.Strategy.Manual)
        self.radio_none_settings.setChecked(strategy == TraceSettings.Strategy.None_)
        self.switch_detection_settings()  # Ensure correct initial state

    def create_automatic_settings(self, layout: QVBoxLayout) -> None:
        """Creates the automatic singularity detection settings."""

        # 'singularity slope' slider
        self.slider_s = QSlider(Qt.Orientation.Horizontal)
        self.slider_s.setMinimum(MIN_SINGULARITY_MIN_SLOPE)
        self.slider_s.setMaximum(MAX_SINGULARITY_MIN_SLOPE)
        self.slider_s.setValue(self.__settings.singularity_min_slope)
        self.slider_s.setMinimumWidth(150)
        self.slider_s.setTickInterval(
            (MAX_SINGULARITY_MIN_SLOPE - MIN_SINGULARITY_MIN_SLOPE) // 15
        )
        self.slider_s.setSingleStep(5)
        self.slider_s.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_s.valueChanged.connect(self.changed_singularity_min_slope)
        self.label_s = QLabel()
        self.label_s.setToolTip(
            """The minimum slope the function must have at point (x,y) in order
for the singularity detection to kick in when at that point.
- higher value: faster, but less accurate
- lower value: possibly much slower, but more accurate"""
        )
        self.label_s.setText(
            f"  &Singularity slope: {self.__settings.singularity_min_slope}   "
        )
        self.label_s.setBuddy(self.slider_s)
        layout.addWidget(self.label_s)
        layout.addWidget(self.slider_s)

        # the 'trace y margin' input line
        self.y_margin_input = QLineEdit()
        self.y_margin_input.setText(str(self.__settings.y_margin))
        self.y_margin_input.textChanged.connect(self.update_y_margin)
        label = QLabel("  Y offscreen margin:")
        label.setToolTip(
            """When the solution curve goes offscreen, it is cut off if it gets
too far, to save calculation time. This setting determines how many
screen heights the curve can go offscreen before it is cut off.
- set this to 0 if you know that the curve doesn't go offscreen.
- if the curve goes really far offscreen and you know it will
  eventually come back, but it doesn't, increase this value."""
        )
        form = QFormLayout()
        form.addRow(label, self.y_margin_input)
        layout.addLayout(form)

    def create_manual_detection_settings(self, layout: QVBoxLayout) -> None:
        """Creates the manual singularity detection settings."""

        # 'enter singular equation' line input
        self.equation_input = QLineEdit()
        self.equation_input.setText(
            self.__settings.get_singularity_equation_for(self.__slope_function_str)
        )
        self.equation_input.setPlaceholderText("Enter singularity equation")
        form = QHBoxLayout()
        form.addWidget(QLabel("  0 ="))
        self.equation_input.setToolTip(
            """The equation that defines the singularities of the function.
Examples:
    - y' = x/y  ⟶  y=0
    - y' = (x+y)/ln(abs(x))  ⟶  ln(abs(x))=0 or abs(x)-1=0
    - y' = y*ln(x) ⟶  x=0
    - y' = tan(x)  ⟶  cos(x)=0
What if there are multiple singularities? Just multiply them together!
    - y' = y/x + ln(sin(y)) ⟶ x*sin(y)=0"""
        )
        self.equation_input.setFocus()
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
        self.__settings.show_advanced_settings = not self.__settings.show_advanced_settings
        self.adjustSize()

    def switch_detection_settings(self) -> None:
        """Switches displayed detection settings based on the selected radio button"""
        # automatic settings
        if self.radio_automatic_settings.isChecked():
            self.no_detection_widget.setVisible(False)
            self.manual_detection_widget.setVisible(False)
            self.automatic_settings_widget.setVisible(True)
        # manual settings
        elif self.radio_manual_settings.isChecked():
            self.no_detection_widget.setVisible(False)
            self.automatic_settings_widget.setVisible(False)
            self.manual_detection_widget.setVisible(True)
        # no detection
        elif self.radio_none_settings.isChecked():
            self.automatic_settings_widget.setVisible(False)
            self.manual_detection_widget.setVisible(False)
            self.no_detection_widget.setVisible(True)
        # adjust the size of the dialog window
        self.adjustSize()

    @override
    def accept(self) -> None:
        """
        Accepts the dialog, and updates singularity detection settings.
        Shows an error message if the manual singularity equation is invalid and denys the accept.
        """

        # auto detection --> accept
        if self.radio_automatic_settings.isChecked():
            self.__settings.set_preferred_detection_for(
                self.__slope_function_str, TraceSettings.Strategy.Automatic
            )
            super().accept()
            return

        # no detection --> accept
        if self.radio_none_settings.isChecked():
            self.__settings.set_preferred_detection_for(
                self.__slope_function_str, TraceSettings.Strategy.None_
            )
            super().accept()
            return

        # manual detection
        equation = self.equation_input.text()

        # if no equation
        if equation == "":
            # if wants manual --> show warning
            if (
                self.__settings.get_preferred_detection_for(self.__slope_function_str)
                == TraceSettings.Strategy.Manual
            ):
                QMessageBox.warning(self, "Warning", f"Please enter a singularity equation.")
                return
            # else dont change the detection strategy
            super().accept()
            return

        # get previous equation
        previous_equation = self.__settings.get_singularity_equation_for(
            self.__slope_function_str
        )

        # if same equation --> accept
        if equation == previous_equation:
            self.__settings.set_preferred_detection_for(
                self.__slope_function_str, TraceSettings.Strategy.Manual
            )
            super().accept()
            return

        # if different equation --> check if it is valid
        if self.__settings.set_new_singularity_equation(
            self.__slope_function_str, equation, self.__xlim, self.__ylim
        ):
            self.__settings.set_preferred_detection_for(
                self.__slope_function_str, TraceSettings.Strategy.Manual
            )
            super().accept()
        else:
            QMessageBox.critical(self, "Error", f"Invalid singularity equation.")

    def changed_trace_lines_width(self) -> None:
        """Updates the trace lines width according to the slider."""
        width = self.slider_w.value()
        self.label_w.setText(f"  &Trace lines width: {width}")
        self.__settings.displayed_line_width = width

    def changed_trace_precision(self) -> None:
        """Updates the trace precision according to the slider."""
        precision = self.slider_p.value()
        self.label_p.setText(f"  &Trace precision: {precision}")
        self.__settings.trace_precision = precision

    def changed_singularity_min_slope(self) -> None:
        """Updates the min_slope according to the slider."""
        min_slope = self.slider_s.value()
        self.label_s.setText(f"  &Singularity slope: {min_slope}")
        self.__settings.singularity_min_slope = min_slope

    def update_y_margin(self) -> None:
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
        self.__settings.y_margin = y_margin

    def open_color_dialog(self) -> None:
        """Opens a QColorDialog to select a color."""
        color_dialog = QColorDialog(self.__selected_color, self)
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

        # change color if dialog is accepted
        if color_dialog.exec() == QColorDialog.DialogCode.Accepted:
            self.__settings.line_color = color_dialog.selectedColor().name()
            self.update_color_box()  # Update the color box with the new color
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setFocus()

    def update_color_box(self) -> None:
        """Updates the background color of the color box (QLabel)."""
        self.color_box.setStyleSheet(
            f"background-color: {self.__settings.line_color}; border: 1px solid #626262; border-radius: 5px;"
        )
