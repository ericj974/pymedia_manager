import logging
import time
from enum import Enum

import cv2
import numpy as np
from deepface import DeepFace
from deepface.basemodels import VGGFace, OpenFace, Facenet, Facenet512, FbDeepFace, DeepID, ArcFace, DlibWrapper, \
    Boosting
from deepface.commons import functions, distance as dst
from deepface.detectors import (DlibWrapper as DDlibWrapper, SsdWrapper, RetinaFaceWrapper,
                                MtcnnWrapper, OpenCvWrapper)
from deepface.extendedmodels import Emotion, Age, Gender, Race
from tqdm import tqdm

"""
    Generic Model Types
"""


class ModelType(Enum):
    ENSEMBLE = ('Ensemble', Boosting.loadModel)
    VGG_FACE = ('VGGFace', VGGFace.loadModel)
    OPEN_FACE = ('OpenFace', OpenFace.loadModel)
    FACENET = ('Facenet', Facenet.loadModel)
    FACENET512 = ('Facenet512', Facenet512.loadModel)
    DEEP_FACE = ('DeepFace', FbDeepFace.loadModel)
    DEEP_ID = ('DeepID', DeepID.loadModel)
    DLIB = ('Dlib', DlibWrapper.loadModel)
    ARC_FACE = ('ArcFace', ArcFace.loadModel)
    EMOTION = ('Emotion', Emotion.loadModel)
    AGE = ('Age', Age.loadModel)
    GENDER = ('Gender', Gender.loadModel)
    RACE = ('Race', Race.loadModel)

    def __init__(self, name, load_model):
        self.model_name = name
        self.load_model = load_model

    @staticmethod
    def get_model_from_name(name: str):
        for model in ModelType:
            if model.model_name == name:
                return model


"""
    Detector Model Types
"""


class FaceDetectorBackendType(Enum):
    OPENCV = ('opencv', OpenCvWrapper.build_model, OpenCvWrapper.detect_face)
    SSD = ('ssd', SsdWrapper.build_model, SsdWrapper.detect_face)
    DLIB = ('dlib', DlibWrapper, DDlibWrapper.detect_face)
    MTCNN = ('mtcnn', MtcnnWrapper.build_model, MtcnnWrapper.detect_face)
    RETINA_FACE = ('retinaface', RetinaFaceWrapper.build_model, RetinaFaceWrapper.detect_face)

    def __init__(self, name, build_model, detect_face):
        self.model_name = name
        self.build_model = build_model
        self.detect_face = detect_face

    @staticmethod
    def get_model_from_name(name: str):
        for model in FaceDetectorBackendType:
            if model.model_name == name:
                return model


