import pyheif
from PIL import Image

from views.renamer import *
from views.renamer.common.status import StatusPhoto
from views.renamer.parsers.photo_heic import ParserHEIC


class ConverterPhotoHeic(ClassWithTag, RenamerWithParser):
    tag = 'photo_heic'

    def __init__(self):
        RenamerWithParser.__init__(self, parser=ParserHEIC())

    @classmethod
    def generate_renamer(cls, config, file_extensions):
        return ConverterPhotoHeic()

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
            filename, file_extension_case = os.path.splitext(file)
            file_extension = file_extension_case[1:].lower()

            # Skip if not heic
            if "heic" != file_extension: continue

            filename = os.path.basename(filename)

            filename_case = filename
            filename_case += '.' + file_extension_case[1:]

            filename_src = filename_case
            filename_dst = filename + '.jpg'

            results[filename_case] = Result(dirpath=os.path.dirname(file),
                                            filename_src=filename_src,
                                            filename_dst=filename_dst,
                                            status=StatusPhoto.ok)

            print(filename_src + '|' + filename_dst + '|')

        return results

    def rename_all(self, results_to_rename, create_backup, backup_foldername, delete_duplicate=True, options=None):

        for result in results_to_rename.values():
            dst = os.path.join(result['dirpath'], result.filename_dst)
            src = os.path.join(result['dirpath'], result.filename_src)

            if os.path.exists(dst):
                print('Filepath ' + dst + ' already exists. Skip it ...')
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
                print(result.filename_src + '---->' + result.filename_dst)
            except:
                print(result.filename_src + '---->' + 'NOT OK')
                pass

        print('DONE RENAMING !')
