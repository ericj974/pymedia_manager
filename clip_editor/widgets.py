from PyQt5.QtWidgets import QMessageBox

from clip_editor.action_params import ClipRotateParams, ClipFlipParams
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
        # thread = Thread(target=lambda: clip.write_videofile(file))
        if clip:
            try:
                # Make sure to stop file playing before writing (other file closed exception)
                self.clip_stop()
                clip.write_videofile(file)
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
        ind, params = self._update_create_action(ClipCropperParams)
        self.dialog = ClipCropperDialog(clip=self.get_processed_clip(ind),
                                        params=params,
                                        parent=self.parent)
        self.dialog.show()
        self.dialog.window_closing.connect(self.process_clip)

    def zoom_media(self):
        ind, params = self._update_create_action(ClipZoomParams)
        self.dialog = ClipZoomDialog(clip=self.get_processed_clip(ind),
                                     params=params,
                                     parent=self.parent)
        self.dialog.show()
        self.dialog.window_closing.connect(self.process_clip)

    def rotate_image_90(self, orientation):
        ind, params = self._update_create_action(ClipRotateParams)
        params.add_angle(90.0, orientation)
        self.process_clip()

    def flip_image(self, orientation):
        ind, params = self._update_create_action(ClipFlipParams)
        params.add_flip(orientation)
        self.process_clip()

    def change_brightness(self):
        pass

    def change_contrast(self):
        pass

    def process_clip(self):
        self.clip_stop()
        clip = self.get_processed_clip(ind=-1)
        self.set_clip(clip)

    def get_processed_clip(self, ind=-1):
        """
        Process the clip using action sequence pipeline up to (but excl.) the action indexed by ind
        :param ind:
        :return:
        """
        if self.clip_orig is None:
            return None
        else:
            clip = self.clip_orig
            for i, params in enumerate(self.action_pipeline):
                if i >= ind > -1:
                    break
                clip = params.process_clip(clip)
        return clip
