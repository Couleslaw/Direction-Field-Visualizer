import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
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
    QFileDialog,
)

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
    fabs,
    floor,
    ceil,
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
abs = fabs
sign = lambda x: int((x > 0)) - int((x < 0))


np.seterr(divide="raise", invalid="ignore")


# constants
AXIS_RATIO = 1.5
DEFAULT_XMIN = -2.5
DEFAULT_XMAX = 2.5
DEFAULT_YMIN = DEFAULT_XMIN / AXIS_RATIO
DEFAULT_YMAX = DEFAULT_XMAX / AXIS_RATIO

DEFAULT_FUNCTION = "-x*y"


def create_function_from_string(string):
    return eval(f"lambda x, y: {string}")


TRACE_AUTO_DX_GRANULARITY = 10000
TRACE_NUM_SEGMENTS_IN_DIAGONAL = 1000
DEFAULT_TRACE_LINES_WIDTH = 4
DEFAULT_MOUSE_LINE_WIDTH = 4

# length = 1    ~  1 / 100  of the length of the diagonal
# length = 10   ~  1 / 10   of the length of the diagonal
DEFAULT_ARROW_LENGTH = 4
DEFAULT_ARROW_WIDTH = 3
DEFAULT_NUM_ARROWS = 21
MAX_NUM_ARROWS = 100

ROUND_INPUT_LINES = 7
ZOOM = 2
MAX_ZOOM = 5e-3


