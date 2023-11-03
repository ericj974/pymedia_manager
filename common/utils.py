from PyQt5.QtGui import QPixmap, QImage


def pixmap_from_frame(videoframe):
    if videoframe is None: return QPixmap()

    bytesPerLine = 3 * videoframe.shape[1]
    qimage = QImage(videoframe.copy(),
                    videoframe.shape[1],
                    videoframe.shape[0], bytesPerLine,
                    QImage.Format_RGB888)
    return QPixmap.fromImage(qimage)


def get_number_frames(clip):
    return int(clip.fps * clip.duration) if clip is not None else 0


def get_time_from_frame_number(clip, n):
    if get_number_frames(clip) > 0:
        return n / get_number_frames(clip) * clip.duration if n > -1 else clip.duration
    else:
        return 0
