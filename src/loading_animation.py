
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

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


ANIMATION_FILES = [resource_path("loading-snake-io.gif")]

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

