from PyQt5.QtCore import QObject, pyqtSignal


class MainModel(QObject):
    # Change of directory path
    selected_dir_changed = pyqtSignal(str)
    # Change of selected picture file
    selected_media_changed = pyqtSignal(str)
    # Change of directory path
    selected_dir_content_changed = pyqtSignal(str)
    # Change of the content of the selected image (maybe it has been modified
    selected_file_content_changed = pyqtSignal(str)

    def __init__(self):
        super(MainModel, self).__init__()
        self._dir_path = ""
        self._media_path = ""
        self._files = []

    @property
    def dirpath(self):
        return self._dir_path

    @dirpath.setter
    def dirpath(self, value):
        dirpath, files = value
        self._dir_path = dirpath
        self._files = files
        self.selected_dir_changed.emit(dirpath)

    @property
    def media_path(self):
        return self._media_path

    @media_path.setter
    def media_path(self, file):
        self._media_path = file
        self.selected_media_changed.emit(file)

    @property
    def files(self):
        return self._files

    @files.setter
    def files(self, new_files: set):
        self._files = new_files
        self.selected_dir_content_changed.emit(self.dirpath)

    def remove_file_from_list(self, file):
        if file in self._files:
            self._files.remove(file)
            self.selected_dir_content_changed.emit(self.dirpath)

    def update_selected_file_content(self):
        self.selected_file_content_changed.emit(self.media_path)
