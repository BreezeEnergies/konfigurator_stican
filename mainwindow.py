# mainwindow.py

import time
import serial
import serial.tools.list_ports
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
)
from PySide6.QtCore import QTimer, QObject, QThread, Signal
from PySide6.QtCore import (
    QTranslator,
    QLocale,
    QLibraryInfo,
    QCoreApplication,
    QSysInfo,
)
from datetime import datetime
from PySide6.QtGui import QMovie, QValidator
from ui_form import Ui_MainWindow

import os
import sys
from bleak import BleakScanner
import asyncio

from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout


# def show_message_box(parent, message):
#     # Use QTimer.singleShot to delay the execution of the message box
#     QTimer.singleShot(0, lambda: QMessageBox.information(parent, "Action Required", message, QMessageBox.Ok))


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


ANIMATION_FILES = [resource_path("loading-snake-io.gif")]
# ANIMATION_FILES = [os.path.join(base_path, "loading-snake-io.gif")]


# # Load the appropriate translation file
# def load_translation(language_code):
#     translator = QTranslator()
#     if language_code == 'pl':
#         translator.load(os.path.join(base_path, "form_pl.qm"))
#     else:
#         translator.load(os.path.join(base_path, "form_en.qm"))
#     QCoreApplication.instance().installTranslator(translator)


APPLICATION_VERSION = "1.1.1"
APPLICATION_AUTHORS = ["Maciej Hejlasz <DeimosMH>", ""]
APPLICATION_OWNERS = "Breeze Energies Sp. z o.o."

# ANIMATION_FILES = ["loading-snake-io.gif"]


