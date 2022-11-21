import argparse
import json
import logging
import os
import sys

import cv2

from utils import load_image, QImageToCvMat, image_resize
from views.face_editor.db import FaceDetectionDB, db_json_filename, db_img_foldername
from views.face_editor.utils import face_recognition_model, face_encodings

argparser = argparse.ArgumentParser(description='Rebuild database')
argparser.add_argument('--dir',
                       help='Input dataset directory',
                       type=str)

# logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, stream=sys.stdout)


class FaceDetectionDBConverter(object):

    def __init__(self, db_folder):

        self.db_file = os.path.join(db_folder, db_json_filename)
        self.db_img_folder = os.path.join(db_folder, db_img_foldername)

        if os.path.exists(self.db_file):
            os.remove(self.db_file)

        # Serializing json
        json_object = json.dumps({}, indent=4)
        # Write to file
        with open(self.db_file, 'w') as f:
            f.write(json_object)

        self.face_db = FaceDetectionDB(db_folder)

    def rebuild(self):
        self.rebuild_names()
        self.rebuild_encodings()

    def rebuild_names(self):
        names = os.listdir(self.db_img_folder)
        for name in names:
            filenames = os.listdir(os.path.join(self.db_img_folder, name))
            for filename in filenames:
                file = os.path.join(self.db_img_folder, name, filename)
                img = cv2.imread(file)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # Add an entry without encodings
                self.face_db.add_to_db(name=name,
                                       img=img,
                                       file=file)

    def rebuild_encodings(self):
        db = self.face_db.db
        for model in face_recognition_model:
            logging.info(f"Creating embedding for model {model}")
            for i in range(len(db)):
                v = db[str(i)]
                embeddings = v.embeddings
                if model in embeddings:
                    continue
                logging.info(f"Updating embeddings for {v.name} with model {model}")
                # Read file
                file = os.path.join(self.face_db.db_img_folder, v.name, v.filename)
                qimage, _ = load_image(file)
                frame = QImageToCvMat(qimage)

                # Representation
                embedding = face_encodings(imgs=[frame], model_name=model)[0]

                # Add to db
                self.face_db.update_embedding_entry(name=v.name, embedding=embedding,
                                                    filename=v.filename, model=model)


def main():
    # Initialization
    args = argparser.parse_args()
    dir_path = args.dir
    if not os.path.isdir(dir_path):
        logging.error("input path does not exist or is not a folder...exiting.")
        sys.exit()
    converter = FaceDetectionDBConverter(db_folder=dir_path)
    converter.rebuild()


if __name__ == '__main__':
    main()
