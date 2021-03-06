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
from unittest.mock import (
    MagicMock,
    patch,
)
from xml.etree import ElementTree as XmlElementTree

import pandas as pd

from pyplist.utils import (
    json_normalized_plist_dict,
    plist_dict_from_path,
)
from pyplist.core.plist import (
    Plist,
    ProgramPlist,
)


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

    def test__init__valid_xml_plist_file__correct_path_stored(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
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
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            received_plist = Plist(plist_file.name)

            self.assertEqual(received_plist.file_path, Path(plist_file.name).absolute())

    def test__init__valid_xml_plist_file__no_post_creation_modification__all_properties_correctly_set(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
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
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            received_plist = Plist(plist_file.name)

            # Check plist path
            plist_file_path = Path(plist_file.name).absolute()
            self.assertEqual(received_plist.file_path, plist_file_path)

            # Check plist name
            self.assertEqual(received_plist.name, plist_file_path.name.rstrip('.plist'))

            # Check plist file XMl source string property - we don't want to
            # compare this with the source XML string that was written to the
            # file, because of indentation and spacing differences in the two
            # strings. Instead we check that the plist properties dict
            # constructed from the XML string property is the same as the
            # plist dict expected from the original plist object
            received_plist_xml = received_plist.xml
            with NamedTemporaryFile('wb') as plist_file2:
                plist_file2.write(received_plist_xml.encode('utf8'))
                plist_file2.flush()

                plist_dict_from_received_plist_xml, _ = plist_dict_from_path(plist_file2.name)
                plist_dict_from_received_plist_xml = json_normalized_plist_dict(
                    plist_dict_from_received_plist_xml
                )

                self.assertEqual(
                    MappingProxyType(plist_dict_from_received_plist_xml),
                    expected_plist_dict
                )

            # Check plist XML version
            self.assertEqual(received_plist.plist_version, '1.0')

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

            # Check plist file summary dict
            expected_file_summary = MappingProxyType({
                'name': plist_file_path.name,
                'dir': os.path.dirname(plist_file_path),
                'exists': True,
                'type': 'xml',
                'plist_version': '1.0',
                'user': expected_file_owner,
                'group': expected_file_group,
                'size': expected_file_size,
                'mode': expected_file_mode,
                'created': expected_file_created.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'updated': expected_file_updated.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'accessed': expected_file_accessed.strftime('%Y-%m-%d %H:%M:%S.%f')
            })
            self.assertEqual(received_plist.file_summary, expected_file_summary)

    def test__repr__correct_repr_returned(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>a</key>
                        <string>one</string>
                    </dict>
                    </plist>
                    """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            received_plist = Plist(plist_file.name)

            expected_plist_repr = f'pyplist.core.plist.Plist("{plist_file.name}")'

            self.assertEqual(received_plist.__repr__(), expected_plist_repr)

    def test__property__xml__valid_xml_plist__prop_call_returns_correct_xml_str(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
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

    def test__property__xml__valid_binary_plist__prop_call_returns_null(self):
        # ``test_binary.plist`` is a static test binary plist file generated
        # converted from a valid XML plist file, with the same content as in
        # the test case above. So the ``Plist`` obtained from this file should
        # have the same data as in the test case above
        test_binary_plist_file = Path('tests/core/test_binary.plist')

        received_plist = Plist(test_binary_plist_file)

        self.assertIsNone(received_plist.xml)

    def test__property__plist_version__valid_xml_plist__prop_call_returns_correct_version_str(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>a</key>
                        <string>one</string>
                    </dict>
                    </plist>
                    """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            received_plist = Plist(plist_file.name)

            self.assertEqual(received_plist.plist_version, '1.0')

    def test__property__plist_version__valid_binary_plist__prop_call_returns_null(self):

        # ``test_binary.plist`` is a static test binary plist file generated
        # converted from a valid XML plist file, with the same content as in
        # the test case above. So the ``Plist`` obtained from this file should
        # have the same data as in the test case above
        test_binary_plist_file = Path('tests/core/test_binary.plist')

        with open(test_binary_plist_file, 'rb') as plist_file:
            received_plist = Plist(plist_file.name)
            self.assertIsNone(received_plist.plist_version)

    def test__property__properties__valid_plist_file_deleted_after_creation__prop_call_triggers_file_not_found_error(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
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
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            received_plist = Plist(plist_file.name)

            # Check the plist ``properties`` property call - it's a valid plist, so the
            # call should return something (we don't care what at this point)
            self.assertIsNotNone(received_plist.properties)

        # Temp. plist file is now gone - so the ``properties`` property call will trigger
        # a ``FileNotFoundError``
        with self.assertRaises(FileNotFoundError):
            received_plist.properties

    def test__property__properties__valid_plist_file_corrupted_after_creation__prop_call_triggers_plistlib_invalid_file_exception(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
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
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            received_plist = Plist(plist_file.name)

            # Check the plist ``properties`` property call - it's a valid plist, so the
            # call should return something (we don't care what at this point)
            self.assertIsNotNone(received_plist.properties)

            # Write some bad data to the plist file and check that the ``properties``
            # property call triggers a ``plistlib.InvalidFileException``
            plist_file.write('!BAD??%$@??DATA'.encode('utf8'))
            plist_file.flush()

            with self.assertRaises(plistlib.InvalidFileException):
                received_plist.properties

    def test__hash__valid_plist_file__correct_hash_returned(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
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
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
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
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
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
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            with NamedTemporaryFile('wb') as plist_file_copy:
                plist_file_copy.write(textwrap.dedent(plist_xml).encode('utf8'))
                plist_file_copy.flush()

                received_plist = Plist(plist_file.name)

                received_plist_copy = Plist(plist_file_copy.name)

                self.assertTrue(received_plist.__eq__(received_plist_copy))

    def test__eq__valid_plist_file__compared_with_a_different_valid_plist__false_returned(self):
        plist1_xml = """<?xml version="1.0" encoding="UTF-8"?>
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

        plist2_xml = """<?xml version="1.0" encoding="UTF-8"?>
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
            plist1_file.write(textwrap.dedent(plist1_xml).encode('utf8'))
            plist1_file.flush()

            with NamedTemporaryFile('wb') as plist2_file:
                plist2_file.write(textwrap.dedent(plist2_xml).encode('utf8'))
                plist2_file.flush()

                received_plist1 = Plist(plist1_file.name)

                received_plist2 = Plist(plist2_file.name)

                self.assertFalse(received_plist1.__eq__(received_plist2))


class TestProgramPlist(TestCase):

    def test__init__invalid_plist_file__plistlib_invalid_file_exception_raised(self):
        with self.assertRaises(plistlib.InvalidFileException):
            ProgramPlist(None)

        with self.assertRaises(plistlib.InvalidFileException):
            ProgramPlist(True)

        with self.assertRaises(plistlib.InvalidFileException):
            ProgramPlist(0)

        with self.assertRaises(plistlib.InvalidFileException):
            ProgramPlist('/some/invalid/plist.plist')

        with self.assertRaises(plistlib.InvalidFileException):
            ProgramPlist(['x'])

        with self.assertRaises(plistlib.InvalidFileException):
            ProgramPlist(('x',))

        with self.assertRaises(plistlib.InvalidFileException):
            ProgramPlist(set('x'))

        with self.assertRaises(plistlib.InvalidFileException):
            ProgramPlist(b'bytes')

    def test__init__valid_xml_plist_file__correct_path_stored(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>Label</key>
                        <string>test</string>
                        <key>Program</key>
                        <string>/test/program/test.plist</string>
                    </dict>
                    </plist>
                    """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            received_plist = ProgramPlist(plist_file.name)

            self.assertEqual(received_plist.file_path, Path(plist_file.name).absolute())

    def test__init__valid_xml_plist_file__no_post_creation_modification__all_properties_correctly_set(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>Label</key>
                        <string>test</string>
                        <key>Program</key>
                        <string>/test/program/test.plist</string>
                        <key>ProgramArguments</key>
                        <array>
                            <string>/test/program/test.plist</string>
                            <string>-t</string>
                            <string>/test/program/test.conf</string>
                        </array>
                    </dict>
                    </plist>
                    """

        expected_plist_dict = MappingProxyType({
            'Label': 'test',
            'Program': '/test/program/test.plist',
            'ProgramArguments': ['/test/program/test.plist', '-t', '/test/program/test.conf']
        })

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            received_plist = ProgramPlist(plist_file.name)

            # Check plist path
            plist_file_path = Path(plist_file.name).absolute()
            self.assertEqual(received_plist.file_path, plist_file_path)

            # Check plist name
            self.assertEqual(received_plist.name, plist_file_path.name.rstrip('.plist'))

            # Check plist program path
            self.assertEqual(
                received_plist.program_path,
                Path('/test/program/test.plist')
            )

            # Check plist program name
            self.assertEqual(received_plist.program_name, 'test.plist')

            # Check plist file XMl source string property - we don't want to
            # compare this with the source XML string that was written to the
            # file, because of indentation and spacing differences in the two
            # strings. Instead we check that the plist properties dict
            # constructed from the XML string property is the same as the
            # plist dict expected from the original plist object
            received_plist_xml = received_plist.xml
            with NamedTemporaryFile('wb') as plist_file2:
                plist_file2.write(received_plist_xml.encode('utf8'))
                plist_file2.flush()

                plist_dict_from_received_plist_xml, _ = plist_dict_from_path(plist_file2.name)
                plist_dict_from_received_plist_xml = json_normalized_plist_dict(
                    plist_dict_from_received_plist_xml
                )

                self.assertEqual(
                    MappingProxyType(plist_dict_from_received_plist_xml),
                    expected_plist_dict
                )

            # Check plist XML version
            self.assertEqual(received_plist.plist_version, '1.0')

            # Check plist properties dict
            self.assertEqual(received_plist.properties, expected_plist_dict)

            # Check plist properties hash (using the BLAKE2b hash function)
            expected_plist_str_series = pd.Series(
                [
                    'test',
                    '/test/program/test.plist',
                    "['/test/program/test.plist', '-t', '/test/program/test.conf']"
                ],
                index=['Label', 'Program', 'ProgramArguments']
            )

            expected_plist_bytes_series = expected_plist_str_series.apply(lambda val: val.encode('utf8'))
            blake2b_hasher = blake2b()
            for val in expected_plist_bytes_series:
                blake2b_hasher.update(val)

            expected_plist_hash = hash(blake2b_hasher.hexdigest())

            self.assertEqual(received_plist.hash, expected_plist_hash)

            # Check plist properties keys
            self.assertEqual(received_plist.keys, tuple(['Label', 'Program', 'ProgramArguments']))

            # Check plist properties values
            self.assertEqual(
                received_plist.values,
                tuple(
                    ['test', '/test/program/test.plist', ['/test/program/test.plist', '-t', '/test/program/test.conf']]
                )
            )

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

            # Check plist file summary dict
            expected_file_summary = MappingProxyType({
                'name': plist_file_path.name,
                'dir': os.path.dirname(plist_file_path),
                'exists': True,
                'type': 'xml',
                'plist_version': '1.0',
                'user': expected_file_owner,
                'group': expected_file_group,
                'size': expected_file_size,
                'mode': expected_file_mode,
                'created': expected_file_created.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'updated': expected_file_updated.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'accessed': expected_file_accessed.strftime('%Y-%m-%d %H:%M:%S.%f')
            })
            self.assertEqual(received_plist.file_summary, expected_file_summary)

    def test__property__program_path__valid_xml_plist__null_program_path__prop_call_returns_null(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>Label</key>
                        <string>test</string>
                    </dict>
                    </plist>
                    """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            received_plist = ProgramPlist(plist_file.name)

            self.assertIsNone(received_plist.program_path)

    def test__property__program_path__valid_xml_plist__prop_call_returns_correct_program_path(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>Label</key>
                        <string>test</string>
                        <key>Program</key>
                        <string>/test/program/test.plist</string>
                    </dict>
                    </plist>
                    """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            received_plist = ProgramPlist(plist_file.name)

            self.assertEqual(received_plist.program_path, Path('/test/program/test.plist'))

    def test__property__program_name__valid_xml_plist__null_program_path__prop_call_returns_null(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>Label</key>
                        <string>test</string>
                    </dict>
                    </plist>
                    """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            received_plist = ProgramPlist(plist_file.name)

            self.assertIsNone(received_plist.program_name)

    def test__property__program_name__valid_xml_plist__prop_call_returns_correct_program_name(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>Label</key>
                        <string>test</string>
                        <key>Program</key>
                        <string>/test/program/test.plist</string>
                    </dict>
                    </plist>
                    """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            received_plist = ProgramPlist(plist_file.name)

            self.assertEqual(received_plist.program_name, 'test.plist')

    def test__property__process_instances__valid_xml_plist__null_program_path__prop_call_returns_null(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>Label</key>
                        <string>test</string>
                    </dict>
                    </plist>
                    """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            received_plist = ProgramPlist(plist_file.name)

            self.assertIsNone(received_plist.program_path)

    def test__property__process_instances__valid_xml_plist__no_running_processes__prop_call_returns_empty_dict(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>Label</key>
                        <string>test</string>
                        <key>Program</key>
                        <string>/test/program/test.plist</string>
                    </dict>
                    </plist>
                    """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            with patch('pyplist.core.plist.process_instances_by_exec_path', MagicMock()) as mock_process_instances:
                mock_process_instances.iter.return_value = iter([])

                received_plist = ProgramPlist(plist_file.name)

                self.assertEqual(received_plist.process_instances, MappingProxyType({}))

    def test__property__process_instances__valid_xml_plist__one_running_process__prop_call_returns_correct_process_dict(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>Label</key>
                        <string>test</string>
                        <key>Program</key>
                        <string>/test/program/test.plist</string>
                    </dict>
                    </plist>
                    """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            mocked_process_dict = {'name': 'test_proc_name', 'pid': 100, 'exe': '/test/program/test.plist'}
            with patch('pyplist.core.plist.process_instances_by_exec_path', MagicMock()) as mock_process_instances:
                mock_process_instances.return_value = iter([mocked_process_dict])

                received_plist = ProgramPlist(plist_file.name)

                self.assertEqual(
                    received_plist.process_instances,
                    MappingProxyType(
                        {100: {'name': 'test_proc_name', 'pid': 100, 'exe': '/test/program/test.plist'}}
                    )
                )

    def test__property__is_running__valid_xml_plist__null_program_path__prop_call_returns_null(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>Label</key>
                        <string>test</string>
                    </dict>
                    </plist>
                    """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            received_plist = ProgramPlist(plist_file.name)

            self.assertIsNone(received_plist.is_running)

    def test__property__is_running__valid_xml_plist__no_running_processes__prop_call_returns_false(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>Label</key>
                        <string>test</string>
                        <key>Program</key>
                        <string>/test/program/test.plist</string>
                    </dict>
                    </plist>
                    """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            with patch('pyplist.core.plist.process_instances_by_exec_path', MagicMock()) as mock_process_instances:
                mock_process_instances.iter.return_value = iter([])

                received_plist = ProgramPlist(plist_file.name)

                self.assertFalse(received_plist.is_running)

    def test__property__is_running__valid_xml_plist__one_running_process__prop_call_returns_true(self):
        plist_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>Label</key>
                        <string>test</string>
                        <key>Program</key>
                        <string>/test/program/test.plist</string>
                    </dict>
                    </plist>
                    """

        with NamedTemporaryFile('wb') as plist_file:
            plist_file.write(textwrap.dedent(plist_xml).encode('utf8'))
            plist_file.flush()

            mocked_process_dict = {'name': 'test_proc_name', 'pid': 100, 'exe': '/test/program/test.plist'}
            with patch('pyplist.core.plist.process_instances_by_exec_path', MagicMock()) as mock_process_instances:
                mock_process_instances.return_value = iter([mocked_process_dict])

                received_plist = ProgramPlist(plist_file.name)

                self.assertTrue(received_plist.is_running)
