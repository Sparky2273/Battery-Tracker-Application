import os
import sys
import wmi
import json
import psutil
import pygame
import elevate
import datetime
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QTime, QTimer, QSettings
from PyQt5.QtWidgets import (
    QMenu,
    QLabel,
    QSlider,
    QWidget,
    QSlider,
    QAction,
    QMenuBar,
    QTextEdit,
    QGroupBox,
    QComboBox,
    QHeaderView,
    QPushButton,
    QMessageBox,
    QFormLayout,
    QMainWindow,
    QGridLayout,
    QVBoxLayout,
    QTextBrowser,
    QTableWidget,
    QApplication,
    QSystemTrayIcon,
    QTableWidgetItem,
    QAbstractItemView,
)


class Entities:
    appStyle = "Fusion"
    appName = "Battery Tracker"
    appVersion = "3.1"
    appIcon = "main-window-icon.ico"

    pluggSound = "stop-sound.wav"
    unpluggSound = "ding-sound.wav"

    mainWindowName = "Battery Tracker - Main"
    mainWindowStartPoint = 250, 150
    mainWindowSize = 600, 600
    mainWindowIcon = "main-window-icon.ico"

    batteryCareIcon = "battery-care-icon.ico"
    restoreIcon = "restore-icon.ico"
    minimizeIcon = "minimize-icon.ico"
    resetIcon = "reset-icon.ico"
    aboutIcon = "about-icon.ico"
    closeIcon = "close-icon.ico"

    settingsWindowName = "Battery Tracker - Settings"
    settingsWindowStartPoint = 950, 150
    settingsWindowSize = 300, 200
    settingsWindowIcon = "settings-window-icon"

    manualWindowName = "Battery Tracker - Manual"
    manualWindowStartPoint = 950, 225
    manualWindowSize = 800, 600
    manualWindowIcon = "manual-window-icon"

    globalStyleSheet = """
        color: white;
        background-color: #2c3e50;
    """

    menueStyleSheet = """
        QMenu {
            background-color: #34495e;
            border: 1px solid #2c3e50;
            padding: 5px;
            color: white;
        }

        QMenu::item {
            padding: 5px 25px;
        }

        QMenu::item:selected {
            background-color: #2c3e50;
        }

        QMenu::separator {
            height: 2px;
            background-color: #2c3e50;
            margin: 5px 0;
        }
    """


class SettingsStatus:
    def __init__(self):
        self.settingsFile = "program-settings.json"
        self.loadSettings()

    def loadSettings(self):
        try:
            with open(self.settingsFile, "r") as file:
                settings_data = json.load(file)
            self.batteryCare = settings_data.get("batteryCare", True)
            self.batteryCareNotif = settings_data.get("batteryCareNotif", True)
            self.startAtStartup = settings_data.get("startAtStartup", False)
            self.startMinimize = settings_data.get("startMinimize", True)
            self.resetTimesAfterBatteryStatusChsnged = settings_data.get(
                "resetTimesAfterBatteryStatusChsnged", True
            )
        except FileNotFoundError:
            self.batteryCare = True
            self.batteryCareNotif = True
            self.startAtStartup = False
            self.startMinimize = True
            self.resetTimesAfterBatteryStatusChsnged = True
            self.saveSettings()

    def saveSettings(self):
        settings_data = {
            "batteryCare": self.batteryCare,
            "batteryCareNotif": self.batteryCareNotif,
            "startAtStartup": self.startAtStartup,
            "startMinimize": self.startMinimize,
            "resetTimesAfterBatteryStatusChsnged": self.resetTimesAfterBatteryStatusChsnged,
        }
        with open(self.settingsFile, "w") as file:
            json.dump(settings_data, file, indent=4)

    def setBatteryCare(self, value):
        self.batteryCare = value
        self.saveSettings()

    def getBatteryCare(self):
        self.loadSettings()
        return self.batteryCare

    def setBatteryCareNotif(self, value):
        self.batteryCareNotif = value
        self.saveSettings()

    def getBatteryCareNotif(self):
        self.loadSettings()
        return self.batteryCareNotif

    def setStartAtStartup(self, value):
        self.startAtStartup = value
        self.saveSettings()

    def getStartAtStartup(self):
        self.loadSettings()
        return self.startAtStartup

    def setStartMinimize(self, value):
        self.startMinimize = value
        self.saveSettings()

    def getStartMinimize(self):
        self.loadSettings()
        return self.startMinimize

    def setResetTimesAfterBatteryStatusChsnged(self, value):
        self.resetTimesAfterBatteryStatusChsnged = value
        self.saveSettings()

    def getResetTimesAfterBatteryStatusChsnged(self):
        self.loadSettings()
        return self.resetTimesAfterBatteryStatusChsnged


