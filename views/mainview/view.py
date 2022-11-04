from functools import partial

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import *

from views.clip_editor.view import ClipEditorWindow
from controller import MainController
from views.face_editor.view import FaceEditorWindow
from views.gps.view import MainGPSWindow
from views.img_editor.view import PhotoEditorWindow
from views.mainview import gui
from model import MainModel
from views.renamer import nameddic
from views.renamer.view import MainRenamerWindow
from views.tileview.view import MainTileWindow

class MediaManagementView(QMainWindow, gui.Ui_MainWindow):

    def __init__(self, model: MainModel, controller: MainController, config: dict):
        super(self.__class__, self).__init__()

        self._model = model
        self._controller = controller
        self.config = config

        self.setupUi(self)

        # connect widgets to controller
        self.__class__.dropEvent = self._controller.update_dirpath

        self.widget.treeview.doubleClicked.connect(self.on_treeview_doubleclick)
        self.widget.listview.doubleClicked.connect(self.on_listview_doubleclick)

        # listen for model event signals
        self._model.selected_dir_changed.connect(self.on_dirpath_changed)
        self._model.selected_media_changed.connect(self.on_media_changed)

        # update exif button
        self.options = nameddic()

        # Connect the buttons
        self.pushButton_renamer.clicked.connect(self.launch_renamer)
        self.pushButton_editor_img.clicked.connect(partial(self.launch_editor_img, True))
        self.pushButton_editor_vid.clicked.connect(partial(self.launch_editor_vid, True))
        self.pushButton_tileview.clicked.connect(self.launch_tile_view)
        self.pushButton_gps.clicked.connect(self.launch_gps_window)
        self.pushButton_editor_face.clicked.connect(self.launch_editor_face)

        # Connect the drop
        self.__class__.dragEnterEvent = self.dragEnterEvent
        self.__class__.dragMoveEvent = self.dragEnterEvent
        self.setAcceptDrops(True)

        # Renamer window
        self.renamer_dialog = None
        # Editor window
        self.editor_img_window = None
        self.editor_vid_window = None
        # Tile view
        self.tile_window = None
        # GPS Dialog
        self.gps_window = None
        # Face editor Dialog
        self.face_editor = None

    def launch_renamer(self):
        def _on_destroyed():
            self.renamer_dialog = None

        config = self.config[MainRenamerWindow.__name__]
        if not self.renamer_dialog:
            self.renamer_dialog = MainRenamerWindow(config=config, model=self._model, controller=self._controller)
            self.renamer_dialog.destroyed.connect(_on_destroyed)
        # set the dir
        self.renamer_dialog.set_dirpath(self._model.dirpath)
        # check the all by default
        self.renamer_dialog.checkBox_all.setChecked(True)
        self.renamer_dialog.checked_all()
        self.renamer_dialog.show()

    def launch_editor_img(self, force_show=False):
        def _on_destroyed():
            self.editor_img_window = None

        if not self.editor_img_window:
            self.editor_img_window = PhotoEditorWindow(model=self._model, controller=self._controller)
            self.editor_img_window.destroyed.connect(_on_destroyed)
            if force_show:
                self.editor_img_window.show()

    def launch_editor_vid(self, force_show=False):
        def _on_destroyed():
            self.editor_vid_window = None

        if not self.editor_vid_window:
            self.editor_vid_window = ClipEditorWindow(model=self._model, controller=self._controller)
            self.editor_vid_window.destroyed.connect(_on_destroyed)
            if force_show:
                self.editor_vid_window.show()

    def launch_tile_view(self):
        def _on_destroyed():
            self.tile_window = None

        config = self.config[MainTileWindow.__name__]
        if not self.tile_window:
            self.tile_window = MainTileWindow(model=self._model, controller=self._controller, config=config)
            self.tile_window.destroyed.connect(_on_destroyed)
        self.tile_window.set_dirpath(self._model.dirpath)
        self.tile_window.show()

    def launch_gps_window(self):
        def _on_destroyed():
            self.gps_window = None

        if not self.gps_window:
            self.gps_window = MainGPSWindow(model=self._model, controller=self._controller)
            self.gps_window.destroyed.connect(_on_destroyed)
        self.gps_window.set_dirpath(self._model.dirpath)
        self.gps_window.show()

    def launch_editor_face(self):
        def _on_destroyed():
            self.face_editor = None

        config = self.config[FaceEditorWindow.__name__]
        if not self.face_editor:
            self.face_editor = FaceEditorWindow(model=self._model, controller=self._controller, config=config)
            self.face_editor.destroyed.connect(_on_destroyed)
        self.face_editor.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def on_treeview_doubleclick(self, event):
        self._controller.update_dirpath(
            self.widget.dirModel.filePath(
                self.widget.treeview.selectionModel().selectedIndexes()[0]))

    def on_listview_doubleclick(self, event):
        # self.launch_editor_img()
        # self.launch_editor_vid()
        self._controller.set_media_path(
            self.widget.fileModel.filePath(
                self.widget.listview.selectionModel().selectedIndexes()[0]))

    @pyqtSlot(str)
    def on_dirpath_changed(self, dirpath):
        self.widget.set_dirpath(dirpath)

    @pyqtSlot(str)
    def on_media_changed(self, file):
        if file == '':
            return

        index = self.widget.fileModel.index(file, 0)
        if index.row() != -1:
            self.widget.listview.setCurrentIndex(index)
