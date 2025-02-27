from PyQt6.QtCore import QThread, QObject, QTimer
from typing import Callable, List, Tuple

from src.threading.parallel_tracer import ParallelTracer
from src.threading.drawing_manager import DrawingManager
from src.tracing.trace_settings import TraceSettings

from matplotlib.axes import Axes
from matplotlib.figure import Figure


class PeriodicTimer(QObject):
    """A timer that calls a function periodically"""

    def __init__(self, time_period, on_timeout):
        super().__init__()
        self.time_period = time_period
        self.on_timeout = on_timeout
        self.running = True

    def run(self):
        while self.running and (thread := self.thread()) is not None:
            thread.msleep(self.time_period)
            self.on_timeout()

    def stop(self):
        self.running = False


class Job:
    """A class that manages a tracer in a separate thread"""

    def __init__(self, tracer: ParallelTracer):
        self.tracer = tracer
        self.thread = QThread()

    def start(self, on_finished: Callable):
        # run the tracer
        self.tracer.moveToThread(self.thread)
        self.thread.started.connect(self.tracer.run)

        # on worker finished, quit the thread
        self.tracer.finished.connect(self.thread.quit)
        self.tracer.finished.connect(self.tracer.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # on thread finished, call the on_finished function
        self.thread.finished.connect(on_finished)

        # start the thread
        self.thread.start()

    def append_curve_to_list(
        self, curves_list: List[Tuple[TraceSettings, List[Tuple[float, float]]]]
    ):
        """Appends the tracer's curve to the list"""
        return self.tracer.append_curve_to_list(curves_list)

    def stop(self):
        self.tracer.stop()
        self.thread.wait()


class TraceManager:
    """Manages tracing jobs and drawing curves"""

    draw_interval = 50  # ms
    show_stop_button_delay = 1500  # ms

    def __init__(
        self,
        plot_axes: Axes,
        plot_figure: Figure,
        show_stop_button: Callable,
        hide_stop_button: Callable,
    ):
        self.show_stop_button = show_stop_button
        self.hide_stop_button = hide_stop_button

        # remember running jobs
        self.jobs: list[Job] = []
        # timer for periodic drawing
        self.create_timer()
        # drawing manager
        self.create_drawing_manager(plot_axes, plot_figure)

    def stop_all_threads(self):
        """Stops all running threads"""
        # stop the timer
        self.timer.stop()
        self.timer_thread.quit()
        self.timer_thread.wait()
        # stop all jobs
        self.stop_tracing()
        # stop the drawing manager
        self.drawing_manager.stop()
        self.drawing_manager_thread.quit()
        self.drawing_manager_thread.wait()

    def create_timer(self):
        """Creates and starts a timer for periodic drawing"""
        self.timer_thread = QThread()
        self.timer = PeriodicTimer(self.draw_interval, self.draw_all_curves)
        self.timer.moveToThread(self.timer_thread)
        self.timer_thread.started.connect(self.timer.run)
        self.timer_thread.finished.connect(self.timer.deleteLater)
        self.timer_thread.start()

    def create_drawing_manager(self, plot_axes: Axes, plot_figure: Figure):
        """Creates and starts a drawing manager in a separate thread"""
        self.drawing_manager_thread = QThread()
        self.drawing_manager = DrawingManager(plot_axes, plot_figure)
        self.drawing_manager.moveToThread(self.drawing_manager_thread)
        self.drawing_manager_thread.started.connect(self.drawing_manager.run)
        self.drawing_manager_thread.finished.connect(self.drawing_manager.deleteLater)
        self.drawing_manager_thread.start()

    def remove_job_from_list(self, job: Job):
        """Removes 'job' from the list of running jobs"""
        self.jobs.remove(job)

    def stop_tracing(self):
        """Stops all running jobs and current drawing task"""
        for job in self.jobs:
            job.stop()
        self.drawing_manager.stop_current_task()

    def draw_all_curves(self):
        """Takes curve segments from all running jobs and gives them to the drawing manager"""
        if not self.jobs:
            return
        curves = []
        for job in self.jobs:
            job.append_curve_to_list(curves)
        if curves:
            self.drawing_manager.add_curve_collection(curves)

    def start_new_tracer(self, tracer: ParallelTracer):
        """Starts a new tracer in a new thread"""
        job = Job(tracer)

        def on_finished():
            self.remove_job_from_list(job)
            # hide the stop button if no jobs are running
            if not self.jobs:
                self.hide_stop_button()

        # start the job
        job.start(on_finished)
        self.jobs.append(job)

        # show the stop button if tracing takes too long
        def after_delay():
            if job in self.jobs:
                self.show_stop_button()

        QTimer.singleShot(self.show_stop_button_delay, after_delay)
