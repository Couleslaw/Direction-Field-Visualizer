from typing import Callable, Tuple
import numpy as np


from src.math_functions import *
from src.default_constants import (
    TRACE_NUM_SEGMENTS_IN_DIAGONAL,
    DEFAULT_TRACE_COLOR,
    DEFAULT_TRACE_LINES_WIDTH,
    MIN_TRACE_LINES_WIDTH,
    MAX_TRACE_LINES_WIDTH,
    DEFAULT_TRACE_Y_MARGIN,
    DEFAULT_TRACE_PRECISION,
    DEFAULT_SINGULARITY_MIN_SLOPE,
    MAX_TRACE_GRANULARITY,
    MIN_TRACE_GRANULARITY,
    MAX_TRACE_PRECISION,
    MIN_TRACE_PRECISION,
)


def create_function_from_string(string):
    """Receives a string that should be a mathematical function f(x,y) and returns a lambda function."""
    return eval(f"lambda x, y: {string}")


# helper functions for working with vectors


def resize_vector(vector, length):
    return vector / np.linalg.norm(vector) * length


def resize_vector_by_x(vector, x):
    return vector / fabs(vector[0]) * x


def vector_length(vector):
    return np.linalg.norm(vector)


def newtons_method(function: Callable[[float], float], x0, precision=1e-4):
    """Newton's method for finding roots of a function."""

    def relative_error(xnew, xlast):
        return fabs((xnew - xlast) / xnew)

    def derivative(function: Callable[[float], float], x) -> float:
        dx = 1e-12
        return (function(x + dx) - function(x)) / dx

    xlast = x0
    i = 0
    while True:
        xnew = xlast - function(xlast) / derivative(function, xlast)
        error = relative_error(xnew, xlast)
        xlast = xnew
        i = i + 1
        if error < precision or i > 20:
            break
    return xlast


def find_first_intersection(
    slope_func: Callable[[float, float], float],
    singularity_func: Callable[[float, float], float],
    x0,
    y0,
) -> Tuple[float, float]:
    """Draws a tangent line to the slope function at the point (x0, y0) and tries to find the closest intersection of this line with the singularity function.

    Args:
        slope_func (Callable[[float, float], float]): Slope function y'(x) = f(x, y)
        singularity_func (Callable[[float, float], float]): Equation 0 = g(x, y) giving where the slope function has singularities
        x0: initial x value
        y0: initial y value

    Returns:
        Tuple[float, float]: (x, y) of the intersection point
    """

    def line(x):
        return y0 + slope_func(x0, y0) * (x - x0)

    func = lambda x: singularity_func(x, line(x))
    xguess = newtons_method(func, x0)
    return (xguess, line(xguess))


class TraceSettings:
    """Class for storing settings for tracing a solutions of given differential equation."""

    def __init__(self):
        self.line_color = DEFAULT_TRACE_COLOR
        self.line_width = DEFAULT_TRACE_LINES_WIDTH
        self.y_margin = DEFAULT_TRACE_Y_MARGIN
        self.trace_precision = DEFAULT_TRACE_PRECISION
        self.singularity_min_slope = DEFAULT_SINGULARITY_MIN_SLOPE
        self.show_advanced_settings = False
        self.auto_singularity_detection = True
        self.singularity_equations = dict()

    def copy(self):
        """Returns a copy if itself"""
        new = TraceSettings()
        new.line_color = self.line_color
        new.line_width = self.line_width
        new.y_margin = self.y_margin
        new.trace_precision = self.trace_precision
        new.singularity_min_slope = self.singularity_min_slope
        new.show_advanced_settings = self.show_advanced_settings
        new.auto_singularity_detection = self.auto_singularity_detection
        new.singularity_equations = self.singularity_equations.copy()
        return new

    def has_singularity_for(self, equation: str):
        """Returns True if there is a singularity equation for the given equation."""
        return equation in self.singularity_equations

    def get_trace_granularity(self):
        """Converts trace precision to granularity, which is then used to calculate dx."""
        return MIN_TRACE_GRANULARITY + (MAX_TRACE_GRANULARITY - MIN_TRACE_GRANULARITY) * (
            self.trace_precision - MIN_TRACE_PRECISION
        ) / (MAX_TRACE_PRECISION - MIN_TRACE_PRECISION)

    def get_line_width(self):
        """Converts line width entered by the user to a value that is then actually used."""
        # mapping min->1, max->7
        return 1 + 6 * (self.line_width - MIN_TRACE_LINES_WIDTH) / (
            MAX_TRACE_LINES_WIDTH - MIN_TRACE_LINES_WIDTH
        )


