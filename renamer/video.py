import glob
import os
from datetime import datetime

import utils
from renamer import ClassWithTag, RenamerWithParser, ResultsRenaming, Result
from renamer.common.status import StatusPhoto
from renamer.parsers.base import ResultParser
from renamer.parsers.video import ParserMTS
from thirdparty import exiftool

file_extensions = {
    'AVI': 'avi',
    'avi': 'avi',
    'MTS': 'MTS',
    'mts': 'MTS',
    'MP4': 'mp4',
    'mp4': 'mp4',
    'mov': 'mov',
    'MOV': 'mov',
    'WMV': 'wmv',
    'wmv': 'wmv'
}


class RenamerVideo(ClassWithTag, RenamerWithParser):
    tag = 'video'

    def __init__(self):
        RenamerWithParser.__init__(self, parser=ParserMTS())

    @classmethod
    def generate_renamer(cls, config, file_extension):
        return RenamerVideo()

    # Build the list of files based on this renamer rules
    def try_parse_build_filename(self, folderpath_or_list_filenames):

        # 'filename' -> result
        results = ResultsRenaming()
        # Now get the generator
        if isinstance(folderpath_or_list_filenames, str):
            generator = glob.iglob(os.path.join(folderpath_or_list_filenames, "*.*"))
        else:
            generator = folderpath_or_list_filenames

        for file in generator:
            filename_src = os.path.basename(file)
            filename_no_ext, file_extension_case = os.path.splitext(file)
            file_extension_case = file_extension_case[1:]

            # Skip if not MTS
            if file_extension_case not in file_extensions: continue

            # Datetime from exif
            try:
                with exiftool.ExifTool() as et:
                    exif = et.get_metadata(file)
                    datetime_from_exif = utils.get_datetime_exiftool(exif)
            except:
                datetime_from_exif = None

            # Pattern matching from filename
            datetime_from_filename = None
            result_parser = ResultParser()
            if self.parser.try_match(filename_no_ext, result_parser, do_search_first=False):
                datetime_from_filename = result_parser.DateTimeOriginal

            result_parser.datetime_from_exif = datetime_from_exif
            result_parser.datetime_from_filename = datetime_from_filename

            filename_dst, status_out = self.build_filename(filename_src, result_parser)
            results[filename_src] = Result(dirpath=os.path.dirname(file),
                                           filename_src=filename_src,
                                           filename_dst=filename_dst,
                                           status=status_out)

            print(filename_src + '|' + filename_dst + '|')

        return results

    def rename_all(self, results_to_rename, create_backup=True, delete_duplicate=True, options=None):

        for result in results_to_rename.values():
            dst = os.path.join(result['dirpath'], result.filename_dst)
            src = os.path.join(result['dirpath'], result.filename_src)

            if os.path.exists(dst):
                print('Filepath ' + dst + ' already exists. Skip it ...')
                continue

            # Get the exif if possible
            try:
                os.rename(src, dst)
                print(result.filename_src + '---->' + result.filename_dst)
            except:
                print(result.filename_src + '---->' + 'NOT OK')
                pass

        print('DONE RENAMING !')

    def build_filename(self, filename_in, parser_result_dic):

        filename_no_ext, file_extension_case = os.path.splitext(filename_in)
        file_extension_case = file_extension_case[1:]
        file_extension = file_extensions[file_extension_case]

        datetime_from_exif = parser_result_dic.datetime_from_exif
        datetime_from_filename = parser_result_dic.datetime_from_filename
        extra = parser_result_dic.extra

        datetime_out = None
        status_out = StatusPhoto.not_ok

        # Exif > Exact + extra
        extra_out = ''
        if (datetime_from_exif is not None):
            datetime_out = datetime_from_exif
            extra_out = ''
        elif (datetime_from_filename is not None):
            datetime_out = datetime_from_filename
            extra_out = '_' + extra if extra else ''

        # Update of the status
        if (datetime_from_exif is not None):
            if (datetime_from_filename is not None):
                status_out = StatusPhoto.ok
            else:
                status_out = StatusPhoto.exif_only
        elif (datetime_from_filename is not None):
            status_out = StatusPhoto.filename_exact_only

        if datetime_out is None:
            return '', status_out

        return datetime.strftime(datetime_out, '%Y%m%d_%H%M%S') + extra_out + '.' + file_extension, status_out
