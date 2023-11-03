import logging
from pathlib import Path
from threading import Thread

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPalette, QImage, QPixmap
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QWidget, QLabel, QSizePolicy, QVBoxLayout, QCheckBox, QSlider, QSpinBox, \
    QGridLayout, QToolButton, QStyle, QHBoxLayout, QMessageBox

import common.cv
from common.constants import FILE_EXTENSION_VIDEO
from common.videoclipplayer import VideoClipPlayer, PlayerState
from common.widgets import Slider
from mvc.views.clip_editor.action_params import ClipRotateParams, ClipFlipParams, ClipLumContrastParams, \
    ClipConcatParams, \
    ClipCropperParams, ClipZoomParams, ClipActionParams
from mvc.views.clip_editor.dialogs.crop import ClipCropperDialog
from mvc.views.clip_editor.dialogs.zoom import ClipZoomDialog


class CallbackType:
    frameChanged = "frameChanged"


class ClipViewerWidget(QWidget):
    """
    The main editor / player for the clip to be processed
    """
    instance = None

    def __init__(self, parent=None):
        super(ClipViewerWidget, self).__init__(parent)
        self.parent = parent
        # Slider change listener
        self.slider_listener = None
        # The clip reader containing the clip to be processed
        self.clip_reader = VideoClipPlayer()

        self.label_movie = QLabel("No clip loaded")
        self.label_movie.setAlignment(Qt.AlignCenter)
        self.label_movie.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label_movie.setBackgroundRole(QPalette.Dark)
        self.label_movie.setAutoFillBackground(True)

        self.currentMovieDirectory = ''

        # Create controls
        self.checkbox_fit = QCheckBox("Fit to Window")

        self.label_frame = QLabel("Current frame:")

        self.slider_frame = Slider(Qt.Horizontal)
        self.slider_frame.setTickPosition(QSlider.TicksBelow)
        self.slider_frame.setTickInterval(10)

        self.label_speed = QLabel("Speed:")

        self.spinbox_speed = QSpinBox()
        self.spinbox_speed.setRange(1, 9999)
        self.spinbox_speed.setValue(100)
        self.spinbox_speed.setSuffix("%")

        self.layout_controls = QGridLayout()
        self.layout_controls.addWidget(self.checkbox_fit, 0, 0, 1, 2)
        self.layout_controls.addWidget(self.label_frame, 1, 0)
        self.layout_controls.addWidget(self.slider_frame, 1, 1, 1, 2)
        self.layout_controls.addWidget(self.label_speed, 2, 0)
        self.layout_controls.addWidget(self.spinbox_speed, 2, 1)

        # Create buttons
        icon_size = QSize(36, 36)

        self.btn_play = QToolButton()
        self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.btn_play.setIconSize(icon_size)
        self.btn_play.setToolTip("Play")
        self.btn_play.clicked.connect(self.clip_play)

        self.btn_pause = QToolButton()
        self.btn_pause.setCheckable(True)
        self.btn_pause.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.btn_pause.setIconSize(icon_size)
        self.btn_pause.setToolTip("Pause")
        self.btn_pause.clicked.connect(self.clip_pause)

        self.btn_stop = QToolButton()
        self.btn_stop.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.btn_stop.setIconSize(icon_size)
        self.btn_stop.setToolTip("Stop")
        self.btn_stop.clicked.connect(self.clip_stop)

        self.layout_buttons = QHBoxLayout()
        self.layout_buttons.addStretch()
        self.layout_buttons.addWidget(self.btn_play)
        self.layout_buttons.addWidget(self.btn_pause)
        self.layout_buttons.addWidget(self.btn_stop)
        self.layout_buttons.addStretch()

        # Callbacks
        self.clip_reader.set_video_frame_render_callback(self.update_slider_frame)

        # TODO
        # self.movie.stateChanged.connect(self.updateButtons)
        self.checkbox_fit.clicked.connect(self.fit_to_window)
        self.slider_frame.sliderMoved.connect(self.goto_frame)
        # TODO
        # self.speedSpinBox.valueChanged.connect(self.movie.setSpeed)

        layout_main = QVBoxLayout(self)
        layout_main.addWidget(self.label_movie)
        layout_main.addLayout(self.layout_controls)
        layout_main.addLayout(self.layout_buttons)
        self.setLayout(layout_main)

        self.update_slider_frame()
        self.update_buttons()

        self.setWindowTitle("Movie Player")
        self.resize(1280, 720)

        self.callbacks = {
            CallbackType.frameChanged: None
        }

    def set_callback(self, callback_type, callback_fn):
        self.callbacks[callback_type] = callback_fn

    def remove_callback(self, callback_type):
        self.callbacks[callback_type] = None

    def open_media(self, path: Path, play=True, play_audio=False, **kwargs):
        # Reset the current reader
        self.clip_reader.reset()
        self.label_movie.setText(path.name)
        if self.clip_reader.open_media(path, play_audio, **kwargs):
            self.update_slider_frame()
            self.update_buttons()
            self.goto_frame(0)
            self.clip_pause()
            if play:
                self.clip_play()

    def reset(self):
        # Reset the current reader
        self.clip_stop()
        self.clip_reader.reset()
        self.label_movie.setText("")
        self.slider_listener = None

    def set_clip(self, clip, reset=True):
        # Reset the current reader
        self.clip_stop()
        if reset:
            self.clip_reader.reset()
        self.label_movie.setText("")
        if self.clip_reader.load_clip(clip=clip):
            self.update_slider_frame()
            self.update_buttons()
            self.goto_frame(0)

    def goto_frame(self, frame):
        if self.clip_reader.fps is None:
            return
        frame_to_time = frame / self.clip_reader.fps
        self.clip_reader.seek(frame_to_time)
        self.clip_reader.render_video_frame()

    def fit_to_window(self):
        self.label_movie.setScaledContents(self.checkbox_fit.isChecked())

    def update_slider_frame(self, new_frame=None):
        has_frames = (self.clip_reader.currentFrameNumber() >= 0)

        if has_frames:
            if new_frame is None:
                new_frame = self.clip_reader.current_videoframe

            if self.clip_reader.frame_count() > 0:
                self.slider_frame.setMaximum(self.clip_reader.frame_count() - 1)
            elif self.clip_reader.currentFrameNumber() > self.slider_frame.maximum():
                self.slider_frame.setMaximum(self.clip_reader.currentFrameNumber())

            self.slider_frame.setValue(self.clip_reader.currentFrameNumber())

            if self.clip_reader.current_videoframe is not None:
                bytes_per_line = 3 * new_frame.shape[1]
                qimage = QImage(new_frame.copy(),
                                new_frame.shape[1],
                                new_frame.shape[0], bytes_per_line,
                                QImage.Format_RGB888)
                _pixmap = QPixmap.fromImage(qimage)
                self.label_movie.setPixmap(_pixmap)
                if self.callbacks[CallbackType.frameChanged]:
                    self.callbacks[CallbackType.frameChanged](_pixmap)
        else:
            self.slider_frame.setMaximum(0)

        self.label_frame.setEnabled(has_frames)
        self.slider_frame.setEnabled(has_frames)

        if self.slider_listener:
            self.slider_listener.updateSliders()

    def update_buttons(self):
        state = self.clip_reader.state()

        # Play Button state first
        self.btn_play.setEnabled(self.clip_reader.is_valid() and
                                 self.clip_reader.frame_count() != 1 and
                                 state != PlayerState.PLAYING)

        self.btn_pause.setEnabled(state != PlayerState.STOPPED)
        self.btn_pause.setChecked(state == PlayerState.PAUSED)
        self.btn_stop.setEnabled(state != PlayerState.STOPPED)

    def clip_play(self):
        if self.clip_reader.state() == PlayerState.PAUSED:
            self.clip_reader.pause()
        else:
            self.clip_reader.play()
        self.update_buttons()

    def clip_stop(self):
        self.clip_reader.stop()
        self.update_buttons()
        self.goto_frame(0)

    def clip_pause(self):
        self.clip_reader.pause()
        self.update_buttons()

    def closeEvent(self, event):
        pass


