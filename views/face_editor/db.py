import json
import logging
import os

import cv2

from utils import Singleton

db_json_filename = 'dataset.json'
db_img_foldername = 'images'

class FaceDetectionDB(metaclass=Singleton):

    def __init__(self, db_folder):

        # Database path containing embeddings
        assert os.path.exists(db_folder) and os.path.isdir(db_folder)
        self.db_file = os.path.join(db_folder, db_json_filename)
        self.db_img_folder = os.path.join(db_folder, db_img_foldername)

        # Raw database
        self.db = {}
        # Re-structured params for face_detection
        # Create arrays of known face encodings and their names
        self.known_face_embeddings = []
        self.known_face_names = []
        self.known_face_filenames = []

        self.load_db()

    def get_embeddings(self, model='face_recognition'):
        return [v['embeddings'][f'{model}']['embedding'] for v in self.db.values()]

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
            self.known_face_filenames.append(v['filename'])
            self.known_face_embeddings.append(v['embeddings'])

        return True

    def save_db(self):
        # Serializing json
        json_object = json.dumps(self.db, indent=4)
        # Write to file
        with open(self.db_file, 'w') as f:
            f.write(json_object)

    def get_entry(self, name, filename):
        uids = [os.path.join(v['name'], v['filename']) for v in self.db.values()]
        uid = os.path.join(name, filename)
        try:
            ind = uids.index(uid)
            return self.db[str(ind)]
        except:
            return None

    def update_embedding_entry(self, name, filename, model, embedding):
        uids = [os.path.join(v['name'], v['filename']) for v in self.db.values()]
        uid = os.path.join(name, filename)
        assert uid in uids, "Name + Filename not found in DB"

        ind = uids.index(uid)
        item = self.db[str(ind)]
        if model in item['embeddings']:
            # Update embedding
            item['embeddings'][model]['embedding'] = embedding
        else:
            new_item = self.create_item(name=name, encoding=embedding, filename=filename, enc_hash=None, model=model)
            item['embeddings'][model] = new_item['embeddings'][model]

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
        known_face_hashes = [v['embeddings'][f'{model}']['hash'] for v in self.db.values() if
                             f'{model}' in v['embeddings']]

        hash = item['embeddings'].get(model, {}).get('hash', None)
        if hash is not None and hash in known_face_hashes:
            ind = known_face_hashes.index(item['hash'])
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
            self.known_face_filenames[int(index)] = filename_out

            embeddings = self.known_face_embeddings[int(index)]
            embeddings[f'{model}'] = item['embeddings'][f'{model}']
            self.known_face_embeddings[int(index)] = embeddings
        else:
            self.known_face_names.append(name)
            self.known_face_filenames.append(filename_out)
            self.known_face_embeddings.append(item['embeddings'])

        # Save db
        self.save_db()

        # Delete old img
        if item_remove is not None:
            file_old = os.path.join(self.db_img_folder, item_remove['filename'])
            os.remove(file_old)
            if len(os.listdir(os.path.dirname(file_old))) == 0:
                os.rmdir(os.path.dirname(file_old))

        # Copy original image to images folder
        if not os.path.exists(os.path.dirname(file_out)):
            os.mkdir(os.path.dirname(file_out))
        cv2.imwrite(file_out, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

        return True

    @staticmethod
    def create_item(name, filename, model='', encoding=None, enc_hash=None):
        embeddings_dic = {}
        if model != '' and encoding is not None:
            enc_hash = enc_hash if enc_hash else str(hash(encoding.tobytes()))
            embeddings_dic[model] = {
                'lib': 'face_recognition' if model == 'face_recognition' else 'deepface',
                'embedding': encoding.tolist(),
                'hash': enc_hash
            }
        return {
            'filename': filename,
            'embeddings': embeddings_dic,
            'name': name,
        }
