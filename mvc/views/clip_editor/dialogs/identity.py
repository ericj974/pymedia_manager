from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QToolButton, QStyle, QHBoxLayout

from common import utils
from common.videoclipplayer import VideoClipPlayer
from mvc.views.clip_editor.action_params import ClipIdentityParams
from mvc.views.clip_editor.dialogs.base import ClipActionDialog
from mvc.views.clip_editor.dialogs.identity_ui import Ui_Form


class ClipIdentityWidget(QWidget, Ui_Form):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        Ui_Form.__init__(self)
        self.setupUi(self)


class ClipIdentityDialog(ClipActionDialog):
    def __init__(self,
                 path,
                 parent=None,
                 params: ClipIdentityParams = None
                 ):
        super().__init__(parent, params)

        # The clip reader containing the clip to be processed
        self.clip_reader = VideoClipPlayer()

        self.path = path
        if path is not None:
            self.clip_reader.open_media(path, False)
            self.clip_reader.pause()
            clip = self.clip_reader.clip
        else:
            clip = None

        self.clip = clip
        self.view = ClipIdentityWidget(self)
        if clip is not None:
            self.update_fps_label(params.fps, clip.fps)
        if clip:
            self.view.frame_slider.setMaximum(utils.get_number_frames(clip))
        self.view.frame_slider.valueChanged.connect(self.goto_frame)

        # Rotation
        self.view.rotation_combo.currentIndexChanged.connect(self.rotation_selection_change)
        index = self.view.rotation_items.index(str(params.rotation))
        self.view.rotation_combo.setCurrentIndex(index)
        # self.clip = self.clip.add_mask().rotate(rot)

        # FPS
        self.view.fps_combo.currentIndexChanged.connect(self.fps_selection_change)
        index = self.view.fps_items.index(str(params.fps))
        self.view.fps_combo.setCurrentIndex(index)

        # Main Layout
        layout_main = QVBoxLayout(self)

        # Button + Layout
        iconSize = QSize(36, 36)
        button_validate = QToolButton()
        button_validate.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        button_validate.setIconSize(iconSize)
        button_validate.setToolTip("Validate")
        button_validate.clicked.connect(self.validate)

        layout_buttons = QHBoxLayout()
        layout_buttons.addStretch()
        layout_buttons.addWidget(button_validate)
        layout_buttons.addStretch()

        layout_main.addWidget(self.view)
        layout_main.addLayout(layout_buttons)
        self.setLayout(layout_main)

        self.resize(1280, 30)

    def update_params(self):
        index = self.view.rotation_combo.currentIndex()
        item = self.view.rotation_combo.itemText(index)
        self.params.rotation = int(item)

        index = self.view.fps_combo.currentIndex()
        item = self.view.fps_combo.itemText(index)
        self.params.fps = str(item)

    def goto_frame(self, frame_number):
        if self.clip is None:
            return

        rot = int(self.view.rotation_combo.currentText())
        clip = self.clip.add_mask().rotate(rot)

        seconds = utils.get_time_from_frame_number(clip, frame_number)
        _viewer = self.view.graphicsView_1
        try:
            frame = clip.get_frame(seconds) if clip is not None and seconds <= clip.duration else None
        except:
            return
        pix = utils.pixmap_from_frame(frame)
        _viewer.set_img(pix)

    def close(self):
        pass

    def rotation_selection_change(self, i):
        self.goto_frame(self.view.frame_slider.value())

    def fps_selection_change(self, i):
        fps_src = self.view.fps_combo.itemText(i)
        if self.path:
            self.clip_reader.open_media(path=self.path, play_audio=False, fps_source=fps_src)
            self.clip_reader.pause()
            self.clip = self.clip_reader.clip
            self.update_fps_label(fps_src, self.clip.fps)

    def update_fps_label(self, fps_src, fps):
        self.view.fps_label.setText(f"FPS info from {fps_src} "
                                    f"with value {fps}")
