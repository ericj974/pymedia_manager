import numpy as np


def deg_to_dms(deg: float):
    """
    Convert decimal degrees to piexif repr of Degrees, Minutes, Seconds
    1.305140852777778 -> ((1, 1), (18, 1), (18507070, 1000000))
    :param deg: Decimal degrees
    :return:
    """
    deg = abs(deg)
    deg = int(deg)
    min = int((deg - deg) * 60)
    sec = int((deg - deg - min / 60) * 3600 * 1000000)
    return (deg, 1), (min, 1), (sec, 1000000)


def dms_to_deg(dms, ref):
    """
    Convert Degrees, Minutes, Seconds to decimal degrees
    ((1, 1), (18, 1), (18507070, 1000000)) -> 1.305140852777778
    :param dms: Degrees, Minutes, Seconds
    :param ref: Direction ('S', 'W', 'E' or 'N')
    :return: decimal degrees
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
        return None


def deg_to_mercator(lng, lat):
    """
    Switch from decimal degrees lat/long to mercator coordinates
    """

    r_major = 6378137.000
    x = r_major * np.radians(lng)
    scale = x / lng
    y = 180.0 / np.pi * np.log(np.tan(np.pi / 4.0 +
                                      lat * (np.pi / 180.0) / 2.0)) * scale
    return x, y
