import sys
import wmi
import psutil
import pygame
import datetime
import pygetwindow
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTime, QTimer
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
    QDialog,
    QTextEdit,
    QSlider,
    QFormLayout,
    QHBoxLayout,
)


class BatteryTracker(QWidget):
    def __init__(self):
        super().__init__()

        self.appVersion = "2.0"
        self.appIcon = QIcon("bt.ico")
        self.appTitle = "Battery Tracker"
        self.appSize = 580, 480

        self.batteryCare = True
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
        self.setGeometry(200, 200, *self.appSize)
        self.setFixedSize(*self.appSize)
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

        self.menuBar = QMenuBar()

        self.helpMenu = QMenu("Help", self)
        self.menuBar.addMenu(self.helpMenu)

        self.aboutAction = QAction("About", self)
        self.aboutAction.setShortcut("Ctrl+A")
        self.aboutAction.triggered.connect(self.aboutMessageBox)
        self.helpMenu.addAction(self.aboutAction)

        self.manualAction = QAction("Manual", self)
        self.manualAction.setShortcut("Ctrl+B")
        self.manualAction.triggered.connect(self.manual)
        self.helpMenu.addAction(self.manualAction)

        self.resetMenu = QMenu("Reset", self)
        self.menuBar.addMenu(self.resetMenu)

        self.totalTimeResetAction = QAction("TotalTime", self)
        self.totalTimeResetAction.setShortcut("Ctrl+Z")
        self.totalTimeResetAction.triggered.connect(self.totalTimeReset)
        self.resetMenu.addAction(self.totalTimeResetAction)

        self.totalBatteryTimeResetAction = QAction("BatteryTime", self)
        self.totalBatteryTimeResetAction.setShortcut("Ctrl+X")
        self.totalBatteryTimeResetAction.triggered.connect(self.totalBatteryTimeReset)
        self.resetMenu.addAction(self.totalBatteryTimeResetAction)

        self.totalPluggedInTimeResetAction = QAction("PluggedInTime", self)
        self.totalPluggedInTimeResetAction.setShortcut("Ctrl+S")
        self.totalPluggedInTimeResetAction.triggered.connect(
            self.totalPluggedInTimeReset
        )
        self.resetMenu.addAction(self.totalPluggedInTimeResetAction)

        self.tableWidgetResetAction = QAction("TableWidget", self)
        self.tableWidgetResetAction.setShortcut("Ctrl+D")
        self.tableWidgetResetAction.triggered.connect(self.tableWidgetReset)
        self.resetMenu.addAction(self.tableWidgetResetAction)

        self.allResetAction = QAction("All", self)
        self.allResetAction.setShortcut("Ctrl+R")
        self.allResetAction.triggered.connect(self.allReset)
        self.resetMenu.addAction(self.allResetAction)

        self.batteryCareMenu = QMenu("Battery Care", self)
        self.menuBar.addMenu(self.batteryCareMenu)

        self.batteryCareOnAction = QAction("On", self)
        self.batteryCareOnAction.setShortcut("Ctrl+N")
        self.batteryCareOnAction.triggered.connect(self.batteryCareOn)
        self.batteryCareOnAction.setCheckable(True)
        self.batteryCareOnAction.setChecked(True)
        self.batteryCareMenu.addAction(self.batteryCareOnAction)

        self.batteryCareOffAction = QAction("Off", self)
        self.batteryCareOffAction.setShortcut("Ctrl+F")
        self.batteryCareOffAction.triggered.connect(self.batteryCareOff)
        self.batteryCareOffAction.setCheckable(True)
        self.batteryCareMenu.addAction(self.batteryCareOffAction)

        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setToolTip("Battery Tracker")
        self.trayIcon.setIcon(self.appIcon)
        self.trayIcon.activated.connect(self.trayIconActivated)

        self.restoreAction = QAction("Restore", self)
        self.restoreAction.triggered.connect(self.show)

        self.minimizeAction = QAction("Minimize", self)
        self.minimizeAction.triggered.connect(self.hide)

        self.closeAction = QAction("Close", self)
        self.closeAction.triggered.connect(self.close)

        self.trayMenu = QMenu(self)
        self.trayMenu.addAction(self.restoreAction)
        self.trayMenu.addAction(self.minimizeAction)
        self.trayMenu.addAction(self.closeAction)

        self.trayIcon.setContextMenu(self.trayMenu)

        self.trayIcon.show()

        self.tableWidget = QTableWidget(self)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels(
            ["Time", "Percentage", "Status", "Remaining"]
        )
        self.tableWidget.setStyleSheet("QTableWidget {alignment: center;}")

        self.groupBox = QGroupBox("Battery Info", self)

        self.batteryLabel = QLabel("On battery power on time:", self.groupBox)
        self.batteryTimeLabel = QLabel(self.timeZero, self.groupBox)

        self.pluggedInLabel = QLabel("Plugged in power on time:", self.groupBox)
        self.pluggedInTimeLabel = QLabel(self.timeZero, self.groupBox)

        self.totalInUseLabel = QLabel("Total in use time:", self.groupBox)
        self.totalInUseTimeLabel = QLabel(self.timeZero, self.groupBox)

        self.batteryRemainingLabel = QLabel("Remaining Battery Time:", self.groupBox)
        self.batteryRemainingTimeLabel = QLabel(self.timeZero, self.groupBox)

        self.batteryLevelLabel = QLabel("Battery Level:", self.groupBox)
        self.batteryLevelPercentLabel = QLabel(self.percentZero, self.groupBox)

        self.brightnessLevelLabel = QLabel("Brightness Level:", self.groupBox)
        self.brightnessLevelPercentLabel = QLabel(self.percentZero, self.groupBox)

        self.brightnessSlider = QSlider(Qt.Horizontal, self.groupBox)
        self.brightnessSlider.setRange(10, 80)
        self.brightnessSlider.valueChanged.connect(self.updateBrightness)

        self.windowButtonGroupBox = QGroupBox("Window", self)

        self.minimizeToTrayButton = QPushButton("Minimize", self.windowButtonGroupBox)
        self.minimizeToTrayButton.setShortcut("Ctrl+M")
        self.minimizeToTrayButton.clicked.connect(self.hide)

        self.closeButton = QPushButton("Close", self.windowButtonGroupBox)
        self.closeButton.setShortcut("Ctrl+C")
        self.closeButton.clicked.connect(self.close)

        self.buttonLayout = QHBoxLayout(self.windowButtonGroupBox)
        self.buttonLayout.addWidget(self.minimizeToTrayButton)
        self.buttonLayout.addWidget(self.closeButton)

        self.groupBoxLayout = QFormLayout(self.groupBox)
        self.groupBoxLayout.addRow(self.batteryLabel, self.batteryTimeLabel)
        self.groupBoxLayout.addRow(self.pluggedInLabel, self.pluggedInTimeLabel)
        self.groupBoxLayout.addRow(self.totalInUseLabel, self.totalInUseTimeLabel)
        self.groupBoxLayout.addRow(
            self.batteryRemainingLabel, self.batteryRemainingTimeLabel
        )
        self.groupBoxLayout.addRow(
            self.batteryLevelLabel, self.batteryLevelPercentLabel
        )
        self.groupBoxLayout.addRow(
            self.brightnessLevelLabel, self.brightnessLevelPercentLabel
        )
        self.groupBoxLayout.addRow(self.brightnessSlider)

        layout = QVBoxLayout(self)
        layout.setMenuBar(self.menuBar)
        layout.addWidget(self.tableWidget)
        layout.addWidget(self.groupBox)
        layout.addWidget(self.windowButtonGroupBox)
        self.setLayout(layout)

    def manual(self):
        self.manualWindow = Manual()
        self.manualWindow.show()

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

    def batteryCareOn(self):
        self.batteryCare = True
        self.batteryCareOffAction.setChecked(False)
        self.batteryCareOnAction.setChecked(True)

    def batteryCareOff(self):
        self.batteryCare = False
        self.batteryCareOnAction.setChecked(False)
        self.batteryCareOffAction.setChecked(True)

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
        QMessageBox.information(self, "About", aboutText)

    def showNotification(self, status):
        if status == "Plugg":
            self.trayIcon.showMessage(
                "Plugged In",
                "Please connect the charger.",
                QSystemTrayIcon.Critical,
                3 * 1000,
            )
        elif status == "UnPlugg":
            self.trayIcon.showMessage(
                "Unplugged",
                "Please disconnect the charger.",
                QSystemTrayIcon.Warning,
                3 * 1000,
            )

    def updateStatus(self):
        if self.batteryCare:
            battery = psutil.sensors_battery()
            percent = battery.percent
            plugged = battery.power_plugged

            if percent < 21 and not plugged:
                pluggSoundFile = "C:/Windows/Media/Windows Critical Stop.wav"
                pygame.mixer.init()
                pygame.mixer.music.load(pluggSoundFile)
                pygame.mixer.music.play()
                self.showNotification("Plugg")

            elif percent > 90 and plugged:
                unpluggSoundFile = "C:/Windows/Media/Windows Ding.wav"
                pygame.mixer.init()
                pygame.mixer.music.load(unpluggSoundFile)
                pygame.mixer.music.play()
                self.showNotification("UnPlugg")

        QTimer.singleShot(1 * 1000, self.updateStatus)

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
        else:
            self.totalBatteryTime += elapsedTime
            timeFormat = str(self.totalBatteryTime).split(".")[0]
            self.batteryTimeLabel.setText(str(timeFormat))

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

        QTimer.singleShot(10 * 1000, self.updateBattery)


