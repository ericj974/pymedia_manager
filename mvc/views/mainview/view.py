from functools import partial
from pathlib import Path

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMainWindow

from common.constants import FILE_EXTENSION_PHOTO_JPG
from common.db import FaceDetectionDB
from mvc.controllers.face import FaceDetectionController
from mvc.controllers.main import MainController
from mvc.models.face import FaceDetectionModel
from mvc.models.main import MainModel
from mvc.views.clip_editor.view import ClipEditorWindow
from mvc.views.gps.view import MainGPSWindow
from mvc.views.img_editor.face_batch import FaceEditorBatchWindow
from mvc.views.img_editor.view import PhotoEditorWindow
from mvc.views.mainview import gui
from mvc.views.renamer import nameddic
from mvc.views.renamer.view import MainRenamerWindow
from mvc.views.tileview.view import MainTileWindow


class MediaManagementView(QMainWindow, gui.Ui_MainWindow):

    def __init__(self, model: MainModel, controller: MainController, config: dict):
        super(self.__class__, self).__init__()

        # MVC
        self._model = model
        self._controller = controller
        self._controller.set_parent(self)
        self.config = config

        # MVC Faces
        db_face_folder = Path(self.config["DB_FACE_FOLDER"])
        self._model_face = FaceDetectionModel(db=FaceDetectionDB(db_face_folder))
        self._controller_face = FaceDetectionController(model=self._model_face)

        self.setupUi(self)

        # connect widgets to controller
        self.__class__.dropEvent = self._controller.update_dirpath

        self.widget.treeview.doubleClicked.connect(self.on_treeview_doubleclick)
        self.widget.listview.doubleClicked.connect(self.on_listview_doubleclick)
        self.widget.selected_files_face_det.connect(self.on_selected_files_face_det)

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

        # Connect the drop
        self.__class__.dragEnterEvent = self.dragEnterEvent
        self.__class__.dragMoveEvent = self.dragEnterEvent
        self.setAcceptDrops(True)

        # Windows
        self.win_renamer = None
        self.win_img_editor = None
        self.win_vid_editor = None
        self.win_tiles = None
        self.win_gps = None
        self.win_batch_faces = None

    def launch_renamer(self):
        def _on_destroyed():
            self.win_renamer = None

        config = self.config[MainRenamerWindow.__name__]
        if not self.win_renamer:
            self.win_renamer = MainRenamerWindow(config=config, model=self._model, controller=self._controller)
            self.win_renamer.destroyed.connect(_on_destroyed)
        # set the dir
        self.win_renamer.set_dirpath(self._model.dirpath)
        # check the all by default
        self.win_renamer.checkBox_all.setChecked(True)
        self.win_renamer.checked_all()
        self.win_renamer.show()

    def launch_editor_img(self, force_show=False):
        def _on_destroyed():
            self.win_img_editor = None

        if not self.win_img_editor:
            self.win_img_editor = PhotoEditorWindow(model=self._model, controller=self._controller,
                                                    model_local=self._model_face,
                                                    controller_local=self._controller_face)
            self.win_img_editor.destroyed.connect(_on_destroyed)
            if force_show:
                self.win_img_editor.show()

    def launch_editor_vid(self, force_show=False):
        def _on_destroyed():
            self.win_vid_editor = None

        config = self.config[ClipEditorWindow.__name__]
        if not self.win_vid_editor:
            self.win_vid_editor = ClipEditorWindow(model=self._model, controller=self._controller, config=config)
            self.win_vid_editor.destroyed.connect(_on_destroyed)
            if force_show:
                self.win_vid_editor.show()

    def launch_tile_view(self):
        def _on_destroyed():
            self.win_tiles = None

        config = self.config[MainTileWindow.__name__]
        if not self.win_tiles:
            self.win_tiles = MainTileWindow(model=self._model, controller=self._controller, config=config)
            self.win_tiles.destroyed.connect(_on_destroyed)
        self.win_tiles.set_dirpath(self._model.dirpath)
        self.win_tiles.show()

    def launch_gps_window(self):
        def _on_destroyed():
            self.win_gps = None

        if not self.win_gps:
            self.win_gps = MainGPSWindow(model=self._model, controller=self._controller)
            self.win_gps.destroyed.connect(_on_destroyed)
        self.win_gps.set_dirpath(self._model.dirpath)
        self.win_gps.show()

    def launch_face_editor_batch(self):
        def _on_destroyed():
            self.win_batch_faces = None

        if not self.win_batch_faces:
            self.win_batch_faces = FaceEditorBatchWindow(model=self._model, controller=self._controller,
                                                         model_local=self._model_face,
                                                         controller_local=self._controller_face)
            self.win_batch_faces.destroyed.connect(_on_destroyed)
        self.win_batch_faces.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def on_treeview_doubleclick(self, event):
        path = Path(self.widget.dirModel.filePath(self.widget.treeview.selectionModel().selectedIndexes()[0]))
        self._controller.update_dirpath(path)

    def on_listview_doubleclick(self, event):
        # self.launch_editor_img()
        # self.launch_editor_vid()
        path = Path(self.widget.fileModel.filePath(self.widget.listview.selectionModel().selectedIndexes()[0]))
        self._controller.set_media_path(path)

    @pyqtSlot(Path)
    def on_dirpath_changed(self, dirpath):
        self.widget.set_dirpath(dirpath)

    @pyqtSlot(Path)
    def on_media_changed(self, file):
        if file is None:
            return

        index = self.widget.fileModel.index(str(file), 0)
        if index.row() != -1:
            self.widget.listview.setCurrentIndex(index)

    @pyqtSlot()
    def on_selected_files_face_det(self):
        files = []
        for ind in self.widget.listview.selectedIndexes():
            file = Path(self.widget.fileModel.filePath(ind))
            if file.suffix in FILE_EXTENSION_PHOTO_JPG:
                files.append(file)
        self.launch_face_editor_batch()
        self.win_batch_faces.detect_faces(files)
