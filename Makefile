all: direction_field_visualizer.exe

clean:
	rm -rf dist build main.spec direction_field_visualizer.exe

direction_field_visualizer.exe: main.py lib/canvas.py lib/default_constants.py lib/direction_field_builder.py icon.ico
	pyinstaller -w --onefile --clean -y --icon=icon.ico --add-data="icon.ico;." main.py;
	mv dist/main.exe direction_field_visualizer.exe;
	rm -rf dist build main.spec;
