import datetime
import re
import uuid
from pathlib import Path

from PyQt5.QtCore import QRectF
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.fx import all as vfx
from moviepy.video.io.VideoFileClip import VideoFileClip

from common import nameddic, utils
from common.keys import Keys
from common.videoclipplayer import VideoClipPlayer


class RotationOrientation(object):
    cw = "cw"
    ccw = "ccw"


class FlipOrientation(object):
    none = "none"
    horizontal = 'horizontal'
    vertical = 'vertical'


class ClipActionParams(nameddic):

    def __init__(self, name=None, action_id=None):
        self.name = name if name else ClipActionParams.action_type()
        self.action_id = uuid.uuid1().int if not action_id else action_id
        self.parents_id = []

    @staticmethod
    def action_type():
        raise NotImplementedError()


class ClipRotateParams(ClipActionParams):

    def __init__(self, angle=0, name=None):
        super().__init__(name=name if name else self.action_type())
        # in degrees, counter clockwise
        self.angle = angle

    def process_clip(self, clip):
        if clip is None:
            return clip
        clip = clip.fx(vfx.rotate, angle=self.angle, unit='deg')
        return clip

    def add_angle(self, angle, orientation=RotationOrientation.ccw):
        angle = angle if orientation == RotationOrientation.cw else -1.0 * angle
        self.angle += angle

    @staticmethod
    def action_type():
        return "Rotate"


class ClipFlipParams(ClipActionParams):

    def __init__(self, name=None):
        super().__init__(name=name if name else self.action_type())
        # Horizontal Flip Flag
        self.mirror_x = False
        # Vertical Flip Falg
        self.mirror_y = False

    def process_clip(self, clip):
        if clip is None:
            return clip
        if self.mirror_x:
            clip = clip.fx(vfx.mirror_x)
        if self.mirror_y:
            clip = clip.fx(vfx.mirror_y)
        return clip

    def add_flip(self, orientation):
        if orientation == FlipOrientation.horizontal:
            self.mirror_x = not self.mirror_x
        elif orientation == FlipOrientation.vertical:
            self.mirror_y = not self.mirror_y

    @staticmethod
    def action_type():
        return "Flip"


class ClipLumContrastParams(ClipActionParams):

    def __init__(self, lum: float = 0, contrast: float = 0, name=None):
        super().__init__(name=name if name else self.action_type())
        # Brightness
        self.lum = lum
        self.contrast = contrast
        self.contrast_thr = 128.

    def set_luminosity(self, value: float):
        self.lum = value

    def set_contrast(self, value: float):
        self.contrast = value

    def process_im(self, im):
        # See https://www.dfstudios.co.uk/articles/programming/image-programming-algorithms/image-processing-algorithms-part-5-contrast-adjustment/
        f = 259. * (self.contrast + 255.) / (255. * (259 - self.contrast))
        frame = im.astype('float')
        new_frame = f * (frame - self.contrast_thr) + self.contrast_thr + self.lum
        new_frame[new_frame < 0] = 0
        new_frame[new_frame > 255] = 255
        return new_frame.astype('uint8')

    def process_clip(self, clip):
        return clip.fl_image(self.process_im)

    @staticmethod
    def action_type():
        return "LuminosityContrast"


class ClipConcatParams(ClipActionParams):
    def __init__(self, file2=None, name=None):
        super().__init__(name=name if name else self.action_type())
        self.file2 = file2

    @staticmethod
    def action_type():
        return "Concat"

    def process_clip(self, clip1, clip2=None):
        if clip2 is None:
            if self.file2 is None:
                return clip1
            else:
                clip_reader = VideoClipPlayer()
                if clip_reader.open_media(self.file2, play_audio=False):
                    clip2 = clip_reader.clip
                else:
                    return clip1
        elif clip1 is None:
            return clip2
        # Method = compose to avoid glitch when concatenating due to diff in fps / resolution
        return concatenate_videoclips([clip1, clip2], method='compose')


class ClipCropperParams(ClipActionParams):

    def __init__(self, start_slider=0, stop_slider=-1, name=None):
        super().__init__(name=name if name else self.action_type())
        # in frame number
        self.start_slider = start_slider
        self.stop_slider = stop_slider

    def process_clip(self, clip):
        if clip is None:
            return clip
        frame_to_time_start = utils.get_time_from_frame_number(clip, self.start_slider)
        frame_to_time_stop = utils.get_time_from_frame_number(clip, self.stop_slider)
        clip_out = clip.subclip(frame_to_time_start, frame_to_time_stop) if clip else None
        return clip_out

    @staticmethod
    def action_type():
        return "Crop"


class ClipZoomParams(ClipActionParams):

    def __init__(self, rect=None, zoom=0, name=None):
        super().__init__(name=name if name else self.action_type())
        self.rect = rect
        self.zoom = zoom

    def process_clip(self, clip):
        if clip is None:
            return clip
        # Get the rect in the viewrect
        if self.rect:
            x1, y1, width1, height1 = self.rect
        else:
            x1, y1 = 0.0, 0.0
            width1, height1 = clip.size
        # Remove the black borders
        dx = min(0.0, x1)
        dy = min(0.0, y1)
        rect = QRectF(max(0.0, x1),
                      max(0.0, y1),
                      width1 + 2 * dx,
                      height1 + 2 * dy)
        # Convert to image view
        center = rect.center()
        (x_center, y_center) = center.x(), center.y()
        temp = clip.fx(vfx.crop,
                       x_center=x_center,
                       y_center=y_center,
                       width=int(rect.width()),
                       height=int(rect.height()))
        _factor = round(int(min(clip.size[0] / rect.width(), clip.size[1] / rect.height())))
        clip_out = temp.fx(vfx.resize, _factor)
        return clip_out

    @staticmethod
    def action_type():
        return "Zoom"


