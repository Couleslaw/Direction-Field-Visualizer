from matplotlib.collections import LineCollection
from PyQt6.QtCore import QObject, QMutex
from typing import List, Tuple
from src.tracing.trace_settings import TraceSettings


class DrawingManager(QObject):
    """Manages drawing curves in a separate thread."""

    def __init__(self, settings: TraceSettings, plot):
        super().__init__()
        self.settings = settings
        self.plot = plot
        self.curve_queue = []  # list of curves to draw
        # mutex for thread safety
        self.queue_mutex = QMutex()
        self.settings_mutex = QMutex()
        self.running = True

    def stop(self):
        self.running = False

    def add_curve_collection(self, curves: List[List[Tuple[float, float]]]):
        """Adds a collection of curves to the queue"""
        self.queue_mutex.lock()
        self.curve_queue.append(curves)
        self.queue_mutex.unlock()

    def stop_current_task(self):
        """Clears the queue"""
        self.queue_mutex.lock()
        self.curve_queue.clear()
        self.queue_mutex.unlock()

    def update_settings(self, settings: TraceSettings):
        """Updates trace settings"""
        self.settings_mutex.lock()
        self.settings = settings
        self.settings_mutex.unlock()

    def draw_curves(self, curves: List[List[Tuple[float, float]]]):
        """Draws the curves on the plot"""
        if not curves:
            return

        # get color and width
        self.settings_mutex.lock()
        color = self.settings.line_color
        width = self.settings.get_line_width()
        self.settings_mutex.unlock()

        # draw the curves
        lc = LineCollection(curves, color=color, linewidth=width)
        self.plot.axes.add_collection(lc)
        self.plot.figure.canvas.draw()

    def run(self):
        """Periodically draws the curves from the queue"""
        while self.running:
            # sleep for a while to avoid busy waiting
            self.thread().msleep(5)

            # get a bunch of curves from the queue and draw them
            curves = []
            count = 0
            while count < 10:
                self.queue_mutex.lock()
                if not self.curve_queue:
                    self.queue_mutex.unlock()
                    break
                curve = self.curve_queue.pop(0)
                self.queue_mutex.unlock()
                curves += curve
                count += 1
            self.draw_curves(curves)