class CustomTableWidget(QTableWidget):
    def __init__(self):
        super().__init__()
        self.resizeEvent = self.customResizeEvent

    def customResizeEvent(self, event):
        self.resizeColumnsToContents()
        header = self.horizontalHeader()
        table_width = self.viewport().width()
        total_width = header.length()
        if total_width < table_width:
            header.setSectionResizeMode(QHeaderView.Stretch)
        else:
            header.setSectionResizeMode(QHeaderView.Interactive)

        return super().resizeEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.entities = Entities()

        self.settingsStatus = SettingsStatus()

        self.close_on_exit = False

        self.prevPercent = None
        self.timeZero = "0:00:00"
        self.percentZero = "0%"
        self.batteryRemaining = None

        self.startTime = datetime.datetime.now()
        self.totalInUseTime = datetime.timedelta()
        self.totalBatteryTime = datetime.timedelta()
        self.totalPluggedInTime = datetime.timedelta()

        self.initUI()
        self.updateStatus()
        self.updateTimes()
        self.updateBattery()

    def initUI(self):
        self.setWindowTitle(self.entities.mainWindowName)
        self.setStyleSheet(self.entities.globalStyleSheet)
        self.setWindowIcon(QIcon(self.entities.mainWindowIcon))
        self.setGeometry(
            *self.entities.mainWindowStartPoint, *self.entities.mainWindowSize
        )

        menubar = QMenuBar()

        menubar.setStyleSheet(self.entities.menueStyleSheet)

        appMenu = QMenu("App", self)
        menubar.addMenu(appMenu)

        settingsAction = QAction("Settings", self)
        settingsAction.setShortcut("Ctrl+S")
        settingsAction.setIcon(QIcon(self.entities.settingsWindowIcon))
        settingsAction.triggered.connect(self.settings)
        appMenu.addAction(settingsAction)

        appMenu.addSeparator()

        exitAction = QAction("Exit", self)
        exitAction.setShortcut("Ctrl+E")
        exitAction.setIcon(QIcon(self.entities.closeIcon))
        exitAction.triggered.connect(self.close_window)
        appMenu.addAction(exitAction)

        helpMenu = QMenu("Help", self)
        menubar.addMenu(helpMenu)

        aboutAction = QAction("About", self)
        aboutAction.setShortcut("Ctrl+A")
        aboutAction.setIcon(QIcon(self.entities.aboutIcon))
        aboutAction.triggered.connect(self.aboutMessageBox)
        helpMenu.addAction(aboutAction)

        helpMenu.addSeparator()

        manualAction = QAction("Manual", self)
        manualAction.setShortcut("Ctrl+B")
        manualAction.setIcon(QIcon(self.entities.manualWindowIcon))
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
        allResetAction.setIcon(QIcon(self.entities.resetIcon))
        allResetAction.triggered.connect(self.allReset)
        resetMenu.addAction(allResetAction)

        self.setMenuBar(menubar)

        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setToolTip(self.entities.appName)
        self.trayIcon.setIcon(QIcon(self.entities.appIcon))
        self.trayIcon.activated.connect(self.trayIconActivated)

        trayMenu = QMenu()

        trayMenu.setStyleSheet(self.entities.menueStyleSheet)

        appInfoAction = QAction(self.entities.appName, self)
        appInfoAction.setIcon(QIcon(self.entities.appIcon))
        appInfoAction.setDisabled(True)
        appInfoAction.triggered.connect(self.aboutMessageBox)
        trayMenu.addAction(appInfoAction)

        trayMenu.addSeparator()

        batteryCareMenu = QMenu("Battery Care", self)
        batteryCareMenu.setIcon(QIcon(self.entities.batteryCareIcon))
        trayMenu.addMenu(batteryCareMenu)

        self.batteryCareOnAction = QAction("On", self)
        self.batteryCareOnAction.triggered.connect(self.batteryCareOn)
        batteryCareMenu.addAction(self.batteryCareOnAction)

        self.batteryCareOffAction = QAction("Off", self)
        self.batteryCareOffAction.triggered.connect(self.batteryCareOff)
        batteryCareMenu.addAction(self.batteryCareOffAction)

        trayMenu.addSeparator()

        restoreAction = QAction("Restore", self)
        restoreAction.setIcon(QIcon(self.entities.restoreIcon))
        restoreAction.triggered.connect(self.restoreTry)
        trayMenu.addAction(restoreAction)

        minimizeAction = QAction("Minimize", self)
        minimizeAction.setIcon(QIcon(self.entities.minimizeIcon))
        minimizeAction.triggered.connect(self.hide)
        trayMenu.addAction(minimizeAction)

        trayMenu.addSeparator()

        closeAction = QAction("Close", self)
        closeAction.setIcon(QIcon(self.entities.closeIcon))
        closeAction.triggered.connect(self.close_window)
        trayMenu.addAction(closeAction)

        self.trayIcon.setContextMenu(trayMenu)

        self.trayIcon.show()

        self.tableWidget = CustomTableWidget()
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels(
            ["Time", "Percentage", "Status", "Remaining"]
        )
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        batteryRecordGroupbox = QGroupBox("Battery Record")
        batteryRecordLayout = QVBoxLayout(batteryRecordGroupbox)
        batteryRecordLayout.addWidget(self.tableWidget)

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

        batteryInfoGroupbox = QGroupBox("Battery Info")
        batteryInfoLayout = QFormLayout(batteryInfoGroupbox)
        batteryInfoLayout.addRow(batteryLabel, self.batteryTimeLabel)
        batteryInfoLayout.addRow(pluggedInLabel, self.pluggedInTimeLabel)
        batteryInfoLayout.addRow(totalInUseLabel, self.totalInUseTimeLabel)
        batteryInfoLayout.addRow(batteryRemainingLabel, self.batteryRemainingTimeLabel)
        batteryInfoLayout.addRow(batteryLevelLabel, self.batteryLevelPercentLabel)
        batteryInfoLayout.addRow(brightnessLevelLabel, self.brightnessLevelPercentLabel)
        batteryInfoLayout.addRow(self.brightnessSlider)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(batteryRecordGroupbox)
        mainLayout.addWidget(batteryInfoGroupbox)

        widget = QWidget()
        widget.setLayout(mainLayout)
        self.setCentralWidget(widget)

    def batteryCareOn(self):
        self.settingsStatus.setBatteryCare(True)
        self.settingsStatus.saveSettings()

    def batteryCareOff(self):
        self.settingsStatus.setBatteryCare(False)
        self.settingsStatus.saveSettings()

    def manual(self):
        self.manualWindow = ManualWindow()
        if self.manualWindow.isHidden():
            self.manualWindow.show()

    def settings(self):
        self.settingsWindow = SettingsWindow()
        if self.settingsWindow.isHidden():
            self.settingsWindow.show()

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
        \nVersion: {self.entities.appVersion}
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
                pluggSoundFile = self.entities.pluggSound
                pygame.mixer.init()
                pygame.mixer.music.load(pluggSoundFile)
                pygame.mixer.music.play()
                self.showNotification("Plugg")

            elif percent > 80 and plugged:
                unpluggSoundFile = self.entities.unpluggSound
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

    def restoreTry(self):
        self.showNormal()
        self.activateWindow()

    def trayIconActivated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isHidden():
                self.restoreTry()
            else:
                self.hide()

    def close_window(self):
        self.close_on_exit = True
        self.close()

    def closeEvent(self, event):
        if self.close_on_exit:
            self.deleteLater()
        else:
            self.hide()
            event.ignore()


class SettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.entities = Entities()
        self.settingsStatus = SettingsStatus()

        self.initUI()
        self.batteryCareComboBoxStatus()

    def initUI(self):
        self.setWindowTitle(self.entities.settingsWindowName)
        self.setStyleSheet(self.entities.globalStyleSheet)
        self.setWindowIcon(QIcon(self.entities.settingsWindowIcon))
        self.setGeometry(
            *self.entities.settingsWindowStartPoint, *self.entities.settingsWindowSize
        )
        self.setWindowFlags(
            self.windowFlags()
            & ~(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        )

        batteryCareLabel = QLabel("Battery Care:")

        self.batteryCareComboBox = QComboBox()
        self.batteryCareComboBox.addItem("Enabled")
        self.batteryCareComboBox.addItem("Disabled")
        self.batteryCareComboBox.setCurrentIndex(
            0 if self.settingsStatus.getBatteryCare() else 1
        )
        self.batteryCareComboBox.currentIndexChanged.connect(
            self.batteryCareComboBoxStatus
        )

        batteryCareNotifLabel = QLabel("Battery Care Notification:")

        self.batteryCareNotifComboBox = QComboBox()
        self.batteryCareNotifComboBox.addItem("Enabled")
        self.batteryCareNotifComboBox.addItem("Disabled")
        self.batteryCareNotifComboBox.setCurrentIndex(
            0 if self.settingsStatus.getBatteryCareNotif() else 1
        )

        startMinimizeLabel = QLabel("Start Minimize:")

        self.startComboBox = QComboBox()
        self.startComboBox.addItem("Enabled")
        self.startComboBox.addItem("Disabled")
        self.startComboBox.setCurrentIndex(
            0 if self.settingsStatus.getStartMinimize() else 1
        )

        startAtStartupLabel = QLabel("Start at Startup:")

        self.startAtStartupComboBox = QComboBox()
        self.startAtStartupComboBox.addItem("Enabled")
        self.startAtStartupComboBox.addItem("Disabled")
        self.startAtStartupComboBox.setCurrentIndex(
            0 if self.settingsStatus.getStartAtStartup() else 1
        )

        resetTimesLabel = QLabel("Reset Times After Battery Status Changed:")

        self.resetTimesComboBox = QComboBox()
        self.resetTimesComboBox.addItem("Enabled")
        self.resetTimesComboBox.addItem("Disabled")
        self.resetTimesComboBox.setCurrentIndex(
            0 if self.settingsStatus.getResetTimesAfterBatteryStatusChsnged() else 1
        )

        applyButton = QPushButton("Apply")
        applyButton.clicked.connect(self.applySettings)

        controlGroupbox = QGroupBox("Control")
        controlLayout = QGridLayout(controlGroupbox)
        controlLayout.addWidget(applyButton)

        settingsGroupbox = QGroupBox("Settings")
        settingsLayout = QGridLayout(settingsGroupbox)
        settingsLayout.addWidget(batteryCareLabel, 0, 0)
        settingsLayout.addWidget(self.batteryCareComboBox, 0, 1)
        settingsLayout.addWidget(batteryCareNotifLabel, 0, 2)
        settingsLayout.addWidget(self.batteryCareNotifComboBox, 0, 3)
        settingsLayout.addWidget(startMinimizeLabel, 1, 0)
        settingsLayout.addWidget(self.startComboBox, 1, 1)
        settingsLayout.addWidget(startAtStartupLabel, 1, 2)
        settingsLayout.addWidget(self.startAtStartupComboBox, 1, 3)
        settingsLayout.addWidget(resetTimesLabel, 2, 0)
        settingsLayout.addWidget(self.resetTimesComboBox, 2, 1)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(settingsGroupbox)
        mainLayout.addWidget(controlGroupbox)

        widget = QWidget()
        widget.setLayout(mainLayout)
        self.setCentralWidget(widget)

    def batteryCareComboBoxStatus(self):
        battery_care_enabled = self.batteryCareComboBox.currentIndex() == 0
        self.batteryCareNotifComboBox.setEnabled(battery_care_enabled)

    def applySettings(self):
        batteryCareValue = self.batteryCareComboBox.currentIndex() == 0
        self.settingsStatus.setBatteryCare(batteryCareValue)

        batteryCareNotifValue = self.batteryCareNotifComboBox.currentIndex() == 0
        self.settingsStatus.setBatteryCareNotif(batteryCareNotifValue)

        startMinimizeValue = self.startComboBox.currentIndex() == 0
        self.settingsStatus.setStartMinimize(startMinimizeValue)

        startAtStartupValue = self.startAtStartupComboBox.currentIndex() == 0
        self.startAtStartupConfigure(startAtStartupValue)
        self.settingsStatus.setStartAtStartup(startAtStartupValue)

        resetTimesValue = self.resetTimesComboBox.currentIndex() == 0
        self.settingsStatus.setResetTimesAfterBatteryStatusChsnged(resetTimesValue)

        self.settingsStatus.saveSettings()

        QMessageBox.information(
            self, "Apply", "The new settings have been successfully applied."
        )

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

    def closeEvent(self, event):
        self.deleteLater()


class ManualWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.entities = Entities()

        self.manualTetxt = """
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
                <li>Ctrl+E: Exit the app.</li>
                <li>Ctrl+A: Opens the 'About' dialog box.</li>
                <li>Ctrl+B: Opens the manual.</li>
                <li>Ctrl+S: Opens the settings window.</li>
                <li>Ctrl+Z: Resets the total in-use time.</li>
                <li>Ctrl+X: Resets the total battery time.</li>
                <li>Ctrl+V: Resets the total plugged-in time.</li>
                <li>Ctrl+D: Resets the table widget.</li>
                <li>Ctrl+R: Resets all records.</li>
            </ul>

            <p style="font-size: 14px;">Note: Shortcut keys are available for Windows-based systems. On other operating systems, use the corresponding key combinations.</p>

            <p style="font-size: 14px;">That concludes the manual for Battery Tracker. If you have any further questions or need assistance, please refer to the application's documentation or contact our support team. Enjoy using Battery Tracker to monitor and optimize your battery usage!</p>
        """

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.entities.manualWindowName)
        self.setStyleSheet(self.entities.globalStyleSheet)
        self.setWindowIcon(QIcon(self.entities.manualWindowIcon))
        self.setGeometry(
            *self.entities.manualWindowStartPoint, *self.entities.manualWindowSize
        )

        self.textBrowser = QTextBrowser()
        self.textBrowser.setFont(QFont("Arial", 12))
        self.textBrowser.setReadOnly(True)
        self.textBrowser.setLineWrapMode(QTextEdit.NoWrap)
        self.textBrowser.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.textBrowser.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.textBrowser.setHtml(self.manualTetxt)
        self.setCentralWidget(self.textBrowser)

    def closeEvent(self, event):
        self.deleteLater()


def main():
    elevate.elevate()

    app = QApplication([])

    entities = Entities()

    app.setStyle(entities.appStyle)
    app.setApplicationName(entities.appName)
    app.setApplicationVersion(entities.appVersion)
    app.setWindowIcon(QIcon(entities.appIcon))

    mainWindow = MainWindow()
    settingsStatus = SettingsStatus()
    if not settingsStatus.getStartMinimize():
        mainWindow.showNormal()
        mainWindow.activateWindow()

    app.exec_()


if __name__ == "__main__":
    main()
