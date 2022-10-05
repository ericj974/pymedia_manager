import argparse
import logging
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from controller import MainController
from model import MainModel
from views.tileview import MainTileWindow

argparser = argparse.ArgumentParser(description='Display tile view for images inside the specified folder')
argparser.add_argument('--dir',
                       help='Input directory containing the images with GPS metadata to display',
                       type=str,
                       default=os.path.dirname(os.path.abspath(test_pics.__file__)))

# logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, stream=sys.stdout)


def main():
    # Initialization
    args = argparser.parse_args()
    path = args.dir
    if not os.path.isdir(path):
        logging.error("input dirpath is does not exist or is not a directory...exiting.")
        sys.exit()

    # MVC
    model = MainModel()
    controller = MainController(model=model)

    # App setup
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
    window = MainTileWindow(controller=controller, model=model)
    window.show()

    # Set dirpath
    controller.update_dirpath(path)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
