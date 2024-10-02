from typing import Callable, Tuple
import matplotlib.pyplot as plt
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
    return eval(f"lambda x, y: {string}")


def relative_error(xnew, xlast):
    return fabs((xnew - xlast) / xnew)


def derivative(function: Callable[[float], float], x) -> float:
    dx = 1e-12
    return (function(x + dx) - function(x)) / dx


def newtons_method(function: Callable[[float], float], x0, precision=1e-4):
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
    method=newtons_method,
) -> Tuple[float, float]:
    def der(x=x0, y=y0, n=1) -> float:
        if n == 1:
            return slope_func(x, y)
        dx = 1e-12
        diff = der(x, y, n - 1)
        nx = x + dx
        ny = y + dx * diff
        return (der(nx, ny, n - 1) - diff) / dx

    def approx(x):
        return y0 + der(n=1) * (x - x0)

    func = lambda x: singularity_func(x, approx(x))
    xguess = method(func, x0)
    # print(f"Found solution: x={xguess}, y={approx(xguess)}")
    return (xguess, approx(xguess))


class TraceSettings:
    def __init__(self):
        # Initialize color attribute with default red color
        self.line_color = DEFAULT_TRACE_COLOR
        self.line_width = DEFAULT_TRACE_LINES_WIDTH
        self.show_advanced_settings = False
        self.y_margin: float = DEFAULT_TRACE_Y_MARGIN
        self.trace_precision = DEFAULT_TRACE_PRECISION
        self.auto_singularity_detection = True
        self.singularity_min_slope = DEFAULT_SINGULARITY_MIN_SLOPE
        self.singularity_equations = dict()

    def copy(self):
        new = TraceSettings()
        new.line_color = self.line_color
        new.line_width = self.line_width
        new.show_advanced_settings = self.show_advanced_settings
        new.y_margin = self.y_margin
        new.trace_precision = self.trace_precision
        new.auto_singularity_detection = self.auto_singularity_detection
        new.singularity_min_slope = self.singularity_min_slope
        new.singularity_equations = self.singularity_equations.copy()
        return new

    def has_singularity_for(self, equation: str):
        return equation in self.singularity_equations

    def get_trace_granularity(self):
        return MIN_TRACE_GRANULARITY + (MAX_TRACE_GRANULARITY - MIN_TRACE_GRANULARITY) * (
            self.trace_precision - MIN_TRACE_PRECISION
        ) / (MAX_TRACE_PRECISION - MIN_TRACE_PRECISION)

    def get_line_width(self):
        # mapping min->1, max->7
        return 1 + 6 * (self.line_width - MIN_TRACE_LINES_WIDTH) / (
            MAX_TRACE_LINES_WIDTH - MIN_TRACE_LINES_WIDTH
        )


def resize_vector(vector, length):
    return vector / np.linalg.norm(vector) * length


def resize_vector_by_x(vector, x):
    return vector / fabs(vector[0]) * x


def vector_length(vector):
    return np.linalg.norm(vector)


