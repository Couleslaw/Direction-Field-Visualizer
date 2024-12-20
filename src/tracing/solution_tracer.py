from typing import Tuple, Iterator
import numpy as np

from src.math_functions import *
from src.default_constants import (
    TRACE_NUM_SEGMENTS_IN_DIAGONAL,
)


from src.math_functions import create_function_from_string
from src.tracing.numerical_methods import find_first_intersection
from src.tracing.trace_settings import TraceSettings

# helper functions for working with vectors


def resize_vector(vector, length):
    return vector / np.linalg.norm(vector) * length


def resize_vector_by_x(vector, x):
    return vector / fabs(vector[0]) * x


def vector_length(vector):
    return np.linalg.norm(vector)


def round_if_close_to_zero(x, epsilon=1e-9):
    if fabs(x) < epsilon:
        return 0
    return x


class SolutionTracer:
    """Class for tracing a solution curve with an initial point (x0, y0) and a given slope function."""

    # trace direction constants
    class Direction:
        Right = 1
        Left = -1
        Up = 1
        Down = -1

    # singularity handling return codes
    class Strategy:
        Stop = 1
        Infinite = 2
        Continue = 3

    def __init__(self, settings: TraceSettings, slope_function_string: str, xlim, ylim):
        self.settings = settings
        self.detection_strategy = settings.get_preferred_detection_for(slope_function_string)
        self.slope_func = create_function_from_string(slope_function_string)

        # determine the singularity detection strategy
        if self.detection_strategy == TraceSettings.Strategy.Manual:
            assert settings.has_singularity_for(slope_function_string)  # should be true
            self.singularity_eq = create_function_from_string(
                self.settings.singularity_equations[slope_function_string]
            )
        else:
            self.singularity_eq = None

        # calculate diagonal length and max line segment length
        self.xlim = xlim
        self.ylim = ylim
        self.diagonal_len = np.sqrt((xlim[1] - xlim[0]) ** 2 + (ylim[1] - ylim[0]) ** 2)
        self.max_line_segment_length = self.diagonal_len / TRACE_NUM_SEGMENTS_IN_DIAGONAL

    def is_monotonous_on(self, start, diff_vector, num_points) -> bool:
        """
        Checks if the slope function is monotonous on the line segment from start to start + diff_vector.
        Checks the slope at num_points equidistant points on the segment.
        """

        sgn = sign(self.slope_func(start[0], start[1]))
        diff = diff_vector / num_points

        # try because slope_func is unsafe
        try:
            for _ in range(num_points):
                start += diff
                if sign(self.slope_func(start[0], start[1])) != sgn:
                    return False
            return True
        except:
            return False

    def should_stop_if_y_out_of_bounds(self, y) -> bool:
        """This should be called when the y value is out of bounds. Returns True if the tracing should stop."""

        if self.detection_strategy in [
            TraceSettings.Strategy.None_,
            TraceSettings.Strategy.Manual,
        ]:
            return False

        # distance from edge of the screen
        dist = fabs(y - self.ylim[0]) if y < self.ylim[0] else fabs(y - self.ylim[1])

        # automatic detection --> cut off when further than screen_height * y_margin
        return dist > (self.ylim[1] - self.ylim[0]) * self.settings.y_margin

    def possible_singularity_at(self, x, y) -> bool:
        """Checks if there might a singularity close to the point (x, y)."""

        # if no detection --> return False
        if self.detection_strategy == TraceSettings.Strategy.None_:
            return False

        # if automatic detection is enabled, check if the slope is too steep
        if self.detection_strategy == TraceSettings.Strategy.Automatic:
            try:  # slope_func is unsafe
                return fabs(self.slope_func(x, y)) > self.settings.singularity_min_slope
            except:
                # probably division by zero --> close to singularity
                return True

        # manual detection --> singularity_eq should be set
        assert self.singularity_eq is not None

        try:
            singularity = find_first_intersection(self.singularity_eq, self.slope, x, y)
            diff = np.array([singularity[0] - x, singularity[1] - y])
        except:
            # newtons method probably failed --> no singularity close
            # but still set a valid sing_diff, it is used during the iteration
            # --> set sing_diff to a large vector in the correct direction
            self.sing_diff = resize_vector(self.vector, 10 * self.singularity_alert_distance)
            if fabs(self.sing_diff[0]) < self.max_dx:
                self.sing_diff = resize_vector_by_x(self.sing_diff, self.max_dx)
            return False

        diff = np.array([singularity[0] - x, singularity[1] - y])
        self.sing_diff = diff

        # if the singularity is close enough, return True
        if vector_length(diff) < self.singularity_alert_distance:
            return True

        # very high slope --> the diff will probably be x=0 and y>>x
        if (
            not (self.ylim[0] <= y <= self.ylim[1])
            and fabs(self.slope) > 1e9
            and fabs(diff[0]) < self.max_dx
        ):
            return True

        return False

    def handle_singularity(self, x, y):
        """
        This function is called when there is reason to believe that a singularity is close to the point (x, y).
        Return a strategy on how to proceed
        - CONTINUE = cautiously continue, your next step should be safe
        - STOP = stop tracing, a STOP singularity was detected
        - INFINITE = an infinite singularity was detected, the line should go off screen
        """

        # manual detection & if y is out of bounds --> STOP
        if self.detection_strategy == TraceSettings.Strategy.Manual and (
            y < self.ylim[0] or y > self.ylim[1]
        ):
            if fabs(self.slope_func(x, y)) > 1:
                return self.Strategy.Infinite
            return self.Strategy.Stop

        # calculate the first derivative at (x,y)
        # get vector in the direction of the slope: diff
        # determine a new point (nx, ny) = (x, y) + diff
        # hopefully its on the other side of the singularity
        # calculate the first and second derivative at (nx, ny)

        # this is in a try block because slope_func is unsafe
        try:
            der = self.slope_func(x, y)
            der = round_if_close_to_zero(der)

            # auto detection --> use sing_dx to determine size of diff
            if self.detection_strategy == TraceSettings.Strategy.Automatic:
                diff = np.array([self.sing_dx, self.sing_dx * der]) * self.direction

            # manual detection --> use distance to singularity to determine size of diff
            elif self.detection_strategy == TraceSettings.Strategy.Manual:
                # sing_diff = distance to singularity
                # jump to the other side
                if vector_length(self.sing_diff) > self.min_step:
                    diff = self.sing_diff
                else:
                    diff = resize_vector(np.array([1, der]), self.min_step)

                # correct the direction
                if sign(diff[0]) != sign(self.vector[0]):
                    diff *= -1
                # if the jump is too big, resize it
                if fabs(diff[0]) > self.sing_dx:
                    diff = resize_vector_by_x(diff, self.sing_dx)
                if vector_length(diff) > self.max_step:
                    diff = resize_vector(diff, self.max_step)
                diff = 2 * diff

            else:
                raise ValueError("Invalid detection strategy")  # should never happen

            # jump to the other side of the singularity (hopefully)
            nx, ny = x + diff[0], y + diff[1]

            # calculate first and second derivative at (nx, ny)
            sdx = 1e-15
            n_der = self.slope_func(nx, ny)
            n_der = round_if_close_to_zero(n_der)
            n_der2 = (self.slope_func(nx + sdx, ny + sdx * n_der) - n_der) / sdx
            n_der2 = round_if_close_to_zero(n_der2)

        except:
            # either division-by-zero, math-domain-error or the function is not valid
            # --> something is wrong, stop tracing
            return self.Strategy.Stop

        # helper function to determine if the tracing can continue
        def can_continue():
            if self.detection_strategy == TraceSettings.Strategy.Manual:
                return vector_length(self.sing_diff) > self.min_step

            # if the slope is very steep, there is almost certainly a singularity --> STOP
            if fabs(der) > 1e6:
                return False

            # this is automatic detection --> steep slope
            # if the function is not monotonic in the neighborhood of this suspected singularity
            # there is most probably a singularity --> STOP
            vector = resize_vector_by_x(diff, self.sing_dx)
            return self.is_monotonous_on(np.array([x, y]), 2 * vector, 10)

        # convex up - forward
        if der > 0 and self.direction == self.Direction.Right:
            if n_der2 > 0 and n_der < 0:  # convex down
                return self.Strategy.Infinite
            if n_der2 > 0 and n_der > 0:  # convex up
                return self.Strategy.Continue if can_continue() else self.Strategy.Stop
            if n_der2 < 0 and n_der > 0:  # concave up
                return self.Strategy.Continue if can_continue() else self.Strategy.Infinite
            if n_der2 < 0 and n_der < 0:  # concave down
                return self.Strategy.Stop

        # concave down - forward
        if der < 0 and self.direction == self.Direction.Right:
            if n_der2 > 0 and n_der < 0:  # convex down
                return self.Strategy.Continue if can_continue() else self.Strategy.Infinite
            if n_der2 > 0 and n_der > 0:  # convex up
                return self.Strategy.Stop
            if n_der2 < 0 and n_der > 0:  # concave up
                return self.Strategy.Infinite
            if n_der2 < 0 and n_der < 0:  # concave down
                return self.Strategy.Continue if can_continue() else self.Strategy.Stop

        # concave up - backward
        if der > 0 and self.direction == self.Direction.Left:
            if n_der2 > 0 and n_der < 0:  # convex down
                return self.Strategy.Stop
            if n_der2 > 0 and n_der > 0:  # convex up
                return self.Strategy.Continue if can_continue() else self.Strategy.Infinite
            if n_der2 < 0 and n_der > 0:  # concave up
                return self.Strategy.Continue if can_continue() else self.Strategy.Stop
            if n_der2 < 0 and n_der < 0:  # concave down
                return self.Strategy.Infinite

        # convex down - backward
        if der < 0 and self.direction == self.Direction.Left:
            if n_der2 > 0 and n_der < 0:  # convex down
                return self.Strategy.Continue if can_continue() else self.Strategy.Stop
            if n_der2 > 0 and n_der > 0:  # convex up
                return self.Strategy.Infinite
            if n_der2 < 0 and n_der > 0:  # concave up
                return self.Strategy.Stop
            if n_der2 < 0 and n_der < 0:  # concave down
                return self.Strategy.Continue if can_continue() else self.Strategy.Infinite

        return self.Strategy.Continue if can_continue() else self.Strategy.Infinite

    def should_yield_point(
        self, point, current_line_segment_length, line_segment_start
    ) -> bool:
        """Determines if a new point should be yielded based on the point position and the current line segment."""
        start_in_screen = self.ylim[0] < line_segment_start[1] < self.ylim[1]
        end_in_screen = self.ylim[0] < point[1] < self.ylim[1]

        if start_in_screen and end_in_screen:
            return current_line_segment_length > self.max_line_segment_length
        elif (start_in_screen and not end_in_screen) or (
            not start_in_screen and end_in_screen
        ):
            return True

        # start and end are out of screen
        dist = (
            fabs(point[1] - self.ylim[0])
            if point[1] < self.ylim[0]
            else fabs(point[1] - self.ylim[1])
        )
        length_needed = max(dist / 2, self.max_line_segment_length)
        return current_line_segment_length > length_needed

    def create_infinite_line(self, x0, y0, direction) -> Iterator[Tuple[float, float]]:
        """
        Goes off to infinity (and possibly stops) from (x0, y0) in the given direction.
        This can be either an INFINITE or a STOP singularity.
        """

        assert direction in [self.Direction.Up, self.Direction.Down]

        point = np.array([x0, y0])
        original_dist = vector_length(self.sing_diff)

        current_line_segment_length = 0
        line_segment_start = point.copy()

        def get_y_step(y):
            if self.ylim[0] <= y <= self.ylim[1]:
                step = self.max_step
            else:
                dist = fabs(y - self.ylim[0]) if y < self.ylim[0] else fabs(y - self.ylim[1])
                step = max(dist / 100, self.max_step)
            return step * direction

        while True:
            # if y out of bounds --> break
            if (direction == self.Direction.Up and point[1] > self.ylim[1]) or (
                direction == self.Direction.Down and point[1] < self.ylim[0]
            ):
                break

            diff_to_next_point = np.array([0, get_y_step(point[1])])

            # if manual --> calculate diff to singularity
            if self.detection_strategy == TraceSettings.Strategy.Manual:
                assert self.singularity_eq is not None
                try:
                    singularity = find_first_intersection(
                        self.singularity_eq,
                        self.slope_func(point[0], point[1]),
                        point[0],
                        point[1],
                    )
                except:
                    break

                diff = np.array([singularity[0] - point[0], singularity[1] - point[1]])

                # if on screen
                if self.ylim[0] <= point[1] <= self.ylim[1]:
                    # if the point is getting far from the singularity --> STOP
                    if vector_length(diff) > self.diagonal_len / 100:
                        break
                # if out of bounds
                else:
                    if vector_length(diff) > 10 * original_dist:
                        break

                # correct the x-position
                diff_to_next_point += diff / 2

            # calculate slope here and at the next point
            try:  # slope_func is unsafe
                der = self.slope_func(point[0], point[1])
                n_der = self.slope_func(
                    point[0] + diff_to_next_point[0], point[1] + diff_to_next_point[1]
                )
            except:
                break

            # if the slope changes sign --> STOP
            if sign(der) != sign(n_der):
                break

            point += diff_to_next_point

            # if by correcting position for MANUAL detection, the point got moved far from x0
            # something is wrong --> STOP
            if fabs(point[0] - x0) > (self.xlim[1] - self.xlim[0]) / 50:
                break

            current_line_segment_length += vector_length(diff_to_next_point)
            if self.should_yield_point(point, current_line_segment_length, line_segment_start):
                yield (x0, point[1])
                line_segment_start = point.copy()
                current_line_segment_length = 0

        yield (x0, point[1])

    def trace(self, x0, y0, direction) -> Iterator[Tuple[float, float]]:
        """
        Traces a solution curve starting at (x0, y0) in the given direction.
        yields points that are on the curve until it reaches a singularity or goes off screen.
        """
        yield (x0, y0)
        self.direction = direction

        point = np.array([x0, y0])  # current point
        last_point = point.copy()  # last point

        # manual detection
        self.min_step = (
            self.diagonal_len / 10 ** self.settings.get_trace_min_step_granularity()
        )
        self.max_step = (
            self.diagonal_len / 10 ** self.settings.get_trace_max_step_granularity()
        )
        self.singularity_alert_distance = (
            self.diagonal_len / 10 ** self.settings.get_singularity_alert_dist_granularity()
        )

        # max_dx is the maximum step size in x direction
        x_diff = self.xlim[1] - self.xlim[0]
        self.max_dx = (x_diff) / 10 ** self.settings.get_trace_dx_granularity()
        # sing_dx is the step size used when a singularity is detected in auto-detection mode
        self.sing_dx = min(1e-6, self.max_dx / 1000)

        # gives the number of times in a row the tracing continued after a singularity was detected
        # is used in auto-detection mode
        continue_count = 0
        current_line_segment_length = 0  # for adding new points
        line_segment_start = point.copy()

        while True:
            try:  # slope_func is unsafe
                self.slope = self.slope_func(point[0], point[1])
                self.vector = np.array([1, self.slope]) * direction
            except:
                break

            # if the slope is too big --> end
            if vector_length(self.vector) == np.inf:
                return

            # no singularity detected
            if not self.possible_singularity_at(point[0], point[1]):
                continue_count = 0  # reset continue count
                self.vector = resize_vector_by_x(self.vector, self.max_dx)

                # if not out of bounds and the step is too big, resize it
                # allow big steps out of bounds to save time
                if (
                    self.ylim[0] <= point[1] <= self.ylim[1]
                    and vector_length(self.vector) > self.max_step
                ):
                    self.vector = resize_vector(self.vector, self.max_step)

                if self.detection_strategy == TraceSettings.Strategy.Manual:
                    # if the step would overshoot a possible singularity, resize it
                    if vector_length(self.vector) >= (l := vector_length(self.sing_diff) / 3):
                        self.vector = resize_vector(self.vector, l)
            # singularity detected
            else:
                # get strategy on how to proceed
                strategy = self.handle_singularity(point[0], point[1])

                # if tracing should stop
                if strategy == self.Strategy.Stop:
                    break

                # if the function goes off to infinity
                if strategy == self.Strategy.Infinite:
                    # calculate last line segment
                    last_x, last_y = last_point[0], last_point[1]
                    last_slope = self.slope_func(last_x, last_y)
                    if sign(last_slope) != sign(self.slope):
                        self.slope = last_slope
                        point = last_point

                    if sign(self.slope) == 0:
                        yield (point[0], point[1])
                        return

                    line_direction = sign(self.slope) * direction

                    yield from self.create_infinite_line(point[0], point[1], line_direction)
                    return

                # if the tracing should continue
                if strategy == self.Strategy.Continue:
                    # manual detection
                    if self.detection_strategy == TraceSettings.Strategy.Manual:
                        step_size = np.clip(
                            vector_length(self.sing_diff) / 3, 0, self.max_step
                        )
                        self.vector = resize_vector(self.vector, step_size)
                        # if the step is too big, resize it
                        if fabs(self.vector[0]) > self.max_dx:
                            self.vector = resize_vector_by_x(self.vector, self.max_dx)

                    # automatic detection
                    else:
                        continue_count += 1
                        # resize vector to have normal dx
                        self.vector = resize_vector_by_x(self.vector, self.max_dx)

                        # if we continued a couple times in a row and the function seems to be monotonic ahead
                        # --> probably safe
                        if continue_count % 10 == 0 and self.is_monotonous_on(
                            point, 2 * self.vector, 20
                        ):
                            pass  # keep normal dx

                        else:
                            # resize vector to have the same dx as is used in singularity detection
                            # step of this size should be safe
                            self.vector = resize_vector_by_x(self.vector, self.sing_dx)

            # move to the next point
            last_point = point.copy()
            point += self.vector

            # if x is out of bounds --> break
            if point[0] < self.xlim[0] or point[0] > self.xlim[1]:
                break

            # if y is out of bounds --> maybe break
            if point[1] < self.ylim[0] or point[1] > self.ylim[1]:
                if self.should_stop_if_y_out_of_bounds(point[1]):
                    break

            # yield a new point if the segment has reached the desired length
            current_line_segment_length += vector_length(self.vector)

            if self.should_yield_point(point, current_line_segment_length, line_segment_start):
                yield (point[0], point[1])
                line_segment_start = point.copy()
                current_line_segment_length = 0

        # yield the last point
        yield (point[0], point[1])
