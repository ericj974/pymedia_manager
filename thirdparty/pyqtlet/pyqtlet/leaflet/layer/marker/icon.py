from ...core import Evented


class Icon(Evented):
    # iconId is a static variable shared between all controls
    # It is used to give unique names to controls
    iconId = 0

    def __init__(self, color="red"):
        super().__init__()
        super().__init__()
        self._iconName = self._getNewIconName()
        if color == "red":
            self.options = {
                'iconUrl': '/media/veracrypt1/AAA_DOCUMENTS/CODE/Renamer/pyqtlet/pyqtlet/web/modules/leaflet_171/images/marker-icon.png'
                # 'iconUrl': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                # 'shadowUrl': 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                # 'iconSize': [25, 41],
                # 'iconAnchor': [12, 41],
                # 'popupAnchor': [1, -34],
                # 'shadowSize': [41, 41]
            }
        else:
            raise NotImplementedError()
        self._initJs()

    def _initJs(self):
        leafletJsObject = 'L.icon({options})'.format(options=self.options)
        self._createJsObject(leafletJsObject)

    @property
    def jsName(self):
        return self._iconName

    @property
    def iconName(self):
        return self._iconName

    @iconName.setter
    def iconName(self, name):
        self._iconName = name

    def _getNewIconName(self):
        iconName = 'i{}'.format(self.iconId)
        Icon.iconId += 1
        return iconName
