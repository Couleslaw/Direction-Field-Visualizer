from matplotlib.collections import LineCollection
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from PyQt6.QtCore import QObject, QMutex
from typing import List
from src.tracing.trace_settings import CurveInfo


class DrawingManager(QObject):
    """Manages drawing curves in a separate thread."""

    def __init__(self, plot_axes: Axes, plot_figure: Figure) -> None:
        super().__init__()
        self.__plot_axes = plot_axes
        self.__plot_figure = plot_figure

        # curves collections to draw
        self.__curve_queue: List[List[CurveInfo]] = []

        # mutex for thread safety
        self.__queue_mutex = QMutex()
        self.__running = True

    def stop(self):
        self.__running = False

    def enqueue_curve_collection(self, curves: List[CurveInfo]):
        """Adds a collection of curves to the drawing queue."""
        self.__queue_mutex.lock()
        self.__curve_queue.append(curves)
        self.__queue_mutex.unlock()

    def stop_current_task(self):
        """Clears the drawing queue."""
        self.__queue_mutex.lock()
        self.__curve_queue.clear()
        self.__queue_mutex.unlock()

    def __draw_curves(self, curves: List[CurveInfo]):
        """Draws the curves on the plot."""
        if not curves:
            return

        for settings, curve in curves:
            # get color and width
            color = settings.line_color
            width = settings.line_width

            # draw the curve
            lc = LineCollection([curve], color=color, linewidth=width)
            self.__plot_axes.add_collection(lc)
        self.__plot_figure.canvas.draw()

    def run(self):
        """Periodically draws the curves from the drawing queue."""
        while self.__running:
            # sleep for a while to avoid busy waiting
            thread = self.thread()
            if thread is not None:
                thread.msleep(5)

            # get a bunch of curves from the queue and draw them
            curves_to_draw: List[CurveInfo] = []
            count = 0
            batch_size = 10  # number of curves to draw at once

            while count < batch_size:
                self.__queue_mutex.lock()
                if not self.__curve_queue:
                    self.__queue_mutex.unlock()
                    break
                curve_infos = self.__curve_queue.pop(0)
                self.__queue_mutex.unlock()
                curves_to_draw += curve_infos
                count += 1

            # draw the curves
            self.__draw_curves(curves_to_draw)
