import abc
import glob
import importlib
import inspect
import os
from shutil import copy2

from views.renamer.common import nameddic, MyRepo
from views.renamer.common.base import ClassWithTag
from views.renamer.parsers.base import MetaParser

BACKUP_FOLDERNAME = '.backup'
REPO_RENAMERS = MyRepo()


# Load the plugins in the current module
def load_plugins(parser_repo=REPO_RENAMERS, parent_module_name=''):
    for file in glob.iglob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "*.py")):
        name = os.path.splitext(os.path.basename(file))[0]
        # add package prefix to name, if required
        module = importlib.import_module(parent_module_name + '.' + name)
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


class Result(nameddic):
    def __init__(self, dirpath='', filename_src='', filename_dst='', status=Status.not_ok):
        super().__init__()
        self.dirpath = dirpath
        self.filename_src = filename_src
        self.filename_dst = filename_dst
        self.status = status


class ResultsRenaming(nameddic):

    def get_dic_from_status(self, status_list):
        out = {filename: result for filename, result in self.items() if result.status in status_list}
        return out

    def get_status(self):
        status_list = []
        for i, result in enumerate(self.values()):
            if (result.status not in status_list):
                status_list.append(result.status)
        return status_list


class IRenamer(object):

    @classmethod
    def generate_renamer(cls, config, file_extensions):
        raise NotImplementedError

    # return a dic filename -> parsing_result in a nameddic format
    @abc.abstractmethod
    def try_parse_build_filename(self, folderpath_or_list_filenames):
        raise NotImplementedError

    def try_rename_folder(self, folderpath_or_list_filenames):
        # 'filename' -> result
        results = ResultsRenaming()
        # Now get the generator
        if isinstance(folderpath_or_list_filenames, str):
            generator = glob.iglob(os.path.join(folderpath_or_list_filenames, "*.*"))
        else:
            generator = folderpath_or_list_filenames

        for file in generator:

            for renamer in REPO_RENAMERS:
                # Tentatively try to get the new name
                res = renamer.try_parse_build_filename(file)
                # Look at the status and continue to the next renamer if not ok
                if res.status == Status.ok:
                    break

            filename, file_extension = os.path.splitext(file)
            file_extension = file_extension[1:].lower()
            filename = os.path.basename(filename)
            filename += '.' + file_extension

            results[filename] = res

    # rename the files in the dic filename -> Result
    def rename_all(self, results_to_rename,
                   create_backup=True, delete_duplicate=True, options=None):
        # Create the output that will contain the dictionary with the new names
        results = {}

        for result in results_to_rename.values():
            folderpath = result.dirpath
            # If create backup need to check if the backup folder exists
            if create_backup:
                self._init_backup_folder(folderpath=folderpath)

            # check if output name does not change. skip if this is the case
            if result.filename_dst == result.filename_src:
                results[result.filename_dst] = results_to_rename[result.filename_src]
                continue

            if create_backup:
                self._backup_file(folderpath=folderpath, filename=result.filename_src)

            dst = os.path.join(folderpath, result.filename_dst)
            src = os.path.join(folderpath, result.filename_src)
            try:
                # If a file of the same name exists
                if os.path.exists(dst):
                    if not delete_duplicate:
                        print('Filepath ' + dst + ' already exists. Skip it ...')
                        continue
                    else:
                        print('Filepath ' + dst + ' already exists. Delete current one ...')
                        os.remove(src)

                os.rename(src, dst)
                results[result.filename_dst] = results_to_rename[result.filename_src]
                print(result.filename_src + '---->' + result.filename_dst)
            except:
                pass

        return results

    def _init_backup_folder(self, folderpath):
        # Test that the target folder exists
        assert os.path.exists(folderpath)
        # check if it already exists
        backup_folderpath = os.path.join(folderpath, BACKUP_FOLDERNAME)
        if os.path.exists(backup_folderpath):
            assert os.path.isdir(backup_folderpath)
        else:
            os.mkdir(backup_folderpath)

    def _backup_file(self, folderpath, filename):
        # Check that backup folder path exists
        backup_folderpath = os.path.join(folderpath, BACKUP_FOLDERNAME)
        assert os.path.exists(backup_folderpath) and os.path.isdir(backup_folderpath)
        # Copy the file to the backup folder
        src = os.path.join(folderpath, filename)
        dst = os.path.join(backup_folderpath, filename)
        # If the file is already in there, remove it
        if os.path.exists(dst):
            os.remove(dst)
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
    def try_parse_build_filename(self, folderpath_or_list_filenames):

        # 'filename' -> result
        results = ResultsRenaming()
        # Now get the generator
        if isinstance(folderpath_or_list_filenames, str):
            generator = glob.iglob(os.path.join(folderpath_or_list_filenames, "*.*"))
        else:
            generator = folderpath_or_list_filenames

        for file in generator:
            filename, file_extension = os.path.splitext(file)
            file_extension = file_extension[1:].lower()
            filename = os.path.basename(filename)
            filename += '.' + file_extension

            # Try to get a result
            out = Result()
            out.dirpath = os.path.dirname(file)
            if self.parser.try_match(filename, out):
                out.filename_dst = self.build_filename(filename_in=filename, parser_result_dic=out)
                out.status = Status.ok
            else:
                out.filename_dst = ''
                out.status = Status.not_ok

            # At this stage out can contain useful information even if the parsing failed
            out.filename_src = filename
            results[filename] = out
            print(out.filename_src + ' | ' + out.filename_dst)

        return results