class LoadingAnimation(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Loading Animation")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.loading_label = QLabel(self)
        layout.addWidget(self.loading_label)

        self.movie = QMovie(ANIMATION_FILES[0])
        self.loading_label.setMovie(self.movie)

        # Start the animation
        self.start_animation()

    def start_animation(self):
        self.movie.start()

    def stop_animation(self):
        self.movie.stop()


class ConfigureWorker(QObject):
    prompt_message = Signal(str)
    finished = Signal()
    progress = Signal(int, str)  # Step index, status ("PASS", "FAIL")
    log = Signal(str)  # For sending logs to advConfigureOutputText
    error = Signal(str)  # For error messages
    started = Signal()  # New signal to indicate when the process starts
    success = Signal()  # New signal to indicate success

    devices_not_found = Signal(list)  # Signal emitting a list of not found devices
    expected_disconnection = False

    def __init__(self, devices, port):
        super().__init__()
        self.devices = devices
        self.port = port
        self.serial_connection = None
        self.stican_detected = False  # Initialize the attribute
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connection_status)

    def check_connection_status(self):
        # Check if the StiCAN device is still connected
        ports = list(serial.tools.list_ports.comports())
        stican_port = next(
            (p.device for p in ports if p.vid == 0x10C4 and p.pid == 0xEA60), None
        )

        if stican_port:
            self.stican_detected = True
        else:
            self.stican_detected = False
            self.handle_disconnection()

    def handle_disconnection(self):
        self.connection_timer.stop()  # Stop the timer to prevent multiple dialogs
        QMessageBox.warning(
            None,
            "Connection Lost",
            "StiCAN device disconnected. Attempting to reconnect...",
        )

        # Attempt to reconnect
        try:
            self.serial_connection = serial.Serial(self.port, 115200, timeout=1)
            self.log.emit("Reconnected to StiCAN device.")
            self.stican_detected = True
            self.connection_timer.start(500)  # Restart the timer
        except Exception as e:
            self.log.emit(f"Error: Could not reconnect to StiCAN device: {str(e)}")
            self.progress.emit(step_index, "FAIL")
            self.error.emit(
                QCoreApplication.translate(
                    "MainWindow", "Error: Could not reconnect to StiCAN device."
                )
            )
            self.clean_conn()

    def clean_conn(self):
        if hasattr(self, "serial_connection"):
            if self.serial_connection != None:
                if self.stican_detected:
                    self.serial_connection.reset_input_buffer()
                    self.serial_connection.reset_output_buffer()
                    if self.serial_connection.is_open:
                        self.serial_connection.close()

        self.serial_connection = None
        self.finished.emit()

    def run(self):
        self.started.emit()  # Emit the started signal

        # Each step, update progress and log messages
        try:
            # OptionCheck
            step_index = 1  # Updated index after adding 'Connection Status' as step 0
            self.log.emit("Starting OptionCheck...")
            correctedData = False

            # Validate and possibly correct the configuration data
            firstLine = self.devices[0]
            if not firstLine.isdigit():
                self.log.emit("First line must be a number")
                correctedData = True
                self.devices[0] = "{0:02d}".format(len(self.devices) - 1)
            else:
                firstLineInt = int(firstLine)
                expectedFirstLine = "{0:02d}".format(len(self.devices) - 1)
                if "{0:02d}".format(firstLineInt) != expectedFirstLine:
                    self.log.emit("First line count incorrect")
                    correctedData = True
                    self.devices[0] = expectedFirstLine
                else:
                    self.log.emit("First line is correct")

            # Validate each device line
            seen_devices = set()  # Set to track seen devices
            for i in range(1, len(self.devices)):
                device = self.devices[i]

                # Check for duplicate device
                if device in seen_devices:
                    self.log.emit(
                        f"Error during StiCAN configuration: Duplicate device found - {device}"
                    )
                    self.progress.emit(step_index, "FAIL")
                    self.error.emit(
                        QCoreApplication.translate(
                            "MainWindow", "Error: Serial Number duplicate"
                        )
                    )
                    self.finished.emit()
                    return
                else:
                    seen_devices.add(device)

                fields = device.split(",")  # Do not filter out empty strings
                num_non_empty_fields = len([f for f in fields if f != ""])
                if num_non_empty_fields == 1:
                    self.log.emit(f"{device} is old battery or erroneous")
                    self.devices[i] = device.rstrip(",") + ",,"
                elif len(fields) == 3 and fields[2] == "":
                    self.log.emit(f"{device} is correct")
                else:
                    self.log.emit(f"{device} is erroneous - invalid format")
                    self.devices[i] = device.rstrip(",") + ","
                    correctedData = True

            if correctedData:
                self.log.emit("Configuration data was corrected")
                self.log.emit("Read the Manual to avoid configuration errors")
                status = "PASS"
            else:
                self.log.emit("Data is correct")
                status = "PASS"
            self.progress.emit(step_index, status)

            ###
            ### Check StiCAN version - currently line 409
            ### TO DO ->
            ###############

            # OptionConfig
            step_index = 2
            self.log.emit("Starting OptionConfig...")
            try:
                self.serial_connection = serial.Serial(self.port, 115200, timeout=1)
                self.log.emit("Connected to StiCAN device.")
            except Exception as e:
                self.log.emit(f"Error: Could not connect to StiCAN device: {str(e)}")
                self.progress.emit(step_index, "FAIL")
                self.finished.emit()
                return

            try:
                self.serial_connection.reset_input_buffer()
                self.serial_connection.reset_output_buffer()

                self.log.emit("Configuring StiCAN...")
                # Send 'help' - check connection
                self.serial_connection.write(b"help")
                time.sleep(2)
                received_check_data = self.serial_connection.read_all().decode(
                    "utf-8", errors="ignore"
                )
                self.log.emit(f"Check: {received_check_data}")

                ## CAN FRAMES
                # Send 'memerase'
                self.serial_connection.write(b"memerase")
                time.sleep(3)
                # Send '0'
                self.serial_connection.write(b"0")
                time.sleep(1.5)
                # Send '50'
                self.serial_connection.write(b"2")
                time.sleep(3)
                
                ## BAT DATA
                # Send 'memerase'
                self.serial_connection.write(b"memerase")
                time.sleep(3)
                # Send '0'
                self.serial_connection.write(b"4")
                time.sleep(1.5)
                # Send '50'
                self.serial_connection.write(b"27")
                time.sleep(3)
                # Send 'b'
                self.serial_connection.write(b"b")
                time.sleep(1)

                # Check for expected response
                attempts = 0
                max_attempts = 3
                expected_substring = ",E,1,1,1"
                config_success = False

                while attempts < max_attempts:
                    self.serial_connection.write(b"memchck")
                    time.sleep(2)
                    received_data = self.serial_connection.read_all().decode(
                        "utf-8", errors="ignore"
                    )

                    self.log.emit(f"Data: {received_data}")

                    # Define substrings to remove
                    substrings_to_remove = [
                        ",012131210,",
                        "-U-",
                        "-COMMAND-MODE-",
                        " ",
                        "\n",
                    ]
                    # Remove specified substrings
                    for substring in substrings_to_remove:
                        received_data = received_data.replace(substring, "")

                    self.log.emit(f"Cleaned Data: {received_data}")

                    if expected_substring in received_data:
                        self.log.emit("Expected substring detected in received data")
                        config_success = True
                        break
                    else:
                        self.log.emit("Unexpected data received, retrying...")
                        attempts += 1

                if config_success:
                    self.log.emit("StiCAN is prepared for configuration")
                    self.progress.emit(step_index, "PASS")
                else:
                    self.log.emit("Configuration of StiCAN failed")
                    self.progress.emit(step_index, "FAIL")
                    self.error.emit(
                        QCoreApplication.translate(
                            "MainWindow",
                            "Error: Can't prepare StiCAN for writing data. Try to plug out, then plug in StiCAN again.",
                        )
                    )

                    self.clean_conn()
                    return
            except Exception as e:
                self.log.emit(f"Error during StiCAN configuration: {str(e)}")
                self.progress.emit(step_index, "FAIL")
                self.clean_conn()
                return
            finally:
                self.serial_connection.reset_input_buffer()
                self.serial_connection.reset_output_buffer()

            # Option1 (Upload data to device)
            step_index = 3
            try:
                self.log.emit("Uploading data to StiCAN...")
                self.serial_connection.write(b"batnew")
                time.sleep(2)
                iTemp = 0
                for device_line in self.devices:
                    time.sleep(2)
                    if iTemp == 0:
                        self.log.emit("Wrote :: CONFIG DATA ::")
                    else:
                        self.log.emit(f"Wrote SN {iTemp} : {device_line}")
                    line_to_send = device_line.encode("utf-8")
                    self.serial_connection.write(line_to_send)
                    iTemp += 1
                time.sleep(2)
                self.log.emit("Data upload completed")
                self.progress.emit(step_index, "PASS")
            except Exception as e:
                self.log.emit(f"Error writing data to StiCAN: {str(e)}")
                self.progress.emit(step_index, "FAIL")
                self.clean_conn()
                return
            finally:
                self.serial_connection.reset_input_buffer()
                self.serial_connection.reset_output_buffer()

            # Option2 (Verify uploaded data)
            step_index = 4
            try:
                self.log.emit("Verifying uploaded data...")
                device_lines = []
                start_time = time.time()

                self.log.emit("\nRead lines:")

                max_retries = 4
                for attempt in range(max_retries):
                    self.serial_connection.write(b"batread")
                    device_lines = []
                    start_time = time.time()

                    self.log.emit("\nRead lines:")
                    while True:
                        if self.serial_connection.in_waiting > 0:
                            line = (
                                self.serial_connection.readline()
                                .decode("utf-8", errors="ignore")
                                .strip()
                            )
                            self.log.emit(f"Read line: {line}")
                            if line:
                                if line != "-COMMAND-MODE-":
                                    device_lines.append(line)
                                else:
                                    break  # End marker reached
                            else:
                                continue
                        else:
                            if time.time() - start_time > 10:
                                break

                    if len(device_lines) > 0:
                        # Process the received data
                        break

                    if attempt < max_retries - 1:
                        self.log.emit(
                            f"No data received. Retrying... (Attempt {attempt + 2}/{max_retries})"
                        )
                        time.sleep(1)  # Wait for 1 second before retrying

                # Remove the first line (number of devices) if present
                if device_lines and device_lines[0].isdigit():
                    device_lines = device_lines[1:]
                devices_from_device = device_lines
                # Remove spaces and normalize
                devices_normalized = [
                    line.replace(" ", "").strip() for line in self.devices[1:]
                ]
                devices_from_device_normalized = [
                    line.replace(" ", "").strip() for line in devices_from_device
                ]

                # Remove known substrings
                if ",012131210," in devices_from_device_normalized:
                    devices_from_device_normalized.remove(",012131210,")

                # Compare the lists
                self.log.emit("\ndevices_normalized:")
                self.log.emit(str(devices_normalized))
                self.log.emit("\ndevices_from_device_normalized:")
                self.log.emit(str(devices_from_device_normalized))

                if devices_normalized == devices_from_device_normalized:
                    self.log.emit("No differences found. Data verified successfully.")
                    self.progress.emit(step_index, "PASS")
                else:
                    self.log.emit("Differences found in uploaded data:")
                    differences = set(devices_normalized).symmetric_difference(
                        devices_from_device_normalized
                    )
                    for diff in differences:
                        self.log.emit(f"Difference: {diff}")
                    self.log.emit("Data corrupted. Please try again.")
                    self.progress.emit(step_index, "FAIL")
                    self.clean_conn()
                    return
            except Exception as e:
                self.log.emit(f"Error during verification: {str(e)}")
                self.progress.emit(step_index, "FAIL")
                self.clean_conn()
                return
            finally:
                self.serial_connection.reset_input_buffer()
                self.serial_connection.reset_output_buffer()
            self.log.emit("Step 4 Completed\n")

            # send command "info"
            # assign it variables: "STICAN,V2.0 rev1,V1.1 rel1", where:
            # device type: STICAN
            # hardware version: V2.0 rev1
            # software version: V1.1 rel1

            try:
                # self.serial_connection.write(b"info")
                # time.sleep(2)  # Wait for the device to respond
                # info_response = self.serial_connection.read_all().decode("utf-8", errors="ignore")
                # self.log.emit(f"Info Response: {info_response}")

                max_attempts = 3
                attempts = 0
                info_response = ""

                while attempts < max_attempts:
                    try:
                        self.serial_connection.write(b"info")

                        time.sleep(2)  # Wait for the device to respond
                        info_response = self.serial_connection.read_all().decode(
                            "utf-8", errors="ignore"
                        )
                        self.log.emit(f"Info Response: {info_response}")

                        # Check if the response is valid (you can define what a valid response is)
                        if "STICAN" in info_response:  # Example check, adjust as needed
                            break  # Exit the loop if the response is valid
                    except Exception as e:
                        self.log.emit(f"Error sending 'info' command: {str(e)}")

                    attempts += 1
                    if attempts < max_attempts:
                        self.log.emit(
                            f"Retrying 'info' command... (Attempt {attempts + 1}/{max_attempts})"
                        )
                    else:
                        self.log.emit(
                            "Failed to get a valid response after 3 attempts."
                        )

                # After the loop, you can handle the case where the response is still invalid
                if "STICAN" not in info_response:
                    self.log.emit(
                        "Error: Unable to retrieve valid info response after 3 attempts."
                    )
                    self.progress.emit(step_index, "FAIL")
                    self.error.emit(
                        QCoreApplication.translate(
                            "MainWindow",
                            "Error: Unable to retrieve valid info response.",
                        )
                    )
                    self.clean_conn()
                    return

                # Parse the response to extract the required information
                # Assuming the response format is "STICAN,V2.0 rev1,V1.1 rel1"
                parts = info_response.split(",")
                if len(parts) >= 3:
                    device_type = parts[0].strip()
                    hardware_version = parts[1].strip()
                    software_version = parts[2].strip()

                    self.log.emit(f"Device Type: {device_type}")
                    self.log.emit(f"Hardware Version: {hardware_version}")
                    self.log.emit(f"Software Version: {software_version}")

                    # Check the software version
                    # Assuming the version format is "V1.1 rel1" and you want to compare the numeric part
                    software_version_number = float(
                        software_version.split()[0][1:]
                    )  # Extract "1.1" from "V1.1 rel1"
                    if software_version_number > 1.0:
                        self.log.emit("Software version is greater than 1.0")
                        # Add logic for when the software version is greater than 1.0
                        # For example, you might want to reboot the device
                        self.serial_connection.write(b"reboot")
                    else:
                        self.log.emit("Software version is 1.0")
                        # Close the serial connection before showing the message box
                        if self.serial_connection and self.serial_connection.is_open:
                            self.serial_connection.close()

                        # Set a flag to indicate that disconnection is expected
                        self.expected_disconnection = True

                        # Emit the signal with the message
                        message = QCoreApplication.translate(
                            "MainWindow",
                            "Please disconnect and reconnect the StiCAN device",
                        )
                        self.prompt_message.emit(message)

                        # Wait for the device to be disconnected
                        self.log.emit("Waiting for device to be disconnected...")
                        while True:
                            ports = list(serial.tools.list_ports.comports())
                            stican_port = next(
                                (
                                    p.device
                                    for p in ports
                                    if p.vid == 0x10C4 and p.pid == 0xEA60
                                ),
                                None,
                            )
                            if stican_port is None:
                                self.log.emit("Device disconnected.")
                                break
                            else:
                                time.sleep(0.5)

                        # Wait for the device to be reconnected
                        self.log.emit("Waiting for device to be reconnected...")
                        while True:
                            ports = list(serial.tools.list_ports.comports())
                            stican_port = next(
                                (
                                    p.device
                                    for p in ports
                                    if p.vid == 0x10C4 and p.pid == 0xEA60
                                ),
                                None,
                            )
                            if stican_port is not None:
                                self.log.emit("Device reconnected.")
                                # Wait a moment to ensure device is ready
                                time.sleep(2)
                                break
                            else:
                                time.sleep(0.5)

                        # Reopen the serial connection
                        try:
                            self.serial_connection = serial.Serial(
                                self.port, 115200, timeout=1
                            )
                            self.log.emit("Reconnected to StiCAN device.")
                        except Exception as e:
                            self.log.emit(
                                f"Error: Could not reconnect to StiCAN device: {str(e)}"
                            )
                            self.progress.emit(step_index, "FAIL")
                            self.error.emit(
                                QCoreApplication.translate(
                                    "MainWindow",
                                    "Error: Could not reconnect to StiCAN device.",
                                )
                            )
                            self.clean_conn()
                            return

                        # Reset the expected disconnection flag
                        self.expected_disconnection = False

                else:
                    self.log.emit(
                        "Error: Unexpected response format from 'info' command"
                    )
                    self.progress.emit(step_index, "FAIL")
                    self.error.emit(
                        QCoreApplication.translate(
                            "MainWindow",
                            "Error: Unexpected response format from software version request",
                        )
                    )
                    self.clean_conn()
                    return

            except Exception as e:
                self.log.emit(f"Error sending 'info' command: {str(e)}")
                self.progress.emit(step_index, "FAIL")
                self.error.emit(
                    QCoreApplication.translate(
                        "MainWindow",
                        "Error sending request for software version request",
                    )
                )
                self.clean_conn()
                return

            # Option5 (Verify battery detection)
            step_index = 5
            try:

                attempt = 0
                max_retries = 2
                not_found_batteries = []

                for attempt in range(max_retries):

                    self.log.emit("\nVerifying battery detection...")
                    time.sleep(1)
                    self.serial_connection.write(b"b")
                    time.sleep(2)
                    self.serial_connection.reset_input_buffer()
                    self.serial_connection.write(b"scan")
                    allBatConn = []
                    readTime = 9  # seconds
                    self.log.emit(
                        f"Performing battery detection for {readTime} seconds..."
                    )
                    start_time = time.time()

                    while True:
                        if self.serial_connection.in_waiting > 0:
                            line = (
                                self.serial_connection.readline()
                                .decode("utf-8", errors="ignore")
                                .strip()
                            )
                            self.log.emit("ln: " + str(line))

                            if line.startswith("found") or line.startswith("search"):
                                # Extract serial number from device response
                                parts = line.split(",")
                                if len(parts) >= 2:
                                    found_serial = parts[1]
                                    for device_line in self.devices[1:]:
                                        # Check if the serial number matches any in our list
                                        if found_serial in device_line:
                                            if device_line not in allBatConn:
                                                allBatConn.append(device_line)
                            else:
                                pass
                        else:
                            if time.time() - start_time > readTime:
                                break

                    # Verify which batteries are connected
                    STICAN_PASS = True
                    for device_line in self.devices[1:]:
                        if device_line in allBatConn:
                            self.log.emit(f"PASS: {device_line}")
                        else:
                            self.log.emit(f"FAIL: {device_line}")
                            not_found_batteries.append(device_line)
                            STICAN_PASS = False

                    if STICAN_PASS:
                        break

                if STICAN_PASS:
                    self.log.emit("CONFIGURATION RESULT: SUCCESS!")
                    self.progress.emit(step_index, "PASS")
                    self.success.emit()

                else:
                    self.log.emit("CONFIGURATION RESULT: FAIL!")
                    self.progress.emit(step_index, "FAIL")
                    # self.error.emit(
                    #     QCoreApplication.translate("MainWindow", "Error: StiCAN can't detect all batteries. Are Serial Numbers correct?")
                    # )
                    # Add message box with information "Devices not found" and list: not_found_batteries

                    not_found_batteries_filtered = list(set(not_found_batteries))
                    # not_found_message = QCoreApplication.translate("MainWindow", "Devices not found") + ":\n" + "\n".join(not_found_batteries_filtered)
                    # QMessageBox.warning(None, "Devices Not Found", not_found_message)

                    self.devices_not_found.emit(not_found_batteries_filtered)

            except Exception as e:
                self.log.emit(f"Error during battery detection: {str(e)}")
                self.progress.emit(step_index, "FAIL")
                # self.finished.emit()

                # Ensure we send 'b' to exit debug mode
                self.serial_connection.write(b"b")
                self.clean_conn()
                return
            finally:
                # Ensure we send 'b' to exit debug mode
                self.serial_connection.write(b"b")
                self.serial_connection.reset_input_buffer()
                self.serial_connection.reset_output_buffer()
                self.clean_conn()

            self.finished.emit()

        except Exception as e:
            self.log.emit(f"Error during configuration: {str(e)}")
            self.progress.emit(step_index, "FAIL")
            self.clean_conn()


