import logging
from pathlib import Path

from PyQt5.QtCore import QJsonValue
from PyQt5.QtWidgets import QTableWidgetItem

from common.exif import get_exif, set_geotagging, save_exif, get_lng_lat
from mvc.views.gps import opacity_unselected
from pyqtlet2.leaflet import Marker
from pyqtlet2.leaflet.control import Draw


class MyDraw(Draw):

    def addDrawnToFeatureGroup(self):
        self.map.addLayer(self.featureGroup)


class MyQTableWidgetItem(QTableWidgetItem):
    def __init__(self, file: Path, map, lng=None, lat=None):
        super().__init__(file.name)
        self.file: Path = file
        self.map = map
        self.lat = lat
        self.lng = lng
        self.item_lng = QTableWidgetItem()
        self.item_lat = QTableWidgetItem()
        self.marker = None
        self.set_lng_lat(lng, lat, True)

    def set_lng_lat(self, lng, lat, update_marker=True):
        if lng and lat:
            self.lat = lat
            self.lng = lng
            self.item_lng.setText(str(lng) if lng else '')
            self.item_lat.setText(str(lat) if lat else '')
            if update_marker:
                if self.marker:
                    self.marker.setLatLng([lat, lng])
                else:
                    self.marker = Marker([lat, lng], options={'draggable': 'true'}).addTo(self.map)
                    self.marker.setOpacity(opacity_unselected)
                    self.marker.bindPopup(self.file.name)
                    self.marker.moveend.connect(self.on_marker_move)
                    self.marker.move.connect(self.on_marker_move)

    def save_gps(self):
        file = self.file
        if self.lng and self.lat:
            lng, lat = get_lng_lat(file)
            # Avoid re-saving identical coords
            if lng == self.lng and lat == self.lat:
                return
            logging.info(f'Saving exif GPS info to {file}')
            exif = get_exif(file)
            exif = set_geotagging(exif, self.lng, self.lat)
            save_exif(exif, path=file)

    def on_marker_move(self, event: QJsonValue):
        if 'latlng' in event:
            lat, lng = event["latlng"]['lat'], event["latlng"]['lng']
        else:
            lat, lng = event["latLng"]

        self.set_lng_lat(lng=lng, lat=lat, update_marker=False)
