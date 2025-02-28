# importing Canvas for type annotations like this to prevent circular imports
from __future__ import annotations
from typing import Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.canvas import Canvas


from PyQt6.QtWidgets import QMessageBox
from matplotlib.backend_bases import MouseEvent
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

    def __init__(self, canvas: Canvas) -> None:
        """Initializes a new CanvasManager of the given canvas.

        Args:
            canvas (Canvas): Canvas to manage.
        """
        self.__canvas = canvas

        # tracing
        self.trace_settings = TraceSettings()
        self.trace_manager = TraceManager(
            self.__canvas.axes,
            self.__canvas.figure,
            canvas.app.show_stop_tracing_button,
            canvas.app.hide_stop_tracing_button,
        )

        self.field_settings = DirectionFieldSettings()
        self.__field_builder = DirectionFieldBuilder(self.__canvas.axes, self.field_settings)
        self.__field_plotter = DirectionFieldPlotter(self.__canvas.axes, self.field_settings)

        # connect the canvas to user input events
        self.__connect()

        # True if the canvas can be moved
        self.canvas_locked: bool = False

        # True if there are no trace curves drawn on the canvas
        self.__no_trace_curves_on_canvas: bool = True

        # holds x, y of pressed point while moving, else None
        self.__press: Tuple[float, float] | None = None

        # True if the canvas is being moved
        self.__moving_canvas: bool = False

        # True if mouse line is being drawn
        self.__drawing_mouse_line: bool = False

        # line object of the last drawn mouse line or None
        self.__last_mouse_line = None

        # x, y of the mouse cursor or None
        self.__mouse_pos: Tuple[float, float] | None = None

        self.__mouse_line_width = DEFAULT_MOUSE_LINE_WIDTH
        self.__mouse_line_length = DEFAULT_MOUSE_LINE_LENGTH

        self.__motion_counter = 0

    def set_drawing_mouse_line(self, drawing: bool) -> None:
        """Sets the drawing mouse line state."""
        self.__drawing_mouse_line = drawing

    @property
    def mouse_line_width(self) -> int:
        """The width of the mouse line."""
        return self.__mouse_line_width

    @mouse_line_width.setter
    def mouse_line_width(self, width: int) -> None:
        """Sets the width of the mouse line."""
        self.__mouse_line_width = width

    @property
    def mouse_line_length(self) -> int:
        """The length of the mouse line."""
        xlim = self.__canvas.xlim
        ylim = self.__canvas.ylim
        diagonal = np.sqrt((xlim[1] - xlim[0]) ** 2 + (ylim[1] - ylim[0]) ** 2)
        return diagonal / 40 * self.__mouse_line_length

    @mouse_line_length.setter
    def mouse_line_length(self, length: int) -> None:
        """Sets the length of the mouse line."""
        self.__mouse_line_length = length

    @property
    def plot_is_empty(self) -> bool:
        """True if there are no trace curves drawn on the canvas, False otherwise."""
        return self.__no_trace_curves_on_canvas

    def stop_all_threads(self) -> None:
        """Stops all tracing threads."""
        self.trace_manager.stop_all_threads()

    def __connect(self) -> None:
        """Connect the Canvas to user input events."""

        self.cidpress = self.__canvas.figure.canvas.mpl_connect(
            "button_press_event", self.__on_press
        )
        self.cidrelease = self.__canvas.figure.canvas.mpl_connect(
            "button_release_event", self.__on_release
        )
        self.cidmotion = self.__canvas.figure.canvas.mpl_connect(
            "motion_notify_event", self.__on_motion
        )
        self.cidzoom = self.__canvas.figure.canvas.mpl_connect("scroll_event", self.__on_scroll)

    def __on_press(self, event: MouseEvent) -> None:
        """
        Begins canvas movement if the left mouse button was clicked.
        Starts tracing from the clicked point if the right mouse button was clicked.
        """

        if event.inaxes != self.__canvas.axes:
            return

        assert event.xdata is not None and event.ydata is not None

        # left mouse button --> begin canvas movement
        if event.button == 1 and not self.canvas_locked:
            self.draw_field(keep_cache=True)
            self.__press = (event.xdata, event.ydata)
            self.__moving_canvas = True

        # right mouse button --> start tracing the field from the clicked point
        elif event.button == 3:
            self.__press = (event.xdata, event.ydata)
            self.trace_curve()

    def __on_motion(self, event: MouseEvent) -> None:
        """Changes axes limits when moving_canvas"""

        # if outside of the matplotlib plot
        if event.inaxes != self.__canvas.axes:
            # if a direction line is being drawn at the mouse location
            if self.__last_mouse_line is not None:
                # remove line - mouse is out of bounds
                self.remove_mouse_line_from_plot()
                self.__canvas.figure.canvas.draw()
                self.__last_mouse_line = None
            return

        # if the canvas is locked, do not move it
        if self.canvas_locked:
            return

        assert event.xdata is not None and event.ydata is not None
        self.__mouse_pos = (event.xdata, event.ydata)

        # if a direction line is being drawn at the mouse location --> redraw after movement
        if self.__drawing_mouse_line:
            self.draw_mouse_line()
        if self.__press is None or not self.__moving_canvas:
            return

        # move the canvas based on the mouse shift
        dx, dy = self.__mouse_pos[0] - self.__press[0], self.__mouse_pos[1] - self.__press[1]
        xlim, ylim = self.__canvas.xlim, self.__canvas.ylim

        # set new canvas limits
        self.__canvas.xlim = (xlim[0] - dx, xlim[1] - dx)
        self.__canvas.ylim = (ylim[0] - dy, ylim[1] - dy)
        self.__canvas.app.update_displayed_axes_limits()

        # redraw the plot every 3rd motion event
        self.__motion_counter += 1
        if self.__motion_counter % 3 == 0:
            self.__motion_counter = 0
            self.draw_field(keep_cache=True)
        else:
            # updates the plot without redrawing the direction field
            self.__canvas.figure.canvas.draw()

    def __on_release(self, event: MouseEvent) -> None:
        """Stops canvas movement."""

        # check if the operation can be done
        if (self.__press is None) or (event.inaxes != self.__canvas.axes) or (self.canvas_locked):
            return

        # accept only left mouse button
        if event.button != 1:
            return

        if self.__moving_canvas:
            self.__moving_canvas = False
            self.draw_field(keep_cache=True)
        self.__press = None

    def __on_scroll(self, event: MouseEvent) -> None:
        """Zooms in and out by scaling the x and y limitss accordingly."""

        if event.inaxes != self.__canvas.axes:
            return

        zoom_in = event.button == "up"
        self.zoom(zoom_in, event.xdata, event.ydata)

    def zoom(self, zoom_in: bool, x: float | None = None, y: float | None = None) -> None:
        """Zooms in or out by scaling the x and y limits accordingly.
        If `x` and `y` are `None`, zooms to the center of the plot. Else zooms to the point `(x, y)`.

        Args:
            zoom_in (bool): _description_
            x (float | None, optional): x-coordinate of zoom center. Defaults to None.
            y (float | None, optional): y-coordinate of zoom center. Defaults to None.
        """

        if self.canvas_locked:
            return

        # get current limits
        (xmin, xmax), (ymin, ymax) = (
            self.__canvas.xlim,
            self.__canvas.ylim,
        )

        # if x and y are None, zoom to the center of the plot
        if x is None or y is None:
            x, y = (xmin + xmax) / 2, (ymin + ymax) / 2

        # calculate the distance from the point to the edges of the plot
        xleft, xright, ydown, yup = (
            x - xmin,
            xmax - x,
            y - ymin,
            ymax - y,
        )

        if zoom_in:
            # if the zoom is too large, do not zoom
            if (xmax - xmin < MAX_ZOOM) or (ymax - ymin < MAX_ZOOM):
                return
            margin = 1 - 2 / (ZOOM + 1)
            xlim = (xmin + margin * xleft, xmax - margin * xright)
            ylim = (ymin + margin * ydown, ymax - margin * yup)

        else:  # zoom out
            margin = (ZOOM - 1) / 2
            xlim = (xmin - margin * xleft, xmax + margin * xright)
            ylim = (ymin - margin * ydown, ymax + margin * yup)

        # set new limits
        self.__canvas.xlim = xlim
        self.__canvas.ylim = ylim
        self.__canvas.app.update_displayed_axes_limits()
        self.draw_field()

    def set_new_function(self, new_function_str: str) -> bool:
        """Sets a new slope-function to be draw if it is valid.

        Args:
            new_function (str): The new slope-function to be drawn.

        Returns:
            success (bool): True if the function is valid and was set, False otherwise.
        """

        # check if the new function is the same as the previous one
        if new_function_str == self.field_settings.function_string:
            return True

        # check if the new function is syntactically correct
        try:
            new_function = create_function_from_string(new_function_str)
        except SyntaxError:
            return False

        # save the previous function in case the new one is invalid
        previous_function = self.field_settings.function

        # set new function and try to recalculate the direction field
        self.field_settings.function = new_function
        builder = DirectionFieldBuilder(self.__canvas.axes, self.field_settings)
        arrows = builder.get_arrows()

        # if the function is invalid, revert to the previous function
        if arrows is None:
            self.field_settings.function = previous_function
            return False

        # if the function is valid, update the function string
        self.field_settings.function_string = new_function_str
        return True

    def draw_field(self, keep_cache: bool = False) -> None:
        """Draws the direction field. If keep_cache is False, the arrow-cache is cleared."""

        self.trace_manager.stop_tracing()

        if not keep_cache:
            self.__field_builder.clear_arrow_cache()

        # try to calculate direction field
        result = self.__field_builder.get_arrows()
        if result == None:
            # display a message box if the function is invalid
            QMessageBox.critical(self.__canvas.app, "Error", f"Invalid function.")
            return

        arrows, arrow_centers = result

        # if there are no arrows to draw, return
        if len(arrows) == 0:
            return

        # traced curves will be removed
        self.__no_trace_curves_on_canvas = True

        # draw the direction field
        colors = self.__field_builder.get_colors(arrow_centers)
        self.__field_plotter.draw_field(arrows, colors)

        # draw mouse line
        if self.__drawing_mouse_line:
            self.draw_mouse_line()

        # update the plot
        self.__canvas.figure.canvas.draw()

    def trace_from_point(self, x: float, y: float) -> None:
        """Traces the curve from the point `(x, y)`."""
        self.__press = (x, y)
        self.trace_curve()

    def trace_curve(self) -> None:
        """Draws a solution curve passing through `self.__press`."""
        if self.__press is None:
            return

        # there will be a traced curve on the canvas
        self.__no_trace_curves_on_canvas = False

        x, y = self.__press
        current_settings = self.trace_settings.copy()

        # create the two tracers - to the left and right of the point
        right_tracer = ParallelTracer(
            x,
            y,
            self.__canvas.xlim,
            self.__canvas.ylim,
            SolutionTracer.Direction.Right,
            self.field_settings.function_string,
            current_settings,
        )

        left_tracer = ParallelTracer(
            x,
            y,
            self.__canvas.xlim,
            self.__canvas.ylim,
            SolutionTracer.Direction.Left,
            self.field_settings.function_string,
            current_settings,
        )

        # start the tracers
        self.trace_manager.start_new_tracer(right_tracer)
        self.trace_manager.start_new_tracer(left_tracer)

    def remove_mouse_line_from_plot(self) -> None:
        """Remove the direction line drawn at the mouse cursor location"""
        if self.__last_mouse_line is not None:
            try:
                self.__canvas.axes.lines.remove(self.__last_mouse_line[0])
            except:
                return
            self.__canvas.figure.canvas.draw()

    def draw_mouse_line(self) -> None:
        """Draws a direction line at the mouse cursor location"""
        if self.__mouse_pos is None:
            return

        # remove the old arrow
        self.remove_mouse_line_from_plot()

        # calculate coordinates of the new arrow
        line_info = self.__field_builder.get_arrow(
            self.__mouse_pos[0], self.__mouse_pos[1], self.mouse_line_length, use_cache=False
        )

        # if the mouse cursor is in an area where the function is not defined --> return
        if line_info is None:
            return

        # create the new arrow
        x1, y1 = line_info[0], line_info[1]
        x2, y2 = x1 + line_info[2], y1 + line_info[3]

        self.__last_mouse_line = self.__canvas.axes.plot(
            [x1, x2],
            [y1, y2],
            color="r",
            linewidth=self.mouse_line_width,
            solid_capstyle="round",
        )

        # update the plot
        self.__canvas.figure.canvas.draw()
