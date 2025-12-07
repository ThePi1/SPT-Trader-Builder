# SPT Quest Builder

A tool for building EFT SPT Quests.

## Usage
    pip install -r requirements.txt
    cd src
    python .\trader_builder.py

## GUI
The GUI is currently created using PyQt6 and laid out using the Qt Designer tool.

You can get this by `pip install pyqt6-tools` and then launch by `pyqt6-tools designer`.

`.\tools\update_gui_py.ps1` is ran from the `src` folder to compile the `.ui` files into their `.py` counterparts.
If you're not developing on Windows feel free to skip this (or make an analogue to it), and just run the commands yourself in that file as needed.

## Packaging binary
Packaged with Python 3.11.6.

Run the packaging tool from the src/ folder as follows:

    python .\tools\pack.py


Alternatively, manually, you can pack as follows:

    pip install pyinstaller
    pyinstaller .\trader_builder.py --onefile --icon=data/icon.ico --hide-console=hide-early
    > Go into dist/ folder and grab trader_builder.exe
    > Copy trader_builder.exe, LICENSE, and data/ folder to new folder.
    > Zip up and release

I don't have it packaged for Linux/Mac on hand, but if you want to, you can.

