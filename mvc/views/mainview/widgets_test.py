from mvc.views.mainview.view_test import BaseTest
from mvc.views.mainview.widgets import FileExplorerWidget


class FileExplorerWidgetTest(BaseTest):
    def setUp(self) -> None:
        super(FileExplorerWidgetTest, self).setUp()
        self.widget = FileExplorerWidget()

    def tearDown(self) -> None:
        super(FileExplorerWidgetTest, self).tearDown()

    def test_set_dirpath(self):
        self.widget.set_dirpath(self.pics_folder)
        self.assertTrue(self.widget.fileModel.rowCount() > 0)
