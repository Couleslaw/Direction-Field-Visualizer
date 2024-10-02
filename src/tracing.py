from typing import Callable, Tuple
import matplotlib.pyplot as plt
import numpy as np


from src.math_functions import *
from src.default_constants import (
    TRACE_NUM_SEGMENTS_IN_DIAGONAL,
    DEFAULT_TRACE_COLOR,
    DEFAULT_TRACE_LINES_WIDTH,
    DEFAULT_TRACE_Y_MARGIN,
    DEFAULT_TRACE_PRECISION,
    DEFAULT_SINGULARITY_MIN_SLOPE,
)


class TraceSettings:
    def __init__(self):
        # Initialize color attribute with default red color
        self.line_color = DEFAULT_TRACE_COLOR
        self.line_width = DEFAULT_TRACE_LINES_WIDTH
        self.y_margin: float = DEFAULT_TRACE_Y_MARGIN
        self.trace_precision = DEFAULT_TRACE_PRECISION
        self.auto_singularity_detection = True
        self.singularity_min_slope = DEFAULT_SINGULARITY_MIN_SLOPE
        self.singularity_equations = dict()

    def copy(self):
        new = TraceSettings()
        new.line_color = self.line_color
        new.line_width = self.line_width
        new.y_margin = self.y_margin
        new.trace_precision = self.trace_precision
        new.auto_singularity_detection = self.auto_singularity_detection
        new.singularity_min_slope = self.singularity_min_slope
        new.singularity_equations = self.singularity_equations.copy()
        return new

    def has_singularity_for(self, equation: str):
        return equation in self.singularity_equations


def relative_error(x_now, x_last):
    return fabs((x_now - x_last) / x_now)


def derivative(function: Callable[[float], float], x) -> float:
    dx = 1e-12
    return (function(x + dx) - function(x)) / dx


def newtons_method(function: Callable[[float], float], x0, precision=1e-4):
    xlast = x0
    i = 0
    while True:
        try:
            xnew = xlast - function(xlast) / derivative(function, xlast)
        except FloatingPointError:
            print(f"Zero division error, x0={x0} i={i}", xlast, function(xlast))
            break
        error = relative_error(xnew, xlast)
        xlast = xnew
        i = i + 1
        if error < precision or i > 100:
            break
    return xlast


# TODO osetrit, cele je to unsafe vuci vyjimkam
# TODO komplet prepsat trasovani zvlast pro auto a pro manual
# manual hlavni myslenka: nikdy neudelat vetsi krok nez je dist_to_singularity


def find_first_solution(
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
        return (
            y0
            + der(n=1) * (x - x0)
            # + der(n=2) * (x - x0) ** 2 / 2
            # + der(n=3) * (x - x0) ** 3 / 6
        )

    func = lambda x: singularity_func(x, approx(x))
    xguess = method(func, x0)
    # print(f"Found solution: x={xguess}, y={approx(xguess)}")
    return (xguess, approx(xguess))
