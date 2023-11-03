from PyQt5 import QtCore
from PyQt5.QtCore import QSize, QRectF
from PyQt5.QtGui import QTransform
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QToolButton, QStyle, QHBoxLayout

from common import utils
from mvc.views.clip_editor.action_params import ClipZoomParams
from mvc.views.clip_editor.dialogs.base import ClipActionDialog
from mvc.views.clip_editor.dialogs.zoom_ui import Ui_Form


class ClipZoomWidget(QWidget, Ui_Form):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        Ui_Form.__init__(self)
        self.setupUi(self)


class ClipZoomDialog(ClipActionDialog):
    def __init__(self,
                 clip,
                 params: ClipZoomParams,
                 parent=None):
        super().__init__(parent, params)
        self.clip = clip
        self.view = ClipZoomWidget(self)

        self.view.frameSlider.valueChanged.connect(self.goto_frame)
        self.is_viewer_initialized = False

        # Main Layout
        layout_main = QVBoxLayout(self)
        layout_main.addWidget(self.view)

        # Button + Layout
        iconSize = QSize(36, 36)
        button_validate = QToolButton()
        button_validate.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        button_validate.setIconSize(iconSize)
        button_validate.setToolTip("Validate")
        button_validate.clicked.connect(self.validate)

        # 'Load image' button
        button_load = QToolButton(self)
        button_load.setText('Reload image')
        button_load.clicked.connect(self.reloadImages)

        layout_buttons = QHBoxLayout()
        layout_buttons.addStretch()
        layout_buttons.addWidget(button_validate)
        layout_buttons.addWidget(button_load)
        layout_buttons.addStretch()

        layout_main.addLayout(layout_buttons)
        self.setGeometry(500, 300, 800, 600)

        self.clip = clip
        n_frames = utils.get_number_frames(clip) if clip else 0
        self.view.frameSlider.setMaximum(n_frames)

        # Display the first frame
        self.goto_frame(0)

    def update_params(self):
        rect = self.visibleRect()
        zoom = self.view.graphicsView_1._zoom
        self.params.rect = [rect.x(), rect.y(), rect.width(), rect.height()]
        self.params.zoom = zoom

    def goto_frame(self, frame_number):
        to_seconds = utils.get_time_from_frame_number(self.clip, frame_number)
        self.goto_frame_viewer(to_seconds)

    def goto_frame_viewer(self, insecond):
        clip = self.clip
        _viewer = self.view.graphicsView_1
        try:
            frame = clip.get_frame(insecond) if insecond <= clip.duration else None
        except:
            return
        pix = utils.pixmap_from_frame(frame)
        _viewer.set_img(pix)
        if pix and not pix.isNull():
            rect = QtCore.QRectF(pix.rect())
            if not rect.isNull() and not self.is_viewer_initialized:
                self.init_photoViewer()

    def init_photoViewer(self):
        #
        if self.params.rect is None:
            self.update_params()
            return self.init_photoViewer()

        _viewer = self.view.graphicsView_1
        x, y, width, height = self.params.rect
        zoom = self.params.zoom

        # Was is initialized (first picture was in)
        self.is_viewer_initialized = True
        if self.params:
            _viewer.fitInView()
            rect = QRectF(x, y, width, height)
            _viewer.setSceneRect(rect)
            _viewer.centerOn(rect.center())

            mtx = QTransform().scale(_viewer.width() / rect.width(),
                                     _viewer.height() / rect.height())
            _viewer.setTransform(mtx)
            _viewer._zoom = zoom

    def reloadImages(self):
        pass

    def visibleRect(self):
        clip = self.clip
        _viewer = self.view.graphicsView_1
        # Return in the image original definition the rectangle
        return _viewer.mapToScene(_viewer.viewport().geometry()).boundingRect()

    def screenRect(self, number=0):
        _viewer = self.view.graphicsView_1
        return _viewer.viewport().geometry()
