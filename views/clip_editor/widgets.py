from threading import Thread

from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QMessageBox, QFileDialog

from common.state import PlayerState
from constants import FILE_EXTENSION_VIDEO
from nodes.dialogs.concat import ClipConcatParams
from views.clip_editor.action_params import ClipRotateParams, ClipFlipParams, ClipLumContrastParams
from common.clipreader import ClipReader
from nodes.clip_editor import ClipViewerWidget
from nodes.dialogs.crop import ClipCropperParams, ClipCropperDialog
from nodes.dialogs.zoom import ClipZoomParams, ClipZoomDialog


class ClipEditorWidget(ClipViewerWidget):
    def __init__(self, parent=None):
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

    def open_media(self, filepath, play=True, play_audio=False):
        super(ClipEditorWidget, self).open_media(filepath, play, play_audio)
        self.clip_orig = self.clip_reader.clip

    def save_media(self, file, **kwargs):
        """ Save the media """
        clip = self.get_processed_clip()
        thread = Thread(target=self.thread_save_media, args=(self.clip_orig.filename, file))
        if clip:
            try:
                # Make sure to stop file playing before writing (other file closed exception)
                self.clip_stop()
                # clip.write_videofile(file)
                thread.start()
            except Exception as e:
                QMessageBox.warning(self, "Save Media Error",
                                    str(e), QMessageBox.Ok)

    def thread_save_media(self, file, file_dest):
        """
        Perform the following actions.
        * Process clip from original file
        * Write to destination file
        TODO: Handle case where destination file == file
        """
        # Check that file exist
        if file == file_dest:
            QMessageBox.warning(self, "",
                                "Overwriting source file is not supported yet.", QMessageBox.Ok)
            return
        try:
            clip_reader = ClipReader()
            if clip_reader.load_mediafile(file, play_audio=False):
                clip = clip_reader.clip
                clip = self.static_get_process_clip(clip, self.action_pipeline, ind=-1)
                clip.write_videofile(file_dest)
                QMessageBox.information(self, "Save Media", "Save Media Complete.", QMessageBox.Ok)
            else:
                QMessageBox.warning(self, "Opening media error", "Could not open Media.", QMessageBox.Ok)
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
            return self.action_pipeline[-1]
        else:
            params = cls()
            self.action_pipeline.append(params)
            return params
    
    def concat_media(self):
        self.clip_stop()
        extensions = ['*.' + ext for ext in FILE_EXTENSION_VIDEO]
        ext = "("
        for e in extensions:
            ext += e + " "
        ext += ")"

        file, _ = QFileDialog.getOpenFileName(self, "Open Media",
                                              "", f"Files {ext}")
        if file is not None:
            params = self._update_create_action(ClipConcatParams)
            params.file2 = file
        self.process_clip()
                
    def crop_media(self):
        self.clip_stop()
        params = self._update_create_action(ClipCropperParams)
        self.dialog = ClipCropperDialog(clip=self.get_processed_clip(),
                                        params=params,
                                        parent=self.parent)
        self.dialog.show()
        self.dialog.window_closing.connect(self.process_clip)

    def zoom_media(self):
        self.clip_stop()
        params = self._update_create_action(ClipZoomParams)
        self.dialog = ClipZoomDialog(clip=self.get_processed_clip(),
                                     params=params,
                                     parent=self.parent)
        self.dialog.show()
        self.dialog.window_closing.connect(self.process_clip)

    def rotate_image_90(self, orientation):
        self.clip_stop()
        params = self._update_create_action(ClipRotateParams)
        params.add_angle(90.0, orientation)
        self.process_clip()

    def flip_image(self, orientation):
        self.clip_stop()
        params = self._update_create_action(ClipFlipParams)
        params.add_flip(orientation)
        self.process_clip()

    def timerEvent(self, event):
        self.killTimer(self.timer_id)
        self.timer_id = -1
        self.orig_videoframe = None
        self.process_clip()

    def change_lum_contrast(self, lum, contrast):
        if lum < -255 | lum > 255 | contrast < -255 | contrast > 255:
            return
        # Get the clip before this action
        # (assumed to be the last action in the pipeline)
        clip = self.get_processed_clip(len(self.action_pipeline) - 1)
        if self.clip_reader.state() == PlayerState.PLAYING:
            self.clip_stop()
            self.orig_videoframe =  clip.get_frame(self.clip_reader.clock.time)
        elif self.orig_videoframe is None:
            self.orig_videoframe = clip.get_frame(self.clip_reader.clock.time)

        # Get current frame and apply the bightness change

        params = self._update_create_action(ClipLumContrastParams)
        params.set_luminosity(lum)
        params.set_contrast(contrast)

        # Apply current transformation to pixmap
        new_frame = params.process_im(self.orig_videoframe)
        bytes_per_line = 3 * new_frame.shape[1]
        qimage = QImage(new_frame.copy(),
                        new_frame.shape[1],
                        new_frame.shape[0], bytes_per_line,
                        QImage.Format_RGB888)
        _pixmap = QPixmap.fromImage(qimage)
        self.label_movie.setPixmap(_pixmap)

        if self.timer_id != -1:
            self.killTimer(self.timer_id)
        self.timer_id = self.startTimer(500)

    def process_clip(self):
        self.clip_stop()
        clip = self.get_processed_clip(ind=-1)
        self.set_clip(clip)

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
