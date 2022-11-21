from PyQt5.QtCore import QObject, pyqtSignal

from controller import MainController
from model import MainModel
from utils import load_image
from views.face_editor import utils
from views.face_editor.utils import detection_backend, face_recognition_model


class DetectionResult:

    def __init__(self, file, encoding, img, location, name):
        self.file = file
        self.encoding = encoding
        self.img = img
        self.location = location
        self.name = name


class FaceDetectionModel(QObject):
    # Change of detection model
    detection_model_changed = pyqtSignal(str)
    # Change of recognition model
    recognition_model_changed = pyqtSignal(str)
    # Detection results
    detection_results_changed = pyqtSignal(DetectionResult)

    def __init__(self, db):
        super(FaceDetectionModel, self).__init__()
        self._detection_model = detection_backend[0]
        self._recognition_model = face_recognition_model[0]
        self._det_results = {}
        self.db = db

    @property
    def detection_model(self):
        return self.detection_model

    @detection_model.setter
    def detection_model(self, value):
        self._detection_model = value
        self.detection_model_changed.emit(value)

    @property
    def recognition_model(self):
        return self.detection_model

    @recognition_model.setter
    def recognition_model(self, value):
        self._recognition_model = value
        self.recognition_model_changed.emit(value)


class FaceDetectionController:
    def __init__(self, model: FaceDetectionModel):
        super(self.__class__, self).__init__()
        # init
        self._model = model

    def set_detection_model(self, model):
        assert model in detection_backend, "detection model not recognized"
        self._model.detection_model = model

    def set_recognition_model(self, model):
        assert model in face_recognition_model, "recognition model not recognized"
        self._model.recognition_model = model

    def detect_faces_batch(self, files):
        self.results = {}

        ind = 0

        for file in files:
            qimage, exif_dict = load_image(file)
            encodings, imgs, locations, names = utils.face_recognition(qimage=qimage,
                                                                       detection_backend=self._model.detection_model,
                                                                       face_recognition_model=self._model.recognition_model,
                                                                       db=self.db)

            # Keep Track
            self.results[file] = (file, encodings, imgs, locations, names)

            # Display
            for (encoding, img, location, name) in zip(encodings, imgs, locations, names):
                filename = os.path.basename(file)
                self.table_result.setItem(ind, 0, MyQTableWidgetItem(filename, file, encoding, img, location, name))
                self.table_result.setItem(ind, 1, QTableWidgetItem(filename))
                ind += 1
