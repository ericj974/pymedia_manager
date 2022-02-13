from .control import Control
from .layer import LayerGroup, FeatureGroup, imageOverlay
from .layer.marker import Marker
from .layer.marker.icon import Icon
from .layer.tile import TileLayer
from .layer.vector import Circle, CircleMarker, Polygon, Polyline, Rectangle
from .map import Map


class L:
    """
    Leaflet namespace that holds reference to all the leaflet objects
    """
    map = Map
    tileLayer = TileLayer
    imageOverlay = imageOverlay
    marker = Marker
    icon = Icon
    circleMarker = CircleMarker
    polyline = Polyline
    polygon = Polygon
    rectangle = Rectangle
    circle = Circle
    layerGroup = LayerGroup
    featureGroup = FeatureGroup
    control = Control
