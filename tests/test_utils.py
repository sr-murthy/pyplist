import plistlib
import textwrap

from hashlib import blake2b
from pathlib import Path
from plistlib import InvalidFileException
from xml.parsers.expat import ExpatError

from pyplist.utils import (
    blake2b_hash_iterable,
    json_normalized_plist,
    plist_from_path,
)

from tempfile import NamedTemporaryFile
from unittest import TestCase


class TestBlake2bHashIterable(TestCase):

    def test__bool_iterable__correct_hash_computed(self):

        iterable = [True, False, True, False, False]

        bytes_iterable = [b'True', b'False', b'True', b'False', b'False']

        hasher = blake2b()

        for val in bytes_iterable:
            hasher.update(val)

        expected_hash = hasher.hexdigest()

        received_hash = blake2b_hash_iterable(iterable)

        self.assertEqual(received_hash, expected_hash)

    def test__int_iterable__correct_hash_computed(self):

        iterable = [0, -10 ** 6, 17, 250000, -1078]

        bytes_iterable = [b'0', b'-1000000', b'17', b'250000', b'-1078']

        hasher = blake2b()

        for val in bytes_iterable:
            hasher.update(val)

        expected_hash = hasher.hexdigest()

        received_hash = blake2b_hash_iterable(iterable)

        self.assertEqual(received_hash, expected_hash)

    def test__float_iterable__correct_hash_computed(self):

        iterable = [0.0, -100000.0, 1.7, 25000.0, -107.8]

        bytes_iterable = [b'0.0', b'-100000.0', b'1.7', b'25000.0', b'-107.8']

        hasher = blake2b()

        for val in bytes_iterable:
            hasher.update(val)

        expected_hash = hasher.hexdigest()

        received_hash = blake2b_hash_iterable(iterable)

        self.assertEqual(received_hash, expected_hash)

    def test__complex_iterable__correct_hash_computed(self):

        iterable = [0j, -100000.0 + 0j, 1 + 7j, 250000 + 0j, 107 - 80j]

        bytes_iterable = [b'0j', b'(-100000+0j)', b'(1+7j)', b'(250000+0j)', b'(107-80j)']

        hasher = blake2b()

        for val in bytes_iterable:
            hasher.update(val)

        expected_hash = hasher.hexdigest()

        received_hash = blake2b_hash_iterable(iterable)

        self.assertEqual(received_hash, expected_hash)

    def test__string_iterable__ascii_chars_only__correct_hash_computed(self):

        iterable = ['this', 'is', '@', 'uNiT', 'TEST!!']

        bytes_iterable = [b'this', b'is', b'@', b'uNiT', b'TEST!!']

        hasher = blake2b()

        for val in bytes_iterable:
            hasher.update(val)

        expected_hash = hasher.hexdigest()

        received_hash = blake2b_hash_iterable(iterable)

        self.assertEqual(received_hash, expected_hash)

    def test__string_iterable__mixed_chars_with_unicode__correct_hash_computed(self):

        iterable = ['thïs', 'iš', '@', 'uÑiT', 'TEST!!']

        bytes_iterable = [b'th\xc3\xafs', b'i\xc5\xa1', b'@', b'u\xc3\x91iT', b'TEST!!']

        hasher = blake2b()

        for val in bytes_iterable:
            hasher.update(val)

        expected_hash = hasher.hexdigest()

        received_hash = blake2b_hash_iterable(iterable)

        self.assertEqual(received_hash, expected_hash)

    def test__bytes_iterable__correct_hash_computed(self):

        iterable = [b'True', b'10', b'-100000.0', b'1-7j', b'T\xc3\xab\xc5\x9bt']

        bytes_iterable = [b'True', b'10', b'-100000.0', b'1-7j', b'T\xc3\xab\xc5\x9bt']

        hasher = blake2b()

        for val in bytes_iterable:
            hasher.update(val)

        expected_hash = hasher.hexdigest()

        received_hash = blake2b_hash_iterable(iterable)

        self.assertEqual(received_hash, expected_hash)

    def test__mixed_iterable__correct_hash_computed(self):

        iterable = [True, 10, -100000.0, 1 - 7j, 'Tëšt', b'bytes']

        bytes_iterable = [b'True', b'10', b'-100000.0', b'(1-7j)', b'T\xc3\xab\xc5\xa1t', b'bytes']

        hasher = blake2b()

        for val in bytes_iterable:
            hasher.update(val)

        expected_hash = hasher.hexdigest()

        received_hash = blake2b_hash_iterable(iterable)

        self.assertEqual(received_hash, expected_hash)


class PlistFromPath(TestCase):

    def test__non_existent_plist_file_path__file_not_found_error_raised(self):
        with self.assertRaises(FileNotFoundError):
            plist_from_path('/non/existent/plist.plist')

    def test__invalid_binary_plist_file_path__invalid_file_exception_raised(self):
        binary_plist = (
            """
            <?xml version="1.0" encoding="UTF-8">?
            <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
            <plist version="1.0">
            <dict>
                <key>a</key>
                <strings>one</string>
            </dict>
            </plist>
            """
        )

        with NamedTemporaryFile('wb') as binary_plist_file:
            plistlib.dump(binary_plist.encode('utf8'), binary_plist_file, fmt=plistlib.FMT_BINARY)
            binary_plist_file.flush()

            with self.assertRaises(InvalidFileException):
                plist_from_path(binary_plist_file.name)

    def test__invalid_xml_plist_file_path__invalid_file_exception_raised(self):
        xml_plist = textwrap.dedent("""<?xml version="1.0" encoding="UTF-8">?
                                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                                    <plist version="1.0">
                                    <dict>
                                        <key>a</key>
                                        <strings>one</string>
                                    </dict>
                                    </plist>
                                    """)

        with NamedTemporaryFile('wb') as xml_plist_file:
            plistlib.dump(xml_plist, xml_plist_file, fmt=plistlib.FMT_XML)
            xml_plist_file.flush()

            with self.assertRaises(InvalidFileException):
                plist_from_path(xml_plist_file.name)


    def test__valid_xml_plist_file_path__correct_plist_dict_returned(self):
        expected = {
            'a': 'one',
            'b': 2,
            'c': {
                'd': {
                    'e': False
                }
            }
        }

        xml_plist = textwrap.dedent("""<?xml version="1.0" encoding="UTF-8"?>
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
                    """)

        with NamedTemporaryFile('wb') as xml_plist_file:
            xml_plist_file.write(xml_plist.encode('utf8'))
            xml_plist_file.flush()

            received = plist_from_path(xml_plist_file.name)

            self.assertEqual(received, expected)

    def test__valid_binary_plist_file_path__correct_plist_dict_returned(self):
        expected = {
            'a': 'one',
            'b': 2,
            'c': {
                'd': {
                    'e': False
                }
            }
        }

        # ``test_binary.plist`` is a static test binary plist file generated
        # converted from a valid XML plist file, with the same content as in
        # the test case above. So the ``Plist`` obtained from this file should
        # have the same data as in the test case above
        test_binary_plist_file = Path('tests/test_binary.plist')
        received = plist_from_path(test_binary_plist_file)

        self.assertEqual(received, expected)


class JsonNormalizedPlist(TestCase):

    def test__hierarchical_plist_dict__normalized_plist_dict_returned(self):

        plist_dict = {
            'a': 'one',
            'b': 2,
            'c': {
                'd': {
                    'e': False
                }
            }
        }

        expected = {
            'a': 'one',
            'b': 2,
            'c.d.e': False
        }

        received = json_normalized_plist(plist_dict)

        self.assertEqual(received, expected)
