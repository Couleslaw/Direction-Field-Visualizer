all: direction_field_visualizer.exe

clean:
	rm -rf dist build main.spec direction_field_visualizer.exe

direction_field_visualizer.exe: main.py src/canvas.py src/default_constants.py src/direction_field_builder.py icon.ico
	pyinstaller -w --onefile --clean -y --icon=icon.ico --add-data="icon.ico;." main.py;
	mv dist/main.exe direction_field_visualizer.exe;
	rm -rf dist build main.spec;
