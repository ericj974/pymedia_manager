import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QApplication

import resources.test_clips as test_clips
import resources.test_db_faces as test_db_faces
import resources.test_db_tags as test_db_tags
import resources.test_pics as test_pics
from common import constants
from common.db import FaceDetectionDB, TagDB
from mvc.controllers.face import FaceDetectionController
from mvc.controllers.main import MainController
from mvc.models.face import FaceDetectionModel
from mvc.models.main import MainModel
from mvc.views.mainview.view import MediaManagementView

app = QApplication([sys.argv, '--no-sandbox'])
app.setAttribute(Qt.AA_DontShowIconsInMenus, True)

default_db_faces_folder = Path(test_db_faces.__file__).parent
default_db_tags_folder = Path(test_db_tags.__file__).parent
default_pics_folder = Path(test_pics.__file__).parent
default_clips_folder = Path(test_clips.__file__).parent
default_config = Path(constants.__file__).parent.parent / "config_default.json"


class BaseTest(unittest.TestCase):

    def setUp(self) -> None:
        # Create temporary directory and copy relevant directories
        self.out_dir = Path(tempfile.mkdtemp())
        self.pics_folder = self.out_dir / default_pics_folder.name
        self.clips_folder = self.out_dir / default_clips_folder.name
        shutil.copytree(default_pics_folder, self.pics_folder)
        shutil.copytree(default_clips_folder, self.clips_folder)
        with open(default_config, "r") as f:
            self.config = json.load(f)

        # MVC
        db = TagDB(default_db_tags_folder)
        self.model = MainModel(db_tags=db)
        self.controller = MainController(model=self.model)

        # MVC Local
        db = FaceDetectionDB(default_db_faces_folder)
        self.model_local = FaceDetectionModel(db=db)
        self.controller_local = FaceDetectionController(model=self.model_local)

    def reset(self):
        shutil.rmtree(self.pics_folder)
        shutil.rmtree(self.clips_folder)
        shutil.copytree(default_pics_folder, self.pics_folder)
        shutil.copytree(default_clips_folder, self.clips_folder)

    def tearDown(self) -> None:
        # cleanup temporary directory
        shutil.rmtree(self.out_dir)


class ViewTest(BaseTest):
    def setUp(self) -> None:
        super(ViewTest, self).setUp()
        self.view = MediaManagementView(controller=self.controller, model=self.model, config=self.config)
        self.test_pic = self.pics_folder / 'lenna.jpg'
        self.test_clip = self.clips_folder / 'woman-58142.mp4'

        # Set image dir
        self.controller.update_dirpath(self.pics_folder)

    def tearDown(self) -> None:
        super(ViewTest, self).tearDown()

    def test_launch_renamer(self):
        # Set media path via controller
        self.controller.set_media_path(self.test_pic)

        # Open view
        self.view.pushButton_renamer.click()
        self.assertIsNotNone(self.view.win_renamer)

    def test_launch_editor_img(self):
        # Set media path via controller
        self.controller.set_media_path(self.test_pic)

        # Open view
        self.view.pushButton_editor_img.click()
        self.assertIsNotNone(self.view.win_img_editor)

        # Tests proper loading of image
        self.assertIsNotNone(self.view.win_img_editor.media_widget.qimage)
        self.assertIsNotNone(self.view.win_img_editor.media_widget.qimage_orig)
        self.assertIsNotNone(self.view.win_img_editor.media_widget.qimage_ex)
        self.assertEqual(QImage(str(self.test_pic)), self.view.win_img_editor.media_widget.qimage)

        # Set clip path via controller
        self.controller.set_media_path(self.test_clip)

        # Tests that editor has been reset
        self.assertEqual(self.view.win_img_editor.media_widget.qimage, QImage())
        self.assertEqual(self.view.win_img_editor.media_widget.qimage_orig, QImage())
        self.assertEqual(self.view.win_img_editor.media_widget.qimage_ex, QImage())

    def test_launch_editor_vid(self):
        # Set media path via controller
        self.controller.set_media_path(self.test_clip)

        # Open view
        self.view.pushButton_editor_vid.click()
        self.assertIsNotNone(self.view.win_vid_editor)

        # Tests proper loading of clip
        self.assertIsNotNone(self.view.win_vid_editor.media_widget.clip_reader.clip)
        self.assertIsNotNone(self.view.win_vid_editor.media_widget.clip_reader.path)

        # Set media path via controller
        self.controller.set_media_path(self.test_pic)

        # Test that the pic has not been loaded
        self.assertIsNone(self.view.win_vid_editor.media_widget.clip_reader.clip)
        self.assertIsNone(self.view.win_vid_editor.media_widget.clip_reader.path)

    def test_launch_tile_view(self):
        # Set media path via controller
        self.controller.set_media_path(self.test_pic)

        # Open view
        self.view.pushButton_tileview.click()
        self.assertIsNotNone(self.view.win_tiles)

    # def test_launch_gps_window(self):
    #     # Set media path via controller
    #     self.controller.set_media_path(self.test_pic)
    #
    #     # Open view
    #     self.view.pushButton_gps.click()
    #     self.assertIsNotNone(self.view.win_gps)

    def test_launch_face_editor_batch(self):
        # Set media path via controller
        self.controller.set_media_path(self.test_pic)

        # Open view
        self.view.launch_face_editor_batch()
        self.assertIsNotNone(self.view.win_batch_faces)

    def test_pics_folder_content_loaded(self):
        test_pic = self.pics_folder / 'lenna.jpg'

        # Set media path via controller
        self.controller.set_media_path(test_pic)

        # Open Image editor
        self.view.pushButton_editor_img.click()
        self.assertIsNotNone(self.view.win_img_editor)

        # Tests proper loading of image
        self.assertIsNotNone(self.view.win_img_editor.media_widget.qimage)
        self.assertIsNotNone(self.view.win_img_editor.media_widget.qimage_orig)
        self.assertIsNotNone(self.view.win_img_editor.media_widget.qimage_ex)
        self.assertEqual(QImage(str(test_pic)), self.view.win_img_editor.media_widget.qimage)

        # Open Clip editor
        self.view.pushButton_editor_vid.click()
        self.assertIsNotNone(self.view.win_vid_editor)

        # Test that the pic has not been loaded
        self.assertIsNone(self.view.win_vid_editor.media_widget.clip_reader.clip)
        self.assertIsNone(self.view.win_vid_editor.media_widget.clip_reader.path)
