from mvc.views.clip_editor.view_test import BaseTest
from mvc.views.clip_editor.widgets import ClipEditorWidget


class TestClipEditorWidget(BaseTest):

    def setUp(self) -> None:
        super(TestClipEditorWidget, self).setUp()
        self.config = {
            "AUTOPLAY": False
        }
        self.widget = ClipEditorWidget(config=self.config)

    def tearDown(self) -> None:
        super(TestClipEditorWidget, self).tearDown()
        self.widget.close()

    def test_open_media(self):
        pass

    def test_save_media(self):
        pass

    def test_media_concat(self):
        pass

    def test_media_crop(self):
        pass

    def test_media_zoom(self):
        pass

    def test_media_rotate_90(self):
        pass

    def test_media_flip(self):
        pass

    def test_media_set_lum_contrast(self):
        pass

    def test_process_clip(self):
        pass
