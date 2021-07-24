from hashlib import blake2b

from pyplist.utils import (
    blake2b_hash_iterable,
)

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
