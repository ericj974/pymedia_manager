import argparse
import logging
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

import resources.test_clips as test_clips
from clip_editor.view import ClipEditorWindow
from controller import MainController
from img_editor.view import PhotoEditorWindow
from model import MainModel

argparser = argparse.ArgumentParser(description='Display tile view for images inside the specified folder')
argparser.add_argument('--file',
                       help='Input file image',
                       type=str,
                       default=os.path.join(os.path.dirname(os.path.abspath(test_clips.__file__)), 'Poppy Field - 16453.mp4')
                       )

# logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, stream=sys.stdout)


def main():
    # Initialization
    args = argparser.parse_args()
    path = args.file
    if not os.path.isfile(path):
        logging.error("input path is does not exist or is not a file...exiting.")
        sys.exit()

    # MVC
    model = MainModel()
    controller = MainController(model=model)

    # App setup
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
    window = ClipEditorWindow(controller=controller, model=model)
    window.show()

    # Set image path
    controller.set_media_path(path)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
