import os

from PyQt5.QtCore import QFileSystemWatcher
from send2trash import send2trash

import utils
from constants import FILE_EXTENSION_MEDIA, FILE_EXTENSION_PHOTO, FILE_EXTENSION_VIDEO, FILE_EXTENSION_PHOTO_JPG
from model import MainModel


class MainController:
    def __init__(self, model: MainModel):
        super(self.__class__, self).__init__()
        # init
        self._model = model
        # Watcher to the current file and folder
        self._watcher = QFileSystemWatcher()
        self._watcher.fileChanged.connect(self.on_watcher_file_changed)
        self._watcher.directoryChanged.connect(self.on_watcher_dir_changed)

    def update_dirpath(self, event):
        dirpath = None
        if isinstance(event, str):
            dirpath = event
        else:
            for url in event.mimeData().urls():
                dirpath = url.toLocalFile()
                break
        if dirpath is None or dirpath == '' or not os.path.isdir(dirpath):
            return

        # List content of the folder
        files = [os.path.join(dirpath, file) for file in os.listdir(dirpath)]
        files = sorted([f for f in files if os.path.isfile(f) and os.path.splitext(f)[1][1:] in FILE_EXTENSION_MEDIA])

        if dirpath != self._model.dirpath:  # Actual change of dirpath
            dirpath_old = self._model.dirpath
            self._model.dirpath = (dirpath, files)
            if dirpath_old != dirpath:
                self._watcher.removePaths(self._watcher.directories())
                self._watcher.addPath(dirpath)
        else:  # Update of the content
            _set_model_files = set(self._model.files)
            _set_files = set(files)

            #
            new_files = _set_files.difference(_set_model_files)
            deleted_files = _set_model_files.difference(_set_files)

            # TODO: Give more granularity to this and handle the addition of files event
            if len(new_files) > 0:  # We have new files or renamed file(s)
                self._model.files = files
            if len(deleted_files) > 0:  # Files have been deleted
                if self._model._media_path in deleted_files:
                    _old_files = self._model.files
                    idx = _old_files.index(self._model.media_path)
                    while _old_files[idx] in deleted_files and idx > 0:
                        idx = (idx + 1) % len(self._model.files)
                    # Select the first image in the current list that is still
                    self._model.files = files
                    path = _old_files[idx] if _old_files[idx] in files else files[0]
                    self.set_media_path(path)
                else:
                    self._model.files = files

    def set_media_path(self, path: str):
        if os.path.isfile(path) and self._model.media_path != path:
            self._watcher.removePaths(self._watcher.files())
            self._watcher.addPath(path)
            if os.path.dirname(path) != self._model.dirpath:
                self.update_dirpath(os.path.dirname(path))
            self._model.media_path = path

            # Load the comments
            ext = os.path.splitext(path)[1][1:]
            if ext in FILE_EXTENSION_PHOTO_JPG:
                self._model.media_comment = utils.ImageUserComment.load_from_file(path)

    def update_media_comment(self, comment):
        self._model.media_comment = comment

    def save_media_comment(self):
        self._model.media_comment.save_comment(self._model.media_path)

    def _next_media(self, incr = 1, extension = FILE_EXTENSION_MEDIA):
        idx0 = idx = self._model.files.index(self._model.media_path)

        def increment():
            _idx = (idx + incr) % len(self._model.files)
            path = self._model.files[_idx]
            filename, file_extension = os.path.splitext(path)
            file_extension = file_extension[1:]
            return _idx, file_extension

        while True:
            idx, ext = increment()
            if (ext in extension) or (idx == idx0):
                break
        path = self._model.files[idx]
        self.set_media_path(path)

    def select_next_media(self, extension= FILE_EXTENSION_MEDIA):
        self._next_media(incr=1, extension=extension)

    def select_prev_media(self, extension= FILE_EXTENSION_MEDIA):
        self._next_media(incr=-1,extension=extension)

    def delete_cur_media(self, extension= FILE_EXTENSION_MEDIA):
        file_to_delete = self._model.media_path
        self.select_next_media(extension=filter)
        send2trash(file_to_delete)
        self._model.remove_file_from_list(file_to_delete)

    def on_watcher_file_changed(self, filepath):
        # https://doc.qt.io/qt-5/qfilesystemwatcher.html
        # This signal is emitted when the file at the specified path is modified, renamed or removed from disk.
        if os.path.exists(filepath):
            if filepath not in self._watcher.files():  # Current file renamed ?
                # We remove all the files that we're watching. Normally one only
                self._watcher.removePaths(self._watcher.files())
                self._watcher.addPath(filepath)
            else:
                self._model.update_selected_file_content()
        else:
            # Selected image file has been deleted or renamed
            pass

    def on_watcher_dir_changed(self, dirpath):
        # https://doc.qt.io/qt-5/qfilesystemwatcher.html
        # Called  when the directory at a specified path is modified (e.g., when a file is added or deleted) or
        # removed from disk
        if dirpath == '':
            return
        if not os.path.exists(dirpath):
            # TODO: Update this
            pass
        else:
            # Content has been changed.
            self.update_dirpath(dirpath)
            # TODO: Update this to handle properly the content that has changed
            if dirpath not in self._watcher.directories():
                self._watcher.removePaths(self._watcher.directories())
                self._watcher.addPath(dirpath)
