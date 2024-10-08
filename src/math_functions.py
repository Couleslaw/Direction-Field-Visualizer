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

ln = log
abs = fabs
cot = lambda x: cos(x) / sin(x)
sec = lambda x: 1 / cos(x)
csc = lambda x: 1 / sin(x)
acot = lambda x: pi / 2 - atan(x)
asec = lambda x: acos(1 / x)
acsc = lambda x: asin(1 / x)
sign = lambda x: int((x > 0)) - int((x < 0))


def create_function_from_string(string):
    """Receives a string that should be a mathematical function f(x,y) and returns a lambda function."""
    return eval(f"lambda x, y: {string}")
