# importing Canvas for type annotations like this to prevent circular imports
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.canvas import Canvas


from PyQt6.QtWidgets import QMessageBox
import numpy as np

np.seterr(divide="raise", invalid="ignore")


from src.math_functions import *
from src.default_constants import *

from src.tracing.trace_settings import TraceSettings
from src.tracing.solution_tracer import SolutionTracer

from src.direction_field.direction_field_settings import DirectionFieldSettings
from src.direction_field.direction_field_builder import (
    DirectionFieldPlotter,
    DirectionFieldBuilder,
)

from src.threading.parallel_tracer import ParallelTracer
from src.threading.trace_manager import TraceManager


class CanvasManager:
    """Plots direction fields using the matplotlib library."""

    def __init__(self, canvas: Canvas):
        self._canvas = canvas

        self.trace_settings = TraceSettings()
        self.trace_manager = TraceManager(
            self._canvas.axes,
            self._canvas.figure,
            canvas.app.show_stop_tracing_button,
            canvas.app.hide_stop_tracing_button,
        )
        self.has_trace_curves_on_plot = False
        self.field_settings = DirectionFieldSettings()
        self.field_builder = DirectionFieldBuilder(self._canvas.axes, self.field_settings)
        self.field_plotter = DirectionFieldPlotter(self._canvas.axes, self.field_settings)

        self.canvas_locked = False  # True if the canvas can be moved
        self.press = None  # holds x, y of pressed point while moving, else None
        self.moving_canvas = False  # True if the canvas is being moved
        self.drawing_mouse_line = False
        self.last_mouse_line = None
        self.mouse_pos = None

        self.mouse_line_width = DEFAULT_MOUSE_LINE_WIDTH
        self.mouse_line_length = DEFAULT_MOUSE_LINE_LENGTH

        self.motion_counter = 0

    def stop_all_threads(self):
        """Stops all the threads."""
        self.trace_manager.stop_all_threads()

    def lock_canvas(self, lock: bool):
        """Locks or unlocks the canvas."""
        self.canvas_locked = lock

    def connect(self):
        """Connect to all the events we need."""
        self.cidpress = self._canvas.figure.canvas.mpl_connect(
            "button_press_event", self.on_press
        )
        self.cidrelease = self._canvas.figure.canvas.mpl_connect(
            "button_release_event", self.on_release
        )
        self.cidmotion = self._canvas.figure.canvas.mpl_connect(
            "motion_notify_event", self.on_motion
        )
        self.cidzoom = self._canvas.figure.canvas.mpl_connect("scroll_event", self.on_scroll)

    def on_press(self, event):
        """
        Begins canvas movement if the left mouse button was clicked
        """
        if event.inaxes != self._canvas.axes:
            return

        # left mouse button --> begin canvas movement
        elif event.button == 1 and not self.canvas_locked:
            self.draw_field(keep_cache=True)
            self.press = (event.xdata, event.ydata)
            self.moving_canvas = True
        # right mouse button --> start tracing the field from the clicked point
        elif event.button == 3:
            self.press = (event.xdata, event.ydata)
            self.trace_curve()

    def on_motion(self, event):
        """Changes axes lims when moving_canvas"""
        # if outside of the matplotlib plot
        if event.inaxes != self._canvas.axes:
            # if a direction line is being drawn at the mouse location
            if self.last_mouse_line is not None:
                # remove line - mouse is out of bounds
                self.remove_mouse_line_from_plot()
                self._canvas.figure.canvas.draw()
                self.last_mouse_line = None
            return

        if self.canvas_locked:
            return

        self.mouse_pos = (event.xdata, event.ydata)

        # if a direction line is being drawn at the mouse location --> redraw after movement
        if self.drawing_mouse_line:
            self.draw_mouse_line()
        if self.press is None or not self.moving_canvas:
            return

        xlast, ylast = self.press

        dx, dy = event.xdata - xlast, event.ydata - ylast
        self._canvas.axes.set_xlim(*[x - dx for x in self._canvas.axes.get_xlim()])
        self._canvas.axes.set_ylim(*[y - dy for y in self._canvas.axes.get_ylim()])

        self._canvas.app.update_displayed_lims()

        self.motion_counter += 1
        if self.motion_counter % 3 == 0:
            self.motion_counter = 0
            self.draw_field(keep_cache=True)
        else:
            self._canvas.figure.canvas.draw()

    def on_release(self, event):
        """Stops canvas movement or point movement."""
        if self.press is None or event.inaxes != self._canvas.axes or self.canvas_locked:
            return

        if self.moving_canvas:
            self.moving_canvas = False
            self.draw_field(keep_cache=True)
        self.press = None

    def on_scroll(self, event):
        """Zooms in and out based on 'ZOOM' by scaling the x and y lims accordingly."""

        if event.inaxes != self._canvas.axes:
            return

        zoom_in = event.button == "up"
        self.zoom(zoom_in, event.xdata, event.ydata)

    def zoom(self, zoom_in: bool, x: float | None = None, y: float | None = None) -> None:
        """
        Zooms in or out based on the zoom_in parameter by scaling the x and y lims accordingly.
        If x and y are None, zooms to the center of the plot. Else zooms to the point (x, y).
        """

        if self.canvas_locked:
            return

        margin = (ZOOM - 1) / 2  # how much to add on both sides
        (xmin, xmax), (ymin, ymax) = self._canvas.axes.get_xlim(), self._canvas.axes.get_ylim()

        if x is None or y is None:
            x, y = (xmin + xmax) / 2, (ymin + ymax) / 2

        xleft, xright, ydown, yup = (
            x - xmin,
            xmax - x,
            y - ymin,
            ymax - y,
        )

        if zoom_in:
            if xmax - xmin < MAX_ZOOM:  # if max zoom has been reached
                return
            margin = 1 - 1 / (margin + 1)
            xlim = (xmin + margin * xleft, xmax - margin * xright)
            ylim = (ymin + margin * ydown, ymax - margin * yup)
        else:  # zoom out
            xlim = (xmin - margin * xleft, xmax + margin * xright)
            ylim = (ymin - margin * ydown, ymax + margin * yup)

        self._canvas.axes.set_xlim(*xlim)
        self._canvas.axes.set_ylim(*ylim)
        self._canvas.app.update_displayed_lims()
        self.draw_field()

    def set_new_function(self, new_function_str: str) -> bool:
        """Sets a new slope-function to be draw if it is valid.

        Args:
            new_function (str): The new slope-function to be drawn.

        Returns:
            bool: True if the function is valid and was set, False otherwise.
        """ """
        """

        if new_function_str == self.field_settings.function_string:
            return True

        # check if the new function is syntactically correct
        try:
            new_function = create_function_from_string(new_function_str)
        except SyntaxError:
            return False

        # save the previous function in case the new one is invalid
        previous_function = self.field_settings.function

        # set new function and redraw the plot
        self.field_settings.function = new_function
        builder = DirectionFieldBuilder(self._canvas.axes, self.field_settings)
        arrows = builder.get_arrows()

        # if the function is invalid, revert and redraw the plot
        if arrows is None:
            self.field_settings.function = previous_function
            return False

        # if the function is valid, update the function string
        self.field_settings.function_string = new_function_str
        return True

    def draw_field(self, keep_cache=False):
        """Draws the direction field. If keep_cache is False, the arrow-cache is cleared."""

        self.trace_manager.stop_tracing()

        if not keep_cache:
            self.field_builder._arrows_cache = {}

        result = self.field_builder.get_arrows()
        if result == None:
            QMessageBox.critical(self._canvas.app, "Error", f"Invalid function.")
            return

        arrows, arrow_centers = result
        if len(arrows) == 0:
            return

        # traced curves will be removed
        self.has_trace_curves_on_plot = False

        colors = self.field_builder.get_colors(arrow_centers)
        self.field_plotter.draw_field(arrows, colors)

        if self.drawing_mouse_line:
            self.draw_mouse_line()
        self._canvas.figure.canvas.draw()

    def trace_from_point(self, x, y):
        """Traces the curve from the point (x, y)"""
        self.press = (x, y)
        self.trace_curve()

    def trace_curve(self):
        """Draws a solution curve passing through self.press"""
        if self.press is None:
            return

        self.has_trace_curves_on_plot = True

        x, y = self.press
        settings = self.trace_settings.copy()

        # create the two tracers
        right_tracer = ParallelTracer(
            x,
            y,
            self._canvas.xlim,
            self._canvas.ylim,
            SolutionTracer.Direction.Right,
            self.field_settings.function_string,
            settings,
        )

        left_tracer = ParallelTracer(
            x,
            y,
            self._canvas.xlim,
            self._canvas.ylim,
            SolutionTracer.Direction.Left,
            self.field_settings.function_string,
            settings,
        )

        self.trace_manager.start_new_tracer(right_tracer)
        self.trace_manager.start_new_tracer(left_tracer)

    def remove_mouse_line_from_plot(self):
        """Remove the direction line drawn at the mouse cursor location"""
        if self.last_mouse_line is not None:
            try:
                self._canvas.axes.lines.remove(self.last_mouse_line[0])
            except:
                return
            self._canvas.figure.canvas.draw()

    def draw_mouse_line(self):
        """Draws a direction line at the mouse cursor location"""
        if self.mouse_pos is None:
            return

        xlim = self._canvas.axes.get_xlim()
        ylim = self._canvas.axes.get_ylim()
        diagonal = np.sqrt((xlim[1] - xlim[0]) ** 2 + (ylim[1] - ylim[0]) ** 2)
        vector_len = diagonal / 40 * self.mouse_line_length

        # calculate coordinates of the new arrow
        line_info = self.field_builder.get_arrow(
            self.mouse_pos[0], self.mouse_pos[1], vector_len, use_cache=False
        )

        # remove the old arrow
        self.remove_mouse_line_from_plot()

        # if the mouse cursor is in an area where the function is not defined --> return
        if line_info is None:
            return

        # create the new arrow
        x1 = line_info[0]
        y1 = line_info[1]
        x2 = x1 + line_info[2]
        y2 = y1 + line_info[3]
        self.last_mouse_line = self._canvas.axes.plot(
            [x1, x2],
            [y1, y2],
            color="r",
            linewidth=self.mouse_line_width,
            solid_capstyle="round",
        )
        self._canvas.figure.canvas.draw()
