import sys
import psutil
import pygame
import datetime
import pygetwindow
from PyQt5.QtGui import QIcon, QFont
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
)


class BatteryTracker(QWidget):
    def __init__(self):
        super().__init__()

        self.appVersion = "1.0"
        self.appIcon = QIcon("bt.ico")
        self.appTitle = "Battery Tracker"

        self.batteryCare = True
        self.prevPercent = None
        self.timeZero = "0:00:00"

        self.startTime = datetime.datetime.now()
        self.totalInUseTime = datetime.timedelta()
        self.totalBatteryTime = datetime.timedelta()
        self.totalPluggedInTime = datetime.timedelta()

        self.tableStyle = """
            QTableWidget {
                background-color: #f5f5f5;
                border: none;
                font-size: 12px;
            }

            QTableWidget::item {
                padding: 5px;
            }

            QTableWidget::item:selected {
                background-color: #d5e8f9;
            }
        """

        self.headerStyle = """
            QHeaderView::section {
                background-color: #e6e6e6;
                border: none;
                font-weight: bold;
            }
        """

        self.labelStyle = """
            QLabel {
                color: #333333;
                font-size: 14px;
            }
        """

        self.buttonStyle = """
            QPushButton {
                background-color: #4C9EFF;
                border: none;
                color: #ffffff;
                padding: 10px 20px;
                font-size: 14px;
                text-align: center;
                border-radius: 5px;
            }

            QPushButton:hover {
                background-color: #2088FF;
            }
        """

        self.initUI()
        self.updateStatus()
        self.updateTimes()
        self.updateBattery()

    def initUI(self):
        self.setGeometry(200, 200, 455, 485)
        self.setFixedSize(455, 485)
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
        self.aboutAction.triggered.connect(self.aboutMessageBox)
        self.helpMenu.addAction(self.aboutAction)

        self.manualAction = QAction("Manual", self)
        self.manualAction.triggered.connect(self.manual)
        self.helpMenu.addAction(self.manualAction)

        self.resetMenu = QMenu("Reset", self)
        self.menuBar.addMenu(self.resetMenu)

        self.totalTimeResetAction = QAction("TotalTime", self)
        self.totalTimeResetAction.triggered.connect(self.totalTimeReset)
        self.resetMenu.addAction(self.totalTimeResetAction)

        self.totalBatteryTimeResetAction = QAction("BatteryTime", self)
        self.totalBatteryTimeResetAction.triggered.connect(self.totalBatteryTimeReset)
        self.resetMenu.addAction(self.totalBatteryTimeResetAction)

        self.totalPluggedInTimeResetAction = QAction("PluggedInTime", self)
        self.totalPluggedInTimeResetAction.triggered.connect(
            self.totalPluggedInTimeReset
        )
        self.resetMenu.addAction(self.totalPluggedInTimeResetAction)

        self.tableWidgetResetAction = QAction("TableWidget", self)
        self.tableWidgetResetAction.triggered.connect(self.tableWidgetReset)
        self.resetMenu.addAction(self.tableWidgetResetAction)

        self.allResetAction = QAction("All", self)
        self.allResetAction.triggered.connect(self.allReset)
        self.resetMenu.addAction(self.allResetAction)

        self.batteryCareMenu = QMenu("Battery Care", self)
        self.menuBar.addMenu(self.batteryCareMenu)

        self.batteryCareOnAction = QAction("On", self)
        self.batteryCareOnAction.triggered.connect(self.batteryCareOn)
        self.batteryCareMenu.addAction(self.batteryCareOnAction)

        self.batteryCareOffAction = QAction("Off", self)
        self.batteryCareOffAction.triggered.connect(self.batteryCareOff)
        self.batteryCareMenu.addAction(self.batteryCareOffAction)

        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(11)

        self.tableWidget = QTableWidget(self)
        self.tableWidget.setStyleSheet(self.tableStyle)
        self.tableWidget.horizontalHeader().setStyleSheet(self.headerStyle)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(["Time", "Percentage", "Status"])
        self.tableWidget.setStyleSheet("QTableWidget {alignment: center;}")
        self.tableWidget.setFont(font)
        self.tableWidget.horizontalHeader().setFont(font)

        self.groupBox = QGroupBox("Battery Tracker", self)

        self.batteryLabel = QLabel("On battery power on time:", self.groupBox)
        self.batteryTimeLabel = QLabel(self.timeZero, self.groupBox)

        self.pluggedInLabel = QLabel("Plugged in power on time:", self.groupBox)
        self.pluggedInTimeLabel = QLabel(self.timeZero, self.groupBox)

        self.totalInUseLabel = QLabel("Total in use time:", self.groupBox)
        self.totalInUseTimeLabel = QLabel(self.timeZero, self.groupBox)

        self.minimizeToTrayButton = QPushButton("Minimize", self.groupBox)
        self.minimizeToTrayButton.clicked.connect(self.hide)

        self.closeButton = QPushButton("Close", self.groupBox)
        self.closeButton.clicked.connect(self.close)

        self.batteryLabel.setStyleSheet(self.labelStyle)
        self.batteryTimeLabel.setStyleSheet(self.labelStyle)

        self.pluggedInLabel.setStyleSheet(self.labelStyle)
        self.pluggedInTimeLabel.setStyleSheet(self.labelStyle)

        self.totalInUseLabel.setStyleSheet(self.labelStyle)
        self.totalInUseTimeLabel.setStyleSheet(self.labelStyle)

        self.minimizeToTrayButton.setStyleSheet(self.buttonStyle)
        self.closeButton.setStyleSheet(self.buttonStyle)

        self.groupBoxLayout = QVBoxLayout(self.groupBox)
        self.groupBoxLayout.addWidget(self.batteryLabel)
        self.groupBoxLayout.addWidget(self.batteryTimeLabel)
        self.groupBoxLayout.addWidget(self.pluggedInLabel)
        self.groupBoxLayout.addWidget(self.pluggedInTimeLabel)
        self.groupBoxLayout.addWidget(self.totalInUseLabel)
        self.groupBoxLayout.addWidget(self.totalInUseTimeLabel)
        self.groupBoxLayout.addWidget(self.minimizeToTrayButton)
        self.groupBoxLayout.addWidget(self.closeButton)

        layout = QVBoxLayout(self)
        layout.addWidget(self.menuBar)
        layout.addWidget(self.tableWidget)
        layout.addWidget(self.groupBox)

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

    def manual(self):
        self.manualWindow = ManualWindow()
        self.manualWindow.show()

    def trayIconActivated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isHidden():
                self.showNormal()
                self.activateWindow()
            else:
                self.hide()

    def batteryCareOn(self):
        self.batteryCare = True

    def batteryCareOff(self):
        self.batteryCare = False

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
        aboutText = f"""The "Battery Tracker" app is a desktop application that monitors and displays real-time information about the battery status of the device it's running on. It provides details such as battery percentage, charging status, and usage time. Users can track total battery usage, reset timers, enable/disable notifications, and minimize the app to the system tray. It's a convenient tool for monitoring and managing battery usage.
        \nVersion: {self.appVersion}
        \nDeveloper: Sparky
        \nContact: Sparky#2273 on Discord or Sparky2273 on Telegram"""
        QMessageBox.information(self, "About", aboutText)

    def showNotification(self, status):
        if status == "Plugg":
            self.trayIcon.showMessage(
                "Plugged In",
                "Please connect the charger.",
                QSystemTrayIcon.Critical,
                1 * 1000,
            )
        elif status == "UnPlugg":
            self.trayIcon.showMessage(
                "Unplugged",
                "Please disconnect the charger.",
                QSystemTrayIcon.Warning,
                1 * 1000,
            )

    def updateStatus(self):
        if self.batteryCare:
            battery = psutil.sensors_battery()
            percent = battery.percent

            if percent < 21:
                pluggSoundFile = "C:/Windows/Media/Windows Critical Stop.wav"
                pygame.mixer.init()
                pygame.mixer.music.load(pluggSoundFile)
                pygame.mixer.music.play()
                self.showNotification("Plugg")

            elif percent > 90:
                unpluggSoundFile = "C:/Windows/Media/Windows Ding.wav"
                pygame.mixer.init()
                pygame.mixer.music.load(unpluggSoundFile)
                pygame.mixer.music.play()
                self.showNotification("UnPlugg")

        QTimer.singleShot(1 * 1000, self.updateStatus)

    def updateTimes(self):
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

            self.prevPercent = percent

        QTimer.singleShot(10 * 1000, self.updateBattery)


class ManualWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Battery Tracker Application Manual")
        self.setGeometry(150, 150, 1315, 715)
        self.setFixedSize(1315, 715)
        self.setWindowFlags(
            self.windowFlags()
            & ~(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        )

        self.manualText = """
        # Battery Tracker Application Manual

        ## Introduction
        The Battery Tracker application is a desktop tool designed to monitor and display real-time information about the battery status of your device. It provides details such as battery percentage, charging status, and usage time. With Battery Tracker, you can track your total battery usage, reset timers, enable or disable notifications, and minimize the app to the system tray. This manual will guide you through the features and usage of the Battery Tracker application.

        ## Table of Contents
        1. Installation and Setup
        2. Application Interface
        3. Menu Options
        - Help Menu
        - Reset Menu
        - Battery Care Menu
        4. Using the Application
        - Tracking Battery Status
        - Monitoring Usage Time
        - Resetting Timers
        - Minimizing to System Tray
        5. About the Application

        ## 1. Installation and Setup
        - No installation is required. The Sorting Application is an executable (`.exe`) file that can be run directly on your operating system.

        ## 2. Application Interface
        The Battery Tracker application window consists of the following elements:

        - **Table Widget**: Displays a table of battery status information, including time, percentage, and status (plugged/unplugged).
        - **Battery Tracker Group Box**: Contains information about battery usage and control buttons.
        - **Minimize Button**: Minimizes the application window to the system tray.
        - **Close Button**: Closes the application.

        ## 3. Menu Options
        The Battery Tracker application provides several menu options accessible from the menu bar:

        ### Help Menu
        - **About**: Displays information about the application, including the version and contact details of the developer.
        - **Manual**: Opens a manual window with detailed instructions on using the Battery Tracker application.

        ### Reset Menu
        - **TotalTime**: Resets the total in-use time counter.
        - **BatteryTime**: Resets the total battery time counter.
        - **PluggedInTime**: Resets the total plugged-in time counter.
        - **TableWidget**: Clears the table widget displaying battery status information.
        - **All**: Resets all timers and clears the table widget.

        ### Battery Care Menu
        - **On**: Enables battery care mode. The application will play sounds and display notifications when the battery percentage is low (below 21%) or high (above 90%).
        - **Off**: Disables battery care mode. No sounds or notifications will be displayed.

        ## 4. Using the Application

        ### Tracking Battery Status
        The Battery Tracker application continuously monitors the battery status of your device. The table widget displays real-time information about the battery's time, percentage, and status (plugged/unplugged). The table is updated every 10 seconds with the latest information.

        ### Monitoring Usage Time
        The Battery Tracker application tracks the total in-use time, total battery time, and total plugged-in time. These timers are displayed in the Battery Tracker group box.

        - **Total In Use Time**: Shows the total time the device has been in use (on battery power or plugged in).
        - **Total Battery Time**: Displays the total time the device has been running on

        .
        """

        self.textEdit = QTextEdit(self)
        self.textEdit.setPlainText(self.manualText)
        self.textEdit.setReadOnly(True)

        font = QFont("Helvetica", 10)
        self.textEdit.setFont(font)

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
