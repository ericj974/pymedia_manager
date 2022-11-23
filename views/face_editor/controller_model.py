from PyQt5.QtCore import QObject, pyqtSignal

from utils import load_image
from views.face_editor import utils
from views.face_editor.utils import detection_backend, face_recognition_model, DetectionResult


class FaceDetectionModel(QObject):
    # Change of detection model
    detection_model_changed = pyqtSignal(str)
    # Change of recognition model
    recognition_model_changed = pyqtSignal(str)
    # Detection results
    detection_results_changed = pyqtSignal(list)

    def __init__(self, db):
        super(FaceDetectionModel, self).__init__()
        self._detection_model = detection_backend[0]
        self._recognition_model = face_recognition_model[0]
        self._det_results = {}
        self.db = db

    @property
    def detection_model(self):
        return self._detection_model

    @detection_model.setter
    def detection_model(self, value: str):
        self._detection_model = value
        self.detection_model_changed.emit(value)

    @property
    def recognition_model(self):
        return self._recognition_model

    @recognition_model.setter
    def recognition_model(self, value: str):
        self._recognition_model = value
        self.recognition_model_changed.emit(value)

    @property
    def detection_results(self):
        return self._det_results

    @detection_results.setter
    def detection_results(self, value: list):
        self._det_results = value
        self.detection_results_changed.emit(value)


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

    def set_detection_results(self, results: list):
        self._model.detection_results = results

    def detect_faces(self, files):
        detections = []

        for file in files:
            temp = utils.face_recognition(file=file,
                                          detection_model=self._model.detection_model,
                                          recognition_model=self._model.recognition_model,
                                          db=self._model.db)
            detections += temp

        # Update model
        self.set_detection_results(detections)
