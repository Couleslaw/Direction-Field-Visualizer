import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
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
    QCheckBox,
    QMessageBox,
    QSpacerItem,
    QSizePolicy,
    QShortcut,
    QFileDialog,
)

import time

# import standard function from math
from math import (
    sin,
    cos,
    tan,
    exp,
    log,
    log2,
    log10,
    sqrt,
    asin,
    acos,
    atan,
    sinh,
    cosh,
    tanh,
    asinh,
    acosh,
    atanh,
    pi,
    e,
)

ln = log


np.seterr(divide="raise", invalid="ignore")


# constants
AXIS_RATIO = 1.7
DEFAULT_XMIN = -3
DEFAULT_XMAX = 3
DEFAULT_YMIN = DEFAULT_XMIN / AXIS_RATIO
DEFAULT_YMAX = DEFAULT_XMAX / AXIS_RATIO

DEFAULT_FUNCTION = "-x*y"

# priklad: ln(sqrt(sin(x)*sin(y)))


def create_function_from_string(string):
    return eval(f"lambda x, y: {string}")


DEFAULT_NUM_ARROWS = 21
MAX_NUM_ARROWS = 100

# length = 1    ~  1 / 100  of the length of the diagonal
# length = 10   ~  1 / 10   of the length of the diagonal
DEFAULT_ARROW_LENGTH = 4

ROUND_INPUT_LINES = 7
ZOOM = 2
MAX_ZOOM = 5e-3


# TODO:
# more efficient arrow drawing - caching


