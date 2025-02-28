from PyQt6.QtCore import QThread, QObject, QTimer
from typing import Callable, List, Any

from src.threading.parallel_tracer import ParallelTracer
from src.threading.drawing_manager import DrawingManager, CurveInfo

from matplotlib.axes import Axes
from matplotlib.figure import Figure


class PeriodicTimer(QObject):
    """A timer that calls a function periodically without busy waiting."""

    def __init__(self, time_period: int, on_timeout: Callable[[], Any]) -> None:
        """Initializes a periodic timer.

        Args:
            time_period (int): The period between calls to `on_timeout`.
            on_timeout (Callable[[], Any]): The function to be called every `time_period`.
        """
        super().__init__()
        self.__time_period = time_period
        self.__on_timeout = on_timeout
        self.__running = True

    def run(self) -> None:
        """Starts the timer. The function will be called periodically until `stop` is called."""
        while self.__running and (thread := self.thread()) is not None:
            thread.msleep(self.__time_period)
            self.__on_timeout()

    def stop(self) -> None:
        """Stops the timer."""
        self.__running = False


class Job:
    """A class that manages a tracer in a separate thread"""

    def __init__(self, tracer: ParallelTracer) -> None:
        """Initializes a new tracing job.

        Args:
            tracer (ParallelTracer): The tracer to run.
        """
        self.__tracer = tracer
        self.__thread = QThread()

    def start(self, on_finished: Callable[[], Any]) -> None:
        """Runs the tracer in a separate thread."""

        # run the tracer
        self.__tracer.moveToThread(self.__thread)
        self.__thread.started.connect(self.__tracer.run)

        # on worker finished, quit the thread
        self.__tracer.finished.connect(self.__thread.quit)
        self.__tracer.finished.connect(self.__tracer.deleteLater)
        self.__thread.finished.connect(self.__thread.deleteLater)

        # on thread finished, call the on_finished function
        self.__thread.finished.connect(on_finished)

        # start the thread
        self.__thread.start()

    def add_curve_to_list(self, curves_list: List[CurveInfo]) -> None:
        """Adds the tracer's curve to the given list."""
        self.__tracer.add_curve_to_list(curves_list)

    def stop(self) -> None:
        """Stops the tracer. The thread will be stopped when the tracer finishes."""
        self.__tracer.stop()
        self.__thread.wait()


class TraceManager:
    """Manages tracing jobs and drawing curves."""

    __draw_interval: int = 50  # ms
    """Time in milliseconds between drawing curves."""

    __show_stop_button_delay: int = 1500  # ms
    """Time in milliseconds after which the stop button is shown if tracing takes too long."""

    def __init__(
        self,
        plot_axes: Axes,
        plot_figure: Figure,
        show_stop_button: Callable[[], Any],
        hide_stop_button: Callable[[], Any],
    ) -> None:
        """Initializes a new TraceManager.

        Args:
            plot_axes (Axes): Matplotlib Axes object of the canvas.
            plot_figure (Figure): Matplotlib Figure object of the canvas.
            show_stop_button (Callable[[], Any]): Should show the stop button when called.
            hide_stop_button (Callable[[], Any]): Should hide the stop button when called.
        """
        self.__show_stop_button = show_stop_button
        self.__hide_stop_button = hide_stop_button

        # remember running jobs
        self.__jobs: list[Job] = []

        # timer for periodic drawing
        self.__create_timer()

        # drawing manager
        self.__create_drawing_manager(plot_axes, plot_figure)

    def __create_timer(self) -> None:
        """Creates and starts a timer for periodic drawing."""
        self.__timer_thread = QThread()
        self.__timer = PeriodicTimer(self.__draw_interval, self.__draw_all_curves)
        self.__timer.moveToThread(self.__timer_thread)
        self.__timer_thread.started.connect(self.__timer.run)
        self.__timer_thread.finished.connect(self.__timer.deleteLater)
        self.__timer_thread.start()

    def __create_drawing_manager(self, plot_axes: Axes, plot_figure: Figure) -> None:
        """Creates and starts a drawing manager in a separate thread."""
        self.__drawing_manager_thread = QThread()
        self.__drawing_manager = DrawingManager(plot_axes, plot_figure)
        self.__drawing_manager.moveToThread(self.__drawing_manager_thread)
        self.__drawing_manager_thread.started.connect(self.__drawing_manager.run)
        self.__drawing_manager_thread.finished.connect(self.__drawing_manager.deleteLater)
        self.__drawing_manager_thread.start()

    def __draw_all_curves(self) -> None:
        """Takes curve segments from all running jobs and gives them to the drawing manager"""
        if not self.__jobs:
            return
        curves: List[CurveInfo] = []
        for job in self.__jobs:
            job.add_curve_to_list(curves)
        if curves:
            self.__drawing_manager.enqueue_curve_collection(curves)

    def start_new_tracer(self, tracer: ParallelTracer) -> None:
        """Starts a new tracer in a new thread."""
        job = Job(tracer)

        def on_finished() -> None:
            self.__jobs.remove(job)
            # hide the stop button if no jobs are running
            if not self.__jobs:
                self.__hide_stop_button()

        # start the job
        job.start(on_finished)
        self.__jobs.append(job)

        # show the stop button if tracing takes too long
        def after_delay() -> None:
            if job in self.__jobs:
                self.__show_stop_button()

        QTimer.singleShot(self.__show_stop_button_delay, after_delay)

    def stop_tracing(self) -> None:
        """Stops all running jobs and current drawing task"""
        for job in self.__jobs:
            job.stop()
        self.__drawing_manager.stop_current_task()

    def stop_all_threads(self) -> None:
        """Stops all running threads"""
        # stop the timer
        self.__timer.stop()
        self.__timer_thread.quit()
        self.__timer_thread.wait()
        # stop all jobs
        self.stop_tracing()
        # stop the drawing manager
        self.__drawing_manager.stop()
        self.__drawing_manager_thread.quit()
        self.__drawing_manager_thread.wait()
