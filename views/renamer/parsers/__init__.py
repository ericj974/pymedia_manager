import glob
import importlib
import inspect
import os

from views.renamer.common import MyRepo
from views.renamer.common.base import ClassWithTag
from views.renamer.parsers.base import ParserWithRegexSegments

sub_modules = []

REPO_PARSERS = MyRepo()


# Load the plugins in the current module
def load_plugins(parent_module_name=''):
    for modulename in sub_modules:
        parent_name = parent_module_name + '.' + modulename
        module = importlib.import_module(parent_name)
        module.load_parser_plugins(REPO_PARSERS, parent_name)

    for file in glob.iglob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "*.py")):
        name = os.path.splitext(os.path.basename(file))[0]
        # add package prefix to name, if required
        module = importlib.import_module(parent_module_name + '.' + name)
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj):
                if issubclass(obj, ClassWithTag) and \
                        (obj.__name__ != ClassWithTag.__name__):
                    test = obj
                    test.register_tag(repo_parsers=REPO_PARSERS)


class YearMonthDayParser(ParserWithRegexSegments):
    def __init__(self):
        super(YearMonthDayParser, self).__init__(None)
        self.reg_segments = [YearParser(), MonthParser(), DayParser()]


class YearParser(ParserWithRegexSegments):
    def __init__(self):
        super(YearParser, self).__init__(None)
        self.reg_segments = ['[1-2][0-9][0-9][0-9]']

    def _process_string(self, string, result):
        result.year = int(string)


class MonthParser(ParserWithRegexSegments):
    def __init__(self):
        super(MonthParser, self).__init__(None)
        self.reg_segments = ['[0,1][0-9]']

    def _process_string(self, string, result):
        result.month = int(string)


class DayParser(ParserWithRegexSegments):
    def __init__(self):
        super(DayParser, self).__init__(None)
        self.reg_segments = ['[0-3][0-9]']

    def _process_string(self, string, result):
        result.day = int(string)


class TimeParser(ParserWithRegexSegments):
    def __init__(self):
        super(TimeParser, self).__init__(None)
        self.reg_segments = [HourParser(), MinParser(), SecondParser()]


class HourParser(ParserWithRegexSegments):
    def __init__(self):
        super(HourParser, self).__init__(None)
        self.reg_segments = ['[0-2][0-9]']

    def _process_string(self, string, result):
        result.hour = int(string)


class MinParser(ParserWithRegexSegments):
    def __init__(self):
        super(MinParser, self).__init__(None)
        self.reg_segments = ['[0-6][0-9]']

    def _process_string(self, string, result):
        result.minute = int(string)


class SecondParser(ParserWithRegexSegments):
    def __init__(self):
        super(SecondParser, self).__init__(None)
        self.reg_segments = ['[0-6][0-9]']

    def _process_string(self, string, result):
        result.second = int(string)
