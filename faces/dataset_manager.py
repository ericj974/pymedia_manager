import logging
import os
import time
from ast import literal_eval

import cv2
import numpy as np
import pandas as pd
from deepface import DeepFace
from deepface.DeepFace import build_model
from deepface.basemodels import Boosting
from deepface.commons import functions, distance as dst
from tqdm import tqdm

from faces.face_manager import ModelType


class FaceDatasetManager():

    def __init__(self, path, model_type=ModelType.FACENET, distance_metric='cosine'):
        assert os.path.exists(path) and os.path.isdir(path)
        # Dataset path
        self.path = path

        self.models = {}
        self.model_names = []
        self.metric_names = []
        self.model_type = model_type

        if model_type == ModelType.ENSEMBLE:
            raise NotImplementedError("Manager not Implemented yet for Ensemble model")
            self.models = Boosting.loadModel()
            self.model_names = ['VGG-Face', 'Facenet', 'OpenFace', 'DeepFace']
            self.metric_names = ['cosine', 'euclidean', 'euclidean_l2']
        else:
            self.models = {model_type.model_name: model_type.load_model}
            self.model_names = [model_type.model_name]
            self.metric_names.append(distance_metric)

        # Store when loading the db
        # self.store_name = f"representations_{model_name}.csv"
        self.store_name = f"representations.csv"
        self.store_path = os.path.join(self.path, self.store_name)
        self.store = None
        self._file_col_names_embeddings = {}
        self.init_store()
        self.rebuild_store_delta()
        print("There are ", len(self.store), " representations found in ", self.store_path)

    def get_col_names(self):
        columns = ['img_name', 'face_name']
        embedding_cols = [f'{name}_representation' for name in self.model_names]
        columns.extend(embedding_cols)
        return columns, embedding_cols

    def init_store(self):
        col_names, col_names_embeddings = self.get_col_names()
        if os.path.exists(self.store_path):
            self.store = pd.read_csv(self.store_path,
                                     converters={name: literal_eval for name in col_names_embeddings})
            self._file_col_names_embeddings = {col for col in self.store.columns if col.endswith("_representation")}
        else:
            self.store = pd.DataFrame([], columns=col_names)
            self._file_col_names_embeddings = col_names_embeddings
            self.save_store()

    def rebuild_store_delta(self):
        """
            Check whether:
            - An image was added but not present in the db (addition)
            - An image is present in the db but not on the disk (deletion)
            - An image has the "correct" naming name_index.jpg
        """
        file_image_names = set(self.list_disk_images())
        store_image_names = set(self.store['img_name'].values)

        store_col_names_embeddings = set(self.get_col_names()[1])

        # files missing in store
        missing_in_store = file_image_names.difference(store_image_names)
        # Missing files
        missing_files = store_image_names.difference(file_image_names)

        logging.info("Removing store filenames with no files on disk ....")
        for f in missing_files:
            indices_to_drop = self.store[self.store['img_name'] == f].index
            self.store.drop(indices_to_drop)

        logging.info("Adding missing filenames in store for existing store models")
        self._build_store(missing_in_store)

        # Missing models in csv file
        missing_embeddings_model_names = store_col_names_embeddings.difference(self._file_col_names_embeddings)
        missing_embeddings_model_names = [item.rsplit("_representation", 1)[0] for item in
                                          missing_embeddings_model_names]
        logging.info("Adding missing embeddings to existing files in store")
        if len(missing_embeddings_model_names) > 0:
            self._build_store(model_names=missing_embeddings_model_names)

    def add_image_to_dataset(self, path, face_name):
        """
            Add one image to the dataset.
                - A detection + alignment
                - Save resulting image with face_name_index.jpg
        """
        # Index of the image
        index = len(self.store[self.store['face_name'] == face_name])
        # Copy to the folder
        img_name = f'{face_name}_{index}.jpg'
        # Face detection and alignment
        img = DeepFace.detectFace(img_path=path, align=True)
        img = (img * 255.).astype(np.uint8)
        # Embedding generation
        embedding_dic = self.get_embedding(path)
        cv2.imwrite(os.path.join(self.path, img_name), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        item = {'img_name': img_name, 'face_name': face_name}
        item.update(embedding_dic)
        self.store.loc[len(self.store)] = item

    def reset_store(self):
        try:
            os.remove(self.store_path)
        except FileNotFoundError:
            pass
        self.init_store()

    def save_store(self):
        """
            Override the dataset file with updated store
        """
        try:
            os.remove(self.store_path)
        except FileNotFoundError:
            pass
        self.store.to_csv(self.store_path, index=False)

    def get_embedding(self, path, model_dic=None):
        model_dic = model_dic if model_dic is not None else self.models

        out = {}
        for (model_name, model) in model_dic.items():
            temp = DeepFace.represent(img_path=path, model=model)
            # Check if NaN
            if np.isnan(temp).any():
                temp = float('nan')
            out[f'{model_name}_representation'] = temp
        return out

    def list_disk_images(self):
        # List images inside the dataset folder
        list_files = [f for f in os.listdir(self.path) if
                      os.path.isfile(os.path.join(self.path, f)) and f.endswith(".jpg") or f.endswith(".JPG")]
        return list_files

    def _build_store(self, list_images=None, model_names=None):
        list_images = list_images if list_images is not None else self.list_disk_images()
        model_dic = {name: self.models[name] for name in model_names} if model_names is not None else self.models

        df = pd.DataFrame()

        # Name
        for fname in list_images:
            logging.info(f"Building embedding for {fname}")
            # Get name and index
            face_name, _ = fname.rsplit("_", 1)
            # Embedding generation
            embedding_dic = self.get_embedding(os.path.join(self.path, fname), model_dic=model_dic)
            item = {'img_name': fname, 'face_name': face_name}
            item.update(embedding_dic)
            df = df.append(item, ignore_index=True)

        # Merge
        if len(df) > 0:
            self.store = self.store.set_index("img_name", drop=False).combine_first(
                df.set_index("img_name", drop=False))
