all: direction_field_visualizer.exe

clean:
	rm -rf build direction_field_visualizer.exe direction_field_visualizer.spec

direction_field_visualizer.exe: main.py src/gui src/threading src/tracing src/direction_field src/icon.ico assets/graphics
	pyinstaller -w -F --icon=src/icon.ico --add-data="src/icon.ico:src" --add-data="assets/graphics/lock_closed.png:assets/graphics" --add-data="assets/graphics/lock_open.png:assets/graphics" --add-data="assets/graphics/stop_red.png:assets/graphics" --distpath . --name "direction_field_visualizer" --hidden-import "matplotlib.backends.backend_svg" --hidden-import "matplotlib.backends.backend_pdf"  main.py
	rm -rf build direction_field_visualizer.spec