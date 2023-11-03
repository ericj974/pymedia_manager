import logging
from pathlib import Path

import piexif
from PIL import ImageQt
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QRect, QSize, QEvent
from PyQt5.QtGui import QImage, QPixmap, QTransform, QColor, qRgb, QPalette, QKeySequence
from PyQt5.QtWidgets import QLabel, QRubberBand, QSizePolicy, QShortcut, QLineEdit, QScrollArea, QPushButton, \
    QHBoxLayout, QVBoxLayout, QMenu, QAction, QListWidgetItem

import common.comment
import common.cv
import common.exif
from common.face import DetectionResult
from common.widgets import MyQListWidget, MediaWithMetadata
from mvc.views.clip_editor.action_params import ClipLumContrastParams


class State:
    normal = "normal"
    crop = "crop"


class ImageLabel(QLabel, MediaWithMetadata):
    """Subclass of QLabel for displaying image"""

    def __init__(self, parent=None):
        super(QLabel, self).__init__(parent)
        self.parent = parent
        self.file: Path = None

        # Current qimage
        self.qimage = QImage()
        # qimage resulting from past action.
        # Useful when applying a destructive operation that could change like luminosity / contrast
        self.qimage_ex = self.qimage
        # Save a copy of the original image
        self.qimage_orig = self.qimage

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
        self.cancel_sc.activated.connect(self.revert_original_img)

    def reset(self):
        self.qimage = QImage()
        self.setPixmap(QPixmap())
        self.qimage_orig = self.qimage.copy()
        self.qimage_ex = self.qimage.copy()

    def open_media(self, path: Path, **kwargs):
        if path.is_file():
            self.file = path
            self.qimage, self.exif_dict = common.cv.load_image(path)
            self.qimage_ex = self.qimage
            pixmap = QPixmap().fromImage(self.qimage)
            self.setPixmap(pixmap)
            # Keep a copy of the image
            self.qimage_orig = self.qimage.copy()

    def save_media(self, file: Path = None, **kwargs):
        file = file if file else self.file
        try:
            self.exif_dict['Exif'][41729] = str(self.exif_dict['Exif'][41729]).encode("ascii")
        except:
            pass
        if 'thumbnail' in self.exif_dict:
            del self.exif_dict['thumbnail']
        exif_bytes = piexif.dump(self.exif_dict)
        # Need to use ImageQt to save metadata
        ImageQt.fromqimage(self.qimage).save(str(file), exif=exif_bytes, optimize=True, quality=95)

    def load_comment(self):
        user_comment = common.comment.ImageUserComment.load_from_file(self.file)
        return user_comment

    def save_comment(self, user_comment, file: Path = None):
        file = file if file else self.file
        exif_dic = common.exif.get_exif(self.file)
        user_comment.update_exif(exif_dic)
        common.exif.save_exif(exif_dict=exif_dic, path=file)

    def set_state(self, state):
        self.state = state
        if state == State.crop:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def revert_original_img(self):
        """Revert the image back to original image."""
        self.qimage = self.qimage_orig
        self.setPixmap(QPixmap().fromImage(self.qimage))
        if self.parent:
            self.parent.fit_window()
        self.repaint()

    def img_resize(self):
        pass

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

    def img_crop(self, rect: QRect) -> None:
        """
        Crop selected portions in the image.
        rect: the rectangle wrt Qlabel dimensions
        """
        self.qimage_ex = self.qimage

        if not self.qimage.isNull():
            xmin = rect.x() / self.width() * self.qimage.width()
            ymin = rect.y() / self.height() * self.qimage.height()
            width = rect.width() / self.width() * self.qimage.width()
            height = rect.height() / self.height() * self.qimage.height()
            rect_img = QRect(int(xmin), int(ymin), int(width), int(height))
            original_image = self.qimage
            cropped = original_image.copy(rect_img)
            self.qimage = QImage(cropped)
            self.setPixmap(QPixmap().fromImage(cropped))
            if self.parent:
                self.parent.fit_window()

    def img_rotate_90(self, direction: str) -> None:
        """Rotate image 90º clockwise or counterclockwise."""
        self.qimage_ex = self.qimage

        if not self.qimage.isNull():
            if direction == "cw":
                transform = QTransform().rotate(90)
            elif direction == "ccw":
                transform = QTransform().rotate(-90)

            self.qimage = self.qimage.transformed(transform, mode=Qt.SmoothTransformation)
            self.setPixmap(QPixmap().fromImage(self.qimage))
            if self.parent:
                self.parent.fit_window()
        else:
            # No image to rotate
            pass

    def img_flip(self, axis: str):
        """
        Mirror the image across the horizontal axis.
        """
        self.qimage_ex = self.qimage

        if not self.qimage.isNull():
            if axis == "horizontal":
                transform = QTransform().scale(-1, 1)
            elif axis == "vertical":
                transform = QTransform().scale(1, -1)

            self.qimage = self.qimage.transformed(transform, mode=Qt.SmoothTransformation)
            self.setPixmap(QPixmap().fromImage(self.qimage))
            if self.parent:
                self.parent.fit_window()
        else:
            # No image to flip
            pass

    def img_to_gray(self):
        """Convert image to grayscale."""
        self.qimage_ex = self.qimage

        if not self.qimage.isNull():
            converted_img = self.qimage.convertToFormat(QImage.Format_Grayscale16)
            # self.qimage = converted_img
            self.qimage = QImage(converted_img)
            self.setPixmap(QPixmap().fromImage(converted_img))
            self.repaint()

    def img_to_rgb(self):
        """Convert image to RGB format."""
        self.qimage_ex = self.qimage

        if not self.qimage.isNull():
            converted_img = self.qimage.convertToFormat(QImage.Format_RGB32)
            # self.qimage = converted_img
            self.qimage = QImage(converted_img)
            self.setPixmap(QPixmap().fromImage(converted_img))
            self.repaint()

    def img_to_sepia(self):
        """Convert image to sepia filter."""
        self.qimage_ex = self.qimage

        # TODO: Sepia #704214 rgb(112, 66, 20)
        # TODO: optimize speed that the image converts, or add to thread
        if not self.qimage.isNull():
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

    def img_set_lum_contrast(self, lum: float, contrast: float):
        if (lum < -255.) | (lum > 255.) | (contrast < -255.) | (contrast > 255.):
            return
        params = ClipLumContrastParams(lum=lum, contrast=contrast)
        new_frame = params.process_im(common.cv.toCvMat(self.qimage_ex))
        self.qimage = common.cv.toQImage(new_frame)
        self.setPixmap(QPixmap().fromImage(self.qimage))

    def img_set_hue(self):
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
            self.img_crop(rect)
        self.rubber_band.hide()


