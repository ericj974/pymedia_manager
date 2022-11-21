import json
import logging
import os

import cv2
import numpy as np

from utils import Singleton

db_json_filename = 'dataset.json'
db_img_foldername = 'images'


class FaceDetectionDBItem:
    def __init__(self, name, filename):
        self.name = name
        self.filename = filename
        self.embeddings = {}

    def to_dict(self):
        return {
            'filename': self.filename,
            'embeddings': self.embeddings,
            'name': self.name,
        }

    def get_models(self):
        return self.embeddings.keys()

    def get_embedding(self, model):
        return self.embeddings.get(model, {}).get('embedding', None)

    def get_hash(self, model):
        return self.embeddings.get(model, {}).get('hash', None)

    def set_embedding(self, model, embedding):
        _dic = {
            'lib': 'face_recognition' if model == 'face_recognition' else 'deepface',
            'embedding': embedding if isinstance(embedding, list) else embedding.tolist(),
            'hash': str(hash(embedding.tobytes())) if not isinstance(embedding, list) else str(
                hash(np.array(embedding).tobytes()))
        }
        self.embeddings[model] = _dic

    @staticmethod
    def create(name, filename, model='', embedding=None):
        item = FaceDetectionDBItem(name=name, filename=filename)
        if model != '' and embedding is not None:
            item.set_embedding(model=model, embedding=embedding)
        return item

    @staticmethod
    def from_dict(dic):
        item = FaceDetectionDBItem.create(name=dic['name'], filename=dic['filename'])
        for model, value in dic['embeddings'].items():
            item.set_embedding(model=model, embedding=value['embedding'])
        return item


class FaceDetectionDB(metaclass=Singleton):

    def __init__(self, db_folder):

        # Database path containing embeddings
        assert os.path.exists(db_folder) and os.path.isdir(db_folder)
        self.db_file = os.path.join(db_folder, db_json_filename)
        self.db_img_folder = os.path.join(db_folder, db_img_foldername)

        # Database
        self.db = {}

        self.load_db()

    @property
    def known_face_names(self):
        return [item.name for item in self.db.values()]

    @property
    def known_face_filenames(self):
        return [item.filename for item in self.db.values()]

    @property
    def known_face_embeddings(self):
        return [item.embeddings for item in self.db.values()]

    def get_embeddings(self, model='face_recognition'):
        return [item.get_embedding(model) for item in self.db.values()]

    def load_db(self):
        # If no content, create empty json file
        if not os.path.exists(self.db_file):
            # Make sure image dir does not exist
            assert not os.path.exists(self.db_img_folder)
            logging.warning("Dataset folder is empty, creating new structure")
            self.save_db()
            os.mkdir(os.path.join(self.db_img_folder))
            return False

        # Opening JSON file
        with open(self.db_file, 'r') as f:
            _db = json.load(f)
            for k, v in _db.items():
                self.db[k] = FaceDetectionDBItem.from_dict(v)

        return True

    def save_db(self):
        # Getting the json
        _json = {k: v.to_dict() for k, v in self.db.items()}
        # Serializing json
        json_object = json.dumps(_json, indent=4)
        # Write to file
        with open(self.db_file, 'w') as f:
            f.write(json_object)

    def get_entry(self, name, filename):
        uids = [os.path.join(item.name, item.filename) for item in self.db.values()]
        uid = os.path.join(name, filename)
        try:
            ind = uids.index(uid)
            return self.db[str(ind)]
        except:
            return None

    def update_embedding_entry(self, name, filename, model, embedding):
        uids = [os.path.join(item.name, item.filename) for item in self.db.values()]
        uid = os.path.join(name, filename)
        assert uid in uids, "Name + Filename not found in DB"

        ind = uids.index(uid)
        item = self.db[str(ind)]
        item.set_embedding(model=model, embedding=embedding)

        # Save db
        self.save_db()

    def add_to_db(self, name, img, file, model='', encoding=None):
        '''
        name: Name of the person
        encoding: The encoding
        img: The patch containing the face
        file: Original image file path from which the encoding was extracted
        '''
        assert name != ''
        assert img is not None
        assert file is not None and file != ''

        filename_out = os.path.basename(file)
        file_out = os.path.join(self.db_img_folder, name, filename_out)

        index = str(len(self.db))
        item = self.create_item(name=name, encoding=encoding, filename=filename_out, model=model)
        item_remove = None

        # We simply updated the name, or the filename here
        known_face_hashes = [item.get_hash(model) for item in self.db.values() if
                             model in item.get_models()]

        item_hash = item.get_hash(model=model)
        if item_hash is not None and item_hash in known_face_hashes:
            ind = known_face_hashes.index(item_hash)
            # Update the name if different name
            if name == self.known_face_names[ind]:
                logging.warning('FaceDB: Duplicate entry with same hash. Skip saving...')
                return False
            else:
                index = str(ind)
                item_remove = self.db[index]

        self.db[index] = item

        # Save db
        self.save_db()

        # Delete old img
        if item_remove is not None:
            file_old = os.path.join(self.db_img_folder, item_remove.filename)
            os.remove(file_old)
            if len(os.listdir(os.path.dirname(file_old))) == 0:
                os.rmdir(os.path.dirname(file_old))

        # Copy original image to images folder
        if not os.path.exists(os.path.dirname(file_out)):
            os.mkdir(os.path.dirname(file_out))
        cv2.imwrite(file_out, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

        return True

    @staticmethod
    def create_item(name, filename, model='', encoding=None):
        return FaceDetectionDBItem.create(name=name, filename=filename, model=model, embedding=encoding)
