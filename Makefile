all: direction-field-visualizer.exe

clean:
    rm -rf dist build main.spec direction-field-visualizer.exe

direction-field-visualizer.exe: main.py
    pyinstaller -w --onefile --clean -y --icon=assets/icon.ico --add-data="assets\icon.ico;assets" main.py
	mv dist/main.exe direction-field-visualizer.exe
	rm -rf dist build main.spec