class FaceDetectionWidget(QtWidgets.QWidget):
    def __init__(self, db, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        self.file: Path = None
        self.db = db

        # Detection model selection
        self.detection_model_combobox = QtWidgets.QComboBox()
        self.detection_model_combobox.addItems(common.face.detection_backend)
        self.face_model_combobox = QtWidgets.QComboBox()
        self.face_model_combobox.addItems(common.face.face_recognition_model)

        # Search bar.
        self.searchbar = QLineEdit()
        self.searchbar.textChanged.connect(self.update_display_when_searching)

        # Listing of existing face tags
        self.list_db_tags_widget = MyQListWidget()
        self.list_db_tags_widget.doubleClicked.connect(self.on_db_table_clicked)
        self.list_db_tags_widget.__class__.dropEvent = self.on_db_drop

        self.scroll_db = QScrollArea()
        self.scroll_db.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_db.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_db.setWidgetResizable(True)
        self.scroll_db.setWidget(self.list_db_tags_widget)

        # Listing of detection results
        self.result_widget = MyQListWidget()
        self.list_db_tags_widget.src_widget = self.result_widget
        self.result_widget.installEventFilter(self)

        self.scroll_detection = QScrollArea()
        self.scroll_detection.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_detection.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_detection.setWidgetResizable(True)
        self.scroll_detection.setWidget(self.result_widget)

        # Buttons
        self.btn_save_to_db = QPushButton('Save to DB', self)
        self.btn_save_to_db.clicked.connect(self.save_selected_det_to_db)
        # Create layouts to place inside widget
        layout_buttons = QHBoxLayout()
        layout_buttons.setContentsMargins(0, 0, 0, 0)
        layout_buttons.addWidget(self.btn_save_to_db)

        # Set layout for dock widget
        vlay = QVBoxLayout()
        self.setLayout(vlay)
        vlay.addWidget(QLabel("Detection Backend"))
        vlay.addWidget(self.detection_model_combobox)
        vlay.addWidget(QLabel("Face Recognition Model"))
        vlay.addWidget(self.face_model_combobox)
        vlay.addWidget(self.searchbar)
        vlay.addWidget(QtWidgets.QLabel("Existing Tags"))
        vlay.addWidget(self.scroll_db, 2)
        vlay.addWidget(QLabel("Detection Results"))
        vlay.addWidget(self.scroll_detection)
        vlay.addLayout(layout_buttons)

        # Display update
        self.update_db_display()
        self.set_detection_results([])

    def set_file(self, file: Path):
        self.file = file

    def update_display_when_searching(self, text):
        for i in range(self.list_db_tags_widget.count()):
            # item(row)->setHidden(!item(row)->text().contains(filter, Qt::CaseInsensitive));
            self.list_db_tags_widget.item(i).setHidden(text.lower() not in
                                                       self.list_db_tags_widget.item(i).text().lower())

    def update_db_display(self):
        self.list_db_tags_widget.clear()
        self.list_db_tags_widget.addItems(self.db.known_face_names)

    def set_detection_results(self, results: list[DetectionResult]):
        self.result_widget.clear()

        for result in results:
            if result.file == self.file:
                self.result_widget.addItem(MyDetectionQListWidgetItem(result))

    def clear(self):
        self.set_detection_results([])

    def save_selected_det_to_db(self):

        for item, index in zip(self.result_widget.selectedItems(),
                               self.result_widget.selectionModel().selectedIndexes()):
            if item.result.name == common.face.unknown_tag:
                continue

            # Create encoding for all recognition models
            for model in common.face.face_recognition_model:
                item_db = self.db.get_entry(name=item.result.name, filename=item.result.file.name,
                                            model=model)
                if item_db is not None:
                    continue
                logging.info(f"Creating embedding for model {model}")

                # Representation
                embedding = common.face.face_encodings(imgs=[item.result.patch], recognition_model=model)[0]

                # Add to db
                self.db.add_to_db(name=item.result.name, patch=item.result.patch, embedding=embedding,
                                  location=item.result.location, file=item.result.file, model=model, overwrite=True)

        self.update_db_display()

    def eventFilter(self, source, event):
        def rename():
            text, okPressed = QtWidgets.QInputDialog.getText(self, "New tag", "New tag:")
            if okPressed and text != '':
                if len(self.result_widget.selectedItems()) > 0:
                    self.result_widget.currentItem().setText(text)

        if event.type() == QEvent.ContextMenu and source is self.result_widget:
            if len(self.result_widget.selectedItems()) > 0:
                menu = QMenu()
                action = QAction('Rename', self)
                action.triggered.connect(rename)
                menu.addAction(action)
                menu.exec_(event.globalPos())
                return True
        return super().eventFilter(source, event)

    def on_db_table_clicked(self, index):
        if len(self.result_widget.selectedItems()) > 0:
            self.result_widget.currentItem().setText(self.list_db_tags_widget.item(index.row()).text())

    def on_db_drop(self, e):
        if (e.source() == self.result_widget):
            self.save_selected_det_to_db()


class MyDetectionQListWidgetItem(QListWidgetItem):
    def __init__(self, result: DetectionResult):
        super(QListWidgetItem, self).__init__(result.name)
        self.result: DetectionResult = result

    def setText(self, text: str):
        self.result.name = text
        super().setText(text)
