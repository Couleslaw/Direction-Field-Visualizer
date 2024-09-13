import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
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
)

from canvas import Canvas
from direction_field_builder import create_function_from_string
from default_constants import *

ROUND_INPUT_LINES = 7


class MyApp(QWidget):
    """Creates the GUI using the PyQt5 library."""

    equal_axes = True  # True if the 'Equal axes' checkbox is checked

    def __init__(self):
        super().__init__()
        self.setMinimumSize(1600, 800)
        self.setWindowTitle("Direction Field Visualizer")

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        # create the matplotlib graph
        self.canvas = Canvas(self)
        self.layout.addWidget(self.canvas)

        # store all side-bar widgets here
        sidebar = QWidget()
        self.sidebarLayout = QVBoxLayout()
        self.sidebarLayout.setAlignment(Qt.AlignTop)
        sidebar.setLayout(self.sidebarLayout)
        sidebar.setMaximumWidth(400)
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
        spacer = QSpacerItem(20, 70, QSizePolicy.Minimum, QSizePolicy.Preferred)
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
        self.slider_a = QSlider(Qt.Horizontal)
        self.slider_a.setMinimum(1)
        self.slider_a.setMaximum(15)
        self.slider_a.setValue(DEFAULT_ARROW_LENGTH)
        self.slider_a.setMinimumWidth(150)
        self.slider_a.setTickInterval(1)
        self.slider_a.setSingleStep(1)
        self.slider_a.setTickPosition(QSlider.TicksBelow)
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
        self.slider_aw = QSlider(Qt.Horizontal)
        self.slider_aw.setMinimum(1)
        self.slider_aw.setMaximum(10)
        self.slider_aw.setValue(DEFAULT_ARROW_WIDTH)
        self.slider_aw.setMinimumWidth(150)
        self.slider_aw.setTickInterval(1)
        self.slider_aw.setSingleStep(1)
        self.slider_aw.setTickPosition(QSlider.TicksBelow)
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

        # create the 'Mouse line' checkbox
        self.mouseLine = QCheckBox("Mouse line")
        self.mouseLine.stateChanged.connect(self.checked_mouseLine)
        self.mouseLine.setChecked(False)
        self.mouseLine.setShortcut("Ctrl+M")
        self.sidebarLayout.addWidget(self.mouseLine)

        # create the 'Mouse line width' slider
        self.slider_mw = QSlider(Qt.Horizontal)
        self.slider_mw.setMinimum(1)
        self.slider_mw.setMaximum(10)
        self.slider_mw.setValue(DEFAULT_MOUSE_LINE_WIDTH)
        self.slider_mw.setMinimumWidth(150)
        self.slider_mw.setTickInterval(1)
        self.slider_mw.setSingleStep(1)
        self.slider_mw.setTickPosition(QSlider.TicksBelow)
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

        # create the 'Mouse line length' slider
        self.slider_ml = QSlider(Qt.Horizontal)
        self.slider_ml.setMinimum(1)
        self.slider_ml.setMaximum(10)
        self.slider_ml.setValue(DEFAULT_MOUSE_LINE_LENGTH)
        self.slider_ml.setMinimumWidth(150)
        self.slider_ml.setTickInterval(1)
        self.slider_ml.setSingleStep(1)
        self.slider_ml.setTickPosition(QSlider.TicksBelow)
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

        # add some spacing
        self.sidebarLayout.addItem(spacer)

        # create the 'trace line width' slider
        self.slider_w = QSlider(Qt.Horizontal)
        self.slider_w.setMinimum(1)
        self.slider_w.setMaximum(10)
        self.slider_w.setValue(DEFAULT_TRACE_LINES_WIDTH)
        self.slider_w.setMinimumWidth(150)
        self.slider_w.setTickInterval(1)
        self.slider_w.setSingleStep(1)
        self.slider_w.setTickPosition(QSlider.TicksBelow)
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

        # create the 'Auto trace dx' checkbox
        self.autoTrace = QCheckBox("Auto trace dx")
        self.autoTrace.setChecked(True)
        self.autoTrace.stateChanged.connect(self.checked_autoTrace)
        self.sidebarLayout.addWidget(self.autoTrace)

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

        # add space
        self.sidebarLayout.addItem(spacer)

        # create the 'x min' input line
        self.xmin_input = QLineEdit()
        self.xmin_input.setText(str(DEFAULT_XMIN))
        self.xmin_input.textChanged.connect(self.update_xmin)
        form = QFormLayout()
        form.addRow(
            "  x min:", self.xmin_input
        )  # spaces at the beginning are for additional padding
        self.sidebarLayout.addLayout(form)

        # create the 'x max' input line
        self.xmax_input = QLineEdit()
        self.xmax_input.setText(str(DEFAULT_XMAX))
        self.xmax_input.textChanged.connect(self.update_xmax)
        form = QFormLayout()
        form.addRow(
            "  x max:", self.xmax_input
        )  # spaces at the beginning are for additional padding
        self.sidebarLayout.addLayout(form)

        # create the 'y min' input line
        self.ymin_input = QLineEdit()
        self.ymin_input.setText(str(DEFAULT_YMIN))
        self.ymin_input.textChanged.connect(self.update_ymin)
        form = QFormLayout()
        form.addRow(
            "  y min:", self.ymin_input
        )  # spaces at the beginning are for additional padding
        self.sidebarLayout.addLayout(form)

        # create the 'y max' input line
        self.ymax_input = QLineEdit()
        self.ymax_input.setText(str(DEFAULT_YMAX))
        self.ymax_input.textChanged.connect(self.update_ymax)
        form = QFormLayout()
        form.addRow(
            "  y max:", self.ymax_input
        )  # spaces at the beginning are for additional padding
        self.sidebarLayout.addLayout(form)

        self.enable_input_lines(not MyApp.equal_axes)

        # create the 'Equal axes' checkbox
        self.equalAxes = QCheckBox("Equal axes")
        self.equalAxes.stateChanged.connect(self.checked_equalAxes)
        self.equalAxes.setChecked(MyApp.equal_axes)
        self.sidebarLayout.addWidget(self.equalAxes)

    def show_save_file_dialog(self):
        """Opens a dialog to save the current figure as a png or svg file."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            "PNG (*.png);; svg (*.svg)",
            options=options,
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

    def checked_autoTrace(self, checked):
        """Turns automatic trace dx on and off"""
        self.canvas.dfb.auto_trace_dx = not self.canvas.dfb.auto_trace_dx
        self.trace_dx_input.setEnabled(not checked)
        self.update_displayed_trace_dx()

    def update_trace_dx(self):
        """Updates trace dx according to the dx input line"""
        dx = self.trace_dx_input.text()
        try:
            dx = float(dx)
        except ValueError:  # don't change anything if the input is not valid
            return
        dx = max(dx, MIN_TRACE_DX)
        self.canvas.set_trace_lines_dx(dx)

    def update_displayed_trace_dx(self):
        """Sets trace dx to the one given"""
        dx = self.canvas.dfb.get_auto_dx()
        self.trace_dx_input.setText(f"{dx:.10f}")

    def update_xmin(self):
        """Updates xmin according to the xmin input line."""
        xmin = self.xmin_input.text()
        try:
            xmin = float(xmin)
        except ValueError:  # don't change anything if the input is not valid
            return
        xlim = self.canvas.get_xlim()
        if xmin == round(xlim[0], ROUND_INPUT_LINES):
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
        if xmax == round(xlim[1], ROUND_INPUT_LINES):
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
        if ymin == round(ylim[0], ROUND_INPUT_LINES):
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
        if ymax == round(ylim[1], ROUND_INPUT_LINES):
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
    myApp = MyApp()
    myApp.show()

    try:
        sys.exit(app.exec_())
    except SystemExit:
        print("Closing Window...")


if __name__ == "__main__":
    main()
