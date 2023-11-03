import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QTransform, QPixmap
from PyQt5.QtWidgets import QApplication

import common.cv
import resources.test_db_faces as test_db_faces
import resources.test_db_tags as test_db_tags
from apps.img_editor import default_file
from common.db import FaceDetectionDB, TagDB
from mvc.controllers.face import FaceDetectionController
from mvc.controllers.main import MainController
from mvc.models.face import FaceDetectionModel
from mvc.models.main import MainModel
from mvc.views.img_editor.view import PhotoEditorWindow

app = QApplication([sys.argv, '--no-sandbox'])
app.setAttribute(Qt.AA_DontShowIconsInMenus, True)

default_db_faces_folder = Path(test_db_faces.__file__).parent
default_db_tags_folder = Path(test_db_tags.__file__).parent


class BaseTest(unittest.TestCase):

    def setUp(self) -> None:
        # Create temporary directory for downloaded files
        self.out_dir = Path(tempfile.mkdtemp())
        # Test File
        self.test_file: Path = shutil.copy2(src=default_file, dst=self.out_dir / default_file.name)
        self.test_qimage, _ = common.cv.load_image(self.test_file)
        self.test_pixmap = QPixmap().fromImage(self.test_qimage)
        self.test_cv_img = common.cv.toCvMat(self.test_qimage)

        # MVC
        db = TagDB(default_db_tags_folder)
        self.model = MainModel(db_tags=db)
        self.controller = MainController(model=self.model)

        # MVC Local
        db = FaceDetectionDB(default_db_faces_folder)
        self.model_local = FaceDetectionModel(db=db)
        self.controller_local = FaceDetectionController(model=self.model_local)

    def reload(self):
        self.test_qimage, _ = common.cv.load_image(self.test_file)
        self.test_pixmap = QPixmap().fromImage(self.test_qimage)
        self.test_cv_img = common.cv.toCvMat(self.test_qimage)

    def new_test_file(self, action_name: str) -> str:
        # Copy test file
        test_file = shutil.copy2(src=default_file, dst=self.out_dir / f"{action_name}_{default_file.name}")
        return test_file

    def tearDown(self) -> None:
        # cleanup temporary directory
        shutil.rmtree(self.out_dir)


class ViewTest(BaseTest):
    def setUp(self) -> None:
        super(ViewTest, self).setUp()
        self.view = PhotoEditorWindow(controller=self.controller, model=self.model,
                                      controller_local=self.controller_local, model_local=self.model_local)
        # Set image path via controller
        self.controller.set_media_path(self.test_file)

    def tearDown(self) -> None:
        super(ViewTest, self).tearDown()
        self.view.close()

    def test_image_content(self):
        # Tests proper loading of image
        self.assertIsNotNone(self.view.media_widget.qimage)
        self.assertIsNotNone(self.view.media_widget.qimage_orig)
        self.assertIsNotNone(self.view.media_widget.qimage_ex)
        self.assertEqual(QImage(str(self.test_file)), self.view.media_widget.qimage)

    def test_comment_content(self):
        # Test proper loading of user comment on the comment toolbar
        user_comment = self.view.comment_toolbar.get_user_comment()
        # Comment
        self.assertEqual(user_comment.comment.data, 'comment1')
        # Tag
        self.assertEqual(len(user_comment.tags), 1)
        self.assertEqual(user_comment.tags[0].name, 'tag1')
        # Person
        self.assertEqual(len(user_comment.persons), 1)
        self.assertEqual(user_comment.persons[0].name, 'lenna')

    def test_save_media(self):
        # Copy test file
        test_file_flip = self.new_test_file("flip")
        self.view.open_media(file=test_file_flip)

        # Perform a flip
        self.view.flip_vertical.trigger()
        self.assertEqual(
            QImage(str(self.test_file)).transformed(QTransform().scale(1, -1), mode=Qt.SmoothTransformation),
            self.view.media_widget.qimage)

        # Save, Load and test
        self.view.save_media(file=test_file_flip)
        self.view.open_media(file=test_file_flip)
        self.assertIsNotNone(self.view.media_widget.qimage)
        self.assertIsNotNone(self.view.media_widget.qimage_orig)
        self.assertIsNotNone(self.view.media_widget.qimage_ex)

        # Test that comment is being saved
        self.test_comment_content()
