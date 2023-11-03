from pathlib import Path

import cv2
import numpy as np
import piexif
from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QTransform, qRgb


def image_resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    dim = None
    (h, w) = image.shape[:2]

    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # resize the image
    resized = cv2.resize(image, dim, interpolation=inter)

    # return the resized image
    return resized


def load_image(path: Path) -> (QImage, dict):
    """
    Load an image and rotate if orientation exif tag
    """
    # This step is necessary to load the exif
    try:
        img = Image.open(str(path))
        qimage = QImage(str(path))
    except:
        return QImage(), None

    # exif data.
    exif_dict = piexif.load(img.info['exif']) if 'exif' in img.info else {}
    # Remove orientation metadata
    if "0th" in exif_dict and piexif.ImageIFD.Orientation in exif_dict["0th"]:
        orientation = exif_dict["0th"].pop(piexif.ImageIFD.Orientation)
        transforms = []
        if orientation == 2:  # Flip left / right
            transforms = [QTransform().scale(1, -1)]
        elif orientation == 3:  # rotate 180
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


def toCvMat(qimage: QImage):
    '''  Converts a QImage into an opencv MAT format  '''

    qimage = qimage.convertToFormat(QImage.Format.Format_RGB32)
    ptr = qimage.constBits()
    ptr.setsize(qimage.byteCount())
    cv_im_in = np.array(ptr, copy=True).reshape(qimage.height(), qimage.width(), 4)
    cv_im_in = cv2.cvtColor(cv_im_in, cv2.COLOR_BGRA2RGB)
    return cv_im_in


def toQImage(im: np.array, copy=False):
    if im is None:
        return QImage()

    if im.dtype == np.uint8:
        if len(im.shape) == 2:
            qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_Indexed8)
            qim.setColorTable(gray_color_table)
            return qim.copy() if copy else qim

        elif len(im.shape) == 3:
            if im.shape[2] == 3:
                qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_RGB888)
                return qim.copy() if copy else qim
            elif im.shape[2] == 4:
                qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_ARGB32)
                return qim.copy() if copy else qim


gray_color_table = [qRgb(i, i, i) for i in range(256)]
