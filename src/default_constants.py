# TRACING CONSTANTS

# line width
MIN_TRACE_LINES_WIDTH = 1
MAX_TRACE_LINES_WIDTH = 10
DEFAULT_TRACE_LINES_WIDTH = 4

# line color
DEFAULT_TRACE_COLOR = "red"

# how many screens worth of space will be used to trace if the
# function goes out of the screen on Y axis before its cut off
DEFAULT_TRACE_Y_MARGIN = 20
MAX_TRACE_Y_MARGIN = 1000

# dx = (xlim[1]-xlim[0]) / 10^Granulity
MIN_TRACE_GRANULARITY = 2
MAX_TRACE_GRANULARITY = 7

# granularity is linearly interpolated from precision
MIN_TRACE_PRECISION = 1
MAX_TRACE_PRECISION = 10
DEFAULT_TRACE_PRECISION = 5

# minimum slope needed to enable singularity-handling if tracing in automatic mode
MIN_SINGULARITY_MIN_SLOPE = 10
MAX_SINGULARITY_MIN_SLOPE = 200
DEFAULT_SINGULARITY_MIN_SLOPE = 60

# size of line segments := diagonal_len / num_segments_in_diagonal
TRACE_NUM_SEGMENTS_IN_DIAGONAL = 500

# MOUSE LINE CONSTANTS

DEFAULT_MOUSE_LINE_WIDTH = 4
DEFAULT_MOUSE_LINE_LENGTH = 4

# ARROWS CONSTANTS

# arrow length
MIN_ARROW_LENGTH = 1
MAX_ARROW_LENGTH = 20
DEFAULT_ARROW_LENGTH = 7

# arrow width
MIN_ARROW_WIDTH = 1
MAX_ARROW_WIDTH = 20
DEFAULT_ARROW_WIDTH = 6

# number of arrows
MIN_NUM_ARROWS = 1
MAX_NUM_ARROWS = 150
DEFAULT_NUM_ARROWS = 26

# APP INITIALIZATION CONSTANTS
DEFAULT_FUNCTION = "x/y"
AXIS_RATIO = 1.5
DEFAULT_XMIN = -2.5
DEFAULT_XMAX = 2.5
DEFAULT_YMIN = DEFAULT_XMIN / AXIS_RATIO
DEFAULT_YMAX = DEFAULT_XMAX / AXIS_RATIO

# COLOR CONSTANTS

# color precision
# higher precision --> smaller dx for calculating curvature
MIN_COLOR_PRECISION = 1
MAX_COLOR_PRECISION = 10
DEFAULT_COLOR_PRECISION = 6

# color intensity
# smaller intensity --> even small differences in curvature are visible
MIN_COLOR_INTENSITY = 1
MAX_COLOR_INTENSITY = 15
DEFAULT_COLOR_INTENSITY = 5

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
