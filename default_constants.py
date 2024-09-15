# tracing
DEFAULT_TRACE_LINES_WIDTH = 4
MIN_TRACE_DX = 1e-9
TRACE_AUTO_DX_GRANULARITY = 10000
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
DEFAULT_COLOR_INTENSITY = 5
MIN_COLOR_INTENSITY = 1
MAX_COLOR_INTENSITY = 10
MIN_COLOR_EXP = 0.1
MAX_COLOR_EXP = 2.0
DEFAULT_COLOR_MAP = "viridis"
AVAILABLE_COLOR_MAPS = [
    "viridis",
    "plasma",
    "cividis",
    "turbo",
    "gnuplot",
    "brg",
    "gray",
    "spring",
    "cool",
    "hot",
    "rainbow",
    "prism",
]

# zoom
ZOOM = 2
MAX_ZOOM = 1e-3
