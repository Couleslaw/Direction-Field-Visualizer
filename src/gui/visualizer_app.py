import numpy as np
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt
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
    QSpacerItem,
    QSizePolicy,
    QFileDialog,
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QGridLayout,
)

from src.gui.tracing_dialogs import CoordinateDialog, TraceSettingsDialog
from src.gui.lock_button import LockButton
from src.gui.stop_button import StopButton
from src.canvas import Canvas
from src.default_constants import *

from typing import override


class VisualizerApp(QWidget):
    """Creates the GUI using the PyQt6 library."""

    equal_axes = True  # True if the 'Equal axes' checkbox is checked

    def __init__(self):
        super().__init__()

        # call open_wiki function on F1 press

        appLayout = QHBoxLayout()
        self.setLayout(appLayout)

        # main layout = graph + bar bellow it
        main_layout = QVBoxLayout()
        appLayout.addLayout(main_layout)
        self.create_canvas(main_layout)

        # create the bot bar
        bot_bar = QWidget()
        bot_bar_layout = QHBoxLayout()
        bot_bar.setLayout(bot_bar_layout)
        self.create_bot_bar(bot_bar_layout)
        main_layout.addWidget(bot_bar)

        # create the sidebar
        sidebar = QWidget()
        appLayout.addWidget(sidebar)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar.setLayout(sidebar_layout)
        sidebar.setMaximumWidth(200)
        self.create_sidebar(sidebar_layout)

    def stop_background_threads(self):
        """Closes all threads."""
        self.canvas.manager.stop_all_threads()

    def open_reset_plot_dialog(self):
        """Opens a dialog to reset the plot and erase all traced curves."""

        if self.canvas.manager.plot_is_empty:
            return

        reply = QMessageBox.question(
            self,
            "Message",
            "Are you sure you want to erase all traced curves?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.canvas.redraw()

    @override
    def keyPressEvent(self, a0: QKeyEvent | None):
        """
        Stops tracing when pressing Esc
        Redraws the plot when pressing Ctrl+R
        Zoom in and out when pressing Ctrl + and Ctrl -
        """

        # the argument is not called 'event' because the function being overridden has a different signature
        if (event := a0) is None:
            return

        super().keyPressEvent(event)

        if event.key() == Qt.Key.Key_Escape:
            self.canvas.stop_tracing()
            return

        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_R:
                self.open_reset_plot_dialog()
                return

        # Get the physical key's scan code (independent of layout)
        scan_code = event.nativeScanCode()

        MINUS_KEY = 12
        PLUS_KEY = 13

        if scan_code == MINUS_KEY:
            self.canvas.zoom(zoom_in=False)
        elif scan_code == PLUS_KEY:
            self.canvas.zoom(zoom_in=True)

    def create_canvas(self, layout):
        """Creates the canvas for the graph and overlay buttons."""

        container = QWidget(self)
        container_layout = QGridLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # create the matplotlib graph
        self.canvas = Canvas(self)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        container_layout.addWidget(self.canvas)

        overlay_layout = QHBoxLayout()

        # add lock button to overlay
        self.lock_button = LockButton(self)
        self.lock_button.setState(LockButton.LockState.Unlocked)
        self.lock_button.setShortcut("Ctrl+L")
        self.lock_button.clicked.connect(self.clicked_lock_canvas_button)
        overlay_layout.addWidget(self.lock_button)

        # add space
        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        overlay_layout.addItem(spacer)

        # add 'stop tracing' button to overlay
        self.stop_tracing_button = StopButton(self)
        self.stop_tracing_button.setVisible(False)
        self.stop_tracing_button.setToolTip(
            "Stop tracing (Esc)"
        )  # ESC handled in keyPressEvent
        self.stop_tracing_button.clicked.connect(self.canvas.stop_tracing)
        overlay_layout.addWidget(self.stop_tracing_button)

        # add overlay to container
        container_layout.addLayout(overlay_layout, 0, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(container)

    def clicked_lock_canvas_button(self):
        """Locks the canvas if it is unlocked and vice versa."""
        self.canvas.lock_canvas(not self.canvas.manager.canvas_locked)

    def show_stop_tracing_button(self):
        """Shows the stop tracing button."""
        self.stop_tracing_button.setVisible(True)

    def hide_stop_tracing_button(self):
        """Hides the stop tracing button."""
        self.stop_tracing_button.setVisible(False)

    def create_bot_bar(self, layout):
        """
        Creates the bot bar
            - y and x limits input lines
            - Equal-axes, grid-lines and axes-lines checkboxes
            - Center x and y buttons
        """

        # create the 'Equal axes' checkbox
        self.equalAxes = QCheckBox("Equal axes")
        self.equalAxes.setToolTip(
            "If checked, the x and y axes will have the same scale.\nUncheck for manual control."
        )
        self.equalAxes.stateChanged.connect(self.checked_equalAxes)
        layout.addWidget(self.equalAxes)

        # create the 'x min' input line
        self.xmin_input = QLineEdit()
        self.xmin_input.setMinimumWidth(10)

        self.xmin_input.setText(str(DEFAULT_XMIN))
        self.xmin_input.textChanged.connect(self.update_xmin)
        form = QFormLayout()
        form.addRow(
            "x min:", self.xmin_input
        )  # spaces at the beginning are for additional padding
        layout.addLayout(form)

        # create the 'x max' input line
        self.xmax_input = QLineEdit()
        self.xmax_input.setMinimumWidth(10)
        self.xmax_input.setText(str(DEFAULT_XMAX))
        self.xmax_input.textChanged.connect(self.update_xmax)
        form = QFormLayout()
        form.addRow(
            "x max:", self.xmax_input
        )  # spaces at the beginning are for additional padding
        layout.addLayout(form)

        # create the 'y min' input line
        self.ymin_input = QLineEdit()
        self.ymin_input.setMinimumWidth(10)
        self.ymin_input.setText(str(DEFAULT_YMIN))
        self.ymin_input.textChanged.connect(self.update_ymin)
        form = QFormLayout()
        form.addRow(
            "y min:", self.ymin_input
        )  # spaces at the beginning are for additional padding
        layout.addLayout(form)

        # create the 'y max' input line
        self.ymax_input = QLineEdit()
        self.ymax_input.setMinimumWidth(10)
        self.ymax_input.setText(str(DEFAULT_YMAX))
        self.ymax_input.textChanged.connect(self.update_ymax)
        form = QFormLayout()
        form.addRow(
            "y max:", self.ymax_input
        )  # spaces at the beginning are for additional padding
        layout.addLayout(form)

        self.equalAxes.setChecked(VisualizerApp.equal_axes)

        # create the 'center x' button
        self.center_x_button = QPushButton("Center &X")
        self.center_x_button.setToolTip("Center the plot on the x-axis.\nShortcut 'Alt+X'")
        self.center_x_button.clicked.connect(self.canvas.centralize_plot_x)
        self.center_x_button.setShortcut("Alt+X")
        layout.addWidget(self.center_x_button)

        # create the 'center y' button
        self.center_y_button = QPushButton("Center &Y")
        self.center_y_button.setToolTip("Center the plot on the y-axis.\nShortcut 'Alt+Y'")
        self.center_y_button.clicked.connect(self.canvas.centralize_plot_y)
        self.center_y_button.setShortcut("Alt+Y")
        layout.addWidget(self.center_y_button)

        # create the 'Grid' checkbox
        self.gridCheckBox = QCheckBox("Grid")
        self.gridCheckBox.setToolTip("Turn grid lines on and off.")
        self.gridCheckBox.setChecked(False)
        self.gridCheckBox.stateChanged.connect(self.checked_grid)
        layout.addWidget(self.gridCheckBox)

        # create the 'Axes' checkbox
        self.axesCheckBox = QCheckBox("Axes")
        self.axesCheckBox.setToolTip("Turn axes lines on and off.")
        self.axesCheckBox.setChecked(True)
        self.axesCheckBox.stateChanged.connect(self.checked_axes)
        layout.addWidget(self.axesCheckBox)

    def create_sidebar(self, layout):
        """
        Creates the sidebar
            - function input line
            - graph-function, save-image, trace-settings, trace-point buttons
            - arrow / direction field settings
            - color settings
            - mouse line settings
        """

        # create the function input line and graph button
        self.function_input = QLineEdit()
        self.function_input.setPlaceholderText("Enter a function")
        self.function_input.setText(str(DEFAULT_FUNCTION))
        form = QFormLayout()
        form.addRow(
            "  y'(x) =", self.function_input
        )  # spaces at the beginning are for additional padding
        layout.addLayout(form)

        # add space
        spacer = QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        layout.addItem(spacer)

        graphLayout = QHBoxLayout()
        self.graph_button = QPushButton("Graph")
        self.graph_button.setToolTip("Graph the above entered function.\nShortcut: 'Enter'")
        self.graph_button.clicked.connect(self.execute_graph_function)
        self.graph_button.setShortcut("Return")
        graphLayout.addWidget(self.graph_button)

        # create the 'save image' button
        self.save_button = QPushButton("&Save image")
        self.save_button.setToolTip("Export the figure as PNG/SVG/PDF.\nShortcut: 'Ctrl+S'")
        self.save_button.clicked.connect(self.show_save_file_dialog)
        self.save_button.setShortcut("Ctrl+S")
        graphLayout.addWidget(self.save_button)
        layout.addLayout(graphLayout)

        traceLayout = QHBoxLayout()
        # create the 'trace settings' button
        self.trace_settings_button = QPushButton("&Trace settings")
        self.trace_settings_button.setToolTip(
            """Open solution tracing settings. A solution can be traced by 
- right-clicking on the graph
- clicking on the 'Trace point' to specify an initial value
Shortcut: 'Ctrl+T'"""
        )
        self.trace_settings_button.clicked.connect(self.show_trace_settings_dialog)
        self.trace_settings_button.setShortcut("Ctrl+T")
        traceLayout.addWidget(self.trace_settings_button)
        # add button for specifying x and y coordinates of the start point
        self.trace_point_button = QPushButton("Trace &point")
        self.trace_point_button.setToolTip(
            "Trace a solution from a given initial value. You can also just right-click on the graph.<br>Shortcut: 'Ctrl+P'"
        )
        self.trace_point_button.clicked.connect(self.clicked_trace_point_button)
        self.trace_point_button.setShortcut("Ctrl+P")
        traceLayout.addWidget(self.trace_point_button)
        layout.addLayout(traceLayout)

        # add space
        layout.addItem(spacer)

        # arrow settings
        arrow_group = QGroupBox("Direction Field Settings")
        arrow_layout = QVBoxLayout()
        arrow_group.setLayout(arrow_layout)

        # create the 'num arrows' input line and buttons
        self.num_arrows_input = QLineEdit()
        self.num_arrows_input.setText(str(DEFAULT_NUM_ARROWS))
        self.num_arrows_input.textChanged.connect(self.update_num_arrows)
        form = QFormLayout()
        num_arrows_label = QLabel("  Number of arrows:")  # spaces for padding
        num_arrows_label.setToolTip("Number of arrows in the x-direction.")
        form.addRow(num_arrows_label, self.num_arrows_input)

        self.plus_arrows = QPushButton("+")
        self.plus_arrows.setToolTip("Add 5 arrows.\nShortcut: 'Alt+right'")
        self.plus_arrows.clicked.connect(self.add_more_arrows)
        self.plus_arrows.setShortcut("Alt+right")
        self.minus_arrows = QPushButton("-")
        self.minus_arrows.setToolTip("Remove 5 arrows.\nShortcut: 'Alt+left'")
        self.minus_arrows.clicked.connect(self.remove_some_arrows)
        self.minus_arrows.setShortcut("Alt+left")

        arrow_buttons_layout = QHBoxLayout()
        arrow_buttons_layout.addWidget(self.minus_arrows)
        arrow_buttons_layout.addWidget(self.plus_arrows)

        arrow_layout.addLayout(form)
        arrow_layout.addLayout(arrow_buttons_layout)

        # create the 'arrow length' slider
        self.slider_a = QSlider(Qt.Orientation.Horizontal)
        self.slider_a.setMinimum(MIN_ARROW_LENGTH)
        self.slider_a.setMaximum(MAX_ARROW_LENGTH)
        self.slider_a.setValue(DEFAULT_ARROW_LENGTH)
        self.slider_a.setMinimumSize(150, 10)
        self.slider_a.setTickInterval(2)
        self.slider_a.setSingleStep(1)
        self.slider_a.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_a.valueChanged.connect(self.changed_arrow_length)
        self.label_a = QLabel()
        self.label_a.setText(f"  &Arrow length: {DEFAULT_ARROW_LENGTH}   ")
        self.label_a.setMinimumHeight(15)
        self.label_a.setBuddy(
            self.slider_a
        )  # changes focus to the slider if 'Alt+a' is pressed
        form = QVBoxLayout()
        form.addWidget(self.label_a)
        form.addWidget(self.slider_a)
        arrow_layout.addLayout(form)

        # create the 'arrow width' slider
        self.slider_aw = QSlider(Qt.Orientation.Horizontal)
        self.slider_aw.setMinimum(MIN_ARROW_WIDTH)
        self.slider_aw.setMaximum(MAX_ARROW_WIDTH)
        self.slider_aw.setValue(DEFAULT_ARROW_WIDTH)
        self.slider_aw.setMinimumSize(150, 10)
        self.slider_aw.setTickInterval(2)
        self.slider_aw.setSingleStep(1)
        self.slider_aw.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_aw.valueChanged.connect(self.changed_arrow_width)
        self.label_aw = QLabel()
        self.label_aw.setMinimumHeight(15)
        self.label_aw.setText(f"  &Arrow width: {DEFAULT_ARROW_WIDTH}   ")
        self.label_aw.setBuddy(
            self.slider_aw
        )  # changes focus to the slider if 'Alt+a' is pressed
        form = QVBoxLayout()
        form.addWidget(self.label_aw)
        form.addWidget(self.slider_aw)
        arrow_layout.addLayout(form)

        layout.addWidget(arrow_group)

        # add some spacing
        layout.addItem(spacer)

        # color settings group
        color_group = QGroupBox("Color Settings")
        color_layout = QVBoxLayout()
        color_group.setLayout(color_layout)

        # create the 'Color by curvature' checkbox
        self.colors = QCheckBox("&Color by curvature")
        self.colors.setToolTip(
            "Toggle on to color the arrows according to the curvature of the function.\nShortcut: 'Ctrl+C'"
        )
        self.colors.setChecked(True)
        self.colors.setShortcut("Ctrl+C")
        self.colors.stateChanged.connect(self.checked_color)
        color_layout.addWidget(self.colors)

        # create the 'color contrast' slider
        self.slider_c = QSlider(Qt.Orientation.Horizontal)
        self.slider_c.setMinimum(MIN_COLOR_CONTRAST)
        self.slider_c.setMaximum(MAX_COLOR_CONTRAST)
        self.slider_c.setValue(DEFAULT_COLOR_CONTRAST)
        self.slider_c.setMinimumSize(150, 10)
        self.slider_c.setTickInterval(1)
        self.slider_c.setSingleStep(1)
        self.slider_c.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_c.valueChanged.connect(self.changed_color_contrast)
        self.label_c = QLabel()
        self.label_c.setMinimumHeight(15)
        self.label_c.setToolTip(
            "Lower contrast means that even small differences in curvature will be visible."
        )
        self.label_c.setText(f"  &Color contrast: {DEFAULT_COLOR_CONTRAST}   ")
        self.label_c.setBuddy(
            self.slider_c
        )  # changes focus to the slider if 'Alt+c' is pressed
        form = QVBoxLayout()
        form.addWidget(self.label_c)
        form.addWidget(self.slider_c)
        color_layout.addLayout(form)

        # create the 'color precision' slider
        self.slider_cp = QSlider(Qt.Orientation.Horizontal)
        self.slider_cp.setMinimum(MIN_COLOR_PRECISION)
        self.slider_cp.setMaximum(MAX_COLOR_PRECISION)
        self.slider_cp.setValue(DEFAULT_COLOR_PRECISION)
        self.slider_cp.setMinimumSize(150, 10)
        self.slider_cp.setTickInterval(1)
        self.slider_cp.setSingleStep(1)
        self.slider_cp.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_cp.valueChanged.connect(self.updated_color_precision)
        self.label_cp = QLabel()
        self.label_cp.setMinimumHeight(15)
        self.label_cp.setToolTip(
            "Determines the dx used for calculating curvature. See the <b>User Guide</b> (press <b>F1</b>) for more information."
        )
        self.label_cp.setText(f"  &Color precision: {DEFAULT_COLOR_PRECISION}   ")
        self.label_cp.setBuddy(self.slider_cp)
        form = QVBoxLayout()
        form.addWidget(self.label_cp)
        form.addWidget(self.slider_cp)
        color_layout.addLayout(form)

        # create color map dropdown list
        self.color_map = QComboBox()
        self.color_map.setToolTip("Chose a color map.")
        for color_map in AVAILABLE_COLOR_MAPS:
            self.color_map.addItem(color_map)
        self.color_map.setCurrentText(DEFAULT_COLOR_MAP)
        self.color_map.currentTextChanged.connect(self.canvas.set_color_map)
        color_layout.addWidget(self.color_map)

        layout.addWidget(color_group)

        # add some spacing
        layout.addItem(spacer)

        # mouse line settings group
        mouse_line_group = QGroupBox("Mouse Line Settings")
        mouse_line_layout = QVBoxLayout()
        mouse_line_group.setLayout(mouse_line_layout)

        # create the 'Mouse line' checkbox
        self.mouseLine = QCheckBox("&Mouse line")
        self.mouseLine.setToolTip(
            "Draw a tangent line at the position of the mouse cursor.\nShortcut: 'Ctrl+M'"
        )
        self.mouseLine.stateChanged.connect(self.checked_mouseLine)
        self.mouseLine.setChecked(False)
        self.mouseLine.setShortcut("Ctrl+M")
        mouse_line_layout.addWidget(self.mouseLine)

        # create the 'Mouse line length' slider
        self.slider_ml = QSlider(Qt.Orientation.Horizontal)
        self.slider_ml.setMinimum(MIN_MOUSE_LINE_LENGTH)
        self.slider_ml.setMaximum(MAX_MOUSE_LINE_LENGTH)
        self.slider_ml.setValue(DEFAULT_MOUSE_LINE_LENGTH)
        self.slider_ml.setMinimumSize(150, 10)
        self.slider_ml.setTickInterval(1)
        self.slider_ml.setSingleStep(1)
        self.slider_ml.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_ml.valueChanged.connect(self.changed_mouse_line_length)
        self.label_ml = QLabel()
        self.label_ml.setMinimumHeight(15)
        self.label_ml.setText(f"  &Mouse line length: {DEFAULT_MOUSE_LINE_LENGTH}   ")
        self.label_ml.setBuddy(
            self.slider_ml
        )  # changes focus to the slider if 'Alt+m' is pressed
        form = QVBoxLayout()
        form.addWidget(self.label_ml)
        form.addWidget(self.slider_ml)
        mouse_line_layout.addLayout(form)

        # create the 'Mouse line width' slider
        self.slider_mw = QSlider(Qt.Orientation.Horizontal)
        self.slider_mw.setMinimum(MIN_MOUSE_LINE_WIDTH)
        self.slider_mw.setMaximum(MAX_MOUSE_LINE_WIDTH)
        self.slider_mw.setValue(DEFAULT_MOUSE_LINE_WIDTH)
        self.slider_mw.setMinimumSize(150, 10)
        self.slider_mw.setTickInterval(1)
        self.slider_mw.setSingleStep(1)
        self.slider_mw.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_mw.valueChanged.connect(self.changed_mouse_line_width)
        self.label_mw = QLabel()
        self.label_mw.setMinimumHeight(15)
        self.label_mw.setText(f"  &Mouse line width: {DEFAULT_MOUSE_LINE_WIDTH}   ")
        self.label_mw.setBuddy(
            self.slider_mw
        )  # changes focus to the slider if 'Alt+m' is pressed
        form = QVBoxLayout()
        form.addWidget(self.label_mw)
        form.addWidget(self.slider_mw)
        mouse_line_layout.addLayout(form)

        layout.addWidget(mouse_line_group)

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
        """Plots the function given in the function input line."""

        func_str = self.function_input.text()
        if not self.canvas.set_new_function(func_str):
            QMessageBox.critical(self, "Error", f"Invalid function.")

    def checked_equalAxes(self, checked):
        """Turns equal_axes on and off."""
        VisualizerApp.equal_axes = not VisualizerApp.equal_axes
        if checked:
            self.canvas.set_equal_axes()
            self.enable_input_lines(False)
        else:
            self.canvas.set_auto_axes()
            self.enable_input_lines(True)
            self.update_xmin()
            self.update_xmax()
            self.update_ymin()
            self.update_ymax()

    def enable_input_lines(self, enabled):
        """Enables or disables all of the input lines for x and y limits."""
        self.xmin_input.setEnabled(enabled)
        self.xmax_input.setEnabled(enabled)
        self.ymin_input.setEnabled(enabled)
        self.ymax_input.setEnabled(enabled)

    def checked_color(self, checked):
        """Turns color on and off."""
        self.canvas.set_show_field_colors(checked)

    def changed_color_contrast(self):
        """Updates the color contrast according to the slider."""
        color_contrast = self.slider_c.value()
        self.label_c.setText(f"  &Color contrast: {color_contrast}")
        self.canvas.set_color_contrast(color_contrast)

    def updated_color_precision(self):
        """Updates the color precision according to the slider."""
        color_precision = self.slider_cp.value()
        self.label_cp.setText(f"  &Color precision: {color_precision}")
        self.canvas.set_color_precision(color_precision)

    def checked_grid(self, checked):
        """Turns grid lines on and off."""
        self.canvas.set_grid_enabled(checked)

    def checked_axes(self, checked):
        """Turns axes lines on and off."""
        self.canvas.set_axes_enabled(checked)

    def clicked_trace_point_button(self):
        """Opens a dialog to input the x and y coordinates of the start point."""
        dialog = CoordinateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            x, y = dialog.get_coordinates()
            try:
                x = float(eval(x))
                y = float(eval(y))
                xlim = self.canvas.xlim
                ylim = self.canvas.ylim
                if x < xlim[0] or x > xlim[1]:
                    QMessageBox.warning(self, "Warning", "X is out of bounds, not tracing.")
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
                self.canvas.manager.trace_from_point(x, y)
            except Exception:
                QMessageBox.critical(self, "Error", f"Invalid coordinates.")

    def show_trace_settings_dialog(self):
        """Opens a dialog to set the trace settings."""
        new_settings = self.canvas.manager.trace_settings.copy()
        dialog = TraceSettingsDialog(
            self,
            new_settings,
            self.canvas.manager.field_settings.function_string,
            self.canvas.xlim,
            self.canvas.ylim,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.canvas.manager.trace_settings = new_settings

    def update_xmin(self):
        """Updates xmin according to the xmin input line."""
        xmin = self.xmin_input.text()
        try:
            xmin = float(xmin)
        except ValueError:  # don't change anything if the input is not valid
            return
        xlim = self.canvas.xlim
        if xmin == round(xlim[0], ROUND_INPUT_LINES) or xmin >= xlim[1]:
            return
        self.canvas.xlim = (xmin, xlim[1])

    def update_xmax(self):
        """Updates xmax according to the xmax input line."""
        xmax = self.xmax_input.text()
        try:
            xmax = float(xmax)
        except ValueError:  # don't change anything if the input is not valid
            return
        xlim = self.canvas.xlim
        if xmax == round(xlim[1], ROUND_INPUT_LINES) or xmax <= xlim[0]:
            return
        self.canvas.xlim = (xlim[0], xmax)

    def update_ymin(self):
        """Updates ymin according to the ymin input line."""
        ymin = self.ymin_input.text()
        try:
            ymin = float(ymin)
        except ValueError:  # don't change anything if the input is not valid
            return
        ylim = self.canvas.ylim
        if ymin == round(ylim[0], ROUND_INPUT_LINES) or ymin >= ylim[1]:
            return
        self.canvas.ylim = (ymin, ylim[1])

    def update_ymax(self):
        """Updates ymax according to the ymax input line."""
        ymax = self.ymax_input.text()
        try:
            ymax = float(ymax)
        except ValueError:  # don't change anything if the input is not valid
            return
        ylim = self.canvas.ylim
        if ymax == round(ylim[1], ROUND_INPUT_LINES) or ymax <= ylim[0]:
            return
        self.canvas.ylim = (ylim[0], ymax)

    def update_displayed_lims(self):
        """Updates all displayed lims according to actual lims."""
        (xmin, xmax), (ymin, ymax) = self.canvas.xlim, self.canvas.ylim
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

    def add_more_arrows(self):
        """Adds 5 arrows."""
        self.num_arrows_input.setText(str(int(self.num_arrows_input.text()) + 5))

    def remove_some_arrows(self):
        """Removes 5 arrows."""
        self.num_arrows_input.setText(str(int(self.num_arrows_input.text()) - 5))

    def changed_arrow_length(self):
        """Updates the arrow length according to the slider."""
        arrow_length = self.slider_a.value()
        self.label_a.setText(f"  &Arrow length: {arrow_length}")
        self.canvas.set_arrow_length(arrow_length)

    def changed_arrow_width(self):
        """Updates the arrow width according to the slider."""
        arrow_width = self.slider_aw.value()
        self.label_aw.setText(f"  &Arrow width: {arrow_width}")
        self.canvas.set_arrow_width(arrow_width)

    def changed_mouse_line_width(self):
        """Updates the mouse line width according to the slider."""
        width = self.slider_mw.value()
        self.label_mw.setText(f"  &Mouse line width: {width}")
        self.canvas.set_mouse_line_width(width)

    def changed_mouse_line_length(self):
        """Updates the mouse line length according to the slider."""
        length = self.slider_ml.value()
        self.label_ml.setText(f"  &Mouse line length: {length}")
        self.canvas.set_mouse_line_length(length)

    def checked_mouseLine(self, checked):
        """Turns the mouse line on and off."""
        self.canvas.set_drawing_mouse_line(checked)

    def enable_trace_settings_button(self, enabled):
        """Enables or disables the trace settings button."""
        self.trace_settings_button.setEnabled(enabled)
