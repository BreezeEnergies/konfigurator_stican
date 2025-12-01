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
    QWidget,
    QVBoxLayout,
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

