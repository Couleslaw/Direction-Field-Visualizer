import numpy as np
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
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
from src.gui.component_builder import QtComponentBuilder
from src.canvas import Canvas
from src.default_constants import *
from src.math_functions import try_get_value_from_string

from typing import override


class VisualizerApp(QWidget):
    """Creates the GUI using the PyQt6 library."""

    def __init__(self) -> None:
        super().__init__()

        # call open_wiki function on F1 press

        appLayout = QHBoxLayout()
        self.setLayout(appLayout)

        # main layout = graph + bar bellow it
        main_layout = QVBoxLayout()
        appLayout.addLayout(main_layout)
        self.__create_canvas(main_layout)

        # create the bot bar
        bot_bar = QWidget()
        bot_bar_layout = QHBoxLayout()
        bot_bar.setLayout(bot_bar_layout)
        self.__create_bot_bar(bot_bar_layout)
        main_layout.addWidget(bot_bar)

        # create the sidebar
        sidebar = QWidget()
        appLayout.addWidget(sidebar)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar.setLayout(sidebar_layout)
        sidebar.setMaximumWidth(200)
        self.__create_sidebar(sidebar_layout)

    def stop_background_threads(self) -> None:
        """Closes all threads."""
        self.__canvas.manager.stop_all_threads()

    def __open_reset_plot_dialog(self) -> None:
        """Opens a dialog to reset the plot and erase all traced curves."""

        if self.__canvas.manager.plot_is_empty:
            return

        reply = QMessageBox.question(
            self,
            "Message",
            "Are you sure you want to erase all traced curves?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.__canvas.redraw()

    @override
    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
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
            self.__canvas.stop_tracing()
            return

        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_R:
                self.__open_reset_plot_dialog()
                return

        # Get the physical key's scan code (independent of keyboard layout)
        scan_code = event.nativeScanCode()

        MINUS_KEY = 12
        PLUS_KEY = 13

        if scan_code == MINUS_KEY:
            self.__canvas.zoom(zoom_in=False)
        elif scan_code == PLUS_KEY:
            self.__canvas.zoom(zoom_in=True)

    def __create_canvas(self, layout: QVBoxLayout | QHBoxLayout) -> None:
        """Creates the canvas for the graph and overlay buttons."""

        container = QWidget(self)
        container_layout = QGridLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # create the matplotlib graph
        self.__canvas = Canvas(self)
        self.__canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        container_layout.addWidget(self.__canvas)

        overlay_layout = QHBoxLayout()

        # add lock button to overlay
        self.__lock_button = LockButton(self)
        self.__lock_button.setShortcut("Ctrl+L")
        self.__lock_button.setState(LockButton.LockState.UNLOCKED)
        self.__lock_button.clicked.connect(self.__clicked_lock_canvas_button)
        overlay_layout.addWidget(self.__lock_button)

        # add space
        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        overlay_layout.addItem(spacer)

        # add 'stop tracing' button to overlay
        self.__stop_tracing_button = StopButton(self)
        self.__stop_tracing_button.setVisible(False)
        self.__stop_tracing_button.setToolTip("Stop tracing (Esc)")  # ESC handled in keyPressEvent
        self.__stop_tracing_button.clicked.connect(self.__canvas.stop_tracing)
        overlay_layout.addWidget(self.__stop_tracing_button)

        # add overlay to container
        container_layout.addLayout(overlay_layout, 0, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(container)

    def __clicked_lock_canvas_button(self) -> None:
        """Locks the canvas if it is unlocked and vice versa."""
        self.__canvas.lock_canvas(not self.__canvas.manager.canvas_locked)

    def show_stop_tracing_button(self) -> None:
        """Shows the stop tracing button."""
        self.__stop_tracing_button.setVisible(True)

    def hide_stop_tracing_button(self) -> None:
        """Hides the stop tracing button."""
        self.__stop_tracing_button.setVisible(False)

    def __create_bot_bar(self, layout: QVBoxLayout | QHBoxLayout) -> None:
        """
        Creates the bot bar
            - y and x limits input lines
            - Equal-axes, grid-lines and axes-lines checkboxes
            - Center x and y buttons
        """

        # create the 'Equal axes' checkbox
        self.__equalAxes = QCheckBox("Equal axes")
        self.__equalAxes.setToolTip(
            "If checked, the x and y axes will have the same scale.\nUncheck for manual control."
        )
        self.__equalAxes.stateChanged.connect(self.__checked_equalAxes)
        layout.addWidget(self.__equalAxes)

        # create the 'x min' input line
        self.__xmin_input, _ = QtComponentBuilder.add_line_edit_with_label(
            default_text=str(DEFAULT_XMIN),
            label_text="x min:",
            on_text_changed=self.__update_xmin,
            layout=layout,
        )

        # create the 'x max' input line
        self.__xmax_input, _ = QtComponentBuilder.add_line_edit_with_label(
            default_text=str(DEFAULT_XMAX),
            label_text="x max:",
            on_text_changed=self.__update_xmax,
            layout=layout,
        )

        # create the 'y min' input line
        self.__ymin_input, _ = QtComponentBuilder.add_line_edit_with_label(
            default_text=str(DEFAULT_YMIN),
            label_text="y min:",
            on_text_changed=self.__update_ymin,
            layout=layout,
        )

        # create the 'y max' input line
        self.__ymax_input, _ = QtComponentBuilder.add_line_edit_with_label(
            default_text=str(DEFAULT_YMAX),
            label_text="y max:",
            on_text_changed=self.__update_ymax,
            layout=layout,
        )

        self.__equalAxes.setChecked(True)

        # create the 'center x' button
        self.__center_x_button = QPushButton("Center &X")
        self.__center_x_button.setToolTip("Center the plot on the x-axis.\nShortcut 'Alt+X'")
        self.__center_x_button.clicked.connect(self.__canvas.centralize_plot_x)
        self.__center_x_button.setShortcut("Alt+X")
        layout.addWidget(self.__center_x_button)

        # create the 'center y' button
        self.__center_y_button = QPushButton("Center &Y")
        self.__center_y_button.setToolTip("Center the plot on the y-axis.\nShortcut 'Alt+Y'")
        self.__center_y_button.clicked.connect(self.__canvas.centralize_plot_y)
        self.__center_y_button.setShortcut("Alt+Y")
        layout.addWidget(self.__center_y_button)

        # create the 'Grid' checkbox
        self.__gridCheckBox = QCheckBox("Grid")
        self.__gridCheckBox.setToolTip("Turn grid lines on and off.")
        self.__gridCheckBox.setChecked(False)
        self.__gridCheckBox.stateChanged.connect(self.__checked_grid)
        layout.addWidget(self.__gridCheckBox)

        # create the 'Axes' checkbox
        self.__axesCheckBox = QCheckBox("Axes")
        self.__axesCheckBox.setToolTip("Turn axes lines on and off.")
        self.__axesCheckBox.setChecked(True)
        self.__axesCheckBox.stateChanged.connect(self.__checked_axes)
        layout.addWidget(self.__axesCheckBox)

    def __create_sidebar(self, layout: QVBoxLayout | QHBoxLayout) -> None:
        """
        Creates the sidebar
            - function input line
            - graph-function, save-image, trace-settings, trace-point buttons
            - arrow / direction field settings
            - color settings
            - mouse line settings
        """

        # create the function input line and graph button
        self.__function_input = QLineEdit()
        self.__function_input.setPlaceholderText("Enter a function")
        self.__function_input.setText(str(DEFAULT_FUNCTION))
        form = QFormLayout()
        form.addRow(
            "  y'(x) =", self.__function_input
        )  # spaces at the beginning are for additional padding
        layout.addLayout(form)

        # add space
        spacer = QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        layout.addItem(spacer)

        graphLayout = QHBoxLayout()
        self.__graph_button = QPushButton("Graph")
        self.__graph_button.setToolTip("Graph the above entered function.\nShortcut: 'Enter'")
        self.__graph_button.clicked.connect(self.__execute_graph_function)
        self.__graph_button.setShortcut("Return")
        graphLayout.addWidget(self.__graph_button)

        # create the 'save image' button
        self.__save_button = QPushButton("&Save image")
        self.__save_button.setToolTip("Export the figure as PNG/SVG/PDF.\nShortcut: 'Ctrl+S'")
        self.__save_button.clicked.connect(self.__show_save_file_dialog)
        self.__save_button.setShortcut("Ctrl+S")
        graphLayout.addWidget(self.__save_button)
        layout.addLayout(graphLayout)

        traceLayout = QHBoxLayout()

        # create the 'trace settings' button
        self.__trace_settings_button = QPushButton("&Trace settings")
        self.__trace_settings_button.setToolTip(
            """Open solution tracing settings. A solution can be traced by 
- right-clicking on the graph
- clicking on the 'Trace point' to specify an initial value
Shortcut: 'Ctrl+T'"""
        )
        self.__trace_settings_button.clicked.connect(self.__show_trace_settings_dialog)
        self.__trace_settings_button.setShortcut("Ctrl+T")
        traceLayout.addWidget(self.__trace_settings_button)

        # add button for specifying x and y coordinates of the start point
        self.__trace_point_button = QPushButton("Trace &point")
        self.__trace_point_button.setToolTip(
            "Trace a solution from a given initial value. You can also just right-click on the graph.<br>Shortcut: 'Ctrl+P'"
        )
        self.__trace_point_button.clicked.connect(self.__clicked_trace_point_button)
        self.__trace_point_button.setShortcut("Ctrl+P")
        traceLayout.addWidget(self.__trace_point_button)
        layout.addLayout(traceLayout)

        # add space
        layout.addItem(spacer)

        # arrow settings
        arrow_group = QGroupBox("Direction Field Settings")
        arrow_layout = QVBoxLayout()
        arrow_group.setLayout(arrow_layout)

        # create the 'num arrows' input line and buttons
        self.__num_arrows_input, _ = QtComponentBuilder.add_line_edit_with_label(
            default_text=str(DEFAULT_NUM_ARROWS),
            label_text="  Number of arrows:",
            on_text_changed=self.__update_num_arrows,
            tooltip="Number of arrows in the x-direction.",
            layout=arrow_layout,
        )

        # '+' arrows button
        plus_arrows = QPushButton("+")
        plus_arrows.setToolTip("Add 5 arrows.\nShortcut: 'Alt+right'")
        plus_arrows.clicked.connect(self.__add_five_arrows)
        plus_arrows.setShortcut("Alt+right")

        # '-' arrows button
        minus_arrows = QPushButton("-")
        minus_arrows.setToolTip("Remove 5 arrows.\nShortcut: 'Alt+left'")
        minus_arrows.clicked.connect(self.__remove_five_arrows)
        minus_arrows.setShortcut("Alt+left")

        # add the buttons to the layout
        arrow_buttons_layout = QHBoxLayout()
        arrow_buttons_layout.addWidget(minus_arrows)
        arrow_buttons_layout.addWidget(plus_arrows)
        arrow_layout.addLayout(arrow_buttons_layout)

        # create the 'arrow length' slider
        self.__slider_al, self.__label_al = QtComponentBuilder.add_slider_with_label(
            min_value=MIN_ARROW_LENGTH,
            max_value=MAX_ARROW_LENGTH,
            default_value=DEFAULT_ARROW_LENGTH,
            tick_interval=2,
            on_value_changed=self.__changed_arrow_length,
            label_text=f"&Arrow length: {DEFAULT_ARROW_LENGTH}",
            layout=arrow_layout,
        )

        # create the 'arrow width' slider
        self.__slider_aw, self.__label_aw = QtComponentBuilder.add_slider_with_label(
            min_value=MIN_ARROW_WIDTH,
            max_value=MAX_ARROW_WIDTH,
            default_value=DEFAULT_ARROW_WIDTH,
            tick_interval=2,
            on_value_changed=self.__changed_arrow_width,
            label_text=f"&Arrow width: {DEFAULT_ARROW_WIDTH}",
            layout=arrow_layout,
        )

        layout.addWidget(arrow_group)

        # add some spacing
        layout.addItem(spacer)

        # color settings group
        color_group = QGroupBox("Color Settings")
        color_layout = QVBoxLayout()
        color_group.setLayout(color_layout)

        # create the 'Color by curvature' checkbox
        self.__colors = QCheckBox("&Color by curvature")
        self.__colors.setToolTip(
            "Toggle on to color the arrows according to the curvature of the function.\nShortcut: 'Ctrl+C'"
        )
        self.__colors.setChecked(True)
        self.__colors.setShortcut("Ctrl+C")
        self.__colors.stateChanged.connect(self.__checked_color)
        color_layout.addWidget(self.__colors)

        # create the 'color contrast' slider
        self.__slider_cc, self.__label_cc = QtComponentBuilder.add_slider_with_label(
            min_value=MIN_COLOR_CONTRAST,
            max_value=MAX_COLOR_CONTRAST,
            default_value=DEFAULT_COLOR_CONTRAST,
            label_text=f"&Color contrast: {DEFAULT_COLOR_CONTRAST}",
            tooltip="Lower contrast means that even small differences in curvature will be visible.",
            on_value_changed=self.__changed_color_contrast,
            layout=color_layout,
        )

        # create the 'color precision' slider
        self.__slider_cp, self.__label_cp = QtComponentBuilder.add_slider_with_label(
            min_value=MIN_COLOR_PRECISION,
            max_value=MAX_COLOR_PRECISION,
            default_value=DEFAULT_COLOR_PRECISION,
            label_text=f"&Color precision: {DEFAULT_COLOR_PRECISION}",
            tooltip="Determines the dx used for calculating curvature. See the <b>User Guide</b> (press <b>F1</b>) for more information.",
            on_value_changed=self.__updated_color_precision,
            layout=color_layout,
        )

        # create color map dropdown list
        self.__color_map = QComboBox()
        self.__color_map.setToolTip("Chose a color map.")
        for color_map in AVAILABLE_COLOR_MAPS:
            self.__color_map.addItem(color_map)
        self.__color_map.setCurrentText(DEFAULT_COLOR_MAP)
        self.__color_map.currentTextChanged.connect(self.__canvas.set_color_map)
        color_layout.addWidget(self.__color_map)

        layout.addWidget(color_group)

        # add some spacing
        layout.addItem(spacer)

        # mouse line settings group
        mouse_line_group = QGroupBox("Mouse Line Settings")
        mouse_line_layout = QVBoxLayout()
        mouse_line_group.setLayout(mouse_line_layout)

        # create the 'Mouse line' checkbox
        self.__mouseLine = QCheckBox("&Mouse line")
        self.__mouseLine.setToolTip(
            "Draw a tangent line at the position of the mouse cursor.\nShortcut: 'Ctrl+M'"
        )
        self.__mouseLine.stateChanged.connect(self.__checked_mouseLine)
        self.__mouseLine.setChecked(False)
        self.__mouseLine.setShortcut("Ctrl+M")
        mouse_line_layout.addWidget(self.__mouseLine)

        # create the 'Mouse line length' slider
        self.__slider_ml, self.__label_ml = QtComponentBuilder.add_slider_with_label(
            min_value=MIN_MOUSE_LINE_LENGTH,
            max_value=MAX_MOUSE_LINE_LENGTH,
            default_value=DEFAULT_MOUSE_LINE_LENGTH,
            label_text=f"&Mouse line length: {DEFAULT_MOUSE_LINE_LENGTH}",
            on_value_changed=self.__changed_mouse_line_length,
            layout=mouse_line_layout,
        )

        # create the 'Mouse line width' slider
        self.__slider_mw, self.__label_mw = QtComponentBuilder.add_slider_with_label(
            min_value=MIN_MOUSE_LINE_WIDTH,
            max_value=MAX_MOUSE_LINE_WIDTH,
            default_value=DEFAULT_MOUSE_LINE_WIDTH,
            label_text=f"&Mouse line width: {DEFAULT_MOUSE_LINE_WIDTH}",
            on_value_changed=self.__changed_mouse_line_width,
            layout=mouse_line_layout,
        )

        layout.addWidget(mouse_line_group)

    def __show_save_file_dialog(self) -> None:
        """Opens a dialog to save the current figure as a png or svg file."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            f"",
            "SVG (*.svg);; PNG (*.png);; PDF (*.pdf);; All Files (*)",
        )
        if file_name:
            self.__canvas.figure.savefig(file_name, bbox_inches="tight")

    def __execute_graph_function(self) -> None:
        """Plots the function given in the function input line and updates the displayed axes limits."""

        func_str = self.__function_input.text()
        if not self.__canvas.set_new_function(func_str):
            QMessageBox.critical(self, "Error", f"Invalid function.")

        self.update_displayed_axes_limits()

    def __checked_equalAxes(self, checked: bool) -> None:
        """Turns equal_axes on and off."""
        if checked:
            self.__canvas.set_equal_axes()
            self.__enable_input_lines(False)
        else:
            self.__canvas.set_auto_axes()
            self.__enable_input_lines(True)

    def __enable_input_lines(self, enabled: bool) -> None:
        """Enables or disables all of the input lines for x and y limits."""
        self.__xmin_input.setEnabled(enabled)
        self.__xmax_input.setEnabled(enabled)
        self.__ymin_input.setEnabled(enabled)
        self.__ymax_input.setEnabled(enabled)

    def __checked_color(self, checked: bool) -> None:
        """Turns color on and off."""
        self.__canvas.set_show_field_colors(checked)

    def __changed_color_contrast(self) -> None:
        """Updates the color contrast according to the slider."""
        color_contrast = self.__slider_cc.value()
        self.__label_cc.setText(f"  &Color contrast: {color_contrast}")
        self.__canvas.set_color_contrast(color_contrast)

    def __updated_color_precision(self) -> None:
        """Updates the color precision according to the slider."""
        color_precision = self.__slider_cp.value()
        self.__label_cp.setText(f"  &Color precision: {color_precision}")
        self.__canvas.set_color_precision(color_precision)

    def __checked_grid(self, checked: bool) -> None:
        """Turns grid lines on and off."""
        self.__canvas.set_grid_enabled(checked)

    def __checked_axes(self, checked: bool) -> None:
        """Turns axes lines on and off."""
        self.__canvas.set_axes_enabled(checked)

    def __clicked_trace_point_button(self) -> None:
        """Opens a dialog to input the x and y coordinates of the start point."""

        dialog = CoordinateDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        # if accepted -> get result
        x, y = dialog.get_coordinates()

        if x is None or y is None:
            QMessageBox.critical(self, "Error", f"Invalid coordinates.")
            return

        xlim = self.__canvas.xlim
        ylim = self.__canvas.ylim
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
        self.__canvas.manager.trace_from_point(x, y)

    def __show_trace_settings_dialog(self) -> None:
        """Opens a dialog to set the trace settings."""
        new_settings = self.__canvas.manager.trace_settings.copy()
        dialog = TraceSettingsDialog(
            self,
            new_settings,
            self.__canvas.manager.field_settings.function_string,
            self.__canvas.xlim,
            self.__canvas.ylim,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.__canvas.manager.trace_settings = new_settings

    def __update_xmin(self) -> None:
        """Updates xmin according to the xmin input line."""
        xmin = try_get_value_from_string(self.__xmin_input.text())
        if xmin is None:
            return
        xlim = self.__canvas.xlim
        if xmin == round(xlim[0], ROUND_INPUT_LINES) or xmin >= xlim[1]:
            return
        self.__canvas.xlim = (xmin, xlim[1])

    def __update_xmax(self) -> None:
        """Updates xmax according to the xmax input line."""
        xmax = try_get_value_from_string(self.__xmax_input.text())
        if xmax is None:
            return
        xlim = self.__canvas.xlim
        if xmax == round(xlim[1], ROUND_INPUT_LINES) or xmax <= xlim[0]:
            return
        self.__canvas.xlim = (xlim[0], xmax)

    def __update_ymin(self) -> None:
        """Updates ymin according to the ymin input line."""
        ymin = try_get_value_from_string(self.__ymin_input.text())
        if ymin is None:
            return
        ylim = self.__canvas.ylim
        if ymin == round(ylim[0], ROUND_INPUT_LINES) or ymin >= ylim[1]:
            return
        self.__canvas.ylim = (ymin, ylim[1])

    def __update_ymax(self) -> None:
        """Updates ymax according to the ymax input line."""
        ymax = try_get_value_from_string(self.__ymax_input.text())
        if ymax is None:
            return
        ylim = self.__canvas.ylim
        if ymax == round(ylim[1], ROUND_INPUT_LINES) or ymax <= ylim[0]:
            return
        self.__canvas.ylim = (ylim[0], ymax)

    def update_displayed_axes_limits(self) -> None:
        """Updates all displayed axes limits according to actual limits."""
        (xmin, xmax), (ymin, ymax) = self.__canvas.xlim, self.__canvas.ylim
        self.__xmin_input.setText(f"{xmin:.{ROUND_INPUT_LINES}f}")
        self.__xmax_input.setText(f"{xmax:.{ROUND_INPUT_LINES}f}")
        self.__ymin_input.setText(f"{ymin:.{ROUND_INPUT_LINES}f}")
        self.__ymax_input.setText(f"{ymax:.{ROUND_INPUT_LINES}f}")

    def __update_num_arrows(self) -> None:
        """Updates the number of arrows according to the input line."""
        num_arrows = try_get_value_from_string(self.__num_arrows_input.text())
        if num_arrows is None:
            return

        if num_arrows < MIN_NUM_ARROWS or num_arrows > MAX_NUM_ARROWS:
            num_arrows = np.clip(num_arrows, MIN_NUM_ARROWS, MAX_NUM_ARROWS)
            self.__num_arrows_input.setText(str(num_arrows))
        if num_arrows < 1:
            num_arrows = 1
            self.__num_arrows_input.setText(str(num_arrows))

        self.__num_arrows_input.setText(str(int(num_arrows)))
        self.__canvas.set_num_arrows(int(num_arrows))

    def __add_five_arrows(self) -> None:
        """Adds 5 arrows."""
        self.__num_arrows_input.setText(str(int(self.__num_arrows_input.text()) + 5))

    def __remove_five_arrows(self) -> None:
        """Removes 5 arrows."""
        self.__num_arrows_input.setText(str(int(self.__num_arrows_input.text()) - 5))

    def __changed_arrow_length(self) -> None:
        """Updates the arrow length according to the slider."""
        arrow_length = self.__slider_al.value()
        self.__label_al.setText(f"  &Arrow length: {arrow_length}")
        self.__canvas.set_arrow_length(arrow_length)

    def __changed_arrow_width(self) -> None:
        """Updates the arrow width according to the slider."""
        arrow_width = self.__slider_aw.value()
        self.__label_aw.setText(f"  &Arrow width: {arrow_width}")
        self.__canvas.set_arrow_width(arrow_width)

    def __changed_mouse_line_width(self) -> None:
        """Updates the mouse line width according to the slider."""
        width = self.__slider_mw.value()
        self.__label_mw.setText(f"  &Mouse line width: {width}")
        self.__canvas.set_mouse_line_width(width)

    def __changed_mouse_line_length(self) -> None:
        """Updates the mouse line length according to the slider."""
        length = self.__slider_ml.value()
        self.__label_ml.setText(f"  &Mouse line length: {length}")
        self.__canvas.set_mouse_line_length(length)

    def __checked_mouseLine(self, checked: bool) -> None:
        """Turns the mouse line on and off."""
        self.__canvas.set_drawing_mouse_line(checked)
