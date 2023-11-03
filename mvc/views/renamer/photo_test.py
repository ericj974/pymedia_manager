import shutil
import tempfile
import unittest
from pathlib import Path

import resources.test_pics as test_pics
from common import nameddic
from common.constants import FILE_EXTENSION_PHOTO_JPG
from mvc.views.renamer import MetaParser
from mvc.views.renamer.common.status import StatusPhoto
from mvc.views.renamer.photo import RenamerPhoto

file_to_rename = Path(test_pics.__file__).parent / 'to_rename.jpg'
file_renamed = Path(test_pics.__file__).parent / '20210908_122743.jpg'

from mvc.views.renamer import parsers

parsers.load_plugins(parent_module_name='mvc.views.renamer.parsers')


class RenamerPhotoTest(unittest.TestCase):

    def setUp(self) -> None:
        # Create temporary directory and copy the test files
        self.out_dir: Path = None
        self.file_to_rename: Path = None
        self.file_to_rename_upper_case: Path = None
        self.file_renamed: Path = None
        self.file_renamed_upper_case: Path = None

        # Renamer
        config = nameddic()
        config.parser_cls_list = parsers.REPO_PARSERS['photo']
        parser = MetaParser.generate_parser(config=config,
                                            file_extensions=FILE_EXTENSION_PHOTO_JPG)
        self.renamer = RenamerPhoto(parser=parser)

    def _delete_temp(self):
        try:
            shutil.rmtree(self.out_dir)
        except:
            pass

    def init(self):
        self._delete_temp()

        # Create temporary directory for downloaded files
        self.out_dir = Path(tempfile.mkdtemp())
        # Test Files
        self.file_to_rename = shutil.copy2(src=file_to_rename, dst=self.out_dir / file_to_rename.name)
        dst = self.out_dir / file_to_rename.with_suffix(file_to_rename.suffix.upper()).name
        self.file_to_rename_upper_case = shutil.copy2(src=file_to_rename, dst=dst)

        self.file_renamed = shutil.copy2(src=file_renamed, dst=self.out_dir / file_renamed.name)
        dst = self.out_dir / file_renamed.with_suffix(file_renamed.suffix.upper()).name
        self.file_renamed_upper_case = shutil.copy2(src=file_renamed, dst=dst)

    def test_try_parse_build_filename_only_exif(self):
        self.init()
        try:
            results = self.renamer.try_parse_build_filename([self.file_to_rename])
            self.assertEqual(len(results), 1)
            result = results[self.file_to_rename.name]
            self.assertEqual(result.dirpath, self.out_dir)
            self.assertEqual(result.filename_src, self.file_to_rename.name)
            self.assertEqual(result.filename_dst, self.file_renamed.name)
            self.assertEqual(result.status, StatusPhoto.exif_only)
        finally:
            self._delete_temp()

    def test_try_parse_build_filename_ext_upper_case(self):
        self.init()
        try:
            results = self.renamer.try_parse_build_filename([self.file_to_rename_upper_case])
            self.assertEqual(len(results), 1)
            result = results[self.file_to_rename_upper_case.name]
            self.assertEqual(result.dirpath, self.out_dir)
            self.assertEqual(result.filename_src, self.file_to_rename_upper_case.name)
            self.assertEqual(result.filename_dst, self.file_renamed.name)
            self.assertEqual(result.status, StatusPhoto.exif_only)
        finally:
            self._delete_temp()

    def test_try_parse_build_filename(self):
        self.init()
        try:
            results = self.renamer.try_parse_build_filename([self.file_renamed])
            self.assertEqual(len(results), 1)
            result = results[self.file_renamed.name]
            self.assertEqual(result.dirpath, self.out_dir)
            self.assertEqual(result.filename_src, self.file_renamed.name)
            self.assertEqual(result.filename_dst, self.file_renamed.name)
            self.assertEqual(result.status, StatusPhoto.ok)
        finally:
            self._delete_temp()

    def test_try_parse_build_filename_upper_case(self):
        self.init()
        try:
            results = self.renamer.try_parse_build_filename([self.file_renamed_upper_case])
            self.assertEqual(len(results), 1)
            result = results[self.file_renamed_upper_case.name]
            self.assertEqual(result.dirpath, self.out_dir)
            self.assertEqual(result.filename_src, self.file_renamed_upper_case.name)
            self.assertEqual(result.filename_dst, self.file_renamed.name)
            self.assertEqual(result.status, StatusPhoto.ok)
        finally:
            self._delete_temp()

    def test_rename_all_exif_only(self):
        self.init()
        try:
            self.file_renamed.unlink()
            self.file_renamed_upper_case.unlink()
            self.file_to_rename_upper_case.unlink()

            results = self.renamer.try_parse_build_filename([self.file_to_rename])
            self.renamer.rename_all(results_to_rename=results, create_backup=False,
                                    backup_foldername=None,
                                    delete_duplicate=True)
            self.assertTrue(self.file_renamed.exists())
            self.assertFalse(self.file_to_rename.exists())
        finally:
            self._delete_temp()

        # dst file exists and duplicates are skipped
        self.init()
        try:
            self.file_renamed_upper_case.unlink()
            self.file_to_rename_upper_case.unlink()

            results = self.renamer.try_parse_build_filename([self.file_to_rename])
            self.renamer.rename_all(results_to_rename=results, create_backup=False,
                                    backup_foldername=None,
                                    delete_duplicate=False)
            self.assertTrue(self.file_renamed.exists())
            self.assertTrue(self.file_to_rename.exists())
        finally:
            self._delete_temp()

        # This time, dst file exists and duplicates are deleted
        self.init()
        try:
            self.file_renamed_upper_case.unlink()
            self.file_to_rename_upper_case.unlink()

            results = self.renamer.try_parse_build_filename([self.file_to_rename])
            self.renamer.rename_all(results_to_rename=results, create_backup=False,
                                    backup_foldername=None,
                                    delete_duplicate=True)
            self.assertTrue(self.file_renamed.exists())
            self.assertFalse(self.file_to_rename.exists())
        finally:
            self._delete_temp()

    def test_rename_all_upper_case(self):
        self.init()
        try:
            self.file_renamed.unlink()
            self.file_to_rename.unlink()
            self.file_to_rename_upper_case.unlink()

            results = self.renamer.try_parse_build_filename([self.file_renamed_upper_case])
            self.renamer.rename_all(results_to_rename=results, create_backup=False,
                                    backup_foldername=None,
                                    delete_duplicate=True)
            self.assertTrue(self.file_renamed.exists())
            self.assertFalse(self.file_renamed_upper_case.exists())
        finally:
            self._delete_temp()

        # dst file exists and duplicates are skipped
        self.init()
        try:
            self.file_to_rename.unlink()
            self.file_to_rename_upper_case.unlink()

            results = self.renamer.try_parse_build_filename([self.file_renamed_upper_case])
            self.renamer.rename_all(results_to_rename=results, create_backup=False,
                                    backup_foldername=None,
                                    delete_duplicate=False)
            self.assertTrue(self.file_renamed.exists())
            self.assertTrue(self.file_renamed_upper_case.exists())
        finally:
            self._delete_temp()

        # This time, dst file exists and duplicates are deleted
        self.init()
        try:
            self.file_to_rename.unlink()
            self.file_to_rename_upper_case.unlink()

            results = self.renamer.try_parse_build_filename([self.file_renamed_upper_case])
            self.renamer.rename_all(results_to_rename=results, create_backup=False,
                                    backup_foldername=None,
                                    delete_duplicate=True)
            self.assertTrue(self.file_renamed.exists())
            self.assertFalse(self.file_renamed_upper_case.exists())
        finally:
            self._delete_temp()

    def tearDown(self) -> None:
        # cleanup temporary directory
        self._delete_temp()
