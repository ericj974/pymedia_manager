from pathlib import Path

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QAction, QMainWindow, QMessageBox, QFileDialog

from common import exif
from common.constants import FILE_EXTENSION_PHOTO_JPG
from mvc.controllers.main import MainController
from mvc.models.main import MainModel
from mvc.views.gps import opacity_selected, opacity_unselected
from mvc.views.gps.widgets import MyDraw, MyQTableWidgetItem
from mvc.views.img_editor import widgets
from pyqtlet2 import L, MapWidget
from pyqtlet2.leaflet.core import Evented

icon_path = Path(widgets.__file__).parent / "icons"


class MainGPSWindow(QMainWindow):

    # This is a workaround for some issues with
    # "Registered new object after initialization, existing clients won't be notified!"
    def closeEvent(self, qcloseevent):
        Evented.mapWidget = None
        qcloseevent.accept()

    def __init__(self, model: MainModel, controller: MainController):
        super(self.__class__, self).__init__()
        self.setWindowTitle("GPS View")

        # MVC model
        self._model = model
        self._controller = controller
        self._controller.set_parent(self)

        # listen for model event signals
        self._model.selected_dir_changed.connect(self.on_dirpath_changed)
        self._model.selected_media_changed.connect(self.on_media_changed)
        self._model.selected_dir_content_changed.connect(self.on_dir_content_changed)

        # Main attributes
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setMinimumSize(800, 600)

        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # table widget
        _translate = QtCore.QCoreApplication.translate
        self.gps_table = QtWidgets.QTableWidget(self.central_widget)
        self.gps_table.doubleClicked.connect(self.on_table_double_clicked)
        self.gps_table.itemChanged.connect(self.on_gps_table_item_changed)
        self.gps_table.setColumnCount(3)
        self.gps_table.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem(_translate("MainWindow", "Filename")))
        self.gps_table.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem(_translate("MainWindow", "Lng")))
        self.gps_table.setHorizontalHeaderItem(2, QtWidgets.QTableWidgetItem(_translate("MainWindow", "Lat")))
        self.gps_table.horizontalHeader().setVisible(True)
        self.gps_table.horizontalHeader().setMinimumSectionSize(40)
        self.gps_table.verticalHeader().setStretchLastSection(False)
        self.gps_table.setMinimumWidth(150 + 120 + 120)
        self.gps_table.setMaximumWidth(150 + 120 + 120)
        self.gps_table.setColumnWidth(0, 150)
        self.gps_table.setSortingEnabled(True)

        # GPS widget
        self.gps_view = MapWidget(self.central_widget)
        # Main Layout
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.gps_table)
        self.layout.addWidget(self.gps_view)
        self.central_widget.setLayout(self.layout)
        # Actions
        self.save_act = QAction(QIcon(str(icon_path / "save.png")), "Save GPS coords...", self)
        self.save_act.setShortcut('Ctrl+S')
        self.save_act.triggered.connect(self.save_gps)
        self.save_act.setEnabled(True)
        self.addAction(self.save_act)
        self.screen_cap_act = QAction("Save current map screenshot...", self)
        self.screen_cap_act.setShortcut('Ctrl+Shift+S')
        self.screen_cap_act.triggered.connect(self.screen_capture)
        self.screen_cap_act.setEnabled(True)
        self.addAction(self.screen_cap_act)
        self.decrease_opacity_act = QAction("Decrease marker opacity...", self)
        self.decrease_opacity_act.setShortcut('Ctrl+-')
        self.decrease_opacity_act.triggered.connect(self._decrease_opacity)
        self.decrease_opacity_act.setEnabled(True)
        self.addAction(self.decrease_opacity_act)
        self.increase_opacity_act = QAction("Increase marker opacity...", self)
        self.increase_opacity_act.setShortcut('Ctrl+=')
        self.increase_opacity_act.triggered.connect(self._increase_opacity)
        self.increase_opacity_act.setEnabled(True)
        self.addAction(self.increase_opacity_act)

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        file_menu.addAction(self.save_act)
        file_menu.addAction(self.screen_cap_act)

        tools_menu = menubar.addMenu("Tools")
        tools_menu.addAction(self.decrease_opacity_act)
        tools_menu.addAction(self.increase_opacity_act)

        # Working with the maps with pyqtlet
        self.map = L.map(self.gps_view)
        self.map.setView([0., 0.], 10)
        # https://leaflet-extras.github.io/leaflet-providers/preview/
        L.tileLayer('https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png', {
            'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(self.map)
        # L.tileLayer('https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}{r}.png').addTo(self.map)

        # Add the editing tools for the map
        self.drawControl = MyDraw(options={
            'position': 'topleft',
            'draw': {
                "polyline": False,
                "polygon": False,
                "rectangle": False,
                "circle": False,
                "circlemarker": False,
                "marker": {"repeatMode": False}
            }
        }, handleFeatureGroup=True).addTo(self.map)

        self.map.drawCreated.connect(self.on_draw_created)

        # opacity level
        self.opacity_selected = opacity_selected
        self.opacity_unselected = opacity_unselected
        # Dic of items: {file: item}
        self.items_dic = {}
        # Dic of selected markers. {file: marker}. For now it should only be one selected file
        self.selected_items = {}

    def _reset_state(self):
        # Clear the table of results
        self.gps_table.setRowCount(0)
        # Remove all markers from the map
        for (file, item) in self.items_dic.items():
            self.drawControl.featureGroup.removeLayer(item.marker)

        self.selected_items = {}
        self.items_dic = {}

    def _increase_opacity(self):
        return self.update_opacity_by(0.1)

    def _decrease_opacity(self):
        return self.update_opacity_by(-0.1)

    def update_opacity_by(self, incr):
        self.opacity_unselected = min(max(self.opacity_unselected + incr, 0.0), 1.0)
        for item in self.items_dic.values():
            item.marker.setOpacity(self.opacity_unselected)
        for item in self.selected_items.values():
            item.marker.setOpacity(self.opacity_selected)

    def screen_capture(self):
        # Proposed save folder = the dir containing the pictures
        dirpath = self._model.dirpath
        size = self.gps_view.contentsRect()
        qimage = QPixmap(size.width(), size.height())
        self.gps_view.render(qimage)

        """Save the image displayed in the label."""
        if not qimage.isNull():
            image_file, _ = QFileDialog.getSaveFileName(self, "Save Image",
                                                        dirpath, "JPG Files (*.jpeg *.jpg );;"
                                                                 "PNG Files (*.png);;"
                                                                 "Bitmap Files (*.bmp);;GIF Files (*.gif)")

            if image_file and qimage.isNull() == False:
                qimage.save(image_file)
            else:
                QMessageBox.information(self, "Error",
                                        "Unable to save image.", QMessageBox.Ok)
        else:
            QMessageBox.information(self, "Empty Image",
                                    "There is no image to save.", QMessageBox.Ok)

    def on_table_double_clicked(self, index):
        row = index.row()
        file = self.gps_table.item(row, 0).file
        self._controller.set_media_path(file)

    def on_gps_table_item_changed(self, obj):
        pass

    @pyqtSlot(Path)
    def on_dirpath_changed(self, dirpath: Path):
        self.set_dirpath(dirpath)

    @pyqtSlot(Path)
    def on_dir_content_changed(self, dirpath: Path):
        self.set_dirpath(dirpath)

    @pyqtSlot(Path)
    def on_media_changed(self, file: Path):
        if file is None:
            return
        # Center map on double cliked item
        lng, lat = exif.get_lng_lat(file)
        if lng and lat:
            for item in self.selected_items.values():
                item.marker.setOpacity(self.opacity_unselected)
            self.selected_items = {}
            self.map.setView([lat, lng])
            item = self.items_dic[file]
            item.marker.setOpacity(self.opacity_selected)
            self.selected_items[file] = self.items_dic[file]

        # Select the right row in the table
        for i in range(self.gps_table.rowCount()):
            if file == self.gps_table.item(i, 0).file:
                self.gps_table.selectRow(i)
                break

    @pyqtSlot(dict)
    def on_draw_created(self, event):

        indices = self.gps_table.selectedIndexes()
        if len(indices) == 0:
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Warning)
            self.msg.setText("No picture has been selected for this marker...")
            self.msg.setWindowTitle("Informational Message")
            self.msg.show()
            return

        if not self.is_set_view_init:
            lng, lat = event['layer']['_latlng']['lng'], event['layer']['_latlng']['lat']
            self.map.setView([lat, lng], 10)
            self.is_set_view_init = True

        for idx in indices:
            file = self.gps_table.item(idx.row(), 0).file
            lng, lat = event['layer']['_latlng']['lng'], event['layer']['_latlng']['lat']
            self.items_dic[file].set_lng_lat(lng, lat, update_marker=True)
            self.drawControl.featureGroup.addLayer(self.items_dic[file].marker)

    def set_dirpath(self, dirpath):
        self._reset_state()
        self.gps_table.blockSignals(True)
        for file in self._model.files:
            try:
                if file.suffix not in FILE_EXTENSION_PHOTO_JPG:
                    continue
            except:
                continue

            lng, lat = exif.get_lng_lat(file)
            item = MyQTableWidgetItem(file=file, map=self.map, lng=lng, lat=lat)
            self.items_dic[file] = item
            if item.marker:
                self.drawControl.featureGroup.addLayer(item.marker)

        # Show the results
        self._display_results_table()
        self._display_result_figure()
        self.gps_table.blockSignals(False)
        # Activate a selected imagepath changed
        self.on_media_changed(self._model.media_path)

    # Set the results and display them
    def _display_results_table(self):
        # Clear the table of results
        self.gps_table.setRowCount(0)
        # Set row and col counts
        if (self.items_dic is None) or (len(self.items_dic.keys()) == 0):
            return
        self.gps_table.setRowCount(len(self.items_dic.keys()))

        # Populate the table
        # https://stackoverflow.com/questions/7960505/strange-qtablewidget-behavior-not-all-cells-populated-after-sorting-followed-b
        # Bug workaround: deactivate sorting during repopulation
        self.gps_table.setSortingEnabled(False)
        for i, (file, item) in enumerate(self.items_dic.items()):
            self.gps_table.setItem(i, 0, item)
            self.gps_table.setItem(i, 1, item.item_lng)
            self.gps_table.setItem(i, 2, item.item_lat)
        self.gps_table.setSortingEnabled(True)
        self.gps_table.repaint()

    def _display_result_figure(self):
        self.is_set_view_init = False
        for i, (file, item) in enumerate(self.items_dic.items()):
            if item is None:
                continue
            if not self.is_set_view_init and item.lng and item.lat:
                self.map.setView([item.lat, item.lng], 10)
                self.is_set_view_init = True

    def save_gps(self):
        for item in self.items_dic.values():
            item.save_gps()
