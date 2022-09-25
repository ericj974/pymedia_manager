import datetime
import json
import os

import numpy as np
from PIL import Image
import piexif
import piexif.helper
import pytz
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QTransform, qRgb

from tzwhere import tzwhere

user_comment_template = {
    'tags': [],
    'comments': ""
}

# GPS -> Timezone
TZWHERE = tzwhere.tzwhere()


def get_exif_v2(filepath):
    assert os.path.exists(filepath), 'File ' + filepath + 'does not exist'
    try:
        exif_dict = piexif.load(filepath)
        # See bug https://github.com/hMatoba/Piexif/issues/95
        try:
            del exif_dict['Exif'][piexif.ExifIFD.SceneType]
        except:
            pass
    except KeyError:
        print(f"Cannot find exif for image {filepath}")
        return None
    return exif_dict


def get_exif_user_comment(filepath):
    exif_dict = get_exif_v2(filepath)
    if piexif.ExifIFD.UserComment in exif_dict["Exif"]:
        try:
            user_comment = piexif.helper.UserComment.load(exif_dict["Exif"][piexif.ExifIFD.UserComment])
            return json.loads(user_comment)
        except:
            return user_comment_template.copy()
    return user_comment_template.copy()


def update_user_comment(exif_dict, userdata):
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(json.dumps(userdata),
                                                                                   encoding='unicode')


def save_exif(exif_dict, filepath):
    assert os.path.exists(filepath)
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, filepath)


def print_exif(exif):
    for ifd in exif:
        print(f'{ifd}:')
        try:
            for tag in exif[ifd]:
                tag_name = piexif.TAGS[ifd][tag]["name"]
                tag_value = exif[ifd][tag]
                if isinstance(tag_value, bytes):
                    tag_value = tag_value.decode("utf-8")
                print(f'\t{tag_name}: {tag_value}')
        except:
            pass


def get_datetime_exiftool(exif):
    def correct_time_jpg_from_gps(t, exif):
        if 'EXIF:GPSLatitude' in exif and 'EXIF:GPSLongitude' in exif:
            lat = exif['EXIF:GPSLatitude']
            lat = -lat if (exif['EXIF:GPSLatitudeRef'] == 'S') else lat
            lng = exif['EXIF:GPSLongitude']
            lng = -lng if (exif['EXIF:GPSLongitudeRef'] == 'W') else lng
            timezone_str = TZWHERE.tzNameAt(lat, lng)  # coordinates
            timezone = pytz.timezone(timezone_str)
            return t + timezone.utcoffset(t)

        # No gps coords. We will compare 'File:FileModifyDate' to t
        file_modify_datetime = datetime.datetime.strptime(exif['File:FileModifyDate'], '%Y:%m:%d %H:%M:%S%z')
        delta_with_t = t - (file_modify_datetime.replace(tzinfo=None) - file_modify_datetime.utcoffset())
        if delta_with_t.total_seconds() < 60.0:
            return file_modify_datetime.replace(tzinfo=None)

        # Here we
        raise NotImplementedError()

    def correct_time_quicktime_from_gps(t, exif):
        key = 'QuickTime:GPSCoordinates'

        # Try to offset the time using gps coords lat, lng
        if key in exif:
            lat, lng = exif[key].split(" ")
            lat, lng = float(lat), float(lng)
            timezone_str = TZWHERE.tzNameAt(lat, lng)  # coordinates
            timezone = pytz.timezone(timezone_str)
            return t + timezone.utcoffset(t)

        # No gps coords. We will compare 'File:FileModifyDate' to t
        file_modify_datetime = datetime.datetime.strptime(exif['File:FileModifyDate'], '%Y:%m:%d %H:%M:%S%z')
        delta_with_t = t - (file_modify_datetime.replace(tzinfo=None) - file_modify_datetime.utcoffset())
        if delta_with_t.total_seconds() < 60.0:
            return file_modify_datetime.replace(tzinfo=None)

        # Here we
        raise NotImplementedError()

    keys_dict = {'EXIF:DateTimeOriginal': None, 'H264:DateTimeOriginal': None,
                 'QuickTime:MediaCreateDate': correct_time_quicktime_from_gps, 'ASF:CreationDate': None}
    try:
        key = set(keys_dict.keys()).intersection(exif.keys()).pop()
    except TypeError as e:
        key = None
    if key:
        try:
            t = datetime.datetime.strptime(exif[key],
                                           '%Y:%m:%d %H:%M:%S')
            # Update t by taking into account timezone of where the media was taken
            if keys_dict[key] is not None:
                t = keys_dict[key](t, exif)

        except ValueError as v:
            if len(v.args) > 0 and v.args[0].startswith('unconverted data remains: '):
                # remove +XX at the end
                t = datetime.datetime.strptime(exif[key][:-6],
                                               '%Y:%m:%d %H:%M:%S')
            else:
                raise
        except NotImplementedError as v:  # Catch unable to find timezone
            raise
        return t


