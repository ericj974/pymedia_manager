from abc import abstractmethod
from functools import partial

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QDragMoveEvent
from PyQt5.QtWidgets import QVBoxLayout, QMenu, QAction, QListWidgetItem, QListWidget, QAbstractItemView, QHBoxLayout, \
    QLineEdit, QSizePolicy, QFrame, QLabel, QPushButton, QCompleter

from common.comment import PersonEntity, TagEntity


class MediaWithMetadata(object):

    @abstractmethod
    def open_media(self, file, **kwargs):
        """

        :param file:
        :return:
        """

    @abstractmethod
    def save_media(self, file, **kwargs):
        """ Save the media """
        pass

    @abstractmethod
    def load_comment(self):
        """
        Update the comments
        :return: user_comment:  comment in the following dic form
        {
            'comments': Comments,
            'tags': list of tags in a single string format with whitespace as separator
        }
        """

    @abstractmethod
    def save_comment(self, user_comment, file=None):
        """
        If handled by the file format, save user_comment in the media file metadata
        :param user_comment:  comment in the following dic form
        {
            'comments': Comments,
            'tags': list of tags in a single string format with whitespace as separator
        }
        :return: None
        """


class PersonQListWidgetItem(QListWidgetItem):
    def __init__(self, entity: PersonEntity):
        super(PersonQListWidgetItem, self).__init__(entity.name)
        self.entity: PersonEntity = entity


class PersonTagWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        self.title = QtWidgets.QLabel()
        self.persons_widget = MyQListWidget()
        self.persons_widget.installEventFilter(self)

        vlay = QVBoxLayout()
        self.setLayout(vlay)
        vlay.addWidget(self.title)
        vlay.addWidget(self.persons_widget, 1)

    def get_entities(self) -> list[PersonEntity]:
        return [self.persons_widget.item(i).entity for i in range(self.persons_widget.count())]

    def set_entities(self, tags: list[PersonEntity]):
        self.persons_widget.clear()
        for tag in tags:
            self.persons_widget.addItem(PersonQListWidgetItem(tag))

    def get_items(self) -> list[PersonQListWidgetItem]:
        return [self.persons_widget.item(i) for i in range(self.persons_widget.count())]

    def act_rename(self):
        if len(self.persons_widget.selectedItems()) == 0:
            return
        text, okPressed = QtWidgets.QInputDialog.getText(self, "New Name", "New Name:")
        if okPressed and text != '':
            if len(self.persons_widget.selectedItems()) > 0:
                self.persons_widget.currentItem().setText(text)

    def act_add_tag(self):
        raise Exception("Need to be implemented")
        text, okPressed = QtWidgets.QInputDialog.getText(self, "New tag", "New tag:")
        if okPressed and text != '':
            if text not in [tag.text() for tag in self.get_items()]:
                self.persons_widget.addItem(text)

    def eventFilter(self, source, event):
        if event.type() == QEvent.ContextMenu and source is self.persons_widget:
            menu = QMenu()
            if len(self.persons_widget.selectedItems()) > 0:
                action = QAction('Rename', self)
                action.triggered.connect(self.act_rename)
                menu.addAction(action)
            action = QAction('New Tag', self)
            action.triggered.connect(self.act_add_tag)
            menu.addAction(action)
            if menu.exec_(event.globalPos()):
                item = source.itemAt(event.pos())
            return True
        elif event.type() == QEvent.KeyPress and event.key() == QtCore.Qt.Key_Delete and source is self.persons_widget:
            sel_items = self.persons_widget.selectedItems()
            list_items = [item for item in self.persons_widget.items() if item not in sel_items]
            self.persons_widget.clear()
            self.persons_widget.addItems(list_items)

        return super().eventFilter(source, event)


class MyQListWidget(QListWidget):
    def __init__(self, parent=None):
        super(MyQListWidget, self).__init__(parent)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDropIndicatorShown(True)
        self.src_widget = None

    def dragMoveEvent(self, e: QDragMoveEvent):
        if (e.source() != self):
            e.accept()
        else:
            e.ignore()


