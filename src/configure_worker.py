from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QTimer, QObject, Signal, QCoreApplication, QSysInfo
import os
import sys
import queue
import time
import serial
import serial.tools.list_ports


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

    # 1. ask the GUI to show a binary-choice dialog
    request_choice = Signal(
        str, list
    )  # question, [button1, button2] (V > 3.0) Victron/Deye

    def __init__(self, devices, port):
        super().__init__()
        self.devices = devices
        self.port = port
        self.serial_connection = None
        self.stican_detected = False  # Initialize the attribute
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connection_status)
        self.correctedData = False
        self.software_version = None
        self.software_version_number = 0.0

        self._choice_queue = queue.Queue()  # 1-element queue

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
        self.connection_timer.stop()
        QMessageBox.warning(
            None,
            "Connection Lost",
            "StiCAN device disconnected. Attempting to reconnect...",
        )
        try:
            self.serial_connection = serial.Serial(self.port, 115200, timeout=1)
            self.log.emit("Reconnected to StiCAN device.")
            self.stican_detected = True
            self.connection_timer.start(500)
        except Exception as e:
            self.log.emit(f"Error: Could not reconnect: {str(e)}")
            self.progress.emit(1, "FAIL")
            self.error.emit("Error: Could not reconnect to StiCAN device.")
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

    def open_serial_connection(self):
        """Try opening a serial connection to self.port."""
        try:
            self.serial_connection = serial.Serial(self.port, 115200, timeout=1)
            self.log.emit("Connected to StiCAN device.")
            return True
        except Exception as e:
            self.log.emit(f"Error: Could not connect: {str(e)}")
            return False

    def step_ConnectionStatus(self, step_index):
        """
        Optional small step to confirm or log the device is connected
        (and set the step to PASS if it is).
        """
        self.log.emit("Checking initial Connection Status...")
        self.progress.emit(step_index, "PASS")

    def step_ValidateDataToWrite(self, step_index):
        """
        Validate the lines in self.devices, correct if needed, and
        check for duplicates or formatting errors.
        """
        self.log.emit("Starting OptionCheck (ValidateDataToWrite)...")
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
                self.log.emit(f"Duplicate device found: {device}")
                self.progress.emit(step_index, "FAIL")
                self.error.emit(
                    QCoreApplication.translate(
                        "MainWindow", "Error: Serial Number duplicate"
                    )
                )
                self.finished.emit()
                raise RuntimeError("Duplicate device found")
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
            self.log.emit("Configuration data was corrected.")
            self.log.emit("Read the Manual to avoid config errors.")
        else:
            self.log.emit("Data is correct.")

        self.progress.emit(step_index, "PASS")
        self.correctedData = correctedData


    def step_ReadDeviceInfo(self, step_index):
        """
        Open the serial port and read the device info (e.g., \'info\' command).
        Also parse out self.software_version and self.software_version_number.
        """

        if not self.open_serial_connection():
            self.progress.emit(step_index, "FAIL")
            self.finished.emit()
            return


        os_name = QSysInfo.productType()
        if "lin" in os_name.lower():
            self.log.emit("Linux")
        else:
            self.log.emit("Windows")
            self.log.emit("'s' - wait")
            self.serial_connection.write(b"s")  # stop work mode for >= v3.0 at start 
            time.sleep(3)
            self.serial_connection.write(b"info")  # stop work mode for >= v3.0 at start 
            time.sleep(3)
            self.serial_connection.write(b"s")  # stop work mode for >= v3.0 at start 
            time.sleep(3)

        MANDATORY = "STICAN,"  # More specific: ignores "-STICAN-" in boot logs (StiCAN can be rebooted in Windows in some cases)
        ABORT = "-U-"  # stop-reading token
        ABORT_b = "POWERON_RESET"
        ABORT_c = "entry 0x"
        RX_TIMEOUT = 3.0  # seconds we are prepared to listen
        RETRY_PAUSE = 1.0  # seconds to wait after we saw “-U-”

        max_attempts = 3
        attempts = 0
        info_response = ""

        while attempts < max_attempts:
            attempts += 1

            if attempts == 2:
                if "win" in os_name.lower():
                    self.serial_connection.write(b"s")  # stop work mode for >= v3.0 at start 
                time.sleep(7)  # if p2p - stopping work mode can be slow

            self.log.emit(f"info attempt {attempts}/{max_attempts}")

            self.serial_connection.write(b"info")  # the actual command

            t0 = time.time()
            rx_buffer = ""
            success = False
            aborted = False

            # read until timeout or one of the two tokens arrives
            while (time.time() - t0) < RX_TIMEOUT:
                chunk = self.serial_connection.read(
                    self.serial_connection.in_waiting or 1
                ).decode(errors="ignore")

                if not chunk:  # nothing arrived in this poll
                    time.sleep(0.05)
                    continue

                rx_buffer += chunk

                # rule-2 : we have what we need
                if MANDATORY in rx_buffer:
                    success = True
                    break

                # rule-3 : abort criterion met
                if ABORT in rx_buffer and MANDATORY not in rx_buffer:
                    aborted = True
                    break

                if (ABORT_b in rx_buffer or ABORT_c in rx_buffer):
                    if "win" in os_name.lower():
                        self.serial_connection.write(b"s")  # stop work mode for >= v3.0 at start 
                        time.sleep(1)
                    aborted = True
                    break


            # -----------------------------------------------------------
            # evaluate this attempt
            # -----------------------------------------------------------
            if success:  # rule-2
                # Once we find the valid start, discard everything before it
                info_response = rx_buffer[rx_buffer.find(MANDATORY):]
                break

            if aborted:  # rule-3
                self.log.emit("'-U-' detected - pausing 1 s before next attempt")
                attempts -= 1
                time.sleep(RETRY_PAUSE)
                # loop will continue with attempts+1

            else:  # rule-1 (nothing arrived)
                self.log.emit(f"No reply within {RX_TIMEOUT} s - retrying")
                if "win" in os_name.lower():
                    self.serial_connection.write(b"s")  # stop work mode for >= v3.0 at start 
                    time.sleep(1)

        # -----------------------------------------------------------------------
        # after the loop
        # -----------------------------------------------------------------------
        if MANDATORY not in info_response:
            self.log.emit("Failed to get a valid response after 3 attempts.")
            self.progress.emit(step_index, "FAIL")
            self.error.emit("Error: Unable to retrieve valid info response.")
            self.clean_conn()
            raise RuntimeError("No 'info' response")

        # Define substrings to remove
        substrings_to_remove = [
            ",012131210,",
            "-U-",
            "-COMMAND-MODE-",
            # " ", # dont remove spaces in this case
            "\n",
        ]
        # Remove specified substrings
        for substring in substrings_to_remove:
            info_response = info_response.replace(substring, "")

        self.log.emit(f"Cleaned Data: {info_response}")

        # Parse the response to extract the required information
        # Assuming the response format is: "STICAN,V2.0 rev1,V1.1 rel1"
        parts = info_response.split(",")
        if len(parts) >= 3:
            device_type = parts[0].strip()
            hardware_version = parts[1].strip()
            self.software_version = parts[2].strip()
            self.software_version_number = float(
                self.software_version.split()[0][1:]
            )  # Extract "1.1" from "V1.1 rel1"

            self.log.emit(f"Device Type: {device_type}")
            self.log.emit(f"Hardware Version: {hardware_version}")
            self.log.emit(f"Software Version: {self.software_version}")
            self.log.emit(f"Software Version Number: {self.software_version_number}")

        else:  # inserted
            self.log.emit("Error: Unexpected info format.")
            self.progress.emit(step_index, "FAIL")
            self.clean_conn()
            raise RuntimeError("Bad 'info' format")

        self.progress.emit(step_index, "PASS")

    def step_PrepareForConfiguration(self, step_index):
        """
        Erase memory / do memory checks based on software version to prepare device.
        """

        self.log.emit("Preparing device for configuration...")
        self.serial_connection.reset_input_buffer()
        self.serial_connection.reset_output_buffer()

        if not (self.serial_connection and self.serial_connection.is_open) and (
            not self.open_serial_connection()
        ):
            self.progress.emit(step_index, "FAIL")
            self.clean_conn()
            raise RuntimeError("Port not open")
        
        try:
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()


            os_name = QSysInfo.productType()
            if "lin" in os_name.lower():
                self.log.emit("Linux")
            else:
                self.log.emit("Windows - cmd")
                self.serial_connection.write(b'help')
                time.sleep(2)

            received_check_data = self.serial_connection.read_all().decode(
                "utf-8", errors="ignore"
            )
            self.log.emit(f"Check: {received_check_data}")
            if self.software_version_number >= 3.0:
                self.log.emit("SW >= 3.0 => using 'memfctr'")
                self.serial_connection.write(b"memfctr")
                time.sleep(2)

                if "win" in os_name.lower():
                    time.sleep(4)

                RX_TIMEOUT = 8.0  # seconds we are prepared to listen
                self.serial_connection.write(b"info")  # the actual command
                self.log.emit("Send 'info'")

                t0 = time.time()
                rx_buffer = ""

                # read until timeout or one of the two tokens arrives
                while (time.time() - t0) < RX_TIMEOUT:
                    chunk = self.serial_connection.read(
                        self.serial_connection.in_waiting or 1
                    ).decode(errors="ignore")

                    if not chunk:  # nothing arrived in this poll
                        time.sleep(0.05)
                        continue

                    rx_buffer += chunk

                    # rule-2 : we have what we need
                    if "STICAN" in rx_buffer:
                        break

            elif self.software_version_number > 1.1:
                self.log.emit("SW > 1.1 -> memory 64kB => using 'memfctr'")
                self.serial_connection.write(b"memfctr")
                time.sleep(9)
            else:
                self.log.emit("SW <= 1.1 -> memory 16kB => manual erase approach")
                self.serial_connection.write(b"memerase")
                time.sleep(3)
                self.serial_connection.write(b"0")
                time.sleep(1.5)
                self.serial_connection.write(b"2")
                time.sleep(3)
                self.serial_connection.write(b"memerase")
                time.sleep(3)
                self.serial_connection.write(b"4")
                time.sleep(1.5)
                self.serial_connection.write(b"23")
                time.sleep(3)

            # Check for expected response
            attempts = 0
            max_attempts = 3
            expected_substring = ",E,1,1,1"
            config_success = False

            while attempts < max_attempts:
                self.log.emit("Send 'memchck'")
                self.serial_connection.write(b"memchck")

                RX_TIMEOUT = 3.0
                t0 = time.time()
                rx_buffer = ""

                # read until timeout or one of the two tokens arrives
                while (time.time() - t0) < RX_TIMEOUT:
                    chunk = self.serial_connection.read(
                        self.serial_connection.in_waiting or 1
                    ).decode(errors="ignore")

                    if not chunk:  # nothing arrived in this poll
                        time.sleep(0.05)
                        continue

                    rx_buffer += chunk
                    self.log.emit(f"ln {chunk}")

                    if expected_substring in rx_buffer:
                        config_success = True
                        break

                if config_success:
                    break

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
        finally:
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()

    def step_UploadData(self, step_index):
        """
        Upload the data in self.devices (serial numbers of batteries) to the StiCAN device.
        """
        self.log.emit("Uploading data to StiCAN...")

        if not (self.serial_connection and self.serial_connection.is_open) and (
            not self.open_serial_connection()
        ):
            self.progress.emit(step_index, "FAIL")
            self.clean_conn()
            raise RuntimeError("Port not open")
        try:
            self.serial_connection.write(b"batnew")

            time.sleep(2)
            iTemp = 0
            for device_line in self.devices:
                time.sleep(2)
                self.serial_connection.write(device_line.encode("utf-8"))

                if iTemp == 0:
                    self.log.emit("Wrote :: CONFIG DATA ::")

                    if self.software_version_number >= 3.0:
                        self.log.emit(
                            "Additional :: CONFIG DATA :: for software_version ≥ 3.0"
                        )

                        # ---- pop-up -------------------------------------------------
                        self.request_choice.emit(
                            "Inverter connection mode", ["Deye", "Victron"]
                        )
                        choice = self._choice_queue.get(timeout=30)  # blocks ≤ 30 s
                        # choice is the **text** of the clicked button
                        # -------------------------------------------------------------

                        code = b"01" if choice == "Victron" else b"00"

                        if code == b"01":
                            self.log.emit(f"Set 'Victron': {code}")
                        else:
                            self.log.emit(f"Set 'Deye': {code}")

                        self.serial_connection.write(code)
                        time.sleep(2)

                        # # ---- pop-up -------------------------------------------------
                        # self.request_choice.emit(
                        #     "Work connection mode\nCDT works only with batteries from 2025 and above",
                        #     ["P2P", "CDT"],
                        # )
                        # choice = self._choice_queue.get(timeout=30)  # blocks ≤ 30 s
                        # # choice is the **text** of the clicked button
                        # # -------------------------------------------------------------

                        # code = b"0" if choice == "CDT" else b"1"

                        # if code == b"0":
                        #     self.log.emit(f"Set 'CDT': {code}")
                        # else:
                        #     self.log.emit(f"Set 'P2P': {code}")

                        # self.serial_connection.write(code)
                        self.serial_connection.write(b'1') # P2P

                        time.sleep(2)

                else:
                    self.log.emit(f"Wrote SN {iTemp} : {device_line}")

                iTemp += 1
            time.sleep(2.5)
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


    def step_VerifyDeviceData(self, step_index):
        """
        Read the data back from the device and verify it matches the lines in self.devices.
        """
        self.log.emit("Verifying uploaded data...")

        if not (self.serial_connection and self.serial_connection.is_open) and (
            not self.open_serial_connection()
        ):
            self.progress.emit(step_index, "FAIL")
            self.clean_conn()
            raise RuntimeError("Port not open")
        
        self.serial_connection.timeout = 5  # Set a 5-second timeout for this slow command

        try:
            self.serial_connection.reset_input_buffer()  # Still important to clear old data

            max_full_retries = 3
            fail_full = True

            for full_attempt in range(max_full_retries):
                device_lines = []
                max_retries = 4
                for attempt in range(max_retries):
                    self.serial_connection.write(b"batread")
                    self.log.emit("Send `batread`")

                    time.sleep(2 + (full_attempt + attempt) * 0.5)

                    # header = self.serial_connection.read(2) # prone to errors
                    header_line = self.serial_connection.readline().decode("ascii", errors="ignore").strip()
                    
                    if not header_line:
                        self.log.emit(f"Attempt {attempt + 1}: Timeout waiting for header.")
                        continue # Retry

                    self.log.emit(f"Header: {header_line}")

                    try:
                        # Attempt to parse device count
                        device_reported_count = int(header_line)
                        self.log.emit(f"Attempt to parse device count {device_reported_count} from {header_line}")
                    except ValueError:
                         # Fallback if header is garbage, though readline() helps prevent this
                        self.log.emit(f"WARNING: Invalid header received: {header_line}")
                        device_reported_count = -1

                    local_expected_count = len(self.devices) - 1

                    self.log.emit(f"Header: {header_line} (Reported: {device_reported_count}, Expected: {local_expected_count})")

                    # Logic to handle mismatch
                    expected = local_expected_count
                    if device_reported_count != local_expected_count:
                        self.log.emit(f"WARNING: Device reports {device_reported_count} batteries, but we uploaded {local_expected_count}.")
                        self.log.emit("Retrying full process...")
                        continue

                    self.log.emit(f"Expected number of bat line {self.devices},\n INT {expected}, INT:02 {expected:02d}")

                    if not self.devices[0].isdigit() or int(self.devices[0]) != expected:
                        self.log.emit(f"First line corrected to {expected:02d}")
                        self.devices[0] = f"{expected:02d}"

                    self.log.emit(f"Expecting {expected} battery lines")

                    # Read lines until we have the expected number or time out
                    start_time = time.time()
                    while len(device_lines) < expected and ( (time.time() - start_time) < 10 ):
                        raw = self.serial_connection.readline()
                        if not raw: # readline timed out
                            break
                        line = (
                            raw.decode("utf-8", errors="ignore")
                            .replace(",012131210,", "")
                            .strip()
                        )
                        if line: # Append if not empty
                            device_lines.append(line)
                    
                    if len(device_lines) == expected:
                        break # Success! Exit the retry loop.

                if len(device_lines) == 0 and full_attempt < max_full_retries -1:
                    self.log.emit("Failed to read any device lines. Retrying full process...")
                    continue

                devices_from_device = device_lines

                devices_normalized = [
                    line.replace(" ", "").strip() for line in self.devices[1:]
                ]
                devices_from_device_normalized = [
                    line.replace(" ", "").strip() for line in devices_from_device
                ]

                self.log.emit(f"\ndevices_normalized:\n{devices_normalized}")
                self.log.emit(f"\ndevices_from_device_normalized:\n{devices_from_device_normalized}")


                if devices_normalized == devices_from_device_normalized:
                    self.log.emit("No differences found. Data verified successfully.")
                    self.progress.emit(step_index, "PASS")
                    fail_full = False
                    break
                else:
                    self.log.emit("Differences found in uploaded data:")
                    differences = set(devices_normalized).symmetric_difference(
                        devices_from_device_normalized
                    )
                    for diff in differences:
                        self.log.emit(f"Difference: {diff}")
                    self.log.emit("Data corrupted. Try again.")
                    fail_full = True
                    continue

            if fail_full:
                self.progress.emit(step_index, "FAIL")
                self.clean_conn()
                raise RuntimeError("Data verification failed")

        except Exception as e:
            self.log.emit(f"Error verifying data: {str(e)}")
            self.progress.emit(step_index, "FAIL")
            self.clean_conn()
        finally:
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()

    def step_ScanAndDetectDevices(self, step_index):
        self.log.emit("Verifying battery detection...")
        if not (self.serial_connection and self.serial_connection.is_open) and (
            not self.open_serial_connection()
        ):
            self.progress.emit(step_index, "FAIL")
            self.clean_conn()
            raise RuntimeError("Port not open")

        max_retries = 4
        not_found_batteries = []

        if self.software_version_number > 1.0:
            self.serial_connection.write(
                b"reboot"
            )  # necessary for proper scan after configuration
            time.sleep(3)
            
        attempt = 0
        while attempt < max_retries and attempt < 6:
            not_found_batteries.clear()
            self.log.emit(
                f"\nVerifying battery detection... (attempt {attempt + 1}/{max_retries})"
            )

            # os_name = QSysInfo.productType()
            # if "win" in os_name.lower() and attempt > 3 and attempt <= 5:
            #     self.log.emit("Win - s")
            #     self.serial_connection.write(b"s")
            #     time.sleep(7)

            # --- send command (no line ending) -----------------------------
            time.sleep(2)
            self.serial_connection.write(b"scan")

            # --- read with the new rules ----------------------------------
            allBatConn = []
            RX_TIMEOUT = 9.0  # rule-1: 9-second window
            ABORT = "-U-"
            ABORT_b = "SW_CPU_RESET"
            ABORT_c = "entry 0x"
            start_time = time.time()
            got_data = False  # true as soon as we see any char

            while (time.time() - start_time) < RX_TIMEOUT:
                if self.serial_connection.in_waiting > 0:
                    line = (
                        self.serial_connection.readline()
                        .decode("utf-8", errors="ignore")
                        .strip()
                    )
                    self.log.emit(f"ln: {line}")
                    got_data = True

                    # rule-3: abort if -U- arrives while still missing batteries
                    if ABORT in line and not all(
                        r in allBatConn for r in self.devices[1:]
                    ):
                        self.log.emit("'-U-' detected - pause 3 s")
                        max_retries += 1  
                        time.sleep(3)
                        break

                    if (ABORT_b in line or ABORT_c in line) and not all(
                        r in allBatConn for r in self.devices[1:]
                    ):
                        self.serial_connection.write(b"s")  
                        time.sleep(3)
                        # self.serial_connection.write(b"scan") # The loop does it

                        self.log.emit("'SW_CPU_RESET' detected - Waiting 5s for reboot...")
                        
                        max_retries += 1
                        time.sleep(2) 
                        # Flush the "configsip..." boot garbage so it doesn't confuse the next read
                        self.serial_connection.reset_input_buffer()
                        
                        break

                    # normal processing
                    if line.startswith("found") or line.startswith("search"):
                        parts = line.split(",")
                        if len(parts) >= 2:
                            found_serial = parts[1]
                            for device_line in self.devices[1:]:
                                if (
                                    found_serial in device_line
                                    and device_line not in allBatConn
                                ):
                                    allBatConn.append(device_line)

                            # <-- early exit when list complete
                            if all(d in allBatConn for d in self.devices[1:]):
                                self.log.emit(
                                    "All devices found - finishing scan early"
                                )
                                break  # leaves the while-loop instantly

                else:
                    time.sleep(0.05)  # small anti-spin delay

            # rule-1: nothing arrived at all -> retry
            if not got_data:
                self.log.emit("No reply within timeout - retry")
                attempt += 1 # Increment attempt counter
                continue

            # --- pass/fail evaluation -------------------------------------
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
            
            # Increment attempt counter for next iteration
            attempt += 1

        # --- final report ---------------------------------------------------
        self.serial_connection.reset_input_buffer()
        self.serial_connection.reset_output_buffer()

        if STICAN_PASS:
            self.log.emit("CONFIGURATION RESULT: SUCCESS!")
            self.progress.emit(step_index, "PASS")
            self.success.emit()
            self.finished.emit()
        else:
            self.log.emit("CONFIGURATION RESULT: FAIL")
            self.devices_not_found.emit(not_found_batteries)
            self.progress.emit(step_index, "FAIL")
            self.error.emit("Error: Not all devices were detected.")
            self.finished.emit()

    def run(self):
        """Perform the full configuration in discrete steps."""

        self.started.emit()
        try:
            step_index = 0
            self.step_ConnectionStatus(step_index)
            step_index = 1
            self.step_ValidateDataToWrite(step_index)
            self.step_ReadDeviceInfo(step_index=1)
            step_index = 2
            self.step_PrepareForConfiguration(step_index)
            step_index = 3
            self.step_UploadData(step_index)
            step_index = 4
            self.step_VerifyDeviceData(step_index)
            step_index = 5
            self.step_ScanAndDetectDevices(step_index)
        except Exception as e:
            self.log.emit(f"Error during configuration: {str(e)}")
            self.progress.emit(step_index, "FAIL")
            self.clean_conn()

