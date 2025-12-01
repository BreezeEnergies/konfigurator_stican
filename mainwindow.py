from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
    QLabel,
    QVBoxLayout,
    QMessageBox,
    QDialog,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QScrollArea,
)
from PySide6.QtCore import (
    QTimer,
    QObject,
    QThread,
    Signal,
    Slot,
    QMetaObject,
    Qt,
    QTranslator,
    QLocale,
    QLibraryInfo,
    QCoreApplication,
    QSysInfo,
)
from PySide6.QtGui import QMovie, QValidator

from datetime import datetime
from ui_form import Ui_MainWindow

import os
import sys
import queue
import asyncio
import time
import serial
import serial.tools.list_ports

from bleak import BleakScanner

# Import worker classes and utilities
from src.command_worker import CommandWorker
from src.configure_worker import ConfigureWorker
from src.loading_animation import LoadingAnimation

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

ANIMATION_FILES = [resource_path("loading-snake-io.gif")]

APPLICATION_VERSION = "1.2.5"
APPLICATION_AUTHORS = ["Maciej Hejlasz <DeimosMH>", ""]
APPLICATION_OWNERS = "Breeze Energies Sp. z o.o."

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.SYSTEM = ""
        # Initialize translators
        self.translator = QTranslator(self)

        # Miscleanous for translation
        self.current_language = "pl"  # Default language
        self.step_keys = []

        # Connect language buttons
        self.ui.EN_Button.clicked.connect(lambda: self.change_language("en"))
        self.ui.PL_Button.clicked.connect(lambda: self.change_language("pl"))

        # Load default language
        self.change_language(self.current_language)

        # Initialize the timer for automatic detection
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.detect_stican)
        self.timer.start(500)  # Check every 0.5 seconds

        # Connect buttons to functions
        self.ui.configureSticanButton.clicked.connect(self.configure_stican)
        self.ui.addBatteryButton.clicked.connect(self.add_battery_row)
        self.ui.advSaveLog.clicked.connect(self.save_log)
        self.ui.advSendCommand.clicked.connect(self.send_command)
        self.ui.scanDevicesButton.clicked.connect(self.scan_for_devices)
        # self.ui.scanDevicesButton.clicked.connect(lambda: self.scan_for_devices())

        # Initialize list to store battery row data
        self.battery_rows = []

        # Add 4 battery fields at the start
        self.add_battery_row(is_first_row=True)  # First row with placeholders
        # for _ in range(3):  # Remaining rows
        #     self.add_battery_row()

        # Initialize User Configure Validation indicators
        self.init_user_configure_validation()

        # Check if initialization was successful
        if not self.validation_steps:
            print(
                "Error: init_user_configure_validation failed to populate self.validation_steps"
            )

        # Adjust the window size to fit the contents
        self.adjustSize()

        ### Info tab
        self.ui.versionValueLabel.setText(f"{APPLICATION_VERSION}")
        self.ui.authorsValueLabel.setText(f"{', '.join(APPLICATION_AUTHORS)}")
        self.ui.licenseValueLabel.setText("GPL v3")
        self.ui.companyValueLabel.setText(f"{APPLICATION_OWNERS}")

        self.loading_animation = LoadingAnimation()
        self.all_animations_stopped = True

        # Initialize detection status flag
        self.stican_detected = False
        self.stican_detected_stop_sig = (
            False  # Send signal at the connection only once - for StiCAN > V3.0
        )

        self.detect_system()
        self.print_system_params()

    def show_devices_not_found(self, not_found_devices):
        not_found_message = (
            QCoreApplication.translate("MainWindow", "Devices not found")
            + ":\n"
            + "\n".join(not_found_devices)
        )
        QMessageBox.warning(self, "Devices Not Found", not_found_message)

    def handle_prompt_message(self, message):
        QMessageBox.information(self, "Action Required", message, QMessageBox.Ok)

    def scan_for_devices(self):
        self.ui.scanDevicesButton.setEnabled(False)

        # Create a dialog to display the results
        dialog = QDialog(self)
        dialog.setWindowTitle("Bluetooth Devices")
        dialog.setMinimumSize(680, 600)  # Set minimum size to 300x600

        # Create a QTableWidget to display the results
        table_widget = QTableWidget(dialog)
        table_widget.setColumnCount(3)
        table_widget.setHorizontalHeaderLabels(["Name", "Address", "Signal"])
        table_widget.setColumnWidth(0, 300)  # Set Name column width to 300px
        table_widget.setColumnWidth(1, 200)  # Set Address column width to 200px
        table_widget.setColumnWidth(2, 100)  # Set Signal column width to 100px

        # Create a layout and add the QTableWidget
        layout = QVBoxLayout(dialog)
        layout.addWidget(table_widget)

        # Add a close button
        close_button = QPushButton("Close", dialog)
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        # Show the dialog
        dialog.show()

        # List to store devices and a set to track seen addresses
        devices_list = []
        seen_addresses = set()

        # Callback function to handle discovered devices
        def detection_callback(device, advertisement_data):
            # Check if the device has a name, is not a duplicate, and starts with the desired prefixes
            if (
                device.name
                and device.address not in seen_addresses
                and device.name.startswith(("BR", "LC", "NB", "AP"))
            ):
                # Add device to the list with its RSSI
                devices_list.append((device, advertisement_data.rssi))
                seen_addresses.add(device.address)
                # Sort devices by RSSI (from lowest to highest)
                devices_list.sort(key=lambda x: x[1], reverse=True)

                # Update the QTableWidget with the results
                table_widget.setRowCount(len(devices_list))
                for row, (d, rssi) in enumerate(devices_list):
                    table_widget.setItem(row, 0, QTableWidgetItem(d.name))
                    table_widget.setItem(row, 1, QTableWidgetItem(d.address))
                    table_widget.setItem(row, 2, QTableWidgetItem(f"{rssi} dBm"))

        # Create a BleakScanner with the callback
        scanner = BleakScanner(detection_callback)

        if "win" == self.SYSTEM:
            import threading

            # Function to run the scanner in a separate thread
            def run_scanner():
                async def scanner_task():
                    self.log("Scanning for Bluetooth devices...")
                    await scanner.start()
                    await asyncio.sleep(5)  # Scan for 5 seconds
                    await scanner.stop()
                    self.log("Bluetooth scan completed.")

                # Run the event loop in a new thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(scanner_task())

            # Start the scanner in a new thread
            scanner_thread = threading.Thread(target=run_scanner)
            scanner_thread.start()

            # Execute the dialog to block until closed
            dialog.exec()

            # Wait for the scanner thread to finish
            scanner_thread.join()

        if "lin" == self.SYSTEM:
            # Run the scanner
            async def run_scanner():
                self.log("Scanning for Bluetooth devices...")
                await scanner.start()
                await asyncio.sleep(3)  # Scan for 3 seconds
                await scanner.stop()
                self.log("Bluetooth scan completed.")

            # Run the asynchronous function
            asyncio.run(run_scanner())

            # Execute the dialog to block until closed
            dialog.exec()

        self.ui.scanDevicesButton.setEnabled(True)

    def detect_system(self):
        os_name = QSysInfo.productType()
        if "win" in os_name.lower():
            self.log("Windows is detected.")
            self.SYSTEM = "win"
            
            ## some drivers installed automatically from windows have the same signature and dont work!
            # if not self.check_driver_in_driverstore() or not self.check_driver_loaded():
            translated_status = QCoreApplication.translate(
                "MainWindow",
                "Do you want to install drivers to connect with StiCAN?")

            reply = QMessageBox.question(
                self,
                "Drivers",
                translated_status,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes)          # default button

            if reply == QMessageBox.Yes:
                self.install_driver()
        elif "linux" in os_name.lower():
            self.log("Linux is detected.")
            self.SYSTEM = "lin"
        else:
            self.log(f"Detected OS: {os_name}")
            self.SYSTEM = "lin"

    def install_driver(self):
        import subprocess
        import ctypes
        import tempfile
        import shutil

        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            self.log(f"Temporary directory created at: {temp_dir}")

            # Create the "x64" subdirectory within the temporary directory
            x64_dir = os.path.join(temp_dir, "x64")
            os.makedirs(x64_dir, exist_ok=True)
            self.log(f"x64 directory created at: {x64_dir}")

            # Extract the bundled files to the appropriate directories
            files_to_extract = [
                "slabvcp.inf",
                "slabvcp.cat",
                "dpinst.xml",
                "silabser.sys",
                "WdfCoInstaller01009.dll",
                "WdfCoInstaller01011.dll",
                "SLAB_License_Agreement_VCP_Windows.txt",
                "CP210xVCPInstaller_x64.exe",
            ]

            for file in files_to_extract:
                bundled_file = resource_path(file)
                if file in [
                    "silabser.sys",
                    "WdfCoInstaller01009.dll",
                    "WdfCoInstaller01011.dll",
                ]:
                    extracted_file = os.path.join(x64_dir, file)
                else:
                    extracted_file = os.path.join(temp_dir, file)
                shutil.copy(bundled_file, extracted_file)
                self.log(f"Copied {file} to {extracted_file}")

            # Print all files in temp_dir
            self.log("Files in temp_dir:")
            for root, dirs, files in os.walk(temp_dir):
                for name in files:
                    self.log(os.path.join(root, name))

            exe_path = os.path.join(temp_dir, "CP210xVCPInstaller_x64.exe")

            self.log(f"temp_dir: {temp_dir} ")

            self.log(f"exe_path: {exe_path} ")

            # ##### -> WORKS
            # # process = None
            # try:
            #     # # Run the executable
            #     # subprocess.run(exe_path)
            #     # subprocess.Popen(
            #     #                 [exe_path],
            #     #                 cwd=temp_dir,
            #     #                 # shell=True
            #     #             )
            #     result = ctypes.windll.shell32.ShellExecuteW(
            #         None, "runas", exe_path, None, None, 1
            #     )

            #     if result <= 32:
            #         raise Exception(f"Failed to execute installer, error code: {result}")

            #     self.log("driver CP210xVCPInstaller_x64 ran successfully.")
            # except subprocess.CalledProcessError as e:
            #     self.log(f"An error occurred while running driver CP210xVCPInstaller_x64.exe: {e}")
            # except FileNotFoundError:
            #     self.log("driver CP210xVCPInstaller_x64 not found. Please ensure it is in the correct directory.")

            ######### DIFF

            try:
                # Get the path to the executable
                # exe_path = os.path.join(temp_dir, 'CP210xVCPInstaller_x64.exe')

                # self.log(f"exe_path: {exe_path}")

                # Define structures needed for ShellExecuteEx
                class SHELLEXECUTEINFO(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", ctypes.c_ulong),
                        ("fMask", ctypes.c_ulong),
                        ("hwnd", ctypes.c_void_p),
                        ("lpVerb", ctypes.c_char_p),
                        ("lpFile", ctypes.c_char_p),
                        ("lpParameters", ctypes.c_char_p),
                        ("lpDirectory", ctypes.c_char_p),
                        ("nShow", ctypes.c_int),
                        ("hInstApp", ctypes.POINTER(ctypes.c_void_p)),
                        ("lpIDList", ctypes.POINTER(ctypes.c_void_p)),
                        ("lpClass", ctypes.c_char_p),
                        ("hkeyClass", ctypes.c_void_p),
                        ("dwHotKey", ctypes.c_ulong),
                        ("hIcon", ctypes.c_void_p),
                        ("hProcess", ctypes.c_void_p),
                    ]

                # Create an instance of SHELLEXECUTEINFO
                sei = SHELLEXECUTEINFO()
                sei.cbSize = ctypes.sizeof(sei)
                sei.fMask = 0x00000040  # SEE_MASK_NOCLOSEPROCESS
                sei.lpVerb = b"runas"
                sei.lpFile = exe_path.encode("utf-8")
                sei.nShow = 1

                # Execute the installer with elevated privileges
                ctypes.windll.shell32.ShellExecuteEx(ctypes.byref(sei))

                if sei.hProcess:
                    # Wait for the process to finish
                    ctypes.windll.kernel32.WaitForSingleObject(sei.hProcess, -1)
                    # Close the handle
                    ctypes.windll.kernel32.CloseHandle(sei.hProcess)

                self.log("driver CP210xVCPInstaller_x64 ran successfully.")
            except Exception as e:
                self.log(
                    f"An error occurred while running driver CP210xVCPInstaller_x64.exe: {e}"
                )

            # Clean up the temporary directory
            shutil.rmtree(temp_dir)
            self.log("Temporary directory cleaned up.\n")
            return True

        except Exception as e:
            self.log(f"An error occurred while installing the driver: {e}")
            return False

    def print_system_params(self):
        self.log(f"Product Type: {QSysInfo.productType()}")
        self.log(f"Product Version: {QSysInfo.productVersion()}")
        self.log(f"Kernel Type: {QSysInfo.kernelType()}")
        self.log(f"Kernel Version: {QSysInfo.kernelVersion()}")
        self.log(f"Machine Host Name: {QSysInfo.machineHostName()}")
        self.log(f"Current CPU Architecture: {QSysInfo.currentCpuArchitecture()}")
        self.log(f"Build CPU Architecture: {QSysInfo.buildCpuArchitecture()}")
        self.log(f"Build ABI: {QSysInfo.buildAbi()}")

        # Additional information available on some systems
        pretty_product_name = QSysInfo.prettyProductName()
        if pretty_product_name:
            self.log(f"System Product Name: {pretty_product_name}")

    def check_driver_in_driverstore(self):
        driverstore_path = r"C:\Windows\System32\DriverStore\FileRepository"
        for root, dirs, files in os.walk(driverstore_path):
            for file in files:
                if file.lower() == "slabvcp.inf":
                    self.log("CP210x driver exist.")
                    return True

        self.log("CP210x driver not exist on this system.")
        return False

    def check_driver_loaded(self):
        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\silabser"
            ) as key:
                self.log("CP210x driver is loaded.")
                return True
        except WindowsError:
            self.log("CP210x driver is not loaded.")
            return False
        return False

    def show_success_message(self):
        QMessageBox.information(
            self,
            "Success",
            QCoreApplication.translate("MainWindow", "Configuration Successful"),
        )

    def log(self, message):
        # Append the log message to the advConfigureOutputText widget
        self.ui.advConfigureOutputText.append(message)

    def change_language(self, language_code):
        if language_code == "pl":
            self.translator.load(resource_path("form_pl.qm"))
        else:
            self.translator.load(resource_path("form_en.qm"))

        QApplication.instance().installTranslator(self.translator)
        self.ui.retranslateUi(self)
        self.current_language = language_code

        self.update_step_translations()

    def init_user_configure_validation(self):
        # Steps of configuration
        self.step_keys = [
            "Connection Status",
            "Validate data to write",
            "Prepare for configuration",
            "Upload data",
            "Verify device data",
            "Scan and detect devices",
        ]
        self.validation_steps = []
        layout = QVBoxLayout()

        # Check if the GIF file exists
        gif_path = ANIMATION_FILES[0]
        if not os.path.exists(gif_path):
            print(f"Warning: {gif_path} does not exist in the current directory.")
            gif_path = os.path.join(os.path.dirname(__file__), ANIMATION_FILES[0])
            if not os.path.exists(gif_path):
                print(f"Error: {gif_path} does not exist. Using default path.")
                gif_path = ANIMATION_FILES[0]

        for i, step_key in enumerate(self.step_keys):
            # Create a horizontal layout for each step
            h_layout = QHBoxLayout()
            # Create an indicator (QLabel with background color)
            indicator = QLabel()
            indicator.setFixedSize(20, 20)
            indicator.setStyleSheet(
                "background-color: gray; border-radius: 10px; border: 1px solid black;"
            )
            # Create a label for the step
            step_label = QLabel(
                f"{QCoreApplication.translate('MainWindow', step_key)}: NA"
            )

            # Add widgets to the row layout
            h_layout.addWidget(indicator)
            h_layout.addWidget(step_label)

            if i > 0:  # Exclude animation for "Connection Status"
                # Create a label for the animation
                animation_label = QLabel()
                animation_label.setFixedSize(20, 20)
                # Create a QMovie object for the animation
                movie = QMovie(gif_path)
                if not movie.isValid():
                    print(f"Error: Failed to load {gif_path}. Using empty movie.")
                    movie = QMovie()
                movie.setScaledSize(animation_label.size())
                h_layout.addWidget(animation_label)  # Add animation to the right side
            else:
                animation_label = None
                movie = None

            # Add to the main layout
            layout.addLayout(h_layout)

            # Store references for later updates
            self.validation_steps.append(
                {
                    "indicator": indicator,
                    "label": step_label,
                    "animation_label": animation_label,
                    "movie": movie,
                }
            )

        # Set the layout to UserConfigureValidation
        self.ui.UserConfigureValidation.setLayout(layout)

        if not self.validation_steps:
            print("Error: self.validation_steps is empty after initialization.")

    def update_step_translations(self):
        for i, step_key in enumerate(self.step_keys):
            translated_step_name = QCoreApplication.translate("MainWindow", step_key)
            self.validation_steps[i]["label"].setText(f"{translated_step_name}: NA")

    def update_validation_step(self, step_index, status):
        print(f"Updating validation step {step_index} with status: {status}")
        step = self.validation_steps[step_index]
        step_name = step["label"].text().split(":")[0]

        if status == "PASS":
            translated_status = QCoreApplication.translate("MainWindow", "PASS")
            step["indicator"].setStyleSheet(
                "background-color: green; border-radius: 10px; border: 1px solid black;"
            )
            if step["movie"] and not self.all_animations_stopped:
                step["movie"].stop()
                step["animation_label"].setMovie(None)
        elif status == "FAIL":
            translated_status = QCoreApplication.translate("MainWindow", "FAIL")
            step["indicator"].setStyleSheet(
                "background-color: red; border-radius: 10px; border: 1px solid black;"
            )
            if step["movie"] and not self.all_animations_stopped:
                step["movie"].stop()
                step["animation_label"].setMovie(None)
        else:  # status == "NA"
            translated_status = QCoreApplication.translate("MainWindow", "NA")
            step["indicator"].setStyleSheet(
                "background-color: gray; border-radius: 10px; border: 1px solid black;"
            )
            if step["movie"] and not self.all_animations_stopped:
                step["animation_label"].setMovie(step["movie"])
                step["movie"].start()

        # self.log(f"update_validation_step: {step_name}: {translated_status}")
        translated_step_name = QCoreApplication.translate("MainWindow", step_name)
        step["label"].setText(f"{translated_step_name}: {translated_status}")

    def update_progress(self, step_index, status):
        # Update the indicator color and label text for step
        if 0 <= step_index < len(self.validation_steps):
            step = self.validation_steps[step_index]
            if status == "PASS":
                color = "green"
                translated_status = QCoreApplication.translate("MainWindow", "PASS")
            elif status == "FAIL":
                color = "red"
                translated_status = QCoreApplication.translate("MainWindow", "FAIL")
            else:
                color = "gray"
                translated_status = QCoreApplication.translate("MainWindow", "NA")
            step["indicator"].setStyleSheet(
                f"background-color: {color}; border-radius: 10px; border: 1px solid black;"
            )
            step_name = step["label"].text().split(":")[0]
            translated_step_name = QCoreApplication.translate("MainWindow", step_name)

            # self.log(f"update_progress: {step_name}: {translated_status}")
            step["label"].setText(f"{translated_step_name}: {translated_status}")

    def update_connection_status(self, connected):
        if not self.validation_steps:
            print(
                "Warning: self.validation_steps is empty. Cannot update connection status."
            )
            return

        # Update the first validation step (index 0)
        step_index = 0
        if connected:
            color = "green"
            # text = "Connected"
            translated_status = QCoreApplication.translate("MainWindow", "Connected")
        else:
            color = "red"
            # text = "Disconnected"
            translated_status = QCoreApplication.translate("MainWindow", "Disconnected")

        if step_index < len(self.validation_steps):
            step = self.validation_steps[step_index]
            step["indicator"].setStyleSheet(
                f"background-color: {color}; border-radius: 10px; border: 1px solid black;"
            )
            # step_name = "Connection Status"
            translated_step_name = QCoreApplication.translate(
                "MainWindow", "Connection Status"
            )

            step["label"].setText(f"{translated_step_name}: {translated_status}")
        else:
            print(
                f"Warning: step_index {step_index} is out of range for self.validation_steps"
            )

    def log_message(self, message):
        self.ui.advConfigureOutputText.append(message)

    def detect_stican(self):
        ports = list(serial.tools.list_ports.comports())

        # Detect StiCAN device using VID and PID
        stican_port = next(
            (p.device for p in ports if p.vid == 0x10C4 and p.pid == 0xEA60), None
        )

        if stican_port:
            self.stican_detected = True
            self.ui.detectionStatusLabel.setText(
                QCoreApplication.translate("MainWindow", "StiCAN Status: Detected")
            )
            self.ui.detectedPortLabel.setText(
                QCoreApplication.translate("MainWindow", "Port: {0}").format(
                    stican_port
                )
            )
            self.ui.statusIndicatorLabel.setStyleSheet(
                """
                background-color: green;
                border-radius: 10px;
                border: 1px solid black;
            """
            )
            if self.validation_steps:
                self.update_connection_status(True)
            else:
                print(
                    "Warning: Cannot update connection status. self.validation_steps is empty."
                )

            # Re-enable buttons
            self.ui.configureSticanButton.setEnabled(True)
            self.ui.addBatteryButton.setEnabled(True)

            # Broken in Windows
            if self.stican_detected_stop_sig is False:
                if self.SYSTEM == "lin":
                    # Send once after connection
                    ports = list(serial.tools.list_ports.comports())
                    stican_port = next(
                        (p.device for p in ports if p.vid == 0x10C4 and p.pid == 0xEA60),
                        None,
                    )
                    conn = serial.Serial(stican_port, 115200, timeout=1)
                    conn.write(b"s")  # stop work mode for >= v3.0
                self.stican_detected_stop_sig = True

        else:
            self.stican_detected = False
            self.stican_detected_stop_sig = False
            self.ui.detectionStatusLabel.setText(
                QCoreApplication.translate("MainWindow", "StiCAN Status: Not Detected")
            )
            self.ui.detectedPortLabel.setText(
                QCoreApplication.translate("MainWindow", "Port: N/A")
            )
            self.ui.statusIndicatorLabel.setStyleSheet(
                """
                background-color: red;
                border-radius: 10px;
                border: 1px solid black;
            """
            )
            if self.validation_steps:
                self.update_connection_status(False)
            else:
                print(
                    "Warning: Cannot update connection status. self.validation_steps is empty."
                )
            # Close the serial connection if open
            if hasattr(self, "serial_connection") and self.serial_connection.is_open:
                self.serial_connection.close()

    def configure_stican(self):
        # Check if StiCAN is detected
        if not self.stican_detected:
            # Update indicator for Connection Status to FAIL
            self.update_connection_status(False)
            # Log message
            self.ui.advConfigureOutputText.append("Error: StiCAN was not detected.")
            self.show_error_popup("Error: StiCAN was not detected.")
            return

        # Disable Configure and Add Battery buttons
        self.ui.configureSticanButton.setEnabled(False)
        self.ui.addBatteryButton.setEnabled(False)

        # Disable input fields and remove buttons
        for row in self.battery_rows:
            if not row["is_first_row"]:
                row["serial_number_input"].setEnabled(False)
                row["pin_input"].setEnabled(False)
                row["remove_button"].setEnabled(False)

        # Reset indicators to gray
        for step in self.validation_steps[1:]:
            step["indicator"].setStyleSheet(
                "background-color: gray; border-radius: 10px; border: 1px solid black;"
            )
            step_name = step["label"].text().split(":")[0]
            step["label"].setText(f"{step_name}: NA")

        # Gather battery data from GUI
        battery_data = []
        for row in self.battery_rows:
            if row["is_first_row"]:
                continue  # Skip the first row

            serial_number = row["serial_number_input"].text().strip()
            pin = row["pin_input"].text().strip()
            if serial_number:
                data_line = f"{serial_number},{pin},"
                battery_data.append(data_line)
            else:
                # Handle missing serial number
                self.ui.advConfigureOutputText.append(
                    "Error: Missing serial number in one of the batteries."
                )
                return

        # Prepare devices list
        devices = []
        # First line is the number of devices, formatted as two-digit number
        devices.append("{0:02d}".format(len(battery_data)))
        # Then add the battery data lines
        devices.extend(battery_data)

        # # Get port
        port = self.ui.detectedPortLabel.text().replace("Port: ", "")
        self.start_configuration(devices, port)

    def configuration_finished(self):
        # Re-enable buttons
        self.ui.configureSticanButton.setEnabled(True)
        self.ui.addBatteryButton.setEnabled(True)

        # Re-enable input fields and remove buttons
        for row in self.battery_rows:
            if not row["is_first_row"]:
                row["serial_number_input"].setEnabled(True)
                row["pin_input"].setEnabled(True)
                row["remove_button"].setEnabled(True)

        self.ui.advConfigureOutputText.append("Configuration process completed.")

        try:
            self.worker.request_choice.disconnect()
        except RuntimeError:
            pass

        # Restart the timer to reactivate detect_stican
        self.timer.start(500)  # Check every 0.5 seconds

    def start_configuration(self, devices, port):
        # Stop the timer to deactivate detect_stican
        self.timer.stop()

        # Create worker thread
        self.thread = QThread()
        self.worker = ConfigureWorker(devices, port)

        self.worker.moveToThread(self.thread)

        self.worker.request_choice.connect(
            self._show_choice_dialog, Qt.BlockingQueuedConnection
        )

        # Connect signals and slots
        self.worker.prompt_message.connect(self.handle_prompt_message)
        self.worker.devices_not_found.connect(self.show_devices_not_found)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.update_validation_step)
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.log_message)
        self.worker.error.connect(self.show_error_popup)
        self.worker.started.connect(self.start_all_animations)
        self.thread.finished.connect(self.stop_all_animations)
        self.thread.finished.connect(self.configuration_finished)

        # Connect the success signal to the show_success_message slot
        self.worker.success.connect(self.show_success_message)

        # Start the thread
        self.thread.start()

    # ------------------------------------------------------------------
    @Slot(str, list)
    def _show_choice_dialog(self, question, choices):
        """Called in the **main** thread.  Returns the chosen text."""
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Configuration")
        dlg.setText(question)
        dlg.setIcon(QMessageBox.Question)

        # Add the two buttons
        btn1 = dlg.addButton(choices[0], QMessageBox.AcceptRole)
        btn2 = dlg.addButton(choices[1], QMessageBox.AcceptRole)
        dlg.setDefaultButton(btn1)

        dlg.exec()  # modal, blocks until user clicks

        clicked_text = dlg.clickedButton().text()
        self.worker._choice_queue.put(clicked_text)  # send back to worker

    def show_error_popup(self, message):
        QMessageBox.critical(
            self,
            QCoreApplication.translate("MainWindow", "Configuration Error"),
            message,
        )

    def start_all_animations(self):
        self.all_animations_stopped = False
        for step in self.validation_steps[
            1:
        ]:  # Skip the first step (Connection Status)
            if step["movie"]:
                step["animation_label"].setMovie(step["movie"])
                step["movie"].start()

    def stop_all_animations(self):
        self.all_animations_stopped = True
        for step in self.validation_steps[
            1:
        ]:  # Skip the first step (Connection Status)
            if step["movie"]:
                step["movie"].stop()
                step["animation_label"].setMovie(None)

    def _create_battery_validator(self):
        class UpperCaseValidator(QValidator):
            def validate(self, input_str, pos):
                return QValidator.Acceptable, input_str.upper(), pos

        return UpperCaseValidator()

    def _create_pin_validator(self):
        class PinValidator(QValidator):
            def __init__(self, max_length=6):
                super().__init__()
                self.max_length = max_length

            def validate(self, input_str, pos):
                # Allow empty input
                if input_str == "":
                    return QValidator.Acceptable, input_str, pos
                # Check if the input is a digit
                if not input_str.isdigit():
                    return QValidator.Invalid, "", pos
                # Check if the input length exceeds the maximum length
                if len(input_str) > self.max_length:
                    return QValidator.Invalid, "", pos
                return QValidator.Acceptable, input_str, pos

        return PinValidator(max_length=6)

    def add_battery_row(self, is_first_row=False):
        # Create a new horizontal layout for the row
        row_layout = QHBoxLayout()

        if is_first_row:
            # Use QLabel for the first row to display placeholder text
            serial_number_label = QLabel(
                QCoreApplication.translate("MainWindow", "Battery Serial Number")
            )
            pin_label = QLabel(QCoreApplication.translate("MainWindow", "PIN"))
            row_layout.addWidget(serial_number_label)
            row_layout.addWidget(pin_label)

            # Add an empty space where the remove button would be
            spacer = QWidget()
            spacer.setFixedSize(75, 0)  # Adjust the width as needed
            row_layout.addWidget(spacer)
        else:
            # Create input fields for other rows
            serial_number_input = QLineEdit()
            serial_number_input.setPlaceholderText(
                QCoreApplication.translate("MainWindow", "Battery Serial Number")
            )
            # serial_number_input.setText("BR4830TWFO10121J01")
            serial_number_input.setText("TT0000TTTT00000T00")

            validator = self._create_battery_validator()
            serial_number_input.setValidator(validator)

            pin_input = QLineEdit()
            pin_input.setPlaceholderText(
                QCoreApplication.translate("MainWindow", "PIN")
            )
            # pin_input.setText("080324")
            pin_input.setText("000000")

            pin_validator = self._create_pin_validator()
            pin_input.setValidator(pin_validator)

            # Add widgets to the row layout
            row_layout.addWidget(serial_number_input)
            row_layout.addWidget(pin_input)

            # Create and add remove button
            remove_button = QPushButton(
                QCoreApplication.translate("MainWindow", "Remove")
            )
            row_layout.addWidget(remove_button)
            # Connect the remove button to a function to remove the row
            remove_button.clicked.connect(
                lambda: self.remove_battery_row(row_widget, row_data)
            )

        # Create a container widget for the row
        row_widget = QWidget()
        row_widget.setLayout(row_layout)

        # Add the row widget to the battery layout
        self.ui.batteryLayout.addWidget(row_widget)

        # Create a reference to the row's serial and pin inputs
        row_data = {
            "row_widget": row_widget,
            "serial_number_input": serial_number_input if not is_first_row else None,
            "pin_input": pin_input if not is_first_row else None,
            "remove_button": remove_button if not is_first_row else None,
            "is_first_row": is_first_row,  # Add flag to indicate if it's the first row
        }
        self.battery_rows.append(row_data)

        # # Expand the window vertically
        # current_size = self.size()
        # new_height = current_size.height() + 40  # Adjust the height increment as needed
        # self.resize(current_size.width(), new_height)

    def remove_battery_row(self, row_widget, row_data):
        if row_data["serial_number_input"]:
            row_data["serial_number_input"].setValidator(None)

        if row_data["pin_input"]:
            row_data["pin_input"].setValidator(None)

        # Remove the row widget from the layout
        self.ui.batteryLayout.removeWidget(row_widget)
        row_widget.deleteLater()
        # Remove row_data from self.battery_rows
        self.battery_rows.remove(row_data)

        # # Adjust the window size
        # current_size = self.size()
        # new_height = current_size.height() - 40  # Adjust the height decrement as needed
        # self.resize(current_size.width(), new_height)

    def save_log(self):
        # Get the content of advConfigureOutputText
        log_content = self.ui.advConfigureOutputText.toPlainText()

        # Get current date
        # current_date = datetime.now().strftime("%Y%m%d")
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"sc_{current_datetime}.txt"

        # Save to file
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(log_content)
            # Optionally, show a message box indicating success
            translated_message = QCoreApplication.translate(
                "MainWindow", "Log saved to"
            )
            QMessageBox.information(
                self, "Save Log", f"{translated_message} {file_name}"
            )
        except Exception as e:
            translated_message = QCoreApplication.translate(
                "MainWindow", "Failed to save log"
            )
            QMessageBox.warning(
                self, "Save Log Error", f"{translated_message}: {str(e)}"
            )

    def send_command(self):
        # Get the command from advCommandText
        command = self.ui.advCommandText.toPlainText().strip()
        if not command:
            QMessageBox.warning(
                self, "Invalid Command", "Please enter a command to send."
            )
            return

        # Get the port
        port = self.ui.detectedPortLabel.text().replace("Port: ", "")
        if not port or "N/A" in port:
            QMessageBox.warning(self, "No Device", "StiCAN device not detected.")
            return

        # Disable the send button
        self.ui.advSendCommand.setEnabled(False)

        # Create worker and thread
        self.command_thread = QThread()
        self.command_worker = CommandWorker(command, port)
        self.command_worker.moveToThread(self.command_thread)

        # Connect signals and slots
        self.command_thread.started.connect(self.command_worker.run)
        self.command_worker.finished.connect(self.command_thread.quit)
        self.command_worker.finished.connect(self.command_worker.deleteLater)
        self.command_thread.finished.connect(self.command_thread.deleteLater)
        self.command_worker.log.connect(self.log_message)
        # self.command_worker.error.connect(self.handle_error)
        self.command_thread.finished.connect(
            lambda: self.ui.advSendCommand.setEnabled(True)
        )

        # Start the thread
        self.command_thread.start()

    def closeEvent(self, event):
        # Close the serial connection when the window is closed
        if hasattr(self, "serial_connection"):
            if self.serial_connection.is_open:
                self.serial_connection.close()

        # Wait for the command thread to finish
        if hasattr(self, "command_thread"):
            if self.command_thread.isRunning():
                self.command_thread.quit()
                self.command_thread.wait()

        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
