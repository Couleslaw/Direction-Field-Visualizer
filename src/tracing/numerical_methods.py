from typing import Callable, Tuple
from numpy import floating, fabs


def newtons_method(
    function: Callable[[floating], floating],
    x0: floating,
    precision: float = 1e-5,
    max_iter: int = 30,
) -> floating:
    """Newton's method for finding roots of a function.

    Args:
        function (Callable[[floating], floating]): Function to find the root of.
        x0 (floating): Initial guess.
        precision (float, optional): Desired relative error. Defaults to 1e-5.
        max_iter (int, optional): Maximum number of iterations. Defaults to 30.

    Returns:
        out (floating): The best estimate of the root found.
    """

    def relative_error(xnew: floating, xlast: floating) -> floating:
        # if there would be division by zero --> shift a bit
        if xnew == 0:
            xnew += precision
            xlast += precision
        return fabs((xnew - xlast) / xnew)

    def derivative(function: Callable[[floating], floating], x: floating) -> floating:
        dx = 1e-12
        return (function(x + dx) - function(x - dx)) / (2 * dx)

    xlast = x0
    i = 0
    while True:
        der = derivative(function, xlast)
        #  if we would run into a dead end --> try moving the point a bot
        if der == 0:
            xnew = xlast * 1.2
        else:
            xnew = xlast - function(xlast) / der
        error = relative_error(xnew, xlast)
        xlast = xnew
        if error < precision or (i := i + 1) > max_iter:
            break
    return xlast


def find_first_intersection(
    equation: Callable[[floating, floating], floating],
    slope: floating,
    x0: floating,
    y0: floating,
) -> Tuple[floating, floating]:
    """Draws a line passing through `(x0, y0)` with slope `slope` and tries to find the closest intersection of this line with the function `equation(x,y)=0`.

    Args:
        equation (Callable[[floating, floating], floating]): Equation `0 = g(x, y)`. (Giving where the slope function has singularities)
        slope (floating): slope of the line
        x0 (floating): initial `x` value
        y0 (floating): initial `y` value

    Returns
    -------
    x, y : (floating, floating):
        The coordinates of the intersection point

    Example
    -------
    >>> equation = lambda x, y: y*x  # eq:   y*x = 0
    >>> x0, y0, slope = 2, 3, 1      # line: y = x + 1

    So we have `y*x = 0`  and  `y = x + 1`  =>  `x*(x+1) = 0`  =>  `x = 0 or x = -1`
    The closes value to `x0 = 2` is `x = 0`, so this function should return (0, 1)
    """

    def line(x: floating) -> floating:
        return y0 + slope * (x - x0)

    xguess = newtons_method(lambda x: equation(x, line(x)), x0)
    return (xguess, line(xguess))
