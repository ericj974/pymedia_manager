from views.renamer.common.base import ClassWithTag
from views.renamer.parsers import ParserWithRegexSegments, YearMonthDayParser, TimeParser


# 'IMG_XXXX.HEIC'
class ParserHEIC(ClassWithTag, ParserWithRegexSegments):
    tag = 'photo_heic'

    class Part1(ParserWithRegexSegments):
        def __init__(self):
            super().__init__(None)
            self.reg_segments = ['[0-9][0-9][0-9][0-9]']

        def _process_string(self, string, result):
            pass

    def __init__(self, file_extension='heic'):
        super().__init__(file_extension)
        self.reg_segments = ['IMG_',
                             ParserHEIC.Part1(),
                             '.' + file_extension]


# 'IMG_XXXX.HEIC'
class ParserHEIC2(ClassWithTag, ParserWithRegexSegments):
    tag = 'photo_heic'

    class Part1(ParserWithRegexSegments):
        def __init__(self):
            super().__init__(None)
            self.reg_segments = [YearMonthDayParser(), '_', TimeParser()]

        def _process_string(self, string, result):
            pass

    def __init__(self, file_extension='heic'):
        super().__init__(file_extension)
        self.reg_segments = [ParserHEIC.Part1(),
                             '.' + file_extension]
