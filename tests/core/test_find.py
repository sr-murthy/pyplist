import os
import textwrap

from pathlib import Path
from tempfile import (
    NamedTemporaryFile,
    TemporaryDirectory,
)
from unittest import TestCase

from pyplist.core.find import find_plists
from pyplist.core.plist import Plist


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

    def test__target_dir_has_plist_files_in_root_only__non_recursive_search__correct_plists_generated(self):
        plist1_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>a</key>
                        <string>one</string>
                    </dict>
                    </plist>
                    """

        plist2_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>b</key>
                        <integer>2</integer>
                    </dict>
                    </plist>
                    """

        with TemporaryDirectory() as target_dir:
            with open(Path(target_dir).joinpath('plist1.plist'), 'wb') as plist1_file:
                with open(Path(target_dir).joinpath('plist2.plist'), 'wb') as plist2_file:
                    plist1_file.write(textwrap.dedent(plist1_xml).encode('utf8'))
                    plist1_file.flush()
                    expected_plist1 = Plist(plist1_file.name)

                    plist2_file.write(textwrap.dedent(plist2_xml).encode('utf8'))
                    plist2_file.flush()
                    expected_plist2 = Plist(plist2_file.name)

                    received_plist1, received_plist2 = list(find_plists(target_dir, recursive=False))

                    assert received_plist1 == expected_plist1
                    assert received_plist2 == expected_plist2

    def test__target_dir_has_plist_files_in_root_and_subfolder__non_recursive_search__correct_plists_generated(self):
        plist1_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>a</key>
                        <string>one</string>
                    </dict>
                    </plist>
                    """

        plist2_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>b</key>
                        <integer>2</integer>
                    </dict>
                    </plist>
                    """

        with TemporaryDirectory() as target_dir:
            with open(Path(target_dir).joinpath('plist1.plist'), 'wb') as plist1_file:
                plist1_file.write(textwrap.dedent(plist1_xml).encode('utf8'))
                plist1_file.flush()
                expected_plist1 = Plist(plist1_file.name)

                subfolder = Path(target_dir).joinpath('sub')
                os.mkdir(subfolder)
                with open(subfolder.joinpath('plist2.plist'), 'wb') as plist2_file:
                    plist2_file.write(textwrap.dedent(plist2_xml).encode('utf8'))
                    plist2_file.flush()

                    received_plist1 = next(find_plists(target_dir, recursive=False))

                    assert received_plist1 == expected_plist1

    def test__target_dir_has_plist_files_in_root_only__recursive_search__correct_plists_generated(self):
        plist1_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>a</key>
                        <string>one</string>
                    </dict>
                    </plist>
                    """

        plist2_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>b</key>
                        <integer>2</integer>
                    </dict>
                    </plist>
                    """

        with TemporaryDirectory() as target_dir:
            with open(Path(target_dir).joinpath('plist1.plist'), 'wb') as plist1_file:
                with open(Path(target_dir).joinpath('plist2.plist'), 'wb') as plist2_file:
                    plist1_file.write(textwrap.dedent(plist1_xml).encode('utf8'))
                    plist1_file.flush()
                    expected_plist1 = Plist(plist1_file.name)

                    plist2_file.write(textwrap.dedent(plist2_xml).encode('utf8'))
                    plist2_file.flush()
                    expected_plist2 = Plist(plist2_file.name)

                    received_plist1, received_plist2 = list(find_plists(target_dir, recursive=True))

                    assert received_plist1 == expected_plist1
                    assert received_plist2 == expected_plist2

    def test__target_dir_has_plist_files_in_root_and_subfolder__recursive_search__correct_plists_generated(self):
        plist1_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>a</key>
                        <string>one</string>
                    </dict>
                    </plist>
                    """

        plist2_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>b</key>
                        <integer>2</integer>
                    </dict>
                    </plist>
                    """

        with TemporaryDirectory() as target_dir:
            with open(Path(target_dir).joinpath('plist1.plist'), 'wb') as plist1_file:
                plist1_file.write(textwrap.dedent(plist1_xml).encode('utf8'))
                plist1_file.flush()
                expected_plist1 = Plist(plist1_file.name)

                subfolder = Path(target_dir).joinpath('sub')
                os.mkdir(subfolder)
                with open(subfolder.joinpath('plist2.plist'), 'wb') as plist2_file:
                    plist2_file.write(textwrap.dedent(plist2_xml).encode('utf8'))
                    plist2_file.flush()
                    expected_plist2 = Plist(plist2_file.name)

                    plists = find_plists(target_dir, recursive=True)
                    received_plist1 = next(plists)
                    received_plist2 = next(plists)

                    assert received_plist1 == expected_plist1
                    assert received_plist2 == expected_plist2