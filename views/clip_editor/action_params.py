import moviepy.video.fx.all as vfx

from nodes.dialogs.base import ClipActionParams


class RotationOrientation(object):
    cw = "cw"
    ccw = "ccw"


class FlipOrientation(object):
    none = "none"
    horizontal = 'horizontal'
    vertical = 'vertical'


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

    def __init__(self, lum=0, contrast=0, name=None):
        super().__init__(name=name if name else self.action_type())
        # Brightness
        self.lum = lum
        self.contrast = contrast
        self.contrast_thr = 128.

    def set_luminosity(self, value):
        self.lum = value

    def set_contrast(self, value):
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