class SolutionTracer:
    """Class for tracing a solution curve with an initial point (x0, y0) and a given slope function."""

    # trace direction constants
    FORWARD = 1
    BACKWARD = -1

    # singularity handling return codes
    STOP = 1
    CONTINUE = 3
    INFINITE = 2

    # singularity detection strategy names
    MANUAL = 0
    AUTO = 1

    def __init__(self, settings: TraceSettings, slope_function_string: str, xlim, ylim):
        self.settings = settings
        self.slope_func = create_function_from_string(slope_function_string)

        # determine the singularity detection strategy
        if not settings.auto_singularity_detection and settings.has_singularity_for(
            slope_function_string
        ):
            self.singularity_eq = create_function_from_string(
                self.settings.singularity_equations[slope_function_string]
            )
            self.detection = self.MANUAL
        else:
            self.singularity_eq = None
            self.detection = self.AUTO

        # calculate diagonal length and max line segment length
        self.xlim = xlim
        self.ylim = ylim
        self.diagonal_len = np.sqrt((xlim[1] - xlim[0]) ** 2 + (ylim[1] - ylim[0]) ** 2)
        self.max_line_segment_length = self.diagonal_len / TRACE_NUM_SEGMENTS_IN_DIAGONAL

    def is_monotonous_on(self, start, diff_vector, num_points) -> bool:
        """
        Checks if the slope function is monotonous on the line segment from start to start + diff_vector.
        Checks the slope at num_points equidistant points on the segment.
        """

        sgn = sign(self.slope_func(start[0], start[1]))
        diff = diff_vector / num_points

        # try because slope_func is unsafe
        try:
            for _ in range(num_points):
                start += diff
                if sign(self.slope_func(start[0], start[1])) != sgn:
                    return False
            return True
        except:
            return False

    def should_stop_if_y_out_of_bounds(self, y) -> bool:
        """This should be called when the y value is out of bounds. Returns True if the tracing should stop."""
        # distance from edge of the screen
        dist = fabs(y - self.ylim[0]) if y < self.ylim[0] else fabs(y - self.ylim[1])

        # automatic detection --> cut off when further than screen_height * y_margin
        if self.detection == self.AUTO:
            return dist > (self.ylim[1] - self.ylim[0]) * self.settings.y_margin

        # manual detection --> cut off when there might be a singularity nearby
        # there is no need to cut off once a certain height is reached as in automatic detection
        # because this i
        return vector_length(self.sing_diff) < self.singularity_alert_distance

    def possible_singularity_at(self, x, y) -> bool:
        """Checks if there might a singularity close to the point (x, y)."""

        # if automatic detection is enabled, check if the slope is too steep
        if self.detection == self.AUTO:
            try:  # slope_func is unsafe
                return fabs(self.slope_func(x, y)) > self.settings.singularity_min_slope
            except:
                # probably division by zero --> close to singularity
                return True

        # if used correctly, the singularity_eq should be set
        assert self.singularity_eq is not None

        try:
            singularity_guess = find_first_intersection(
                self.slope_func, self.singularity_eq, x, y
            )
        except:
            # newtons method probably failed --> no singularity close
            # but still set a valid sing_diff, it is used during the iteration
            # --> set sing_diff to a large vector in the correct direction
            self.sing_diff = resize_vector(self.vector, 10 * self.singularity_alert_distance)
            return False

        diff = np.array([x - singularity_guess[0], y - singularity_guess[1]])
        self.sing_diff = diff

        # if the singularity is close enough, return True
        return vector_length(diff) < self.singularity_alert_distance

    def handle_singularity(self, x, y):
        """
        This function is called when there is reason to believe that a singularity is close to the point (x, y).
        Return a strategy on how to proceed
        - CONTINUE = cautiously continue, your next step should be safe
        - STOP = stop tracing, a STOP singularity was detected
        - INFINITE = an infinite singularity was detected, the line should go off screen
        """

        # calculate the first derivative at (x,y)
        # get vector in the direction of the slope: diff
        # determine a new point (nx, ny) = (x, y) + diff
        # hopefully its on the other side of the singularity
        # calculate the first and second derivative at (nx, ny)

        # this is in a try block because slope_func is unsafe
        try:
            # auto detection --> use sing_dx to determine size of diff
            if self.detection == self.AUTO:
                diff = np.array([self.sing_dx, self.sing_dx * self.slope]) * self.direction

            # manual detection --> use distance to singularity to determine size of diff
            else:
                # sing_diff = distance to singularity
                diff = 2 * self.sing_diff  # jump to the other side
                # newton's method is not perfect, the sign might be wrong
                if sign(diff[0]) != sign(self.vector[0]):
                    diff *= -1
                # if the jump is too big, resize it
                if fabs(diff[0]) > self.max_dx:
                    diff = resize_vector_by_x(diff, self.max_dx)
                # if the jump is too small, resize it
                # prevents getting infinitely close to the singularity but never reaching it
                if vector_length(diff) < self.min_step:
                    diff = resize_vector(diff, self.min_step)

            # jump to the other side of the singularity (hopefully)
            nx, ny = x + diff[0], y + diff[1]

            # calculate first and second derivative at (nx, ny)
            nslope = self.slope_func(nx, ny)
            sdx = 1e-15
            second_der = (self.slope_func(nx + sdx, ny + sdx * nslope) - nslope) / sdx

        except:
            # either division-by-zero, math-domain-error or the function is not valid
            # --> something is wrong, stop tracing
            return self.STOP

        # helper function to determine if the tracing can continue
        def can_continue():
            # manual detection will deal with the singularity
            if self.detection == self.MANUAL:
                return True

            # if the slope is very steep, there is almost certainly a singularity --> STOP
            if fabs(self.slope) > 1e6:
                return False

            # this is automatic detection --> steep slope
            # if the function is not monotonic in the neighborhood of this suspected singularity
            # there is most probably a singularity --> STOP
            vector = resize_vector_by_x(diff, self.sing_dx)
            return self.is_monotonous_on(np.array([x, y]), 2 * vector, 10)

        # convex up - forward
        if self.slope > 0 and self.direction == self.FORWARD:
            if second_der > 0 and nslope < 0:  # convex down
                return self.INFINITE
            if second_der > 0 and nslope > 0:  # convex up
                return self.CONTINUE if can_continue() else self.STOP
            if second_der < 0 and nslope > 0:  # concave up
                return self.CONTINUE if can_continue() else self.INFINITE
            if second_der < 0 and nslope < 0:  # concave down
                return self.STOP

        # concave down - forward
        if self.slope < 0 and self.direction == self.FORWARD:
            if second_der > 0 and nslope < 0:  # convex down
                return self.CONTINUE if can_continue() else self.INFINITE
            if second_der > 0 and nslope > 0:  # convex up
                return self.STOP
            if second_der < 0 and nslope > 0:  # concave up
                return self.INFINITE
            if second_der < 0 and nslope < 0:  # concave down
                return self.CONTINUE if can_continue() else self.STOP

        # concave up - backward
        if self.slope > 0 and self.direction == self.BACKWARD:
            if second_der > 0 and nslope < 0:  # convex down
                return self.STOP
            if second_der > 0 and nslope > 0:  # convex up
                return self.CONTINUE if can_continue() else self.INFINITE
            if second_der < 0 and nslope > 0:  # concave up
                return self.CONTINUE if can_continue() else self.STOP
            if second_der < 0 and nslope < 0:  # concave down
                return self.INFINITE

        # convex down - backward
        if self.slope < 0 and self.direction == self.BACKWARD:
            if second_der > 0 and nslope < 0:  # convex down
                return self.CONTINUE if can_continue() else self.STOP
            if second_der > 0 and nslope > 0:  # convex up
                return self.INFINITE
            if second_der < 0 and nslope > 0:  # concave up
                return self.STOP
            if second_der < 0 and nslope < 0:  # concave down
                return self.CONTINUE if can_continue() else self.INFINITE

        if second_der == 0:
            return self.CONTINUE
        return self.STOP

    def trace(self, x0, y0, direction) -> list[Tuple[float, float]]:
        """
        Traces a solution curve starting at (x0, y0) in the given direction.
        Returns a list of points that are on the curve.
        """
        self.direction = direction
        line = [(x0, y0)]
        point = np.array([x0, y0])  # current point

        # manual detection
        self.min_step = self.diagonal_len / 10 ** self.settings.get_trace_granularity()
        self.max_step = self.diagonal_len / 1000
        self.singularity_alert_distance = self.diagonal_len / 100

        # max_dx is the maximum step size in x direction
        self.max_dx = (
            self.xlim[1] - self.xlim[0]
        ) / 10 ** self.settings.get_trace_granularity()
        # sing_dx is the step size used when a singularity is detected in auto-detection mode
        self.sing_dx = min(1e-6, self.max_dx / 1000)

        # gives the number of times in a row the tracing continued after a singularity was detected
        # is used in auto-detection mode
        continue_count = 0
        current_line_segment_length = 0  # for adding new points

        while True:
            try:  # slope_func is unsafe
                self.slope = self.slope_func(point[0], point[1])
                self.vector = np.array([1, self.slope]) * direction
            except:
                break

            # no singularity detected
            if not self.possible_singularity_at(point[0], point[1]):
                continue_count = 0  # reset continue count
                self.vector = resize_vector_by_x(self.vector, self.max_dx)

                # if not out of bounds and the step is too big, resize it
                # allow mig steps out of bounds to save time
                if (
                    self.ylim[0] <= point[1] <= self.ylim[1]
                    and vector_length(self.vector) > self.max_step
                ):
                    self.vector = resize_vector(self.vector, self.max_step)

            # singularity detected
            else:
                # get strategy on how to proceed
                strategy = self.handle_singularity(point[0], point[1])

                # if tracing should stop
                if strategy == self.STOP:
                    # if manual detection --> last point will end at the singularity
                    if self.detection == self.MANUAL:
                        point += resize_vector(self.vector, vector_length(self.sing_diff))
                    break

                # if the function goes off to infinity
                if strategy == self.INFINITE:
                    # last line segment should go off screen
                    line.append(
                        point
                        + np.array([0, sign(self.slope) * direction])
                        * (self.ylim[1] - self.ylim[0])
                    )
                    break

                # if the tracing should continue
                if strategy == self.CONTINUE:
                    # manual detection
                    if self.detection == self.MANUAL:
                        # step_size = distance to singularity / 2
                        step_size = vector_length(self.sing_diff) / 2
                        self.vector = resize_vector(self.vector, step_size)
                        # if the step is too big, resize it
                        if fabs(self.vector[0]) > self.max_dx:
                            self.vector = resize_vector_by_x(self.vector, self.max_dx)

                    # automatic detection
                    else:
                        continue_count += 1
                        # resize vector to have normal dx
                        self.vector = resize_vector_by_x(self.vector, self.max_dx)

                        # if we continued a couple times in a row and the function seems to be monotonic ahead
                        # --> probably safe
                        if continue_count % 10 == 0 and self.is_monotonous_on(
                            point, 2 * self.vector, 20
                        ):
                            pass  # keep normal dx

                        else:
                            # resize vector to have the same dx as is used in singularity detection
                            # step of this size should be safe
                            self.vector = resize_vector_by_x(self.vector, self.sing_dx)

            # move to the next point
            point += self.vector

            # if x is out of bounds --> break
            if point[0] < self.xlim[0] or point[0] > self.xlim[1]:
                break

            # if y is out of bounds --> maybe break
            if point[1] < self.ylim[0] or point[1] > self.ylim[1]:
                if self.should_stop_if_y_out_of_bounds(point[1]):
                    break

            # add a new point if the segment has reached the desired length
            current_line_segment_length += vector_length(self.vector)
            if current_line_segment_length > self.max_line_segment_length:
                line.append((point[0], point[1]))
                current_line_segment_length = 0

        # add the last point
        line.append((point[0], point[1]))
        return line
