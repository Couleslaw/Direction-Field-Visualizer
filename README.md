# Direction Field Visualizer

This visualizer allows you to plot the direction field of a given differential equation. You can zoom in and out, move around and watch the direction field change in real time as well as tracing individual solution curves. The arrows can also be colored according to the curvature of the solutions, which can result in some truly spectacular images, see [gallery](https://github.com/Couleslaw/Direction-Field-Visualizer/wiki/gallery).

## What is a direction field?

A direction field is a graphical representation of the solutions to a first-order ordinary differential equation of the form

$$\frac{dy}{dx} = f(x,y).$$

The principle of the direction field is to draw small line segments for each point $(x,y)$ in the plane. The slope of the line segment is given by the derivative, that is $f(x,y)$. The direction field can be used to visualize the behavior of solutions to the differential equation because these line segments are tangent to the solution curves.

Let's see an example. Consider the differential equation $y'(x)=-x/y$. The direction field looks like this:

![circle](assets/circle.svg)

The tangent lines clearly form circles around the origin. The red semi-circles are two of the infinitely many solutions to the differential equation. We can guess that the general solution is of the form $y(x)=\pm\sqrt{A-x^2}$ which is indeed the case.

## Installation

### Windows

Windows users can download an executable file from the [releases page](https://github.com/Couleslaw/Direction-Field-Visualizer/releases/latest).

### Linux and macOS

This project is not compatible with the newer versions of matplotlib. It works with version 3.6.2. I recommend creating a virtual environment and installing the dependencies from the `requirements.txt` file.

Clone the repository:

```bash
git clone https://github.com/Couleslaw/Direction-Field-Visualizer.git
cd Direction-Field-Visualizer
```

Create and activate the virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate    # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Run the program with `python3 main.py`. The virtual environment can be deactivated by running `deactivate`.

## Usage

The program is very intuitive to use. You can enter a differential equation in the input field and press the `Graph` button. The program will then plot the direction field of the differential equation. You can zoom in and out with the mouse wheel, move around by dragging the plot and trace individual solution curves by right-clicking on the plot.

Many parameters can be adjusted in the right-hand side panel including the number, width length and color scheme of the arrows. I encuorage you to play around with these settings to see what you can come up with.

For a more detailed explanation of the program, see the [wiki](https://github.com/Couleslaw/Direction-Field-Visualizer/wiki).
