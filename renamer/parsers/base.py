import abc
import datetime
import re

from renamer.common import nameddic


class ResultParser(nameddic):
    def __init__(self):
        super().__init__()
        self.year = 1900
        self.month = 1
        self.day = 1
        self.hour = 00
        self.minute = 00
        self.second = 00
        self.extra = ''

    @property
    def DateTimeOriginal(self):
        return datetime.datetime(year=self.year, month=self.month, day=self.day,
                                 hour=self.hour, minute=self.minute, second=self.second)
        # return str(self.year) + ':' + str(self.month).zfill(2) + ':' + str(self.day).zfill(2) + ' ' + str(self.hour).zfill(2) + ':' + str(self.minute).zfill(2) + ':' + str(self.second).zfill(2)


class IParser(object):

    @classmethod
    def generate_parser(cls, config, file_extensions):
        raise NotImplementedError

    @abc.abstractmethod
    def try_match(self, string, result=nameddic(), do_search_first=False):
        raise NotImplementedError


class ParserWithRegexSegments(IParser):
    def __init__(self, ext):
        self.ext = ext
        self.reg_segments = []

    # recover from string relevant details and return false if cannot
    # result in dic format
    @abc.abstractmethod
    def _process_string(self, string, result):
        pass

    def get_regex(self, do_grouping=False):
        out = ''
        for seg in self.reg_segments:
            if isinstance(seg, str):
                out += '(' + seg + ')' if do_grouping else seg
            elif isinstance(seg, ParserWithRegexSegments):
                out += '(' + seg.get_regex(do_grouping=False) + ')' if do_grouping else seg.get_regex(do_grouping=False)
        return out

    def try_match(self, string, result=nameddic(), do_search_first=False):
        out = re.match(self.get_regex(do_grouping=True), string=string)

        is_ok = True
        if (out is not None):
            self._process_string(out.group(0), result)

            for ind, seg in enumerate(self.reg_segments):
                if isinstance(seg, ParserWithRegexSegments):
                    if not seg.try_match(string=out.group(ind + 1), result=result):
                        is_ok = False
                        break

        if (out is not None) and (is_ok):
            return True

        # Return None if no
        out = re.search(self.get_regex(do_grouping=True), string=string)

        if (out is None):
            return False

        self._process_string(out.group(0), result)

        for ind, seg in enumerate(self.reg_segments):
            if isinstance(seg, ParserWithRegexSegments):
                if not seg.try_match(string=out.group(ind + 1), result=result):
                    return False
        return True


class MetaParser(IParser):
    def __init__(self):
        self.parser_list = []

    @classmethod
    def generate_parser(cls, config, file_extensions):
        # Get all the parsers under such name
        parser_cls_list = config.parser_cls_list

        obj = cls()
        obj.parser_list = [parser_cls(file_extension) for parser_cls in parser_cls_list
                           for file_extension in file_extensions]
        return obj

    # TODO: Add a hierarchy notion especially for aprooximate search
    # (if ne is less precise than the other,  better put him last)
    def try_match(self, string, result=nameddic(), do_search_first=False):
        for parser in self.parser_list:
            tmp = nameddic()
            if parser.try_match(string, result=tmp):
                for key, value in tmp.items():
                    result[key] = value
                return True
        return False
