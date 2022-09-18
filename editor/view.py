import os

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QSize, pyqtSlot
from PyQt5.QtGui import QIcon, QPalette, QWheelEvent
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QAction,
                             QSlider, QToolButton, QToolBar, QDockWidget, QMessageBox, QGridLayout,
                             QScrollArea, QStatusBar, QFileDialog, QShortcut)

from controller import MainController
from editor.widgets import ImageLabel, State
from model import MainModel

icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")


class PhotoEditorWindow(QMainWindow):

    def __init__(self, model: MainModel, controller: MainController):
        super().__init__()

        self._model = model
        self._controller = controller

        self.cumul_scale_factor = 1

        self.createMainLabel()
        self.createEditingBar()
        self.createActionsShortcuts()
        self.createMenus()
        self.createToolBar()
        self.show()

        self.setAttribute(Qt.WA_DeleteOnClose, True)
        # listen for model event
        # Model Event - selected image has changed
        self._model.selected_image_changed.connect(self.on_imagepath_changed)
        #

        self.setMinimumSize(300, 200)
        self.setWindowTitle("Photo Editor")
        self.showMaximized()
        self.setStatusBar(QStatusBar())

        # Open selected image
        if self._model.imagepath:
            self.openImage(file=self._model.imagepath)

    @pyqtSlot(str)
    def on_imagepath_changed(self, imagepath):
        self.openImage(file=imagepath)
        self.show()

    def createActionsShortcuts(self):
        # Actions for Photo Editor menu
        self.about_act = QAction('About', self)
        self.about_act.triggered.connect(self.aboutDialog)

        self.exit_act = QAction(QIcon(os.path.join(icon_path, "exit.png")), 'Quit Photo Editor', self)
        self.exit_act.setShortcut('Ctrl+Q')
        self.exit_act.triggered.connect(self.close)

        # Actions for File menu
        self.new_act = QAction(QIcon(os.path.join(icon_path, "new.png")), 'New...')

        self.open_act = QAction(QIcon(os.path.join(icon_path, "open.png")), 'Open...', self)
        self.open_act.setShortcut('Ctrl+O')
        self.open_act.triggered.connect(self.openImage)

        self.print_act = QAction(QIcon(os.path.join(icon_path, "print.png")), "Print...", self)
        self.print_act.setShortcut('Ctrl+P')
        # self.print_act.triggered.connect(self.printImage)
        self.print_act.setEnabled(False)

        self.save_act = QAction(QIcon(os.path.join(icon_path, "save.png")), "Save...", self)
        self.save_act.setShortcut('Ctrl+S')
        self.save_act.triggered.connect(self.save_image)
        self.save_act.setEnabled(False)

        self.save_as_act = QAction("Save As...", self)
        self.save_as_act.setShortcut('Ctrl+Shift+S')
        self.save_as_act.triggered.connect(self.save_image_as)
        self.save_as_act.setEnabled(False)

        # Actions for Edit menu
        self.revert_act = QAction("Revert to Original", self)
        self.revert_act.triggered.connect(self.image_label.revertToOriginal)
        self.revert_act.setEnabled(False)

        # Actions for Tools menu
        self.crop_act = QAction(QIcon(os.path.join(icon_path, "crop.png")), "Crop", self)
        self.crop_act.setShortcut('C')
        self.crop_act.triggered.connect(lambda: self.image_label.set_state(State.crop))

        self.resize_act = QAction(QIcon(os.path.join(icon_path, "resize.png")), "Resize", self)
        self.resize_act.setShortcut('Shift+Z')
        self.resize_act.triggered.connect(self.image_label.resizeImage)

        self.rotate90_cw_act = QAction(QIcon(os.path.join(icon_path, "rotate90_cw.png")), 'Rotate 90º CW', self)
        self.rotate90_cw_act.setShortcut('R')
        self.rotate90_cw_act.triggered.connect(lambda: self.image_label.rotate_image_90("cw"))

        self.rotate90_ccw_act = QAction(QIcon(os.path.join(icon_path, "rotate90_ccw.png")), 'Rotate 90º CCW', self)
        self.rotate90_ccw_act.setShortcut('Shift+R')
        self.rotate90_ccw_act.triggered.connect(lambda: self.image_label.rotate_image_90("ccw"))

        self.flip_horizontal = QAction(QIcon(os.path.join(icon_path, "flip_horizontal.png")), 'Flip Horizontal', self)
        self.flip_horizontal.triggered.connect(lambda: self.image_label.flip_image("horizontal"))

        self.flip_vertical = QAction(QIcon(os.path.join(icon_path, "flip_vertical.png")), 'Flip Vertical', self)
        self.flip_vertical.triggered.connect(lambda: self.image_label.flip_image('vertical'))

        self.zoom_in_act = QAction(QIcon(os.path.join(icon_path, "zoom_in.png")), 'Zoom In', self)
        self.zoom_in_act.setShortcut('Ctrl++')
        self.zoom_in_act.triggered.connect(lambda: self.scale_image(1.25))
        self.zoom_in_act.setEnabled(False)

        self.zoom_out_act = QAction(QIcon(os.path.join(icon_path, "zoom_out.png")), 'Zoom Out', self)
        self.zoom_out_act.setShortcut('Ctrl+-')
        self.zoom_out_act.triggered.connect(lambda: self.scale_image(0.8))
        self.zoom_out_act.setEnabled(False)

        self.normal_size_act = QAction("Normal Size", self)
        self.normal_size_act.setShortcut('Ctrl+=')
        self.normal_size_act.triggered.connect(self.normalSize)
        self.normal_size_act.setEnabled(False)

        self.fit_to_window_act = QAction("&Fit to Window", self)
        self.fit_to_window_act.setShortcut('Ctrl+F')
        self.fit_to_window_act.triggered.connect(self.fitToWindow)
        self.fit_to_window_act.setEnabled(False)
        self.fit_to_window_act.setCheckable(True)
        self.fit_to_window_act.setChecked(True)

        self.detect_faces_act = QAction("Detect Faces", self)
        self.detect_faces_act.triggered.connect(self._detect_faces)

        # And the shortcuts
        QShortcut(QtCore.Qt.Key.Key_Right, self, self._controller.select_next_image)
        QShortcut(QtCore.Qt.Key.Key_Left, self, self._controller.select_prev_image)
        QShortcut(QtCore.Qt.Key.Key_Delete, self, self._controller.delete_cur_image)

    def createMenus(self):
        """Set up the menubar."""
        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)

        # Create Photo Editor menu and add actions
        main_menu = menu_bar.addMenu('Photo Editor')
        main_menu.addAction(self.about_act)
        main_menu.addSeparator()
        main_menu.addAction(self.exit_act)

        # Create file menu and add actions
        file_menu = menu_bar.addMenu('File')
        file_menu.addAction(self.open_act)
        file_menu.addAction(self.save_act)
        file_menu.addAction(self.save_as_act)
        file_menu.addSeparator()
        file_menu.addAction(self.print_act)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_act)

        edit_menu = menu_bar.addMenu('Edit')
        edit_menu.addAction(self.revert_act)

        tool_menu = menu_bar.addMenu('Tools')
        tool_menu.addAction(self.crop_act)
        tool_menu.addAction(self.resize_act)
        tool_menu.addSeparator()
        tool_menu.addAction(self.rotate90_cw_act)
        tool_menu.addAction(self.rotate90_ccw_act)
        tool_menu.addAction(self.flip_horizontal)
        tool_menu.addAction(self.flip_vertical)
        tool_menu.addSeparator()
        tool_menu.addAction(self.zoom_in_act)
        tool_menu.addAction(self.zoom_out_act)
        tool_menu.addAction(self.normal_size_act)
        tool_menu.addSeparator()
        tool_menu.addAction(self.fit_to_window_act)
        tool_menu.addSeparator()
        tool_menu.addAction(self.detect_faces_act)

        views_menu = menu_bar.addMenu('Views')
        views_menu.addAction(self.tools_menu_act)

    def createToolBar(self):
        """Set up the toolbar."""
        tool_bar = QToolBar("Main Toolbar")
        tool_bar.setIconSize(QSize(26, 26))
        self.addToolBar(tool_bar)

        # Add actions to the toolbar
        tool_bar.addAction(self.open_act)
        tool_bar.addAction(self.save_act)
        tool_bar.addAction(self.print_act)
        tool_bar.addAction(self.exit_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.crop_act)
        tool_bar.addAction(self.resize_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.rotate90_ccw_act)
        tool_bar.addAction(self.rotate90_cw_act)
        tool_bar.addAction(self.flip_horizontal)
        tool_bar.addAction(self.flip_vertical)
        tool_bar.addSeparator()
        tool_bar.addAction(self.zoom_in_act)
        tool_bar.addAction(self.zoom_out_act)

    def createEditingBar(self):
        """Create dock widget for editing tools."""
        # TODO: Add a tab widget for the different editing tools
        self.editing_bar = QDockWidget("Tools")
        self.editing_bar.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.editing_bar.setMinimumWidth(90)

        # Create editing tool buttons
        filters_label = QLabel("Filters")

        convert_to_grayscale = QToolButton()
        convert_to_grayscale.setIcon(QIcon(os.path.join(icon_path, "grayscale.png")))
        convert_to_grayscale.clicked.connect(self.image_label.convertToGray)

        convert_to_RGB = QToolButton()
        convert_to_RGB.setIcon(QIcon(os.path.join(icon_path, "rgb.png")))
        convert_to_RGB.clicked.connect(self.image_label.convertToRGB)

        convert_to_sepia = QToolButton()
        convert_to_sepia.setIcon(QIcon(os.path.join(icon_path, "sepia.png")))
        convert_to_sepia.clicked.connect(self.image_label.convertToSepia)

        change_hue = QToolButton()
        change_hue.setIcon(QIcon(os.path.join(icon_path, "")))
        change_hue.clicked.connect(self.image_label.changeHue)

        brightness_label = QLabel("Brightness")
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-255, 255)
        self.brightness_slider.setTickInterval(35)
        self.brightness_slider.setTickPosition(QSlider.TicksAbove)
        self.brightness_slider.valueChanged.connect(self.image_label.changeBrighteness)

        contrast_label = QLabel("Contrast")
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(-255, 255)
        self.contrast_slider.setTickInterval(35)
        self.contrast_slider.setTickPosition(QSlider.TicksAbove)
        self.contrast_slider.valueChanged.connect(self.image_label.changeContrast)

        # Set layout for dock widget
        editing_grid = QGridLayout()
        # editing_grid.addWidget(filters_label, 0, 0, 0, 2, Qt.AlignTop)
        editing_grid.addWidget(convert_to_grayscale, 1, 0)
        editing_grid.addWidget(convert_to_RGB, 1, 1)
        editing_grid.addWidget(convert_to_sepia, 2, 0)
        editing_grid.addWidget(change_hue, 2, 1)
        editing_grid.addWidget(brightness_label, 3, 0)
        editing_grid.addWidget(self.brightness_slider, 4, 0, 1, 0)
        editing_grid.addWidget(contrast_label, 5, 0)
        editing_grid.addWidget(self.contrast_slider, 6, 0, 1, 0)
        editing_grid.setRowStretch(7, 10)

        container = QWidget()
        container.setLayout(editing_grid)

        self.editing_bar.setWidget(container)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.editing_bar)

        self.tools_menu_act = self.editing_bar.toggleViewAction()

    def createMainLabel(self):
        """Create an instance of the imageLabel class and set it 
           as the main window's central widget."""
        self.image_label = ImageLabel(self)

        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.Dark)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.image_label)
        self.setCentralWidget(self.scroll_area)
        self.resize(QApplication.primaryScreen().availableSize() * 3 / 5)

    def updateActions(self):
        """Update the values of menu and toolbar items when an image 
        is loaded."""
        self.save_act.setEnabled(True)
        self.revert_act.setEnabled(True)
        self.zoom_in_act.setEnabled(True)
        self.zoom_out_act.setEnabled(True)
        self.normal_size_act.setEnabled(True)

    def _detect_faces(self):
        pass

    def openImage(self, file=""):
        """Load a new image into the """
        if file == "":
            file, _ = QFileDialog.getOpenFileName(self, "Open Image",
                                                  "", "PNG Files (*.png);;JPG Files (*.jpeg *.jpg );;Bitmap Files (*.bmp);;\
                    GIF Files (*.gif)")

        if file:
            self.image_label.load_image(file)
            self.cumul_scale_factor = 1
            self.scroll_area.setVisible(True)
            self.print_act.setEnabled(True)
            self.fit_to_window_act.setEnabled(True)
            self.updateActions()

            if not self.fit_to_window_act.isChecked():
                self.image_label.adjustSize()
            else:
                self.fitToWindow()

            # Reset all sliders
            self.brightness_slider.setValue(0)

        elif file == "":
            # User selected Cancel
            pass
        else:
            QMessageBox.information(self, "Error",
                                    "Unable to open image.", QMessageBox.Ok)

    def save_image_as(self):
        """Save the image displayed in the label."""
        if not self.image_label.qimage.isNull():
            image_file, _ = QFileDialog.getSaveFileName(self, "Save Image",
                                                        "", "PNG Files (*.png);;JPG Files (*.jpeg *.jpg );;Bitmap Files (*.bmp);;\
                    GIF Files (*.gif)")

            if image_file and self.image_label.qimage.isNull() == False:
                self.image_label.qimage.save(image_file)
            else:
                QMessageBox.information(self, "Error",
                                        "Unable to save image.", QMessageBox.Ok)
        else:
            QMessageBox.information(self, "Empty Image",
                                    "There is no image to save.", QMessageBox.Ok)

    def save_image(self):
        """Save the image displayed in the label."""
        if not self.image_label.qimage.isNull():
            self.image_label.save(self._model.imagepath)
        else:
            QMessageBox.information(self, "Empty Image",
                                    "There is no image to save.", QMessageBox.Ok)

    def scale_image(self, scale_factor):
        """Zoom in and zoom out."""
        self.cumul_scale_factor *= scale_factor
        self.image_label.resize(scale_factor * self.image_label.size())

        self.adjustScrollBar(self.scroll_area.horizontalScrollBar(), scale_factor)
        self.adjustScrollBar(self.scroll_area.verticalScrollBar(), scale_factor)

        self.zoom_in_act.setEnabled(self.cumul_scale_factor < 4.0)
        self.zoom_out_act.setEnabled(self.cumul_scale_factor > 0.333)

    def normalSize(self):
        """View image with its normal dimensions."""
        self.image_label.adjustSize()
        self.cumul_scale_factor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fit_to_window_act.isChecked()
        # self.scroll_area.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()
        else:
            if not self.image_label.pixmap().isNull():
                w, h = self.scroll_area.width(), self.scroll_area.height()
                wi, hi = self.image_label.pixmap().width(), self.image_label.pixmap().height()
                self.cumul_scale_factor = factor = min(h / hi, w / wi)
                self.image_label.resize(factor * self.image_label.pixmap().size())

        self.updateActions()

    def adjustScrollBar(self, scroll_bar, factor):
        """Adjust the scrollbar when zooming in or out."""
        scroll_bar.setValue(int(factor * scroll_bar.value() + ((factor - 1) * scroll_bar.pageStep() / 2)))

    def aboutDialog(self):
        QMessageBox.about(self, "About Photo Editor",
                          "Photo Editor\nVersion 0.2\n\nCreated by Joshua Willman")

    def wheelEvent(self, event: QWheelEvent) -> None:
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            numDegrees = event.angleDelta() / 8
            if not numDegrees.isNull():
                numSteps = int(numDegrees.y() / 15)
                if numSteps > 0:
                    for i in range(numSteps):
                        self.scale_image(1.25)
                else:
                    for i in range(-numSteps):
                        self.scale_image(0.8)
        QMainWindow.wheelEvent(self, event)

    def resizeEvent(self, event):
        self.fitToWindow()
        QMainWindow.resizeEvent(self, event)

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            self.close()
        if event.key() == Qt.Key_F1:  # fn + F1 on Mac
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()

    def closeEvent(self, event):
        pass