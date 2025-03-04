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
    pow,
    fabs,
    floor,
    ceil,
    pi,
    e,
)

from typing import Callable, Any
from numpy import floating
import regex as re

# define some other common math function
ln = log
abs = fabs
cot: Callable[[float], float] = lambda x: cos(x) / sin(x)
sec: Callable[[float], float] = lambda x: 1 / cos(x)
csc: Callable[[float], float] = lambda x: 1 / sin(x)
acot: Callable[[float], float] = lambda x: pi / 2 - atan(x)
asec: Callable[[float], float] = lambda x: acos(1 / x)
acsc: Callable[[float], float] = lambda x: asin(1 / x)
sign: Callable[[float], int] = lambda x: int((x > 0)) - int((x < 0))


def create_function_from_string(string: str) -> Callable[[floating, floating], floating] | Any:
    """Receives a string that should be a mathematical function f(x,y) and returns a lambda expression."""
    # check using reges if the string contains `input`
    if re.search(r"\binput\b", string):
        return None
    return eval(f"lambda x, y: {string}")


def try_get_value_from_string(string: str) -> float | None:
    """Receives a string that should contain a mathematical expression which can be evaluated to a real number and tries to evaluate it.

    Args:
        string (str): String representation of the expression.

    Returns:
        out (float | None): The result if the expression is valid, None otherwise.
    """

    try:
        res = float(eval(string))
        return res
    except:
        return None
