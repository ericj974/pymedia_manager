import piexif
from PIL import Image
from PIL import ImageQt
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QImage, QPixmap, QTransform, QColor, qRgb, QPalette, QKeySequence
from PyQt5.QtWidgets import QLabel, QRubberBand, QSizePolicy, QShortcut


class State:
    normal = "normal"
    crop = "crop"


class ImageLabel(QLabel):
    """Subclass of QLabel for displaying image"""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.qimage = QImage()
        self.original_image = self.qimage

        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.setBackgroundRole(QPalette.Base)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setScaledContents(True)

        # Load image
        self.setPixmap(QPixmap().fromImage(self.qimage))
        self.setAlignment(Qt.AlignCenter)

        # Is cropping state
        self.state = State.normal

        # Shortcut to exit any editing mode
        self.exit_edit_state_sc = QShortcut(QKeySequence('Esc'), self)
        self.exit_edit_state_sc.activated.connect(lambda: self.set_state(State.normal))
        self.cancel_sc = QShortcut(QKeySequence('Ctrl+Z'), self)
        self.cancel_sc.activated.connect(self.revertToOriginal)

    def load_image(self, file):
        # This step is necessary to load the exif
        image = Image.open(file)
        self.qimage = ImageQt.ImageQt(image)
        if self.qimage.isNull():
            return
        pixmap = QPixmap().fromImage(self.qimage)
        self.setPixmap(pixmap)
        # Keep a copy of the image
        self.original_image = self.qimage.copy()
        # exif data.
        self.exif_dict = piexif.load(image.info['exif']) if 'exif' in image.info else {}
        # Remove orientation metadata
        if piexif.ImageIFD.Orientation in self.exif_dict["0th"]:
            self.exif_dict["0th"].pop(piexif.ImageIFD.Orientation)

    def save(self, imagepath):
        try:
            self.exif_dict['Exif'][41729] = str(self.exif_dict['Exif'][41729]).encode("ascii")
        except:
            pass
        if 'thumbnail' in self.exif_dict:
            del self.exif_dict['thumbnail']
        exif_bytes = piexif.dump(self.exif_dict)
        ImageQt.fromqimage(self.qimage).save(imagepath, exif=exif_bytes, optimize=True, quality=95)

    def clearImage(self):
        """ """
        pass

    def revertToOriginal(self):
        """Revert the image back to original image."""
        self.qimage = self.original_image
        self.setPixmap(QPixmap().fromImage(self.qimage))
        self.parent.fitToWindow()
        self.repaint()

    def resizeImage(self):
        """Resize image."""
        # TODO: Resize image by specified size
        if self.qimage.isNull() == False:
            resize = QTransform().scale(0.5, 0.5)
            pixmap = QPixmap(self.qimage)
            resized_image = pixmap.transformed(resize, mode=Qt.SmoothTransformation)
            self.qimage = QImage(resized_image)
            self.setPixmap(resized_image)
            # self.qimage = QPixmap(rotated)
            self.setScaledContents(True)
            self.repaint()  # repaint the child widget
        else:
            # No image to rotate
            pass

    def set_state(self, state):
        self.state = state
        if state == State.crop:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def crop_image(self, rect):
        """
        Crop selected portions in the image.
        rect: the rectangle wrt Qlabel dimensions
        """
        if not self.qimage.isNull():
            xmin = rect.x() / self.width() * self.qimage.width()
            ymin = rect.y() / self.height() * self.qimage.height()
            width = rect.width() / self.width() * self.qimage.width()
            height = rect.height() / self.height() * self.qimage.height()
            rect_img = QRect(xmin, ymin, width, height)
            original_image = self.qimage
            cropped = original_image.copy(rect_img)
            self.qimage = QImage(cropped)
            self.setPixmap(QPixmap().fromImage(cropped))
            self.parent.fitToWindow()

    def rotate_image_90(self, direction):
        """Rotate image 90º clockwise or counterclockwise."""
        if not self.qimage.isNull():
            if direction == "cw":
                transform = QTransform().rotate(90)
            elif direction == "ccw":
                transform = QTransform().rotate(-90)

            self.qimage = self.qimage.transformed(transform, mode=Qt.SmoothTransformation)
            self.setPixmap(QPixmap().fromImage(self.qimage))
            self.parent.fitToWindow()
        else:
            # No image to rotate
            pass

    def flip_image(self, axis):
        """
        Mirror the image across the horizontal axis.
        """
        if self.qimage.isNull() == False:
            if axis == "horizontal":
                transform = QTransform().scale(-1, 1)
            elif axis == "vertical":
                transform = QTransform().scale(1, -1)

            self.qimage = self.qimage.transformed(transform, mode=Qt.SmoothTransformation)
            self.setPixmap(QPixmap().fromImage(self.qimage))
            self.parent.fitToWindow()
        else:
            # No image to flip
            pass

    def convertToGray(self):
        """Convert image to grayscale."""
        if self.qimage.isNull() == False:
            converted_img = self.qimage.convertToFormat(QImage.Format_Grayscale16)
            # self.qimage = converted_img
            self.qimage = QImage(converted_img)
            self.setPixmap(QPixmap().fromImage(converted_img))
            self.repaint()

    def convertToRGB(self):
        """Convert image to RGB format."""
        if self.qimage.isNull() == False:
            converted_img = self.qimage.convertToFormat(QImage.Format_RGB32)
            # self.qimage = converted_img
            self.qimage = QImage(converted_img)
            self.setPixmap(QPixmap().fromImage(converted_img))
            self.repaint()

    def convertToSepia(self):
        """Convert image to sepia filter."""
        # TODO: Sepia #704214 rgb(112, 66, 20)
        # TODO: optimize speed that the image converts, or add to thread
        if self.qimage.isNull() == False:
            for row_pixel in range(self.qimage.width()):
                for col_pixel in range(self.qimage.height()):
                    current_val = QColor(self.qimage.pixel(row_pixel, col_pixel))

                    # Calculate r, g, b values for current pixel
                    red = current_val.red()
                    green = current_val.green()
                    blue = current_val.blue()

                    new_red = int(0.393 * red + 0.769 * green + 0.189 * blue)
                    new_green = int(0.349 * red + 0.686 * green + 0.168 * blue)
                    new_blue = int(0.272 * red + 0.534 * green + 0.131 * blue)

                    # Set the new RGB values for the current pixel
                    if new_red > 255:
                        red = 255
                    else:
                        red = new_red

                    if new_green > 255:
                        green = 255
                    else:
                        green = new_green

                    if new_blue > 255:
                        blue = 255
                    else:
                        blue = new_blue

                    new_value = qRgb(red, green, blue)
                    self.qimage.setPixel(row_pixel, col_pixel, new_value)

        self.setPixmap(QPixmap().fromImage(self.qimage))
        self.repaint()

    def changeBrighteness(self, value):
        # TODO: Reset the value of brightness, remember the original values
        # as going back to 0, i.e. keep track of original image's values
        # TODO: modify values based on original image
        if (value < -255 | value > 255):
            return self.qimage

        for row_pixel in range(self.qimage.width()):
            for col_pixel in range(self.qimage.height()):
                current_val = QColor(self.qimage.pixel(row_pixel, col_pixel))
                red = current_val.red()
                green = current_val.green()
                blue = current_val.blue()

                new_red = red + value
                new_green = green + value
                new_blue = blue + value

                # Set the new RGB values for the current pixel
                if new_red > 255:
                    red = 255
                elif new_red < 0:
                    red = 0
                else:
                    red = new_red

                if new_green > 255:
                    green = 255
                elif new_green < 0:
                    green = 0
                else:
                    green = new_green

                if new_blue > 255:
                    blue = 255
                elif new_blue < 0:
                    blue = 0
                else:
                    blue = new_blue

                new_value = qRgb(red, green, blue)
                self.qimage.setPixel(row_pixel, col_pixel, new_value)

        self.setPixmap(QPixmap().fromImage(self.qimage))

    def changeContrast(self, contrast):
        """Change the contrast of the pixels in the image.
           Contrast is the difference between max and min pixel intensity."""
        for row_pixel in range(self.qimage.width()):
            for col_pixel in range(self.qimage.height()):
                # Calculate a contrast correction factor
                factor = float(259 * (contrast + 255) / (255 * (259 - contrast)))

                current_val = QColor(self.qimage.pixel(row_pixel, col_pixel))
                red = current_val.red()
                green = current_val.green()
                blue = current_val.blue()

                new_red = factor * (red - 128) + 128
                new_green = factor * (green - 128) + 128
                new_blue = factor * (blue - 128) + 128

                new_value = qRgb(new_red, new_green, new_blue)
                self.qimage.setPixel(row_pixel, col_pixel, new_value)

        self.setPixmap(QPixmap().fromImage(self.qimage))

    def changeHue(self):
        for row_pixel in range(self.qimage.width()):
            for col_pixel in range(self.qimage.height()):
                current_val = QColor(self.qimage.pixel(row_pixel, col_pixel))
                hue = current_val.hue()
                current_val.setHsv(hue, current_val.saturation(),
                                   current_val.value(), current_val.alpha())
                self.qimage.setPixelColor(row_pixel, col_pixel, current_val)
        self.setPixmap(QPixmap().fromImage(self.qimage))

    def mousePressEvent(self, event):
        """Handle mouse press event."""
        self.origin = event.pos()
        if not self.rubber_band:
            self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.rubber_band.setGeometry(QRect(self.origin, QSize()))
        self.rubber_band.show()

    def mouseMoveEvent(self, event):
        """Handle mouse move event."""
        self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        """Handle when the mouse is released."""
        if self.state == State.crop:
            rect = self.rubber_band.geometry()
            self.crop_image(rect)
        self.rubber_band.hide()
