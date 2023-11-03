# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'stackui.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("identity")
        Form.resize(1000, 807)
        Form.setMinimumSize(QtCore.QSize(540, 540))

        self.graphicsView_1 = PhotoViewer(Form)
        self.layout_main = QtWidgets.QVBoxLayout(Form)
        self.layout_main.setObjectName("layout_main")
        self.layout_main.addWidget(self.graphicsView_1)
        # Sliders
        self.frame_label = QtWidgets.QLabel("Frame:")
        self.frame_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        # Combobox for rotation
        self.rotation_label = QtWidgets.QLabel("Rotation angles (anti-clockwise)")
        self.rotation_items = ["0", "180"]
        self.rotation_combo = QtWidgets.QComboBox()
        self.rotation_combo.addItems(self.rotation_items)

        # Combobox for the type of source fps
        self.fps_items = ['tbr', 'fps']
        self.fps_combo = QtWidgets.QComboBox()
        self.fps_combo.addItems(self.fps_items)
        self.fps_label = QtWidgets.QLabel("FPS info")

        # Rot Layout
        layout = QtWidgets.QGridLayout(Form)
        index = 0
        layout.addWidget(self.frame_label, index, 0)
        layout.addWidget(self.frame_slider, index, 1, 1, 2)
        index = 1
        layout.addWidget(self.rotation_label, index, 0)
        layout.addWidget(self.rotation_combo, index, 1, 1, 2)
        index = 2
        layout.addWidget(self.fps_label, index, 0)
        layout.addWidget(self.fps_combo, index, 1, 1, 2)

        self.layout_main.addLayout(layout)
        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Stack"))


from mvc.views.clip_editor.dialogs import PhotoViewer
