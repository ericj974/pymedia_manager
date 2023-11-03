from mvc.views.renamer.common.base import ClassWithTag
from mvc.views.renamer.parsers import ParserWithRegexSegments, YearMonthDayParser, TimeParser, DayParser, MonthParser, \
    YearParser, \
    HourParser, MinParser


class ParserMTS(ClassWithTag, ParserWithRegexSegments):
    tag = 'video'

    class Part1(ParserWithRegexSegments):
        def __init__(self):
            super().__init__(None)
            self.reg_segments = [DayParser(), '-', MonthParser(), '-', YearParser(), '-', HourParser(), 'h',
                                 MinParser()]

        def _process_string(self, string, result):
            pass

    def __init__(self, file_extension='.MTS'):
        super().__init__(file_extension)
        self.reg_segments = [ParserMTS.Part1(), file_extension]


class ParserOnePlus9(ClassWithTag, ParserWithRegexSegments):
    tag = 'video'

    class Part1(ParserWithRegexSegments):
        def __init__(self):
            super().__init__(None)
            self.reg_segments = ['VID_', YearMonthDayParser(), '_', TimeParser()]

        def _process_string(self, string, result):
            pass

    def __init__(self, file_extension='.mp4'):
        super().__init__(file_extension)
        self.reg_segments = [ParserOnePlus9.Part1(), file_extension]


class ParserMP4(ClassWithTag, ParserWithRegexSegments):
    tag = 'video'

    class Part1(ParserWithRegexSegments):
        def __init__(self):
            super().__init__(None)
            self.reg_segments = [YearMonthDayParser(), '_', TimeParser()]

        def _process_string(self, string, result):
            pass

    def __init__(self, file_extension='.mp4'):
        super().__init__(file_extension)
        self.reg_segments = [ParserMP4.Part1(), file_extension]
