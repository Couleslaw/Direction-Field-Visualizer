import sys
import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
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
)

from src.canvas import Canvas
from src.direction_field_builder import create_function_from_string, eval_expression
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


class MyApp(QWidget):
    """Creates the GUI using the PyQt5 library."""

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
        self.slider_a.setMinimum(1)
        self.slider_a.setMaximum(20)
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
        self.slider_aw.setMinimum(1)
        self.slider_aw.setMaximum(20)
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
        self.slider_c.setMaximum(15)
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
        self.slider_cp.setMinimum(1)
        self.slider_cp.setMaximum(10)
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

        # create the 'trace line width' slider
        self.slider_w = QSlider(Qt.Orientation.Horizontal)
        self.slider_w.setMinimum(1)
        self.slider_w.setMaximum(10)
        self.slider_w.setValue(DEFAULT_TRACE_LINES_WIDTH)
        self.slider_w.setMinimumWidth(150)
        self.slider_w.setTickInterval(1)
        self.slider_w.setSingleStep(1)
        self.slider_w.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_w.valueChanged.connect(self.changed_trace_lines_width)
        self.label_w = QLabel()
        self.label_w.setText(f"  &Trace line width: {DEFAULT_TRACE_LINES_WIDTH}   ")
        self.label_w.setBuddy(
            self.slider_w
        )  # changes focus to the slider if 'Alt+t' is pressed
        form = QVBoxLayout()
        form.addWidget(self.label_w)
        form.addWidget(self.slider_w)
        self.sidebarLayout.addLayout(form)

        layout = QHBoxLayout()
        # create the 'Auto trace dx' checkbox
        self.autoTrace = QCheckBox("Auto trace dx")
        self.autoTrace.setChecked(True)
        self.autoTrace.stateChanged.connect(self.checked_autoTrace)
        self.sidebarLayout.addWidget(self.autoTrace)
        layout.addWidget(self.autoTrace)
        # add button for specifying x and y coordinates of the start point
        self.trace_point_button = QPushButton("Trace point")
        self.trace_point_button.clicked.connect(self.clicked_trace_point_button)
        self.trace_point_button.setShortcut("Ctrl+T")
        layout.addWidget(self.trace_point_button)
        self.sidebarLayout.addLayout(layout)

        # create the 'trace dx' input line
        self.trace_dx_input = QLineEdit()
        self.trace_dx_input.setEnabled(False)
        self.trace_dx_input.setText(str(self.canvas.dfb.get_auto_dx()))
        self.trace_dx_input.textChanged.connect(self.update_trace_dx)
        form = QFormLayout()
        form.addRow(
            "  dx:", self.trace_dx_input
        )  # spaces at the beginning are for additional padding
        self.sidebarLayout.addLayout(form)

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

    def checked_autoTrace(self, checked):
        """Turns automatic trace dx on and off"""
        self.canvas.dfb.auto_trace_dx = not self.canvas.dfb.auto_trace_dx
        self.trace_dx_input.setEnabled(not checked)
        self.update_displayed_trace_dx()

    def checked_grid(self, checked):
        self.canvas.set_grid_enabled(checked)

    def checked_axes(self, checked):
        self.canvas.set_axes_enabled(checked)

    def update_trace_dx(self):
        """Updates trace dx according to the dx input line"""
        dx = self.trace_dx_input.text()
        try:
            dx = float(dx)
            if dx <= 0:
                return
            if dx < MIN_TRACE_DX:
                dx = MIN_TRACE_DX
                self.trace_dx_input.setText(str(dx))
        except ValueError:  # don't change anything if the input is not valid
            return
        dx = max(dx, MIN_TRACE_DX)
        self.canvas.set_trace_lines_dx(dx)

    def update_displayed_trace_dx(self):
        """Sets trace dx to the one given"""
        dx = self.canvas.dfb.get_auto_dx()
        self.trace_dx_input.setText(f"{dx:.10f}")

    def clicked_trace_point_button(self):
        """Opens a dialog to input the x and y coordinates of the start point."""
        dialog = CoordinateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            x, y = dialog.get_coordinates()
            try:
                x = float(eval_expression(x))
                y = float(eval_expression(y))
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
        if num_arrows > MAX_NUM_ARROWS:
            num_arrows = MAX_NUM_ARROWS
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

    def changed_trace_lines_width(self):
        """Updates the trace lines width according to the slider."""
        width = self.slider_w.value()
        self.label_w.setText(f"  &Trace lines width: {width}")
        self.canvas.set_trace_lines_width(width)

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

    main_win.setWindowIcon(QIcon(icon))
    main_win.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")


if __name__ == "__main__":
    main()
