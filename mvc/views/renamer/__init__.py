import abc
import importlib
import inspect
import logging
from pathlib import Path
from shutil import copy2

from mvc.views.renamer.common import nameddic, MyRepo
from mvc.views.renamer.common.base import ClassWithTag
from mvc.views.renamer.parsers.base import MetaParser

REPO_RENAMERS = MyRepo()


# Load the plugins in the current module
def load_plugins(parser_repo=REPO_RENAMERS, parent_module_name=''):
    for file in Path(__file__).parent.glob("*.py"):
        # add package prefix to name, if required
        module = importlib.import_module(parent_module_name + '.' + file.stem)
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj):
                if issubclass(obj, ClassWithTag) and \
                        (obj.__name__ != ClassWithTag.__name__) and \
                        issubclass(obj, IRenamer):
                    test = obj
                    test.register_tag(repo_parsers=parser_repo)


class Status:
    ok = 'OK'
    not_ok = 'NOT OK'


class Result:
    def __init__(self, dirpath: Path = None, filename_src='', filename_dst='', status=Status.not_ok):
        super().__init__()
        self.dirpath: Path = dirpath
        self.filename_src: str = filename_src
        self.filename_dst: str = filename_dst
        self.status: str = status


class ResultsRenaming(nameddic):

    def get_dic_from_status(self, status_list):
        out = {filename: result for filename, result in self.items() if result.status in status_list}
        return out

    def get_status_list(self):
        status_list = []
        for i, result in enumerate(self.values()):
            if (result.status not in status_list):
                status_list.append(result.status)
        return status_list


class IRenamer(object):

    def __init__(self, config: dict):
        self.create_backup = config

    @classmethod
    def generate_renamer(cls, config, file_extensions):
        raise NotImplementedError

    # return a dic filename -> parsing_result in a nameddic format
    @abc.abstractmethod
    def try_parse_build_filename(self, folderpath_or_list_files):
        raise NotImplementedError

    def try_rename_folder(self, folderpath_or_list_files):
        # 'filename' -> result
        results = ResultsRenaming()
        # Now get the generator
        if isinstance(folderpath_or_list_files, Path):
            generator = folderpath_or_list_files.glob("*.*")
        else:
            generator = folderpath_or_list_files

        for file in generator:

            for renamer in REPO_RENAMERS:
                # Tentatively try to get the new name
                res = renamer.try_parse_build_filename(file)
                # Look at the status and continue to the next renamer if not ok
                if res.status == Status.ok:
                    break

            results[file.name] = res

    # rename the files in the dic filename -> Result
    def rename_all(self, results_to_rename,
                   create_backup, backup_foldername, delete_duplicate=True, options=None):
        # Create the output that will contain the dictionary with the new names
        results = {}

        for result in results_to_rename.values():
            folderpath = result.dirpath
            # If create backup need to check if the backup folder exists
            if create_backup:
                self._init_backup_folder(folderpath=folderpath, backup_foldername=backup_foldername)

            # check if output name does not change. skip if this is the case
            if result.filename_dst == result.filename_src:
                results[result.filename_dst] = results_to_rename[result.filename_src]
                continue

            if create_backup:
                self._backup_file(folderpath=folderpath, backup_foldername=backup_foldername,
                                  filename=result.filename_src)

            dst = folderpath / result.filename_dst
            src = folderpath / result.filename_src
            try:
                # If a file of the same name exists
                if dst.exists():
                    if not delete_duplicate:
                        print(f"Filepath {dst} already exists. Skip it ...")
                        continue
                    else:
                        print(f"Filepath {dst} already exists. Delete current one ...")
                        src.unlink()
                        continue

                src.replace(src.with_name(result.filename_dst))
                results[result.filename_dst] = results_to_rename[result.filename_src]
                print(result.filename_src + '---->' + result.filename_dst)
            except Exception as e:
                logging.warning(e)

        return results

    def _init_backup_folder(self, folderpath: Path, backup_foldername):
        # Test that the target folder exists and is a dir
        assert folderpath.is_dir()
        # check if it already exists
        backup_folderpath = folderpath / backup_foldername
        if backup_folderpath.exists():
            assert backup_folderpath.is_dir()
        else:
            backup_folderpath.mkdir()

    def _backup_file(self, folderpath: Path, backup_foldername, filename):
        # Check that backup folder path exists
        backup_folderpath = folderpath / backup_foldername
        assert backup_folderpath.is_dir()
        # Copy the file to the backup folder
        src = folderpath / filename
        dst = backup_folderpath / filename
        # If the file is already in there, remove it
        if dst.exists():
            dst.unlink()
        # Copy while (trying to) preserve metadata
        copy2(src=src, dst=dst)


# A generic class to accept a list of parser as input,
class RenamerWithParser(IRenamer):
    def __init__(self, parser):
        self.parser = parser
        self.config = nameddic()
        self.config.builder = nameddic()

    @classmethod
    def generate_renamer(cls, config, file_extensions):
        parser = MetaParser.generate_parser(config=config.parser,
                                            file_extensions=file_extensions)

        return RenamerWithParser(parser=parser)

    @abc.abstractmethod
    def build_filename(self, filename_in, parser_result_dic):
        '''
        Build the output filename with file extension
        :param filename_in:
        :param parser_result_dic:
        :return: filename with file extension, status
        '''
        raise NotImplementedError()

    # Build the list of files based on this renamer rules
    def try_parse_build_filename(self, folderpath_or_list_files):

        # 'filename' -> result
        results = ResultsRenaming()
        # Now get the generator
        if isinstance(folderpath_or_list_files, str):
            generator = folderpath_or_list_files.glob("*.*")
        else:
            generator = folderpath_or_list_files

        for path in generator:
            filename = path.stem + path.suffix.lower()
            # Try to get a result
            out = Result()
            out.dirpath = path.parent
            if self.parser.try_match(filename, out):
                out.filename_dst = self.build_filename(filename_in=filename, parser_result_dic=out)
                out.status = Status.ok
            else:
                out.filename_dst = ''
                out.status = Status.not_ok

            # At this stage out can contain useful information even if the parsing failed
            out.filename_src = path.name
            results[filename] = out
            print(out.filename_src + ' | ' + out.filename_dst)

        return results
