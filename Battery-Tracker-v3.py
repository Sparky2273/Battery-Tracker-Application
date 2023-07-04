import os
import sys
import wmi
import psutil
import pygame
import elevate
import sqlite3
import datetime
from PyQt5.QtGui import QIcon, QKeySequence, QFont
from PyQt5.QtCore import Qt, QTime, QTimer, QSettings
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QLabel,
    QSystemTrayIcon,
    QAction,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QGroupBox,
    QSlider,
    QFormLayout,
    QMainWindow,
    QShortcut,
    QCheckBox,
    QGridLayout,
    QToolBar,
    QAbstractItemView,
    QTextEdit,
)


class ProgramStatus:
    def __init__(self):
        self.statusFile = "program-status.db"
        self.conn = sqlite3.connect(self.statusFile)
        self.cursor = self.conn.cursor()
        self.initializeStatusTable()

    def initializeStatusTable(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS program_status (
            id INTEGER PRIMARY KEY,
            running INTEGER
        )
        """
        self.cursor.execute(create_table_query)
        self.conn.commit()

        select_query = """
        SELECT * FROM program_status WHERE id = 1
        """
        self.cursor.execute(select_query)
        result = self.cursor.fetchone()
        if not result:
            insert_query = """
            INSERT INTO program_status (id, running) VALUES (?, ?)
            """
            values = (1, 0)
            self.cursor.execute(insert_query, values)
            self.conn.commit()

    def startProgram(self):
        update_query = """
        UPDATE program_status SET running = ? WHERE id = ?
        """
        values = (1, 1)
        self.cursor.execute(update_query, values)
        self.conn.commit()

    def stopProgram(self):
        update_query = """
        UPDATE program_status SET running = ? WHERE id = ?
        """
        values = (0, 1)
        self.cursor.execute(update_query, values)
        self.conn.commit()

    def isRunning(self):
        select_query = """
        SELECT running FROM program_status WHERE id = ?
        """
        values = (1,)
        self.cursor.execute(select_query, values)
        result = self.cursor.fetchone()
        if result:
            return bool(result[0])
        return False


class SettingsStatus:
    def __init__(self):
        self.settingsFile = "program-settings.db"
        self.conn = sqlite3.connect(self.settingsFile)
        self.cursor = self.conn.cursor()
        self.initializeSettingsTable()
        self.loadSettings()

    def initializeSettingsTable(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            batteryCare INTEGER,
            batteryCareNotif INTEGER,
            startAtStartup INTEGER,
            startMinimize INTEGER,
            resetTimesAfterBatteryStatusChsnged INTEGER
        )
        """
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def loadSettings(self):
        select_query = """
        SELECT * FROM settings WHERE id = 1
        """
        self.cursor.execute(select_query)
        result = self.cursor.fetchone()
        if result:
            (
                _id,
                batteryCare,
                batteryCareNotif,
                startAtStartup,
                startMinimize,
                resetTimesAfterBatteryStatusChsnged,
            ) = result
            self.batteryCare = {"batteryCare": bool(batteryCare)}
            self.batteryCareNotif = {"batteryCareNotif": bool(batteryCareNotif)}
            self.startAtStartup = {"startAtStartup": bool(startAtStartup)}
            self.startMinimize = {"startMinimize": bool(startMinimize)}
            self.resetTimesAfterBatteryStatusChsnged = {
                "resetTimesAfterBatteryStatusChsnged": bool(
                    resetTimesAfterBatteryStatusChsnged
                )
            }
        else:
            self.batteryCare = {"batteryCare": True}
            self.batteryCareNotif = {"batteryCareNotif": True}
            self.startAtStartup = {"startAtStartup": False}
            self.startMinimize = {"startMinimize": True}
            self.resetTimesAfterBatteryStatusChsnged = {
                "resetTimesAfterBatteryStatusChsnged": True
            }
            self.saveSettings()

    def saveSettings(self):
        update_query = """
        INSERT OR REPLACE INTO settings (
            id,
            batteryCare,
            batteryCareNotif,
            startAtStartup,
            startMinimize,
            resetTimesAfterBatteryStatusChsnged
        ) VALUES (?, ?, ?, ?, ?, ?)
        """
        values = (
            1,
            self.batteryCare["batteryCare"],
            self.batteryCareNotif["batteryCareNotif"],
            self.startAtStartup["startAtStartup"],
            self.startMinimize["startMinimize"],
            self.resetTimesAfterBatteryStatusChsnged[
                "resetTimesAfterBatteryStatusChsnged"
            ],
        )
        self.cursor.execute(update_query, values)
        self.conn.commit()

    def setBatteryCare(self, value):
        self.batteryCare = {"batteryCare": value}
        self.saveSettings()

    def getBatteryCare(self):
        self.loadSettings()
        return self.batteryCare["batteryCare"]

    def setBatteryCareNotif(self, value):
        self.batteryCareNotif = {"batteryCareNotif": value}
        self.saveSettings()

    def getBatteryCareNotif(self):
        self.loadSettings()
        return self.batteryCareNotif["batteryCareNotif"]

    def setStartAtStartup(self, value):
        self.startAtStartup = {"startAtStartup": value}
        self.saveSettings()

    def getStartAtStartup(self):
        self.loadSettings()
        return self.startAtStartup["startAtStartup"]

    def setStartMinimize(self, value):
        self.startMinimize = {"startMinimize": value}
        self.saveSettings()

    def getStartMinimize(self):
        self.loadSettings()
        return self.startMinimize["startMinimize"]

    def setResetTimesAfterBatteryStatusChsnged(self, value):
        self.resetTimesAfterBatteryStatusChsnged = {
            "resetTimesAfterBatteryStatusChsnged": value
        }
        self.saveSettings()

    def getResetTimesAfterBatteryStatusChsnged(self):
        self.loadSettings()
        return self.resetTimesAfterBatteryStatusChsnged[
            "resetTimesAfterBatteryStatusChsnged"
        ]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.appTitle = "Battery Tracker"
        self.appVersion = "3.0"
        self.appSize = 605, 640
        self.appStartPoint = 250, 150
        self.appIcon = QIcon("main-window.ico")

        self.prevPercent = None
        self.timeZero = "0:00:00"
        self.percentZero = "0%"
        self.batteryRemaining = None

        self.settingsStatus = SettingsStatus()

        self.startTime = datetime.datetime.now()
        self.totalInUseTime = datetime.timedelta()
        self.totalBatteryTime = datetime.timedelta()
        self.totalPluggedInTime = datetime.timedelta()

        self.initUI()
        self.updateStatus()
        self.updateTimes()
        self.updateBattery()

    def initUI(self):
        self.setGeometry(*self.appStartPoint, *self.appSize)
        self.setWindowTitle(self.appTitle)
        self.setWindowIcon(self.appIcon)
        self.setWindowFlags(
            self.windowFlags()
            & ~(
                Qt.WindowMinimizeButtonHint
                | Qt.WindowMaximizeButtonHint
                | Qt.WindowCloseButtonHint
            )
        )

        menubar = QMenuBar()

        helpMenu = QMenu("Help", self)
        menubar.addMenu(helpMenu)

        aboutAction = QAction("About", self)
        aboutAction.setShortcut("Ctrl+A")
        aboutAction.triggered.connect(self.aboutMessageBox)
        helpMenu.addAction(aboutAction)

        helpMenu.addSeparator()

        manualAction = QAction("Manual", self)
        manualAction.setShortcut("Ctrl+B")
        manualAction.triggered.connect(self.manual)
        helpMenu.addAction(manualAction)

        resetMenu = QMenu("Reset", self)
        menubar.addMenu(resetMenu)

        totalTimeResetAction = QAction("TotalTime", self)
        totalTimeResetAction.setShortcut("Ctrl+Z")
        totalTimeResetAction.triggered.connect(self.totalTimeReset)
        resetMenu.addAction(totalTimeResetAction)

        totalBatteryTimeResetAction = QAction("BatteryTime", self)
        totalBatteryTimeResetAction.setShortcut("Ctrl+X")
        totalBatteryTimeResetAction.triggered.connect(self.totalBatteryTimeReset)
        resetMenu.addAction(totalBatteryTimeResetAction)

        totalPluggedInTimeResetAction = QAction("PluggedInTime", self)
        totalPluggedInTimeResetAction.setShortcut("Ctrl+V")
        totalPluggedInTimeResetAction.triggered.connect(self.totalPluggedInTimeReset)
        resetMenu.addAction(totalPluggedInTimeResetAction)

        tableWidgetResetAction = QAction("TableWidget", self)
        tableWidgetResetAction.setShortcut("Ctrl+D")
        tableWidgetResetAction.triggered.connect(self.tableWidgetReset)
        resetMenu.addAction(tableWidgetResetAction)

        resetMenu.addSeparator()

        allResetAction = QAction("All", self)
        allResetAction.setShortcut("Ctrl+R")
        allResetAction.triggered.connect(self.allReset)
        resetMenu.addAction(allResetAction)

        self.setMenuBar(menubar)

        toolbar = QToolBar()

        toolbar.setStyleSheet(
            """
            QToolBar {
                background-color: #f5f5f5;
                border: none;
                spacing: 5px;
                padding: 2px;
            }

            QToolButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }

            QToolButton:hover {
                background-color: #e0e0e0;
            }

            QToolButton:pressed {
                background-color: #d0d0d0;
            }
        """
        )

        settingsAction = QAction(QIcon("settings-window.png"), "Settings", self)
        toolbar.addAction(settingsAction)
        settingsAction.triggered.connect(self.settings)

        self.addToolBar(toolbar)

        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setToolTip(self.appTitle)
        self.trayIcon.setIcon(self.appIcon)
        self.trayIcon.activated.connect(self.trayIconActivated)

        trayMenu = QMenu()

        batteryCareMenu = QMenu("Battery Care", self)
        trayMenu.addMenu(batteryCareMenu)

        self.batteryCareOnAction = QAction("On", self)
        self.batteryCareOnAction.triggered.connect(self.batteryCareOn)
        batteryCareMenu.addAction(self.batteryCareOnAction)

        self.batteryCareOffAction = QAction("Off", self)
        self.batteryCareOffAction.triggered.connect(self.batteryCareOff)
        batteryCareMenu.addAction(self.batteryCareOffAction)

        trayMenu.addSeparator()

        restoreAction = QAction("Restore", self)
        restoreAction.triggered.connect(self.restoreTry)
        trayMenu.addAction(restoreAction)

        minimizeAction = QAction("Minimize", self)
        minimizeAction.triggered.connect(self.hide)
        trayMenu.addAction(minimizeAction)

        trayMenu.addSeparator()

        closeAction = QAction("Close", self)
        closeAction.triggered.connect(self.close)
        trayMenu.addAction(closeAction)

        self.trayIcon.setContextMenu(trayMenu)

        self.trayIcon.show()

        settingsWindowShortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        settingsWindowShortcut.activated.connect(self.settings)

        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels(
            ["Time", "Percentage", "Status", "Remaining"]
        )
        self.tableWidget.setStyleSheet("QTableWidget {alignment: center;}")
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setStyleSheet(
            """
            QTableWidget {
                background-color: #f5f5f5;
                alternate-background-color: #e0e0e0;
                border: none;
                gridline-color: #d0d0d0;
                selection-background-color: #a0a0a0;
                selection-color: #ffffff;
            }
        """
        )

        batteryLabel = QLabel("On battery power on time:")
        self.batteryTimeLabel = QLabel(self.timeZero)

        pluggedInLabel = QLabel("Plugged in power on time:")
        self.pluggedInTimeLabel = QLabel(self.timeZero)

        totalInUseLabel = QLabel("Total in use time:")
        self.totalInUseTimeLabel = QLabel(self.timeZero)

        batteryRemainingLabel = QLabel("Remaining Battery Time:")
        self.batteryRemainingTimeLabel = QLabel(self.timeZero)

        batteryLevelLabel = QLabel("Battery Level:")
        self.batteryLevelPercentLabel = QLabel(self.percentZero)

        brightnessLevelLabel = QLabel("Brightness Level:")
        self.brightnessLevelPercentLabel = QLabel(self.percentZero)

        self.brightnessSlider = QSlider(Qt.Horizontal)
        self.brightnessSlider.setRange(10, 80)
        self.brightnessSlider.setPageStep(5)
        self.brightnessSlider.valueChanged.connect(self.updateBrightness)

        minimizeToTrayButton = QPushButton("Minimize to Tray")
        minimizeToTrayButton.setShortcut("Ctrl+M")
        minimizeToTrayButton.clicked.connect(self.hide)

        closeButton = QPushButton("Close")
        closeButton.setShortcut("Ctrl+C")
        closeButton.clicked.connect(self.close)

        batteryRecordGroupbox = QGroupBox("Battery Record")
        batteryRecordLayout = QVBoxLayout(batteryRecordGroupbox)
        batteryRecordLayout.addWidget(self.tableWidget)

        batteryInfoGroupbox = QGroupBox("Battery Info")
        batteryInfoLayout = QFormLayout(batteryInfoGroupbox)
        batteryInfoLayout.addRow(batteryLabel, self.batteryTimeLabel)
        batteryInfoLayout.addRow(pluggedInLabel, self.pluggedInTimeLabel)
        batteryInfoLayout.addRow(totalInUseLabel, self.totalInUseTimeLabel)
        batteryInfoLayout.addRow(batteryRemainingLabel, self.batteryRemainingTimeLabel)
        batteryInfoLayout.addRow(batteryLevelLabel, self.batteryLevelPercentLabel)
        batteryInfoLayout.addRow(brightnessLevelLabel, self.brightnessLevelPercentLabel)
        batteryInfoLayout.addRow(self.brightnessSlider)

        windowButtonGroupbox = QGroupBox("Window Button")
        windowButtonLayout = QVBoxLayout(windowButtonGroupbox)
        windowButtonLayout.addWidget(minimizeToTrayButton)
        windowButtonLayout.addWidget(closeButton)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(batteryRecordGroupbox)
        mainLayout.addWidget(batteryInfoGroupbox)
        mainLayout.addWidget(windowButtonGroupbox)

        widget = QWidget()
        widget.setLayout(mainLayout)
        self.setCentralWidget(widget)

    def batteryCareOn(self):
        self.settingsStatus.setBatteryCare(True)
        self.settingsStatus.saveSettings()

    def batteryCareOff(self):
        self.settingsStatus.setBatteryCare(False)
        self.settingsStatus.saveSettings()

    def startAtStartup(self, state):
        if state:
            settings = QSettings(
                "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run",
                QSettings.NativeFormat,
            )
            path = os.path.abspath(sys.argv[0])
            settings.setValue(self.appTitle, path)

    def manual(self):
        self.manualWindow = ManualWindow()
        if self.manualWindow.isHidden():
            self.manualWindow.show()

    def settings(self):
        self.settingsWindow = SettingsWindow()
        if self.settingsWindow.isHidden():
            self.settingsWindow.show()

    def restoreTry(self):
        self.showNormal()
        self.activateWindow()

    def trayIconActivated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isHidden():
                self.showNormal()
                self.activateWindow()
            else:
                self.hide()

    def updateBrightness(self):
        brightnessLevel = self.brightnessSlider.value()
        self.brightnessLevelPercentLabel.setText(f"{brightnessLevel}%")
        self.setBrightnessLevel(brightnessLevel)

    def setBrightnessLevel(self, level):
        c = wmi.WMI(namespace="wmi")
        methods = c.WmiMonitorBrightnessMethods()[0]
        methods.WmiSetBrightness(level, 0)

    def getBrightnessLevel(self):
        c = wmi.WMI(namespace="wmi")
        currentLevel = c.WmiMonitorBrightness()[0].CurrentBrightness
        return currentLevel

    def formatTime(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} H : {minutes} Min"

    def totalTimeReset(self):
        self.totalInUseTime = datetime.timedelta()
        self.totalInUseTimeLabel.setText(self.timeZero)

    def totalBatteryTimeReset(self):
        self.totalBatteryTime = datetime.timedelta()
        self.batteryTimeLabel.setText(self.timeZero)

    def totalPluggedInTimeReset(self):
        self.totalPluggedInTime = datetime.timedelta()
        self.pluggedInTimeLabel.setText(self.timeZero)

    def tableWidgetReset(self):
        self.tableWidget.setRowCount(0)

    def allReset(self):
        self.totalTimeReset()
        self.totalBatteryTimeReset()
        self.totalPluggedInTimeReset()
        self.tableWidgetReset()

    def aboutMessageBox(self):
        aboutText = f"""Battery Tracker: Monitor and optimize your Windows battery life with real-time updates, usage stats, and helpful notifications.
        \nVersion: {self.appVersion}
        \nDeveloper: Sparky
        \nCompany: SPARKS
        \nContact: Sparky#2273 on Discord or Sparky2273 on Telegram"""
        QMessageBox.about(self, "About", aboutText)

    def showNotification(self, status):
        if self.settingsStatus.getBatteryCareNotif():
            if status == "Plugg":
                self.trayIcon.showMessage(
                    "Plugged In",
                    "Please connect the charger.",
                    QSystemTrayIcon.Critical,
                )
            elif status == "UnPlugg":
                self.trayIcon.showMessage(
                    "Unplugged",
                    "Please disconnect the charger.",
                    QSystemTrayIcon.Warning,
                )

    def updateStatus(self):
        if self.settingsStatus.getBatteryCare():
            battery = psutil.sensors_battery()
            percent = battery.percent
            plugged = battery.power_plugged

            if percent < 21 and not plugged:
                pluggSoundFile = "stop.wav"
                pygame.mixer.init()
                pygame.mixer.music.load(pluggSoundFile)
                pygame.mixer.music.play()
                self.showNotification("Plugg")

            elif percent > 90 and plugged:
                unpluggSoundFile = "ding.wav"
                pygame.mixer.init()
                pygame.mixer.music.load(unpluggSoundFile)
                pygame.mixer.music.play()
                self.showNotification("UnPlugg")

        QTimer.singleShot(2 * 1000, self.updateStatus)

    def updateTimes(self):
        battery = psutil.sensors_battery()
        percent = battery.percent
        plugged = battery.power_plugged

        if plugged:
            self.batteryRemaining = "Charging"
            self.batteryRemainingTimeLabel.setText("Charging")
        else:
            if percent == 100:
                self.batteryRemaining = "Fully Charged"
                self.batteryRemainingTimeLabel.setText("Fully Charged")
            else:
                self.batteryRemaining = self.formatTime(battery.secsleft)
                self.batteryRemainingTimeLabel.setText(self.batteryRemaining)

        brightnessLevel = self.getBrightnessLevel()
        self.brightnessSlider.setValue(brightnessLevel)

        self.batteryLevelPercentLabel.setText(f"{percent}%")
        self.brightnessLevelPercentLabel.setText(f"{brightnessLevel}%")

        currentTime = datetime.datetime.now()
        elapsedTime = currentTime - self.startTime

        self.totalInUseTime += elapsedTime
        timeFormat = str(self.totalInUseTime).split(".")[0]
        self.totalInUseTimeLabel.setText(str(timeFormat))

        if psutil.sensors_battery().power_plugged:
            self.totalPluggedInTime += elapsedTime
            timeFormat = str(self.totalPluggedInTime).split(".")[0]
            self.pluggedInTimeLabel.setText(str(timeFormat))

            if self.settingsStatus.getResetTimesAfterBatteryStatusChsnged():
                if not str(self.batteryTimeLabel.textFormat()) == self.timeZero:
                    self.totalBatteryTimeReset()

        else:
            self.totalBatteryTime += elapsedTime
            timeFormat = str(self.totalBatteryTime).split(".")[0]
            self.batteryTimeLabel.setText(str(timeFormat))

            if self.settingsStatus.getResetTimesAfterBatteryStatusChsnged():
                if not str(self.pluggedInTimeLabel.textFormat()) == self.timeZero:
                    self.totalPluggedInTimeReset()

        self.startTime = currentTime

        QTimer.singleShot(1 * 1000, self.updateTimes)

    def updateBattery(self):
        battery = psutil.sensors_battery()
        percent = battery.percent
        plugged = battery.power_plugged
        currentTime = QTime.currentTime().toString("HH:mm")

        if percent != self.prevPercent:
            rowPosition = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowPosition)

            timeItem = QTableWidgetItem(currentTime)
            timeItem.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(rowPosition, 0, timeItem)

            percentItem = QTableWidgetItem(str(percent) + "%")
            percentItem.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(rowPosition, 1, percentItem)

            statusItem = QTableWidgetItem("Plugged" if plugged else "Unplugged")
            statusItem.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(rowPosition, 2, statusItem)

            remainingItem = QTableWidgetItem(self.batteryRemaining)
            remainingItem.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(rowPosition, 3, remainingItem)

            self.prevPercent = percent

        QTimer.singleShot(1 * 1000, self.updateBattery)

    def closeEvent(self, event):
        programStatus = ProgramStatus()
        programStatus.stopProgram()
        sys.exit(1)


class SettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settingsStatus = SettingsStatus()

        self.initUI()
        self.batteryCareCheckBoxStatus()

    def initUI(self):
        self.setWindowTitle("Settings")
        self.setGeometry(950, 150, 300, 200)
        self.setWindowIcon(QIcon("settings-window.png"))
        self.setWindowFlags(
            self.windowFlags()
            & ~(
                Qt.WindowMinimizeButtonHint
                | Qt.WindowMaximizeButtonHint
                | Qt.WindowCloseButtonHint
            )
        )

        batteryCareLabel = QLabel("Battery Care:")

        self.batteryCareCheckBox = QCheckBox("State")
        self.batteryCareCheckBox.setChecked(self.settingsStatus.getBatteryCare())
        self.batteryCareCheckBox.clicked.connect(self.batteryCareCheckBoxStatus)

        self.batteryCareNotifCheckBox = QCheckBox("Notif")
        self.batteryCareNotifCheckBox.setChecked(
            self.settingsStatus.getBatteryCareNotif()
        )

        startLabel = QLabel("Start:")

        self.startMinimizeCheckBox = QCheckBox("Start Minimize")
        self.startMinimizeCheckBox.setChecked(self.settingsStatus.getStartMinimize())

        self.startAtStartupCheckBox = QCheckBox("Start at Startup")
        self.startAtStartupCheckBox.setChecked(self.settingsStatus.getStartAtStartup())

        resetTimesAfterBatteryStatusChsngedLabel = QLabel(
            "Reset Times After Battery Status Chsnged:"
        )

        self.resetTimesAfterBatteryStatusChsngedCheckBox = QCheckBox("State")
        self.resetTimesAfterBatteryStatusChsngedCheckBox.setChecked(
            self.settingsStatus.getResetTimesAfterBatteryStatusChsnged()
        )

        applyButton = QPushButton("Apply")
        exitButton = QPushButton("Exit")
        exitButton.clicked.connect(self.close)
        applyButton.clicked.connect(self.applySettings)

        controlGroupbox = QGroupBox("Control")
        controlLayout = QGridLayout(controlGroupbox)
        controlLayout.addWidget(applyButton)
        controlLayout.addWidget(exitButton)

        settingsGroupbox = QGroupBox("Settings")
        settingsLayout = QGridLayout(settingsGroupbox)
        settingsLayout.addWidget(batteryCareLabel, 0, 0)
        settingsLayout.addWidget(self.batteryCareCheckBox, 0, 1)
        settingsLayout.addWidget(self.batteryCareNotifCheckBox, 0, 2)
        settingsLayout.addWidget(startLabel, 1, 0)
        settingsLayout.addWidget(self.startMinimizeCheckBox, 1, 1)
        settingsLayout.addWidget(self.startAtStartupCheckBox, 1, 2)
        settingsLayout.addWidget(resetTimesAfterBatteryStatusChsngedLabel, 2, 0)
        settingsLayout.addWidget(self.resetTimesAfterBatteryStatusChsngedCheckBox, 2, 1)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(settingsGroupbox)
        mainLayout.addWidget(controlGroupbox)

        widget = QWidget()
        widget.setLayout(mainLayout)
        self.setCentralWidget(widget)

    def batteryCareCheckBoxStatus(self):
        if self.batteryCareCheckBox.isChecked():
            self.batteryCareNotifCheckBox.setEnabled(True)
        else:
            self.batteryCareNotifCheckBox.setChecked(False)
            self.batteryCareNotifCheckBox.setDisabled(True)

    def startAtStartupConfigure(self, state):
        settings = QSettings(
            "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run",
            QSettings.NativeFormat,
        )

        if state:
            path = os.path.abspath(sys.argv[0])
            settings.setValue("Battery Tracker", path)
        else:
            settings.remove("Battery Tracker")

    def applySettings(self):
        batteryCareValue = self.batteryCareCheckBox.isChecked()
        self.settingsStatus.setBatteryCare(batteryCareValue)

        batteryCareNotifValue = self.batteryCareNotifCheckBox.isChecked()
        self.settingsStatus.setBatteryCareNotif(batteryCareNotifValue)

        startMinimizeValue = self.startMinimizeCheckBox.isChecked()
        self.settingsStatus.setStartMinimize(startMinimizeValue)

        startAtStartupValue = self.startAtStartupCheckBox.isChecked()
        self.startAtStartupConfigure(startAtStartupValue)
        self.settingsStatus.setStartAtStartup(startAtStartupValue)

        resetTimesAfterBatteryStatusChsngedValue = (
            self.resetTimesAfterBatteryStatusChsngedCheckBox.isChecked()
        )
        self.settingsStatus.setResetTimesAfterBatteryStatusChsnged(
            resetTimesAfterBatteryStatusChsngedValue
        )

        self.settingsStatus.saveSettings()

        QMessageBox.information(
            self, "Apply", "The new settings have been successfully applied."
        )


class ManualWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Battery Tracker Manual")
        self.setGeometry(950, 225, 800, 600)
        self.setWindowIcon(QIcon("manual-window.png"))

        self.textEdit = QTextEdit(self)
        self.textEdit.setFont(QFont("Arial", 12))
        self.textEdit.setReadOnly(True)
        self.textEdit.setLineWrapMode(QTextEdit.NoWrap)
        self.textEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.textEdit.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.textEdit.setHtml(
            """
            <h1 style="font-weight: bold;">Battery Tracker Manual</h1>
            <p style="font-size: 14px;">Thank you for using Battery Tracker! This manual provides a detailed explanation of the features and functionality of the application.</p>
            <hr style="border: none; border-top: 1px solid #ccc; margin: 10px 0px;">

            <h2 style="font-weight: bold;">Table of Contents</h2>
            <ol style="font-size: 14px;">
                <li>Introduction</li>
                <li>Main Window
                    <ul>
                        <li>Battery Record</li>
                        <li>Battery Info</li>
                        <li>Window Buttons</li>
                    </ul>
                </li>
                <li>Settings Window</li>
                <li>System Tray Icon</li>
                <li>Shortcuts</li>
            </ol>

            <h2 style="font-weight: bold;">1. Introduction</h2>
            <p style="font-size: 14px;">Battery Tracker is a modern and professional PyQt application designed to track battery usage and provide useful information about battery status and usage time. It helps you monitor your battery life and optimize usage for better battery health.</p>

            <h2 style="font-weight: bold;">2. Main Window</h2>
            <p style="font-size: 14px;">The main window of Battery Tracker provides various features and information related to battery usage.</p>

            <h3 style="font-weight: bold;">Battery Record</h3>
            <p style="font-size: 14px;">The Battery Record section displays a table with the following columns:</p>
            <ul style="font-size: 14px;">
                <li>Time: The time when the battery status was recorded.</li>
                <li>Percentage: The battery level as a percentage.</li>
                <li>Status: The current status of the battery (charging, discharging, or fully charged).</li>
                <li>Remaining: The estimated time remaining for the battery to be fully discharged or charged.</li>
            </ul>

            <h3 style="font-weight: bold;">Battery Info</h3>
            <p style="font-size: 14px;">The Battery Info section displays the following information:</p>
            <ul style="font-size: 14px;">
                <li>On battery power on time: The total time since the battery was last fully charged while on battery power.</li>
                <li>Plugged in power on time: The total time since the battery was last fully charged while plugged in.</li>
                <li>Total in use time: The total time the battery has been in use.</li>
                <li>Remaining Battery Time: The estimated time remaining for the battery to be fully discharged or charged.</li>
                <li>Battery Level: The current battery level as a percentage.</li>
                <li>Brightness Level: The current brightness level of the display.</li>
            </ul>

            <h3 style="font-weight: bold;">Window Buttons</h3>
            <p style="font-size: 14px;">The Window Buttons section provides the following options:</p>
            <ul style="font-size: 14px;">
                <li>Minimize to Tray: Minimizes the application to the system tray for easy access.</li>
                <li>Close: Closes the application.</li>
            </ul>

            <h2 style="font-weight: bold;">3. Settings Window</h2>
            <p style="font-size: 14px;">The Settings Window allows you to customize various settings related to Battery Tracker.</p>

            <h2 style="font-weight: bold;">4. System Tray Icon</h2>
            <p style="font-size: 14px;">The system tray icon provides quick access to essential functions of Battery Tracker. Right-clicking the system tray icon opens a menu with the following options:</p>
            <ul style="font-size: 14px;">
                <li>Battery Care: Allows you to enable or disable battery care mode.</li>
                <li>Restore: Restores the main window if it is minimized or hidden.</li>
                <li>Minimize: Minimizes the main window to the system tray.</li>
                <li>Close: Closes the application.</li>
            </ul>

            <h2 style="font-weight: bold;">5. Shortcuts</h2>
            <p style="font-size: 14px;">Battery Tracker provides the following keyboard shortcuts for quick access to specific functions:</p>
            <ul style="font-size: 14px;">
                <li>Ctrl+A: Opens the 'About' dialog box.</li>
                <li>Ctrl+B: Opens the manual.</li>
                <li>Ctrl+S: Opens the settings window.</li>
                <li>Ctrl+M: Minimizes the main window to the system tray.</li>
                <li>Ctrl+C: Closes the application.</li>
                <li>Ctrl+Z: Resets the total in-use time.</li>
                <li>Ctrl+X: Resets the total battery time.</li>
                <li>Ctrl+V: Resets the total plugged-in time.</li>
                <li>Ctrl+D: Resets the table widget.</li>
                <li>Ctrl+R: Resets all records.</li>
            </ul>

            <p style="font-size: 14px;">Note: Shortcut keys are available for Windows-based systems. On other operating systems, use the corresponding key combinations.</p>

            <p style="font-size: 14px;">That concludes the manual for Battery Tracker. If you have any further questions or need assistance, please refer to the application's documentation or contact our support team. Enjoy using Battery Tracker to monitor and optimize your battery usage!</p>
        """
        )

        self.setCentralWidget(self.textEdit)


def main():
    elevate.elevate()
    programStatus = ProgramStatus()

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication([])
    app.setStyle("Fusion")

    if not programStatus.isRunning():
        programStatus.startProgram()

        mainWindow = MainWindow()
        app.setApplicationVersion(mainWindow.appVersion)

        settingsStatus = SettingsStatus()
        if not settingsStatus.getStartMinimize():
            mainWindow.showNormal()
            mainWindow.activateWindow()

        app.exec_()

    else:
        message = QWidget()
        QMessageBox.warning(message, "Error", "The program is already running.")
        sys.exit(1)


if __name__ == "__main__":
    main()
