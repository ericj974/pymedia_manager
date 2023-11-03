import cv2
from PyQt5.QtCore import QRect

import common.cv
from mvc.views.clip_editor.action_params import ClipLumContrastParams
from mvc.views.img_editor.view_test import BaseTest
from mvc.views.img_editor.widgets import ImageLabel


class ImageLabelTest(BaseTest):
    def setUp(self) -> None:
        super(ImageLabelTest, self).setUp()
        self.widget = ImageLabel()
        # Ensure the widget size is the same as the img size.
        # This is for operations on display like crop which refers to actual display size
        self.widget.setFixedSize(self.test_qimage.size())
        self.reload()

    def tearDown(self) -> None:
        super(ImageLabelTest, self).tearDown()

    def reload(self):
        super(ImageLabelTest, self).reload()
        self.widget.open_media(path=self.test_file)

    def test_img_crop(self):
        self.reload()
        # Init
        h, w = int(self.test_cv_img.shape[0] / 2), int(self.test_cv_img.shape[1] / 2)
        qrect = QRect(0, 0, w, h)
        # Action
        self.widget.img_crop(qrect)
        img1 = self.widget.qimage
        arr1 = common.cv.toCvMat(img1)
        # Target action
        arr2 = self.test_cv_img[:h, :w]
        self.assertTrue((arr1 == arr2).all())

    def test_img_rotate_90_cw(self):
        self.reload()
        # Action
        self.widget.img_rotate_90("cw")
        img1 = self.widget.qimage
        arr1 = common.cv.toCvMat(img1)
        # Target action
        arr2 = cv2.rotate(self.test_cv_img, cv2.ROTATE_90_CLOCKWISE)
        self.assertTrue((arr1 == arr2).all())

    def test_img_rotate_90_ccw(self):
        self.reload()
        # Action
        self.widget.img_rotate_90("ccw")
        img1 = self.widget.qimage
        arr1 = common.cv.toCvMat(img1)
        # Target action
        arr2 = cv2.rotate(self.test_cv_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        self.assertTrue((arr1 == arr2).all())

    def test_img_flip_h(self):
        self.reload()

        # Action
        self.widget.img_flip("horizontal")
        img1 = self.widget.qimage
        arr1 = common.cv.toCvMat(img1)
        # Target action
        arr2 = cv2.flip(self.test_cv_img, 1)
        self.assertTrue((arr1 == arr2).all())

    def test_img_flip_v(self):
        self.reload()

        # Action
        self.widget.img_flip("vertical")
        img1 = self.widget.qimage
        arr1 = common.cv.toCvMat(img1)
        # Target action
        arr2 = cv2.flip(self.test_cv_img, 0)
        self.assertTrue((arr1 == arr2).all())

    def test_img_rotate_cw(self):
        self.reload()
        # Action
        self.widget.img_rotate_90("cw")
        img1 = self.widget.qimage
        arr1 = common.cv.toCvMat(img1)
        # Target action
        arr2 = cv2.rotate(self.test_cv_img, cv2.ROTATE_90_CLOCKWISE)
        self.assertTrue((arr1 == arr2).all())

    def test_img_rotate_ccw(self):
        self.reload()
        # Action
        self.widget.img_rotate_90("ccw")
        img1 = self.widget.qimage
        arr1 = common.cv.toCvMat(img1)
        # Target action
        arr2 = cv2.rotate(self.test_cv_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        self.assertTrue((arr1 == arr2).all())

    def test_img_set_lum_contrast(self):
        self.reload()
        lum = -255.
        contrast = 0.
        # Action
        self.widget.img_set_lum_contrast(lum=lum, contrast=contrast)
        img1 = self.widget.qimage
        arr1 = common.cv.toCvMat(img1)
        # Target action
        arr2 = ClipLumContrastParams(lum=lum, contrast=contrast).process_im(self.test_cv_img)
        self.assertTrue((arr1 == arr2).all())
