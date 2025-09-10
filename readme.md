# StiCAN configurator 

## Dependencies

- Python 3.13.2

venv creation example
```sh
python3.13 -m venv ~/.venvs/qtcreator_Python_3_13_2venv
source ~/.venvs/qtcreator_Python_3_13_2venv/bin/activate    
pip install --upgrade pip
```
`~` is `/home/$USER` 

```sh
pip install pyserial
pip install pyside6
pip install bleak
pip install qasync
pip install pyinstaller
```

## Translation

Install:
```sh
sudo apt install pyqt6-dev-tools qt6-tools-dev qt6-tools-dev-tools
```

Extract:
```sh
pylupdate6 form.ui -ts form_pl.ts
pylupdate6 form.ui -ts form_en.ts
```

Compile into .qm:
```sh
/usr/lib/qt6/bin/lrelease ./form_en.ts
/usr/lib/qt6/bin/lrelease ./form_pl.ts
```

## Build

### Ubuntu
```sh
pyinstaller --onefile --windowed --icon=icon.ico --hidden-import PySide6.QtCore --hidden-import PySide6.QtGui --hidden-import PySide6.QtWidgets --add-data "loading-snake-io.gif:." --add-data "form_pl.qm:." --add-data "form_en.qm:." mainwindow.py
```

### Windows

1. Instal MSVC compiler (VS Community + C++ Desktop Package): https://visualstudio.microsoft.com/pl/vs/community/
2. Run venv with installed dependencies
3. Run command below (for Windows run CMD with Admin rights)

Additional dependencies:
```sh
pip install winrt-runtime
pip install winrt-Windows.Devices.Bluetooth
pip install winrt-Windows.Devices.Bluetooth.Advertisement
pip install winrt-Windows.Devices.Bluetooth.GenericAttributeProfile
pip install winrt-Windows.Devices.Enumeration
pip install winrt-Windows.Foundation
pip install winrt-Windows.Foundation.Collections
pip install winrt-Windows.Storage.Streams
```

```sh
pyinstaller --onefile --windowed --icon=icon.ico    --hidden-import PySide6.QtCore    --hidden-import PySide6.QtGui     --hidden-import PySide6.QtWidgets --hidden-import winrt.windows.foundation --hidden-import winrt.windows.foundation.collections         --add-data "loading-snake-io.gif:."    --add-data "form_pl.qm:."     --add-data "form_en.qm:."     --add-data "slabvcp.inf:."     --add-data "slabvcp.cat:."      --add-data "dpinst.xml:."      --add-data "CP210xVCPInstaller_x64.exe:."     --add-data "silabser.sys:."     --add-data "WdfCoInstaller01009.dll:." --add-data "WdfCoInstaller01011.dll:." --add-data "SLAB_License_Agreement_VCP_Windows.txt:."      mainwindow.py
```
