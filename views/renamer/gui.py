# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gui.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(807, 737)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.pushButton_openFolder = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_openFolder.setGeometry(QtCore.QRect(0, 40, 111, 27))
        self.pushButton_openFolder.setObjectName("pushButton_openFolder")
        self.label_dirpath = QtWidgets.QLabel(self.centralwidget)
        self.label_dirpath.setGeometry(QtCore.QRect(120, 40, 481, 31))
        self.label_dirpath.setObjectName("label_dirpath")
        self.pushButton_applyName = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_applyName.setGeometry(QtCore.QRect(700, 40, 85, 27))
        self.pushButton_applyName.setObjectName("pushButton_applyName")
        self.table_result = QtWidgets.QTableWidget(self.centralwidget)
        self.table_result.setGeometry(QtCore.QRect(0, 210, 801, 491))
        self.table_result.setAcceptDrops(True)
        self.table_result.setDragDropOverwriteMode(True)
        self.table_result.setColumnCount(3)
        self.table_result.setObjectName("table_result")
        self.table_result.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.table_result.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.table_result.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.table_result.setHorizontalHeaderItem(2, item)
        self.table_result.horizontalHeader().setVisible(True)
        self.table_result.horizontalHeader().setCascadingSectionResizes(True)
        self.table_result.horizontalHeader().setDefaultSectionSize(250)
        self.table_result.horizontalHeader().setSortIndicatorShown(True)
        self.table_result.horizontalHeader().setStretchLastSection(False)
        self.table_result.verticalHeader().setCascadingSectionResizes(True)
        self.label_filter_results = QtWidgets.QLabel(self.centralwidget)
        self.label_filter_results.setGeometry(QtCore.QRect(10, 110, 111, 17))
        self.label_filter_results.setObjectName("label_filter_results")
        self.filters_widget = QtWidgets.QWidget(self.centralwidget)
        self.filters_widget.setGeometry(QtCore.QRect(130, 80, 211, 111))
        self.filters_widget.setObjectName("filters_widget")
        self.checkBox_all = QtWidgets.QCheckBox(self.filters_widget)
        self.checkBox_all.setGeometry(QtCore.QRect(20, 0, 86, 22))
        self.checkBox_all.setObjectName("checkBox_all")
        self.comboBox_tags = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox_tags.setGeometry(QtCore.QRect(0, 10, 87, 27))
        self.comboBox_tags.setObjectName("comboBox_tags")
        self.checkBox_exif = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox_exif.setGeometry(QtCore.QRect(10, 140, 101, 22))
        self.checkBox_exif.setObjectName("checkBox_exif")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 807, 20))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Renamer"))
        self.pushButton_openFolder.setText(_translate("MainWindow", "Open Folder...."))
        self.label_dirpath.setText(_translate("MainWindow", "TextLabel"))
        self.pushButton_applyName.setText(_translate("MainWindow", "Apply ..."))
        self.table_result.setSortingEnabled(True)
        item = self.table_result.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Filename In"))
        item = self.table_result.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Filename Out"))
        item = self.table_result.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "Status"))
        self.label_filter_results.setText(_translate("MainWindow", "Filter results"))
        self.checkBox_all.setText(_translate("MainWindow", "all"))
        self.checkBox_exif.setText(_translate("MainWindow", "update exit"))
