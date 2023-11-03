import argparse
import logging
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from mvc.controllers.main import MainController
from mvc.models.main import MainModel
from mvc.views.tileview.view import MainTileWindow
from resources import test_pics

argparser = argparse.ArgumentParser(description='Display tile view for images inside the specified folder')
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
        logging.error("input dirpath is does not exist or is not a directory...exiting.")
        sys.exit()

    # MVC
    model = MainModel()
    controller = MainController(model=model)

    # App setup
    app = QApplication([sys.argv, '--no-sandbox'])
    app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
    window = MainTileWindow(controller=controller, model=model)
    window.show()

    # Set dirpath
    controller.update_dirpath(path)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