class DirectionFieldBuilder:
    """Plots direction fields using the matplotlib library."""

    def __init__(self, plot, app):
        self.press = None  # holds x, y of pressed point while moving, else None
        self.moving_canvas = False  # True if the canvas is being moved
        self.drawing_mouse_line = False
        self.last_mouse_line = None
        self.mouse_pos = None
        self.plot = plot
        self.app = app  # the MyApp object SCB is embedded in

        self.num_arrows = DEFAULT_NUM_ARROWS
        self.arrow_length = DEFAULT_ARROW_LENGTH
        self.arrow_width = DEFAULT_ARROW_WIDTH
        self.trace_lines_width = DEFAULT_TRACE_LINES_WIDTH
        self.mouse_line_width = DEFAULT_MOUSE_LINE_WIDTH
        self.function = create_function_from_string(DEFAULT_FUNCTION)
        self.auto_trace_dx = True
        self.trace_dx = None

        self.motion_counter = 0
        self.arrows_cache = {}

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
            self.draw_field(keep_cache=True)
            self.press = (event.xdata, event.ydata)
            self.moving_canvas = True
        # right mouse button --> start tracing the field from the clicked point
        elif event.button == 3:
            self.press = (event.xdata, event.ydata)
            self.trace_curve()

    def on_motion(self, event):
        """Changes axes lims when moving_canvas"""
        # if outside of the matplotlib plot
        if event.inaxes != self.plot.axes:
            # if a direction line is being drawn at the mouse location
            if self.last_mouse_line is not None:
                # remove line - mouse is out of bounds
                self.remove_mouse_line_from_plot()
                self.plot.figure.canvas.draw()
                self.last_mouse_line = None
            return

        self.mouse_pos = (event.xdata, event.ydata)

        # if a direction line is being drawn at the mouse location --> redraw after movement
        if self.drawing_mouse_line:
            self.draw_mouse_line()
        if self.press is None or not self.moving_canvas:
            return

        xlast, ylast = self.press

        dx, dy = event.xdata - xlast, event.ydata - ylast
        self.plot.axes.set_xlim([x - dx for x in self.plot.axes.get_xlim()])
        self.plot.axes.set_ylim([y - dy for y in self.plot.axes.get_ylim()])

        self.app.update_displayed_lims()

        self.motion_counter += 1
        if self.motion_counter % 3 == 0:
            self.motion_counter = 0
            self.draw_field(keep_cache=True)
        else:
            self.plot.figure.canvas.draw()

    def on_release(self, event):
        """Stops canvas movement or point movement."""
        if self.press is None or event.inaxes != self.plot.axes:
            return

        if self.moving_canvas:
            self.moving_canvas = False
            self.draw_field(keep_cache=True)
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

    def get_arrow(self, x, y, arrow_len):
        """
        x, y: center of the arrow
        returns: [s1, s2, v1, v2] where (s1, s2) is the start of the arrow and (v1, v2) is the vector of the arrow
        """

        # check cache
        if (x, y) in self.arrows_cache:
            return self.arrows_cache[(x, y)]

        try:
            der = self.function(x, y)
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
        vector = vector / np.linalg.norm(vector) * arrow_len

        res = np.append(center - vector / 2, vector)
        self.arrows_cache[(x, y)] = res
        return res

    def draw_field(self, just_entered_new_function=False, keep_cache=False):
        """Draws the direction field."""
        if not keep_cache:
            self.arrows_cache = {}

        xlim = self.plot.axes.get_xlim()  # save old lims
        ylim = self.plot.axes.get_ylim()

        diagonal = np.sqrt((xlim[1] - xlim[0]) ** 2 + (ylim[1] - ylim[0]) ** 2)
        vector_len = diagonal / 100 * self.arrow_length

        xstep = (xlim[1] - xlim[0]) / self.num_arrows
        ystep = (ylim[1] - ylim[0]) / self.num_arrows

        xmargin = (self.num_arrows // 5) * xstep + (
            xstep / 2 if self.num_arrows % 2 == 0 else 0
        )
        ymargin = (self.num_arrows // 5) * ystep + (
            ystep / 2 if self.num_arrows % 2 == 0 else 0
        )

        f = lambda n, s: s * (n // s)
        xs = np.arange(f(xlim[0], xstep) - xmargin, xlim[1] + xstep + xmargin, xstep)
        ys = np.arange(f(ylim[0], ystep) - ymargin, ylim[1] + ystep + ymargin, ystep)

        # try to get the arrows
        try:
            arrows = np.array(
                [
                    line
                    for line in [self.get_arrow(x, y, vector_len) for x in xs for y in ys]
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

        self.plot.axes.cla()

        # arrow_width  1 = 0.001
        # arrow_width 10 = 0.005
        arrow_width = 0.001 + 0.004 * (self.arrow_width - 1) / 9

        if len(arrows) == 4:
            self.plot.axes.quiver(
                arrows[0],
                arrows[1],
                arrows[2],
                arrows[3],
                angles="xy",
                scale_units="xy",
                scale=1,
                width=arrow_width,
            )

        # set old lims
        self.plot.axes.set_xlim(xlim)
        self.plot.axes.set_ylim(ylim)

        # draw the axes
        self.plot.axes.axvline(0, color="b", linewidth=1.5)
        self.plot.axes.axhline(0, color="b", linewidth=1.5)

        if self.drawing_mouse_line:
            self.draw_mouse_line()
        self.plot.figure.canvas.draw()

    def get_auto_dx(self):
        xlim = self.plot.axes.get_xlim()
        return (xlim[1] - xlim[0]) / TRACE_AUTO_DX_GRANULARITY

    def trace_curve(self):
        """Draws a solution curve passing through self.press"""
        if self.press is None:
            return

        x, y = self.press
        ylim = self.plot.axes.get_ylim()
        xlim = self.plot.axes.get_xlim()

        # the curves are made out of line segments of this length
        min_segment_length = (
            np.sqrt((xlim[1] - xlim[0]) ** 2 + (ylim[1] - ylim[0]) ** 2)
            / TRACE_NUM_SEGMENTS_IN_DIAGONAL
        )

        dx = self.get_auto_dx() if self.auto_trace_dx else self.trace_dx

        def trace(x, y, trace_forward: bool):
            line = [(x, y)]
            center = np.array([x, y])
            segment_length = 0

            UNKNOWN = 0
            STOP = 1
            INFINITE = 2
            CONTINUE = 3

            singularity_dx = min(1e-6, dx / 1000)

            def handle_singularity(x, y):
                dx = singularity_dx * (1 if trace_forward else -1)
                sdx = dx**2

                try:
                    slope = self.function(x, y)
                    if slope > 1e10:
                        return INFINITE
                    nx, ny = x + dx, y + dx * slope
                    nslope = self.function(nx, ny)
                    second_der = (self.function(nx + sdx, ny + sdx * nslope) - nslope) / sdx
                except:
                    return UNKNOWN

                def continue_or_stop():
                    vector = np.array([1, slope]) * dx / 5
                    return CONTINUE if is_monotonous_on(np.array([x, y]), vector, 10) else STOP

                def continue_or_infinite():
                    vector = np.array([1, slope]) * dx / 5
                    return (
                        CONTINUE
                        if is_monotonous_on(np.array([x, y]), vector, 10)
                        else INFINITE
                    )

                # convex up - forward
                if slope > 0 and dx > 0:
                    # second_der > 0 & nslope < 0 --> convex down
                    if second_der > 0 and nslope < 0:
                        print("convex down")
                        return INFINITE
                    # second_der > 0 & nslope > 0 --> convex up
                    if second_der > 0 and nslope > 0:
                        return continue_or_stop()
                    # second_der < 0 & nslope > 0 --> concave up
                    if second_der < 0 and nslope > 0:
                        return continue_or_infinite()
                    # second_der < 0 & nslope < 0 --> concave down
                    if second_der < 0 and nslope < 0:
                        return STOP

                # concave down - forward
                if slope < 0 and dx > 0:
                    # second_der > 0 & nslope < 0 --> convex down
                    if second_der > 0 and nslope < 0:
                        print("inf, conved down")
                        return continue_or_infinite()
                    # second_der > 0 & nslope > 0 --> convex up
                    if second_der > 0 and nslope > 0:
                        print("concave down")
                        return STOP
                    # second_der < 0 & nslope > 0 --> concave up
                    if second_der < 0 and nslope > 0:
                        print("INF, concave up")
                        return INFINITE
                    # second_der < 0 & nslope < 0 --> concave down
                    if second_der < 0 and nslope < 0:
                        print("inf, concave down")
                        return continue_or_stop()

                # concave up - backward
                if slope > 0 and dx < 0:
                    # second_der > 0 & nslope < 0 --> convex down
                    if second_der > 0 and nslope < 0:
                        print("stop concave up")
                        return STOP
                    # second_der > 0 & nslope > 0 --> convex up
                    if second_der > 0 and nslope > 0:
                        # print("concave up - second_der > 0")
                        return continue_or_infinite()
                    # second_der < 0 & nslope > 0 --> concave up
                    if second_der < 0 and nslope > 0:
                        # print("concave up - second_der < 0", slope, nslope)
                        return continue_or_stop()
                    # second_der < 0 & nslope < 0 --> concave down
                    if second_der < 0 and nslope < 0:
                        return INFINITE

                # convex down - backward
                if slope < 0 and dx < 0:
                    # second_der > 0 & nslope < 0 --> convex down
                    if second_der > 0 and nslope < 0:
                        return continue_or_stop()
                    # second_der > 0 & nslope > 0 --> convex up
                    if second_der > 0 and nslope > 0:
                        return INFINITE
                    # second_der < 0 & nslope > 0 --> concave up
                    if second_der < 0 and nslope > 0:
                        return STOP
                    # second_der < 0 & nslope < 0 --> concave down
                    if second_der < 0 and nslope < 0:
                        return continue_or_infinite()

                if second_der == 0:
                    return CONTINUE
                return UNKNOWN

            def is_monotonous_on(start, vector, num):
                sgn = sign(self.function(start[0], start[1]))
                for _ in range(num):
                    start += vector
                    if sign(self.function(start[0], start[1])) != sgn:
                        return False
                return True

            singularity_count = 0
            num_skips = 0
            while True:
                try:
                    der = self.function(center[0], center[1])
                    vector = np.array([1, der]) * dx * (1 if trace_forward else -1)
                except:
                    break

                if (slope := abs(vector[1] / vector[0])) > 100:
                    res = handle_singularity(center[0], center[1])
                    print(res, center[0])
                    if res == UNKNOWN or res == STOP:
                        break
                    if res == INFINITE:
                        vector = np.array([0, 1 if slope > 0 else -1])
                        last = center + vector * (ylim[1] - ylim[0])
                        line.append(last)
                        break
                    if res == CONTINUE:
                        singularity_count += 1
                        if not (
                            singularity_count % 10 == 0
                            and is_monotonous_on(np.copy(center), vector / 5, 10)
                        ):
                            vector = vector / abs(vector[0]) * singularity_dx
                        else:
                            print("skipped")
                    else:
                        singularity_count = 0
                else:
                    singularity_count = 0

                center += vector
                if center[0] < xlim[0] or center[0] > xlim[1]:
                    break

                screen_height = ylim[1] - ylim[0]
                if (
                    center[1] > ylim[1] + 20 * screen_height
                    or center[1] < ylim[0] - 20 * screen_height
                ):
                    break

                segment_length += np.linalg.norm(vector)
                if segment_length > min_segment_length:
                    line.append((center[0], center[1]))
                    segment_length = 0

            return line

        # trace right and left from the center point
        right_line = trace(x, y, trace_forward=True)
        left_line = trace(x, y, trace_forward=False)

        lc = LineCollection(
            [left_line, right_line], color="r", linewidth=self.trace_lines_width
        )
        self.plot.axes.add_collection(lc)
        self.plot.figure.canvas.draw()

    def remove_mouse_line_from_plot(self):
        if self.last_mouse_line is not None:
            try:
                self.plot.axes.lines.remove(self.last_mouse_line[0])
            except:
                pass
            else:
                self.plot.figure.canvas.draw()

    def draw_mouse_line(self):
        if self.mouse_pos is None:
            return

        xlim = self.plot.axes.get_xlim()
        ylim = self.plot.axes.get_ylim()
        diagonal = np.sqrt((xlim[1] - xlim[0]) ** 2 + (ylim[1] - ylim[0]) ** 2)
        vector_len = diagonal / 100 * self.arrow_length * 1.7
        line_info = self.get_arrow(self.mouse_pos[0], self.mouse_pos[1], vector_len)
        if line_info is None:
            self.remove_mouse_line_from_plot()
            return
        x1 = line_info[0]
        y1 = line_info[1]
        x2 = x1 + line_info[2]
        y2 = y1 + line_info[3]
        self.remove_mouse_line_from_plot()
        self.last_mouse_line = self.plot.axes.plot(
            [x1, x2], [y1, y2], color="r", linewidth=self.mouse_line_width
        )
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
        """Create the DerectionFieldBuilder object and set default parameters."""
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
        self.ax.set_xlim(xlim)

    def set_ylim(self, ylim):
        self.ax.set_ylim(ylim)

    def get_num_arrows(self):
        return self.dfb.num_arrows

    def set_num_arrows(self, num_arrows):
        self.dfb.num_arrows = num_arrows
        self.redraw()

    def set_arrow_length(self, arrow_length):
        self.dfb.arrow_length = arrow_length
        self.redraw()

    def set_arrow_width(self, arrow_width):
        self.dfb.arrow_width = arrow_width
        self.redraw()

    def set_trace_lines_width(self, trace_lines_width):
        self.dfb.trace_lines_width = trace_lines_width

    def set_mouse_line_width(self, mouse_line_width):
        self.dfb.mouse_line_width = mouse_line_width

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

        self.graph_button = QPushButton("Graph")
        self.graph_button.clicked.connect(self.execute_graph_function)
        self.graph_button.setShortcut("Return")
        graphLayout = QVBoxLayout()
        graphLayout.addLayout(form)
        graphLayout.addWidget(self.graph_button)
        self.sidebarLayout.addLayout(graphLayout)

        # create the 'save image' button
        self.save_button = QPushButton("&Save image")
        self.save_button.clicked.connect(self.show_save_file_dialog)
        self.sidebarLayout.addWidget(self.save_button)
        self.save_button.setShortcut("Ctrl+S")

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
        self.plus_arrows.setShortcut("Alt+right")
        self.minus_arrows = QPushButton("-")
        self.minus_arrows.clicked.connect(self.remove_some_arrows)
        self.minus_arrows.setShortcut("Alt+left")

        arrowLayout = QHBoxLayout()
        arrowLayout.addWidget(self.plus_arrows)
        arrowLayout.addWidget(self.minus_arrows)

        self.sidebarLayout.addLayout(form)
        self.sidebarLayout.addLayout(arrowLayout)

        # create the 'arrow length' slider
        self.slider_a = QSlider(Qt.Horizontal)
        self.slider_a.setMinimum(1)
        self.slider_a.setMaximum(10)
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

        # create the 'trace line width' slider
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

        # create the 'Mouse line' checkbox
        self.mouseLine = QCheckBox("Mouse line")
        self.mouseLine.stateChanged.connect(self.checked_mouseLine)
        self.mouseLine.setChecked(False)
        self.mouseLine.setShortcut("Ctrl+M")
        self.sidebarLayout.addWidget(self.mouseLine)

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
        self.label_a.setText(f"  &Trace lines width: {width}")
        self.canvas.set_trace_lines_width(width)

    def changed_mouse_line_width(self):
        """Updates the mouse line width according to the slider."""
        width = self.slider_mw.value()
        self.label_mw.setText(f"  &Mouse line width: {width}")
        self.canvas.set_mouse_line_width(width)
        self.canvas.dfb.draw_mouse_line()

    def checked_mouseLine(self):
        """Turns the mouse line on and off."""
        self.canvas.dfb.drawing_mouse_line = not self.canvas.dfb.drawing_mouse_line
        if self.mouseLine.isChecked():
            self.canvas.dfb.draw_mouse_line()
        else:
            self.canvas.dfb.remove_mouse_line_from_plot()

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
