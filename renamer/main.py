import argparse
import sys

from PyQt5.QtWidgets import QApplication

import renamer
from controller import MainController
from model import MainModel
from renamer.view import MainRenamerWindow


def main(argv=[]):
    # Parse the basic argument first
    parser = argparse.ArgumentParser()
    # options: 'mt', 'mt_mocked', 'mt_sandbox' or 'normal'
    parser.add_argument('--create_backup', default=True, type=bool,
                        help='do we backup the pictures before renaming')
    parser.add_argument('--delete_duplicate', default=False, type=bool,
                        help='do we delete duplicate file after renaming with the same name')

    args = parser.parse_args()

    # Load the different parsers in a plugin way.
    from renamer import parsers
    parsers.load_plugins(parent_module_name='renamer.parsers')
    repo_parsers = parsers.REPO_PARSERS
    # Finally load the renamer
    renamer.load_plugins(parent_module_name='renamer')
    repo_renamers = renamer.REPO_RENAMERS
    # Build the generic renamer when tere is no specific renamer associated with the tag
    for tag, parsers in repo_parsers.items():
        # if for such tag there is a specific renamer, then ok
        if tag in repo_renamers: continue

    # Launch the UI
    app = QApplication(sys.argv)
    model = MainModel()
    controller = MainController(model=model)
    window = MainRenamerWindow(model=model, controller=controller,
                               create_backup=args.create_backup, delete_duplicate=args.delete_duplicate)
    window.show()  # Show the form
    app.exec_()  # and execute the app


if __name__ == '__main__':  # if we're running file directly and not importing it
    sys.exit(main(sys.argv))  # run the main function
