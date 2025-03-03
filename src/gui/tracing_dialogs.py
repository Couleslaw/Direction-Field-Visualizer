from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QColorDialog,
    QGroupBox,
    QRadioButton,
)

from src.tracing.trace_settings import TraceSettings
from src.gui.component_builder import QtComponentBuilder
from src.default_constants import *
from src.math_functions import try_get_value_from_string

from typing import Tuple, override


class CoordinateDialog(QDialog):
    """Dialog window for inputting X and Y coordinates"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Input Coordinates")

        # Layout for dialog window
        layout = QVBoxLayout()

        # X coordinate input
        x_label = QLabel("Enter X coordinate:")
        self.__x_input = QLineEdit(self)
        layout.addWidget(x_label)
        layout.addWidget(self.__x_input)

        # Y coordinate input
        y_label = QLabel("Enter Y coordinate:")
        self.__y_input = QLineEdit(self)
        layout.addWidget(y_label)
        layout.addWidget(self.__y_input)

        # OK and Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def get_coordinates(self) -> Tuple[float | None, float | None]:
        """Return the X and Y coordinates as a tuple"""
        x = try_get_value_from_string(self.__x_input.text())
        y = try_get_value_from_string(self.__y_input.text())
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
        self.__create_basic_settings(layout)

        # Show/Hide button for advanced settings
        self.__toggle_button = QPushButton(
            "Hide advanced settings"
            if self.__settings.show_advanced_settings
            else "Show advanced settings"
        )
        self.__toggle_button.clicked.connect(self.__toggle_advanced_settings)
        self.__toggle_button.setToolTip(
            "<h4>Hide/show settings for singularity detection</h4>Singularity is a point where the slope of the function goes to infinity. The function can either go to infinity (y = 1/x has a singularity at x=0), or it can abruptly stop (y = sqrt(1-x^2) has singularities at x=1 and x=-1)."
        )
        layout.addWidget(self.__toggle_button)

        # Advanced settings
        self.__create_advanced_settings(layout)

        # OK and Cancel buttons
        self.__button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.__button_box.accepted.connect(self.accept)
        self.__button_box.rejected.connect(self.reject)
        layout.addWidget(self.__button_box)

    def __create_basic_settings(self, layout: QVBoxLayout) -> None:
        """Creates the trace-line-width slider and color-picker button."""

        # Trace line width slider
        self.__slider_w, self.__label_w = QtComponentBuilder.add_slider_with_label(
            min_value=MIN_TRACE_LINES_WIDTH,
            max_value=MAX_TRACE_LINES_WIDTH,
            default_value=self.__settings.displayed_line_width,
            label_text=f"&Trace line width: {self.__settings.displayed_line_width}",
            on_value_changed=self.__changed_trace_lines_width,
        )
        form = QFormLayout()
        form.addRow(self.__label_w, self.__slider_w)
        layout.addLayout(form)

        # Horizontal layout for color button and color box
        color_layout = QHBoxLayout()

        # Button to open color picker dialog
        self.__color_button = QPushButton("Choose color", self)
        self.__color_button.clicked.connect(self.__open_color_dialog)
        color_layout.addWidget(self.__color_button)

        # Color box to display the current color
        self.__color_box = QPushButton(self)
        self.__color_box.clicked.connect(self.__open_color_dialog)
        self.__color_box.setFixedSize(70, 20)  # Size of the color box
        self.__update_color_box()  # Set initial color to red
        color_layout.addWidget(self.__color_box)

        layout.addLayout(color_layout)

    def __create_advanced_settings(self, layout: QVBoxLayout) -> None:
        """Creates the advanced settings section.
        - trace precision slider
        - singularity detection radio buttons
            - automatic: Y offscreen margin, singularity slope
            - manual: singularity equation
            - none
        """

        # Trace precision slider
        self.__slider_p, self.__label_p = QtComponentBuilder.add_slider_with_label(
            min_value=MIN_TRACE_PRECISION,
            max_value=MAX_TRACE_PRECISION,
            default_value=self.__settings.trace_precision,
            label_text=f"&Trace precision: {self.__settings.trace_precision}",
            on_value_changed=self.__changed_trace_precision,
            tooltip="Trace precision directly affects the step size used to trace the solution curve. This affects both Automatic and Equational detection. Higher precision means exponentially smaller step size and exponentially higher calculation time. It is preferred to use equational singularity detection over increasing precision. Increase precision only if a singularity is not being detected correctly.",
        )

        self.__label_p.setVisible(self.__settings.show_advanced_settings)
        self.__slider_p.setVisible(self.__settings.show_advanced_settings)
        layout.addWidget(self.__label_p)
        layout.addWidget(self.__slider_p)

        # Singularity detection settings
        self.__singularity_strategy_group_box = QGroupBox("Singularity detection strategy")
        singularity_layout = QVBoxLayout()
        self.__singularity_strategy_group_box.setLayout(singularity_layout)
        self.__singularity_strategy_group_box.setVisible(self.__settings.show_advanced_settings)
        layout.addWidget(self.__singularity_strategy_group_box)

        # Create singularity detection strategy radio buttons

        # automatic detection
        self.__radio_automatic_settings = QRadioButton("Automatic")
        self.__radio_automatic_settings.setToolTip(
            'Works fine in most cases, detects singularities based on the slope of the function.\nProbably will fail if the singularities appear "suddenly".\nWill be slow if the function has generally high slope.'
        )

        # manual detection
        self.__radio_manual_settings = QRadioButton("Equation")
        self.__radio_manual_settings.setToolTip(
            "Faster, more reliable and more accurate than automatic detection.\nYou have to enter an equation that gives the singularities of the function."
        )

        # no detection
        self.__radio_none_settings = QRadioButton("None")
        self.__radio_none_settings.setToolTip(
            "Chose this if you know that the function doesn't have any singularities.\nWill be faster than the other two methods."
        )

        # Add radio buttons
        radio_buttons_layout = QHBoxLayout()
        radio_buttons_layout.addWidget(self.__radio_automatic_settings)
        radio_buttons_layout.addWidget(self.__radio_manual_settings)
        radio_buttons_layout.addWidget(self.__radio_none_settings)
        singularity_layout.addLayout(radio_buttons_layout)

        # Create settings layouts
        automatic_settings_layout = QVBoxLayout()
        manual_detection_layout = QVBoxLayout()
        self.__create_automatic_detection_settings(automatic_settings_layout)
        self.__create_manual_detection_settings(manual_detection_layout)

        # Wrap the settings layouts in QWidget objects for hiding/showing
        self.__automatic_settings_widget = QWidget()
        self.__automatic_settings_widget.setLayout(automatic_settings_layout)

        self.__manual_detection_widget = QWidget()
        self.__manual_detection_widget.setLayout(manual_detection_layout)

        self.__no_detection_widget = QWidget()

        singularity_layout.addWidget(self.__automatic_settings_widget)
        singularity_layout.addWidget(self.__manual_detection_widget)
        singularity_layout.addWidget(self.__no_detection_widget)

        # Connect radio button signals to switch function
        self.__radio_automatic_settings.toggled.connect(self.__switch_detection_settings)
        self.__radio_manual_settings.toggled.connect(self.__switch_detection_settings)
        self.__radio_none_settings.toggled.connect(self.__switch_detection_settings)

        # Set initial state
        strategy = self.__settings.get_preferred_detection_for(self.__slope_function_str)
        self.__radio_automatic_settings.setChecked(strategy == TraceSettings.Strategy.AUTOMATIC)
        self.__radio_manual_settings.setChecked(strategy == TraceSettings.Strategy.MANUAL)
        self.__radio_none_settings.setChecked(strategy == TraceSettings.Strategy.NONE)
        self.__switch_detection_settings()  # Ensure correct initial state

    def __create_automatic_detection_settings(self, layout: QVBoxLayout) -> None:
        """Creates the automatic singularity detection settings."""

        # 'singularity slope' slider
        self.__slider_s, self.__label_s = QtComponentBuilder.add_slider_with_label(
            min_value=MIN_SINGULARITY_MIN_SLOPE,
            max_value=MAX_SINGULARITY_MIN_SLOPE,
            default_value=self.__settings.singularity_min_slope,
            label_text=f"&Singularity slope: {self.__settings.singularity_min_slope}",
            on_value_changed=self.__changed_singularity_min_slope,
            single_step=5,
            tick_interval=(MAX_SINGULARITY_MIN_SLOPE - MIN_SINGULARITY_MIN_SLOPE) // 15,
            tooltip="""The minimum slope the function must have at point (x,y) in order
