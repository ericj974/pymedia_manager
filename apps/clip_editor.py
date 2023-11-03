import argparse
import logging
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

import resources.test_clips as test_clips
from mvc.controllers.main import MainController
from mvc.models.main import MainModel
from mvc.views.clip_editor.view import ClipEditorWindow

default_file = Path(test_clips.__file__).parent / 'woman-58142.mp4'

argparser = argparse.ArgumentParser(description='Display tile view for images inside the specified folder')
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

    if not path.is_file():
        logging.error("input path is does not exist or is not a file...exiting.")
        sys.exit()

    # MVC
    model = MainModel()
    controller = MainController(model=model)

    # App setup
    app = QApplication([sys.argv, '--no-sandbox'])
    app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
    window = ClipEditorWindow(controller=controller, model=model)
    window.show()

    # Set image path
    controller.set_media_path(path)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
