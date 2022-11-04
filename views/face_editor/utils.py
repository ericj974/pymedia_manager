import json
import logging
import os

import cv2

from utils import Singleton


class FaceDetectionDB(metaclass=Singleton):

    def __init__(self, db_folder):

        # Database path containing embeddings
        assert os.path.exists(db_folder) and os.path.isdir(db_folder)
        self.db_file = os.path.join(db_folder, 'dataset.json')
        self.db_img_folder = os.path.join(db_folder, 'images')

        # Raw database
        self.db = {}
        # Re-structured params for face_detection
        # Create arrays of known face encodings and their names
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_filenames = []
        self.known_face_hashes = []

        self.load_db()

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
            self.db = json.load(f)

        for i in range(len(self.db)):
            v = self.db[str(i)]
            self.known_face_names.append(v['name'])
            self.known_face_encodings.append(v['encoding'])
            self.known_face_filenames.append(v['filename'])
            self.known_face_hashes.append(v['hash'])

        return True

    def save_db(self):
        # Serializing json
        json_object = json.dumps(self.db, indent=4)
        # Write to file
        with open(self.db_file, 'w') as f:
            f.write(json_object)

    def add_to_db(self, name, encoding, img, file):
        '''
        name: Name of the person
        encoding: The encoding
        img: The patch containing the face
        file: Original image file path from which the encoding was extracted
        '''
        assert name != '' and encoding is not None
        assert img is not None
        assert file is not None and file != ''

        filename, file_extension = os.path.splitext(os.path.basename(file))
        filename_out = os.path.join(name, os.path.basename(file))
        file_out = os.path.join(self.db_img_folder, filename_out)
        if filename_out in self.known_face_filenames:
            logging.warning('FaceDB: Duplicate entry with same filename. Skip saving...')
            return False

        index = str(len(self.db))
        item = self.create_item(name, encoding, filename_out)
        item_remove = None
        if item['hash'] in self.known_face_hashes:
            ind = self.known_face_hashes.index(item['hash'])
            # Update the name if different name
            if name == self.known_face_names[ind]:
                logging.warning('FaceDB: Duplicate entry with same hash. Skip saving...')
                return False
            else:
                index = str(ind)
                item_remove = self.db[index]
        # Check that not another item with the same hash
        self.db[index] = item
        if item_remove is not None:
            self.known_face_names[int(index)] = name
            self.known_face_encodings[int(index)] = encoding
            self.known_face_filenames[int(index)] = filename_out
            self.known_face_hashes[int(index)] = item['hash']
        else:
            self.known_face_names.append(name)
            self.known_face_encodings.append(encoding)
            self.known_face_filenames.append(filename_out)
            self.known_face_hashes.append(item['hash'])

        # Save db
        self.save_db()
        # Copy original image to images folder
        # Copy while (trying to) preserve metadata
        if not os.path.exists(os.path.dirname(file_out)):
            os.mkdir(os.path.dirname(file_out))
        cv2.imwrite(file_out, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        if item_remove is not None:
            file_old = os.path.join(self.db_img_folder, item_remove['filename'])
            os.remove(file_old)
            if len(os.listdir(os.path.dirname(file_old))) == 0:
                os.rmdir(os.path.dirname(file_old))
        return True

    @staticmethod
    def create_item(name, encoding, filename, enc_hash=None):
        enc_hash = enc_hash if enc_hash else str(hash(encoding.tobytes()))
        return {
            'filename': filename,
            'encoding': encoding.tolist(),
            'name': name,
            'hash': enc_hash
        }