class ClipStackParams(ClipActionParams):
    def __init__(self, rect1=None, zoom1=0, rect1_screen=None,
                 rect2=None, zoom2=0, rect2_screen=None,
                 rect3=None, zoom3=0, rect3_screen=None,
                 name=None):
        super().__init__(name=name if name else self.action_type())
        # ROI of the left image
        self.rect1 = rect1
        self.zoom1 = zoom1
        # Ratio to get back to the actual screen size
        self.rect1_screen = rect1_screen

        self.rect2 = rect2
        self.zoom2 = zoom2
        self.rect2_screen = rect2_screen

        self.rect3 = rect3
        self.zoom3 = zoom3
        self.rect3_screen = rect3_screen

    @staticmethod
    def action_type():
        return "Stack"

    def process_clip(self, clip1, clip2, clip3=None):
        # PROCESS CLIP 1
        # TODO: Update this
        # Get the image rect in the viewrect
        x, y, width, height = self.rect1
        # Remove the black borders
        dx = min(0.0, x)
        dy = min(0.0, y)
        rect = QRectF(max(0.0, x),
                      max(0.0, y),
                      width + 2 * dx,
                      height + 2 * dy)
        # Convert to image view
        center = rect.center()
        (x_center, y_center) = center.x(), center.y()
        temp1 = clip1.fx(vfx.crop,
                         x_center=x_center,
                         y_center=y_center,
                         width=int(rect.width()),
                         height=int(rect.height()))
        _factor = (min(clip1.size[0] / rect.width(), clip1.size[1] / rect.height()))
        temp1 = temp1.fx(vfx.resize, _factor)

        # PROCESS CLIP 2 if any
        if clip2 is not None:
            # Get the rect in the viewrect
            x, y, width, height = self.rect2
            dx = min(0.0, x)
            dy = min(0.0, y)
            rect2 = QRectF(max(0.0, x),
                           max(0.0, y),
                           width + 2 * dx,
                           height + 2 * dy)
            # Convert to image view
            center = rect2.center()
            (x_center, y_center) = center.x(), center.y()
            temp2 = clip2.fx(vfx.crop,
                             x_center=x_center,
                             y_center=y_center,
                             width=int(rect2.width()),
                             height=int(rect2.height()))

            ratio_x = self.rect1_screen[2] / self.rect2_screen[2]
            ratio_y = self.rect1_screen[3] / self.rect2_screen[3]
            ratio = min(temp1.size[0] / temp2.size[0] / ratio_x, temp1.size[1] / temp2.size[1] / ratio_y)
            temp2 = temp2.fx(vfx.resize, ratio)

        # PROCESS CLIP 3 if any
        if clip3 is not None:
            # Get the rect in the viewrect
            x, y, width, height = self.rect3
            dx = min(0.0, x)
            dy = min(0.0, y)
            rect3 = QRectF(max(0.0, x),
                           max(0.0, y),
                           width + 2 * dx,
                           height + 2 * dy)
            # Convert to image view
            center = rect3.center()
            (x_center, y_center) = center.x(), center.y()
            temp3 = clip3.fx(vfx.crop,
                             x_center=x_center,
                             y_center=y_center,
                             width=int(rect3.width()),
                             height=int(rect3.height()))

            ratio_x = self.rect1_screen[2] / self.rect2_screen[2]
            ratio_y = self.rect1_screen[3] / self.rect2_screen[3]
            ratio = min(temp1.size[0] / temp3.size[0] / ratio_x, temp1.size[1] / temp3.size[1] / ratio_y)
            temp3 = temp3.fx(vfx.resize, ratio)

        # Composite
        if clip2 is None:
            output = clip1
        else:
            output = CompositeVideoClip([temp1,
                                         temp2.set_position(("right", "top"))],
                                        size=(temp1.size[0] + temp2.size[0],
                                              temp1.size[1])
                                        )
            output = output.set_duration(max(clip1.duration, clip2.duration))
        return output


class ClipIdentityParams(ClipActionParams):

    def __init__(self, rotation=0, name=None):
        super().__init__(name=name if name else self.action_type())
        self.clip_id = self.action_id
        self.rotation = rotation
        self.fps = 'tbr'

    def process_clip(self, path: Path):
        if not path:
            return None, None
        clip = VideoFileClip(str(path), audio=False, fps_source=self.fps)
        clip_info = {Keys.PATH: path}
        match = re.match("([0-9]{2})-([0-9]{4})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2}).*", path.name)
        if match:
            _datetime = re.search("([0-9]{4})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})", path.name)
            _datetime = datetime.datetime.strptime(_datetime.group(), '%Y%m%d%H%M%S')
            clip_info[Keys.DATETIME] = _datetime
        clip = clip.add_mask().rotate(self.rotation)
        return clip, clip_info

    @staticmethod
    def action_type():
        return "Identity"
