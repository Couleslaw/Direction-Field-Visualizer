from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from src.math_functions import create_function_from_string
from src.default_constants import TRACE_NUM_SEGMENTS_IN_DIAGONAL
from src.tracing.numerical_methods import find_first_intersection
from src.tracing.trace_settings import TraceSettings

from typing import Tuple, Iterator
from enum import Enum


class SolutionTracer:
    """Class for tracing a solution curve with an initial point and a given slope function."""

    class Direction(Enum):
        """Tracing direction constants."""

        RIGHT = 1
        LEFT = -1

    class VDirection(Enum):
        """Direction constants for vertical lines."""

        UP = 1
        DOWN = -1

    class Strategy(Enum):
        """Singularity handling return codes."""

        STOP = 1
        INFINITE = 2
        CONTINUE = 3

    @staticmethod
    def vector_length(vector: NDArray[np.floating]) -> float:
        return float(np.linalg.norm(vector))

    @staticmethod
    def resize_vector(vector: NDArray[np.floating], length: float) -> NDArray[np.floating]:
        return vector * length / SolutionTracer.vector_length(vector)

    @staticmethod
    def resize_vector_by_x(vector: NDArray[np.floating], new_x: float) -> NDArray[np.floating]:
        return vector * new_x / np.fabs(vector[0])

    @staticmethod
    def round_if_close_to_zero(x: np.floating, epsilon: float = 1e-9) -> np.floating:
        return np.float64(0) if (np.fabs(x) < epsilon) else x

    def __init__(
        self,
        settings: TraceSettings,
        slope_function_string: str,
        direction: SolutionTracer.Direction,
        xlim: Tuple[float, float],
        ylim: Tuple[float, float],
    ) -> None:
        """Initializes the SolutionTracer.

        Args:
            settings (TraceSettings): Settings for the tracing.
            slope_function_string (str): String representation of the slope function.
            direction (Direction): Direction of the tracing. Either Right or Left.
            xlim (Tuple[float, float]): Limits for the x-axis.
            ylim (Tuple[float, float]): Limits for the y-axis.
        """

        # store the arguments
        self.__settings = settings
        self.__direction = direction
        self.__xlim = xlim
        self.__ylim = ylim

        # load the preferred detection strategy for this slope function
        self.__detection_strategy = settings.get_preferred_detection_for(slope_function_string)
        self.__slope_func = create_function_from_string(slope_function_string)

        # load the singularity equation if manual detection is used
        if self.__detection_strategy == TraceSettings.Strategy.MANUAL:
            sing_eq_str = settings.get_singularity_equation_for(slope_function_string)
            assert sing_eq_str is not None
            self.__singularity_eq = create_function_from_string(sing_eq_str)
        else:
            self.__singularity_eq = None

        # calculate diagonal length and max line segment length
        self.__diagonal_len = np.sqrt((xlim[1] - xlim[0]) ** 2 + (ylim[1] - ylim[0]) ** 2)
        self.__max_line_segment_length = self.__diagonal_len / TRACE_NUM_SEGMENTS_IN_DIAGONAL

        # private fields for tracing
        """Tracing direction. Either Right or Left."""
        self.__slope: np.floating
        """Current slope of the solution curve."""
        self.__vector: NDArray[np.float64]
        """A vector in `self.__direction` with slope `self.__slope`."""

        # automatic singularity detection
        xdiff = self.__xlim[1] - self.__xlim[0]
        self.__max_dx: float = (xdiff) / 10**self.__settings.trace_dx_granularity
        """The maximum x-dim size of a step."""
        self.__sing_dx: float = min(1e-6, self.__max_dx / 1000)
        """The size of a step used when a singularity is detected in auto-detection mode."""

        # manual singularity detection
        self.__sing_diff: NDArray[np.float64]
        """The vector from the current point to the singularity. More precisely the place where the closes singularity is believed to be."""
        self.__singularity_alert_distance: float = (
            self.__diagonal_len / 10**self.__settings.singularity_alert_dist_granularity
        )
        """The distance between current point and the singularity at the singularity is considered close."""
        self.__min_step: float = (
            self.__diagonal_len / 10**self.__settings.trace_min_step_granularity
        )
        """The minimum step size allowed when close to a singularity."""
        self.__max_step: float = (
            self.__diagonal_len / 10**self.__settings.trace_max_step_granularity
        )
        """The maximum step size allowed when close to a singularity."""

    def __is_monotonous_on(
        self, start: NDArray[np.float64], diff_vector: NDArray[np.float64], num_points: int
    ) -> bool:
        """Checks if the slope function seems on the line segment from `start` to `start + diff_vector`
        by evaluating it at `num_points` equidistant points on the segment.

        Args:
            start (NDArray[np.float64]): Start of the segment.
            diff_vector (NDArray[np.float64]): Segment vector. `diff_vector = end - start`.
            num_points (int): Number of points to evaluate the slope function at.

        Returns:
            out (bool): True if the function seems monotonous on the segment, False otherwise.
        """

        assert len(start) == 2 == len(diff_vector)

        sgn = np.sign(self.__slope_func(start[0], start[1]))
        diff = diff_vector / num_points

        # try because slope_func is unsafe
        try:
            for _ in range(num_points):
                start += diff
                if np.sign(self.__slope_func(start[0], start[1])) != sgn:
                    return False
            return True
        except:
            return False

    def __should_stop_if_y_out_of_bounds(self, y: np.floating) -> bool:
        """Determines whether the tracing should stop if the y-coordinate is out of bounds.

        Args:
            y (floating): Current y-coordinate.

        Returns:
            decision (bool): True if the tracing should stop, False otherwise.
        """

        #  never stop for non-automatic detection
        if self.__detection_strategy != TraceSettings.Strategy.AUTOMATIC:
            return False

        # distance from edge of the screen
        dist = np.fabs(y - self.__ylim[0]) if y < self.__ylim[0] else np.fabs(y - self.__ylim[1])

        # automatic detection --> cut off when further than screen_height * y_margin
        return dist > (self.__ylim[1] - self.__ylim[0]) * self.__settings.y_margin

    def __possible_singularity_at(self, x: np.floating, y: np.floating) -> bool:
        """Checks if there might a singularity close to the point `(x, y)`.

        Args:
            x (floating): x coordinate of the point.
            y (floating): y coordinate of the point.

        Returns:
            result (bool): True if a singularity is close, False otherwise.
        """

        # if no detection --> return False
        if self.__detection_strategy == TraceSettings.Strategy.NONE:
            return False

        # if automatic detection is enabled, check if the slope is too steep
        if self.__detection_strategy == TraceSettings.Strategy.AUTOMATIC:
            try:  # slope_func is unsafe
                return np.fabs(self.__slope_func(x, y)) > self.__settings.singularity_min_slope
            except:
                # probably division by zero --> close to singularity
                return True

        # manual detection
        assert self.__detection_strategy == TraceSettings.Strategy.MANUAL
        assert self.__singularity_eq is not None

        try:
            singularity = find_first_intersection(self.__singularity_eq, self.__slope, x, y)
            self.__sing_diff = np.array([singularity[0] - x, singularity[1] - y])
        except:
            # newtons method probably failed --> no singularity close
            # but still set a valid sing_diff, it is used during the iteration
            # --> set sing_diff to a large vector in the correct direction
            self.__sing_diff = self.resize_vector(
                self.__vector, 10 * self.__singularity_alert_distance
            )
            if np.fabs(self.__sing_diff[0]) < self.__max_dx:
                self.__sing_diff = self.resize_vector_by_x(self.__sing_diff, self.__max_dx)
            return False

        # if the singularity is close enough, return True
        if self.vector_length(self.__sing_diff) < self.__singularity_alert_distance:
            return True

        # very high slope --> the diff will probably be x=0 and y>>x
        if (
            not (self.__ylim[0] <= y <= self.__ylim[1])
            and np.fabs(self.__slope) > 1e9
            and np.fabs(self.__sing_diff[0]) < self.__max_dx
        ):
            return True

        return False

    def __handle_singularity(self, x: np.floating, y: np.floating) -> Strategy:
        """This function should be called when there is reason to believe that a singularity is close to the point `(x, y)`.

        Args:
            x (floating): x coordinate of the current point.
            y (floating): y coordinate of the current point.

        Returns
        ------
        out (Strategy): A strategy on how to proceed:
            - CONTINUE = cautiously continue, your next step should be safe.
            - STOP = stop tracing, a STOP singularity was detected.
            - INFINITE = an infinite singularity was detected, the line should go off screen.
        """

        # check if the detection strategy is valid (only automatic or manual)
        assert self.__detection_strategy in [
            TraceSettings.Strategy.AUTOMATIC,
            TraceSettings.Strategy.MANUAL,
        ]

        # manual detection & if y is out of bounds --> STOP
        if self.__detection_strategy == TraceSettings.Strategy.MANUAL and (
            y < self.__ylim[0] or y > self.__ylim[1]
        ):
            if np.fabs(self.__slope_func(x, y)) > 1:
                return self.Strategy.INFINITE
            return self.Strategy.STOP

        # calculate the first derivative at (x,y)
        # get vector in the direction of the slope: diff
        # determine a new point (nx, ny) = (x, y) + diff
        # hopefully its on the other side of the singularity
        # calculate the first and second derivative at (nx, ny)

        # this is in a try block because slope_func is unsafe
        try:
            der = self.__slope_func(x, y)
            der = self.round_if_close_to_zero(der)

            # auto detection --> use sing_dx to determine size of diff
            if self.__detection_strategy == TraceSettings.Strategy.AUTOMATIC:
                diff = (
                    np.array([self.__sing_dx, self.__sing_dx * der], dtype=np.float64)
                    * self.__direction.value
                )

            # manual detection --> use distance to singularity to determine size of diff
            elif self.__detection_strategy == TraceSettings.Strategy.MANUAL:
                # sing_diff = distance to singularity
                # jump to the other side
                if self.vector_length(self.__sing_diff) > self.__min_step:
                    diff = self.__sing_diff
                else:
                    diff = self.resize_vector(np.array([1, der]), self.__min_step)

                # correct the direction
                if np.sign(diff[0]) != np.sign(self.__vector[0]):
                    diff *= -1
                # if the jump is too big, resize it
                if np.fabs(diff[0]) > self.__sing_dx:
                    diff = self.resize_vector_by_x(diff, self.__sing_dx)
                if self.vector_length(diff) > self.__max_step:
                    diff = self.resize_vector(diff, self.__max_step)
                diff = 2 * diff

            else:
                assert False

            # jump to the other side of the singularity (hopefully)
            nx, ny = x + diff[0], y + diff[1]

            # calculate first and second derivative at (nx, ny)
            sdx = 1e-15
            n_der = self.__slope_func(nx, ny)
            n_der = self.round_if_close_to_zero(n_der)
            n_der2 = (self.__slope_func(nx + sdx, ny + sdx * n_der) - n_der) / sdx
            n_der2 = self.round_if_close_to_zero(n_der2)

        except:
            # either division-by-zero, math-domain-error or the function is not valid
            # --> something is wrong, stop tracing
            return self.Strategy.STOP

        # helper function to determine if the tracing can continue
        def can_continue() -> bool:
            if self.__detection_strategy == TraceSettings.Strategy.MANUAL:
                return self.vector_length(self.__sing_diff) > self.__min_step

            # if the slope is very steep, there is almost certainly a singularity --> STOP
            if np.fabs(der) > 1e6:
                return False

            # this is automatic detection --> steep slope
            # if the function is not monotonic in the neighborhood of this suspected singularity
            # there is most probably a singularity --> STOP
            vector = self.resize_vector_by_x(diff, self.__sing_dx)
            return self.__is_monotonous_on(np.array([x, y]), 2 * vector, 10)

        # convex up - forward
        if der > 0 and self.__direction == self.Direction.RIGHT:
            if n_der2 > 0 and n_der < 0:  # convex down
                return self.Strategy.INFINITE
            if n_der2 > 0 and n_der > 0:  # convex up
                return self.Strategy.CONTINUE if can_continue() else self.Strategy.STOP
            if n_der2 < 0 and n_der > 0:  # concave up
                return self.Strategy.CONTINUE if can_continue() else self.Strategy.INFINITE
            if n_der2 < 0 and n_der < 0:  # concave down
                return self.Strategy.STOP

        # concave down - forward
        if der < 0 and self.__direction == self.Direction.RIGHT:
            if n_der2 > 0 and n_der < 0:  # convex down
                return self.Strategy.CONTINUE if can_continue() else self.Strategy.INFINITE
            if n_der2 > 0 and n_der > 0:  # convex up
                return self.Strategy.STOP
            if n_der2 < 0 and n_der > 0:  # concave up
                return self.Strategy.INFINITE
            if n_der2 < 0 and n_der < 0:  # concave down
                return self.Strategy.CONTINUE if can_continue() else self.Strategy.STOP

        # concave up - backward
        if der > 0 and self.__direction == self.Direction.LEFT:
            if n_der2 > 0 and n_der < 0:  # convex down
                return self.Strategy.STOP
            if n_der2 > 0 and n_der > 0:  # convex up
                return self.Strategy.CONTINUE if can_continue() else self.Strategy.INFINITE
            if n_der2 < 0 and n_der > 0:  # concave up
                return self.Strategy.CONTINUE if can_continue() else self.Strategy.STOP
            if n_der2 < 0 and n_der < 0:  # concave down
                return self.Strategy.INFINITE

        # convex down - backward
        if der < 0 and self.__direction == self.Direction.LEFT:
            if n_der2 > 0 and n_der < 0:  # convex down
                return self.Strategy.CONTINUE if can_continue() else self.Strategy.STOP
            if n_der2 > 0 and n_der > 0:  # convex up
                return self.Strategy.INFINITE
            if n_der2 < 0 and n_der > 0:  # concave up
                return self.Strategy.STOP
            if n_der2 < 0 and n_der < 0:  # concave down
                return self.Strategy.CONTINUE if can_continue() else self.Strategy.INFINITE

        return self.Strategy.CONTINUE if can_continue() else self.Strategy.INFINITE

    def __should_yield_point(
        self,
        point: NDArray[np.float64],
        current_curve_segment_length: float,
        curve_segment_start: NDArray[np.float64],
    ) -> bool:
        """Determines if a new point should be yielded based on the point position and the current line segment.

        Args:
            point (NDArray[np.float64]): Current point.
            current_curve_segment_length (float): Length of the current curve segment. From `line_segment_start` to `point`.
            line_segment_start (NDArray[np.float64]): The starting point of the current curve segment.

        Returns:
            result (bool): True if a new point should be yielded, False otherwise.
        """

        # check the dimensions
        assert len(point) == 2 == len(curve_segment_start)

        # are start and end of the curve segment visible?
        start_in_screen = self.__ylim[0] < curve_segment_start[1] < self.__ylim[1]
        end_in_screen = self.__ylim[0] < point[1] < self.__ylim[1]

        # if both are in screen --> yield if the segment long enough
        if start_in_screen and end_in_screen:
            return current_curve_segment_length > self.__max_line_segment_length

        # if one is in screen and the other is not --> yield
        elif (start_in_screen and not end_in_screen) or (not start_in_screen and end_in_screen):
            return True

        # if start and end are both out of screen

        # the distance of point.y from the y-edge of the screen
        dist = (
            np.fabs(point[1] - self.__ylim[0])
            if point[1] < self.__ylim[0]
            else np.fabs(point[1] - self.__ylim[1])
        )

        # yield if the segment is long enough
        length_needed = max(dist / 2, self.__max_line_segment_length)
        return current_curve_segment_length > length_needed

    def __create_vertical_line(
        self, x0: np.floating, y0: np.floating, direction: VDirection
    ) -> Iterator[Tuple[np.floating, np.floating]]:
        """Creates a vertical line starting at `(x0, y0)` in the given direction.
        The line can either go off screen or stop (if a singularity is detected).
        This function should be called when an INFINITE singularity is detected.

        Args:
            x0 (floating): x-coordinate of the starting point.
            y0 (floating): y-coordinate of the starting point.
            direction (VDirection): Direction of the line. Either UP or DOWN.

        Yields:
            line (Iterator[Tuple[floating, floating]]): Iterator of points on the line.
        """

        # save the original distance to singularity
        original_dist = self.vector_length(self.__sing_diff)

        # starting point
        point = np.array([x0, y0], dtype=np.float64)
        current_line_segment_length: float = 0
        line_segment_start = point.copy()

        def get_y_step(y: float) -> float:
            """Calculates the step size for the next point based on the current y-coordinate."""
            # if y is on screen --> use max_step
            if self.__ylim[0] <= y <= self.__ylim[1]:
                step = self.__max_step
            # if y out of screen --> jump 1/100 of the distance to the edge
            else:
                dist = (
                    np.fabs(y - self.__ylim[0])
                    if y < self.__ylim[0]
                    else np.fabs(y - self.__ylim[1])
                )
                step = max(dist / 100, self.__max_step)
            return step * direction.value

        while True:
            # if y out of bounds in the desired direction --> break
            if (direction == self.VDirection.UP and point[1] > self.__ylim[1]) or (
                direction == self.VDirection.DOWN and point[1] < self.__ylim[0]
            ):
                break

            diff_to_next_point = np.array([0, get_y_step(point[1])])

            # if manual --> calculate diff to singularity
            if self.__detection_strategy == TraceSettings.Strategy.MANUAL:
                assert self.__singularity_eq is not None
                try:
                    singularity = find_first_intersection(
                        self.__singularity_eq,
                        self.__slope_func(point[0], point[1]),
                        point[0],
                        point[1],
                    )
                except:
                    break

                diff = np.array([singularity[0] - point[0], singularity[1] - point[1]])

                # if on screen
                if self.__ylim[0] <= point[1] <= self.__ylim[1]:
                    # if the point is getting far from the singularity --> STOP
                    if self.vector_length(diff) > self.__diagonal_len / 100:
                        break
                # if out of bounds
                else:
                    if self.vector_length(diff) > 10 * original_dist:
                        break

                # correct the x-position
                diff_to_next_point += diff / 2

            # calculate slope here and at the next point
            try:  # slope_func is unsafe
                der = self.__slope_func(point[0], point[1])
                n_der = self.__slope_func(
                    point[0] + diff_to_next_point[0], point[1] + diff_to_next_point[1]
                )
            except:
                break

            # if the slope changes sign --> STOP
            if np.sign(der) != np.sign(n_der):
                break

            point += diff_to_next_point

            # if by correcting position for MANUAL detection, the point got moved far from x0
            # something is wrong --> STOP
            if np.fabs(point[0] - x0) > (self.__xlim[1] - self.__xlim[0]) / 50:
                break

            current_line_segment_length += self.vector_length(diff_to_next_point)
            if self.__should_yield_point(point, current_line_segment_length, line_segment_start):
                yield (x0, point[1])
                line_segment_start = point.copy()
                current_line_segment_length = 0

        yield (x0, point[1])

    def __set_step_when_no_singularity_detected(self, point: NDArray[np.float64]) -> None:
        """Should be called when no singularity was detected near the given point.
        Sets the step size by scaling `self.__vector`.

        Args:
            point (NDArray[np.float64]): Current point.
        """

        self.__vector = self.resize_vector_by_x(self.__vector, self.__max_dx)

        # if not out of bounds and the step is too big, resize it
        # allow big steps out of bounds to save time
        if (
            self.__ylim[0] <= point[1] <= self.__ylim[1]
            and self.vector_length(self.__vector) > self.__max_step
        ):
            self.__vector = self.resize_vector(self.__vector, self.__max_step)

        if self.__detection_strategy == TraceSettings.Strategy.MANUAL:
            # if the step would overshoot a possible singularity, resize it
            if self.vector_length(self.__vector) >= (l := self.vector_length(self.__sing_diff) / 3):
                self.__vector = self.resize_vector(self.__vector, l)

    def __set_step_when_a_singularity_detected(
        self, point: NDArray[np.float64], continue_count: int
    ) -> None:
        """Should be called when a singularity of type CONTINUE was detected near the given point.
        Sets the step size by scaling `self.__vector`.

        Args:
            point (NDArray[np.float64]): Current point.
            continue_count (int): The number of times in a row the tracing continued OK after the singularity was detected.
        """

        # manual detection
        if self.__detection_strategy == TraceSettings.Strategy.MANUAL:
            step_size = np.clip(self.vector_length(self.__sing_diff) / 3, 0, self.__max_step)
            self.__vector = self.resize_vector(self.__vector, step_size)
            # if the step is too big, resize it
            if np.fabs(self.__vector[0]) > self.__max_dx:
                self.__vector = self.resize_vector_by_x(self.__vector, self.__max_dx)

        # automatic detection
        elif self.__detection_strategy == TraceSettings.Strategy.AUTOMATIC:
            # resize vector to have normal dx
            self.__vector = self.resize_vector_by_x(self.__vector, self.__max_dx)

            # if we continued a couple times in a row and the function seems to be monotonic ahead --> probably safe
            if continue_count % 10 == 0 and self.__is_monotonous_on(point, 2 * self.__vector, 20):
                return

            # resize vector to have the same dx as is used in singularity detection --> step of this size should be safe
            self.__vector = self.resize_vector_by_x(self.__vector, self.__sing_dx)

    def trace(self, x0: np.floating, y0: np.floating) -> Iterator[Tuple[np.floating, np.floating]]:
        """Traces a solution curve starting at `(x0, y0)` in the given direction until it reaches a singularity or goes off screen.

        Args:
            x0 (floating): x-coordinate of the starting point.
            y0 (floating): y-coordinate of the starting point.

        Yields:
            curve (Iterator[Tuple[floating, floating]]): Iterator points that are on the curve.
        """

        # current and last points
        point = np.array([x0, y0], dtype=np.float64)
        last_point = point.copy()

        # yield the starting point
        yield (x0, y0)

        # the number of times in a row the tracing continued OK after a singularity was detected
        # it is used in automatic detection - if it continues OK for a while, it is probably safe
        continue_count: int = 0

        # length of the current curve segment
        current_curve_segment_length: float = 0
        curve_segment_start = point.copy()

        while True:
            try:
                # calculate the slope at the current point
                self.__slope = self.__slope_func(point[0], point[1])
                self.__vector = (
                    np.array([1, self.__slope], dtype=np.float64) * self.__direction.value
                )
            except:
                # slope_func is unsafe
                break

            # if the slope is too big --> end
            if self.vector_length(self.__vector) == np.inf:
                return

            # no singularity detected
            if not self.__possible_singularity_at(point[0], point[1]):
                continue_count = 0  # reset continue count
                self.__set_step_when_no_singularity_detected(point)

            # singularity detected
            else:
                # get strategy on how to proceed
                strategy = self.__handle_singularity(point[0], point[1])

                # if tracing should stop
                if strategy == self.Strategy.STOP:
                    break

                # if the function goes off to infinity
                if strategy == self.Strategy.INFINITE:
                    # calculate last line segment
                    last_x, last_y = last_point[0], last_point[1]
                    last_slope = self.__slope_func(last_x, last_y)
                    if np.sign(last_slope) != np.sign(self.__slope):
                        self.__slope = last_slope
                        point = last_point

                    if np.sign(self.__slope) == 0:
                        yield (point[0], point[1])
                        return

                    line_direction = SolutionTracer.VDirection(
                        np.sign(self.__slope) * self.__direction.value
                    )

                    yield from self.__create_vertical_line(point[0], point[1], line_direction)
                    return

                # if the tracing should continue
                if strategy == self.Strategy.CONTINUE:
                    # increment the continue count if automatic detection is used
                    if self.__detection_strategy == TraceSettings.Strategy.AUTOMATIC:
                        continue_count += 1
                    self.__set_step_when_a_singularity_detected(point, continue_count)

            # move to the next point
            last_point = point.copy()
            point += self.__vector

            # if x is out of bounds --> break
            if point[0] < self.__xlim[0] or point[0] > self.__xlim[1]:
                break

            # if y is out of bounds --> maybe break
            if point[1] < self.__ylim[0] or point[1] > self.__ylim[1]:
                if self.__should_stop_if_y_out_of_bounds(point[1]):
                    break

            # yield a new point if the segment has reached the desired length
            current_curve_segment_length += self.vector_length(self.__vector)

            if self.__should_yield_point(point, current_curve_segment_length, curve_segment_start):
                yield (point[0], point[1])
                curve_segment_start = point.copy()
                current_curve_segment_length = 0

        # yield the last point
        yield (point[0], point[1])
