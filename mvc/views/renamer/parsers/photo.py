from mvc.views.renamer.common.base import ClassWithTag
from mvc.views.renamer.parsers import YearMonthDayParser, TimeParser, ParserWithRegexSegments


class RegPic1(ClassWithTag, ParserWithRegexSegments):
    tag = 'photo'

    def __init__(self, ext):
        super(RegPic1, self).__init__(ext)
        self.reg_segments = ['IMG_', YearMonthDayParser(), '_', TimeParser()]
        if ext is not None:
            self.reg_segments += [ext]


class RegPic2(ClassWithTag, ParserWithRegexSegments):
    tag = 'photo'

    def __init__(self, ext):
        super(RegPic2, self).__init__(ext)
        self.reg_segments = [YearMonthDayParser(), '_', TimeParser()]
        if ext is not None:
            self.reg_segments += [ext]


class RegPic3(ClassWithTag, ParserWithRegexSegments):
    tag = 'photo'

    def __init__(self, ext):
        super(RegPic3, self).__init__(ext)
        self.reg_segments = ['IMG_', YearMonthDayParser(), '_', TimeParser(), '_HDR']
        if ext is not None:
            self.reg_segments += [ext]


class RegPic4(ClassWithTag, ParserWithRegexSegments):
    tag = 'photo'

    def __init__(self, ext):
        super(RegPic4, self).__init__(ext)
        self.reg_segments = [YearMonthDayParser(), '_', TimeParser(), '_HDR']
        if ext is not None:
            self.reg_segments += [ext]


class RegPic5(ClassWithTag, ParserWithRegexSegments):
    tag = 'photo'

    def __init__(self, ext):
        super(RegPic5, self).__init__(ext)
        self.reg_segments = ['Office Lens ', YearMonthDayParser(), '-', TimeParser()]
        if ext is not None:
            self.reg_segments += [ext]


class WhatsappNumberParser(ParserWithRegexSegments):
    def __init__(self):
        super(WhatsappNumberParser, self).__init__(None)
        self.reg_segments = ['WA', '[0-9][0-9][0-9][0-9]']

    def _process_string(self, string, result):
        result.extra = string


class RegPicWhatsapp(ClassWithTag, ParserWithRegexSegments):
    tag = 'photo'

    def __init__(self, ext=None):
        super(RegPicWhatsapp, self).__init__(ext)
        self.reg_segments = ['IMG-', YearMonthDayParser(), '-', WhatsappNumberParser()]
        if ext is not None:
            self.reg_segments += [ext]
