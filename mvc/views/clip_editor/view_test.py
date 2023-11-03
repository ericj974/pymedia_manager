import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

import common.cv
from apps.clip_editor import default_file
from common.videoclipplayer import VideoClipPlayer
from mvc.controllers.main import MainController
from mvc.models.main import MainModel
from mvc.views.clip_editor.action_params import ClipCropperParams
from mvc.views.clip_editor.view import ClipEditorWindow

app = QApplication([sys.argv, '--no-sandbox'])
app.setAttribute(Qt.AA_DontShowIconsInMenus, True)


class BaseTest(unittest.TestCase):

    def setUp(self) -> None:
        # Create temporary directory for downloaded files
        self.out_dir = Path(tempfile.mkdtemp())
        # Test File
        self.test_file = Path(shutil.copy2(src=default_file, dst=self.out_dir / default_file.name))
        self.test_clip_reader = VideoClipPlayer(self.test_file)

        # MVC
        self.model = MainModel()
        self.controller = MainController(model=self.model)

    def reload(self):
        self.test_clip_reader = common.cv.load_image(self.test_file)

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
        self.config = {
            "AUTOPLAY": False
        }
        self.view = ClipEditorWindow(controller=self.controller, model=self.model, config=self.config)
        # Set image path via controller
        self.controller.set_media_path(self.test_file)

    def tearDown(self) -> None:
        super(ViewTest, self).tearDown()
        self.view.close()

    def test_media_content(self):
        # Tests proper loading of image
        self.assertIsNotNone(self.view.media_widget.clip_reader)
        self.assertIsNotNone(self.view.media_widget.clip_orig)

        self.assertEqual(self.test_clip_reader.fps, self.view.media_widget.clip_reader.fps)
        self.assertEqual(self.test_clip_reader.clip.duration, self.view.media_widget.clip_reader.clip.duration)

    def test_save_media(self):
        # Copy test file
        self.view.open_media(file=self.test_file)
        test_file_crop = self.out_dir / f"crop_{default_file.name}"

        # Perform a crop
        duration_out = 1.1
        params, _ = self.view.media_widget._update_create_action(ClipCropperParams)
        params.start_slider = 0
        params.stop_slider = duration_out * self.view.media_widget.clip_reader.fps

        # Save, Load and test
        self.view.media_widget.thread_save_media(self.test_file, test_file_crop, show_dialog=False)
        self.assertTrue(test_file_crop.is_file())
        self.view.open_media(file=test_file_crop)
        self.assertIsNotNone(self.view.media_widget.clip_reader)
        self.assertIsNotNone(self.view.media_widget.clip_orig)

        self.assertEqual(self.test_clip_reader.fps, self.view.media_widget.clip_reader.fps)
        self.assertAlmostEqual(self.view.media_widget.clip_reader.clip.duration, duration_out,
                               delta=2 / self.view.media_widget.clip_reader.fps)
