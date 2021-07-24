__all__ = [
    'json_normalized_plist',
    'Plist'
]

import io
import pathlib
import plistlib


from pathlib import Path
from types import MappingProxyType
from typing import (
    Union,
)

import pandas as pd

from pandas import json_normalize


def plist_from_path(plist_path: Union[str, pathlib.Path]) -> dict:
    """
    Returns a plist dict from a plist path string or ``pathlib.Path`` object.

    Parameters
    ----------
    plist_path : ``str`` or ``pathlib.Path``

    Returns
    -------
    A plist as a plain dict (loaded from the built-in ``plistlib.load``)

    Raises
    ------
    ValueError
        If the file path is invalid or doesn't exist
    """
    try:
        plist_path = Path(plist_path)
    except TypeError:
        raise ValueError('Invalid file path')
    else:
        try:
            with open(plist_path, 'rb') as plist_file:
               plist = plistlib.load(plist_file)
        except FileNotFoundError:
            raise ValueError('Nonexistent file')
        else:
            return plist

def json_normalized_plist(plist: dict) -> pd.Series:
    """
    Returns a Pandas series representation of a plist dict, with values indexed
    by the plist keys. The plist keys are generated from a flattening of the
    hierarchies in the plist dict.

    Parameters
    ----------
    plist_dict : ``dict``
        A plist dict - expected to be loaded from a valid plist file

    Returns
    -------
    Pandas series of plist values, indexed by flattened plist keys
    """
    plist_df = json_normalize(plist).T
    plist_df = plist_df.copy(deep=True)
    plist_df.columns = pd.Index(['value'])

    return plist_df['value']


class Plist:
    """
    Basic Plist class - stores and exposes the plist data, and, if a plist
    file path was provided, the path. Implements ``__eq__`` to allow plist
    objects to be compared for equality.
    """

    def __init__(
        self,
        plist_input: Union[str, io.BufferedReader, dict]
    ) -> None:
        """
        Class initialiser - accepts either a plist file path string, or a plist file
        IO buffer, or a dict preloaded from a plist file.
        """
        self._data = None
        self._path = None

        if isinstance(plist_input, str):
            try:
                plist_dict = plist_from_path(plist_input)
            except ValueError as e:
                raise
            else:
                self._data = json_normalized_plist(plist_dict)
                self._path = Path(plist_input)
        elif isinstance(plist_input, io.BufferedReader):
            self._data = json_normalized_plist(plistlib.load(plist_input))

    @property
    def data(self):
        return self._data

    @property
    def path(self):
        return self._path

    def __eq__(self, other_plist):
        return self._data.equals(other_plist._data)
