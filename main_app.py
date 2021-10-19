import sys  # We need sys so that we can pass argv to QApplication

from PyQt5.QtWidgets import *

from controller import MainController
from mainview.view import PhotoManagementView
from model import MainModel

__appname__ = 'PhotoManagement'


class MyApp(QApplication):
    def __init__(self, sys_argv):
        super(MyApp, self).__init__(sys_argv)
        self.model = MainModel()
        self.main_controller = MainController(self.model)
        self.main_view = PhotoManagementView(self.model, self.main_controller)
        self.main_view.show()


def main(argv=[]):
    # Launch the UI
    app = MyApp(sys.argv)  # A new instance of QApplication
    app.exec_()


if __name__ == '__main__':  # if we're running file directly and not importing it
    sys.exit(main(sys.argv))  # run the main function
