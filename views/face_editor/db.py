import json
import logging
import os

import cv2
import numpy as np

from utils import Singleton, load_image, get_exif_user_comment, ImageUserComment
from views.face_editor.utils import face_recognition_model

db_json_filename = 'dataset.json'
db_img_foldername = 'images'


class FaceDetectionDBItem:
    def __init__(self, name, filename, location, embedding, model):
        self.name = name
        self.filename = filename
        self.location = location # (top, right, bottom, left) as int
        self.embedding = embedding.tolist() if not isinstance(embedding, list) else embedding
        self.model = model
        self.hash = f"{filename}_{location}_{model}"

    def to_dict(self):
        return {
            'filename': self.filename,
            'embedding': self.embedding,
            'location': f"{self.location}",
            'name': self.name,
            'model': self.model
        }


    @staticmethod
    def from_dict(dic):
        item = FaceDetectionDBItem(name=dic['name'], filename=dic['filename'], location=eval(dic['location']),
                                   model=dic['model'], embedding=dic['embedding'])
        return item

    def is_same_location(self, other):
        if self.filename != other.filename:
            return False

        threshold = 0.9
        boxA = self.location[3], self.location[0], self.location[2], self.location[1]
        boxB = other.location[3], other.location[0], other.location[2], other.location[1]

        # determine the (x, y)-coordinates of the intersection rectangle
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        # compute the area of intersection rectangle
        interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
        # compute the area of both the prediction and ground-truth
        # rectangles
        boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
        boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
        # compute the intersection over union by taking the intersection
        # area and dividing it by the sum of prediction + ground-truth
        # areas - the interesection area
        iou = interArea / float(boxAArea + boxBArea - interArea)
        # return the intersection over union value
        return iou > threshold


class FaceDetectionDB(metaclass=Singleton):

    def __init__(self, db_folder):

        # Database path containing embeddings
        assert os.path.exists(db_folder) and os.path.isdir(db_folder)
        self.db_file = os.path.join(db_folder, db_json_filename)
        self.db_img_folder = os.path.join(db_folder, db_img_foldername)

        # Database {hash: FaceDetectionDBItem}
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
        return [item.embedding for item in self.db.values()]

    def get_embeddings(self, model='face_recognition'):
        return ([np.array(item.embedding) for item in self.db.values() if model == item.model],
        [item.name for item in self.db.values() if model == item.model])

    def load_patch(self, file):
        # Patch
        img = cv2.imread(file)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Location in comment
        user_comment = ImageUserComment.load_from_file(file)
        location = eval(user_comment.comments)
        return img, location

    def save_patch(self, file, patch, location):
        # Patch
        cv2.imwrite(file, cv2.cvtColor(patch, cv2.COLOR_RGB2BGR))
        # Location in comment
        user_comment = ImageUserComment.create_item(comments=f"{location}")
        user_comment.save_comment(file)


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

    def get_entry(self, name, filename, model):
        for item in self.db.values():
            if item.name == name and item.filename == filename and item.model == model:
                return item
        return None

    def add_to_db(self, name, patch, file, model, embedding, location, overwrite=True):
        '''
        name: Name of the person
        encoding: The encoding
        img: The patch containing the face
        file: Original image file path from which the encoding was extracted
        '''
        assert name != ''
        assert patch is not None
        assert file is not None and file != ''
        assert model is not None and model in face_recognition_model
        assert embedding is not None


        filename_out = os.path.basename(file)
        file_out = os.path.join(self.db_img_folder, name, filename_out)
        item = FaceDetectionDBItem(name=name, filename=filename_out, location=location,
                                   embedding=embedding, model=model)

        # Check if a similar item has been detected.
        item_remove = None
        for it in self.db.values():
            if it.is_same_location(item) and it.model == item.model:
                item_remove = it
                break

        items_to_rename = []
        if item_remove:
            file_old = os.path.join(self.db_img_folder, item_remove.name, item_remove.filename)
            if not overwrite:
                logging.warning('FaceDB: Duplicate entry with same hash. Skip saving...')
                return False
            else:
                logging.warning('FaceDB: Duplicate entry with same hash. Overwriting...')
                # Update all db entries with same filename and name as item_remove (but diff model)
                # except if item_remove.name is same as item.name
                if item_remove.name != item.name:
                    items_to_rename = [it for it in self.db.values() if
                                       (it.filename == item_remove.filename) and (it.name == item_remove.name)]

        self.db[item.hash] = item
        # Rename items
        for it in items_to_rename:
            it.name = item.name

        # Save db
        self.save_db()

        # Delete old img and Copy original image to images folder, irrespective of
        # whether the item_remove patch was the same or not
        if item_remove:
            os.remove(file_old)
            if len(os.listdir(os.path.dirname(file_old))) == 0:
                os.rmdir(os.path.dirname(file_old))

        if not os.path.exists(os.path.dirname(file_out)):
            os.mkdir(os.path.dirname(file_out))
        self.save_patch(file=file_out, patch=patch, location=location)

        return True