class SolutionTracer:
    FORWARD = 1
    BACKWARD = -1

    STOP = 1
    CONTINUE = 3
    INFINITE = 2

    MANUAL = 0
    AUTO = 1

    def __init__(self, settings: TraceSettings, function_str: str, xlim, ylim):
        self.settings = settings
        self.slope_func = create_function_from_string(function_str)
        if not settings.auto_singularity_detection and settings.has_singularity_for(
            function_str
        ):
            self.singularity_eq = create_function_from_string(
                self.settings.singularity_equations[function_str]
            )
            self.detection = self.MANUAL
        else:
            self.singularity_eq = None
            self.detection = self.AUTO
        self.xlim = xlim
        self.ylim = ylim
        self.diagonal_len = np.sqrt((xlim[1] - xlim[0]) ** 2 + (ylim[1] - ylim[0]) ** 2)
        self.max_line_segment_length = self.diagonal_len / TRACE_NUM_SEGMENTS_IN_DIAGONAL

    def is_monotonous_on(self, start, diff_vector, num_points) -> bool:
        sgn = sign(self.slope_func(start[0], start[1]))
        diff = diff_vector / num_points
        try:
            for _ in range(num_points):
                start += diff
                if sign(self.slope_func(start[0], start[1])) != sgn:
                    return False
            return True
        except:
            return False

    def possible_singularity_at(self, x, y) -> bool:
        if self.detection == self.AUTO:
            try:
                return fabs(self.slope_func(x, y)) > self.settings.singularity_min_slope
            except:
                return True

        assert self.singularity_eq is not None
        try:
            singularity_guess = find_first_intersection(
                self.slope_func, self.singularity_eq, x, y
            )
        except:
            self.sing_diff = resize_vector(self.vector, 10 * self.max_step)
            return False

        diff = np.array([x - singularity_guess[0], y - singularity_guess[1]])
        self.sing_diff = diff

        # if sign(diff[0]) != sign(self.vector[0]) and vector_length(diff) > self.max_step / 10:
        #     return False

        return vector_length(diff) < self.max_step

    def should_stop_if_y_out_of_bounds(self, y) -> bool:
        dist = fabs(y - self.ylim[0]) if y < self.ylim[0] else fabs(y - self.ylim[1])

        if self.detection == self.AUTO:
            return dist > (self.ylim[1] - self.ylim[0]) * self.settings.y_margin

        return vector_length(self.sing_diff) < self.max_step

    def handle_singularity(self, x, y):
        try:
            if self.detection == self.AUTO:
                diff = np.array([self.sing_dx, self.sing_dx * self.slope]) * self.direction

            else:
                diff = 2 * self.sing_diff
                if sign(diff[0]) != sign(self.vector[0]):
                    diff *= -1
                if fabs(diff[0]) > self.max_dx:
                    diff = resize_vector_by_x(diff, self.max_dx)
                if vector_length(diff) < self.min_step:
                    diff = resize_vector(diff, self.min_step)

            nx, ny = x + diff[0], y + diff[1]
            nslope = self.slope_func(nx, ny)
            sdx = 1e-15
            second_der = (self.slope_func(nx + sdx, ny + sdx * nslope) - nslope) / sdx
            # print(
            # f"Handle: x={x:.5f}, y={y:.5f}, slope={self.slope:.2f} nslope={nslope:.2f}, sign(der2)={sign(second_der)}"
            # )
        except:
            return self.STOP

        def can_continue():
            if self.detection == self.MANUAL:
                return True

            if fabs(self.slope) > 1e6:
                return False

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
        self.direction = direction
        line = [(x0, y0)]
        point = np.array([x0, y0])

        # manual detection
        self.min_step = self.diagonal_len / 10 ** self.settings.get_trace_granularity()
        self.max_step = self.diagonal_len / 100

        self.max_dx = (
            self.xlim[1] - self.xlim[0]
        ) / 10 ** self.settings.get_trace_granularity()
        self.sing_dx = min(1e-6, self.max_dx / 1000)

        current_line_segment_length = 0
        continue_count = 0

        while True:
            try:
                self.slope = self.slope_func(point[0], point[1])
                self.vector = np.array([1, self.slope]) * direction
            except:
                break

            if not self.possible_singularity_at(point[0], point[1]):
                continue_count = 0
                self.vector = resize_vector_by_x(self.vector, self.max_dx)
                # TODO co kdyz tak funkce jde fakt vysoko

                if (
                    vector_length(self.vector) > self.max_step
                    and self.ylim[0] <= point[1] <= self.ylim[1]
                ):
                    self.vector = resize_vector(self.vector, self.max_step)

            else:
                # print(
                # f"Sing : x={point[0]:.5f}, y={point[1]:.5f}, dist={vector_length(self.sing_diff):.5f}, slope={self.slope:.1f}"
                # )
                strategy = self.handle_singularity(point[0], point[1])
                if strategy == self.STOP:
                    break
                if strategy == self.INFINITE:
                    # last line segment should go off screen
                    line.append(
                        point
                        + np.array([0, sign(self.slope) * direction])
                        * (self.ylim[1] - self.ylim[0])
                    )
                    break
                if strategy == self.CONTINUE:
                    if self.detection == self.MANUAL:
                        step_size = vector_length(self.sing_diff) / 2
                        self.vector = resize_vector(self.vector, step_size)
                        if fabs(self.vector[0]) > self.max_dx:
                            self.vector = resize_vector_by_x(self.vector, self.max_dx)

                    else:
                        continue_count += 1
                        self.vector = resize_vector_by_x(self.vector, self.max_dx)
                        if not (
                            continue_count % 10 == 0
                            and self.is_monotonous_on(point, 2 * self.vector, 20)
                        ):
                            self.vector = resize_vector_by_x(self.vector, self.sing_dx)

            point += self.vector

            # if x is out of bounds
            if point[0] < self.xlim[0] or point[0] > self.xlim[1]:
                break

            # if y is out of bounds
            if point[1] < self.ylim[0] or point[1] > self.ylim[1]:
                if self.should_stop_if_y_out_of_bounds(point[1]):
                    break

            # add a new point if the segment has reached the desired length
            current_line_segment_length += vector_length(self.vector)
            if current_line_segment_length > self.max_line_segment_length:
                line.append((point[0], point[1]))
                current_line_segment_length = 0

        line.append((point[0], point[1]))
        return line