class DirectionFieldBuilder:
    """Plots direction fields using the matplotlib library."""

    def __init__(self, plot, app):
        self.press = None  # holds x, y of pressed point while moving, else None
        self.plot = plot
        self.app = app  # the MyApp object SCB is embedded in

        self.num_arrows = DEFAULT_NUM_ARROWS
        self.arrow_length = DEFAULT_ARROW_LENGTH
        self.function = create_function_from_string(DEFAULT_FUNCTION)

        self.motion_counter = 0
        self.func_times = []
        self.draw_times = []

    def connect(self):
        """Connect to all the events we need."""
        self.cidpress = self.plot.figure.canvas.mpl_connect(
            "button_press_event", self.on_press
        )
        self.cidrelease = self.plot.figure.canvas.mpl_connect(
            "button_release_event", self.on_release
        )
        self.cidmotion = self.plot.figure.canvas.mpl_connect(
            "motion_notify_event", self.on_motion
        )
        self.cidzoom = self.plot.figure.canvas.mpl_connect("scroll_event", self.on_scroll)

    def on_press(self, event):
        """
        Begins canvas movement if the left mouse button was clicked
        """
        if event.inaxes != self.plot.axes:
            return

        # left mouse button --> begin canvas movement
        elif event.button == 1:
            self.moving_canvas = True
            self.draw_field()
            self.press = (event.xdata, event.ydata)

    def on_motion(self, event):
        """Changes axes lims when moving_canvas"""
        if self.press is None or event.inaxes != self.plot.axes:
            return
        xlast, ylast = self.press

        if self.moving_canvas:
            dx, dy = event.xdata - xlast, event.ydata - ylast
            self.plot.axes.set_xlim([x - dx for x in self.plot.axes.get_xlim()])
            self.plot.axes.set_ylim([y - dy for y in self.plot.axes.get_ylim()])

            self.app.update_displayed_lims()

            self.motion_counter += 1
            if self.motion_counter % 10 == 0:
                self.draw_field()
            else:
                self.plot.figure.canvas.draw()

    def on_release(self, event):
        """Stops canvas movement or point movement."""
        if self.press is None or event.inaxes != self.plot.axes:
            return

        if self.moving_canvas:
            self.moving_canvas = False
            self.draw_field()
        self.press = None

    def on_scroll(self, event):
        """Zooms in and out based on 'ZOOM' by scaling the x and y lims accordingly."""

        if event.inaxes != self.plot.axes:
            return

        margin = (ZOOM - 1) / 2  # how much to add on both sides
        (xmin, xmax), (ymin, ymax) = self.plot.axes.get_xlim(), self.plot.axes.get_ylim()
        xleft, xright, ydown, yup = (
            event.xdata - xmin,
            xmax - event.xdata,
            event.ydata - ymin,
            ymax - event.ydata,
        )

        if event.button == "down":  # zoom out
            xlim = (xmin - margin * xleft, xmax + margin * xright)
            ylim = (ymin - margin * ydown, ymax + margin * yup)
        else:  # zoom in
            if xmax - xmin < MAX_ZOOM:  # if max zoom has been reached
                return
            margin = margin / ZOOM
            xlim = (xmin + margin * xleft, xmax - margin * xright)
            ylim = (ymin + margin * ydown, ymax - margin * yup)

        self.plot.axes.set_xlim(xlim)
        self.plot.axes.set_ylim(ylim)
        self.app.update_displayed_lims()
        self.draw_field()

    def draw_field(self, just_entered_new_function=False):
        """Draws the direction field."""
        xlim = self.plot.axes.get_xlim()  # save old lims
        ylim = self.plot.axes.get_ylim()

        def get_line(x, y, function):
            def round_to_zero(n):
                if abs(n) < 1e-10:
                    return 0
                return n

            x = round_to_zero(x)
            y = round_to_zero(y)

            try:
                der = function(x, y)
                vector = np.array([1, der])
            # this is raised in the case of nonzero/0 --> draw a vertical line
            except FloatingPointError:
                vector = np.array([0, 1])
            # this is raised in the case of 0/0  --> dont draw anything
            except ZeroDivisionError:
                return None
            # this is raised if the function is not defined at the point e.i. sqrt(-1)
            except ValueError:
                return None
            # e.i sinsin(x) --> this is taken care of later
            except NameError as e:
                raise e

            center = np.array([x, y])
            vector = vector / np.linalg.norm(vector)

            diagonal = np.sqrt((xlim[1] - xlim[0]) ** 2 + (ylim[1] - ylim[0]) ** 2)
            line_len = diagonal / 100 * self.arrow_length

            return np.append(
                center - vector * line_len / 2,
                center + vector * line_len / 2,
            )

        xstep = (xlim[1] - xlim[0]) / self.num_arrows
        ystep = (ylim[1] - ylim[0]) / self.num_arrows

        f = lambda n, s: s * (n // s)
        xmargin = (self.num_arrows // 4) * xstep + (
            xstep / 2 if self.num_arrows % 2 == 0 else 0
        )
        ymargin = (self.num_arrows // 4) * ystep
        # xmargin = ymargin = 0
        xs = np.arange(f(xlim[0], xstep) - xmargin, xlim[1] + xstep + xmargin, xstep)
        ys = np.arange(f(ylim[0], ystep) - ymargin, ylim[1] + ystep + ymargin, ystep)

        # start = time.time()
        # try to get the arrows
        try:
            arrows = np.array(
                [
                    line
                    for line in [
                        get_line(x, y, function=self.function) for x in xs for y in ys
                    ]
                    if line is not None
                ]
            ).T
        # if there is an undefined function e.i. sinsin(x)
        except NameError as e:
            QMessageBox.critical(self.app, "Error", f"Unknown function: {e}")
            arrows = []
            # if this occurs right after entering a new function, raise the error --> the previous function will be restored
            if just_entered_new_function:
                raise e

        # self.func_times.append(time.time() - start)
        # start = time.time()

        self.plot.axes.cla()

        if len(arrows) == 4:
            self.plot.axes.quiver(
                arrows[0],
                arrows[1],
                arrows[2] - arrows[0],
                arrows[3] - arrows[1],
                angles="xy",
                scale_units="xy",
                scale=1,
            )

        # self.draw_times.append(time.time() - start)
        # if len(self.func_times) == 10:
        #     print("Function mean: ", sum(self.func_times) / 10)
        #     print("Draw mean: ", sum(self.draw_times) / 10)
        #     self.func_times = []
        #     self.draw_times = []

        # set old lims
        self.plot.axes.set_xlim(xlim)
        self.plot.axes.set_ylim(ylim)

        # draw the axes
        self.plot.axes.axvline(0, color="r", linewidth=1)
        self.plot.axes.axhline(0, color="r", linewidth=1)

        self.plot.figure.canvas.draw()


class Canvas(FigureCanvas):
    """Ensures communication between the matplotlib figure and PyQt5 GUI."""

    def __init__(self, parent):  # parent is the QtWidget object the figure will be embedded in
        self.fig, self.ax = plt.subplots()
        super().__init__(self.fig)
        self.setParent(parent)
        self.parent = parent
        self.pyplot_code()

    def pyplot_code(self):
        """Create the SplineCurvesBuilder object and set default parameters."""
        self.ax.set_xlim(DEFAULT_XMIN, DEFAULT_XMAX)
        self.ax.set_ylim(DEFAULT_YMIN, DEFAULT_YMAX)
        self.ax.axvline(0, color="r", linewidth=1)
        self.ax.axhline(0, color="r", linewidth=1)
        (plot,) = self.ax.plot([0], [0])
        self.dfb = DirectionFieldBuilder(plot, self.parent)
        self.dfb.connect()

    def get_xlim(self):
        return self.ax.get_xlim()

    def get_ylim(self):
        return self.ax.get_ylim()

    def set_xlim(self, xlim):
        print("set_xlim: ", xlim)
        self.ax.set_xlim(xlim)

    def set_ylim(self, ylim):
        print("set_ylim: ", ylim)
        self.ax.set_ylim(ylim)

    def get_num_arrows(self):
        return self.dfb.num_arrows

    def set_num_arrows(self, num_arrows):
        self.dfb.num_arrows = num_arrows
        self.redraw()

    def get_arrow_length(self):
        return self.dfb.arrow_length

    def set_arrow_length(self, arrow_length):
        self.dfb.arrow_length = arrow_length
        self.redraw()

    def redraw(self, just_entered_new_function=False):
        self.dfb.draw_field(just_entered_new_function)

    def set_equal_axes(self):
        self.redraw()
        self.dfb.plot.axes.axis("equal")

    def set_auto_axes(self):
        self.dfb.plot.axes.axis("auto")
        self.redraw()


class MyApp(QWidget):
    """Creates the GUI using the PyQt5 library."""

    equal_axes = True  # True if the 'Equal axes' checkbox is checked

    def __init__(self):
        super().__init__()
        self.setMinimumSize(1500, 800)
        self.setWindowTitle("Spline curves")

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
        sidebar.setMaximumWidth(420)
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

        self.graph_button = QPushButton("Graph")
        self.graph_button.clicked.connect(self.execute_graph_function)
        self.graph_button.setShortcut("Return")
        graphLayout = QVBoxLayout()
        graphLayout.addLayout(form)
        graphLayout.addWidget(self.graph_button)
        self.sidebarLayout.addLayout(graphLayout)

        # add space
        spacer = QSpacerItem(20, 80, QSizePolicy.Minimum)
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
        self.minus_arrows = QPushButton("-")
        self.minus_arrows.clicked.connect(self.remove_some_arrows)

        arrowLayout = QHBoxLayout()
        arrowLayout.addWidget(self.plus_arrows)
        arrowLayout.addWidget(self.minus_arrows)

        self.sidebarLayout.addLayout(form)
        self.sidebarLayout.addLayout(arrowLayout)

        # create the 'arrow length' slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(10)
        self.slider.setValue(DEFAULT_ARROW_LENGTH)
        self.slider.setMinimumWidth(150)
        self.slider.setTickInterval(1)
        self.slider.setSingleStep(1)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.valueChanged.connect(self.changed_arrow_length)
        self.label = QLabel()
        self.label.setText(
            f"  &Arrow length: {DEFAULT_ARROW_LENGTH}   "
        )  # spaces at end for padding
        self.label.setBuddy(self.slider)  # changes focus to the slider if 'Alt+a' is pressed
        form = QVBoxLayout()
        form.addWidget(self.label)
        form.addWidget(self.slider)
        self.sidebarLayout.addLayout(form)

        # create the 'save image' button
        self.save_button = QPushButton("&Save image")
        self.save_button.clicked.connect(self.show_save_file_dialog)
        self.sidebarLayout.addWidget(self.save_button)
        self.save_button.setShortcut("Ctrl+S")

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
            print(f"Selected file: {file_name}")
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
        arrow_length = self.slider.value()
        self.label.setText(f"  &Arrow length: {arrow_length}   ")  # spaces at end for padding
        self.canvas.set_arrow_length(arrow_length)
        self.canvas.redraw()

    def enable_input_lines(self, enabled):
        self.xmin_input.setEnabled(enabled)
        self.xmax_input.setEnabled(enabled)
        self.ymin_input.setEnabled(enabled)
        self.ymax_input.setEnabled(enabled)


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