class CommandWorker(QObject):
    finished = Signal()
    log = Signal(str)  # For sending logs to advConfigureOutputText
    error = Signal(str)  # For error messages

    def __init__(self, command, port):
        super().__init__()
        self.command = command
        self.port = port

    def run(self):
        try:
            self.serial_connection = serial.Serial(self.port, 115200, timeout=1)
            self.log.emit(f"Connected to {self.port}. Sending command: {self.command}")

            # Send the command
            self.serial_connection.write(self.command.encode("utf-8"))

            # Read data for 2 seconds
            start_time = time.time()
            while time.time() - start_time < 2:
                if self.serial_connection.in_waiting > 0:
                    data = (
                        self.serial_connection.readline()
                        .decode("utf-8", errors="ignore")
                        .strip()
                    )
                    self.log.emit(f"Received: {data}")
                else:
                    time.sleep(0.1)  # Wait for data

            self.log.emit("Finished reading data.")
            self.serial_connection.close()
        except Exception as e:
            self.log.emit(f"Error during command execution: {str(e)}")
            self.finished.emit()
        finally:
            self.finished.emit()


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
        for _ in range(3):  # Remaining rows
            self.add_battery_row()

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
            if not self.check_driver_in_driverstore() or not self.check_driver_loaded():
                translated_status = QCoreApplication.translate(
                    "MainWindow",
                    "Drivers not detected. You need to install drivers to connect with StiCAN.",
                )
                QMessageBox.information(self, "Drivers", f"{translated_status}")
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

    # def check_driver_loaded(self):
    #     import subprocess
    #     driver_name = "silabser.sys"
    #     try:
    #         # Use the 'sc query' command to check the status of the driver
    #         result = subprocess.run(['sc', 'query', driver_name], capture_output=True, text=True, encoding='cp1252')
    #         # Check if the driver is running
    #         if "RUNNING" in result.stdout:
    #             self.log("CP210x driver is loaded.")
    #             return True
    #     except Exception as e:
    #         self.log(f"Error checking driver status: {e}")
    #     self.log("CP210x driver is not loaded.")
    #     return False

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

    # def handle_error(self, message):
    #     self.ui.advConfigureOutputText.append(f"Error: {message}")

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
        else:
            self.stican_detected = False
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

        # Restart the timer to reactivate detect_stican
        self.timer.start(500)  # Check every 0.5 seconds

    def start_configuration(self, devices, port):
        # Stop the timer to deactivate detect_stican
        self.timer.stop()

        # Create worker thread
        self.thread = QThread()
        self.worker = ConfigureWorker(devices, port)

        self.worker.moveToThread(self.thread)

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
            serial_number_input.setText("BR4830TWFO10121J01")

            validator = self._create_battery_validator()
            serial_number_input.setValidator(validator)

            pin_input = QLineEdit()
            pin_input.setPlaceholderText(
                QCoreApplication.translate("MainWindow", "PIN")
            )
            pin_input.setText("080324")

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
