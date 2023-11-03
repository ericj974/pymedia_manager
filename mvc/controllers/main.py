from pathlib import Path

from PyQt5.QtCore import QFileSystemWatcher
from send2trash import send2trash

import common.comment
from common.comment import TagEntity, UserComment
from common.constants import FILE_EXTENSION_MEDIA, FILE_EXTENSION_PHOTO_JPG
from mvc.models.main import MainModel


class MainController:
    def __init__(self, model: MainModel):
        super(self.__class__, self).__init__()
        # init
        self._model = model
        # Watcher to the current file and folder.
        # The watched has to be properly initialized by setting the parent window
        self._watcher: QFileSystemWatcher = None

    def set_parent(self, window):
        """
        Re-init the watcher with parent window (this allows to catch events)
        """
        self._watcher = QFileSystemWatcher(window)
        self._watcher.fileChanged.connect(self.on_watcher_file_changed)
        self._watcher.directoryChanged.connect(self.on_watcher_dir_changed)

    def update_dirpath(self, event):
        dirpath = None
        if isinstance(event, Path):
            dirpath = event
        else:
            for url in event.mimeData().urls():
                dirpath = Path(url.toLocalFile())
                break
        if dirpath is None or not dirpath.is_dir():
            return

        # List content of the folder
        files = sorted([file for file in dirpath.glob('*')])

        if dirpath != self._model.dirpath:  # Actual change of dirpath
            dirpath_old = self._model.dirpath
            self._model.files = files
            if dirpath_old != dirpath:
                self._watcher.removePaths(self._watcher.directories())
                self._watcher.addPath(str(dirpath))
        else:  # Update of the content
            _model_files_set = set(self._model.files)
            _files_set = set(files)

            #
            new_files = _files_set.difference(_model_files_set)
            deleted_files = _model_files_set.difference(_files_set)

            # We have new files or renamed file(s)
            # TODO: Give more granularity to this and handle the addition of files event
            if len(new_files) > 0:
                self._model.add_files_to_list(new_files)

            # Files have been deleted
            if len(deleted_files) > 0:
                # Current media in the list of deleted files. Go to the next available file to open
                if self._model._media_path in deleted_files and len(files) > 0:
                    idx = self._model.files.index(self._model.media_path)
                    # Select a file in the old list as we don't know how to "insert" new files into the current list
                    while self._model.files[idx] in deleted_files:
                        idx = (idx + 1) % len(self._model.files)
                        if idx == 0:
                            break

                    # Select the first media in the current list that is still
                    path = self._model.files[idx] if self._model.files[idx] in files else files[0]
                    self.set_media_path(path)

                self._model.remove_files_from_list(deleted_files)

    def set_media_path(self, path: Path):
        if not path.is_file() or self._model.media_path == path:
            return

        self._watcher.removePaths(self._watcher.files())
        self._watcher.addPath(str(path))
        if path.parent != self._model.dirpath:
            self.update_dirpath(path.parent)
        self._model.media_path = path

        # Load the comments
        if path.suffix in FILE_EXTENSION_PHOTO_JPG:
            self._model.media_comment = common.comment.ImageUserComment.load_from_file(path)

    def set_db_tags_path(self, dirpath):
        self._model.set_db_tags_path(dirpath=dirpath)

    def add_tag_to_db(self, tag: TagEntity):
        self._model.add_tag_to_db(tag=tag)

    def update_media_comment(self, comment: UserComment):
        self._model.media_comment = comment

    def save_media_comment(self):
        self._model.media_comment.save_comment(self._model.media_path)

    def _next_media(self, incr=1, extension=FILE_EXTENSION_MEDIA):
        idx0 = idx = self._model.files.index(self._model.media_path)
        while True:
            idx = (idx + incr) % len(self._model.files)
            path = self._model.files[idx]
            if (path.suffix in extension) or (idx == idx0):
                break
        path = self._model.files[idx]
        self.set_media_path(path)

    def select_next_media(self, extension=FILE_EXTENSION_MEDIA):
        self._next_media(incr=1, extension=extension)

    def select_prev_media(self, extension=FILE_EXTENSION_MEDIA):
        self._next_media(incr=-1, extension=extension)

    def delete_cur_media(self, extension=FILE_EXTENSION_MEDIA):
        file_to_delete = self._model.media_path
        self.select_next_media(extension=extension)
        send2trash(file_to_delete)
        self._model.remove_files_from_list({file_to_delete})

    def on_watcher_file_changed(self, path: str):
        # https://doc.qt.io/qt-5/qfilesystemwatcher.html
        # This signal is emitted when the file at the specified path is modified, renamed or removed from disk.
        path = Path(path)
        if not path.is_file():
            return
        if str(path) not in self._watcher.files():  # Current file renamed ?
            # We remove all the files that we're watching. Normally one only
            self._watcher.removePaths(self._watcher.files())
            self._watcher.addPath(str(path))
        else:
            self._model.update_selected_file_content()

    def on_watcher_dir_changed(self, path=None):
        # https://doc.qt.io/qt-5/qfilesystemwatcher.html
        # Called  when the directory at a specified path is modified (e.g., when a file is added or deleted) or
        # removed from disk
        path = Path(path)
        if not path.is_dir():
            return
        # Content has been changed.
        self.update_dirpath(path)
        # TODO: Update this to handle properly the content that has changed
        if path not in self._watcher.directories():
            self._watcher.removePaths(self._watcher.directories())
            self._watcher.addPath(str(path))