# https://developer.here.com/blog/getting-started-with-geocoding-exif-image-metadata-in-python3
def get_geotagging(exif):
    if not exif or 'GPS' not in exif:
        return None
    return exif['GPS']


def update_geotagging(exif, lng, lat):
    """
    Update piexif GPS tags from latitude and longitude in decimal degrees
    :param exif:
    :param lng:
    :param lat:
    :return:
    """
    if exif is None:
        exif = {}
    if "GPS" not in exif:
        exif["GPS"] = {}
    exif["GPS"][piexif.GPSIFD.GPSLatitudeRef] = b'S' if lat < 0 else b'N'
    exif["GPS"][piexif.GPSIFD.GPSLatitude] = deg_to_dms(lat)
    exif["GPS"][piexif.GPSIFD.GPSLongitudeRef] = b'W' if lng < 0 else b'E'
    exif["GPS"][piexif.GPSIFD.GPSLongitude] = deg_to_dms(lng)
    return exif


def deg_to_dms(degFloat):
    """
    Convert decimal degrees to piexif repr of Degrees, Minutes, Seconds
    1.305140852777778 -> ((1, 1), (18, 1), (18507070, 1000000))
    :param degFloat:
    :return:
    """
    degFloat = abs(degFloat)
    deg = int(degFloat)
    min = int((degFloat - deg) * 60)
    sec = int((degFloat - deg - min / 60) * 3600 * 1000000)
    return ((deg, 1), (min, 1), (sec, 1000000))


def dms_to_deg(dms, ref):
    """
    Convert Degrees, Minutes, Seconds to decimal degrees
    ((1, 1), (18, 1), (18507070, 1000000)) -> 1.305140852777778
    :param dms:
    :param ref:
    :return:
    """
    try:
        ref = ref.decode('utf-8')
    except:
        pass
    try:
        degrees = dms[0][0] / dms[0][1]
        minutes = dms[1][0] / dms[1][1] / 60.0
        seconds = dms[2][0] / dms[2][1] / 3600.0

        if ref in ['S', 'W']:
            degrees = -degrees
            minutes = -minutes
            seconds = -seconds

        return degrees + minutes + seconds
    except:
        return ''


def deg_to_mercator(lng, lat):
    """
    Switch from decimal degrees lat/long to mercator coordinates
    :param x:
    :param y:
    :return:
    """

    r_major = 6378137.000
    x = r_major * np.radians(lng)
    scale = x / lng
    y = 180.0 / np.pi * np.log(np.tan(np.pi / 4.0 +
                                      lat * (np.pi / 180.0) / 2.0)) * scale
    return (x, y)


def load_image(file):
    """
    Load an image and rotate if orientation exif tag
    """
    # This step is necessary to load the exif
    try:
        img = Image.open(file)
        qimage = QImage(file)
    except:
        return QImage(), None

    # exif data.
    exif_dict = piexif.load(img.info['exif']) if 'exif' in img.info else {}
    # Remove orientation metadata
    if "0th" in exif_dict and piexif.ImageIFD.Orientation in exif_dict["0th"]:
        orientation = exif_dict["0th"].pop(piexif.ImageIFD.Orientation)
        transforms = []
        if orientation == 2: # Flip left / right
            transforms = [QTransform().scale(1, -1)]
        elif orientation == 3: # rotate 180
            transforms = [QTransform().rotate(180)]
        elif orientation == 4:
            transforms = [QTransform().rotate(180), QTransform().scale(1, -1)]
        elif orientation == 5:
            transforms = [QTransform().rotate(90), QTransform().scale(1, -1)]
        elif orientation == 6:
            transforms = [QTransform().rotate(90)]
        elif orientation == 7:
            transforms = [QTransform().rotate(-90), QTransform().scale(1, -1)]
        elif orientation == 8:
            transforms = [QTransform().rotate(-90)]

        for t in transforms:
            qimage = qimage.transformed(t, mode=Qt.SmoothTransformation)
    return qimage, exif_dict

gray_color_table = [qRgb(i, i, i) for i in range(256)]

def toQImage(im, copy=False):
    if im is None:
        return QImage()

    if im.dtype == np.uint8:
        if len(im.shape) == 2:
            qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_Indexed8)
            qim.setColorTable(gray_color_table)
            return qim.copy() if copy else qim

        elif len(im.shape) == 3:
            if im.shape[2] == 3:
                qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_RGB888);
                return qim.copy() if copy else qim
            elif im.shape[2] == 4:
                qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_ARGB32);
                return qim.copy() if copy else qim