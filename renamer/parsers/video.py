from renamer.common.base import ClassWithTag
from renamer.parsers import ParserWithRegexSegments, YearMonthDayParser, TimeParser, DayParser, MonthParser, YearParser, HourParser, MinParser

# 'IMG_XXXX.HEIC'
class ParserMTS(ClassWithTag, ParserWithRegexSegments):
    tag = 'video'

    class Part1(ParserWithRegexSegments):
        def __init__(self):
            super().__init__(None)
            self.reg_segments = [DayParser(), '-', MonthParser(), '-', YearParser(),'-',HourParser(),'h',MinParser()]

        def _process_string(self, string, result):
            pass

    def __init__(self, file_extension='MTS'):
        super().__init__(file_extension)
        self.reg_segments = [ParserMTS.Part1()]
