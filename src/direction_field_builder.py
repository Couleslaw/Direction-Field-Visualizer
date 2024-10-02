from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from PyQt6.QtWidgets import QMessageBox
from matplotlib import cm
import numpy as np

np.seterr(divide="raise", invalid="ignore")


from src.math_functions import *
from src.default_constants import *
from src.numerical_methods import TraceSettings, SolutionTracer, create_function_from_string


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

        self.show_grid = False
        self.show_axes = True
        self.indicate_colors = True
        self.color_intensity = DEFAULT_COLOR_INTENSITY
        self.color_map_name = DEFAULT_COLOR_MAP
        self.color_precision = DEFAULT_COLOR_PRECISION

        self.num_arrows = DEFAULT_NUM_ARROWS
        self.arrow_length = DEFAULT_ARROW_LENGTH
        self.arrow_width = DEFAULT_ARROW_WIDTH
        self.mouse_line_width = DEFAULT_MOUSE_LINE_WIDTH
        self.mouse_line_length = DEFAULT_MOUSE_LINE_LENGTH
        self.function = create_function_from_string(DEFAULT_FUNCTION)
        self.function_string = DEFAULT_FUNCTION
        self.trace_settings = TraceSettings()

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

    def get_arrow(self, x, y, arrow_len, use_cache=True):
        """
        x, y: center of the arrow
        returns: [s1, s2, v1, v2] where (s1, s2) is the start of the arrow and (v1, v2) is the vector of the arrow
        """

        # check cache
        if use_cache and (x, y) in self.arrows_cache:
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
        if use_cache:
            self.arrows_cache[(x, y)] = res
        return res

    def curvature(self, x, y):
        """
        Returns the curvature of the function at the point (x, y)
        """

        exponent = -self.color_precision - 1
        dx = 10**exponent
        if fabs(x - int(x)) < dx:
            x = int(x)
        if fabs(y - int(y)) < dx:
            y = int(y)

        def get_curvature(x, y):
            dy = self.function(x, y)
            d2y = (self.function(x + dx, y + dx * dy) - self.function(x - dx, y - dx * dy)) / (
                2 * dx
            )
            return d2y / (1 + dy**2) ** 1.5

        xlim = self.plot.axes.get_xlim()
        ylim = self.plot.axes.get_ylim()
        fix_dx = max(0.002, (xlim[1] - xlim[0]) / 1000)
        fix_dy = max(0.002, (ylim[1] - ylim[0]) / 1000)
        try:
            return get_curvature(x, y)
        except:
            try:
                return get_curvature(x, y + fix_dy)
            except:
                try:
                    return get_curvature(x + fix_dx, y)
                except:
                    return 0

    def get_colors(self, curvatures, ignore):
        """
        Returns colors for the arrows based on the curvature of the function at the arrow's center.
        ignore says if the arrow is out of the screen
        """

        def norm(x):
            """normalizes x to values between 0 and 1 while ignoring values off screen and the most extreme value"""
            on_screen = x[np.logical_not(ignore)]
            if len(on_screen) == 0:
                return Normalize()(x)
            # if there is only one max value, which is more than twice as big as the second max value
            # it is quite likely that this is a fluke caused by division by zero --> ignore it
            # in fact lets increase the number from 1 to a number based on #arrows
            max_val = max(on_screen)
            second_max = -np.inf
            num_max = 0
            for val in on_screen:
                if val == max_val:
                    num_max += 1
                elif val > second_max:
                    second_max = val
            if second_max == -np.inf:
                second_max = max_val

            limit = max(1, self.num_arrows // 1000)
            if 1 <= num_max <= limit and max_val > 2 * second_max:
                max_val = second_max

            return Normalize(clip=True, vmin=0, vmax=max_val)(x)

        # since exponents are exponential, we can not simply linear map the COLOR_INTENSITY to EXPONENT
        # use an exponential function to map the values
        base = 1.4
        a = (MAX_COLOR_EXP - MIN_COLOR_EXP) / (
            base**MAX_COLOR_INTENSITY - base**MIN_COLOR_INTENSITY
        )
        b = MIN_COLOR_EXP - a * base**MIN_COLOR_INTENSITY
        exponent = a * base**self.color_intensity + b
        return cm.get_cmap(self.color_map_name)(norm(np.abs(curvatures)) ** exponent)

    def draw_field(self, just_entered_new_function=False, keep_cache=False):
        """Draws the direction field."""
        if not keep_cache:
            self.arrows_cache = {}

        xlim = self.plot.axes.get_xlim()  # save old lims
        ylim = self.plot.axes.get_ylim()

        diagonal = np.sqrt((xlim[1] - xlim[0]) ** 2 + (ylim[1] - ylim[0]) ** 2)
        vector_len = diagonal / 200 * self.arrow_length

        x_step = (xlim[1] - xlim[0]) / self.num_arrows
        y_step = (
            (ylim[1] - ylim[0]) / self.num_arrows
            if self.plot.axes.get_aspect() != 1  # if auto axes
            else x_step  # if equal_axes
        )
        x_margin = (self.num_arrows // 6) * x_step + (
            x_step / 2 if self.num_arrows % 2 == 0 else 0
        )
        y_margin = (self.num_arrows // 6) * y_step + (
            y_step / 2 if self.num_arrows % 2 == 0 else 0
        )
        f = lambda n, s: s * (n // s)
        xs = np.arange(f(xlim[0], x_step) - x_margin, xlim[1] + x_step + x_margin, x_step)
        ys = np.arange(f(ylim[0], y_step) - y_margin, ylim[1] + y_step + y_margin, y_step)
        # try to get the arrows
        try:
            arrows = []
            curvatures = []
            ignore = []
            for x in xs:
                for y in ys:
                    arrow = self.get_arrow(x, y, vector_len)
                    if arrow is not None:
                        arrows.append(arrow)
                        if self.indicate_colors:
                            curvatures.append(self.curvature(x, y))
                            if xlim[0] <= x <= xlim[1] and ylim[0] <= y <= ylim[1]:
                                ignore.append(False)
                            else:
                                ignore.append(True)
            arrows = np.array(arrows).T
            if self.indicate_colors:
                colors = self.get_colors(curvatures, ignore)

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
                color=colors if self.indicate_colors else "black",
                cmap="hsv",
            )

        # set old lims
        self.plot.axes.set_xlim(xlim)
        self.plot.axes.set_ylim(ylim)

        if self.show_grid:
            self.plot.axes.grid(True)

        # draw the axes
        if self.show_axes:
            self.plot.axes.axvline(0, color="black", linewidth=1)
            self.plot.axes.axhline(0, color="black", linewidth=1)

        if self.drawing_mouse_line:
            self.draw_mouse_line()
        self.plot.figure.canvas.draw()

    def trace_from_point(self, x, y):
        """Traces the curve from the point (x, y)"""
        self.press = (x, y)
        self.trace_curve()

    def trace_curve(self):
        """Draws a solution curve passing through self.press"""
        if self.press is None:
            return

        x, y = self.press
        ylim = self.plot.axes.get_ylim()
        xlim = self.plot.axes.get_xlim()

        # trace right and left from the center point
        tracer = SolutionTracer(self.trace_settings, self.function_string, xlim, ylim)

        right_line = tracer.trace(x, y, SolutionTracer.FORWARD)
        left_line = tracer.trace(x, y, SolutionTracer.BACKWARD)

        line_width = self.trace_settings.get_line_width()
        line_color = self.trace_settings.line_color
        lc = LineCollection([left_line, right_line], color=line_color, linewidth=line_width)
        self.plot.axes.add_collection(lc)
        self.plot.figure.canvas.draw()

    def remove_mouse_line_from_plot(self):
        """Tries to remove the direction line drawn at the mouse cursor location"""
        if self.last_mouse_line is not None:
            try:
                self.plot.axes.lines.remove(self.last_mouse_line[0])
            except:
                return
            self.plot.figure.canvas.draw()

    def draw_mouse_line(self):
        """Draws a direction line at the mouse cursor location"""
        if self.mouse_pos is None:
            return

        xlim = self.plot.axes.get_xlim()
        ylim = self.plot.axes.get_ylim()
        diagonal = np.sqrt((xlim[1] - xlim[0]) ** 2 + (ylim[1] - ylim[0]) ** 2)
        vector_len = diagonal / 100 * self.mouse_line_length * 1.7

        # remove the old arrow
        self.remove_mouse_line_from_plot()

        # calculate coordinates of the new arrow
        line_info = self.get_arrow(
            self.mouse_pos[0], self.mouse_pos[1], vector_len, use_cache=False
        )

        # if the mouse cursor is in an area where the function is not defined --> return
        if line_info is None:
            return

        # create the new arrow
        x1 = line_info[0]
        y1 = line_info[1]
        x2 = x1 + line_info[2]
        y2 = y1 + line_info[3]
        self.last_mouse_line = self.plot.axes.plot(
            [x1, x2],
            [y1, y2],
            color="r",
            linewidth=self.mouse_line_width,
            solid_capstyle="round",
        )
        self.plot.figure.canvas.draw()
