from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtWidgets import QTableWidgetItem

from thirdparty.pyqtlet.pyqtlet import MapWidget
from thirdparty.pyqtlet.pyqtlet.leaflet.control import Draw


class MyDraw(Draw):

    def addDrawnToFeatureGroup(self):
        self.map.addLayer(self.featureGroup)


class MyMapWidget(MapWidget):
    def __init__(self, parent):
        super(MyMapWidget, self).__init__()


class MyQTableWidgetItem(QTableWidgetItem):
    def __init__(self, text, file):
        super().__init__(text)
        self.file = file


class Interceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        info.setHttpHeader(b"Accept-Language", b"en-US,en;q=0.9,es;q=0.8,de;q=0.7")
