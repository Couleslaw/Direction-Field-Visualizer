import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import Normalize
from matplotlib import cm

from math import fabs
from src.direction_field.direction_field_settings import DirectionFieldSettings


class DirectionFieldBuilder:
    """Class for calculating arrows and colors for drawing direction fields."""

    def __init__(self, plot_axes: Axes, settings: DirectionFieldSettings):
        self._settings = settings
        self._arrows_cache = {}
        self._plot_axes = plot_axes

    def reset_arrow_cache(self):
        """Resets the arrow cache."""
        self._arrows_cache = {}

    def get_arrow(self, x, y, arrow_len, use_cache=True):
        """
        x, y: center of the arrow
        returns: [s1, s2, v1, v2] where (s1, s2) is the start of the arrow and (v1, v2) is the vector of the arrow
        """

        # check cache
        if use_cache and (x, y) in self._arrows_cache:
            return self._arrows_cache[(x, y)]

        try:
            der = self._settings.function(x, y)
            vector = np.array([1, der])
        # this is raised in the case of nonzero/0 --> draw a vertical line
        except FloatingPointError:
            vector = np.array([0, 1])
        # this is raised in the case of 0/0  --> dont draw anything
        except ZeroDivisionError:
            return None
        # this is raised if the function is not defined at the point e.i. sqrt(-1)
        except ValueError:
            return None
        # e.i sinsin(x) --> this is taken care of later
        except NameError as e:
            raise e

        center = np.array([x, y])
        vector = vector / np.linalg.norm(vector) * arrow_len

        res = np.append(center - vector / 2, vector)
        if use_cache:
            self._arrows_cache[(x, y)] = res
        return res

    def get_curvature_at(self, x, y, dx):
        """
        Returns the curvature of the function at the point (x, y)
        """

        if fabs(x - int(x)) < dx:
            x = int(x)
        if fabs(y - int(y)) < dx:
            y = int(y)

        def get_curvature(x, y):
            dy = self._settings.function(x, y)
            d2y = (
                self._settings.function(x + dx, y + dx * dy)
                - self._settings.function(x - dx, y - dx * dy)
            ) / (2 * dx)
            return d2y / (1 + dy**2) ** 1.5

        xlim = self._plot_axes.get_xlim()
        ylim = self._plot_axes.get_ylim()
        fix_dx = max(0.002, (xlim[1] - xlim[0]) / 1000)
        fix_dy = max(0.002, (ylim[1] - ylim[0]) / 1000)
        try:
            return get_curvature(x, y)
        except:
            try:
                return get_curvature(x, y + fix_dy)
            except:
                try:
                    return get_curvature(x + fix_dx, y)
                except:
                    return 0

    def normalize_curvatures(self, curvatures, ignore):
        """Normalizes curvatures to values between 0 and 1 while ignoring values off screen and the most extreme value"""

        on_screen = curvatures[np.logical_not(ignore)]
        if len(on_screen) == 0:
            return Normalize()(curvatures)
        # if there is only one max value, which is more than twice as big as the second max value
        # it is quite likely that this is a fluke caused by division by zero --> ignore it
        # in fact lets increase the number from 1 to a number based on #arrows
        max_val = max(on_screen)
        second_max = -np.inf
        num_max = 0
        for val in on_screen:
            if val == max_val:
                num_max += 1
            elif val > second_max:
                second_max = val
        if second_max == -np.inf:
            second_max = max_val

        limit = max(1, self._settings.num_arrows // 1000)
        if 1 <= num_max <= limit and max_val > 2 * second_max:
            max_val = second_max

        return Normalize(clip=True, vmin=0, vmax=max_val)(curvatures)

    def get_colors(self, points):
        """Returns colors for the arrows based on the curvature of the function at the arrow's center."""

        if not self._settings.show_colors:
            return "black"

        xlim = self._plot_axes.get_xlim()  # save old lims
        ylim = self._plot_axes.get_ylim()
        curvature_dx = self._settings.get_curvature_dx()

        curvatures = []
        ignore = []
        for x, y in points:
            curvatures.append(self.get_curvature_at(x, y, curvature_dx))
            if xlim[0] <= x <= xlim[1] and ylim[0] <= y <= ylim[1]:
                ignore.append(False)
            else:
                ignore.append(True)

        curvatures = self.normalize_curvatures(np.abs(curvatures), ignore)

        exponent = self._settings.get_color_exp()
        color_map = self._settings.color_map
        return cm.get_cmap(color_map)(curvatures**exponent)

    def get_arrows(self):
        """
        If the slope function is valid, returns (arrows, arrow_centers) where arrows is a 4xN array of arrow data
        If the slope function is invalid, returns None
        """

        xlim = self._plot_axes.get_xlim()
        ylim = self._plot_axes.get_ylim()
        diagonal = np.sqrt((xlim[1] - xlim[0]) ** 2 + (ylim[1] - ylim[0]) ** 2)

        arrow_len = diagonal * self._settings.get_relative_arrow_length()
        num_arrows = self._settings.num_arrows

        # space between arrows
        x_step = (xlim[1] - xlim[0]) / num_arrows
        y_step = (
            (ylim[1] - ylim[0]) / num_arrows
            if self._plot_axes.get_aspect() != 1  # if auto axes
            else x_step  # if equal_axes
        )

        # margin at the edge off the screen to help with drawing while dragging
        x_margin = (num_arrows // 6) * x_step + (x_step / 2 if num_arrows % 2 == 0 else 0)
        y_margin = (num_arrows // 6) * y_step + (y_step / 2 if num_arrows % 2 == 0 else 0)
        f = lambda n, s: s * (n // s)
        xs = np.arange(f(xlim[0], x_step) - x_margin, xlim[1] + x_step + x_margin, x_step)
        ys = np.arange(f(ylim[0], y_step) - y_margin, ylim[1] + y_step + y_margin, y_step)

        arrow_centers = []
        arrows = []
        try:
            for x in xs:
                for y in ys:
                    if (arrow := self.get_arrow(x, y, arrow_len)) is None:
                        # the function isn't defined at the point
                        continue
                    arrows.append(arrow)
                    arrow_centers.append((x, y))

            return np.array(arrows).T, arrow_centers

        # if the slope function is invalid
        except NameError:
            return None


class DirectionFieldPlotter:
    """Class for drawing direction fields."""

    def __init__(self, plot_axes: Axes, settings: DirectionFieldSettings):
        self._plot_axes = plot_axes
        self.settings = settings

    def draw_field(self, arrows, colors):
        """Draws the direction field on the plot."""

        # save old lims
        xlim = self._plot_axes.get_xlim()
        ylim = self._plot_axes.get_ylim()

        # clear the plot
        self._plot_axes.cla()

        # draw the arrows
        self._plot_axes.quiver(
            arrows[0],
            arrows[1],
            arrows[2],
            arrows[3],
            angles="xy",
            scale_units="xy",
            scale=1,
            width=self.settings.get_arrow_width(),
            color=colors,
            cmap="hsv",
        )

        # set old lims
        self._plot_axes.set_xlim(*xlim)
        self._plot_axes.set_ylim(*ylim)

        # draw the grid
        if self.settings.show_grid:
            self._plot_axes.grid(True)

        # draw the axes
        if self.settings.show_axes:
            self._plot_axes.axvline(0, color="black", linewidth=1)
            self._plot_axes.axhline(0, color="black", linewidth=1)
