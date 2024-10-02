import sys
import os
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QSlider,
    QLineEdit,
    QMessageBox,
    QSpacerItem,
    QSizePolicy,
    QFileDialog,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QColorDialog,
    QGroupBox,
)

from src.canvas import Canvas
from src.numerical_methods import (
    TraceSettings,
    create_function_from_string,
)
from src.default_constants import *

ROUND_INPUT_LINES = 7


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
    def __init__(self, parent, trace_settings: TraceSettings, function: str, xlim, ylim):
        super().__init__(parent)

        self.setWindowTitle("Trace Settings")
        self.setFixedWidth(250)
        self.settings = trace_settings
        self.function = function
        self.xlim = xlim
        self.ylim = ylim
        self.selected_color = QColor(self.settings.line_color)

        # Layout for dialog window
        layout = QVBoxLayout()

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
        self.color_button = QPushButton("Choose Color", self)
        self.color_button.clicked.connect(self.open_color_dialog)
        color_layout.addWidget(self.color_button)

        # Color box (QLabel) to display the current color
        self.color_box = QLabel(self)
        self.color_box.setFixedSize(50, 20)  # Size of the color box
        self.update_color_box()  # Set initial color to red
        color_layout.addWidget(self.color_box)

        layout.addLayout(color_layout)

        # Advanced section (collapsible)
        self.advanced_group_box = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout()
        self.advanced_group_box.setLayout(advanced_layout)
        self.advanced_group_box.setVisible(self.settings.show_advanced_settings)
        layout.addWidget(self.advanced_group_box)

        # create trace precision slider
        self.slider_p = QSlider(Qt.Orientation.Horizontal)
        self.slider_p.setMinimum(MIN_TRACE_PRECISION)
        self.slider_p.setMaximum(MAX_TRACE_PRECISION)
        self.slider_p.setValue(self.settings.trace_precision)
        self.slider_p.setMinimumWidth(150)
        self.slider_p.setTickInterval(1)
        self.slider_p.setSingleStep(1)
        self.slider_p.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_p.valueChanged.connect(self.changed_trace_precision)
        self.label_p = QLabel()
        self.label_p.setToolTip(
            """Trace precision directly affects the size of the dx step used 
to trace the solution curve. Higher precision means
exponentially smaller dx and exponentially higher calculation 
time. Increase precision only if there is a singularity that
is not being detected."""
        )
        self.label_p.setText(f"  &Trace precision: {self.settings.trace_precision}   ")
        self.label_p.setBuddy(self.slider_p)
        form = QVBoxLayout()
        form.addWidget(self.label_p)
        form.addWidget(self.slider_p)
        advanced_layout.addRow(form)

        # create the 'trace y margin' input line
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
        advanced_layout.addRow(label, self.y_margin_input)

        if not self.settings.has_singularity_for(function):
            self.settings.auto_singularity_detection = True

        # create 'automatic singularity detection' checkbox
        self.automatic_singularity_detection = QCheckBox("Automatic singularity detection")
        self.automatic_singularity_detection.setToolTip(
            """If enabled the program will try to detect singularities automatically.
In some cases, it might be very difficult to detect singularities correctly, 
especially if you zoom further out. If you specify the equation for singularities 
manually, the program will use that instead of automatic detection.
For example: y'=x/y has the singularity equation 0=y."""
        )
        self.automatic_singularity_detection.setChecked(
            self.settings.auto_singularity_detection
        )
        self.automatic_singularity_detection.stateChanged.connect(
            self.changed_automatic_singularity_detection
        )
        advanced_layout.addRow(self.automatic_singularity_detection)

        # create 'singularity slope' slider
        self.slider_s = QSlider(Qt.Orientation.Horizontal)
        self.slider_s.setEnabled(self.settings.auto_singularity_detection)
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
        form = QVBoxLayout()
        form.addWidget(self.label_s)
        form.addWidget(self.slider_s)
        advanced_layout.addRow(form)

        # create 'enter singular equation' line input
        self.equation_input = QLineEdit()
        self.equation_input.setEnabled(not self.settings.auto_singularity_detection)
        self.equation_input.setText(self.settings.singularity_equations.get(function, ""))
        self.equation_input.setPlaceholderText("Enter singularity equation")
        form = QHBoxLayout()
        form.addWidget(QLabel("  0 ="))
        form.addWidget(self.equation_input)
        advanced_layout.addRow(form)

        # Show/Hide button for advanced settings
        self.toggle_button = QPushButton("Show Advanced Settings")
        self.toggle_button.clicked.connect(self.toggle_advanced_settings)

        layout.addWidget(self.toggle_button)

        # OK and Cancel buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def toggle_advanced_settings(self):
        if self.advanced_group_box.isVisible():
            self.advanced_group_box.setVisible(False)
            self.toggle_button.setText("Show Advanced Settings")
        else:
            self.advanced_group_box.setVisible(True)
            self.toggle_button.setText("Hide Advanced Settings")
        self.settings.show_advanced_settings = not self.settings.show_advanced_settings
        self.adjustSize()

    def accept(self):
        """accept the dialog, but raise an error if the entered singularity eq. is invalid"""
        previous = self.settings.singularity_equations.get(self.function, 0)
        eq_str = self.equation_input.text()
        if not self.settings.auto_singularity_detection and eq_str != previous:
            try:
                new_eq = create_function_from_string(eq_str)
                # try to evaluate the equation at a few random points
                for _ in range(20):
                    try:
                        x = np.random.uniform(self.xlim[0], self.xlim[1])
                        y = np.random.uniform(self.ylim[0], self.ylim[1])
                        new_eq(x, y)
                    except ZeroDivisionError:
                        pass
                    except ValueError:
                        pass
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Invalid singularity equation.")
                return

        # accept the dialog
        self.settings.singularity_equations[self.function] = eq_str
        super().accept()

    def changed_automatic_singularity_detection(self, checked):
        self.slider_s.setEnabled(checked)
        self.equation_input.setEnabled(not checked)
        self.settings.auto_singularity_detection = checked

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


