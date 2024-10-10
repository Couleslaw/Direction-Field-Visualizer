from typing import Callable, Tuple
from math import fabs


def newtons_method(function: Callable[[float], float], x0, precision=1e-5):
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
        if xnew == 0:
            return xnew
        error = relative_error(xnew, xlast)
        xlast = xnew
        i = i + 1
        if error < precision or i > 30:
            break
    return xlast


def find_first_intersection(
    singularity_func: Callable[[float, float], float],
    slope,
    x0,
    y0,
) -> Tuple[float, float]:
    """Draws passing through (x0, y0) with slope 'slope' and tries to find the closest intersection of this line with the singularity function.

    Args:
        singularity_func (Callable[[float, float], float]): Equation 0 = g(x, y) giving where the slope function has singularities
        slope: slope of the line
        x0: initial x value
        y0: initial y value

    Returns:
        Tuple[float, float]: (x, y) of the intersection point
    """

    def line(x):
        return y0 + slope * (x - x0)

    func = lambda x: singularity_func(x, line(x))
    xguess = newtons_method(func, x0)
    return (xguess, line(xguess))
