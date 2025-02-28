from src.math_functions import create_function_from_string, sqrt
from src.default_constants import *
from typing import Tuple, Callable, Any


class DirectionFieldSettings:
    """Class to store settings for the direction field."""

    # base of an exponential used to scale the curvatures before converting to colors
    __color_exp_base = 1.4

    def __init__(self) -> None:
        # arrow settings
        self.__arrow_length: int = DEFAULT_ARROW_LENGTH
        self.__arrow_width: int = DEFAULT_ARROW_WIDTH
        self.num_arrows: int = DEFAULT_NUM_ARROWS

        # color settings
        self.show_colors: bool = True
        self.color_map: str = DEFAULT_COLOR_MAP
        self.color_contrast: int = DEFAULT_COLOR_CONTRAST
        self.color_precision: int = DEFAULT_COLOR_PRECISION

        # slope function
        self.function_string: str = DEFAULT_FUNCTION
        self.function: Callable[[float, float], float] | Any = create_function_from_string(
            self.function_string
        )

        # grid and axes
        self.show_grid: bool = False
        self.show_axes: bool = True

    def set_arrow_length(self, length: int) -> None:
        """Sets new arrow length based on the displayed number."""
        self.__arrow_length = length

    def calculate_arrow_length(self, xlim: Tuple[float, float], ylim: Tuple[float, float]) -> float:
        """Returns the arrow length given limits of the axes."""
        diagonal = sqrt((xlim[1] - xlim[0]) ** 2 + (ylim[1] - ylim[0]) ** 2)
        return diagonal * self.__arrow_length / 200

    @property
    def arrow_width(self) -> float:
        """Returns the arrow width."""
        return 0.001 + 0.009 * (self.__arrow_width - MIN_ARROW_WIDTH) / (
            MAX_ARROW_WIDTH - MIN_ARROW_WIDTH
        )

    @arrow_width.setter
    def arrow_width(self, width: int):
        self.__arrow_width = width

    @property
    def color_exp(self) -> float:
        """Returns the exponent for the color contrast."""
        a = (MAX_COLOR_EXP - MIN_COLOR_EXP) / (
            self.__color_exp_base**MAX_COLOR_CONTRAST - self.__color_exp_base**MIN_COLOR_CONTRAST
        )
        b = MIN_COLOR_EXP - a * self.__color_exp_base**MIN_COLOR_CONTRAST
        return a * self.__color_exp_base**self.color_contrast + b

    @property
    def curvature_dx(self) -> float:
        """Returns the dx for calculating the curvature."""
        return 1 / 10 ** (self.color_precision + 1)
