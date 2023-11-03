import argparse
import json
import logging
from pathlib import Path
import sys  # We need sys so that we can pass argv to QApplication

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

import resources.test_db_tags as test_db_tags
from mvc.controllers.main import MainController
from mvc.models.main import MainModel
from common.db import TagDB
from mvc.views.mainview.view import MediaManagementView

default_db_tags_folder = Path(test_db_tags.__file__).parent

__appname__ = 'MediaManager'

argparser = argparse.ArgumentParser(description='Main App for media management')

argparser.add_argument('--db_tags',
                       help='Optional, Input Tags database folder path. '
                            'If specified, the path will override the one specified in config.json',
                       type=str,
                       default=None)

# logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, stream=sys.stdout)


def main():
    # Initialization
    args = argparser.parse_args()

    # Load config file
    config_path = Path(__file__).parent / "config.json"
    assert config_path.is_file(), "No config file found or is not a file. Config file must be created first !"
    with open(config_path, "r") as f:
        config = json.load(f)

    # MVC
    db_tags_path = Path(args.db_tags) if args.db_tags else Path(config['DB_TAGS_FOLDER'])
    db_tags = TagDB(dirpath=db_tags_path)
    model = MainModel(db_tags=db_tags)
    main_controller = MainController(model)

    # App setup
    # https://stackoverflow.com/questions/72131093/pyqt5-qwebengineview-doesnt-load-url
    app = QApplication([sys.argv, '--no-sandbox'])
    app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
    window = MediaManagementView(model, main_controller, config)
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
