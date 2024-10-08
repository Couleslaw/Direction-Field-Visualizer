import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from src.canvas_manager import CanvasManager
from src.default_constants import DEFAULT_XMIN, DEFAULT_XMAX, DEFAULT_YMIN, DEFAULT_YMAX


class Canvas(FigureCanvas):
    """Ensures communication between the matplotlib figure and PyQt5 GUI."""

    def __init__(self, parent):  # parent is the QtWidget object the figure will be embedded in
        self.fig, self.ax = plt.subplots()
        super().__init__(self.fig)
        self.setParent(parent)
        self.parent = parent
        self.pyplot_code()

    def pyplot_code(self):
        """Create the DerectionFieldBuilder object and set default parameters."""
        self.ax.set_xlim(DEFAULT_XMIN, DEFAULT_XMAX)
        self.ax.set_ylim(DEFAULT_YMIN, DEFAULT_YMAX)
        self.ax.axvline(0, color="r", linewidth=1)
        self.ax.axhline(0, color="r", linewidth=1)
        (plot,) = self.ax.plot([0], [0])
        self.manager = CanvasManager(
            plot,
            self.parent,
        )
        self.manager.connect()

    def get_xlim(self):
        return self.ax.get_xlim()

    def get_ylim(self):
        return self.ax.get_ylim()

    def set_xlim(self, xlim):
        self.ax.set_xlim(xlim)

    def set_ylim(self, ylim):
        self.ax.set_ylim(ylim)

    def zoom(self, zoom_in: bool):
        self.manager.zoom(zoom_in)

    def centralize_plot_x(self):
        xlim = self.get_xlim()
        x_range = xlim[1] - xlim[0]
        self.set_xlim([-x_range / 2, x_range / 2])
        self.redraw()

    def centralize_plot_y(self):
        ylim = self.get_ylim()
        y_range = ylim[1] - ylim[0]
        self.set_ylim([-y_range / 2, y_range / 2])
        self.redraw()

    def set_num_arrows(self, num_arrows):
        self.manager.field_settings.num_arrows = num_arrows
        self.redraw()

    def set_arrow_length(self, arrow_length):
        self.manager.field_settings.arrow_length = arrow_length
        self.redraw()

    def set_arrow_width(self, arrow_width):
        self.manager.field_settings.arrow_width = arrow_width
        self.redraw()

    def set_color_contrast(self, color_contrast):
        self.manager.field_settings.color_contrast = color_contrast
        self.redraw()

    def set_color_precision(self, color_precision):
        self.manager.field_settings.color_precision = color_precision
        self.redraw()

    def set_show_field_colors(self, show_colors):
        self.manager.field_settings.show_colors = show_colors
        self.redraw()

    def set_color_map(self, color_map):
        self.manager.field_settings.color_map = color_map
        self.redraw()

    def set_grid_enabled(self, enabled):
        self.manager.field_settings.show_grid = enabled
        self.redraw()

    def set_axes_enabled(self, enabled):
        self.manager.field_settings.show_axes = enabled
        self.redraw()

    def set_mouse_line_width(self, mouse_line_width):
        self.manager.mouse_line_width = mouse_line_width
        self.manager.draw_mouse_line()

    def set_mouse_line_length(self, mouse_line_length):
        self.manager.mouse_line_length = mouse_line_length
        self.manager.draw_mouse_line()

    def set_drawing_mouse_line(self, drawing_mouse_line):
        self.manager.drawing_mouse_line = drawing_mouse_line
        if drawing_mouse_line:
            self.manager.draw_mouse_line()
        else:
            self.manager.remove_mouse_line_from_plot()

    def set_new_function(self, new_function: str) -> bool:
        if self.manager.set_new_function(new_function):
            self.redraw()
            return True
        return False

    def set_equal_axes(self):
        self.redraw()
        self.manager.plot.axes.axis("equal")
        self.redraw()

    def set_auto_axes(self):
        self.manager.plot.axes.axis("auto")
        self.redraw()

    def redraw(self):
        self.manager.draw_field()
