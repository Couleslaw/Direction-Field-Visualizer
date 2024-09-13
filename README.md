# Direction Field Visualizer

A direction field is a graphical representation of the solutions to a first-order ordinary differential equation of the form

$$\frac{dy}{dx} = f(x,y).$$

The principle of the direction field is to draw small line segments for each point $(x,y)$ in the plane. The slope of the line segment is given by the derivative, that is $f(x,y)$. The direction field can be used to visualize the behavior of solutions to the differential equation because these line segments are tangent to the solution curves.

Let's see an example. Consider the differential equation $y'(x)=-x/y$. The direction field looks like this:

![circle](images/circle.svg)

The tangent lines clearly form circles around the origin. The red semi-circles are two of the infinitely many solutions to the differential equation. We can guess that the general solution is of the form $y(x)=\pm\sqrt{A-x^2}$ which is indeed the case.

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

## Usage

### Entering the differential equation

- The differential equation must be syntactically correct. For example, you can't write `2x` instead of `2*x`. Use `**` for exponentiation. The available functions are

  - `sin`, `cos`, `tan`, `asin`, `acos`, `atan`
  - `sinh`, `cosh`, `tanh`, `asinh`, `acosh`, `atanh`,
  - `exp`, `ln`=`log`, `log2`, `log10`
  - `sqrt`, `abs`, `sign`, `floor`, `ceil`
  - constants `pi` and `e`

- Confirm the differential equation by pressing the 'Enter' key or by clicking the 'Graph' button.

### Movement in the figure

- The graph can be moved by left-clicking and dragging
- You can also zoom in and out using the scroll wheel

### Tracing a solution curve

- To trace a solution curve, right-click and a solution passing through that point will be drawn
- Erase all drawn curves by moving, left-clicking or changing the parameters of the plot
- It is possible to change the width of the curve
- The tracing algorithm automatically picks a suitable $dx$ step size, but you can set it manually if you uncheck 'Auto trace dx'. Smaller $dx$ means better chance of detecting singularities but longer generation time

![trace](images/trace_curve.svg)

### Drawing a tangent line at cursor position

- To draw a tangent line at the cursor's position, toggle 'Mouse line' on. It is off by default
- You can change the width and length of this line

![mouse line example](images/mouse_line.gif)

### Changing graph parameters

- The number of arrows drawn can by changed either by entering a number or by clicking the `+` and `-` buttons which change the value by 5
- It is also possible to change the width and the length of the arrows

![showcase](images/overall_showcase.gif)

### Exporting the figure

- The figure can be exported as a `.png` or `.svg` file by clicking the 'Save image' button or by pressing 'Ctrl+S'

### Changing the limits of the coordinate axes

- By default 'Equal axes' is toggled, but you can untoggle it to change the limits independently
- You can't change limits manually while 'Equal axes' is toggled

## Keybindings

- Alt+left = decrease arrows by 5
- Alt+right = increase arrows by 5
- Alt+t = change focus to 'Trace line width' slider
- Alt+a = cycle focus between 'Arrow length' and 'Arrow width' sliders
- Alt+m = cycle focus between 'Mouse line length' and 'Mouse line width' sliders
- Ctrl+m = toggle 'Mouse line' on and off
- Enter = graph the direction field
- Ctrl+s = save the figure
