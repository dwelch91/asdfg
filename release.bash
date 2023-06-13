rm -rf build
rm -rf dist
pip install --upgrade pip
pip3 install pyinstaller
pip3 install --upgrade PyInstaller pyinstaller-hooks-contrib
pip3 install -r requirements.txt --force-reinstall
pyinstaller --name="asdfg" --windowed --exclude-module _bootlocale --onefile main.py --noupx
cp dist/asdfg ~/.local/bin/asdfg
chmod a+x ~/.local/bin/asdfg
