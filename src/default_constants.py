# tracing
DEFAULT_TRACE_LINES_WIDTH = 4
DEFAULT_TRACE_COLOR = "red"
DEFAULT_TRACE_Y_MARGIN = 20
MAX_TRACE_Y_MARGIN = 1000
# dx = (xlim[1]-xlim[0]) / 10^Granulity
MIN_TRACE_GRANULARITY = 2
MAX_TRACE_GRANULARITY = 6
MIN_TRACE_PRECISION = 1
DEFAULT_TRACE_PRECISION = 6
DEFAULT_SINGULARITY_MIN_SLOPE = 60
MIN_SINGULARITY_MIN_SLOPE = 10
MAX_SINGULARITY_MIN_SLOPE = 200

MAX_TRACE_PRECISION = 10


# linear interpolation of granularity form precision
def precision_to_granularity(precision):
    return MIN_TRACE_GRANULARITY + (MAX_TRACE_GRANULARITY - MIN_TRACE_GRANULARITY) * (
        precision - MIN_TRACE_PRECISION
    ) / (MAX_TRACE_PRECISION - MIN_TRACE_PRECISION)


TRACE_NUM_SEGMENTS_IN_DIAGONAL = 1000

# mouse line
DEFAULT_MOUSE_LINE_WIDTH = 4
DEFAULT_MOUSE_LINE_LENGTH = 4

# arrows
# length = 1    ~  1 / 200  of the length of the diagonal
DEFAULT_ARROW_LENGTH = 7
DEFAULT_ARROW_WIDTH = 6
DEFAULT_NUM_ARROWS = 26
MAX_NUM_ARROWS = 150

# start
DEFAULT_FUNCTION = "x/y"
AXIS_RATIO = 1.5
DEFAULT_XMIN = -2.5
DEFAULT_XMAX = 2.5
DEFAULT_YMIN = DEFAULT_XMIN / AXIS_RATIO
DEFAULT_YMAX = DEFAULT_XMAX / AXIS_RATIO

# color constants
DEFAULT_COLOR_PRECISION = 6  # 1 --> 1e-2, 8 -> 1e-9
DEFAULT_COLOR_INTENSITY = 5
MIN_COLOR_INTENSITY = 1
MAX_COLOR_INTENSITY = 10
MIN_COLOR_EXP = 0.1
MAX_COLOR_EXP = 2.0
DEFAULT_COLOR_MAP = "viridis"
AVAILABLE_COLOR_MAPS = [
    "viridis",
    "plasma",
    "inferno",
    "hot",
    "turbo",
    "gnuplot",
    "gnuplot2",
    "RdPu",
    "gray",
    "bone",
    "pink",
    "cividis",
    "cool",
    "ocean",
    "prism",
    "rainbow",
    "gist_rainbow",
    "gist_stern",
]

# zoom
ZOOM = 2
MAX_ZOOM = 1e-3
