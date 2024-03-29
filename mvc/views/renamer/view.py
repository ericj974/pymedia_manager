import logging
from functools import partial
from pathlib import Path

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QTableWidgetItem

from common.constants import FILE_EXTENSION_PHOTO_JPG, FILE_EXTENSION_PHOTO_HEIF, FILE_EXTENSION_VIDEO
from mvc.controllers.main import MainController
from mvc.models.main import MainModel
from mvc.views import renamer
from mvc.views.renamer import gui as renamer_ui
from mvc.views.renamer.common import nameddic
from mvc.views.renamer.parsers import load_plugins, REPO_PARSERS

file_extensions_per_tag = {
    'photo_heic': FILE_EXTENSION_PHOTO_HEIF,
    'photo': FILE_EXTENSION_PHOTO_JPG,
    'video': FILE_EXTENSION_VIDEO
}


class MainRenamerWindow(QMainWindow, renamer_ui.Ui_MainWindow):
    def __init__(self, model: MainModel, controller: MainController, config: dict = None):
        super(self.__class__, self).__init__()

        # MVC
        self._model = model
        self._controller = controller
        self._controller.set_parent(self)

        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        # connect widgets to controller
        self.__class__.dropEvent = self.on_drop_media  # self._controller.update_dirpath

        # listen for model event signals
        self._model.selected_dir_changed.connect(self.on_dirpath_changed)
        self._model.selected_dir_content_changed.connect(self.on_dir_content_changed)

        # Load the different parsers in a plugin way.
        load_plugins(parent_module_name='mvc.views.renamer.parsers')
        repo_parsers = REPO_PARSERS
        # Finally load the renamer
        renamer.load_plugins(parent_module_name='mvc.views.renamer')
        repo_renamers = renamer.REPO_RENAMERS
        # Build the generic renamer when tere is no specific renamer associated with the tag
        for tag, parsers in repo_parsers.items():
            # if for such tag there is a specific renamer, then ok
            if tag in repo_renamers: continue
        # Parsers repo in dic format: tag -> list_of_parsers
        self.repo_parsers = repo_parsers
        # Renamers repo in dic format: tag -> list of renamers
        self.repo_renamers = repo_renamers

        # Need to keep track of the filter checkboxes
        # TODO: Modify this to be dynamic
        self.checkbox_list = [self.checkBox_all]
        for i, checkbox in enumerate(self.checkbox_list):
            checkbox.setVisible(False)
            checkbox.clicked.connect(partial(self.checked_i, i))
        self.checkBox_all.setVisible(False)
        self.checkBox_all.clicked.connect(self.checked_all)

        # Table part
        self.table_result.doubleClicked.connect(self.on_table_double_clicked)

        # update exif button
        self.options = nameddic()
        self.checkBox_exif.clicked.connect(self.checked_exif)

        # Create backup of the image before renaming ?
        self.create_backup = config["CREATE_BACKUP"] if config else False
        self.backup_foldername = config["BACKUP_FOLDERNAME"] if config else '.backup'

        # Do we create duplicate if destination name exists ?
        self.delete_duplicate = config["DELETE_DUPLICATE"] if config else True

        # Current directory
        self.label_dirpath.setText(str(self._model.dirpath))

        # The dictionary containing the list of results
        self.results = renamer.ResultsRenaming()
        self.renamer = None

        # Connect the different buttons
        self.pushButton_openFolder.clicked.connect(self.openDir)
        self.pushButton_applyName.clicked.connect(self.rename_list)

        # Connect the drop
        self.__class__.dragEnterEvent = self.dragEnterEvent
        self.__class__.dragMoveEvent = self.dragEnterEvent
        self.setAcceptDrops(True)

        # Connect the tag combobox
        self.comboBox_tags.addItems([tag for tag in self.repo_renamers.keys()])
        self.comboBox_tags.currentIndexChanged.connect(self.create_new_renamer)

    @pyqtSlot(Path)
    def on_dirpath_changed(self, dirpath):
        # set the dir
        self.set_dirpath(dirpath)
        # check the all by default
        self.checkBox_all.setChecked(True)
        self.checked_all()

    def create_new_renamer(self, event):
        path = Path(self.label_dirpath.text())
        self.set_dirpath(path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def openDir(self):

        dirpath = QFileDialog.getExistingDirectory(parent=self,
                                                   caption='%s - Open Directory',
                                                   directory=str(self._model.dirpath),
                                                   options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)

        # Check that one folder was actually selected
        if dirpath is None or len(dirpath) <= 1:
            return
        else:
            dirpath = Path(dirpath)

        # set the dir
        self.set_dirpath(dirpath)
        # check the all by default
        self.checkBox_all.setChecked(True)
        self.checked_all()

    def checked_exif(self):
        is_checked = self.checkBox_exif.isChecked()
        self.options.update_exif = is_checked

    def checked_all(self):
        is_checked = self.checkBox_all.isChecked()
        for i, checkbox in enumerate(self.checkbox_list):
            checkbox.setChecked(is_checked)
        if (is_checked):
            self.show_results(self.results)
        else:
            self.show_results(None)

    def checked_i(self, ind):
        # If all is check, we remove only uncheck related items
        # If all is unchecked, we add only checked items
        if self.checkBox_all.isChecked():
            status_list_unchecked = [checkbox.text() for checkbox in self.checkbox_list if not checkbox.isChecked()]
            status_list = [status for status in self.results.get_status_list() if status not in status_list_unchecked]
            self.show_results(results=self.results.get_dic_from_status(status_list))
        else:
            status_list_checked = [checkbox.text() for checkbox in self.checkbox_list if checkbox.isChecked()]
            status_list = [status for status in self.results.get_status_list() if status in status_list_checked]
            self.show_results(results=self.results.get_dic_from_status(status_list))

    def show_checkboxes(self):

        self.checkBox_all.setVisible(True)
        # Update the filters widget (display or not the checkboxes)
        # 1st we need to see which status can create an output different from ''
        status_list = []
        for i, result in enumerate(self.results.values()):
            if (result.filename_dst != result.filename_src) and \
                    (result.filename_dst != '') and \
                    (result.status not in status_list):
                status_list.append(result.status)

        # 2nd update the widget and activate the filters "all"
        # for checkbox in self.checkbox_list:
        #     checkbox.setVisible(False)
        # for i, status in enumerate(status_list):
        #     self.checkbox_list[i].setVisible(True)
        #     self.checkbox_list[i].setText(status)

        # Trigger a check all since we want to show every item
        self.checked_all()

    # Set the results and display them
    def show_results(self, results):
        # Clear the table of results
        self.table_result.setRowCount(0)
        # Set row and col counts
        if (results is None) or (len(results.values()) == 0):
            return
        self.table_result.setRowCount(len(results))
        self.table_result.setColumnCount(3)

        # Populate the table
        for i, (filename_in, result) in enumerate(results.items()):
            item = QTableWidgetItem(filename_in)
            self.table_result.setItem(i, 0, item)
            item = QTableWidgetItem(result.filename_dst)
            self.table_result.setItem(i, 1, item)
            item = QTableWidgetItem(result.status)
            self.table_result.setItem(i, 2, item)

    # Set the dir path
    def set_dirpath(self, dirpath: Path):
        self.label_dirpath.setText(str(dirpath))
        # List the files
        # TODO: GENERALIZE THIS to more than only photo renamer
        # get the selected tag
        tag = self.comboBox_tags.currentText()
        renamer_generator = self.repo_renamers[tag][0]

        logging.info('Listing Files...')
        config = nameddic()
        config.parser = nameddic()
        config.parser.parser_cls_list = self.repo_parsers[tag]

        renamer = renamer_generator.generate_renamer(config=config,
                                                     file_extensions=file_extensions_per_tag[tag])
        results_parsing = renamer.try_parse_build_filename(folderpath_or_list_files=dirpath)

        self.results = results_parsing
        self.renamer = renamer
        # Show the results
        self.show_results(results_parsing)
        # Show the checkboxes
        self.show_checkboxes()

    def on_dir_content_changed(self):
        self.set_dirpath(self._model.dirpath)

    def on_table_double_clicked(self, index):
        row = index.row()
        filename = self.table_result.item(row, 0).data(0)
        file = self._model.dirpath / filename
        self._controller.set_media_path(file)

    def on_drop_media(self, item):
        self._controller.update_dirpath(item)

    # Change the name
    def rename_list(self):
        logging.info('RENAMING')
        # We only rename file that are visible in the table AND
        # for which there is an output filename
        out = {}
        for i in range(self.table_result.rowCount()):

            filename_out = QTableWidgetItem(self.table_result.item(i, 1)).text()
            if filename_out:
                filename_in = QTableWidgetItem(self.table_result.item(i, 0)).text()
                out[filename_in] = self.results[filename_in]
        # Rename
        self.renamer.rename_all(results_to_rename=out,
                                create_backup=self.create_backup,
                                backup_foldername=self.backup_foldername,
                                delete_duplicate=self.delete_duplicate,
                                options=self.options)
        # Update the GUI
        self.set_dirpath(self._model.dirpath)
