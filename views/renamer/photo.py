import datetime
import glob
import io
import os

import piexif
from PIL import Image

import utils
import views.renamer.parsers.base
from constants import FILE_EXTENSION_PHOTO_JPG
from thirdparty import exiftool
from views.renamer import ClassWithTag, RenamerWithParser, MetaParser, ResultsRenaming, Result
from views.renamer import parsers
from views.renamer.common.status import StatusPhoto


class RenamerPhoto(ClassWithTag, RenamerWithParser):
    tag = 'photo'

    def __init__(self,
                 parser,
                 timedelta_max=datetime.timedelta(seconds=60)):
        RenamerWithParser.__init__(self, parser=parser)
        self.timedelta_max = timedelta_max

    @classmethod
    def generate_renamer(cls, config, file_extensions):
        parser = MetaParser.generate_parser(config=config.parser,
                                            file_extensions=file_extensions)
        return RenamerPhoto(parser=parser)

    # Build the list of files based on this renamer rules
    def try_parse_build_filename(self, folderpath_or_list_filenames):

        # 'filename' -> result
        results = ResultsRenaming()
        # Now get the generator
        if isinstance(folderpath_or_list_filenames, str):
            generator = glob.iglob(os.path.join(folderpath_or_list_filenames, "*.*"))
        else:
            generator = folderpath_or_list_filenames

        with exiftool.ExifTool() as et:
            for file in generator:
                filename_src = os.path.basename(file)
                filename_no_ext, file_extension_case = os.path.splitext(filename_src)
                file_extension_case = file_extension_case[1:]

                # Skip if not the right extension
                if file_extension_case not in FILE_EXTENSION_PHOTO_JPG: continue

                # Datetime from exif
                try:
                    exif = et.get_metadata(file)
                    datetime_from_exif = utils.get_datetime_exiftool(exif)
                except:
                    datetime_from_exif = None

                # Datetime from filename
                datetime_from_filename = None
                result_parser = views.renamer.parsers.base.ResultParser()
                if self.parser.try_match(filename_src, result_parser, do_search_first=False):
                    datetime_from_filename = result_parser.DateTimeOriginal

                result_parser.datetime_from_exif = datetime_from_exif
                result_parser.datetime_from_filename = datetime_from_filename

                # Update status
                status = StatusPhoto.not_ok
                if datetime_from_exif:
                    status = StatusPhoto.exif_only
                    if datetime_from_filename:
                        status = StatusPhoto.ok
                elif datetime_from_filename:
                    status = StatusPhoto.filename_exact_only

                filename_dst, status_out = self.build_filename(filename_src, result_parser)
                results[filename_src] = Result(dirpath=os.path.dirname(file),
                                               filename_src=filename_src,
                                               filename_dst=filename_dst,
                                               status=status_out)

                print(filename_src + '|' + str(datetime_from_exif) + '|' + str(datetime_from_filename) + '|' + str(
                    datetime_from_filename) + '|')

        return results

    def rename_all(self, results_to_rename,
                   create_backup, backup_foldername, delete_duplicate=True, options=None):
        results = super(RenamerPhoto, self).rename_all(results_to_rename=results_to_rename,
                                                       create_backup=create_backup,
                                                       backup_foldername=backup_foldername,
                                                       delete_duplicate=delete_duplicate,
                                                       options=options)

        if (options is None) or ('update_exif' not in options) or (not options.update_exif):
            return

        # Time to input the new date in exif if applicable
        # Only applicable if filename_out is either built from datetime_in or datetime_out
        for filename_out, result in results.items():
            filename, file_extension = os.path.splitext(filename_out)
            file_extension = file_extension[1:]

            # Try to reparse the filename and see if we get a date different from exif.
            # If so change exif
            out = views.renamer.parsers.base.ResultParser()
            regex = views.renamer.parsers.base.ParserWithRegexSegments(file_extension)
            regex.reg_segments = [parsers.YearMonthDayParser(), '_', parsers.TimeParser()]
            datetime_name_test = None
            if regex.try_match(filename, out, do_search_first=True):
                datetime_name_test = out.DateTimeOriginal
            if (datetime_name_test is not None) and (result.datetime_from_exif != datetime_name_test):
                folderpath = result.dirpath
                self._write_datetime_to_exif(os.path.join(folderpath, filename_out),
                                             datetime_name_test)

    def _write_datetime_to_exif(self, filepath, datetime_new):
        print('Load image ' + filepath + ' ...')
        try:
            exif_dict = utils.get_exif_v2(filepath)
            exif_dict["0th"][piexif.ImageIFD.DateTime] = datetime.datetime.strftime(datetime_new, '%Y:%m:%d %H:%M:%S')
        except KeyError:
            o = io.BytesIO()
            thumb_im = Image.open(filepath)
            thumb_im.thumbnail((50, 50), Image.ANTIALIAS)
            thumb_im.save(o, "jpeg")
            thumbnail = o.getvalue()

            zeroth_ifd = {piexif.ImageIFD.Make: u"unknown",
                          piexif.ImageIFD.XResolution: (96, 1),
                          piexif.ImageIFD.YResolution: (96, 1),
                          piexif.ImageIFD.Software: u"piexif",
                          piexif.ImageIFD.DateTime: datetime.datetime.strftime(datetime_new, '%Y:%m:%d %H:%M:%S')
                          }

            exif_ifd = {piexif.ExifIFD.DateTimeOriginal: datetime.datetime.strftime(datetime_new, '%Y:%m:%d %H:%M:%S'),
                        piexif.ExifIFD.LensMake: u"LensMake",
                        piexif.ExifIFD.Sharpness: 65535,
                        piexif.ExifIFD.LensSpecification: ((1, 1), (1, 1), (1, 1), (1, 1)),
                        }
            gps_ifd = {piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
                       piexif.GPSIFD.GPSAltitudeRef: 1,
                       piexif.GPSIFD.GPSDateStamp: datetime.datetime.strftime(datetime_new, '%Y:%m:%d %H:%M:%S'),
                       }
            first_ifd = {piexif.ImageIFD.Make: u"unknown",
                         piexif.ImageIFD.XResolution: (40, 1),
                         piexif.ImageIFD.YResolution: (40, 1),
                         piexif.ImageIFD.Software: u"piexif"
                         }

            exif_dict = {"0th": zeroth_ifd, "Exif": exif_ifd, "GPS": gps_ifd, "1st": first_ifd, "thumbnail": thumbnail}

        utils.save_exif(exif_dict=exif_dict, filepath=filepath)

    def _is_timedelta_ok(self, time1, time2):
        return abs(time1 - time2) <= self.timedelta_max

    def build_filename(self, filename_in, parser_result_dic):

        filename, file_extension = os.path.splitext(filename_in)
        file_extension = file_extension[1:].lower()
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
                if self._is_timedelta_ok(datetime_from_exif, datetime_from_filename):
                    status_out = StatusPhoto.ok
                else:
                    status_out = StatusPhoto.conflict_exif_filename
            else:
                status_out = StatusPhoto.exif_only
        elif (datetime_from_filename is not None):
            status_out = StatusPhoto.filename_exact_only

        if datetime_out is None:
            return '', status_out

        return datetime.datetime.strftime(datetime_out, '%Y%m%d_%H%M%S') + extra_out + '.' + file_extension, status_out
