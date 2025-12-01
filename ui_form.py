# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLayout, QMainWindow, QPushButton,
    QScrollArea, QSizePolicy, QStatusBar, QTabWidget,
    QTextBrowser, QTextEdit, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 723)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setMinimumSize(QSize(800, 700))
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.configurationTab = QWidget()
        self.configurationTab.setObjectName(u"configurationTab")
        self.verticalLayout_2 = QVBoxLayout(self.configurationTab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.Status = QFrame(self.configurationTab)
        self.Status.setObjectName(u"Status")
        self.Status.setMaximumSize(QSize(16777215, 60))
        self.connectionLayout = QHBoxLayout(self.Status)
        self.connectionLayout.setObjectName(u"connectionLayout")
        self.connectionLayout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        self.Detect = QFrame(self.Status)
        self.Detect.setObjectName(u"Detect")
        self.Detect.setMaximumSize(QSize(16777215, 40))
        self.detectionLayout = QHBoxLayout(self.Detect)
        self.detectionLayout.setObjectName(u"detectionLayout")
        self.detectionLayout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        self.statusIndicatorLabel = QLabel(self.Detect)
        self.statusIndicatorLabel.setObjectName(u"statusIndicatorLabel")
        self.statusIndicatorLabel.setMinimumSize(QSize(20, 20))
        self.statusIndicatorLabel.setMaximumSize(QSize(20, 20))
        self.statusIndicatorLabel.setStyleSheet(u"\n"
"                background-color: red;\n"
"                border-radius: 10px;\n"
"                border: 1px solid black;\n"
"                ")

        self.detectionLayout.addWidget(self.statusIndicatorLabel)

        self.detectionStatusLabel = QLabel(self.Detect)
        self.detectionStatusLabel.setObjectName(u"detectionStatusLabel")
        self.detectionStatusLabel.setMaximumSize(QSize(16777215, 20))

        self.detectionLayout.addWidget(self.detectionStatusLabel)


        self.connectionLayout.addWidget(self.Detect)

        self.detectedPortLabel = QLabel(self.Status)
        self.detectedPortLabel.setObjectName(u"detectedPortLabel")
        self.detectedPortLabel.setMaximumSize(QSize(16777215, 20))

        self.connectionLayout.addWidget(self.detectedPortLabel)


        self.verticalLayout_2.addWidget(self.Status)

        self.Information1 = QLabel(self.configurationTab)
        self.Information1.setObjectName(u"Information1")
        self.Information1.setMaximumSize(QSize(16777215, 20))
        font = QFont()
        font.setBold(True)
        font.setStrikeOut(False)
        self.Information1.setFont(font)
        self.Information1.setTextFormat(Qt.TextFormat.RichText)
        self.Information1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.Information1)

        self.Information2 = QLabel(self.configurationTab)
        self.Information2.setObjectName(u"Information2")
        self.Information2.setMaximumSize(QSize(16777215, 20))
        self.Information2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.Information2)

        self.batteryScrollArea = QScrollArea(self.configurationTab)
        self.batteryScrollArea.setObjectName(u"batteryScrollArea")
        self.batteryScrollArea.setWidgetResizable(True)
        self.batteryScrollAreaContents = QWidget()
        self.batteryScrollAreaContents.setObjectName(u"batteryScrollAreaContents")
        self.batteryScrollAreaContents.setGeometry(QRect(0, 0, 758, 436))
        self.batteryScrollAreaLayout = QVBoxLayout(self.batteryScrollAreaContents)
        self.batteryScrollAreaLayout.setObjectName(u"batteryScrollAreaLayout")
        self.batteryLayout = QVBoxLayout()
        self.batteryLayout.setObjectName(u"batteryLayout")

        self.batteryScrollAreaLayout.addLayout(self.batteryLayout)

        self.batteryScrollArea.setWidget(self.batteryScrollAreaContents)

        self.verticalLayout_2.addWidget(self.batteryScrollArea)

        self.AddBatteryLayout = QVBoxLayout()
        self.AddBatteryLayout.setObjectName(u"AddBatteryLayout")
        self.AddBatteryLayout.setContentsMargins(9, -1, -1, -1)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.addBatteryButton = QPushButton(self.configurationTab)
        self.addBatteryButton.setObjectName(u"addBatteryButton")
        self.addBatteryButton.setMaximumSize(QSize(325, 16777215))

        self.horizontalLayout.addWidget(self.addBatteryButton)

        self.scanDevicesButton = QPushButton(self.configurationTab)
        self.scanDevicesButton.setObjectName(u"scanDevicesButton")
        self.scanDevicesButton.setMaximumSize(QSize(200, 16777215))

        self.horizontalLayout.addWidget(self.scanDevicesButton)


        self.AddBatteryLayout.addLayout(self.horizontalLayout)


        self.verticalLayout_2.addLayout(self.AddBatteryLayout)

        self.UserConfigureValidation = QFrame(self.configurationTab)
        self.UserConfigureValidation.setObjectName(u"UserConfigureValidation")
        self.UserConfigureValidation.setFrameShape(QFrame.Shape.StyledPanel)
        self.UserConfigureValidation.setFrameShadow(QFrame.Shadow.Raised)

        self.verticalLayout_2.addWidget(self.UserConfigureValidation)

        self.configureSticanButton = QPushButton(self.configurationTab)
        self.configureSticanButton.setObjectName(u"configureSticanButton")
        self.configureSticanButton.setMinimumSize(QSize(120, 0))

        self.verticalLayout_2.addWidget(self.configureSticanButton)

        self.tabWidget.addTab(self.configurationTab, "")
        self.advancedTab = QWidget()
        self.advancedTab.setObjectName(u"advancedTab")
        self.verticalLayout_3 = QVBoxLayout(self.advancedTab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.advConfigureOutput = QVBoxLayout()
        self.advConfigureOutput.setObjectName(u"advConfigureOutput")
        self.advConfigureOutputText = QTextBrowser(self.advancedTab)
        self.advConfigureOutputText.setObjectName(u"advConfigureOutputText")
        self.advConfigureOutputText.setMinimumSize(QSize(0, 150))

        self.advConfigureOutput.addWidget(self.advConfigureOutputText)


        self.verticalLayout_3.addLayout(self.advConfigureOutput)

        self.advComandLayout = QHBoxLayout()
        self.advComandLayout.setObjectName(u"advComandLayout")
        self.advInfoCommand = QTextBrowser(self.advancedTab)
        self.advInfoCommand.setObjectName(u"advInfoCommand")
        self.advInfoCommand.setMaximumSize(QSize(100, 30))

        self.advComandLayout.addWidget(self.advInfoCommand)

        self.advCommandText = QTextEdit(self.advancedTab)
        self.advCommandText.setObjectName(u"advCommandText")
        self.advCommandText.setMaximumSize(QSize(16777215, 30))

        self.advComandLayout.addWidget(self.advCommandText)

        self.advSendCommand = QPushButton(self.advancedTab)
        self.advSendCommand.setObjectName(u"advSendCommand")

        self.advComandLayout.addWidget(self.advSendCommand)

        self.advConnDbgCommand = QPushButton(self.advancedTab)
        self.advConnDbgCommand.setObjectName(u"advConnDbgCommand")

        self.advComandLayout.addWidget(self.advConnDbgCommand)


        self.verticalLayout_3.addLayout(self.advComandLayout)

        self.advButtons = QFrame(self.advancedTab)
        self.advButtons.setObjectName(u"advButtons")
        self.advButtons.setMinimumSize(QSize(0, 25))
        self.advButtons.setFrameShape(QFrame.Shape.StyledPanel)
        self.advButtons.setFrameShadow(QFrame.Shadow.Raised)
        self.advSaveLog = QPushButton(self.advButtons)
        self.advSaveLog.setObjectName(u"advSaveLog")
        self.advSaveLog.setGeometry(QRect(0, 0, 90, 25))
        self.advSaveLog.setMaximumSize(QSize(90, 25))

        self.verticalLayout_3.addWidget(self.advButtons)

        self.tabWidget.addTab(self.advancedTab, "")
        self.infoTab = QWidget()
        self.infoTab.setObjectName(u"infoTab")
        self.verticalLayout_4 = QVBoxLayout(self.infoTab)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.frame = QFrame(self.infoTab)
        self.frame.setObjectName(u"frame")
        self.frame.setMaximumSize(QSize(16777215, 20))
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.EN_Button = QPushButton(self.frame)
        self.EN_Button.setObjectName(u"EN_Button")
        self.EN_Button.setGeometry(QRect(660, 0, 51, 20))
        self.PL_Button = QPushButton(self.frame)
        self.PL_Button.setObjectName(u"PL_Button")
        self.PL_Button.setGeometry(QRect(710, 0, 51, 20))
        self.LanguageLabel = QLabel(self.frame)
        self.LanguageLabel.setObjectName(u"LanguageLabel")
        self.LanguageLabel.setGeometry(QRect(560, 0, 81, 18))

        self.verticalLayout_6.addWidget(self.frame)

        self.InfoLayout = QFormLayout()
        self.InfoLayout.setObjectName(u"InfoLayout")
        self.InfoLayout.setContentsMargins(3, 3, 3, 3)
        self.versionLabel = QLabel(self.infoTab)
        self.versionLabel.setObjectName(u"versionLabel")

        self.InfoLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.versionLabel)

        self.versionValueLabel = QLabel(self.infoTab)
        self.versionValueLabel.setObjectName(u"versionValueLabel")

        self.InfoLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.versionValueLabel)

        self.authorsLabel = QLabel(self.infoTab)
        self.authorsLabel.setObjectName(u"authorsLabel")

        self.InfoLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.authorsLabel)

        self.authorsValueLabel = QLabel(self.infoTab)
        self.authorsValueLabel.setObjectName(u"authorsValueLabel")

        self.InfoLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.authorsValueLabel)

        self.licenseLabel = QLabel(self.infoTab)
        self.licenseLabel.setObjectName(u"licenseLabel")

        self.InfoLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.licenseLabel)

        self.licenseValueLabel = QLabel(self.infoTab)
        self.licenseValueLabel.setObjectName(u"licenseValueLabel")

        self.InfoLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.licenseValueLabel)

        self.companyLabel = QLabel(self.infoTab)
        self.companyLabel.setObjectName(u"companyLabel")

        self.InfoLayout.setWidget(7, QFormLayout.ItemRole.LabelRole, self.companyLabel)

        self.companyValueLabel = QLabel(self.infoTab)
        self.companyValueLabel.setObjectName(u"companyValueLabel")

        self.InfoLayout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.companyValueLabel)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")

        self.InfoLayout.setLayout(10, QFormLayout.ItemRole.FieldRole, self.verticalLayout_5)


        self.verticalLayout_6.addLayout(self.InfoLayout)


        self.verticalLayout_4.addLayout(self.verticalLayout_6)

        self.creationNotice = QLabel(self.infoTab)
        self.creationNotice.setObjectName(u"creationNotice")
        self.creationNotice.setMaximumSize(QSize(16777215, 20))

        self.verticalLayout_4.addWidget(self.creationNotice)

        self.LicenseDisclaimer = QTextBrowser(self.infoTab)
        self.LicenseDisclaimer.setObjectName(u"LicenseDisclaimer")
        self.LicenseDisclaimer.setMaximumSize(QSize(16777215, 80))

        self.verticalLayout_4.addWidget(self.LicenseDisclaimer)

        self.copyrightNotice = QLabel(self.infoTab)
        self.copyrightNotice.setObjectName(u"copyrightNotice")
        self.copyrightNotice.setMaximumSize(QSize(16777215, 20))

        self.verticalLayout_4.addWidget(self.copyrightNotice)

        self.tabWidget.addTab(self.infoTab, "")

        self.verticalLayout.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"StiCAN Configurator", None))
        self.detectionStatusLabel.setText(QCoreApplication.translate("MainWindow", u"StiCAN Status: Unknown", None))
        self.detectedPortLabel.setText(QCoreApplication.translate("MainWindow", u"Port: N/A", None))
        self.Information1.setText(QCoreApplication.translate("MainWindow", u"Make sure you wrote correct PIN code!", None))
        self.Information2.setText(QCoreApplication.translate("MainWindow", u"StiCAN will not verify PIN code.", None))
        self.addBatteryButton.setText(QCoreApplication.translate("MainWindow", u"Add Battery", None))
        self.scanDevicesButton.setText(QCoreApplication.translate("MainWindow", u"Scan for devices", None))
        self.configureSticanButton.setText(QCoreApplication.translate("MainWindow", u"Configure", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.configurationTab), QCoreApplication.translate("MainWindow", u"Configuration", None))
        self.advInfoCommand.setHtml(QCoreApplication.translate("MainWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Ubuntu Sans'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Command:</p></body></html>", None))
        self.advSendCommand.setText(QCoreApplication.translate("MainWindow", u"Send", None))
        self.advConnDbgCommand.setText(QCoreApplication.translate("MainWindow", u"Connect", None))
        self.advSaveLog.setText(QCoreApplication.translate("MainWindow", u"SaveLog", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.advancedTab), QCoreApplication.translate("MainWindow", u"Advanced", None))
        self.EN_Button.setText(QCoreApplication.translate("MainWindow", u"EN", None))
        self.PL_Button.setText(QCoreApplication.translate("MainWindow", u"PL", None))
        self.LanguageLabel.setText(QCoreApplication.translate("MainWindow", u"Language:", None))
        self.versionLabel.setText(QCoreApplication.translate("MainWindow", u"Version:", None))
        self.authorsLabel.setText(QCoreApplication.translate("MainWindow", u"Authors:", None))
        self.licenseLabel.setText(QCoreApplication.translate("MainWindow", u"License:", None))
        self.companyLabel.setText(QCoreApplication.translate("MainWindow", u"Company:", None))
        self.creationNotice.setText(QCoreApplication.translate("MainWindow", u"Program created using Qt Creator", None))
        self.LicenseDisclaimer.setHtml(QCoreApplication.translate("MainWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Ubuntu Sans'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3 </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">This program is distr"
                        "ibuted in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details. </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">You should have received a copy of the GNU General Public License along with this program.  If not, see http://www.gnu.org/licenses/</span></p></body></html>", None))
        self.copyrightNotice.setText(QCoreApplication.translate("MainWindow", u"Copyright (C) 2024 Breeze Energies Sp. z o.o.", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.infoTab), QCoreApplication.translate("MainWindow", u"Info", None))
    # retranslateUi

