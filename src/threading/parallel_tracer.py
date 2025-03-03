from PyQt6.QtCore import pyqtSignal, QObject, QMutex
from typing import List, Tuple

from src.tracing.solution_tracer import SolutionTracer
from src.tracing.trace_settings import TraceSettings, CurveInfo


class ParallelTracer(QObject):
    """This class does tracing calculations in a separate thread."""

    finished = pyqtSignal()

    def __init__(
        self,
        x: float,
        y: float,
        xlim: Tuple[float, float],
        ylim: Tuple[float, float],
        direction: SolutionTracer.Direction,
        slope_function_str: str,
        trace_settings: TraceSettings,
    ) -> None:
        """Initializes the ParallelTracer.

        Args:
            x (float): x coordinate of the starting point.
            y (float): y coordinate of the starting point.
            xlim (Tuple[float, float]): Limits of the x axis.
            ylim (Tuple[float, float]): Limits of the y axis.
            direction (Direction): Direction of the tracing. Either `SolutionTracer.Direction.Left` or `SolutionTracer.Direction.Right`.
            slope_function_str (str): String representation of the slope function.
            trace_settings (TraceSettings): Settings for the tracing.
        """

        # check if the direction is valid
        assert direction in [SolutionTracer.Direction.LEFT, SolutionTracer.Direction.RIGHT]
        super().__init__()

        # store the arguments
        self.__x = x
        self.__y = y
        self.__xlim = xlim
        self.__ylim = ylim

        self.__direction = direction
        self.__slope_function_str = slope_function_str
        self.__settings = trace_settings

        # initial values
        self.__running: bool = False
        self.__should_draw_curve: bool = False
        self.__empty_iterator: bool = False

        # the curve that is being traced
        self.__curve: List[Tuple[float, float]] = []

        # mutex for thread safety
        self.__mutex = QMutex()

    def __get_new_should_draw_curve(self) -> bool:
        """
        Decides whether or not the curve should be drawn.
        This function should be called every time after appending a new point to the curve.
        """

        # if it should --> keep it
        if self.__should_draw_curve:
            return True

        # if the curve is empty, don't draw it
        if len(self.__curve) < 2:
            return False

        # if finished iterating, draw the last bit of the curve
        if self.__empty_iterator:
            return True

        start_in_screen = self.__ylim[0] < self.__curve[0][1] < self.__ylim[1]
        end_in_screen = self.__ylim[0] < self.__curve[-1][1] < self.__ylim[1]

        # if the whole curve is out of screen, don't draw it
        if not start_in_screen and not end_in_screen:
            return False
        return True

    def add_curve_to_list(self, curves_list: List[CurveInfo]) -> None:
        """Appends the current curve to the list of curves and resets the current curve."""

        # if should draw curve --> append and reset
        if self.__should_draw_curve and self.__running:
            self.__mutex.lock()
            curves_list.append((self.__settings, self.__curve.copy()))
            self.__curve = [self.__curve[-1]]
            self.__should_draw_curve = False
            self.__mutex.unlock()

        # if finished iterating --> stop the thread
        if self.__empty_iterator and self.__running:
            self.__running = False
            self.finished.emit()

    def run(self) -> None:
        """Runs the tracing calculations in a separate thread."""

        # create a new solution tracer
        tracer = SolutionTracer(
            self.__settings, self.__slope_function_str, self.__xlim, self.__ylim
        )
        # get the line segment iterator
        line_iterator = tracer.trace(self.__x, self.__y, self.__direction)

        # change state to running
        self.__running = True

        # iterate over the line segment iterator to get the curve
        while self.__running and not self.__empty_iterator:
            # append the next point to the curve
            self.__mutex.lock()
            try:
                self.__curve.append(next(line_iterator))
            except StopIteration:
                self.__empty_iterator = True

            # update should_draw_curve
            self.__should_draw_curve = self.__get_new_should_draw_curve()
            self.__mutex.unlock()

    def stop(self) -> None:
        """Stops the thread."""

        if self.__running == False:
            return
        self.__running = False
        self.finished.emit()
