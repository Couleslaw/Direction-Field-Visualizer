# Direction Field Visualizer

This visualizer allows you to plot the direction field of a given differential equation. You can zoom in and out, move around and watch the direction field change in real time as well as trace individual solution curves. The arrows can also be colored according to the curvature of the solutions, which can result in some truly spectacular images, see the [gallery](https://github.com/Couleslaw/Direction-Field-Visualizer/wiki/gallery).

## What is a direction field?

A direction field is a graphical representation of the solutions to a first-order ordinary differential equation of the form

$$\frac{dy}{dx} = f(x,y).$$

The principle of the direction field is to draw small line segments for each point $(x,y)$ in the plane. The slope of the line segment is given by the derivative, that is $f(x,y)$. The direction field can be used to visualize the behavior of solutions to the differential equation because these line segments are tangent to the solution curves.

Let's see an example. Consider the differential equation $y'(x)=-x/y$. The direction field looks like this:

![circle](https://github.com/Couleslaw/Direction-Field-Visualizer/wiki/images/docs/circle_with_ui.png)

The tangent lines clearly form circles around the origin. The red semi-circles are two of the infinitely many solutions to the differential equation. We can guess that the general solution is of the form $y(x)=\pm\sqrt{A-x^2}$ which is indeed the case.

## Installation

<details><summary><b>Windows</b></summary>

Windows users can simply download an executable file from the [releases page](https://github.com/Couleslaw/Direction-Field-Visualizer/releases/latest).

</details>

<details><summary><b>Linux and macOS (and Windows)</b></summary>

Ensure that you have [python](https://www.python.org/) and [git](https://git-scm.com/) installed on your system.

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

The next time you want to run the program, you only need to activate the virtual environment with `source venv/bin/activate` and run `python3 main.py`.

<details><summary><b>Building using pyinstaller</b></summary>

If you don't want to activate the virtual environment every time you want to run the program, you can use [pyinstaller](https://pyinstaller.org/en/stable/usage.html) to create an executable file. Ensure that the virtual environment is **activated** and run `pip install pyinstaller`. If you have [make](https://www.gnu.org/software/make/) installed, you can simply run `make` to build the executable. Otherwise, run the following commands:

```bash
pyinstaller -w -F --icon=src/icon.ico --add-data="src/icon.ico:src" --add-data="assets/graphics/lock_closed.png:assets/graphics" --add-data="assets/graphics/lock_open.png:assets/graphics" --add-data="assets/graphics/stop_red.png:assets/graphics" --distpath . --name "direction_field_visualizer" --hidden-import "matplotlib.backends.backend_svg" --hidden-import "matplotlib.backends.backend_pdf"  main.py
rm -rf build direction_field_visualizer.spec
```

This will create an executable file named `direction_field_visualizer`.

</details>
</details>

## Usage

The program is very intuitive to use. You can enter a differential equation in the input field and press the `Graph` button. The program will then plot the direction field of the differential equation. You can zoom in and out with the mouse wheel, move around by dragging the plot and trace individual solution curves by right-clicking on the plot.

Many parameters can be adjusted in the right-hand side panel including the number, width, length and color scheme of the arrows. I encourage you to play around with these settings to see what you can come up with.

For a more detailed explanation of the program and an image gallery, see the [wiki](https://github.com/Couleslaw/Direction-Field-Visualizer/wiki).

![art](https://github.com/Couleslaw/Direction-Field-Visualizer/wiki/images/png-border/inferno_sin.png)
