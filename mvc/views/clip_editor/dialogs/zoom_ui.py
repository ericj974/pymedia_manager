# -*- coding: utf-8 -*-

#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        # Form.setObjectName(ActionType.zoom.value)
        Form.resize(1000, 807)
        Form.setMinimumSize(QtCore.QSize(540, 540))

        self.graphicsView_1 = PhotoViewer(Form)
        self.layout_main = QtWidgets.QVBoxLayout(Form)
        self.layout_main.setObjectName("layout_main")
        self.layout_main.addWidget(self.graphicsView_1)
        # Sliders
        self.frameLabel = QtWidgets.QLabel("Frame:")
        self.frameSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        # Slider Layout
        slider_layout = QtWidgets.QGridLayout(Form)
        index = 0
        slider_layout.addWidget(self.frameLabel, index, 0)
        slider_layout.addWidget(self.frameSlider, index, 1, 1, 2)
        self.layout_main.addLayout(slider_layout)
        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Stack"))


from mvc.views.clip_editor.dialogs import PhotoViewer
