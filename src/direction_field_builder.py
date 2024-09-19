from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from PyQt6.QtWidgets import QMessageBox
from matplotlib import cm
import numpy as np

np.seterr(divide="raise", invalid="ignore")


# import standard function from math
from math import (
    sin,
    cos,
    tan,
    asin,
    acos,
    atan,
    sinh,
    cosh,
    tanh,
    asinh,
    acosh,
    atanh,
    exp,
    log,
    log2,
    log10,
    sqrt,
    fabs,
    floor,
    ceil,
    pi,
    e,
)

ln = log
abs = fabs
cot = lambda x: cos(x) / sin(x)
sec = lambda x: 1 / cos(x)
csc = lambda x: 1 / sin(x)
acot = lambda x: pi / 2 - atan(x)
asec = lambda x: acos(1 / x)
acsc = lambda x: asin(1 / x)
sign = lambda x: int((x > 0)) - int((x < 0))


from src.default_constants import *


def create_function_from_string(string):
    return eval(f"lambda x, y: {string}")


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
        self.trace_lines_width = DEFAULT_TRACE_LINES_WIDTH
        self.mouse_line_width = DEFAULT_MOUSE_LINE_WIDTH
        self.mouse_line_length = DEFAULT_MOUSE_LINE_LENGTH
        self.function = create_function_from_string(DEFAULT_FUNCTION)
        self.auto_trace_dx = True
        self.trace_dx = 0.01

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
        self.app.update_displayed_trace_dx()
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

        step = (xlim[1] - xlim[0]) / self.num_arrows
        margin = (self.num_arrows // 6) * step + (step / 2 if self.num_arrows % 2 == 0 else 0)

        f = lambda n, s: s * (n // s)
        xs = np.arange(f(xlim[0], step) - margin, xlim[1] + step + margin, step)
        ys = np.arange(f(ylim[0], step) - margin, ylim[1] + step + margin, step)
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

        def trace(trace_forward: bool):
            """
            Helper function for tracing right (forward) and left (backward) from the selected point
            Returns a list containing points that define the resulting curve
            """

            def is_monotonous_on(start, vector, num):
                # self.function gives the slope of the tangent line at a given point
                # --> if > 0: increasing function, if < 0: decreasing function
                sgn = sign(self.function(start[0], start[1]))
                for _ in range(num):
                    start += vector
                    if sign(self.function(start[0], start[1])) != sgn:
                        return False
                return True

            # possible results of singularity handling
            UNKNOWN = 0
            STOP = 1
            INFINITE = 2
            CONTINUE = 3

            # singularity ~ infinite growth --> dx needs to be very small
            singularity_dx = min(1e-6, dx / 1000) * (1 if trace_forward else -1)

            def handle_singularity(x, y):
                """
                This method is called when the derivative is very high.
                It analyzes the situation and returns an instruction what to do next
                - UNKNOWN = something weird is going on
                - STOP = end curve tracing in this direction
                - CONTINUE = continue tracing but with caution
                - INFINITE = this is a singularity, let the curve go to infinity
                """

                # this is in a try block because function() could raise an exception
                try:
                    # get derivative at (x,y)
                    slope = self.function(x, y)
                    if slope > 1e6:  # if its insanely high --> go to infinity
                        return INFINITE
                    # move in the direction of the derivative
                    nx, ny = x + singularity_dx, y + singularity_dx * slope
                    # we are hopefully on the other side of the singularity now
                    # 1. calculate the derivative here
                    nslope = self.function(nx, ny)
                    # 2. calculate the second derivative here
                    second_der_dx = singularity_dx**2
                    second_der = (
                        self.function(nx + second_der_dx, ny + second_der_dx * nslope) - nslope
                    ) / second_der_dx
                except:
                    return UNKNOWN

                # if the function is not monotonous in the direction of the derivative
                # something is most probably going on because
                # - this is either a singularity --> STOP/INFINITE
                # - or just a really steep function --> then it would be monotonous
                def can_continue():
                    vector = np.array([1, slope]) * singularity_dx
                    return is_monotonous_on(np.array([x, y]), vector / 5, 10)

                # convex up - forward
                if slope > 0 and singularity_dx > 0:
                    if second_der > 0 and nslope < 0:  # convex down
                        return INFINITE
                    if second_der > 0 and nslope > 0:  # convex up
                        return CONTINUE if can_continue() else STOP
                    if second_der < 0 and nslope > 0:  # concave up
                        return CONTINUE if can_continue() else INFINITE
                    if second_der < 0 and nslope < 0:  # concave down
                        return STOP

                # concave down - forward
                if slope < 0 and singularity_dx > 0:
                    if second_der > 0 and nslope < 0:  # convex down
                        return CONTINUE if can_continue() else INFINITE
                    if second_der > 0 and nslope > 0:  # convex up
                        return STOP
                    if second_der < 0 and nslope > 0:  # concave up
                        return INFINITE
                    if second_der < 0 and nslope < 0:  # concave down
                        return CONTINUE if can_continue() else STOP

                # concave up - backward
                if slope > 0 and singularity_dx < 0:
                    if second_der > 0 and nslope < 0:  # convex down
                        return STOP
                    if second_der > 0 and nslope > 0:  # convex up
                        return CONTINUE if can_continue() else INFINITE
                    if second_der < 0 and nslope > 0:  # concave up
                        return CONTINUE if can_continue() else STOP
                    if second_der < 0 and nslope < 0:  # concave down
                        return INFINITE

                # convex down - backward
                if slope < 0 and singularity_dx < 0:
                    if second_der > 0 and nslope < 0:  # convex down
                        return CONTINUE if can_continue() else STOP
                    if second_der > 0 and nslope > 0:  # convex up
                        return INFINITE
                    if second_der < 0 and nslope > 0:  # concave up
                        return STOP
                    if second_der < 0 and nslope < 0:  # concave down
                        return CONTINUE if can_continue() else INFINITE

                if second_der == 0:
                    return CONTINUE
                return UNKNOWN

            line = [(x, y)]  # array for storing points on the curve
            center = np.array([x, y])  # center point
            segment_length = 0  # total length of the current segment

            # how many CONTINUEs were there in a row
            continue_count = 0
            while True:
                try:
                    # get the direction vector
                    der = self.function(center[0], center[1])
                    vector = np.array([1, der]) * dx * (1 if trace_forward else -1)
                except:
                    break

                # if the slope is very high --> there might be a singularity
                if fabs(der) > 70:
                    result = handle_singularity(center[0], center[1])

                    if result == UNKNOWN or result == STOP:
                        break
                    if result == INFINITE:
                        # the last line segment should go off the screen
                        line.append(center + np.array([0, sign(der)]) * (ylim[1] - ylim[0]))
                        break
                    if result == CONTINUE:
                        continue_count += 1
                        # if there was 10 CONTINUEs in a row and the function seems to be monotonous in the near future
                        if continue_count % 10 == 0 and is_monotonous_on(
                            np.copy(center), vector / 5, 10
                        ):
                            pass  # assume that there is no singularity --> this is to speed things up
                        else:
                            # make the next step only 'singularity_dx' long --> it should be safe there
                            vector = vector / vector[0] * singularity_dx
                    else:
                        # result is not CONTINUE --> reset counter
                        continue_count = 0
                else:
                    # no singularity --> reset counter
                    continue_count = 0

                center += vector
                # if x is out of bounds --> we are done
                if center[0] < xlim[0] or center[0] > xlim[1]:
                    break

                # if y is out of bounds --> let it go for a while, it might come back
                screen_height = ylim[1] - ylim[0]
                if fabs(center[1] - ylim[0]) > 20 * screen_height:
                    break

                # add a new point if the segment has reached the desired length
                segment_length += np.linalg.norm(vector)
                if segment_length > min_segment_length:
                    line.append((center[0], center[1]))
                    segment_length = 0

            return line

        # trace right and left from the center point
        right_line = trace(trace_forward=True)
        left_line = trace(trace_forward=False)

        # mapping 1->1, 10->7
        line_width = 1 + 6 * (self.trace_lines_width - 1) / 9
        lc = LineCollection([left_line, right_line], color="r", linewidth=line_width)
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
