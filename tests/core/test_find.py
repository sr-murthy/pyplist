import os

from pathlib import Path
from tempfile import (
    NamedTemporaryFile,
    TemporaryDirectory,
)
from unittest import TestCase

from pyplist.core.find import find_plists


class TestFindPlists(TestCase):

    def test__target_dir_does_not_exist__non_recursive_search__file_not_found_error_raised(self):
        target_dir = TemporaryDirectory().name

        with self.assertRaises(FileNotFoundError):
            list(find_plists(target_dir, recursive=False))

    def test__target_dir_does_not_exist__recursive_search__file_not_found_error_raised(self):
        target_dir = TemporaryDirectory().name

        with self.assertRaises(FileNotFoundError):
            list(find_plists(target_dir, recursive=True))

    def test__no_plist_files_in_target_dir__non_recursive_search__no_plists_generated(self):
        with TemporaryDirectory() as target_dir:
            with open(Path(target_dir).joinpath('test.txt'), 'w') as txt_file:
                txt_file.write('Text file')
                txt_file.flush()

                self.assertEqual(list(find_plists(target_dir, recursive=False)), [])

    def test__no_plist_files_in_target_dir__recursive_search__no_plists_generated(self):
        with TemporaryDirectory() as target_dir:
            with open(Path(target_dir).joinpath('test.txt'), 'w') as txt_file:
                txt_file.write('Text file')
                txt_file.flush()

                subfolder = Path(target_dir).joinpath('sub')
                os.mkdir(subfolder)
                with open(subfolder.joinpath('test.csv'), 'w') as csv_file:
                    csv_file.write('CSV file')
                    csv_file.flush()

                self.assertEqual(list(find_plists(target_dir, recursive=False)), [])

