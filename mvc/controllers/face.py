import common.face as api
from common.face import detection_backend, face_recognition_model
from mvc.models.face import FaceDetectionModel


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

    def set_selected_result(self, idx):
        self._model.set_selection(idx)

    def detect_faces(self, files):
        detections = []

        for file in files:
            temp = api.face_recognition(path=file,
                                        detection_model=self._model.detection_model,
                                        recognition_model=self._model.recognition_model,
                                        db=self._model.db)
            detections += temp

        # Update model
        self.set_detection_results(detections)
