from abc import abstractmethod

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog

from mvc.views.clip_editor.action_params import ClipActionParams


class ClipActionDialog(QDialog):
    # Change of directory path
    window_closing = pyqtSignal()

    def __init__(self, parent, params: ClipActionParams):
        super(ClipActionDialog, self).__init__(parent)
        self.params = params if params else ClipActionParams()
        self.action_close_listener = None

    @abstractmethod
    def update_params(self) -> None:
        """
        Update the params based on GUI element values.
        This is usually called before closing the dialog
        """
        pass

    @abstractmethod
    def get_params(self) -> ClipActionParams:
        """
        :return: The parameters of the current node
        """
        self.update_params()
        return self.params

    def validate(self) -> None:
        """
        This function is called before closing the GUI
        """
        self.update_params()
        if self.action_close_listener:
            self.action_close_listener(self.get_params())
        self.close()
        self.destroy()

    def closeEvent(self, event):
        self.window_closing.emit()
        super(ClipActionDialog, self).closeEvent(event)