class MyApp(QWidget):
    """Creates the GUI using the PyQt6 library."""

    equal_axes = True  # True if the 'Equal axes' checkbox is checked

    def __init__(self):
        super().__init__()
        self.setMinimumSize(900, 560)
        self.setWindowTitle("Direction Field Visualizer")

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        mainLayout = QVBoxLayout()

        # create the matplotlib graph
        self.canvas = Canvas(self)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        mainLayout.addWidget(self.canvas)

        # create the top bar layout
        topbar = QWidget()
        self.bot_barLayout = QHBoxLayout()
        topbar.setLayout(self.bot_barLayout)
        # topbar.setMaximumHeight(170)
        mainLayout.addWidget(topbar)

        self.layout.addLayout(mainLayout)

        # store all side-bar widgets here
        sidebar = QWidget()
        self.sidebarLayout = QVBoxLayout()
        self.sidebarLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar.setLayout(self.sidebarLayout)
        sidebar.setMaximumWidth(200)
        self.layout.addWidget(sidebar)

        self.initUI()

    def initUI(self):
        # create the function input line and graph button
        self.function_input = QLineEdit()
        self.function_input.setText(str(DEFAULT_FUNCTION))
        form = QFormLayout()
        form.addRow(
            "  y'(x) =", self.function_input
        )  # spaces at the beginning are for additional padding
        self.sidebarLayout.addLayout(form)

        graphLayout = QHBoxLayout()
        self.graph_button = QPushButton("Graph")
        self.graph_button.clicked.connect(self.execute_graph_function)
        self.graph_button.setShortcut("Return")
        graphLayout.addWidget(self.graph_button)

        # create the 'save image' button
        self.save_button = QPushButton("&Save image")
        self.save_button.clicked.connect(self.show_save_file_dialog)
        self.save_button.setShortcut("Ctrl+S")
        graphLayout.addWidget(self.save_button)
        self.sidebarLayout.addLayout(graphLayout)

        # add space
        spacer = QSpacerItem(0, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        self.sidebarLayout.addItem(spacer)

        # create the 'num arrows' input line and buttons
        self.num_arrows_input = QLineEdit()
        self.num_arrows_input.setText(str(DEFAULT_NUM_ARROWS))
        self.num_arrows_input.textChanged.connect(self.update_num_arrows)
        form = QFormLayout()
        form.addRow(
            "  Number of arrows:", self.num_arrows_input
        )  # spaces at the beginning are for additional padding

        self.plus_arrows = QPushButton("+")
        self.plus_arrows.clicked.connect(self.add_more_arrows)
        self.plus_arrows.setShortcut("Alt+right")
        self.minus_arrows = QPushButton("-")
        self.minus_arrows.clicked.connect(self.remove_some_arrows)
        self.minus_arrows.setShortcut("Alt+left")

        arrowLayout = QHBoxLayout()
        arrowLayout.addWidget(self.minus_arrows)
        arrowLayout.addWidget(self.plus_arrows)

        self.sidebarLayout.addLayout(form)
        self.sidebarLayout.addLayout(arrowLayout)

        # create the 'arrow length' slider
        self.slider_a = QSlider(Qt.Orientation.Horizontal)
        self.slider_a.setMinimum(MIN_ARROW_LENGTH)
        self.slider_a.setMaximum(MAX_ARROW_LENGTH)
        self.slider_a.setValue(DEFAULT_ARROW_LENGTH)
        self.slider_a.setMinimumWidth(150)
        self.slider_a.setTickInterval(2)
        self.slider_a.setSingleStep(1)
        self.slider_a.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_a.valueChanged.connect(self.changed_arrow_length)
        self.label_a = QLabel()
        self.label_a.setText(f"  &Arrow length: {DEFAULT_ARROW_LENGTH}   ")
        self.label_a.setBuddy(
            self.slider_a
        )  # changes focus to the slider if 'Alt+a' is pressed
        form = QVBoxLayout()
        form.addWidget(self.label_a)
        form.addWidget(self.slider_a)
        self.sidebarLayout.addLayout(form)

        # create the 'arrow width' slider
        self.slider_aw = QSlider(Qt.Orientation.Horizontal)
        self.slider_aw.setMinimum(MIN_ARROW_WIDTH)
        self.slider_aw.setMaximum(MAX_ARROW_WIDTH)
        self.slider_aw.setValue(DEFAULT_ARROW_WIDTH)
        self.slider_aw.setMinimumWidth(150)
        self.slider_aw.setTickInterval(2)
        self.slider_aw.setSingleStep(1)
        self.slider_aw.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_aw.valueChanged.connect(self.changed_arrow_width)
        self.label_aw = QLabel()
        self.label_aw.setText(f"  &Arrow width: {DEFAULT_ARROW_WIDTH}   ")
        self.label_aw.setBuddy(
            self.slider_aw
        )  # changes focus to the slider if 'Alt+a' is pressed
        form = QVBoxLayout()
        form.addWidget(self.label_aw)
        form.addWidget(self.slider_aw)
        self.sidebarLayout.addLayout(form)

        # add some spacing
        self.sidebarLayout.addItem(spacer)

        # create the 'Color by curvature' checkbox
        self.colors = QCheckBox("Color by curvature")
        self.colors.setChecked(True)
        self.colors.stateChanged.connect(self.checked_color)
        self.sidebarLayout.addWidget(self.colors)

        # create the 'color intensity' slider
        self.slider_c = QSlider(Qt.Orientation.Horizontal)
        self.slider_c.setMinimum(MIN_COLOR_INTENSITY)
        self.slider_c.setMaximum(MAX_COLOR_INTENSITY)
        self.slider_c.setValue(DEFAULT_COLOR_INTENSITY)
        self.slider_c.setMinimumWidth(150)
        self.slider_c.setTickInterval(1)
        self.slider_c.setSingleStep(1)
        self.slider_c.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_c.valueChanged.connect(self.changed_color_intensity)
        self.label_c = QLabel()
        self.label_c.setText(f"  &Color contrast: {DEFAULT_COLOR_INTENSITY}   ")
        self.label_c.setBuddy(
            self.slider_c
        )  # changes focus to the slider if 'Alt+c' is pressed
        form = QVBoxLayout()
        form.addWidget(self.label_c)
        form.addWidget(self.slider_c)
        self.sidebarLayout.addLayout(form)

        # create the 'color precision' slider
        self.slider_cp = QSlider(Qt.Orientation.Horizontal)
        self.slider_cp.setMinimum(MIN_COLOR_PRECISION)
        self.slider_cp.setMaximum(MAX_COLOR_PRECISION)
        self.slider_cp.setValue(DEFAULT_COLOR_PRECISION)
        self.slider_cp.setMinimumWidth(150)
        self.slider_cp.setTickInterval(1)
        self.slider_cp.setSingleStep(1)
        self.slider_cp.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_cp.valueChanged.connect(self.updated_color_precision)
        self.label_cp = QLabel()
        self.label_cp.setText(f"  &Color precision: {DEFAULT_COLOR_PRECISION}   ")
        self.label_cp.setBuddy(self.slider_cp)
        form = QVBoxLayout()
        form.addWidget(self.label_cp)
        form.addWidget(self.slider_cp)
        self.sidebarLayout.addLayout(form)

        # create color map dropdown list
        self.color_map = QComboBox()
        for color_map in AVAILABLE_COLOR_MAPS:
            self.color_map.addItem(color_map)
        self.color_map.setCurrentText(DEFAULT_COLOR_MAP)
        self.color_map.currentTextChanged.connect(self.canvas.set_color_map)
        self.sidebarLayout.addWidget(self.color_map)

        # add some spacing
        self.sidebarLayout.addItem(spacer)

        # create the 'Mouse line' checkbox
        self.mouseLine = QCheckBox("Mouse line")
        self.mouseLine.stateChanged.connect(self.checked_mouseLine)
        self.mouseLine.setChecked(False)
        self.mouseLine.setShortcut("Ctrl+&M")
        self.sidebarLayout.addWidget(self.mouseLine)

        # create the 'Mouse line length' slider
        self.slider_ml = QSlider(Qt.Orientation.Horizontal)
        self.slider_ml.setMinimum(1)
        self.slider_ml.setMaximum(10)
        self.slider_ml.setValue(DEFAULT_MOUSE_LINE_LENGTH)
        self.slider_ml.setMinimumWidth(150)
        self.slider_ml.setTickInterval(1)
        self.slider_ml.setSingleStep(1)
        self.slider_ml.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_ml.valueChanged.connect(self.changed_mouse_line_length)
        self.label_ml = QLabel()
        self.label_ml.setText(f"  &Mouse line length: {DEFAULT_MOUSE_LINE_LENGTH}   ")
        self.label_ml.setBuddy(
            self.slider_ml
        )  # changes focus to the slider if 'Alt+m' is pressed
        form = QVBoxLayout()
        form.addWidget(self.label_ml)
        form.addWidget(self.slider_ml)
        self.sidebarLayout.addLayout(form)

        # create the 'Mouse line width' slider
        self.slider_mw = QSlider(Qt.Orientation.Horizontal)
        self.slider_mw.setMinimum(1)
        self.slider_mw.setMaximum(10)
        self.slider_mw.setValue(DEFAULT_MOUSE_LINE_WIDTH)
        self.slider_mw.setMinimumWidth(150)
        self.slider_mw.setTickInterval(1)
        self.slider_mw.setSingleStep(1)
        self.slider_mw.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_mw.valueChanged.connect(self.changed_mouse_line_width)
        self.label_mw = QLabel()
        self.label_mw.setText(f"  &Mouse line width: {DEFAULT_MOUSE_LINE_WIDTH}   ")
        self.label_mw.setBuddy(
            self.slider_mw
        )  # changes focus to the slider if 'Alt+m' is pressed
        form = QVBoxLayout()
        form.addWidget(self.label_mw)
        form.addWidget(self.slider_mw)
        self.sidebarLayout.addLayout(form)
        # add some spacing
        self.sidebarLayout.addItem(spacer)

        layout = QHBoxLayout()
        # create the 'trace settings' button
        self.trace_settings_button = QPushButton("&Trace settings")
        self.trace_settings_button.clicked.connect(self.show_trace_settings_dialog)
        self.trace_settings_button.setShortcut("Ctrl+T")
        layout.addWidget(self.trace_settings_button)
        # add button for specifying x and y coordinates of the start point
        self.trace_point_button = QPushButton("Trace &point")
        self.trace_point_button.clicked.connect(self.clicked_trace_point_button)
        self.trace_point_button.setShortcut("Ctrl+P")
        layout.addWidget(self.trace_point_button)
        self.sidebarLayout.addLayout(layout)

        layout = QHBoxLayout()
        # create the 'Grid' checkbox
        self.gridCheckBox = QCheckBox("Grid")
        self.gridCheckBox.setChecked(False)
        self.gridCheckBox.stateChanged.connect(self.checked_grid)
        layout.addWidget(self.gridCheckBox)

        # create the 'Axes' checkbox
        self.axesCheckBox = QCheckBox("Axes")
        self.axesCheckBox.setChecked(True)
        self.axesCheckBox.stateChanged.connect(self.checked_axes)
        layout.addWidget(self.axesCheckBox)
        self.sidebarLayout.addLayout(layout)

        # create the 'Equal axes' checkbox
        self.equalAxes = QCheckBox("Equal axes")
        self.equalAxes.stateChanged.connect(self.checked_equalAxes)
        self.bot_barLayout.addWidget(self.equalAxes)

        # create the 'x min' input line
        self.xmin_input = QLineEdit()
        self.xmin_input.setText(str(DEFAULT_XMIN))
        self.xmin_input.textChanged.connect(self.update_xmin)
        form = QFormLayout()
        form.addRow(
            "  x min:", self.xmin_input
        )  # spaces at the beginning are for additional padding
        self.bot_barLayout.addLayout(form)

        # create the 'x max' input line
        self.xmax_input = QLineEdit()
        self.xmax_input.setText(str(DEFAULT_XMAX))
        self.xmax_input.textChanged.connect(self.update_xmax)
        form = QFormLayout()
        form.addRow(
            "  x max:", self.xmax_input
        )  # spaces at the beginning are for additional padding
        self.bot_barLayout.addLayout(form)

        # create the 'y min' input line
        self.ymin_input = QLineEdit()
        self.ymin_input.setText(str(DEFAULT_YMIN))
        self.ymin_input.textChanged.connect(self.update_ymin)
        form = QFormLayout()
        form.addRow(
            "  y min:", self.ymin_input
        )  # spaces at the beginning are for additional padding
        self.bot_barLayout.addLayout(form)

        # create the 'y max' input line
        self.ymax_input = QLineEdit()
        self.ymax_input.setText(str(DEFAULT_YMAX))
        self.ymax_input.textChanged.connect(self.update_ymax)
        form = QFormLayout()
        form.addRow(
            "  y max:", self.ymax_input
        )  # spaces at the beginning are for additional padding
        self.bot_barLayout.addLayout(form)

        self.equalAxes.setChecked(MyApp.equal_axes)

        # create the 'center x' button
        self.center_x_button = QPushButton("Center &X")
        self.center_x_button.clicked.connect(self.canvas.centralize_plot_x)
        self.center_x_button.setShortcut("Alt+X")
        self.bot_barLayout.addWidget(self.center_x_button)

        # create the 'center y' button
        self.center_y_button = QPushButton("Center &Y")
        self.center_y_button.clicked.connect(self.canvas.centralize_plot_y)
        self.center_y_button.setShortcut("Alt+Y")
        self.bot_barLayout.addWidget(self.center_y_button)

    def show_save_file_dialog(self):
        """Opens a dialog to save the current figure as a png or svg file."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            f"",
            "SVG (*.svg);; PNG (*.png);; PDF (*.pdf);; All Files (*)",
        )
        if file_name:
            self.canvas.figure.savefig(file_name, bbox_inches="tight")

    def execute_graph_function(self):
        """Executes the function given in the function input line."""
        func_str = self.function_input.text()
        success = False

        # save the last function in case the new one is invalid
        # it is possible that the last is invalid as well iff
        # 1. the user entered a valid function that is not defined everywhere
        # 2. moved the canvas so that the whole rendering region is undefined --> no arrows are drawn
        # 3. entered an invalid function s.t. it is undefined on the whole rendering region
        #    --> ValueErrors are raised before NameErrors and ihe invalid function is not detected
        # 4. moved the canvas such that there is a point where the NameError is raised (ValueError is not raised)

        previous = self.canvas.dfb.function
        try:
            new_func = create_function_from_string(func_str)
            self.canvas.dfb.function = new_func
            self.canvas.redraw(just_entered_new_function=True)
            success = True
        except:
            QMessageBox.critical(self, "Error", f"Invalid function")

        # restore the previous function if the new one is invalid
        if not success:
            self.canvas.dfb.function = previous
            self.canvas.redraw()
        else:
            if self.canvas.dfb.function_string != func_str:
                self.canvas.dfb.function_string = func_str
                self.canvas.dfb.trace_settings.auto_singularity_detection = (
                    not self.canvas.dfb.trace_settings.has_singularity_for(func_str)
                )

    def checked_equalAxes(self, checked):
        """Turns equal_axes on and off."""
        MyApp.equal_axes = not MyApp.equal_axes
        if checked:
            self.canvas.set_equal_axes()
            self.enable_input_lines(False)
        else:
            self.canvas.set_auto_axes()
            self.enable_input_lines(True)
            self.update_xmin()  # set pre-equal_axes lims
            self.update_xmax()
            self.update_ymin()
            self.update_ymax()
        self.canvas.redraw()

    def enable_input_lines(self, enabled):
        self.xmin_input.setEnabled(enabled)
        self.xmax_input.setEnabled(enabled)
        self.ymin_input.setEnabled(enabled)
        self.ymax_input.setEnabled(enabled)

    def checked_color(self, checked):
        """Turns color on and off."""
        self.canvas.set_is_colored(checked)

    def changed_color_intensity(self):
        """Updates the color intensity according to the slider."""
        color_intensity = self.slider_c.value()
        self.label_c.setText(f"  &Color contrast: {color_intensity}")
        self.canvas.set_color_intensity(color_intensity)

    def updated_color_precision(self):
        """Updates the color precision according to the slider."""
        color_precision = self.slider_cp.value()
        self.label_cp.setText(f"  &Color precision: {color_precision}")
        self.canvas.set_color_precision(color_precision)

    def checked_grid(self, checked):
        self.canvas.set_grid_enabled(checked)

    def checked_axes(self, checked):
        self.canvas.set_axes_enabled(checked)

    def clicked_trace_point_button(self):
        """Opens a dialog to input the x and y coordinates of the start point."""
        dialog = CoordinateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            x, y = dialog.get_coordinates()
            try:
                x = float(eval(x))
                y = float(eval(y))
                xlim = self.canvas.get_xlim()
                ylim = self.canvas.get_ylim()
                if x < xlim[0] or x > xlim[1]:
                    QMessageBox.warning(self, "Warning", f"X is out of bounds, not tracing.")
                    return
                elif y < ylim[0] or y > ylim[1]:
                    # create messagebox to ask if the user wishes to continue
                    continue_messagebox = QMessageBox(self)
                    continue_messagebox.setWindowTitle("Warning")
                    continue_messagebox.setText("Y is out of bounds, continue tracing?")
                    continue_messagebox.setStandardButtons(
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    continue_messagebox.setDefaultButton(QMessageBox.StandardButton.No)
                    continue_messagebox.setIcon(QMessageBox.Icon.Warning)
                    continue_messagebox.exec()
                    if continue_messagebox.result() == QMessageBox.StandardButton.No:
                        return
                self.canvas.dfb.trace_from_point(x, y)
            except Exception:
                QMessageBox.critical(self, "Error", f"Invalid coordinates.")

    def show_trace_settings_dialog(self):
        """Opens a dialog to set the trace settings."""
        new_settings = self.canvas.dfb.trace_settings.copy()
        dialog = TraceSettingsDialog(
            self,
            new_settings,
            self.canvas.dfb.function_string,
            self.canvas.get_xlim(),
            self.canvas.get_ylim(),
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.canvas.dfb.trace_settings = new_settings

    def update_xmin(self):
        """Updates xmin according to the xmin input line."""
        xmin = self.xmin_input.text()
        try:
            xmin = float(xmin)
        except ValueError:  # don't change anything if the input is not valid
            return
        xlim = self.canvas.get_xlim()
        if xmin == round(xlim[0], ROUND_INPUT_LINES) or xmin >= xlim[1]:
            return
        self.canvas.set_xlim((xmin, xlim[1]))

    def update_xmax(self):
        """Updates xmax according to the xmax input line."""
        xmax = self.xmax_input.text()
        try:
            xmax = float(xmax)
        except ValueError:  # don't change anything if the input is not valid
            return
        xlim = self.canvas.get_xlim()
        if xmax == round(xlim[1], ROUND_INPUT_LINES) or xmax <= xlim[0]:
            return
        self.canvas.set_xlim((xlim[0], xmax))

    def update_ymin(self):
        """Updates ymin according to the ymin input line."""
        ymin = self.ymin_input.text()
        try:
            ymin = float(ymin)
        except ValueError:  # don't change anything if the input is not valid
            return
        ylim = self.canvas.get_ylim()
        if ymin == round(ylim[0], ROUND_INPUT_LINES) or ymin >= ylim[1]:
            return
        self.canvas.set_ylim((ymin, ylim[1]))

    def update_ymax(self):
        """Updates ymax according to the ymax input line."""
        ymax = self.ymax_input.text()
        try:
            ymax = float(ymax)
        except ValueError:  # don't change anything if the input is not valid
            return
        ylim = self.canvas.get_ylim()
        if ymax == round(ylim[1], ROUND_INPUT_LINES) or ymax <= ylim[0]:
            return
        self.canvas.set_ylim((ylim[0], ymax))

    def update_displayed_lims(self):
        """Updates all displayed lims according to actual lims."""
        (xmin, xmax), (ymin, ymax) = self.canvas.get_xlim(), self.canvas.get_ylim()
        self.xmin_input.setText(f"{xmin:.{ROUND_INPUT_LINES}f}")
        self.xmax_input.setText(f"{xmax:.{ROUND_INPUT_LINES}f}")
        self.ymin_input.setText(f"{ymin:.{ROUND_INPUT_LINES}f}")
        self.ymax_input.setText(f"{ymax:.{ROUND_INPUT_LINES}f}")

    def update_num_arrows(self):
        """Updates the number of arrows according to the input line."""
        num_arrows = self.num_arrows_input.text()
        try:
            num_arrows = int(num_arrows)
        except ValueError:  # don't change anything if the input is not valid
            return
        if num_arrows < MIN_NUM_ARROWS or num_arrows > MAX_NUM_ARROWS:
            num_arrows = np.clip(num_arrows, MIN_NUM_ARROWS, MAX_NUM_ARROWS)
            self.num_arrows_input.setText(str(num_arrows))
        if num_arrows < 1:
            num_arrows = 1
            self.num_arrows_input.setText(str(num_arrows))
        self.canvas.set_num_arrows(num_arrows)
        self.canvas.redraw()

    def add_more_arrows(self):
        self.num_arrows_input.setText(str(int(self.num_arrows_input.text()) + 5))

    def remove_some_arrows(self):
        self.num_arrows_input.setText(str(int(self.num_arrows_input.text()) - 5))

    def changed_arrow_length(self):
        """Updates the arrow length according to the slider."""
        arrow_length = self.slider_a.value()
        self.label_a.setText(f"  &Arrow length: {arrow_length}")
        self.canvas.set_arrow_length(arrow_length)
        self.canvas.redraw()

    def changed_arrow_width(self):
        """Updates the arrow width according to the slider."""
        arrow_width = self.slider_aw.value()
        self.label_aw.setText(f"  &Arrow width: {arrow_width}")
        self.canvas.set_arrow_width(arrow_width)
        self.canvas.redraw()

    def changed_mouse_line_width(self):
        """Updates the mouse line width according to the slider."""
        width = self.slider_mw.value()
        self.label_mw.setText(f"  &Mouse line width: {width}")
        self.canvas.set_mouse_line_width(width)
        self.canvas.dfb.draw_mouse_line()

    def changed_mouse_line_length(self):
        """Updates the mouse line length according to the slider."""
        length = self.slider_ml.value()
        self.label_ml.setText(f"  &Mouse line length: {length}")
        self.canvas.set_mouse_line_length(length)
        self.canvas.dfb.draw_mouse_line()

    def checked_mouseLine(self):
        """Turns the mouse line on and off."""
        self.canvas.dfb.drawing_mouse_line = not self.canvas.dfb.drawing_mouse_line
        if self.mouseLine.isChecked():
            self.canvas.dfb.draw_mouse_line()
        else:
            self.canvas.dfb.remove_mouse_line_from_plot()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Direction Field Visualizer")
    myApp = MyApp()
    main_win = QMainWindow()
    main_win.setCentralWidget(myApp)

    # magic for pyinstaller to find the icon
    if getattr(sys, "frozen", False):
        icon = os.path.join(sys._MEIPASS, "src/icon.ico")
    else:
        icon = "src/icon.ico"

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

    main_win.setWindowIcon(QIcon(icon))
    main_win.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")


if __name__ == "__main__":
    main()
