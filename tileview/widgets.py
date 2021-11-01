import os
import sys

import piexif
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QStatusBar, QHBoxLayout, QVBoxLayout

import utils


class UserCommentWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        vlay = QVBoxLayout()
        self.setLayout(vlay)
        self.title = QtWidgets.QLabel()
        self.text_widget  = QtWidgets.QTextEdit()
        self.tags_widget = QtWidgets.QTextEdit()
        self.filepath = None
        vlay.addWidget(self.title)
        vlay.addWidget(self.text_widget, 3)
        vlay.addWidget(QtWidgets.QLabel("Tags"))
        vlay.addWidget(self.tags_widget, 1)

    def update_comment(self, filepath):
        user_comment = utils.get_exif_user_comment(filepath)
        assert 'tags' in user_comment
        assert 'comments' in user_comment
        self.filepath = filepath
        self.text_widget.setText(user_comment['comments'])
        text = ""
        for tag in user_comment['tags']:
            text += tag + " "
        self.tags_widget.setText(text)
        self.title.setText(os.path.basename(filepath))

    def save_comment(self):
        if self.filepath is None: return

        user_comment = {
            'comments': self.text_widget.toPlainText(),
            'tags': self.tags_widget.toPlainText().split()
        }

        exif_dic = utils.get_exif_v2(self.filepath)
        utils.update_user_comment(exif_dict=exif_dic, userdata=user_comment)
        utils.save_exif(exif_dict=exif_dic, filepath=self.filepath)





