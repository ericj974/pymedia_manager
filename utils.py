import datetime
import os

import numpy as np
import piexif
from PIL import Image


# cf https://www.blog.pythonlibrary.org/2010/03/28/getting-photo-metadata-exif-using-python/
def get_exif(filepath):
    assert os.path.exists(filepath), 'File ' + filepath + 'does not exist'
    image = Image.open(filepath)
    try:
        exif_dict = piexif.load(image.info["exif"])
    except KeyError:
        print(f"Cannot find exif for image {filepath}")
        return None
    return exif_dict


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


def get_datetime(exif):
    if piexif.ExifIFD.DateTimeOriginal in exif['Exif']:
        return datetime.datetime.strptime(exif['Exif'][piexif.ExifIFD.DateTimeOriginal].decode("utf-8"),
                                          '%Y:%m:%d %H:%M:%S')
    elif piexif.ExifIFD.DateTimeDigitized in exif['Exif']:
        return datetime.datetime.strptime(exif['Exif'][piexif.ExifIFD.DateTimeDigitized].decode("utf-8"),
                                          '%Y:%m:%d %H:%M:%S')
    elif piexif.ImageIFD.DateTime in exif['0th']:
        return datetime.datetime.strptime(exif['0th'][piexif.ImageIFD.DateTime].decode("utf-8"),
                                          '%Y:%m:%d %H:%M:%S')

def get_datetime_exiftool(exif):
    keys = {'EXIF:DateTimeOriginal', 'H264:DateTimeOriginal',
            'QuickTime:MediaCreateDate', 'ASF:CreationDate'}
    try:
        key = keys.intersection(exif.keys()).pop()
    except TypeError as e:
        key = None
    if key:
        try:
            t = datetime.datetime.strptime(exif[key],
                                          '%Y:%m:%d %H:%M:%S')
        except ValueError as v:
            if len(v.args) > 0 and v.args[0].startswith('unconverted data remains: '):
                # remove +XX at the end
                t = datetime.datetime.strptime(exif[key][:-6],
                                               '%Y:%m:%d %H:%M:%S')
            else:
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
