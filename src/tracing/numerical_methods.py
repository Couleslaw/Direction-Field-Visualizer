from typing import Callable, Tuple
from math import fabs


def newtons_method(
    function: Callable[[float], float], x0: float, precision: float = 1e-5, max_iter: int = 30
) -> float:
    """Newton's method for finding roots of a function.

    Args:
        function (Callable[[float], float]): Function to find the root of.
        x0 (float): Initial guess.
        precision (float, optional): Desired relative error. Defaults to 1e-5.
        max_iter (int, optional): Maximum number of iterations. Defaults to 30.

    Returns:
        out (float): The best estimate of the root found.
    """

    def relative_error(xnew: float, xlast: float) -> float:
        return fabs((xnew - xlast) / xnew)

    def derivative(function: Callable[[float], float], x: float) -> float:
        dx = 1e-12
        return (function(x + dx) - function(x - dx)) / (2 * dx)

    xlast = x0
    i = 0
    while True:
        xnew = xlast - function(xlast) / derivative(function, xlast)
        if xnew == 0:
            return xnew
        error = relative_error(xnew, xlast)
        xlast = xnew
        if error < precision or (i := i + 1) > max_iter:
            break
    return xlast


def find_first_intersection(
    equation: Callable[[float, float], float],
    slope: float,
    x0: float,
    y0: float,
) -> Tuple[float, float]:
    """Draws a line passing through `(x0, y0)` with slope `slope` and tries to find the closest intersection of this line with the function `equation(x,y)=0`.

    Args:
        equation (Callable[[float, float], float]): Equation `0 = g(x, y)`. (Giving where the slope function has singularities)
        slope (float): slope of the line
        x0 (float): initial `x` value
        y0 (float): initial `y` value

    Returns
    -------
    x, y : (float, float):
        The coordinates of the intersection point

    Example
    -------
    >>> equation = lambda x, y: y*x  # eq:   y*x = 0
    >>> x0, y0, slope = 2, 3, 1      # line: y = x + 1

    So we have `y*x = 0`  and  `y = x + 1`  =>  `x*(x+1) = 0`  =>  `x = 0 or x = -1`
    The closes value to `x0 = 2` is `x = 0`, so this function should return (0, 1)
    """

    def line(x: float) -> float:
        return y0 + slope * (x - x0)

    xguess = newtons_method(lambda x: equation(x, line(x)), x0)
    return (xguess, line(xguess))
