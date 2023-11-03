from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QVBoxLayout, QToolButton, QStyle, QHBoxLayout

from common import utils
from mvc.views.clip_editor.action_params import ClipConcatParams
from mvc.views.clip_editor.dialogs.base import ClipActionDialog
from mvc.views.clip_editor.dialogs.identity import ClipIdentityWidget


class ClipConcatDialog(ClipActionDialog):
    def __init__(self,
                 clip,
                 parent=None,
                 params: ClipConcatParams = None
                 ):
        super().__init__(parent, params)

        self.clip = clip
        self.view = ClipIdentityWidget(self)
        self.view.rotation_combo.setVisible(False)
        self.view.rotation_label.setVisible(False)
        self.view.fps_combo.setVisible(False)
        self.view.fps_label.setVisible(False)
        self.view.frame_slider.valueChanged.connect(self.goto_frame)

        # Main Layout
        layout_main = QVBoxLayout(self)

        # Button + Layout
        icon_size = QSize(36, 36)
        button_validate = QToolButton()
        button_validate.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        button_validate.setIconSize(icon_size)
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
        pass

    def goto_frame(self, frame_number):
        clip = self.clip

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
