from PyQt5.QtCore import QObject, pyqtSignal

from common.face import detection_backend, face_recognition_model


class FaceDetectionModel(QObject):
    # Change of detection model
    detection_model_changed = pyqtSignal(str)
    # Change of recognition model
    recognition_model_changed = pyqtSignal(str)
    # Detection results for the file specified by main model
    detection_results_changed = pyqtSignal(list)
    # Selected detection result
    selected_detection_result_changed = pyqtSignal(int)

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

    def set_selection(self, idx):
        self.selected_detection_result_changed.emit(idx)
