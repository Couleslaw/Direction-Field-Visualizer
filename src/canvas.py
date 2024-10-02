import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from src.direction_field_builder import DirectionFieldBuilder
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
        self.dfb = DirectionFieldBuilder(plot, self.parent)
        self.dfb.connect()

    def get_xlim(self):
        return self.ax.get_xlim()

    def get_ylim(self):
        return self.ax.get_ylim()

    def set_xlim(self, xlim):
        self.ax.set_xlim(xlim)

    def set_ylim(self, ylim):
        self.ax.set_ylim(ylim)

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

    def get_num_arrows(self):
        return self.dfb.num_arrows

    def set_num_arrows(self, num_arrows):
        self.dfb.num_arrows = num_arrows
        self.redraw()

    def set_arrow_length(self, arrow_length):
        self.dfb.arrow_length = arrow_length
        self.redraw()

    def set_arrow_width(self, arrow_width):
        self.dfb.arrow_width = arrow_width
        self.redraw()

    def set_color_contrast(self, color_contrast):
        self.dfb.color_contrast = color_contrast
        self.redraw()

    def set_color_precision(self, color_precision):
        self.dfb.color_precision = color_precision
        self.redraw()

    def set_is_colored(self, is_colored):
        self.dfb.indicate_colors = is_colored
        self.redraw()

    def set_color_map(self, color_map):
        self.dfb.color_map_name = color_map
        self.redraw()

    def set_grid_enabled(self, enabled):
        self.dfb.show_grid = enabled
        self.redraw()

    def set_axes_enabled(self, enabled):
        self.dfb.show_axes = enabled
        self.redraw()

    def set_mouse_line_width(self, mouse_line_width):
        self.dfb.mouse_line_width = mouse_line_width

    def set_mouse_line_length(self, mouse_line_length):
        self.dfb.mouse_line_length = mouse_line_length

    def redraw(self, just_entered_new_function=False):
        self.dfb.draw_field(just_entered_new_function)

    def set_equal_axes(self):
        self.redraw()
        self.dfb.plot.axes.axis("equal")

    def set_auto_axes(self):
        self.dfb.plot.axes.axis("auto")
        self.redraw()
