import os
import plistlib
import textwrap

from datetime import datetime
from hashlib import blake2b
from pathlib import Path
from pyplist.plist import Plist
from tempfile import NamedTemporaryFile
from types import MappingProxyType
from unittest import TestCase

import pandas as pd


class TestPlist(TestCase):

    def test__init__invalid_plist_file__plistlib_invalid_file_exception_raised(self):
        with self.assertRaises(plistlib.InvalidFileException):
            Plist(None)

        with self.assertRaises(plistlib.InvalidFileException):
            Plist(True)

        with self.assertRaises(plistlib.InvalidFileException):
            Plist(0)

        with self.assertRaises(plistlib.InvalidFileException):
            Plist('/some/invalid/plist.plist')

        with self.assertRaises(plistlib.InvalidFileException):
            Plist(['x'])

        with self.assertRaises(plistlib.InvalidFileException):
            Plist(('x',))

        with self.assertRaises(plistlib.InvalidFileException):
            Plist(set('x'))

        with self.assertRaises(plistlib.InvalidFileException):
            Plist(b'bytes')

    def test__init__valid_plist_file__correct_path_and_name_stored(self):
        plist = """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                <plist version="1.0">
                <dict>
                    <key>a</key>
                    <string>one</string>
                    <key>b</key>
                    <integer>2</integer>
                    <key>c</key>
                    <dict>
                        <key>d</key>
                        <dict>
                            <key>e</key>
                            <false/>
                        </dict>
                    </dict>
                </dict>
                </plist>
                """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist).encode('utf8'))
            plist_file.flush()

            test_name = 'test__init__valid_plist_file__path_and_name_stored'
            received_plist = Plist(plist_file.name, name=test_name)

            self.assertEqual(received_plist.path, Path(plist_file.name))
            self.assertEqual(received_plist.name, test_name)

    def test__init__valid_plist_file__no_post_creation_modification__all_properties_correctly_set(self):
        plist = """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                <plist version="1.0">
                <dict>
                    <key>a</key>
                    <string>one</string>
                    <key>b</key>
                    <integer>2</integer>
                    <key>c</key>
                    <dict>
                        <key>d</key>
                        <dict>
                            <key>e</key>
                            <false/>
                        </dict>
                    </dict>
                </dict>
                </plist>
                """

        expected_plist_data = MappingProxyType({
            'a': 'one',
            'b': 2,
            'c.d.e': False
        })

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist).encode('utf8'))
            plist_file.flush()

            test_name = 'test__post__init__valid_plist_file__all_properties_correctly_set'
            received_plist = Plist(plist_file.name, name=test_name)

            # Check plist path
            self.assertEqual(received_plist.path, Path(plist_file.name))

            # Check plist name
            self.assertEqual(received_plist.name, test_name)

            # Check plist data
            self.assertEqual(received_plist.data, expected_plist_data)

            # Check plist data hash (using the BLAKE2b hash function)
            expected_plist_str_series = pd.Series(
                ['one', '2', 'False'],
                index=['a', 'b', 'c.d.e']
            )

            expected_plist_bytes_series = expected_plist_str_series.apply(lambda val: val.encode('utf8'))
            blake2b_hasher = blake2b()
            for val in expected_plist_bytes_series:
                blake2b_hasher.update(val)

            expected_plist_hash = hash(blake2b_hasher.hexdigest())

            self.assertEqual(received_plist.hash, expected_plist_hash)

            # Check plist data keys
            self.assertEqual(received_plist.keys, tuple(['a', 'b', 'c.d.e']))

            # Check plist data values
            self.assertEqual(received_plist.values, tuple(['one', 2, False]))

            # Check plist exists
            self.assertTrue(received_plist.exists)

            # Check plist creation time
            expected_created = datetime.utcfromtimestamp(
                os.path.getctime(Path(plist_file.name))).strftime('%Y-%m-%d %H:%M:%S')
            self.assertEqual(received_plist.created, expected_created)

            # Check plist updated time
            expected_updated = datetime.utcfromtimestamp(
                os.path.getmtime(Path(plist_file.name))).strftime('%Y-%m-%d %H:%M:%S')
            self.assertEqual(received_plist.updated, expected_updated)

            # Check plist accessed time
            expected_accessed = datetime.utcfromtimestamp(
                os.path.getatime(Path(plist_file.name))).strftime('%Y-%m-%d %H:%M:%S')
            self.assertEqual(received_plist.accessed, expected_accessed)

            # Check plist file owner login name
            self.assertEqual(received_plist.owner, Path(plist_file.name).owner())

            # Check plist file gid group name
            self.assertEqual(received_plist.group, Path(plist_file.name).group())

    def test__data_property__valid_plist_file_deleted_after_creation__data_prop_call_triggers_file_not_found_error(self):
        plist = """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                <plist version="1.0">
                <dict>
                    <key>a</key>
                    <string>one</string>
                    <key>b</key>
                    <integer>2</integer>
                    <key>c</key>
                    <dict>
                        <key>d</key>
                        <dict>
                            <key>e</key>
                            <false/>
                        </dict>
                    </dict>
                </dict>
                </plist>
                """

        received_plist = None

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist).encode('utf8'))
            plist_file.flush()

            received_plist = Plist(plist_file.name)

            # Check the plist ``data`` property call - it's a valid plist, so the
            # call should return something (we don't care what at this point)
            self.assertIsNotNone(received_plist.data)

        # Temp. plist file is now gone - so the ``data`` property call will trigger
        # a ``FileNotFoundError``
        with self.assertRaises(FileNotFoundError):
            received_plist.data

    def test__data_property__valid_plist_file_corrupted_after_creation__data_prop_call_triggers_plistlib_invalid_file_exception(self):
        plist = """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                <plist version="1.0">
                <dict>
                    <key>a</key>
                    <string>one</string>
                    <key>b</key>
                    <integer>2</integer>
                    <key>c</key>
                    <dict>
                        <key>d</key>
                        <dict>
                            <key>e</key>
                            <false/>
                        </dict>
                    </dict>
                </dict>
                </plist>
                """

        received_plist = None

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist).encode('utf8'))
            plist_file.flush()

            received_plist = Plist(plist_file.name)

            # Check the plist ``data`` property call - it's a valid plist, so the
            # call should return something (we don't care what at this point)
            self.assertIsNotNone(received_plist.data)

            # Write some bad data to the plist file and check that the ``data``
            # property call triggers a ``plistlib.InvalidFileException``
            plist_file.write('!BAD£%$@£DATA'.encode('utf8'))
            plist_file.flush()

            with self.assertRaises(plistlib.InvalidFileException):
                received_plist.data

    def test__hash__valid_plist_file__correct_hash_returned(self):
        plist = """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                <plist version="1.0">
                <dict>
                    <key>a</key>
                    <string>one</string>
                    <key>b</key>
                    <integer>2</integer>
                    <key>c</key>
                    <dict>
                        <key>d</key>
                        <dict>
                            <key>e</key>
                            <false/>
                        </dict>
                    </dict>
                </dict>
                </plist>
                """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist).encode('utf8'))
            plist_file.flush()

            received_plist = Plist(plist_file.name)

            # Check plist data hash (using the BLAKE2b hash function)
            expected_plist_str_series = pd.Series(
                ['one', '2', 'False'],
                index=['a', 'b', 'c.d.e']
            )

            expected_plist_bytes_series = expected_plist_str_series.apply(lambda val: val.encode('utf8'))
            blake2b_hasher = blake2b()
            for val in expected_plist_bytes_series:
                blake2b_hasher.update(val)

            expected_plist_hash = hash(blake2b_hasher.hexdigest())

            self.assertEqual(received_plist.__hash__(), expected_plist_hash)

    def test__eq__valid_plist_file__compared_with_copy__true_returned(self):
        plist = """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                <plist version="1.0">
                <dict>
                    <key>a</key>
                    <string>one</string>
                    <key>b</key>
                    <integer>2</integer>
                    <key>c</key>
                    <dict>
                        <key>d</key>
                        <dict>
                            <key>e</key>
                            <false/>
                        </dict>
                    </dict>
                </dict>
                </plist>
                """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist).encode('utf8'))
            plist_file.flush()

            with NamedTemporaryFile('wb') as plist_file_copy:
                plist_file_copy.write(textwrap.dedent(plist).encode('utf8'))
                plist_file_copy.flush()

                received_plist = Plist(plist_file.name)

                received_plist_copy = Plist(plist_file_copy.name)

                self.assertTrue(received_plist.__eq__(received_plist_copy))

    def test__eq__valid_plist_file__compared_with_a_different_valid_plist__false_returned(self):
        plist1 = """<?xml version="1.0" encoding="UTF-8"?>
                 <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                 <plist version="1.0">
                 <dict>
                     <key>a</key>
                     <string>one</string>
                     <key>b</key>
                     <integer>2</integer>
                     <key>c</key>
                     <dict>
                         <key>d</key>
                         <dict>
                             <key>e</key>
                             <false/>
                         </dict>
                     </dict>
                 </dict>
                 </plist>
                 """

        plist2 = """<?xml version="1.0" encoding="UTF-8"?>
                 <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                 <plist version="1.0">
                 <dict>
                     <key>x</key>
                     <dict>
                         <key>y</key>
                         <true/>
                     </dict>
                     <key>z</key>
                     <real>-10209.4324</real>
                 </dict>
                 </plist>
                 """

        with NamedTemporaryFile('wb') as plist1_file:
            plist1_file.write(textwrap.dedent(plist1).encode('utf8'))
            plist1_file.flush()

            with NamedTemporaryFile('wb') as plist2_file:
                plist2_file.write(textwrap.dedent(plist2).encode('utf8'))
                plist2_file.flush()

                received_plist1 = Plist(plist1_file.name)

                received_plist2 = Plist(plist2_file.name)

                self.assertFalse(received_plist1.__eq__(received_plist2))
