import argparse
import logging
import os
import sys

from PyQt5.QtWidgets import QApplication

from views import renamer
from controller import MainController
from model import MainModel
from views.renamer.view import MainRenamerWindow
# Parse the basic argument first
from resources import test_pics

parser = argparse.ArgumentParser(description='Rename app for pictures and videos based on exif')

parser.add_argument('--create_backup', default=True, type=bool,
                    help='do we backup the pictures before renaming')

parser.add_argument('--delete_duplicate', default=False, type=bool,
                    help='do we delete duplicate file after renaming with the same name')

parser.add_argument('--dir',
                       help='Input directory containing the images / videos to rename',
                       type=str,
                       default=os.path.dirname(os.path.abspath(test_pics.__file__)))

# logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, stream=sys.stdout)


def main():
    # Initialization
    args = parser.parse_args()

    # Load the different parsers in a plugin way.
    from views.renamer import parsers
    parsers.load_plugins(parent_module_name='renamer.parsers')
    repo_parsers = parsers.REPO_PARSERS
    # Finally load the renamer
    renamer.load_plugins(parent_module_name='renamer')
    repo_renamers = renamer.REPO_RENAMERS
    # Build the generic renamer when tere is no specific renamer associated with the tag
    for tag, parsers in repo_parsers.items():
        # if for such tag there is a specific renamer, then ok
        if tag in repo_renamers: continue

    # MVC
    model = MainModel()
    controller = MainController(model=model)

    # App setup
    app = QApplication(sys.argv)
    window = MainRenamerWindow(model=model, controller=controller)
    window.create_backup = args.create_backup
    window.delete_duplicate = args.delete_duplicate
    window.show()  # Show the form

    # If provided, set dirpath
    path = args.dir
    if os.path.isdir(path):
        # Set dirpath
        controller.update_dirpath(path)
    else:
        logging.warning("input dirpath is does not exist or is not a directory...")
        sys.exit()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
