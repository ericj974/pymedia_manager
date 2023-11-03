import datetime
import json
from pathlib import Path

import piexif
import piexif.helper
import pytz
import timezonefinder

from common.coords import deg_to_dms, dms_to_deg

user_comment_template = {
    'persons': [],  # name. We don't keep the position in the picture
    'tags': [],
    'comments': ""
}

# GPS -> Timezone
TF = timezonefinder.TimezoneFinder()


def get_exif(path: Path):
    assert path.is_file(), f"{path} does not exist or is not a file"

    try:
        exif_dict = piexif.load(str(path))
        # See bug https://github.com/hMatoba/Piexif/issues/95
        try:
            del exif_dict['Exif'][piexif.ExifIFD.SceneType]
        except:
            pass
    except KeyError:
        print(f"Cannot find exif for image {path}")
        return None
    return exif_dict


def get_lng_lat(file):
    exif = get_exif(file)
    if exif is not None and \
            'GPS' in exif and \
            piexif.GPSIFD.GPSLongitude in exif['GPS'] and \
            piexif.GPSIFD.GPSLatitude in exif['GPS']:
        lng = dms_to_deg(exif['GPS'][piexif.GPSIFD.GPSLongitude],
                         exif['GPS'][piexif.GPSIFD.GPSLongitudeRef])
        lat = dms_to_deg(exif['GPS'][piexif.GPSIFD.GPSLatitude],
                         exif['GPS'][piexif.GPSIFD.GPSLatitudeRef])
    else:
        lng, lat = None, None
    return lng, lat


def get_user_comment(filepath):
    exif_dict = get_exif(filepath)
    if piexif.ExifIFD.UserComment in exif_dict["Exif"]:
        try:
            user_comment = piexif.helper.UserComment.load(exif_dict["Exif"][piexif.ExifIFD.UserComment])
            return json.loads(user_comment)
        except:
            return user_comment_template.copy()
    return user_comment_template.copy()


def set_user_comment(exif_dict, userdata):
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(json.dumps(userdata),
                                                                                   encoding='unicode')


def save_exif(exif_dict, path: Path):
    assert path.is_file()
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, str(path))


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
    def correct_time_quicktime_from_gps(t, exif):
        raise NotImplementedError()

    keys_dict = {("Exif", piexif.ExifIFD.DateTimeOriginal): None}
    try:
        keys_in_dict = {(k1, k2) for k1 in exif if isinstance(exif[k1], dict) for k2 in exif[k1]}
        key_tuple = set(keys_dict.keys()).intersection(keys_in_dict).pop()
    except TypeError as e:
        key_tuple = None
    if key_tuple:
        try:
            t = datetime.datetime.strptime(exif[key_tuple[0]][key_tuple[1]].decode('ascii'),
                                           '%Y:%m:%d %H:%M:%S')
            # Update t by taking into account timezone of where the media was taken
            if keys_dict[key_tuple] is not None:
                t = keys_dict[key_tuple](t, exif)

        except ValueError as v:
            if len(v.args) > 0 and v.args[0].startswith('unconverted data remains: '):
                # remove +XX at the end
                t = datetime.datetime.strptime(exif[key_tuple[0]][key_tuple[1]][:-6].decode('ascii'),
                                               '%Y:%m:%d %H:%M:%S')
            else:
                raise
        except NotImplementedError as v:  # Catch unable to find timezone
            raise
        return t


# def get_datetime_exiftool(exif):
#     def correct_time_jpg_from_gps(t, exif):
#         if 'EXIF:GPSLatitude' in exif and 'EXIF:GPSLongitude' in exif:
#             lat = exif['EXIF:GPSLatitude']
#             lat = -lat if (exif['EXIF:GPSLatitudeRef'] == 'S') else lat
#             lng = exif['EXIF:GPSLongitude']
#             lng = -lng if (exif['EXIF:GPSLongitudeRef'] == 'W') else lng
#             timezone_str = TF.certain_timezone_at(lat, lng)  # coordinates
#             timezone = pytz.timezone(timezone_str)
#             return t + timezone.utcoffset(t)
#
#         # No gps coords. We will compare 'File:FileModifyDate' to t
#         file_modify_datetime = datetime.datetime.strptime(exif['File:FileModifyDate'], '%Y:%m:%d %H:%M:%S%z')
#         delta_with_t = t - (file_modify_datetime.replace(tzinfo=None) - file_modify_datetime.utcoffset())
#         if delta_with_t.total_seconds() < 60.0:
#             return file_modify_datetime.replace(tzinfo=None)
#
#         # Here we
#         raise NotImplementedError()
#
#     def correct_time_quicktime_from_gps(t, exif):
#         key = 'QuickTime:GPSCoordinates'
#
#         # Try to offset the time using gps coords lat, lng
#         if key in exif:
#             lat, lng = exif[key].split(" ")
#             lat, lng = float(lat), float(lng)
#             tz = pytz.timezone(TF.timezone_at(lng=lng, lat=lat))
#             return t + t.astimezone(tz).utcoffset()
#
#         # No gps coords. We will compare 'File:FileModifyDate' to t
#         file_modify_datetime = datetime.datetime.strptime(exif['File:FileModifyDate'], '%Y:%m:%d %H:%M:%S%z')
#         delta_with_t = t - (file_modify_datetime.replace(tzinfo=None) - file_modify_datetime.utcoffset())
#         if delta_with_t.total_seconds() < 60.0:
#             return file_modify_datetime.replace(tzinfo=None)
#
#         # Here we
#         raise NotImplementedError()
#
#     keys_dict = {'EXIF:DateTimeOriginal': None, 'H264:DateTimeOriginal': None,
#                  'QuickTime:MediaCreateDate': correct_time_quicktime_from_gps, 'ASF:CreationDate': None}
#     try:
#         key = set(keys_dict.keys()).intersection(exif.keys()).pop()
#     except TypeError as e:
#         key = None
#     if key:
#         try:
#             t = datetime.datetime.strptime(exif[key],
#                                            '%Y:%m:%d %H:%M:%S')
#             # Update t by taking into account timezone of where the media was taken
#             if keys_dict[key] is not None:
#                 t = keys_dict[key](t, exif)
#
#         except ValueError as v:
#             if len(v.args) > 0 and v.args[0].startswith('unconverted data remains: '):
#                 # remove +XX at the end
#                 t = datetime.datetime.strptime(exif[key][:-6],
#                                                '%Y:%m:%d %H:%M:%S')
#             else:
#                 raise
#         except NotImplementedError as v:  # Catch unable to find timezone
#             raise
#         return t


# https://developer.here.com/blog/getting-started-with-geocoding-exif-image-metadata-in-python3
def get_geotagging(exif):
    if not exif or 'GPS' not in exif:
        return None
    return exif['GPS']


def set_geotagging(exif, lng, lat):
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
