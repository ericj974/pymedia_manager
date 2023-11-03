import logging
from pathlib import Path

import pyheif
from PIL import Image

from common.constants import FILE_EXTENSION_PHOTO_HEIF
from mvc.views.renamer import ClassWithTag, RenamerWithParser, ResultsRenaming, Result
from mvc.views.renamer.common.status import StatusPhoto
from mvc.views.renamer.parsers.photo_heic import ParserHEIC


class ConverterPhotoHeic(ClassWithTag, RenamerWithParser):
    tag = 'photo_heic'

    def __init__(self):
        RenamerWithParser.__init__(self, parser=ParserHEIC())

    @classmethod
    def generate_renamer(cls, config, file_extensions):
        return ConverterPhotoHeic()

    # Build the list of files based on this renamer rules
    def try_parse_build_filename(self, folderpath_or_list_files):

        # 'filename' -> result
        results = ResultsRenaming()
        # Now get the generator
        if isinstance(folderpath_or_list_files, Path):
            generator = folderpath_or_list_files.glob("*.*")
        else:
            generator = folderpath_or_list_files

        for path in generator:
            # Skip if not heic
            if path.suffix not in FILE_EXTENSION_PHOTO_HEIF: continue
            filename_src = path.name
            filename_dst = path.stem + '.jpg'

            results[path.name] = Result(dirpath=path.parent,
                                        filename_src=filename_src,
                                        filename_dst=filename_dst,
                                        status=StatusPhoto.ok)

            logging.info(filename_src + '|' + filename_dst + '|')

        return results

    def rename_all(self, results_to_rename, create_backup, backup_foldername, delete_duplicate=True, options=None):

        for result in results_to_rename.values():
            dst = Path(result.dirpath) / result.filename_dst
            src = Path(result.dirpath) / result.filename_src

            if dst.exists():
                logging.info(f"Filepath {dst} already exists. Skip it ...")
                continue

            # Get the exif if possible
            try:
                # read heic
                io = pyheif.read(src)

                exif_bytes = None
                # Extract metadata etc
                for metadata in io.metadata or []:
                    if metadata['type'] == 'Exif':
                        exif_bytes = metadata['data']

                # Convert to other file format like jpeg
                pi = Image.frombytes(mode=io.mode, size=io.size, data=io.data)
                pi.save(dst, format="jpeg", exif=exif_bytes)
                logging.info(result.filename_src + '---->' + result.filename_dst)
            except:
                logging.info(result.filename_src + '---->' + 'NOT OK')
                pass

        logging.info('Renaming Complete')
