all: direction_field_visualizer.exe

clean:
	rm -rf build direction_field_visualizer.exe direction_field_visualizer.spec

direction_field_visualizer.exe: main.py src/gui src/threading src/tracing src/icon.ico
	pyinstaller -F -w --icon=src/icon.ico --add-data="src/icon.ico:src" --distpath . --name "direction_field_visualizer" --hidden-import "matplotlib.backends.backend_svg" --hidden-import "matplotlib.backends.backend_pdf"  main.py
	rm -rf build direction_field_visualizer.spec