import logging
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from controller import MainController
from model import MainModel
from tileview.view import MainTileWindow


def main(argv=[]):
    logging.basicConfig(level=logging.DEBUG)

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
    model = MainModel()
    controller = MainController(model=model)
    window = MainTileWindow(controller=controller, model=model)
    window.set_dirpath('/home/ericj/Pictures/test/')
    model.imagepath = '/home/ericj/Pictures/test/20210908_122743.jpg'
    window.show()
    app.exec_()


if __name__ == '__main__':
    sys.exit(main(sys.argv))  # run the main function
