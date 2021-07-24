__all__ = [
    'Plist'
]


import io
import pathlib
import types

from pathlib import Path

from types import MappingProxyType
from typing import (
    Any,
    Mapping,
    Tuple,
    Union,
)

import pandas as pd

import plist_utils

from .utils import (
    json_normalized_plist,
    plist_from_path,
    blake2b_hash_iterable,
)


class Plist:
    """
    Basic Plist class - stores and exposes the plist data as a read-only,
    JSON normalized dict, and, if a plist file path was provided, the path.

    Implements ``__hash__`` to allow hashing of the plist data, and
    ``__eq__`` to allow two plist objects to be compared for equality.
    """
    def __init__(
        self,
        plist_input: Union[str, Path, io.BufferedReader, bytes, dict],
        name=None
    ) -> None:
        """
        Class initialiser - accepts either a plist file path string or a
        ``pathlib.Path`` object, or a plist binary file IO buffer which is open
        and ready for reading, or a bytes object representing the entire
        binary content of a plist file, or a dict preloaded from a plist file.
        """
        self._data = None
        self._path = None
        self._name = name

        if isinstance(plist_input, str) or isinstance(plist_input, Path):
            plist_dict = plist_from_path(plist_input)

            self._data = MappingProxyType(
                json_normalized_plist(plist_dict)
            )
            self._path = Path(plist_input)
        elif isinstance(plist_input, io.BufferedReader):
            self._data = MappingProxyType(
                json_normalized_plist(plistlib.load(plist_input))
            )

            self._path = Path(plist_input.name)
        elif isinstance(plist_input, bytes):
            self._data = MappingProxyType(
                json_normalized_plist(plistlib.loads(plist_input))
            )
        elif isinstance(plist_input, Mapping):
            self._data = MappingProxyType(plist_input)
        else:
            raise ValueError(
                'The plist input must be a plist file path string or '
                '``pathlib.Path`` object, an open plist binary file buffer, '
                'a bytes object for a plist binary file, or a plist dict'
            )


    @property
    def name(self):
        return self._name

    @property
    def data(self) -> MappingProxyType:
        """
        Property - returns the read-only, JSON-normalized plist dict.

        Returns
        -------
        The read-only, JSON-normalized plist dict.
        """
        return self._data

    @property
    def keys(self) -> Tuple[str]:
        """
        Property - returns a tuple of the plist keys.

        Returns
        -------
        Tuple of plist keys
        """
        return tuple(self._data.keys())

    @property
    def values(self) -> Tuple[Any]:
        return tuple(self._data.values())
    

    @property
    def path(self) -> Union[None, Path]:
        """
        Property - returns plist file path, if one was provided.

        Returns
        -------
        Null if no file path was provided in initialisation, or a
        ``Pathlib.Path`` object containing the file path.
        """
        return self._path

    def __hash__(self) -> int:
        """
        Returns the integer hash of the BLAKE2b hash of the plist data - this
        is computed by taking the BLAKE2b hash of the sorted Pandas series of
        values, and then taking the hash of the BLAKE2b hash value.

        Returns
        -------

        The integer hash of the BLAKE2b hash value of the plist values
        """
        plist_series = pd.Series(self._data).sort_index().transform(str)

        return hash(blake2b_hash_iterable(plist_series))

    @property
    def hash(self):
        return self.__hash__()

    def __eq__(self, other_plist: plist_utils.plist.Plist) -> bool:
        """
        ``Plist`` object equality comparator - equality is based on equality of
        the Pandas series of values for the two plists.

        Parameters
        ----------
        other_plist : ``plist_utils.plist.Plist``
            The other plist object

        Returns
        -------
        Whether the two plists are equal (in data)
        """        
        this_plist_values = pd.Series(self._data).sort_index().transform(str)
        other_plist_values = pd.Series(other_plist._data).sort_index().transform(str)

        return this_plist_values.equals(other_plist_values)
