import logging
from datetime import datetime
from pathlib import Path

from common import exif
from common.constants import FILE_EXTENSION_VIDEO
from mvc.views.renamer import ClassWithTag, RenamerWithParser, ResultsRenaming, Result
from mvc.views.renamer.common.status import StatusPhoto
from mvc.views.renamer.parsers.base import ResultParser, MetaParser


class RenamerVideo(ClassWithTag, RenamerWithParser):
    tag = 'video'

    def __init__(self, parser):
        RenamerWithParser.__init__(self, parser=parser)

    @classmethod
    def generate_renamer(cls, config, file_extensions):
        parser = MetaParser.generate_parser(config=config.parser,
                                            file_extensions=file_extensions)
        return RenamerVideo(parser=parser)

    # Build the list of files based on this renamer rules
    def try_parse_build_filename(self, folderpath_or_list_files):
        logging.warning(("Retrieval of exif not implemented yet usinf piexif...."))
        return ResultsRenaming()

        # # 'filename' -> result
        # results = ResultsRenaming()
        # # Now get the generator
        # if isinstance(folderpath_or_list_files, Path):
        #     generator = folderpath_or_list_files.glob("*.*")
        # else:
        #     generator = folderpath_or_list_files
        #
        # with exiftool.ExifTool() as et:
        #     for path in generator:
        #         filename_src = path.name
        #
        #         # Skip if not the right extension
        #         if path.suffix not in FILE_EXTENSION_VIDEO: continue
        #
        #         # Datetime from exif
        #         try:
        #             metadata = et.get_metadata(str(path))
        #             datetime_from_exif = exif.get_datetime_exiftool(metadata)
        #         except:
        #             datetime_from_exif = None
        #
        #         # Datetime from filename
        #         datetime_from_filename = None
        #         result_parser = ResultParser()
        #         if self.parser.try_match(filename_src, result_parser, do_search_first=False):
        #             datetime_from_filename = result_parser.DateTimeOriginal
        #
        #         result_parser.datetime_from_exif = datetime_from_exif
        #         result_parser.datetime_from_filename = datetime_from_filename
        #
        #         filename_dst, status_out = self.build_filename(filename_src, result_parser)
        #         results[filename_src] = Result(dirpath=path.parent,
        #                                        filename_src=filename_src,
        #                                        filename_dst=filename_dst,
        #                                        status=status_out)
        #
        #         print(filename_src + '|' + filename_dst + '|')
        #
        # return results

    def rename_all(self, results_to_rename, create_backup, backup_foldername, delete_duplicate=True, options=None):

        for result in results_to_rename.values():
            dst = Path(result.dirpath) / result.filename_dst
            src = Path(result.dirpath) / result.filename_src

            if dst.exists():
                print(f"Filepath {dst} already exists. Skip it ...")
                continue

            try:
                # Rename
                src.replace(src.with_name(result.filename_dst))
                print(result.filename_src + '---->' + result.filename_dst)
            except:
                print(result.filename_src + '---->' + 'NOT OK')
                pass

        print('DONE RENAMING !')

    def build_filename(self, filename_in, parser_result_dic):

        path = Path(filename_in)

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

        return datetime.strftime(datetime_out, '%Y%m%d_%H%M%S') + extra_out + path.suffix.lower(), status_out
