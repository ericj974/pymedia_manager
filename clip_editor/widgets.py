from threading import Thread

from PyQt5.QtWidgets import QMessageBox

from clip_editor.action_params import ClipRotateParams, ClipFlipParams, ClipBrightnessParams
from common.clipreader import ClipReader
from nodes.clip_editor import ClipViewerWidget
from nodes.dialogs.crop import ClipCropperParams, ClipCropperDialog
from nodes.dialogs.zoom import ClipZoomParams, ClipZoomDialog


class ClipEditorWidget(ClipViewerWidget):
    def __init__(self, parent=None):
        super(ClipEditorWidget, self).__init__(parent)
        # Pipeline / sequence of ClipActionParams. Rotations and Flips will be one single action
        # instead of cumulative actions as the user updates the rotation
        # For simplicity, we will add flip and rotations first.
        # Reason behind is that user will usually rotate the video before cropping and zooming,
        # and rotation -> zoom is different from zoom -> rotation, so order will be enforced
        self.action_pipeline = [ClipRotateParams(), ClipFlipParams()]
        # The current opened dialog
        self.dialog = None
        # Save a copy of the original clip
        self.clip_orig = None

    def open_media(self, filepath, play=True, play_audio=False):
        super(ClipEditorWidget, self).open_media(filepath, play, play_audio)
        self.clip_orig = self.clip_reader.clip

    def save_media(self, file, **kwargs):
        """ Save the media """
        # TODO: Separate thread for this which implies a deep copy of the original movie (and file ?)
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
        * Write to temp file if overwrite else write to destination file
        :return:
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
            if param.action_type == action_type:
                return i
        return -1

    def _update_create_action(self, cls):
        ind = self._index(cls.action_type)
        if ind > -1:
            return ind, self.action_pipeline[ind]
        else:
            params = cls()
            self.action_pipeline.append(params)
            return -1, params

    def crop_media(self):
        self.clip_stop()
        ind, params = self._update_create_action(ClipCropperParams)
        self.dialog = ClipCropperDialog(clip=self.get_processed_clip(ind),
                                        params=params,
                                        parent=self.parent)
        self.dialog.show()
        self.dialog.window_closing.connect(self.process_clip)

    def zoom_media(self):
        self.clip_stop()
        ind, params = self._update_create_action(ClipZoomParams)
        self.dialog = ClipZoomDialog(clip=self.get_processed_clip(ind),
                                     params=params,
                                     parent=self.parent)
        self.dialog.show()
        self.dialog.window_closing.connect(self.process_clip)

    def rotate_image_90(self, orientation):
        self.clip_stop()
        ind, params = self._update_create_action(ClipRotateParams)
        params.add_angle(90.0, orientation)
        self.process_clip()

    def flip_image(self, orientation):
        self.clip_stop()
        ind, params = self._update_create_action(ClipFlipParams)
        params.add_flip(orientation)
        self.process_clip()

    def change_brightness(self, value):
        if value < -255 | value > 255:
            return

        self.clip_stop()
        ind, params = self._update_create_action(ClipBrightnessParams)
        params.set_brightness(value)
        self.process_clip()

    def change_contrast(self):
        pass

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
