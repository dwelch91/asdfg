sudo apt-get -y install upx-ucl
pip3 install pyinstaller
pip3 install --upgrade PyInstaller pyinstaller-hooks-contrib
pyinstaller --name="asdfg" --windowed --exclude-module _bootlocale --onefile main.py
cp dist/asdfg ~/.local/bin/asdfg
chmod a+x ~/.local/bin/asdfg
