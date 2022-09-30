import os

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QSize, pyqtSlot
from PyQt5.QtGui import QIcon, QPalette, QWheelEvent
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QAction,
                             QSlider, QToolBar, QDockWidget, QMessageBox, QGridLayout,
                             QScrollArea, QStatusBar, QFileDialog, QShortcut, QStyle)

from clip_editor.action_params import FlipOrientation, RotationOrientation
from clip_editor.widgets import ClipEditorWidget
from controller import MainController
from img_editor import widgets
from model import MainModel
from renamer.parsers import FILE_EXTENSION_PHOTO_JPG, FILE_EXTENSION_VIDEO

icon_path = os.path.join(os.path.dirname(os.path.abspath(widgets.__file__)), "icons")


class ClipEditorWindow(QMainWindow):

    def __init__(self, model: MainModel, controller: MainController):
        super().__init__()

        self._model = model
        self._controller = controller

        self.cumul_scale_factor = 1

        self.createMainLabel()
        self.createEditingBar()
        self.createActionsShortcuts()
        self.createMenus()
        self.createTopToolBar()

        self.setAttribute(Qt.WA_DeleteOnClose, True)
        # listen for model event
        # Model Event - selected image has changed
        self._model.selected_media_changed.connect(self.on_media_path_changed)

        self.setMinimumSize(300, 200)
        self.setWindowTitle("Clip Editor")
        self.showMaximized()
        self.setStatusBar(QStatusBar())
        self.setVisible(False)

        # Open selected image
        if self._model.media_path:
            ext = os.path.splitext(self._model.media_path)[1][1:]
            if ext in FILE_EXTENSION_PHOTO_JPG:
                self.open_media(file=self._model.media_path)
            else:
                self.media_widget.reset()
                self.setEnabled(False)


    @pyqtSlot(str)
    def on_media_path_changed(self, path):
        ok = self.open_media(file=path)
        if ok or self.isVisible():
            self.show()

    def createActionsShortcuts(self):
        # Actions for Editor menu
        self.about_act = QAction('About', self)
        self.about_act.triggered.connect(self.aboutDialog)

        self.exit_act = QAction(QIcon(os.path.join(icon_path, "exit.png")), 'Quit Photo Editor', self)
        self.exit_act.setShortcut('Ctrl+Q')
        self.exit_act.triggered.connect(self.close)

        self.save_act = QAction(QIcon(os.path.join(icon_path, "save.png")), "Save...", self)
        self.save_act.setShortcut('Ctrl+S')
        self.save_act.triggered.connect(self.save_media)
        self.save_act.setEnabled(False)

        # Actions for Edit menu
        self.revert_act = QAction("Revert to Original", self)
        self.revert_act.triggered.connect(self.revertToOriginal)
        self.revert_act.setEnabled(False)

        # Actions for Tools menu
        self.crop_act = QAction(QIcon(os.path.join(icon_path, "vid_cut.png")), "Crop", self)
        self.crop_act.setShortcut('C')
        self.crop_act.triggered.connect(lambda: self.media_widget.crop_media())

        self.resize_act = QAction(QIcon(os.path.join(icon_path, "resize.png")), "Resize", self)
        self.resize_act.setShortcut('Shift+Z')
        self.resize_act.triggered.connect(self.media_widget.zoom_media)

        self.rotate90_cw_act = QAction(QIcon(os.path.join(icon_path, "rotate90_cw.png")), 'Rotate 90º CW', self)
        self.rotate90_cw_act.setShortcut('R')
        self.rotate90_cw_act.triggered.connect(lambda: self.media_widget.rotate_image_90(RotationOrientation.cw))

        self.rotate90_ccw_act = QAction(QIcon(os.path.join(icon_path, "rotate90_ccw.png")), 'Rotate 90º CCW', self)
        self.rotate90_ccw_act.setShortcut('Shift+R')
        self.rotate90_ccw_act.triggered.connect(lambda: self.media_widget.rotate_image_90(RotationOrientation.ccw))

        self.flip_horizontal_act = QAction(QIcon(os.path.join(icon_path, "flip_horizontal.png")), 'Flip Horizontal', self)
        self.flip_horizontal_act.triggered.connect(lambda: self.media_widget.flip_image(FlipOrientation.horizontal))

        self.flip_vertical_act = QAction(QIcon(os.path.join(icon_path, "flip_vertical.png")), 'Flip Vertical', self)
        self.flip_vertical_act.triggered.connect(lambda: self.media_widget.flip_image(FlipOrientation.vertical))

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
        self.normal_size_act.triggered.connect(self._normal_size)
        self.normal_size_act.setEnabled(False)

        self.fit_to_window_act = QAction("&Fit to Window", self)
        self.fit_to_window_act.setShortcut('Ctrl+F')
        self.fit_to_window_act.triggered.connect(self.fitToWindow)
        self.fit_to_window_act.setEnabled(False)
        self.fit_to_window_act.setCheckable(True)
        self.fit_to_window_act.setChecked(True)

        # And the shortcuts
        QShortcut(QtCore.Qt.Key.Key_Right, self, self._controller.select_next_media)
        QShortcut(QtCore.Qt.Key.Key_Left, self, self._controller.select_prev_media)
        QShortcut(QtCore.Qt.Key.Key_Delete, self, self._controller.delete_cur_media)

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
        file_menu.addAction(self.save_act)
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
        tool_menu.addAction(self.flip_horizontal_act)
        tool_menu.addAction(self.flip_vertical_act)
        tool_menu.addSeparator()
        tool_menu.addAction(self.zoom_in_act)
        tool_menu.addAction(self.zoom_out_act)
        tool_menu.addAction(self.normal_size_act)
        tool_menu.addSeparator()
        tool_menu.addAction(self.fit_to_window_act)

        views_menu = menu_bar.addMenu('Views')
        views_menu.addAction(self.tools_menu_act)

    def createTopToolBar(self):
        """Set up the toolbar."""
        tool_bar = QToolBar("Main Toolbar")
        tool_bar.setIconSize(QSize(26, 26))
        self.addToolBar(tool_bar)

        # Add actions to the toolbar
        tool_bar.addAction(self.save_act)
        tool_bar.addAction(self.exit_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.crop_act)
        tool_bar.addAction(self.resize_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.rotate90_ccw_act)
        tool_bar.addAction(self.rotate90_cw_act)
        tool_bar.addAction(self.flip_horizontal_act)
        tool_bar.addAction(self.flip_vertical_act)
        # tool_bar.addSeparator()
        # tool_bar.addAction(self.zoom_in_act)
        # tool_bar.addAction(self.zoom_out_act)


    def createEditingBar(self):
        """Create dock widget for editing tools."""
        # TODO: Add a tab widget for the different editing tools
        self.editing_bar = QDockWidget("Tools")
        self.editing_bar.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.editing_bar.setMinimumWidth(90)


        brightness_label = QLabel("Brightness")
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-255, 255)
        self.brightness_slider.setTickInterval(35)
        self.brightness_slider.setTickPosition(QSlider.TicksAbove)
        self.brightness_slider.valueChanged.connect(self.media_widget.change_brightness)

        contrast_label = QLabel("Contrast")
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(-255, 255)
        self.contrast_slider.setTickInterval(35)
        self.contrast_slider.setTickPosition(QSlider.TicksAbove)
        self.contrast_slider.valueChanged.connect(self.media_widget.change_contrast)

        # Set layout for dock widget
        editing_grid = QGridLayout()
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

        self.media_widget = ClipEditorWidget(self)

        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.Dark)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.media_widget)
        self.setCentralWidget(self.scroll_area)
        self.resize(QApplication.primaryScreen().availableSize() * 3 / 5)

        # self.media_widget.stateChanged.connect(self.mediaStateChanged)
        # self.media_widget.positionChanged.connect(self.positionChanged)
        # self.media_widget.durationChanged.connect(self.durationChanged)
        # self.media_widget.error.connect(self.handleError)

    def updateActions(self):
        """Update the values of menu and toolbar items when an image 
        is loaded."""
        self.save_act.setEnabled(True)
        self.revert_act.setEnabled(True)
        self.zoom_in_act.setEnabled(True)
        self.zoom_out_act.setEnabled(True)
        self.normal_size_act.setEnabled(True)


    def mediaStateChanged(self, state):
        if self.media_widget.state() == QMediaPlayer.PlayingState:
            self.btn_play.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.btn_play.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.slider_frame.setValue(position)

    def durationChanged(self, duration):
        self.slider_frame.setRange(0, duration)

    def setPosition(self, position):
        self.media_widget.setPosition(position)

    def handleError(self):
        self.btn_play.setEnabled(False)
        self.errorLabel.setText("Error: " + self.media_widget.errorString())



    def revertToOriginal(self):
        pass


    def open_media(self, file=""):
        """Load a new image into the """
        if file == "":
            file, _ = QFileDialog.getOpenFileName(self, "Open Media",
                                                  "", "MP4 Files (*.mp4);;AVI Files (*.avi)")

        # Deactivate the img_editor if not an image
        ext = os.path.splitext(file)[1][1:]
        if ext not in FILE_EXTENSION_VIDEO:
            self.media_widget.reset()
            self.setEnabled(False)
            return False
        self.setEnabled(True)

        if file:
            self.media_widget.open_media(file)
            self.cumul_scale_factor = 1
            self.scroll_area.setVisible(True)
            self.fit_to_window_act.setEnabled(True)
            self.updateActions()

            if not self.fit_to_window_act.isChecked():
                self.media_widget.adjustSize()
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
        return True

    def save_media(self):
        """Save the image displayed in the label."""
        if self.media_widget.clip_reader.clip:
            file, _ = QFileDialog.getSaveFileName(parent=self, caption="Save Media",
                                                  directory=self._model.dirpath,
                                                  filter="MP4 Files (*.mp4);;AVI Files (*.avi)")
            filename, file_extension = os.path.splitext(os.path.basename(file))
            if file_extension == '':
                QMessageBox.warning(self, "Missing Extension",
                                    "Cannot save the media.", QMessageBox.Ok)
                return
            if file:
                self.media_widget.save_media(file)
        else:
            QMessageBox.information(self, "Empty Media",
                                    "There is no media to save.", QMessageBox.Ok)

    def scale_image(self, scale_factor):
        """Zoom in and zoom out."""
        self.cumul_scale_factor *= scale_factor
        self.media_widget.resize(scale_factor * self.media_widget.size())

        self.adjustScrollBar(self.scroll_area.horizontalScrollBar(), scale_factor)
        self.adjustScrollBar(self.scroll_area.verticalScrollBar(), scale_factor)

        self.zoom_in_act.setEnabled(self.cumul_scale_factor < 4.0)
        self.zoom_out_act.setEnabled(self.cumul_scale_factor > 0.333)

    def _normal_size(self):
        """View image with its normal dimensions."""
        self.media_widget.adjustSize()
        self.cumul_scale_factor = 1.0


    def fitToWindow(self):
        fitToWindow = self.fit_to_window_act.isChecked()
        # self.scroll_area.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self._normal_size()
        else:
            if self.media_widget.clip_reader.clip:
                w, h = self.scroll_area.width(), self.scroll_area.height()
                wi, hi = self.media_widget.clip_reader.clip.w, self.media_widget.clip_reader.clip.h
                self.cumul_scale_factor = factor = min(h / hi, w / wi)
                self.media_widget.resize(QSize(int(factor*wi), int(factor*hi)))

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
        # self.fitToWindow()
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
        self.media_widget.clip_reader.stop()
