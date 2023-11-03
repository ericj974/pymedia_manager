import json
import logging
import typing
from pathlib import Path

import cv2
import numpy as np

from common.comment import CommentEntity, ImageUserComment, TagEntity
from common.face import face_recognition_model
from common.singleton import Singleton

db_json_filename = 'dataset.json'
db_img_foldername = 'images'


class TagDBItem(TagEntity):
    def __init__(self, name: str):
        super(TagDBItem, self).__init__(name=name)


class TagDB(object):

    def __init__(self, dirpath: Path = None):

        # Database path containing embeddings
        if dirpath:
            assert dirpath.is_dir()

        self.dirpath = dirpath
        self.db_file: Path = dirpath / db_json_filename if dirpath else None

        # Database {name_lower_case: TagDBItem}
        self.db = {}

        if self.db_file:
            self.load_db()

    @property
    def tags(self):
        return list(set(self.db.values()))

    def load_db(self):
        if not self.db_file:
            return False

        # If no content, create empty json file
        if not self.db_file.is_file():
            logging.warning("Dataset folder is empty, creating new structure")
            self.save_db()
            return False

        # Opening JSON file
        with open(self.db_file, 'r') as f:
            _db = json.load(f)
            for k, v in _db.items():
                self.db[k] = TagDBItem.from_dict(v)

        return True

    def save_db(self):
        if not self.db_file:
            return

        # Getting the json
        _json = {k: v.to_dict() for k, v in self.db.items()}
        # Serializing json
        json_object = json.dumps(_json, indent=4)
        # Write to file
        with open(self.db_file, 'w') as f:
            f.write(json_object)

    def get_entry(self, name):
        return self.db.get(name.lower(), None)

    def add_to_db(self, tag: TagEntity):
        '''
        name: Name of the person
        '''
        assert tag.name != ''

        item = TagDBItem(name=tag.name)
        if item in self.db.values():
            return False

        self.db[item.lower()] = item

        # Save db
        self.save_db()

        return True


class FaceDetectionDBItem:
    def __init__(self, name, filename, location, embedding, model):
        self.name = name
        self.filename = filename
        self.location = location  # (top, right, bottom, left) as int
        self.embedding = embedding.tolist() if not isinstance(embedding, list) else embedding
        self.model = model
        self.hash = f"{name}_{filename}_{location}_{model}"

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


class FaceDetectionDB:

    def __init__(self, db_folder: Path):

        # Database path containing embeddings
        assert db_folder and db_folder.is_dir()
        self.json = db_folder / db_json_filename
        self.img_folder = db_folder / db_img_foldername

        # Database {hash: FaceDetectionDBItem}
        self.db: typing.Dict[str, FaceDetectionDBItem] = {}

        self.load_db()

    @property
    def known_face_names(self):
        return list(set([item.name for item in self.db.values()]))

    def known_face_filenames(self, name: str = None):
        if name:
            return list(set([item.filename for item in self.db.values() if item.name == name]))
        else:
            return list(set([item.filename for item in self.db.values()]))

    @property
    def known_face_embeddings(self):
        return [item.embedding for item in self.db.values()]

    def get_embeddings(self, model='face_recognition'):
        return ([np.array(item.embedding) for item in self.db.values() if model == item.model],
                [item.name for item in self.db.values() if model == item.model])

    def load_patch(self, file: Path):
        # Patch
        img = cv2.imread(str(file))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Location in comment
        user_comment: ImageUserComment = ImageUserComment.load_from_file(file)
        location = eval(user_comment.comment.data)
        return img, location

    def save_patch(self, file: Path, patch, location):
        # Patch
        cv2.imwrite(str(file), cv2.cvtColor(patch, cv2.COLOR_RGB2BGR))
        # Location in comment
        user_comment = ImageUserComment([CommentEntity(f"{location}")])
        user_comment.save_comment(file)

    def load_db(self):
        # If no content, create empty json file
        if not self.json.exists():
            # Make sure image dir does not exist
            assert not self.img_folder.exists()
            logging.warning("Dataset folder is empty, creating new structure")
            self.save_db()
            self.img_folder.mkdir(parents=False)
            return False

        # Opening JSON file
        with open(self.json, 'r') as f:
            _db = json.load(f)
            for v in _db.values():
                item = FaceDetectionDBItem.from_dict(v)
                self.db[item.hash] = item

        return True

    def save_db(self):
        # Getting the json
        _json = {k: v.to_dict() for k, v in self.db.items()}
        # Serializing json
        json_object = json.dumps(_json, indent=4)
        # Write to file
        with open(self.json, 'w') as f:
            f.write(json_object)

    def get_entry(self, name, filename, model):
        for item in self.db.values():
            if item.name == name and item.filename == filename and item.model == model:
                return item
        return None



    def add_to_db(self, name: str, patch, file: Path, model, embedding, location, overwrite=True):
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

        file_out = self.img_folder / name / file.name
        item = FaceDetectionDBItem(name=name, filename=file.name, location=location,
                                   embedding=embedding, model=model)

        # Check if a similar item has been detected.
        item_remove = None
        for it in self.db.values():
            if it.is_same_location(item) and it.model == item.model:
                item_remove = it
                break

        items_to_rename = []
        if item_remove:
            file_old = self.img_folder / item_remove.name / item_remove.filename
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
            file_old.unlink()
            if not any(file_old.parent.iterdir()):
                file_old.parent.rmdir()

        if not file_out.parent.exists():
            file_out.parent.mkdir(parents=False)

        self.save_patch(file=file_out, patch=patch, location=location)

        return True

    def remove_from_json(self, name: str, filenames: list[str]):
        '''
        Remove a filename from the db
        '''
        to_remove = [k for k, item in self.db.items() if item.name == name and item.filename in filenames]
        for k in to_remove:
            del self.db[k]

