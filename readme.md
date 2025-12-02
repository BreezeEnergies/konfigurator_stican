# StiCAN configurator 

## Dependencies

- Python 3.13

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

Python 3.13

auto
```sh
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13-dev python3.13-full python3.13-examples
```

venv creation example (Ubuntu)
```sh
python3.13 -m venv ~/.venvs/qtcreator_Python_3_13_2venv
source ~/.venvs/qtcreator_Python_3_13_2venv/bin/activate    
pip install --upgrade pip
```

`~` is `/home/$USER` in Ubuntu

```sh
pyinstaller .\mainwindow.spec
```

### Windows

0. Install Python 3.13 from MS Store
1. Instal MSVC compiler (VS Community + C++ Desktop Package): https://visualstudio.microsoft.com/pl/vs/community/ 
2. Run venv with installed dependencies

```sh
# start CMD
cd <this project directory>

python3.13 -m venv qtcreator_Python_3_13_2venv
qtcreator_Python_3_13_2venv\Scripts\activate

# could give error with cmd with path and command to update
pip install --upgrade pip
```

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
pyinstaller .\mainwindow_windows.spec
```