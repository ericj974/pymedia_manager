from PyQt5.QtCore import QObject, pyqtSignal


class MainModel(QObject):
    # Change of directory path
    selected_dir_changed = pyqtSignal(str)
    # Change of selected picture file
    selected_image_changed = pyqtSignal(str)
    # Change of directory path
    selected_dir_content_changed = pyqtSignal(str)
    # Change of the content of the selected image (maybe it has been modified
    selected_file_content_changed = pyqtSignal(str)

    def __init__(self):
        super(MainModel, self).__init__()
        self._dirpath = ""
        self._imagepath = ""
        self._files = []

    @property
    def dirpath(self):
        return self._dirpath

    @dirpath.setter
    def dirpath(self, value):
        dirpath, files = value
        self._dirpath = dirpath
        self._files = files
        self.selected_dir_changed.emit(dirpath)

    @property
    def imagepath(self):
        return self._imagepath

    @imagepath.setter
    def imagepath(self, file):
        self._imagepath = file
        self.selected_image_changed.emit(file)

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
        self.selected_file_content_changed.emit(self.imagepath)