for the singularity detection to kick in when at that point.
- higher value: faster, but less accurate
- lower value: possibly much slower, but more accurate""",
        )

        layout.addWidget(self.__label_s)
        layout.addWidget(self.__slider_s)

        # the 'trace y margin' input line
        self.__y_margin_input, _ = QtComponentBuilder.add_line_edit_with_label(
            layout=layout,
            default_text=str(self.__settings.y_margin),
            label_text="  Y offscreen margin:",
            on_text_changed=self.__update_y_margin,
            tooltip="""When the solution curve goes offscreen, it is cut off if it gets
too far, to save calculation time. This setting determines how many
screen heights the curve can go offscreen before it is cut off.
- set this to 0 if you know that the curve doesn't go offscreen.
- if the curve goes really far offscreen and you know it will
  eventually come back, but it doesn't, increase this value.""",
        )

    def __create_manual_detection_settings(self, layout: QVBoxLayout) -> None:
        """Creates the manual singularity detection settings."""

        # 'enter singular equation' line input
        self.__equation_input = QLineEdit()
        self.__equation_input.setText(
            self.__settings.get_singularity_equation_for(self.__slope_function_str)
        )
        self.__equation_input.setPlaceholderText("Enter singularity equation")
        self.__equation_input.setToolTip(
            """The equation that defines the singularities of the function.
Examples:
    - y' = x/y  ⟶  y=0
    - y' = (x+y)/ln(abs(x))  ⟶  ln(abs(x))=0 or abs(x)-1=0
    - y' = y*ln(x) ⟶  x=0
    - y' = tan(x)  ⟶  cos(x)=0
What if there are multiple singularities? Just multiply them together!
    - y' = y/x + ln(sin(y)) ⟶ x*sin(y)=0"""
        )
        self.__equation_input.setFocus()
        form = QFormLayout()
        form.addRow("  0 =", self.__equation_input)
        layout.addLayout(form)

    def __toggle_advanced_settings(self):
        """Toggles the visibility of the advanced settings."""
        if self.__singularity_strategy_group_box.isVisible():
            self.__label_p.setVisible(False)
            self.__slider_p.setVisible(False)
            self.__singularity_strategy_group_box.setVisible(False)
            self.__toggle_button.setText("Show advanced settings")
        else:
            self.__label_p.setVisible(True)
            self.__slider_p.setVisible(True)
            self.__singularity_strategy_group_box.setVisible(True)
            self.__toggle_button.setText("Hide advanced settings")
        self.__settings.show_advanced_settings = not self.__settings.show_advanced_settings
        self.adjustSize()

    def __switch_detection_settings(self) -> None:
        """Switches displayed detection settings based on the selected radio button"""
        # automatic settings
        if self.__radio_automatic_settings.isChecked():
            self.__no_detection_widget.setVisible(False)
            self.__manual_detection_widget.setVisible(False)
            self.__automatic_settings_widget.setVisible(True)
        # manual settings
        elif self.__radio_manual_settings.isChecked():
            self.__no_detection_widget.setVisible(False)
            self.__automatic_settings_widget.setVisible(False)
            self.__manual_detection_widget.setVisible(True)
        # no detection
        elif self.__radio_none_settings.isChecked():
            self.__automatic_settings_widget.setVisible(False)
            self.__manual_detection_widget.setVisible(False)
            self.__no_detection_widget.setVisible(True)
        # adjust the size of the dialog window
        self.adjustSize()

    @override
    def accept(self) -> None:
        """
        Accepts the dialog, and updates singularity detection settings.
        Shows an error message if the manual singularity equation is invalid and denys the accept.
        """

        # auto detection --> accept
        if self.__radio_automatic_settings.isChecked():
            self.__settings.set_preferred_detection_for(
                self.__slope_function_str, TraceSettings.Strategy.AUTOMATIC
            )
            super().accept()
            return

        # no detection --> accept
        if self.__radio_none_settings.isChecked():
            self.__settings.set_preferred_detection_for(
                self.__slope_function_str, TraceSettings.Strategy.NONE
            )
            super().accept()
            return

        # manual detection
        equation = self.__equation_input.text()

        # if no equation
        if equation == "":
            # if wants manual --> show warning
            if (
                self.__settings.get_preferred_detection_for(self.__slope_function_str)
                == TraceSettings.Strategy.MANUAL
            ):
                QMessageBox.warning(self, "Warning", f"Please enter a singularity equation.")
                return
            # else dont change the detection strategy
            super().accept()
            return

        # get previous equation
        previous_equation = self.__settings.get_singularity_equation_for(self.__slope_function_str)

        # if same equation --> accept
        if equation == previous_equation:
            self.__settings.set_preferred_detection_for(
                self.__slope_function_str, TraceSettings.Strategy.MANUAL
            )
            super().accept()
            return

        # if different equation --> check if it is valid
        if self.__settings.set_new_singularity_equation(
            self.__slope_function_str, equation, self.__xlim, self.__ylim
        ):
            self.__settings.set_preferred_detection_for(
                self.__slope_function_str, TraceSettings.Strategy.MANUAL
            )
            super().accept()
        else:
            QMessageBox.critical(self, "Error", f"Invalid singularity equation.")

    def __changed_trace_lines_width(self) -> None:
        """Updates the trace lines width according to the slider."""
        width = self.__slider_w.value()
        self.__label_w.setText(f"  &Trace lines width: {width}")
        self.__settings.displayed_line_width = width

    def __changed_trace_precision(self) -> None:
        """Updates the trace precision according to the slider."""
        precision = self.__slider_p.value()
        self.__label_p.setText(f"  &Trace precision: {precision}")
        self.__settings.trace_precision = precision

    def __changed_singularity_min_slope(self) -> None:
        """Updates the min_slope according to the slider."""
        min_slope = self.__slider_s.value()
        self.__label_s.setText(f"  &Singularity slope: {min_slope}")
        self.__settings.singularity_min_slope = min_slope

    def __update_y_margin(self) -> None:
        """Updates y margin according to the y_margin input line."""

        # get y_margin from the input line
        y_margin = try_get_value_from_string(self.__y_margin_input.text())
        if y_margin is None:
            return

        # y_margin should be between 0 and MAX_TRACE_Y_MARGIN
        if y_margin < 0:
            y_margin = 0
            self.__y_margin_input.setText(str(y_margin))

        if y_margin > MAX_TRACE_Y_MARGIN:
            y_margin = MAX_TRACE_Y_MARGIN
            self.__y_margin_input.setText(str(y_margin))

        # update y_margin in settings
        self.__settings.y_margin = round(y_margin, 3)

    def __open_color_dialog(self) -> None:
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
            self.__update_color_box()  # Update the color box with the new color
            self.__button_box.button(QDialogButtonBox.StandardButton.Ok).setFocus()

    def __update_color_box(self) -> None:
        """Updates the background color of the color box (QLabel)."""
        self.__color_box.setStyleSheet(
            f"background-color: {self.__settings.line_color}; border: 1px solid #626262; border-radius: 5px;"
        )
