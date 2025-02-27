import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import Normalize
from matplotlib import cm

from typing import Dict, Tuple, List, Sequence
from numpy.typing import NDArray

from math import fabs
from src.direction_field.direction_field_settings import DirectionFieldSettings


class DirectionFieldBuilder:
    """Class for calculating arrows and colors for drawing direction fields."""

    def __init__(self, plot_axes: Axes, settings: DirectionFieldSettings):
        self.__settings = settings
        self.__arrows_cache: Dict[Tuple[float, float], NDArray[np.float64]] = {}
        self.__plot_axes = plot_axes

    def clear_arrow_cache(self):
        """Clears the arrow cache."""
        self.__arrows_cache = {}

    def get_arrow(
        self, x: float, y: float, arrow_len: float, use_cache: bool = True
    ) -> NDArray[np.float64] | None:
        """_summary_

        Args:
            x (float): the x coordinate of the arrow center.
            y (float): the y coordinate of the arrow center.
            arrow_len (float): the length of the arrow vector.
            use_cache (bool, optional): Looks for the result in cache first if set to True. Defaults to True.

        Raises:
            NameError: when the slope function is invalid.

        Returns:
            arrow (NDArray[np.float64]): `[s1,s2,v1,v2]` where `(s1,s2)` is the start of the arrow and `(v1,v2)` is the vector of the arrow.
            This means that `s + v` is the end of the arrow.
        """

        # check cache
        if use_cache and (x, y) in self.__arrows_cache:
            return self.__arrows_cache[(x, y)]

        # try to evaluate the slope function
        try:
            der = self.__settings.function(x, y)
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
        result = np.append(center - vector / 2, vector)

        # cache the result
        if use_cache:
            self.__arrows_cache[(x, y)] = result

        return result

    def get_curvature_at(self, x: float, y: float, dx: float) -> float:
        """
        Returns the curvature of the function at the point (x, y).

        Note: something that needs to be dealt with are cases similar to the following:
            y' = -x/y and (x,y) = (5, almost 0).
        The solution to the ODE are circles, so the curvature is 1/radius, but in practice we run into the limitation of floating point number and will get insanely high curvature.
        Solution: round number close to integers to integers. Now the curvature will raise a `ZeroDivisionError` and we can handle it.
        How? Shift the point a little bit and calculate the curvature there. If it still raises an error, something weird is going on and we return 0.
        """

        # if the point is almost an integer, round it
        if fabs(x - int(x)) < dx:
            x = int(x)
        if fabs(y - int(y)) < dx:
            y = int(y)

        def calculate_curvature(x: float, y: float) -> float:
            """Returns the curvature of the slope function at the point (x, y)."""
            dy = self.__settings.function(x, y)
            d2y = (
                self.__settings.function(x + dx, y + dx * dy)
                - self.__settings.function(x - dx, y - dx * dy)
            ) / (2 * dx)
            return d2y / (1 + dy**2) ** 1.5

        try:
            return calculate_curvature(x, y)
        except:
            # shifts for x and y for recalculating the curvature
            xlim = self.__plot_axes.get_xlim()
            ylim = self.__plot_axes.get_ylim()
            shift_x = max(0.002, (xlim[1] - xlim[0]) / 1000)
            shift_y = max(0.002, (ylim[1] - ylim[0]) / 1000)

            # try shifting y
            try:
                return calculate_curvature(x, y + shift_y)
            except:
                # try shifting x
                try:
                    return calculate_curvature(x + shift_x, y)
                except:
                    # if both fail, return 0
                    return 0

    def normalize_curvatures(
        self, curvatures: NDArray[np.float64], off_screen: Sequence[bool]
    ) -> NDArray[np.float64]:
        """Normalizes curvatures to values to `[0,1]`. When the max curvature for normalization is searched for,
        the most extreme value and the values on indices where `off_screen` is `True` are ignored.

        Args:
            curvatures (NDArray[np.float64]): Curvatures at arrow locations.
            off_screen (Sequence[bool]):
                Should be `len(curvatures) == len(off_screen)`. Says which points are on screen.

        Returns:
            out (NDArray[np.float64]): Normalized curvatures
        """

        assert len(curvatures) == len(off_screen)

        # get curvature values corresponding to points on screen
        on_screen = curvatures[np.logical_not(off_screen)]

        # if nothing is on screen -> just normalize everything to [0,1]
        if len(on_screen) == 0:
            return np.array(Normalize()(curvatures), dtype=np.float64)

        # if there is only one max value, which is more than twice as big as the second max value
        # it is quite likely that this is a fluke caused by division by zero --> ignore it
        # in fact lets increase the number from 1 to a number based on #arrows

        max_curvature = max(on_screen)
        num_max = 0  # number of points with curvature == max_curvature
        second_max_curvature = -np.inf
        for curvature in on_screen:
            if curvature == max_curvature:
                num_max += 1
            elif curvature > second_max_curvature:
                second_max_curvature = curvature
        if second_max_curvature == -np.inf:
            second_max_curvature = max_curvature

        # if the number of extreme arrows is smaller than `limit`, they will be ignored
        limit = max(1, self.__settings.num_arrows // 1000)
        if (max_curvature > 2 * second_max_curvature) and (1 <= num_max <= limit):
            normalization_max = second_max_curvature
        else:
            normalization_max = max_curvature

        return np.array(
            Normalize(clip=True, vmin=0, vmax=normalization_max)(curvatures), dtype=np.float64
        )

    def get_colors(self, points: Sequence[Tuple[float, float]]) -> str | np.ndarray:
        """Returns colors for the arrows based on the curvature of the function at the arrow's center."""

        # color every arrow black if colors are turned off
        if not self.__settings.show_colors:
            return "black"

        # save old axes limits
        xlim = self.__plot_axes.get_xlim()
        ylim = self.__plot_axes.get_ylim()
        curvature_dx = self.__settings.get_curvature_dx()

        #  calculate curvatures
        curvatures: list[float] = []
        off_screen: list[bool] = []
        for x, y in points:
            curvatures.append(self.get_curvature_at(x, y, curvature_dx))
            off_screen.append(
                False if (xlim[0] <= x <= xlim[1] and ylim[0] <= y <= ylim[1]) else True
            )

        # normalize and scale curvatures before mapping them to colors
        normalized_curvatures = self.normalize_curvatures(np.abs(curvatures), off_screen)
        exponent = self.__settings.get_color_exp()
        color_map = self.__settings.color_map
        return cm.get_cmap(color_map)(normalized_curvatures**exponent)

    def get_arrows(self) -> Tuple[NDArray[np.float64], List[Tuple[float, float]]] | None:
        """_summary_

        Returns
        ------
        arrows, arrow_centers : (NDArray[np.float64], List[Tuple[float, float]]):
            If the slope function is valid, where `arrows` is a 4xN array of arrow data.
        None:
            If the slope function is invalid.
        """

        #  get arrow length and number of arrows
        xlim, ylim = self.__plot_axes.get_xlim(), self.__plot_axes.get_ylim()
        arrow_len = self.__settings.calculate_arrow_length(xlim, ylim)
        num_arrows = self.__settings.num_arrows

        # space between arrows
        x_step = (xlim[1] - xlim[0]) / num_arrows
        y_step = (
            (ylim[1] - ylim[0]) / num_arrows
            if self.__plot_axes.get_aspect() != 1  # if auto axes
            else x_step  # if equal_axes
        )

        # margin at the edge off the screen to help with drawing while dragging
        x_margin = (num_arrows // 6) * x_step + (x_step / 2 if num_arrows % 2 == 0 else 0)
        y_margin = (num_arrows // 6) * y_step + (y_step / 2 if num_arrows % 2 == 0 else 0)
        f = lambda n, s: s * (n // s)
        xs = np.arange(f(xlim[0], x_step) - x_margin, xlim[1] + x_step + x_margin, x_step)
        ys = np.arange(f(ylim[0], y_step) - y_margin, ylim[1] + y_step + y_margin, y_step)

        # calculate arrows and their centers
        arrow_centers: List[Tuple[float, float]] = []
        arrows: List[NDArray[np.float64]] = []
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

    def __init__(self, plot_axes: Axes, settings: DirectionFieldSettings) -> None:
        self.__plot_axes = plot_axes
        self.__settings = settings

    def draw_field(self, arrows: NDArray[np.float64], colors: str | np.ndarray) -> None:
        """Draws the direction field on the plot."""

        # check if arrows are in correct data format
        assert len(arrows) == 4

        # save old lims
        xlim = self.__plot_axes.get_xlim()
        ylim = self.__plot_axes.get_ylim()

        # clear the plot
        self.__plot_axes.cla()

        # draw the arrows
        self.__plot_axes.quiver(
            arrows[0],
            arrows[1],
            arrows[2],
            arrows[3],
            angles="xy",
            scale_units="xy",
            scale=1,
            width=self.__settings.get_arrow_width(),
            color=colors,
            cmap="hsv",
        )

        # set old lims
        self.__plot_axes.set_xlim(*xlim)
        self.__plot_axes.set_ylim(*ylim)

        # draw the grid
        if self.__settings.show_grid:
            self.__plot_axes.grid(True)

        # draw the axes
        if self.__settings.show_axes:
            self.__plot_axes.axvline(0, color="black", linewidth=1)
            self.__plot_axes.axhline(0, color="black", linewidth=1)
