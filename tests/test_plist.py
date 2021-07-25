import plistlib

from hashlib import blake2b
from plistlib import InvalidFileException
from xml.parsers.expat import ExpatError

from pyplist.utils import (
    blake2b_hash_iterable,
    json_normalized_plist,
    plist_from_path,
)
from pyplist.plist import Plist

from tempfile import NamedTemporaryFile
from unittest import TestCase


class TestPlist(TestCase):

    def test__init__invalid_plist_input__raise_value_error(self):
        with self.assertRaises(ValueError):
            Plist(None)

        with self.assertRaises(ValueError):
            Plist(0)

        with self.assertRaises(ValueError):
            Plist(0.0)

        with self.assertRaises(ValueError):
            Plist(['x'])

        with self.assertRaises(ValueError):
            Plist(('x',))

        with self.assertRaises(ValueError):
            Plist(set('x'))
