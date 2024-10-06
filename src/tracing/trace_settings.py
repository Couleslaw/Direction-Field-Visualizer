import numpy as np
from src.math_functions import create_function_from_string

from src.default_constants import (
    DEFAULT_TRACE_COLOR,
    DEFAULT_TRACE_LINES_WIDTH,
    MIN_TRACE_LINES_WIDTH,
    MAX_TRACE_LINES_WIDTH,
    DEFAULT_TRACE_Y_MARGIN,
    DEFAULT_TRACE_PRECISION,
    DEFAULT_SINGULARITY_MIN_SLOPE,
    MIN_TRACE_DX_GRANULARITY,
    MAX_TRACE_DX_GRANULARITY,
    MIN_TRACE_MIN_STEP_GRANULARITY,
    MAX_TRACE_MIN_STEP_GRANULARITY,
    MIN_TRACE_MAX_STEP_GRANULARITY,
    MAX_TRACE_MAX_STEP_GRANULARITY,
    MIN_SINGULARITY_ALERT_DIST_GRANULARITY,
    MAX_SINGULARITY_ALERT_DIST_GRANULARITY,
    MAX_TRACE_PRECISION,
    MIN_TRACE_PRECISION,
)


class TraceSettings:
    """Class for storing settings for tracing a solutions of given differential equation."""

    class Strategy:
        Automatic = 0
        Manual = 1
        None_ = 2

    def __init__(self):
        self.line_color = DEFAULT_TRACE_COLOR
        self.line_width = DEFAULT_TRACE_LINES_WIDTH
        self.y_margin = DEFAULT_TRACE_Y_MARGIN
        self.trace_precision = DEFAULT_TRACE_PRECISION
        self.singularity_min_slope = DEFAULT_SINGULARITY_MIN_SLOPE
        self.show_advanced_settings = False
        # slope function string -> singularity equation string
        self.singularity_equations = {"x/y": "y"}
        self.preferred_detection = dict()  # slope function string -> detection strategy

    def copy(self):
        """Returns a copy if itself"""
        new = TraceSettings()
        new.line_color = self.line_color
        new.line_width = self.line_width
        new.y_margin = self.y_margin
        new.trace_precision = self.trace_precision
        new.singularity_min_slope = self.singularity_min_slope
        new.show_advanced_settings = self.show_advanced_settings
        new.singularity_equations = self.singularity_equations.copy()
        new.preferred_detection = self.preferred_detection.copy()
        return new

    def has_singularity_for(self, equation: str):
        """Returns True if there is a singularity equation for the given equation."""
        return equation in self.singularity_equations

    def set_preferred_detection_for(self, slope_func: str, detection: int):
        assert detection in [
            self.Strategy.Automatic,
            self.Strategy.Manual,
            self.Strategy.None_,
        ]
        self.preferred_detection[slope_func] = detection

    def get_preferred_detection_for(self, slope_func: str):
        return self.preferred_detection.get(slope_func, self.Strategy.Automatic)

    def get_trace_dx_granularity(self):
        """Converts trace precision to granularity, which is then used to calculate dx."""
        return MIN_TRACE_DX_GRANULARITY + (
            MAX_TRACE_DX_GRANULARITY - MIN_TRACE_DX_GRANULARITY
        ) * (self.trace_precision - MIN_TRACE_PRECISION) / (
            MAX_TRACE_PRECISION - MIN_TRACE_PRECISION
        )

    def get_trace_min_step_granularity(self):
        """Converts trace precision to granularity, which is then used to calculate min_step."""
        return MIN_TRACE_MIN_STEP_GRANULARITY + (
            MAX_TRACE_MIN_STEP_GRANULARITY - MIN_TRACE_MIN_STEP_GRANULARITY
        ) * (self.trace_precision - MIN_TRACE_PRECISION) / (
            MAX_TRACE_PRECISION - MIN_TRACE_PRECISION
        )

    def get_trace_max_step_granularity(self):
        """Converts trace precision to granularity, which is then used to calculate max_step."""
        return MIN_TRACE_MAX_STEP_GRANULARITY + (
            MAX_TRACE_MAX_STEP_GRANULARITY - MIN_TRACE_MAX_STEP_GRANULARITY
        ) * (self.trace_precision - MIN_TRACE_PRECISION) / (
            MAX_TRACE_PRECISION - MIN_TRACE_PRECISION
        )

    def get_singularity_alert_dist_granularity(self):
        """Converts trace precision to granularity, which is then used to calculate singularity_alert_dist."""
        return MIN_SINGULARITY_ALERT_DIST_GRANULARITY + (
            MAX_SINGULARITY_ALERT_DIST_GRANULARITY - MIN_SINGULARITY_ALERT_DIST_GRANULARITY
        ) * (self.trace_precision - MIN_TRACE_PRECISION) / (
            MAX_TRACE_PRECISION - MIN_TRACE_PRECISION
        )

    def get_line_width(self):
        """Converts line width entered by the user to a value that is then actually used."""
        # mapping min->1, max->7
        return 1 + 6 * (self.line_width - MIN_TRACE_LINES_WIDTH) / (
            MAX_TRACE_LINES_WIDTH - MIN_TRACE_LINES_WIDTH
        )

    def set_new_singularity_equation(self, slope_func, equation_str, xlim, ylim) -> bool:
        """Checks if the equation is valid and sets it if it is. Returns True if the equation is valid."""

        try:
            func = create_function_from_string(equation_str)
            # try to evaluate the equation at a few random points
            for _ in range(20):
                try:
                    x = np.random.uniform(xlim[0], xlim[1])
                    y = np.random.uniform(ylim[0], ylim[1])
                    func(x, y)
                except ZeroDivisionError:  # can be a singularity
                    pass
                except ValueError:  # it might not be defined everywhere
                    pass
        except:
            # the equation is not valid
            return False

        # the equation seems valid --> accept
        self.singularity_equations[slope_func] = equation_str
        return True
