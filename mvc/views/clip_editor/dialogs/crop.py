from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QVBoxLayout, QToolButton, QStyle, QHBoxLayout, QWidget

from common import utils
from mvc.views.clip_editor.action_params import ClipCropperParams
from mvc.views.clip_editor.dialogs.base import ClipActionDialog
from mvc.views.clip_editor.dialogs.crop_ui import Ui_Form


class ClipCropperWidget(QWidget, Ui_Form):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        Ui_Form.__init__(self)
        self.setupUi(self)


class ClipCropperDialog(ClipActionDialog):

    def __init__(self,
                 clip,
                 params: ClipCropperParams,
                 parent=None
                 ):
        super().__init__(parent, params)
        self.clip = clip
        self.view = ClipCropperWidget(self)

        if clip is not None:
            n_frames = utils.get_number_frames(clip)
            self.params.start_slider = min(self.params.start_slider, n_frames)
            self.params.stop_slider = min(self.params.stop_slider,
                                          n_frames) if self.params.stop_slider > -1 else n_frames

        if clip is not None:
            self.view.start_slider.setMaximum(utils.get_number_frames(clip))
            self.view.stop_slider.setMaximum(utils.get_number_frames(clip))

        self.view.start_slider.setValue(self.params.start_slider)
        self.view.stop_slider.setValue(self.params.stop_slider)

        self.view.start_slider.valueChanged.connect(self.start_slider_goto_frame)
        self.view.stop_slider.valueChanged.connect(self.stop_slider_goto_frame)

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

        # Display the first frame
        self.goto_frame_viewer(0)

    def update_params(self):
        self.params.start_slider = self.view.start_slider.value()
        self.params.stop_slider = self.view.stop_slider.value()

    def start_slider_goto_frame(self, frame_number):
        seconds = utils.get_time_from_frame_number(self.clip, frame_number)
        self.goto_frame_viewer(seconds)
        if self.view.stop_slider.value() < frame_number:
            self.view.stop_slider.setValue(frame_number)

    def stop_slider_goto_frame(self, frame_number):
        seconds = utils.get_time_from_frame_number(self.clip, frame_number)
        self.goto_frame_viewer(seconds)
        if self.view.start_slider.value() > frame_number:
            self.view.start_slider.setValue(frame_number)

    def goto_frame_viewer(self, seconds):
        if self.clip is None:
            return
        clip = self.clip
        _viewer = self.view.graphicsView_1
        try:
            frame = clip.get_frame(seconds) if seconds <= clip.duration else None
        except:
            return
        pix = utils.pixmap_from_frame(frame)
        _viewer.set_img(pix)