class Manual(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Battery Tracker Manual")
        self.setGeometry(150, 150, 1300, 700)
        self.setFixedSize(1300, 700)
        self.setWindowFlags(
            self.windowFlags()
            & ~(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        )

        self.manualText = """
        **Battery Tracker Manual**

        Welcome to the Battery Tracker manual. This manual will guide you on how to use the Battery Tracker application effectively. Battery Tracker is an application that helps you track the battery status of your device and monitor battery usage over time. It provides information about battery level, power status, remaining battery time, and more.

        **1. Application Overview**
        The Battery Tracker application consists of the following components:
        - Main Window: Displays battery information, including time, percentage, status, and remaining battery time.
        - Table Widget: Displays a history of battery changes, including the time, percentage, status, and remaining battery time.
        - Battery Info Group: Provides detailed information about battery usage, including on battery power on time, plugged-in power on time, total in-use time, and remaining battery time.
        - Brightness Level Group: Allows you to adjust the brightness level of your device's screen.
        - Window Group: Provides options to minimize the application to the system tray or close the application.
        - System Tray Icon: Displays a system tray icon for quick access to the application.

        **2. Menu Options**
        The Battery Tracker application provides the following menu options:
        - Help Menu:
        - About: Displays information about the application, including the version, developer, and contact details.
        - Manual: Opens the Battery Tracker manual for detailed instructions on using the application.
        - Reset Menu:
        - TotalTime: Resets the total in-use time to zero.
        - BatteryTime: Resets the battery power on time to zero.
        - PluggedInTime: Resets the plugged-in power on time to zero.
        - TableWidget: Clears the history of battery changes.
        - All: Resets all the above values to zero.
        - Battery Care Menu:
        - On: Enables battery care mode. Battery care mode provides notifications when the battery level is low or high.
        - Off: Disables battery care mode.
        - Window Menu:
        - Restore: Restores the application window if it is minimized.
        - Minimize: Minimizes the application to the system tray.
        - Close: Closes the application.

        **3. Battery Care Mode**
        Battery care mode is a feature that helps you take care of your device's battery by providing notifications when the battery level is low or high. When battery care mode is enabled, the application will play a sound and display a notification when the battery level falls below 21% or exceeds 90%. You can enable or disable battery care mode through the Battery Care menu.

        **4. Brightness Level**
        The Battery Tracker application allows you to adjust the brightness level of your device's screen. In the Brightness Level group, you will find a slider that you can use to increase or decrease the brightness level. Adjusting the brightness level can help optimize battery usage.

        **5. Battery Information**
        The Battery Info group displays detailed information about battery usage:
        - On battery power on time: Shows the total time your device has been running on battery power.
        - Plugged-in power on time: Shows the total time your device has been running while plugged in.
        - Total in use time: Shows the total time your device has been in use.
        - Remaining Battery Time: Displays the estimated time remaining for the current battery charge.

        **6. Battery History**
        The Table Widget displays a history of battery changes, including the time, percentage, status, and remaining battery time at each change. The table provides a record of battery usage over time.

        **7. Minimize to System Tray**
        You can minimize the Battery Tracker application to the system tray by clicking the Minimize button. This allows you to keep the application running in the background while preserving desktop space.

        **8. Closing the Application**
        To close the Battery Tracker application, click the Close button in the Window group.
        """

        self.textEdit = QTextEdit(self)
        self.textEdit.setPlainText(self.manualText)
        self.textEdit.setReadOnly(True)

        manualGroupBox = QGroupBox("Manual")
        manualLayout = QVBoxLayout()
        manualLayout.addWidget(self.textEdit)
        manualGroupBox.setLayout(manualLayout)

        layout = QVBoxLayout()
        layout.addWidget(manualGroupBox)
        self.setLayout(layout)


def checkRunningWindow(mainWindowTitle):
    if pygetwindow.getWindowsWithTitle(mainWindowTitle):
        return mainWindowTitle
    return False


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication([])
    batteryTracker = BatteryTracker()
    app.setApplicationVersion(batteryTracker.appVersion)

    mainWindowTitle = checkRunningWindow(batteryTracker.appTitle)
    if mainWindowTitle:
        mainWindow = pygetwindow.getWindowsWithTitle(mainWindowTitle)[0]
        mainWindow.activate()
        sys.exit(1)

    batteryTracker.show()
    app.exec_()


if __name__ == "__main__":
    main()