class TagBar(QtWidgets.QWidget):
    def __init__(self, known_tags: list[TagEntity] = None, tags: list[TagEntity] = None):
        super(TagBar, self).__init__()
        self.setWindowTitle('Tag Bar')
        self.tags: list[TagEntity] = tags if tags else []
        self.h_layout = QHBoxLayout()
        self.h_layout.setSpacing(4)
        self.setLayout(self.h_layout)
        self.line_edit = QLineEdit()
        self.line_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        # self.line_edit.textChanged.connect(self.update_display_when_searching)
        self.set_known_tags(known_tags)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setContentsMargins(2, 2, 2, 2)
        self.h_layout.setContentsMargins(2, 2, 2, 2)
        self.refresh()
        self.setup_ui()
        self.show()

    def set_known_tags(self, known_tags: list[TagEntity] = None):
        tags = [tag.name for tag in known_tags]
        completer = QCompleter(tags)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        # completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        completer.setFilterMode(Qt.MatchContains)
        self.line_edit.setCompleter(completer)

    def setup_ui(self):
        self.line_edit.returnPressed.connect(self._add_tags)

    def set_entities(self, tags: list[TagEntity]):
        self.tags = list(set(tags))
        self.tags.sort(key=lambda x: x.lower())
        self.refresh()

    def get_entities(self):
        return self.tags

    def _add_tags(self):
        new_tags = [TagEntity(name=text) for text in self.line_edit.text().split(', ')]
        self.line_edit.setText('')
        self.tags.extend(new_tags)
        self.tags = list(set(self.tags))
        self.tags.sort(key=lambda x: x.lower())
        self.refresh()

    def refresh(self):
        for i in reversed(range(self.h_layout.count())):
            self.h_layout.itemAt(i).widget().setParent(None)
        for tag in self.tags:
            self._add_tag_to_bar(tag)
        self.h_layout.addWidget(self.line_edit)
        # self.line_edit.setFocus()

    def _add_tag_to_bar(self, entity: TagEntity):
        tag = QFrame()
        tag.setStyleSheet('border:1px solid rgb(192, 192, 192); border-radius: 4px;')
        tag.setContentsMargins(2, 2, 2, 2)
        tag.setFixedHeight(28)
        hbox = QHBoxLayout()
        hbox.setContentsMargins(4, 4, 4, 4)
        hbox.setSpacing(10)
        tag.setLayout(hbox)
        label = QLabel(entity.name)
        label.setStyleSheet('border:0px')
        label.setFixedHeight(16)
        hbox.addWidget(label)
        x_button = QPushButton('x')
        x_button.setFixedSize(20, 20)
        x_button.setStyleSheet('border:0px; font-weight:bold')
        x_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        x_button.clicked.connect(partial(self.delete_tag, entity))
        hbox.addWidget(x_button)
        tag.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.h_layout.addWidget(tag)

    def delete_tag(self, entity):
        self.tags.remove(entity)
        self.refresh()

    def update_display_when_searching(self, text):
        for i in range(self.list_db_tags_widget.count()):
            # item(row)->setHidden(!item(row)->text().contains(filter, Qt::CaseInsensitive));
            self.list_db_tags_widget.item(i).setHidden(text.lower() not in
                                                       self.list_db_tags_widget.item(i).text().lower())


class Slider(QtWidgets.QSlider):
    def mousePressEvent(self, event):
        super(Slider, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            val = self.pixelPosToRangeValue(event.pos())
            self.setValue(val)
            self.sliderMoved.emit(val)

    def pixelPosToRangeValue(self, pos):
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        gr = self.style().subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderGroove, self)
        sr = self.style().subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderHandle, self)

        if self.orientation() == QtCore.Qt.Horizontal:
            sliderLength = sr.width()
            sliderMin = gr.x()
            sliderMax = gr.right() - sliderLength + 1
        else:
            sliderLength = sr.height()
            sliderMin = gr.y()
            sliderMax = gr.bottom() - sliderLength + 1;
        pr = pos - sr.center() + sr.topLeft()
        p = pr.x() if self.orientation() == QtCore.Qt.Horizontal else pr.y()
        return QtWidgets.QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), p - sliderMin,
                                                        sliderMax - sliderMin, opt.upsideDown)
