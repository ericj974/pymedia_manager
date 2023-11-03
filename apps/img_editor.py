import argparse
import logging
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

import resources.test_db_faces as test_db_faces
import resources.test_db_tags as test_db_tags
import resources.test_pics as test_pics
from common.db import FaceDetectionDB, TagDB
from mvc.controllers.face import FaceDetectionController
from mvc.controllers.main import MainController
from mvc.models.face import FaceDetectionModel
from mvc.models.main import MainModel
from mvc.views.img_editor.view import PhotoEditorWindow

default_db_faces_folder = Path(test_db_faces.__file__).parent
default_db_tags_folder = Path(test_db_tags.__file__).parent
default_file = Path(test_pics.__file__).parent / 'lenna.jpg'

argparser = argparse.ArgumentParser(description='Display tile view for images inside the specified folder')
argparser.add_argument('--db_faces',
                       help='Input Faces database folder path',
                       type=str,
                       default=None)

argparser.add_argument('--db_tags',
                       help='Input Tags database folder path',
                       type=str,
                       default=None)

argparser.add_argument('--file',
                       help='Input file image',
                       type=str,
                       default=None)

# logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, stream=sys.stdout)


def main():
    # Initialization
    args = argparser.parse_args()
    path = Path(args.file) if args.file else default_file
    db_faces_path = Path(args.db_faces) if args.db_faces else default_db_faces_folder
    db_tags_path = Path(args.db_tags) if args.db_tags else default_db_tags_folder

    if not path.is_file():
        logging.error("input path is does not exist or is not a file...exiting.")
        sys.exit()

    # MVC
    db = TagDB(db_tags_path)
    model = MainModel(db_tags=db)
    controller = MainController(model=model)

    # MVC Local
    db = FaceDetectionDB(db_faces_path)
    model_local = FaceDetectionModel(db=db)
    controller_local = FaceDetectionController(model=model_local)

    # App setup
    app = QApplication([sys.argv, '--no-sandbox'])
    app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
    window = PhotoEditorWindow(controller=controller, model=model,
                               controller_local=controller_local, model_local=model_local)
    window.show()

    # Set image path
    controller.set_media_path(path)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
