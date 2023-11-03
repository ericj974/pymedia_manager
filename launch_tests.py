import unittest
from PyQt5 import QtWebEngineWidgets # Necessary to avoid Errors with pyqtlet

def main():
    # Just to avoid removing the import when code cleaning
    QtWebEngineWidgets.__file__

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir='.', pattern="*_test.py")
    alltests = unittest.TestSuite(suite)
    unittest.TextTestRunner(verbosity=2).run(alltests)

if __name__ == '__main__':
    main()