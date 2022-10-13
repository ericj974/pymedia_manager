from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QListWidget, QLineEdit, \
    QScrollArea


class FaceTagWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        # Search bar.
        self.searchbar = QLineEdit()
        self.searchbar.textChanged.connect(self.update_display)

        self.title = QtWidgets.QLabel()

        self.list_db_tags_widget = QListWidget()
        self.scroll_db = QScrollArea()
        self.scroll_db.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_db.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_db.setWidgetResizable(True)
        self.scroll_db.setWidget(self.list_db_tags_widget)

        self.list_img_tags_widget = QListWidget()
        self.scroll_img_tags = QScrollArea()
        self.scroll_img_tags.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_img_tags.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_img_tags.setWidgetResizable(True)
        self.scroll_img_tags.setWidget(self.list_img_tags_widget)

        vlay = QVBoxLayout()
        self.setLayout(vlay)
        vlay.addWidget(self.title)
        vlay.addWidget(self.searchbar)
        vlay.addWidget(QtWidgets.QLabel("Existing Tags"))
        vlay.addWidget(self.scroll_db, 3)
        vlay.addWidget(QtWidgets.QLabel("Img Tags"))
        vlay.addWidget(self.scroll_img_tags, 1)

    def set_tags(self, img_tags, file=None):
        pass

    def get_tags(self):
        pass

    def update_display(self, text):
        for i in range(self.list_db_tags_widget.count()):
            # item(row)->setHidden(!item(row)->text().contains(filter, Qt::CaseInsensitive));
            self.list_db_tags_widget.item(i).setHidden(
                self.list_db_tags_widget.item(i).text().contains(text, Qt.CaseInsensitive))
