from __future__ import annotations
from enum import Enum

import numpy as np
from src.math_functions import create_function_from_string
from src.default_constants import *

from typing import Dict, Tuple, List, TypeAlias


class TraceSettings:
    """Class for storing settings for tracing a solutions of given differential equation."""

    class Strategy(Enum):
        """Strategy of singularity detection"""

        AUTOMATIC = 0
        MANUAL = 1
        NONE = 2

    def __init__(self) -> None:
        self.line_color = DEFAULT_TRACE_COLOR
        self.displayed_line_width: int = DEFAULT_TRACE_LINES_WIDTH
        self.y_margin: float = DEFAULT_TRACE_Y_MARGIN
        self.trace_precision = DEFAULT_TRACE_PRECISION
        self.singularity_min_slope = DEFAULT_SINGULARITY_MIN_SLOPE
        self.show_advanced_settings = False

        # slope function string -> singularity equation string
        self.__singularity_equations: Dict[str, str] = {"x/y": "y"}

        # remembers which strategy to use for detecting singularities for different slope function
        self.__preferred_detection: Dict[str, TraceSettings.Strategy] = dict()

    def copy(self) -> TraceSettings:
        """Returns a copy if itself"""
        new = TraceSettings()
        new.line_color = self.line_color
        new.displayed_line_width = self.displayed_line_width
        new.trace_precision = self.trace_precision
        new.y_margin = self.y_margin
        new.singularity_min_slope = self.singularity_min_slope
        new.show_advanced_settings = self.show_advanced_settings
        new.__singularity_equations = self.__singularity_equations.copy()
        new.__preferred_detection = self.__preferred_detection.copy()
        return new

    def get_singularity_equation_for(self, slope_function: str) -> str | None:
        """Returns the singularity equation for th given slope function, or None if it doesn't exist."""
        return self.__singularity_equations.get(slope_function)

    def set_new_singularity_equation(
        self,
        slope_func_str: str,
        equation_str: str,
        xlim: Tuple[float, float],
        ylim: Tuple[float, float],
        num_random_checks: int = 20,
    ) -> bool:
        """Checks if the equation is valid by trying to evaluate it at random points.
        If it seems valid, the function is set and True is returned. False is returned otherwise.

        Args:
            slope_func_str (str): String representation of the slope function which the equation is for.
            equation_str (str): String representation of the singularity equation.
            xlim (Tuple[float, float]): Limits of the x-axis.
            ylim (Tuple[float, float]): Limits of the y-axis.
            num_random_checks (int, optional): The number of random points the new equation will be evaluated at. Defaults to 20.

        Returns:
            success (bool): True if the equation seems valid; False otherwise.
            Returning True doesn't guarantee that the equation is valid, but False guarantees that it is not.
        """

        try:
            func = create_function_from_string(equation_str)
            # try to evaluate the equation at a few random points
            xs = np.random.uniform(xlim[0], xlim[1], num_random_checks)
            ys = np.random.uniform(ylim[0], ylim[1], num_random_checks)

            for i in range(num_random_checks):
                try:
                    func(xs[i], ys[i])
                except ValueError:  # it might not be defined everywhere
                    pass
        except:
            # the equation is not valid
            return False

        # the equation seems valid --> accept
        self.__singularity_equations[slope_func_str] = equation_str
        return True

    def get_preferred_detection_for(self, slope_func: str) -> Strategy:
        """Returns the preferred detection strategy for the given function."""
        return self.__preferred_detection.get(slope_func, self.Strategy.AUTOMATIC)

    def set_preferred_detection_for(self, slope_func: str, detection: Strategy) -> None:
        """Remembers the preferred detection strategy for the given function."""
        assert detection in [
            self.Strategy.AUTOMATIC,
            self.Strategy.MANUAL,
            self.Strategy.NONE,
        ]
        self.__preferred_detection[slope_func] = detection

    @property
    def trace_dx_granularity(self) -> float:
        """Converts trace precision to granularity, which is then used to calculate dx."""
        return MIN_TRACE_DX_GRANULARITY + (MAX_TRACE_DX_GRANULARITY - MIN_TRACE_DX_GRANULARITY) * (
            self.trace_precision - MIN_TRACE_PRECISION
        ) / (MAX_TRACE_PRECISION - MIN_TRACE_PRECISION)

    @property
    def trace_min_step_granularity(self) -> float:
        """Converts trace precision to granularity, which is then used to calculate min_step."""
        return MIN_TRACE_MIN_STEP_GRANULARITY + (
            MAX_TRACE_MIN_STEP_GRANULARITY - MIN_TRACE_MIN_STEP_GRANULARITY
        ) * (self.trace_precision - MIN_TRACE_PRECISION) / (
            MAX_TRACE_PRECISION - MIN_TRACE_PRECISION
        )

    @property
    def trace_max_step_granularity(self) -> float:
        """Converts trace precision to granularity, which is then used to calculate max_step."""
        return MIN_TRACE_MAX_STEP_GRANULARITY + (
            MAX_TRACE_MAX_STEP_GRANULARITY - MIN_TRACE_MAX_STEP_GRANULARITY
        ) * (self.trace_precision - MIN_TRACE_PRECISION) / (
            MAX_TRACE_PRECISION - MIN_TRACE_PRECISION
        )

    @property
    def singularity_alert_dist_granularity(self) -> float:
        """Converts trace precision to granularity, which is then used to calculate singularity_alert_dist."""
        return MIN_SINGULARITY_ALERT_DIST_GRANULARITY + (
            MAX_SINGULARITY_ALERT_DIST_GRANULARITY - MIN_SINGULARITY_ALERT_DIST_GRANULARITY
        ) * (self.trace_precision - MIN_TRACE_PRECISION) / (
            MAX_TRACE_PRECISION - MIN_TRACE_PRECISION
        )

    @property
    def line_width(self) -> float:
        """Converts line width entered by the user to a value that is then actually used."""
        # mapping min->1, max->7
        return 1 + 6 * (self.displayed_line_width - MIN_TRACE_LINES_WIDTH) / (
            MAX_TRACE_LINES_WIDTH - MIN_TRACE_LINES_WIDTH
        )


CurveInfo: TypeAlias = Tuple[TraceSettings, List[Tuple[np.floating, np.floating]]]
"""Settings of the curve + the curve itself given as a list of coordinates."""
