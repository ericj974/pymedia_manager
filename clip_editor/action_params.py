from nodes.base.dialog import ClipActionParams
import moviepy.video.fx.all as vfx

class RotationOrientation(object):
    cw = "cw"
    ccw = "ccw"

class FlipOrientation(object):
    none = "none"
    horizontal = 'horizontal'
    vertical = 'vertical'

class ClipRotateParams(ClipActionParams):
    action_type = "Rotate"

    def __init__(self, orientation=RotationOrientation.ccw, angle=0, name=None):
        super().__init__(name=name, action_type=ClipRotateParams.action_type)
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


class ClipFlipParams(ClipActionParams):
    action_type = "Flip"

    def __init__(self, orientation=FlipOrientation.none, name=None):
        super().__init__(name=name, action_type=ClipFlipParams.action_type)
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
