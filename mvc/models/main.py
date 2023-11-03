from pathlib import Path
from typing import List, Set

from PyQt5.QtCore import QObject, pyqtSignal

from common.comment import UserComment, TagEntity
from common.constants import FILE_EXTENSION_MEDIA
from common.db import TagDB


class MainModel(QObject):
    # Change of directory path
    selected_dir_changed = pyqtSignal(Path)
    # Change of selected picture file
    selected_media_changed = pyqtSignal(Path)
    # Update of selected media comment / metadata
    selected_media_comment_updated = pyqtSignal(UserComment)
    # Change of directory path
    selected_dir_content_changed = pyqtSignal(Path)
    # Change of the content of the selected image (maybe it has been modified
    selected_file_content_changed = pyqtSignal(Path)
    # Addition of a tag
    tag_added = pyqtSignal(TagEntity)

    def __init__(self, db_tags=None):
        super(MainModel, self).__init__()
        self._dir_path: Path = None
        self._media_path: Path = None
        self._media_comment: UserComment = None
        self._files: List[Path] = []
        self._db_tags: TagDB = db_tags if db_tags else TagDB()

    @property
    def dirpath(self) -> Path:
        return self._dir_path

    # @dirpath.setter
    # def dirpath(self, dirpath: Path):
    #     self._dir_path = dirpath
    #     # List content of the folder
    #     self._files = sorted([file for file in dirpath.glob('*') if file.is_file() and
    #                     file.suffix in FILE_EXTENSION_MEDIA])
    #     self.selected_dir_changed.emit(dirpath)

    @property
    def media_path(self) -> Path:
        return self._media_path

    @media_path.setter
    def media_path(self, file: Path):
        self._media_path = file
        self.selected_media_changed.emit(file)

    @property
    def media_comment(self) -> UserComment:
        return self._media_comment

    @media_comment.setter
    def media_comment(self, value: UserComment):
        self._media_comment = value
        self.selected_media_comment_updated.emit(value)

    @property
    def files(self) -> List[Path]:
        return self._files

    @files.setter
    def files(self, new_files: Set[Path]):
        parents = {i.parent for i in new_files}
        if len(parents) == 0:
            return
        # Ensure same parent dir
        assert len(parents) == 1
        dirpath = parents.pop()
        if dirpath != self.dirpath:
            self._dir_path = dirpath
            self.selected_dir_changed.emit(dirpath)

        self._files = sorted([file for file in new_files if file.is_file() and
                              file.suffix in FILE_EXTENSION_MEDIA])
        self.selected_dir_content_changed.emit(self.dirpath)

    @property
    def db_tags(self) -> TagDB:
        return self._db_tags

    def add_tag_to_db(self, tag: TagEntity):
        is_new = self.db_tags.add_to_db(tag)
        if is_new:
            self.tag_added.emit(tag)

    def set_db_tags_path(self, dirpath: Path):
        self._db_tags = TagDB(dirpath=dirpath)

    def remove_files_from_list(self, files: Set[Path]):
        temp = files.intersection(self._files)
        for file in temp:
            self._files.remove(file)
        if len(temp) > 0:
            self.selected_dir_content_changed.emit(self.dirpath)

    def add_files_to_list(self, files: Set[Path]):
        temp = files.union(self._files)
        self._files = sorted([file for file in temp if file.is_file() and
                            file.suffix in FILE_EXTENSION_MEDIA])
        self.selected_dir_changed.emit(self.dirpath)

    def update_selected_file_content(self):
        self.selected_file_content_changed.emit(self.media_path)