class FaceDetectorManager():
    # Class instance. Holding detector instances
    # detector stored in a global variable in FaceDetector object.
    # this call should be completed very fast because it will return found in memory
    # it will not build face detector model in each call (consider for loops)
    model_obj = {}

    @staticmethod
    def get_model(backend_type: FaceDetectorBackendType):
        if backend_type not in FaceDetectorManager.model_obj:
            face_build_model = backend_type.build_model()
            # Keep track of the instance
            FaceDetectorManager.model_obj[backend_type] = face_build_model
        return FaceDetectorManager.model_obj[backend_type]

    @staticmethod
    def detect_faces(img_path: str, detector_backend_type: FaceDetectorBackendType = FaceDetectorBackendType.OPENCV,
                     enforce_detection: bool = True, align: bool = True, grayscale: bool = False,
                     target_size: tuple = None, return_region: bool = False):
        """

        Args:
            img_path:
            detector_backend_type:
            enforce_detection:
            align:
            grayscale:
            target_size: If not None, target (height,width) shape in pixels. Otherwise, no resizing is performed.
            return_region:

        Returns:

        """

        # img might be path, base64 or numpy array. Convert it to numpy whatever it is.
        img = functions.load_image(img_path)
        base_img = img.copy()

        try:
            detector_instance = FaceDetectorManager.get_model(detector_backend_type)
            obj = detector_backend_type.detect_face(detector_instance, img, align)

            if len(obj) > 0:
                obj_ok = []
                # Sanity check
                for detected_face, face_region in obj:
                    if detected_face.shape[0] > 0 and detected_face.shape[1] > 0:
                        obj_ok.append((detected_face, face_region))

                if len(obj_ok) == 0:
                    if enforce_detection == True:
                        raise ValueError("All detected face shapes have a 0 size ",
                                         ". Consider to set enforce_detection argument to False.")
                    else:
                        for (_, face_region) in obj:
                            detected_face = base_img.copy()
                            obj_ok.append((detected_face, face_region))
                else:
                    obj = obj_ok
            else:  # len(obj) == 0
                if enforce_detection != True:
                    detected_face = img
                else:
                    raise ValueError(
                        "Face could not be detected. Please confirm that the picture is a face photo or consider to set enforce_detection param to False.")
                face_region = [0, 0, img.shape[0], img.shape[1]]
                obj = [(detected_face, face_region)]
        except:  # if detected face shape is (0, 0) and alignment cannot be performed, this block will be run
            detected_face = img
            face_region = [0, 0, img.shape[0], img.shape[1]]
            obj = [(detected_face, face_region)]

        # --------------------------
        results = []
        for detected_face, face_region in obj:
            # post-processing
            detected_face = cv2.cvtColor(detected_face, cv2.COLOR_BGR2GRAY) if grayscale else detected_face

            # resize image to expected shape
            if target_size is not None:
                factor_0 = target_size[0] / detected_face.shape[0]
                factor_1 = target_size[1] / detected_face.shape[1]
                factor = min(factor_0, factor_1)

                dsize = (int(detected_face.shape[1] * factor), int(detected_face.shape[0] * factor))
                detected_face = cv2.resize(detected_face, dsize)

                # Then pad the other side to the target size by adding black pixels
                diff_0 = target_size[0] - detected_face.shape[0]
                diff_1 = target_size[1] - detected_face.shape[1]

                # Padding
                if grayscale:
                    detected_face = np.pad(detected_face,
                                           ((diff_0 // 2, diff_0 - diff_0 // 2), (diff_1 // 2, diff_1 - diff_1 // 2)),
                                           'constant')
                else:
                    # Put the base image in the middle of the padded image
                    detected_face = np.pad(detected_face,
                                           ((diff_0 // 2, diff_0 - diff_0 // 2), (diff_1 // 2, diff_1 - diff_1 // 2),
                                            (0, 0)),
                                           'constant')

                # double check: if target image is not still the same size with target.
                if detected_face.shape[0:2] != target_size:
                    detected_face = cv2.resize(detected_face, target_size)

            # Final steps
            # BGR to RGB
            detected_face = detected_face.squeeze()[:, :, ::-1]  # bgr to rgb
            # uint8 repr
            detected_face = detected_face.astype(np.uint8)
            if return_region:
                results.append((detected_face, face_region))
            else:
                results.append(detected_face)

        return results

    @staticmethod
    def recognize_face(img_path, dataset_manager, enforce_detection=True, detector_backend='opencv',
                       align=True, prog_bar=True, normalization='base'):

        """
        This function applies verification several times and find an identity in a database

        Parameters:
            img_path: exact image path, numpy array or based64 encoded image. If you are going to find several identities, then you should pass img_path as array instead of calling find function in a for loop. e.g. img_path = ["img1.jpg", "img2.jpg"]

            db_path (string): You should store some .jpg files in a folder and pass the exact folder path to this.

            distance_metric (string): cosine, euclidean, euclidean_l2

            enforce_detection (boolean): The function throws exception if a face could not be detected. Set this to True if you don't want to get exception. This might be convenient for low resolution images.

            detector_backend (string): set face detector backend as retinaface, mtcnn, opencv, ssd or dlib

            prog_bar (boolean): enable/disable a progress bar

        Returns:
            This function returns pandas data frame. If a list of images is passed to img_path, then it will return list of pandas data frame.
        """
        tic = time.time()
        img_paths, bulkProcess = functions.initialize_input(img_path)
        df = dataset_manager.store
        df_base = dataset_manager.store.copy()  # df will be filtered in each img. we will restore it for the next item.

        resp_obj = []

        global_pbar = tqdm(range(0, len(img_paths)), desc='Analyzing', disable=prog_bar)
        for index in global_pbar:
            img_path = img_paths[index]
            for model_name in dataset_manager.model_names:
                custom_model = dataset_manager.models[model_name]
                target_representation = DeepFace.represent(img_path=img_path,
                                                           model_name=model_name, model=custom_model,
                                                           enforce_detection=enforce_detection,
                                                           detector_backend=detector_backend,
                                                           align=align,
                                                           normalization=normalization)
                # Loop over the metrics
                for metric_name in dataset_manager.metric_names:
                    distances = []
                    for index, instance in df.iterrows():
                        source_representation = instance[f"{model_name}_representation"]

                        if metric_name == 'cosine':
                            distance = dst.findCosineDistance(source_representation, target_representation)
                        elif metric_name == 'euclidean':
                            distance = dst.findEuclideanDistance(source_representation, target_representation)
                        elif metric_name == 'euclidean_l2':
                            distance = dst.findEuclideanDistance(dst.l2_normalize(source_representation),
                                                                 dst.l2_normalize(target_representation))
                        else:
                            raise NameError(f"Metric {metric_name} is not recognized...")
                        distances.append(distance)

                    # ---------------------------

                    if dataset_manager._model_name == 'Ensemble':
                        if model_name == 'OpenFace' and metric_name == 'euclidean':
                            continue
                        else:
                            df[f"{model_name}_{metric_name}"] = distances
                    else:
                        df[f"{model_name}_{metric_name}"] = distances
                        threshold = dst.findThreshold(model_name, metric_name)
                        df = df.drop(columns=[f"{model_name}_representation"])
                        df = df[df[f"{model_name}_{metric_name}"] <= threshold]
                        df = df.sort_values(by=[f"{model_name}_{metric_name}"], ascending=True).reset_index(drop=True)
                        resp_obj.append(df)
                        df = df_base.copy()  # restore df for the next iteration

            if dataset_manager._model_name == 'Ensemble':
                feature_names = []
                for model_name in dataset_manager.model_names:
                    for metric_name in dataset_manager.metric_names:
                        if dataset_manager._model_name == 'Ensemble' and model_name == 'OpenFace' and metric_name == 'euclidean':
                            continue
                        else:
                            feature = f"{model_name}_{metric_name}"
                            feature_names.append(feature)

                x = df[feature_names].values

                # --------------------------------------

                boosted_tree = Boosting.build_gbm()

                y = boosted_tree.predict(x)

                verified_labels = []
                scores = []
                for i in y:
                    verified = np.argmax(i) == 1
                    score = i[np.argmax(i)]

                    verified_labels.append(verified)
                    scores.append(score)

                df['verified'] = verified_labels
                df['score'] = scores
                df = df[df.verified == True]
                df = df.sort_values(by=["score"], ascending=False).reset_index(drop=True)
                df = df[['identity', 'verified', 'score']]
                resp_obj.append(df)
                df = df_base.copy()  # restore df for the next iteration

        toc = time.time()
        logging.info("find function lasts ", toc - tic, " seconds")

        if len(resp_obj) == 1:
            return resp_obj[0]
        return resp_obj
