import logging
import shutil
import sys  # We need sys so that we can pass argv to QApplication
import os
import json

from PyQt5.QtWidgets import *

from controller import MainController
from views.mainview.view import MediaManagementView
from model import MainModel


__appname__ = 'MediaManager'


class MyApp(QApplication):
    def __init__(self, sys_argv, config):
        super(MyApp, self).__init__(sys_argv)
        self.model = MainModel()
        self.main_controller = MainController(self.model)
        self.main_view = MediaManagementView(self.model, self.main_controller, config)
        self.main_view.show()


def main():
    # Load config file
    config_dirpath = os.path.dirname(os.path.abspath(__file__))
    config_default_path = os.path.join(config_dirpath, "config_default.json")
    config_path = os.path.join(config_dirpath, "config.json")
    if not os.path.exists(config_path):
        logging.info("No config file found. Using default config file")
        src = config_default_path
        dst = config_path
        shutil.copy2(src=src, dst=dst)
    with open(config_path, "r") as f:
        config =  json.load(f)

    # Launch the UI
    app = MyApp(sys.argv, config= config)  # A new instance of QApplication
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
