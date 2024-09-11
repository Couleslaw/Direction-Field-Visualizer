# Direction Field Visualizer

A direction field is a graphical representation of the solutions to a first-order ordinary differential equation of the form

$$\frac{dy}{dx} = f(x,y).$$

The principle of the direction field is to draw small line segments each point $(x,y)$ in the plane. The slope of the line segment is given by the derivative, that is $f(x,y)$. The direction field can be used to visualize the behavior of solutions to the differential equation because these line segments are tangent to the solution curves.

This visualizer allows you to plot the direction field of a given differential equation. You can zoom in and out, move around and watch the direction field change in real time as well as tracing individual solution curves.

## How to install

Windows users can download an executable file from the [releases page](https://github.com/Couleslaw/Direction-Field-Visualizer/releases/latest). Linux and MacOS users can run the program by following the instructions below.

## Dependencies

This project is not compatible with the newer versions of matplotlib. It works with version 3.6.2. I recommend creating a virtual environment and installing the dependencies from the `requirements.txt` file.

Create and activate the virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate    # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Run the program with:

```bash
python3 main.py
```

Deactivate the virtual environment by running `deactivate`.

## User documentation

### Movement in the figure

- The graph can be moved by left-clicking and dragging.
- You can also zoom in and out using the scroll wheel.

### Tracing a solution curve

- To trace a solution curve, right-click on the point where you want to start.

### Entering the differential equation

- The differential equation must be syntactically correct. For example, you can't write `2x` instead of `2*x`. Use `**` for exponentiation. The available functions are

  - `sin`, `cos`, `tan`, `asin`, `acos`, `atan`
  - `sinh`, `cosh`, `tanh`, `asinh`, `acosh`, `atanh`,
  - `exp`, `ln`=`log`, `log2`, `log10`
  - `sqrt`, `abs`, `sign`, `floor`, `ceil`
  - constants `pi` and `e`

- Confirm the differential equation by pressing the 'Enter' key or by clicking the 'Graph' button.

### Changing graph parameters

- The number of arrows drawn can by change either by entering a number or by clicking the `+` and `-` buttons which change the value by 5.
- It is also possible to change the length of the arrows.

### Exporting the figure

- The figure can be exported as a `.png` or `.svg` file by clicking the 'Save image' button or by pressing 'Ctrl+S'.

### Changing the limits of the coordinate axes

- By default 'Equal axes' is toggled, but you can untoggle it to change the limits independently.
- You can't change limits manually while 'Equal axes' is toggled.

## Examples

ln(sqrt(sin(x)\*sin(y)))
