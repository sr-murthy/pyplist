import os
import plistlib
import stat
import textwrap

from datetime import datetime
from hashlib import blake2b
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import MappingProxyType
from unittest import TestCase

import pandas as pd

from pandas.util.testing import assert_frame_equal

from pyplist.core.plist import Plist


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

            self.assertEqual(received_plist.file_path, Path(plist_file.name).absolute())
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

        expected_plist_dict = MappingProxyType({
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
            plist_file_path = Path(plist_file.name).absolute()
            self.assertEqual(received_plist.file_path, plist_file_path)

            # Check plist name
            self.assertEqual(received_plist.name, test_name)

            # Check plist properties dict
            self.assertEqual(received_plist.properties, expected_plist_dict)

            # Check plist properties hash (using the BLAKE2b hash function)
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

            # Check plist properties keys
            self.assertEqual(received_plist.keys, tuple(['a', 'b', 'c.d.e']))

            # Check plist properties values
            self.assertEqual(received_plist.values, tuple(['one', 2, False]))

            # Check plist exists
            self.assertTrue(received_plist.file_exists)

            # Check plist file type - the test plist here is XML
            self.assertEqual(received_plist.file_type, 'xml')

            # Check plist file mode
            expected_file_mode = stat.filemode(os.stat(plist_file_path).st_mode)
            self.assertEqual(received_plist.file_mode, expected_file_mode)

            # Check plist file size
            expected_file_size = os.path.getsize(plist_file_path)
            self.assertEqual(received_plist.file_size, expected_file_size)

            # Check plist creation time
            expected_file_created = datetime.utcfromtimestamp(
                os.path.getctime(plist_file_path))
            self.assertEqual(received_plist.file_created, expected_file_created)

            # Check plist updated time
            expected_file_updated = datetime.utcfromtimestamp(
                os.path.getmtime(plist_file_path))
            self.assertEqual(received_plist.file_updated, expected_file_updated)

            # Check plist accessed time
            expected_file_accessed = datetime.utcfromtimestamp(
                os.path.getatime(plist_file_path))
            self.assertEqual(received_plist.file_accessed, expected_file_accessed)

            # Check plist file owner login name
            expected_file_owner = plist_file_path.owner()
            self.assertEqual(received_plist.file_owner, expected_file_owner)

            # Check plist file group name
            expected_file_group = plist_file_path.group()
            self.assertEqual(received_plist.file_group, expected_file_group)

            # Check plist file summary dataframe
            expected_file_summary = pd.DataFrame([{
                'name': plist_file_path.name,
                'dir': os.path.dirname(plist_file_path),
                'exists': True,
                'type': 'xml',
                'user': expected_file_owner,
                'group': expected_file_group,
                'size': expected_file_size,
                'mode': expected_file_mode,
                'created': expected_file_created.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'updated': expected_file_updated.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'accessed': expected_file_accessed.strftime('%Y-%m-%d %H:%M:%S.%f')
            }])
            assert_frame_equal(received_plist.file_summary, expected_file_summary)

    def test__repr__no_name_set__correct_repr_returned(self):
        plist = """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                <plist version="1.0">
                <dict>
                    <key>a</key>
                    <string>one</string>
                </dict>
                </plist>
                """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist).encode('utf8'))
            plist_file.flush()

            received_plist = Plist(plist_file.name)

            expected_plist_repr = f'pyplist.core.plist.Plist("{plist_file.name}", name=None)'

            self.assertEqual(received_plist.__repr__(), expected_plist_repr)

    def test__repr__name_set__correct_repr_returned(self):
        plist = """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                <plist version="1.0">
                <dict>
                    <key>a</key>
                    <string>one</string>
                </dict>
                </plist>
                """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist).encode('utf8'))
            plist_file.flush()

            received_plist = Plist(plist_file.name, name='test_repr')

            expected_plist_repr = f'pyplist.core.plist.Plist("{plist_file.name}", name="test_repr")'

            self.assertEqual(received_plist.__repr__(), expected_plist_repr)

    def test_name_property_setter__valid_plist_created_with_no_name__prop_call_sets_new_name_set_correctly(self):
        plist = """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                <plist version="1.0">
                <dict>
                    <key>a</key>
                    <string>one</string>
                </dict>
                </plist>
                """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist).encode('utf8'))
            plist_file.flush()

            received_plist = Plist(plist_file.name, name=None)

            self.assertIsNone(received_plist.name)

            received_plist.name = 'new_name'

            self.assertEqual(received_plist.name, 'new_name')

    def test_name_property_setter__valid_plist_created_with_a_name__prop_call_sets_new_name_set_correctly(self):
        plist = """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                <plist version="1.0">
                <dict>
                    <key>a</key>
                    <string>one</string>
                </dict>
                </plist>
                """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist).encode('utf8'))
            plist_file.flush()

            received_plist = Plist(plist_file.name, name='initial_name')

            self.assertEqual(received_plist.name, 'initial_name')

            received_plist.name = 'new_name'

            self.assertEqual(received_plist.name, 'new_name')

    def test__properties_property__valid_plist_file_deleted_after_creation__prop_call_triggers_file_not_found_error(self):
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

            # Check the plist ``properties`` property call - it's a valid plist, so the
            # call should return something (we don't care what at this point)
            self.assertIsNotNone(received_plist.properties)

        # Temp. plist file is now gone - so the ``properties`` property call will trigger
        # a ``FileNotFoundError``
        with self.assertRaises(FileNotFoundError):
            received_plist.properties

    def test__properties_property__valid_plist_file_corrupted_after_creation__prop_call_triggers_plistlib_invalid_file_exception(self):
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

            # Check the plist ``properties`` property call - it's a valid plist, so the
            # call should return something (we don't care what at this point)
            self.assertIsNotNone(received_plist.properties)

            # Write some bad data to the plist file and check that the ``properties``
            # property call triggers a ``plistlib.InvalidFileException``
            plist_file.write('!BAD£%$@£DATA'.encode('utf8'))
            plist_file.flush()

            with self.assertRaises(plistlib.InvalidFileException):
                received_plist.properties

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

            # Check plist properties hash (using the BLAKE2b hash function)
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
