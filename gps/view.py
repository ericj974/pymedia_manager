import os
import sys
from functools import partial

import piexif
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import *

import utils
from controller import MainController
from editor_img import widgets
from gps.widgets import MyDraw, MyMapWidget, MyQTableWidgetItem
from model import MainModel
from thirdparty.pyqtlet.pyqtlet import L
from thirdparty.pyqtlet.pyqtlet.leaflet import Marker
from thirdparty.pyqtlet.pyqtlet.leaflet.core import Evented

icon_path = os.path.join(os.path.dirname(os.path.abspath(widgets.__file__)), "icons")

opacity_selected = 1.0
opacity_unselected = 0.7


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

        # listen for model event signals
        self._model.selected_dir_changed.connect(self.on_dirpath_changed)
        self._model.selected_media_changed.connect(self.on_imagepath_changed)
        # self._model.selected_image_changed.connect(self.on_selected_image_changed)
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
        self.gps_view = MyMapWidget(self.central_widget)
        # # See https://stackoverflow.com/questions/66925445/qt-webengine-not-loading-openstreetmap-tiles
        # interceptor = Interceptor()
        # self.gps_view.page.profile().setRequestInterceptor(interceptor)
        # Main Layout
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.gps_table)
        self.layout.addWidget(self.gps_view)
        self.central_widget.setLayout(self.layout)
        # Actions
        self.save_act = QAction(QIcon(os.path.join(icon_path, "save.png")), "Save GPS coords...", self)
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
            "polyline": False,
            "polygon": False,
            "rectangle": False,
            "circle": False,
            "circlemarker": False,
            "marker": {"repeatMode": False}
        }, handleFeatureGroup=True)

        self.map.addControl(self.drawControl)
        self.map.drawCreated.connect(self.on_draw_created)

        # opacity level
        self.opacity_selected = opacity_selected
        self.opacity_unselected = opacity_unselected
        # Dic containing the exif. {file: exif}
        self.exif_dic = {}
        # Dict of markers. {file: marker}
        self.markers_dic = {}
        # Dic of selected markers. {file: marker}. For now it should only be one selected file
        self.selected_markers = {}

    def _reset_state(self):
        # Reset everything
        self.gps_table.setRowCount(0)
        self.exif_dic = {}
        for (file, marker) in self.markers_dic.items():
            self.drawControl.featureGroup.removeLayer(marker)
        self.selected_markers = {}
        self.markers_dic = {}

    def _increase_opacity(self):
        return self.update_opacity_by(0.1)

    def _decrease_opacity(self):
        return self.update_opacity_by(-0.1)

    def update_opacity_by(self, incr):
        self.opacity_unselected = min(max(self.opacity_unselected + incr, 0.0), 1.0)
        for marker in self.markers_dic.values():
            marker.setOpacity(self.opacity_unselected)
            marker.setZIndexOffset(0.)
        for marker in self.selected_markers.values():
            marker.setOpacity(self.opacity_selected)
            marker.setZIndexOffset(1000.)

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

    @pyqtSlot(str)
    def on_dirpath_changed(self, dirpath):
        self.set_dirpath(dirpath)

    @pyqtSlot(str)
    def on_dir_content_changed(self, dirpath):
        self.set_dirpath(dirpath)

    @pyqtSlot(str)
    def on_imagepath_changed(self, file):
        if file == '':
            return
        # Center map on double cliked item
        result = self.exif_dic.get(file)
        if result is not None and \
                piexif.GPSIFD.GPSLongitude in result['GPS'] and \
                piexif.GPSIFD.GPSLatitude in result['GPS']:
            for marker in self.selected_markers.values():
                marker.setOpacity(self.opacity_unselected)
                marker.setZIndexOffset(0.)
            self.selected_markers = {}

            lng = utils.dms_to_deg(result['GPS'][piexif.GPSIFD.GPSLongitude],
                                   result['GPS'][piexif.GPSIFD.GPSLongitudeRef])
            lat = utils.dms_to_deg(result['GPS'][piexif.GPSIFD.GPSLatitude],
                                   result['GPS'][piexif.GPSIFD.GPSLatitudeRef])
            self.map.setView([lat, lng])
            marker = self.markers_dic[file]
            marker.setOpacity(self.opacity_selected)
            marker.setZIndexOffset(1000.)

            self.selected_markers[file] = self.markers_dic[file]

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
        for idx in indices:
            file = self.gps_table.item(idx.row(), 0).file
            lng, lat = event['layer']['_latlng']['lng'], event['layer']['_latlng']['lat']
            if not self.is_set_view_init:
                self.map.setView([lat, lng], 10)
                self.is_set_view_init = True
            self._update_gps_table(file, event['layer']['_latlng'])
            if file in self.markers_dic:
                marker = self.markers_dic[file]
                marker.setLatLng([lat, lng])
                marker.setZIndexOffset(0.)
            else:
                marker = Marker([lat, lng], options={'draggable': 'true'})
                marker.setOpacity(self.opacity_unselected)
                marker.setZIndexOffset(0.)
                marker.bindPopup(os.path.basename(file))
                self.markers_dic[file] = marker
            self.exif_dic[file] = utils.update_geotagging(self.exif_dic[file], lng, lat)
            self.drawControl.featureGroup.addLayer(marker)

    def set_dirpath(self, dirpath):
        self._reset_state()

        # generator = glob.iglob(os.path.join(dirpath, "*.jpg"))
        for file in self._model.files:
            exif = utils.get_exif_v2(file)
            if not exif:
                self.exif_dic[file] = None
            else:
                try:
                    self.exif_dic[file] = exif
                except ValueError:
                    self.exif_dic[file] = None

        # Show the results
        self._display_results_table()

    # Set the results and display them
    def _display_results_table(self):
        # Clear the table of results
        self.gps_table.setRowCount(0)
        # Set row and col counts
        if (self.exif_dic is None) or (len(self.exif_dic.keys()) == 0):
            return
        self.gps_table.setRowCount(len(self.exif_dic.keys()))

        # Populate the table
        # https://stackoverflow.com/questions/7960505/strange-qtablewidget-behavior-not-all-cells-populated-after-sorting-followed-b
        # Bug workaround: deactivate sorting during repopulation
        self.gps_table.setSortingEnabled(False)
        for i, (file, exif) in enumerate(self.exif_dic.items()):
            item = MyQTableWidgetItem(os.path.basename(file), file)
            self.gps_table.setItem(i, 0, item)
            if exif is not None and \
                    'GPS' in exif and \
                    piexif.GPSIFD.GPSLongitude in exif['GPS'] and \
                    piexif.GPSIFD.GPSLatitude in exif['GPS']:
                lng = utils.dms_to_deg(exif['GPS'][piexif.GPSIFD.GPSLongitude],
                                       exif['GPS'][piexif.GPSIFD.GPSLongitudeRef])
                lat = utils.dms_to_deg(exif['GPS'][piexif.GPSIFD.GPSLatitude],
                                       exif['GPS'][piexif.GPSIFD.GPSLatitudeRef])
            else:
                lng, lat = '', ''

            self.gps_table.setItem(i, 1, MyQTableWidgetItem(str(lng), file))
            self.gps_table.setItem(i, 2, MyQTableWidgetItem(str(lat), file))

        self.gps_table.setSortingEnabled(True)
        self.gps_table.repaint()
        self._display_result_figure()

    def _display_result_figure(self):
        file_list = []
        lng_mer_list = []
        lat_mer_list = []
        self.is_set_view_init = False
        for i, (file, result) in enumerate(self.exif_dic.items()):
            if result is None:
                continue
            if piexif.GPSIFD.GPSLongitude in result['GPS'] and piexif.GPSIFD.GPSLatitude in result['GPS']:
                lng = utils.dms_to_deg(result['GPS'][piexif.GPSIFD.GPSLongitude],
                                       result['GPS'][piexif.GPSIFD.GPSLongitudeRef])
                lat = utils.dms_to_deg(result['GPS'][piexif.GPSIFD.GPSLatitude],
                                       result['GPS'][piexif.GPSIFD.GPSLatitudeRef])
                lng_mer_list.append(lng)
                lat_mer_list.append(lat)
                file_list.append(file)
                if not self.is_set_view_init:
                    self.map.setView([lat, lng], 10)
                    self.is_set_view_init = True

        if len(file_list) > 0:
            self.map.setView([lat_mer_list[0], lng_mer_list[0]], zoom=17)
            for i, file in enumerate(file_list):
                marker = Marker([lat_mer_list[i], lng_mer_list[i]], options={'draggable': 'true'})
                marker.setOpacity(self.opacity_unselected)
                marker.setZIndexOffset(0.)
                marker.bindPopup(os.path.basename(file))
                # icon = Icon("red")
                # marker.setIcon(icon)
                self.markers_dic[file] = marker
                self.drawControl.featureGroup.addLayer(marker)

        # Activate a selected imagepath changed
        self.on_imagepath_changed(self._model.media_path)

    def on_change_data_source(self, attr, old, new):
        pass

    def _save_gps_async(self, file, lng_lat_new):
        exif = self.exif_dic[file]
        lng = utils.dms_to_deg(exif['GPS'][piexif.GPSIFD.GPSLongitude], exif['GPS'][piexif.GPSIFD.GPSLongitudeRef])
        lat = utils.dms_to_deg(exif['GPS'][piexif.GPSIFD.GPSLatitude], exif['GPS'][piexif.GPSIFD.GPSLatitudeRef])

        if lng == lng_lat_new['lng'] and lat == lng_lat_new['lat']:
            return
        print(f'Saving exif GPS info for file {file}')

        exif = utils.update_geotagging(exif, lng_lat_new['lng'], lng_lat_new['lat'])
        self.exif_dic[file] = exif
        utils.save_exif(exif, filepath=file)

    def save_gps(self):
        for file, marker in self.markers_dic.items():
            if not isinstance(marker, Marker):
                continue
            js = '{layerName}.getLatLng()'.format(
                layerName=marker._layerName)
            partial_get_lng_lat = partial(self._save_gps_async, file)
            partial_get_lng_lat.__name__ = "partial_get_lng_lat"
            marker.getJsResponse(js, partial_get_lng_lat)

    def _update_gps_table(self, file, lnglat_dic):
        for i in range(self.gps_table.rowCount()):
            item = self.gps_table.item(i, 0)
            if file != item.file:
                continue
            self.gps_table.item(i, 1).setText(str(lnglat_dic['lng']))
            self.gps_table.item(i, 2).setText(str(lnglat_dic['lat']))


