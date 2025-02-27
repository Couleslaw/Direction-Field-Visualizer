from src.math_functions import create_function_from_string, sqrt
from src.default_constants import (
    DEFAULT_FUNCTION,
    DEFAULT_ARROW_LENGTH,
    DEFAULT_ARROW_WIDTH,
    MIN_ARROW_WIDTH,
    MAX_ARROW_WIDTH,
    DEFAULT_NUM_ARROWS,
    DEFAULT_COLOR_MAP,
    DEFAULT_COLOR_PRECISION,
    DEFAULT_COLOR_CONTRAST,
    MIN_COLOR_CONTRAST,
    MAX_COLOR_CONTRAST,
    MIN_COLOR_EXP,
    MAX_COLOR_EXP,
)
from typing import Tuple


class DirectionFieldSettings:
    """Class to store settings for the direction field."""

    color_exp_base = 1.4

    def __init__(self):
        # arrow settings
        self.arrow_length = DEFAULT_ARROW_WIDTH
        self.arrow_width = DEFAULT_ARROW_LENGTH
        self.num_arrows = DEFAULT_NUM_ARROWS

        # color settings
        self.show_colors = True
        self.color_map = DEFAULT_COLOR_MAP
        self.color_contrast = DEFAULT_COLOR_CONTRAST
        self.color_precision = DEFAULT_COLOR_PRECISION

        # slope function
        self.function_string = DEFAULT_FUNCTION
        self.function = create_function_from_string(self.function_string)

        # grid and axes
        self.show_grid = False
        self.show_axes = True

    def get_arrow_length(self, xlim: Tuple[float, float], ylim: Tuple[float, float]) -> float:
        """Returns the arrow length given limits of the axes."""
        diagonal = sqrt((xlim[1] - xlim[0]) ** 2 + (ylim[1] - ylim[0]) ** 2)
        return diagonal * self.arrow_length / 200

    def get_arrow_width(self):
        """Returns the arrow width."""
        return 0.001 + 0.009 * (self.arrow_width - MIN_ARROW_WIDTH) / (
            MAX_ARROW_WIDTH - MIN_ARROW_WIDTH
        )

    def get_color_exp(self):
        """Returns the exponent for the color contrast."""
        a = (MAX_COLOR_EXP - MIN_COLOR_EXP) / (
            self.color_exp_base**MAX_COLOR_CONTRAST - self.color_exp_base**MIN_COLOR_CONTRAST
        )
        b = MIN_COLOR_EXP - a * self.color_exp_base**MIN_COLOR_CONTRAST
        return a * self.color_exp_base**self.color_contrast + b

    def get_curvature_dx(self):
        """Returns the dx for calculating the curvature."""
        return 1 / 10 ** (self.color_precision + 1)