class ClipEditorWidget(ClipViewerWidget):
    # Change of directory path
    new_action_created = pyqtSignal(ClipActionParams)

    def __init__(self, parent=None, config=None):
        super(ClipEditorWidget, self).__init__(parent)
        # Pipeline / sequence of ClipActionParams. We assume actions are not permutable
        self.action_pipeline = []
        # The current opened dialog
        self.dialog = None
        # Save a copy of the original clip
        self.clip_orig = None

        # tmp pixmap to apply brightness / contrast etc...
        self.orig_videoframe = None
        self.timer_id = -1

        # Autoplay when opening a new file
        self.autoplay = config["AUTOPLAY"] if config else True

    def open_media(self, path, play_audio=True, **kwargs):
        super(ClipEditorWidget, self).open_media(path, self.autoplay, play_audio, **kwargs)
        self.clip_orig = self.clip_reader.clip

    def save_media(self, file, **kwargs):
        """ Save the media """
        thread = Thread(target=self.thread_save_media, args=(Path(self.clip_orig.filename), file))
        clip = self.get_processed_clip()
        if clip:
            try:
                # Make sure to stop file playing before writing (other file closed exception)
                self.clip_stop()
                thread.start()
            except Exception as e:
                QMessageBox.warning(self, "Save Media Error",
                                    str(e), QMessageBox.Ok)

    def thread_save_media(self, file, file_dest, show_dialog=True):
        """
        Perform the following actions.
        * Process clip from original file
        * Write to destination file
        TODO: Handle case where destination file == file
        """
        # Check that file exist
        if file == file_dest:
            msg = "Overwriting source file is not supported yet."
            if show_dialog:
                QMessageBox.warning(self, "", msg, QMessageBox.Ok)
            else:
                logging.warning(msg)
            return
        try:
            clip_reader = VideoClipPlayer()
            try:
                success = clip_reader.open_media(file, play_audio=True, fps_source='fps')
            except:
                success = clip_reader.open_media(file, play_audio=True, fps_source='tbr')

            if success:
                clip = clip_reader.clip
                clip = self.static_get_process_clip(clip, self.action_pipeline, ind=-1)
                clip.write_videofile(str(file_dest))
                msg = "Save Media Complete."
                if show_dialog:
                    QMessageBox.information(self, "Save Media", msg, QMessageBox.Ok)
                else:
                    logging.info(msg)
            else:
                msg = "Could not open Media."
                if show_dialog:
                    QMessageBox.warning(self, "Opening media error", msg, QMessageBox.Ok)
                else:
                    logging.warning("Opening media error: " + msg)
                return
        except Exception as e:
            QMessageBox.warning(self, "Save Media Error",
                                str(e), QMessageBox.Ok)

    def _index(self, action_type):
        for i, param in enumerate(self.action_pipeline):
            if param.action_type() == action_type:
                return i
        return -1

    def _update_create_action(self, cls):
        """
        Assumption: Actions are not permutable
        If the last action is identical, return it.
        Else create a new action.
        """
        if len(self.action_pipeline) > 0 and self.action_pipeline[-1].action_type() == cls.action_type():
            return self.action_pipeline[-1], False
        else:
            params = cls()
            self.action_pipeline.append(params)
            self.new_action_created.emit(params)
            return params, True

    def media_concat(self):
        self.clip_stop()
        extensions = ['*.' + ext for ext in FILE_EXTENSION_VIDEO]
        ext = "("
        for e in extensions:
            ext += e + " "
        ext += ")"

        file, _ = QFileDialog.getOpenFileName(self, "Open Media",
                                              "", f"Files {ext}")
        if file is not None:
            params, _ = self._update_create_action(ClipConcatParams)
            params.file2 = file
        self.process_clip()

    def media_crop(self):
        self.clip_stop()
        params, _ = self._update_create_action(ClipCropperParams)
        self.dialog = ClipCropperDialog(clip=self.get_processed_clip(),
                                        params=params,
                                        parent=self.parent)
        self.dialog.show()
        self.dialog.window_closing.connect(self.process_clip)

    def media_zoom(self):
        self.clip_stop()
        params, _ = self._update_create_action(ClipZoomParams)
        self.dialog = ClipZoomDialog(clip=self.get_processed_clip(),
                                     params=params,
                                     parent=self.parent)
        self.dialog.show()
        self.dialog.window_closing.connect(self.process_clip)

    def media_rotate_90(self, orientation):
        self.clip_stop()
        params, _ = self._update_create_action(ClipRotateParams)
        params.add_angle(90.0, orientation)
        self.process_clip()

    def media_flip(self, orientation):
        self.clip_stop()
        params, _ = self._update_create_action(ClipFlipParams)
        params.add_flip(orientation)
        self.process_clip()

    def media_set_lum_contrast(self, lum, contrast):
        if (lum < -255.) | (lum > 255.) | (contrast < -255.) | (contrast > 255.):
            return
        # Get current frame and apply the brightness change
        params, is_new_action = self._update_create_action(ClipLumContrastParams)
        params.set_luminosity(lum)
        params.set_contrast(contrast)

        # Get the clip before this action
        # (assumed to be the last action in the pipeline)
        if self.clip_reader.state() == PlayerState.PLAYING:
            self.clip_stop()
            clip = self.get_processed_clip(len(self.action_pipeline) - 1)
            self.orig_videoframe = clip.get_frame(self.clip_reader.clock.time)
        elif self.orig_videoframe is None or is_new_action:
            clip = self.get_processed_clip(len(self.action_pipeline) - 1)
            self.orig_videoframe = clip.get_frame(self.clip_reader.clock.time)

        # Apply current transformation to pixmap
        new_frame = params.process_im(self.orig_videoframe)
        qimage = common.cv.toQImage(new_frame, copy=True)
        _pixmap = QPixmap.fromImage(qimage)
        self.label_movie.setPixmap(_pixmap)

        if self.timer_id != -1:
            self.killTimer(self.timer_id)
        self.timer_id = self.startTimer(500)

    def process_clip(self):
        self.clip_stop()
        clip = self.get_processed_clip(ind=-1)
        self.set_clip(clip)

    def timerEvent(self, event):
        self.killTimer(self.timer_id)
        self.timer_id = -1
        self.orig_videoframe = None
        self.process_clip()

    @staticmethod
    def static_get_process_clip(clip_orig, action_pipeline, ind=-1):
        if clip_orig is None:
            return None
        else:
            clip = clip_orig
            for i, params in enumerate(action_pipeline):
                if i >= ind > -1:
                    break
                clip = params.process_clip(clip)
        return clip

    def get_processed_clip(self, ind=-1):
        """
        Process the clip using action sequence pipeline up to (but excl.) the action indexed by ind
        :param ind:
        :return:
        """
        return self.static_get_process_clip(self.clip_orig, self.action_pipeline, ind)
