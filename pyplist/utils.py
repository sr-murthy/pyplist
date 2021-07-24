__all__ = [
    'json_normalized_plist',
    'plist_from_path',
    'blake2b_hash_iterable',
]


import pathlib
import plistlib
import types
import typing


from hashlib import (
    blake2b,
)
from pathlib import Path
from plistlib import InvalidFileException
from typing import (
    Iterable,
    Mapping,
    Union,
)
from xml.parsers.expat import ExpatError

import pandas as pd

from pandas import json_normalize


def blake2b_hash_iterable(
    iterable: Iterable[Union[bool, int, float, complex, str, bytes]]
) -> str:
    """
    Hashes an iterable of Python primitive values, using the Python
    implementation of the BLAKE2b cryptographic hash function.

    https://docs.python.org/3/library/hashlib.html#blake2
    https://blake2.net/
    https://tools.ietf.org/html/rfc7693.html

    The primitive values can be a mixture of booleans, integers, floats,
    complex numbers, strings, or bytes objects.

    Parameters
    ----------
    iterable : An iterable composed of Python primitive values

    Returns
    -------
    The BLAKE2b hash string (message digest) of the iterable
    """
    ser = iterable

    if not isinstance(iterable, pd.Series):
        ser = pd.Series(iterable)

    def to_bytes(val):
        if isinstance(val, bytes):
            return val
        return str(val).encode('utf8')

    bytes_iterable = ser.transform(to_bytes)

    hasher = blake2b()

    for val in bytes_iterable:
        hasher.update(val)

    return hasher.hexdigest()


def plist_from_path(plist_path: Union[str, Path]) -> dict:
    """
    Returns a plist dict from a binary or XML plist file path string, or
    ``pathlib.Path`` object.

    Parameters
    ----------
    plist_path : ``str`` or ``pathlib.Path``

    Returns
    -------
    A plist dict.

    Raises
    ------
    InvalidFileException
        If the file path is invalid, i.e. not a valid path string or
        path object, or if the target file is corruped in some way
    FileNotFoundError
        If the file path does not exist
    """
    try:
        plist_path = Path(plist_path)
    except TypeError:
        raise InvalidFileException('Invalid file path')
    else:
        try:
            with open(plist_path, 'rb') as plist_file:
                plist = plistlib.load(plist_file, fmt=plistlib.FMT_BINARY)

                # A corrupted or invalid binary plist file may not necessarily
                # trigger an ``plistlib.InvalidFileException`` - here, ``plist``
                # might just end up as a malformed bytes object, so in that case
                # we need to manually trigger the ``InvalidFileException``
                if not isinstance(plist, dict):
                    raise InvalidFileException(
                        'Not a valid plist file - the plist file you are trying '
                        'to load is not a valid binary or XML plist file. '
                        'Use plutil (MacOS, OS X, BSD) or plistutil (Debian, '
                        'Ubuntu) to check the correctness of the source file.'
                    )
        except FileNotFoundError as e:
            raise
        except (ExpatError, InvalidFileException):
            try:
                with open(plist_path, 'rb') as plist_file:
                    plist = plistlib.load(plist_file, fmt=plistlib.FMT_XML)

                    # A corrupted or invalid XML plist file may not necessarily
                    # trigger an ``plistlib.InvalidFileException`` - here, ``plist``
                    # might just end up as a malformed XML string, so in that case
                    # we need to manually trigger the ``InvalidFileException``
                    if not isinstance(plist, dict):
                        raise InvalidFileException
            except (ExpatError, InvalidFileException):
                raise InvalidFileException(
                    'Not a valid plist file - the plist file you are trying '
                    'to load is not a valid binary or XML plist file. '
                    'Use plutil (MacOS, OS X, BSD) or plistutil (Debian, '
                    'Ubuntu) to check the correctness of the source file.'
                )
            else:
                return plist
        else:
            return plist

def json_normalized_plist(plist: Mapping) -> dict:
    """
    Returns a plist dict with JSON normalised keys - this means the keys are
    generated by flattening the hierarchies within the original plist, and
    key names indicate their position in the original hierarchy via dot
    separation, e.g.
    ::

        {'x': {'y': {'z': 1}}} -> {'x.y.z': 1}

    The plist must be one loaded from a valid plist file - a non-plist dict
    or mapping may not produce the expected results.

    Parameters
    ----------
    plist_dict : ``typing.Mapping``
        A plist dict - expected to be loaded from a valid plist file

    Returns
    -------
    Read-only dict of the given plist, with JSON normalised keys
    """
    plist_df = json_normalize(plist).T
    plist_df = plist_df.copy(deep=True)
    plist_df.columns = pd.Index(['value'])

    return plist_df['value'].to_dict()