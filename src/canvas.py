# importing VisualizerApp for type annotations like this to prevent circular imports
from __future__ import annotations
from typing import Tuple, TYPE_CHECKING
from math import sqrt

if TYPE_CHECKING:
    from src.gui.visualizer_app import VisualizerApp


import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from src.canvas_manager import CanvasManager
from src.default_constants import (
    DEFAULT_XMIN,
    DEFAULT_XMAX,
    DEFAULT_YMIN,
    DEFAULT_YMAX,
    AVAILABLE_COLOR_MAPS,
)


class Canvas(FigureCanvas):
    """Ensures communication between the matplotlib figure and Qt GUI."""

    def __init__(self, app: VisualizerApp) -> None:
        """Initializes the Canvas object and sets the default parameters.

        Args:
            app (VisualizerApp): The app in which the canvas is embedded.
        """

        self.__app = app

        # create the figure and axes
        self.__figure, self.__axes = plt.subplots()
        super().__init__(self.__figure)

        # set default axes limits
        self.__axes.set_xlim(DEFAULT_XMIN, DEFAULT_XMAX)
        self.__axes.set_ylim(DEFAULT_YMIN, DEFAULT_YMAX)

        # create the canvas manager
        self.manager = CanvasManager(self)

    @property
    def figure(self) -> Figure:
        """The matplotlib figure object of the canvas."""
        return self.__figure

    @figure.setter
    def figure(self, figure: Figure):
        """The setter for the figure property."""
        self.__figure = figure

    @property
    def axes(self) -> Axes:
        """The matplotlib axes object of the canvas."""
        return self.__axes

    @property
    def app(self) -> VisualizerApp:
        """The app in which the canvas is embedded."""
        return self.__app

    @property
    def xlim(self) -> Tuple[float, float]:
        """The limits of the x-axis."""
        return self.axes.get_xlim()

    @xlim.setter
    def xlim(self, xlim: Tuple[float, float]):
        self.__axes.set_xlim(*xlim)

    @property
    def ylim(self) -> Tuple[float, float]:
        """The limits of the y-axis."""
        return self.axes.get_ylim()

    @ylim.setter
    def ylim(self, ylim: Tuple[float, float]):
        self.__axes.set_ylim(*ylim)

    def zoom(self, zoom_in: bool) -> None:
        """Zooms in or out of the plot.

        Args:
            zoom_in (bool): zoom in if True, zoom out if False.
        """
        self.manager.zoom(zoom_in)

    def lock_canvas(self, lock: bool) -> None:
        """Locks or unlocks the canvas."""
        self.manager.canvas_locked = lock

    def stop_tracing(self) -> None:
        """Stops tracing of all partially drawn lines."""
        self.manager.trace_manager.stop_tracing()

    def centralize_plot_x(self) -> None:
        """Moves the plot along the x-axis so that (0,y) is in the center. Redraws the plot after."""
        xlim = self.xlim
        x_range = xlim[1] - xlim[0]
        self.xlim = (-x_range / 2, x_range / 2)
        self.redraw()

    def centralize_plot_y(self) -> None:
        """Moves the plot along the y-axis so that (x,0) is in the center. Redraws the plot after."""
        ylim = self.ylim
        y_range = ylim[1] - ylim[0]
        self.ylim = (-y_range / 2, y_range / 2)
        self.redraw()

    def set_num_arrows(self, num_arrows: int) -> None:
        """Sets the number of arrows to be drawn in each row of the direction field to `num_arrows`. Redraws the plot after."""
        self.manager.field_settings.num_arrows = num_arrows
        self.redraw()

    def set_arrow_length(self, arrow_length: int) -> None:
        """Sets the arrow length setting to `arrow_length`. Redraws the plot after."""
        self.manager.field_settings.set_arrow_length(arrow_length)
        self.redraw()

    def set_arrow_width(self, arrow_width: int) -> None:
        """Sets the arrow width setting to `arrow_width`. Redraws the plot after."""
        self.manager.field_settings.arrow_width = arrow_width
        self.redraw()

    def set_color_contrast(self, color_contrast: int) -> None:
        """Sets the color contrast setting to `color_contrast`. Redraws the plot after."""
        self.manager.field_settings.color_contrast = color_contrast
        self.redraw()

    def set_color_precision(self, color_precision: int) -> None:
        """Sets the color precision setting to `color_precision`. Redraws the plot after."""
        self.manager.field_settings.color_precision = color_precision
        self.redraw()

    def set_show_field_colors(self, show_colors: bool) -> None:
        """Changes between black and colorful arrows. Redraws the plot after.

        Args:
            show_colors (bool): True if the colors should be shown, False otherwise.
        """
        self.manager.field_settings.show_colors = show_colors
        self.redraw()

    def set_color_map(self, color_map: str) -> None:
        """Sets the color map of the direction field to `color_map`. Redraws the plot after."""
        assert color_map in AVAILABLE_COLOR_MAPS
        self.manager.field_settings.color_map = color_map
        self.redraw()

    def set_grid_enabled(self, enabled: bool) -> None:
        """Sets whether the grid lines should be shown or not. Redraws the plot after."""
        self.manager.field_settings.show_grid = enabled
        self.redraw()

    def set_axes_enabled(self, enabled: bool) -> None:
        """Sets whether the axes lines should be shown or not. Redraws the plot after."""
        self.manager.field_settings.show_axes = enabled
        self.redraw()

    def set_mouse_line_width(self, mouse_line_width: int) -> None:
        """Sets The display width of the mouse line to `mouse_line_width`. Redraws the mouse line after."""
        self.manager.mouse_line_width = mouse_line_width
        self.manager.draw_mouse_line()

    def set_mouse_line_length(self, mouse_line_length: int) -> None:
        """Sets the display length of the mouse line to `mouse_line_length`. Redraws the mouse line after."""
        self.manager.mouse_line_length = mouse_line_length
        self.manager.draw_mouse_line()

    def set_drawing_mouse_line(self, drawing_mouse_line: bool) -> None:
        """Sets whether the 'mouse line' should be drawn or not. Redraws the plot after."""
        self.manager.set_drawing_mouse_line(drawing_mouse_line)
        if drawing_mouse_line:
            self.manager.draw_mouse_line()
        else:
            self.manager.remove_mouse_line_from_plot()

    def set_new_function(self, new_function: str) -> bool:
        """Sets a new function to be draw if it is valid. Redraws the plot after.

        Args:
            new_function (str): The new function to be drawn.

        Returns:
            success (bool): True if the function is valid and was set, False otherwise.
        """
        if self.manager.set_new_function(new_function):
            self.redraw()
            return True
        return False

    def set_equal_axes(self) -> None:
        """Sets the plot axes to have equal scaling. Redraws the plot after."""

        # we will scale the axes so that the diagonal length and center of the plot is the same as before, but the axes are equal

        old_diagonal = sqrt((self.xlim[1] - self.xlim[0]) ** 2 + (self.ylim[1] - self.ylim[0]) ** 2)

        self.__axes.axis("equal")
        self.redraw()

        # r = dx / dy  -->  dx = r * dy
        ratio = (self.xlim[1] - self.xlim[0]) / (self.ylim[1] - self.ylim[0])

        # diagonal^2 = dx^2 + dy^2 = dy^2 * (r^2 + 1)  --> dy = diagonal / sqrt(r^2 + 1)
        dy = old_diagonal / sqrt(ratio**2 + 1)
        dx = dy * ratio

        x_center = (self.xlim[1] + self.xlim[0]) / 2
        y_center = (self.ylim[1] + self.ylim[0]) / 2

        # set the new axes limits
        self.xlim = (x_center - dx / 2, x_center + dx / 2)
        self.ylim = (y_center - dy / 2, y_center + dy / 2)

        self.redraw()
        self.app.update_displayed_axes_limits()

    def set_auto_axes(self) -> None:
        """
        Sets the plot axes to have automatic scaling. Redraws the plot after.
        This is used when the user wants to set custom axes limits.
        """
        old_xlim = self.xlim
        old_ylim = self.ylim
        self.__axes.axis("auto")
        self.xlim = old_xlim
        self.ylim = old_ylim
        self.redraw()
        self.app.update_displayed_axes_limits()

    def redraw(self) -> None:
        """Redraws the plot."""
        self.manager.draw_field(keep_cache=False)
