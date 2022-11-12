import warnings

import cv2
import numpy as np
from deepface.detectors import FaceDetector

warnings.filterwarnings("ignore")

import os

# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from deepface.commons import functions, realtime, distance as dst
from deepface.DeepFace import build_model

import tensorflow as tf

tf_version = int(tf.__version__.split(".")[0])
if tf_version == 2:
    import logging

    tf.get_logger().setLevel(logging.ERROR)

def face_locations(img, detector_backend='opencv', align=True):

    img = img[:, :, ::-1]  # rgb to bgr
    img_region = [0, 0, img.shape[0], img.shape[1]]
    face_detector = FaceDetector.build_model(detector_backend)
    obj = FaceDetector.detect_faces(face_detector, detector_backend, img, align)
    if len(obj) > 0:
        # (top, right, bottom, left)
        regions = [[region[1], region[0]+region[2], region[1]+region[3], region[0]] for _, region in obj]
        imgs = [img for img, _ in obj]
    else:
        regions = []
        imgs = []

    # bgr to rgb
    imgs = [img[:, :, ::-1] for img in imgs]
    return imgs, regions

def face_encodings(imgs, model_name='VGG-Face', align=True, normalization='base'):
    """
    This function represents facial images as vectors.
    Parameters:
        img: numpy array (RGB)
        model_name (string): VGG-Face, Facenet, OpenFace, DeepFace, DeepID, Dlib, ArcFace.
        model: Built deepface model. A face recognition model is built every call of verify function. You can pass pre-built face recognition model optionally if you will call verify function several times. Consider to pass model if you are going to call represent function in a for loop.
            model = DeepFace.build_model('VGG-Face')
        enforce_detection (boolean): If any face could not be detected in an image, then verify function will return exception. Set this to False not to have this exception. This might be convenient for low resolution images.
        detector_backend (string): set face detector backend as retinaface, mtcnn, opencv, ssd or dlib
        normalization (string): normalize the input image before feeding to model
    Returns:
        Represent function returns a multidimensional vector. The number of dimensions is changing based on the reference model. E.g. FaceNet returns 128 dimensional vector; VGG-Face returns 2622 dimensional vector.
    """

    # Build model and determine its specific shape
    model = build_model(model_name)
    target_size = functions.find_input_shape(model)

    # For each detection, compute embedding
    embeddings = []
    for img in imgs:
        img = img[:, :, ::-1]  # rgb to bgr
        if img.shape[0] > 0 and img.shape[1] > 0:
            factor_0 = target_size[0] / img.shape[0]
            factor_1 = target_size[1] / img.shape[1]
            factor = min(factor_0, factor_1)

            dsize = (int(img.shape[1] * factor), int(img.shape[0] * factor))
            img = cv2.resize(img, dsize)

            # Then pad the other side to the target size by adding black pixels
            diff_0 = target_size[0] - img.shape[0]
            diff_1 = target_size[1] - img.shape[1]
            # Put the base image in the middle of the padded image
            img = np.pad(img, ((diff_0 // 2, diff_0 - diff_0 // 2), (diff_1 // 2, diff_1 - diff_1 // 2), (0, 0)),
                         'constant')
            # double check: if target image is not still the same size with target.
            if img.shape[0:2] != target_size:
                img = cv2.resize(img, target_size)
            # normalizing the image pixels
            img_pixels = np.expand_dims(img, axis=0)
            img_pixels =  img_pixels.astype(np.float) / 255.  # normalize input in [0, 1]
            # represent
            embedding = model.predict(img_pixels)[0]
            embeddings.append(embedding)
    return embeddings


def face_distance(face_encodings, face_to_compare):
    """
    Given a list of face encodings, compare them to a known face encoding and get a euclidean distance
    for each comparison face. The distance tells you how similar the faces are.

    :param faces: List of face encodings to compare
    :param face_to_compare: A face encoding to compare against
    :return: A numpy ndarray with the distance for each face in the same order as the 'faces' array
    """
    if len(face_encodings) == 0:
        return np.empty((0))

    return np.linalg.norm(face_encodings - face_to_compare, axis=1)

def compare_faces(known_face_encodings, face_encoding_to_check, tolerance=0.6):
    """
    Compare a list of face encodings against a candidate encoding to see if they match.

    :param known_face_encodings: A list of known face encodings
    :param face_encoding_to_check: A single face encoding to compare against the list
    :param tolerance: How much distance between faces to consider it a match. Lower is more strict. 0.6 is typical best performance.
    :return: A list of True/False values indicating which known_face_encodings match the face encoding to check
    """
    return list(face_distance(known_face_encodings, face_encoding_to_check) <= tolerance)

# 'dlib' not installed
detection_backend = ['retinaface', 'mtcnn', 'opencv', 'ssd']
# 'DeepID' not working, 'Dlib' not installed
face_recognition_model = ['Dlib', 'VGG-Face', 'Facenet', 'OpenFace', 'DeepFace', 'ArcFace']
