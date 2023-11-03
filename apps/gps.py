import argparse
import logging
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

import resources.test_pics as test_pics
from mvc.controllers.main import MainController
from mvc.models.main import MainModel
from mvc.views.gps.view import MainGPSWindow

argparser = argparse.ArgumentParser(description='Display GPS location of images inside the specified folder')
argparser.add_argument('--dir',
                       help='Input directory containing the images with GPS metadata to display',
                       type=str,
                       default=None)

# logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, stream=sys.stdout)


def main():
    # Initialization
    args = argparser.parse_args()
    path = Path(args.dir) if args.dir else Path(test_pics.__file__).parent
    if not path.is_dir():
        logging.error("Dirpath is does not exist or is not a directory...exiting.")
        sys.exit()

    # MVC
    model = MainModel()
    controller = MainController(model=model)

    # App setup
    # https://stackoverflow.com/questions/72131093/pyqt5-qwebengineview-doesnt-load-url
    app = QApplication([sys.argv, '--no-sandbox'])
    app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
    window = MainGPSWindow(model=model, controller=controller)
    window.show()

    # Set dirpath
    controller.update_dirpath(path)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
