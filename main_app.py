import sys  # We need sys so that we can pass argv to QApplication

from PyQt5.QtWidgets import *

from controller import MainController
from views.mainview.view import MediaManagementView
from model import MainModel

__appname__ = 'MediaManager'


class MyApp(QApplication):
    def __init__(self, sys_argv):
        super(MyApp, self).__init__(sys_argv)
        self.model = MainModel()
        self.main_controller = MainController(self.model)
        self.main_view = MediaManagementView(self.model, self.main_controller)
        self.main_view.show()


def main():
    # Launch the UI
    app = MyApp(sys.argv)  # A new instance of QApplication
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
