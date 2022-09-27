# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gui.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(878, 692)
        MainWindow.setAcceptDrops(True)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.pushButton_renamer = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_renamer.setGeometry(QtCore.QRect(40, 30, 91, 81))
        self.pushButton_renamer.setObjectName("pushButton_renamer")
        self.pushButton_editor_img = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_editor_img.setGeometry(QtCore.QRect(280, 30, 91, 81))
        self.pushButton_editor_img.setObjectName("pushButton_editor_img")
        self.widget = FileExplorerWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(20, 130, 831, 451))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName("widget")
        self.pushButton_tileview = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_tileview.setGeometry(QtCore.QRect(160, 30, 91, 81))
        self.pushButton_tileview.setObjectName("pushButton_tileview")
        self.pushButton_gps = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_gps.setGeometry(QtCore.QRect(510, 30, 91, 81))
        self.pushButton_gps.setObjectName("pushButton_gps")
        self.pushButton_editor_vid = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_editor_vid.setGeometry(QtCore.QRect(400, 30, 91, 81))
        self.pushButton_editor_vid.setObjectName("pushButton_editor_vid")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 878, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Media Management"))
        self.pushButton_renamer.setText(_translate("MainWindow", "Renamer"))
        self.pushButton_editor_img.setText(_translate("MainWindow", "Img Editor"))
        self.pushButton_tileview.setText(_translate("MainWindow", "Tile View"))
        self.pushButton_gps.setText(_translate("MainWindow", "GPS"))
        self.pushButton_editor_vid.setText(_translate("MainWindow", "Vid Editor"))

from mainview.widgets import FileExplorerWidget
