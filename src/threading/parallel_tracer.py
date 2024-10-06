from PyQt6.QtCore import pyqtSignal, QObject, QMutex
from typing import List, Tuple

from src.tracing.solution_tracer import SolutionTracer
from src.tracing.trace_settings import TraceSettings


class ParallelTracer(QObject):
    """This class does tracing calculations in a separate thread."""

    finished = pyqtSignal()

    def __init__(
        self,
        x,
        y,
        direction,
        slope_function_str,
        trace_settings: TraceSettings,
        plot,
    ):
        assert direction in [SolutionTracer.Direction.Left, SolutionTracer.Direction.Right]
        super().__init__()

        self.x = x
        self.y = y
        self.direction = direction
        self.slope_function_str = slope_function_str
        self.settings = trace_settings

        self.plot = plot
        self.xlim = plot.axes.get_xlim()
        self.ylim = plot.axes.get_ylim()

        # initial values
        self.running = False
        self.should_draw_curve = False
        self.empty_iterator = False

        # mutex for thread safety
        self.mutex = QMutex()

    def get_new_should_draw_curve(self, curve: List[Tuple[float, float]]) -> bool:
        """
        Decides whether or not the curve should be drawn.
        This function should be called every time after appending a new point to the curve.
        """

        # if it should --> keep it
        if self.should_draw_curve:
            return True

        # if the curve is empty, don't draw it
        if len(curve) < 2:
            return False

        # if finished iterating, draw the last bit of the curve
        if self.empty_iterator:
            return True

        start_in_screen = self.ylim[0] < curve[0][1] < self.ylim[1]
        end_in_screen = self.ylim[0] < curve[-1][1] < self.ylim[1]

        # if the whole curve is out of screen, don't draw it
        if not start_in_screen and not end_in_screen:
            return False
        return True

    def append_curve_to_list(self, curves_list: List[List[Tuple[float, float]]]):
        """Appends the current curve to the list of curves and resets the current curve."""

        # if should draw curve --> append and reset
        if self.should_draw_curve and self.running:
            self.mutex.lock()
            curves_list.append(self.curve.copy())
            self.curve = [self.curve[-1]]
            self.should_draw_curve = False
            self.mutex.unlock()

        # if finished iterating --> stop the thread
        if self.empty_iterator and self.running:
            self.running = False
            self.finished.emit()

    def run(self):
        """Runs the tracing calculations in a separate thread."""

        # create the iterator
        tracer = SolutionTracer(self.settings, self.slope_function_str, self.xlim, self.ylim)
        line_iterator = tracer.trace(self.x, self.y, self.direction)

        self.running = True

        self.curve = []
        while self.running and not self.empty_iterator:
            # append the next point to the curve
            self.mutex.lock()
            try:
                self.curve.append(next(line_iterator))
            except StopIteration:
                self.empty_iterator = True

            # update should_draw_curve
            self.should_draw_curve = self.get_new_should_draw_curve(self.curve)
            self.mutex.unlock()

    def stop(self):
        """Stops the thread."""
        self.running = False
        self.finished.emit()
