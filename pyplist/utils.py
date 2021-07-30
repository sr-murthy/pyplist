__all__ = [
    'json_normalized_plist_dict',
    'plist_dict_from_path',
    'process_instances_by_exec_path',
    'process_instances_by_name',
    'blake2b_hash_iterable',
    'INVALID_PLIST_FILE_MSG',
]


import plistlib
import textwrap

from hashlib import (
    blake2b,
)
from pathlib import Path
from xml.parsers.expat import ExpatError

import pandas as pd
import psutil


INVALID_PLIST_FILE_MSG = textwrap.dedent(
    """
    Invalid plist file - the plist file you are trying to load is not a valid
    binary or XML plist file. Use plutil (MacOS, OS X, BSD) or plistutil
    (Debian, Ubuntu) to check the correctness of the source file.
    """
)


def blake2b_hash_iterable(iterable):
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
    ``iterable`` : An iterable composed of Python primitive values

    Returns
    -------
    ``str`` :
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


def plist_dict_from_path(plist_path):
    """
    Returns a plist dict and the underlying file type (``'xml'`` or
    ``'binary'``) from a plist file path string, or ``pathlib.Path`` object.

    Parameters
    ----------
    ``plist_path`` : ``str`` or ``pathlib.Path``

    Returns
    -------
    ``dict`` :
        A plist dict and the underlying file type (``'xml'`` or ``'binary'``)

    Raises
    ------
    ``plistlib.InvalidFileException`` :
        If the file path is invalid, i.e. not a valid path string or
        path object, or if the target file is corruped in some way
    ``FileNotFoundError`` :
        If the file path does not exist
    """
    try:
        plist_path = Path(plist_path)
    except TypeError:
        raise plistlib.InvalidFileException(INVALID_PLIST_FILE_MSG)
    else:
        try:
            with open(plist_path.resolve(), 'rb') as plist_file:
                plist = plistlib.load(plist_file, fmt=plistlib.FMT_BINARY)

                # A corrupted or invalid binary plist file may not necessarily
                # trigger an ``plistlib.plistlib.InvalidFileException`` - here,
                # ``plist`` might just end up as a malformed bytes object, so
                # in that case we need to manually trigger the
                # ``plistlib.InvalidFileException``
                if not isinstance(plist, dict):
                    raise plistlib.InvalidFileException(INVALID_PLIST_FILE_MSG)
        except FileNotFoundError as e:
            raise e
        except (ExpatError, plistlib.InvalidFileException):
            try:
                with open(plist_path, 'rb') as plist_file:
                    plist = plistlib.load(plist_file, fmt=plistlib.FMT_XML)

                    # A corrupted or invalid XML plist file may not necessarily
                    # trigger an ``plistlib.plistlib.InvalidFileException`` -
                    # here, ``plist`` might just end up as a malformed XML
                    # string, so in that case we need to manually trigger the
                    # ``plistlib.InvalidFileException``
                    if not isinstance(plist, dict):
                        raise plistlib.InvalidFileException
            except (ExpatError, plistlib.InvalidFileException):
                raise plistlib.InvalidFileException(INVALID_PLIST_FILE_MSG)
            else:
                return plist, 'xml'
        else:
            return plist, 'binary'


def json_normalized_plist_dict(plist_dict):
    """
    Returns a plist dict with JSON normalised keys - this means the keys are
    generated by flattening the hierarchies within the original plist, and
    key names indicate their position in the original hierarchy via dot
    separation, e.g.
    ::

        {'x': {'y': {'z': 1}}} -> {'x.y.z': 1}

    The input plist dict must be one loaded from a valid plist file - a
    non-plist dict or mapping may not produce the expected results.

    Parameters
    ----------
    ``plist_dict`` : ``typing.Mapping``
        A plist dict - expected to be loaded from a valid plist file

    Returns
    -------
    ``types.MappingProxyType`` :
        Read-only dict of the given plist, with JSON normalised keys
    """
    plist_df = pd.json_normalize(plist_dict).T
    plist_df = plist_df.copy(deep=True)
    plist_df.columns = pd.Index(['value'])

    return plist_df['value'].to_dict()


def process_instances_by_name(process_name):
    """
    Generates read-only versions of ``psutil`` process instance dicts for
    processes sharing a common process name. The search is based on
    an exact match for the process name.

    Parameters
    ----------

    ``process_name`` : ``str``
        The process name to look for - the search will be based on an exact
        match, e.g. ``bash`` will be treated differently from ``Bash``

    Yields
    ------
    ``types.MappingProxyType`` :
        Read-only dict of a ``psutil`` process instance dict
    """
    for proc in psutil.process_iter():
       try:
           pinfo = proc.as_dict()

           if process_name == pinfo['name']:
               yield pinfo
       except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) :
           pass


def process_instances_by_exec_path(exec_path):
    """
    Generates read-only versions of ``psutil`` process instance dicts for
    processes sharing a common executable path.

    Parameters
    ----------

    ``exec_path`` : ``str``, ``pathlib.Path``
        The process name to look for - the search will be based on an exact
        match, e.g. ``bash`` will be treated differently from ``Bash``

    Yields
    ------
    ``types.MappingProxyType`` :
        Read-only dict of a ``psutil`` process instance dict
    """
    for proc in psutil.process_iter():
       try:
           pinfo = proc.as_dict()

           if str(exec_path) == pinfo['exe']:
               yield pinfo
       except (psutil.NoSuchProcess, psutil.AccessDenied , psutil.ZombieProcess) :
           pass