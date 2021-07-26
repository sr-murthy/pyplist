__all__ = [
    'Plist'
]


import os
import plistlib
import stat

from datetime import datetime
from pathlib import Path

from types import MappingProxyType
from typing import (
    Tuple,
    Union,
)

import pandas as pd

from .utils import (
    blake2b_hash_iterable,
    INVALID_PLIST_FILE_MSG,
    json_normalized_plist,
    plist_from_path,
)


class Plist:
    """
    Basic Plist class - exposes the given plist file data via a property
    that retrieves the latest stored version of the plist file data.

    Implements ``__hash__`` to allow hashing of the plist data, and
    ``__eq__`` to allow two plist objects to be compared for equality.
    """
    def __init__(
        self,
        plist_input: Union[str, Path],
        name=None
    ) -> None:
        """
        Class initialiser - accepts either a plist file path string or a
        ``pathlib.Path`` object.
        """
        try:
            plist_from_path(plist_input)
        except (TypeError, FileNotFoundError, plistlib.InvalidFileException):
            raise plistlib.InvalidFileException(INVALID_PLIST_FILE_MSG)
        else:
            self._fp = Path(plist_input)
            self._name = name

    @property
    def file_path(self) -> Union[None, Path]:
        """
        Property - returns plist file path, if one was provided.

        Returns
        -------
        Null if no file path was provided in initialisation, or a
        ``Pathlib.Path`` object containing the file path.
        """
        return self._fp

    @property
    def name(self):
        return self._name

    @property
    def data(self) -> MappingProxyType:
        """
        Property - returns the read-only, JSON-normalized plist dict from
        reading the latest content of the underling plist file.

        Returns
        -------
        The read-only, JSON-normalized plist dict (if the underlying file
        exists, and is a valid plist file).

        Raises
        ------
        ``plistlib.InvalidFileException``
        """
        try:
            plist_dict = plist_from_path(self.file_path)
        except (FileNotFoundError, plistlib.InvalidFileException) as e:
            raise e
        else:
            return MappingProxyType(
                json_normalized_plist(plist_dict)
            )

    def __hash__(self) -> int:
        """
        Returns the integer hash of the BLAKE2b hash of the plist data - this
        is computed by taking the BLAKE2b hash of the sorted Pandas series of
        values, and then taking the hash of the BLAKE2b hash value.

        Returns
        -------

        The integer hash of the BLAKE2b hash value of the plist values
        """
        plist_series = pd.Series(self.data).sort_index().transform(str)

        return hash(blake2b_hash_iterable(plist_series))

    @property
    def hash(self):
        """
        Property - returns an integer hash of the plist data; wrapper attribute
        for ``self.__hash__()``.

        Returns
        -------
        An integer hash of the plist data using ``self.__hash__()``
        """
        return self.__hash__()

    def __eq__(self, other_plist) -> bool:
        """
        ``Plist`` object equality comparator - equality is based on equality of
        the Pandas series of values for the two plists.

        Parameters
        ----------
        other_plist : ``pyplist.plist.Plist``
            The other plist object

        Returns
        -------
        Whether the two plists are equal (in data)
        """
        this_plist_values = pd.Series(self.data).sort_index().transform(str)
        other_plist_values = pd.Series(
            other_plist.data
        ).sort_index().transform(str)

        return this_plist_values.equals(other_plist_values)

    @property
    def keys(self) -> Tuple[str]:
        """
        Property - returns a tuple of the JSON-normalized plist keys.

        Returns
        -------
        Tuple of plist keys
        """
        return tuple(self.data.keys())

    @property
    def values(self) -> Tuple[Union[bool, int, float, str, bytes, list]]:
        """
        Property - returns a tuple of the JSON-normalized plist values.

        Returns
        -------
        ``tuple`` of plist values
        """
        return tuple(self.data.values())

    @property
    def file_exists(self) -> bool:
        """
        Property - returns a bool of whether there the plist file exists.

        Returns
        -------
        ``bool`` of whether the plist file exists
        """
        return self.file_path.exists()

    @property
    def file_mode(self) -> str:
        """
        Property - returns the underlying plist file mode string.

        Returns
        -------
        ``str`` of the plist file mode

        Raises
        ------
        ``FileNotFoundError` if the file no longer exists
        """
        return stat.filemode(os.stat(self.file_path).st_mode)

    @property
    def file_size(self) -> int:
        """
        Property - returns the file size in bytes

        Returns
        -------
        ``int`` of the plist file size in bytes

        Raises
        ------
        ``FileNotFoundError` if the file no longer exists
        """
        return os.path.getsize(self.file_path)

    @property
    def file_created(self) -> str:
        """
        Property - returns the creation time string of the underlying plist
        file, if it exists.

        Returns
        -------
        The creation time string of the underlying plist file, if it exists.

        Raises
        ------
        ``FileNotFoundError` if the file no longer exists
        """
        created_epoch_time = os.path.getctime(self.file_path)

        return datetime.utcfromtimestamp(created_epoch_time).strftime(
            '%Y-%m-%d %H:%M:%S'
        )

    @property
    def file_updated(self) -> str:
        """
        Property - returns the last updated time string of the underlying plist
        file, if it exists.

        Returns
        -------
        The last updated time string of the underlying plist file, if it
        exists.

        Raises
        ------
        ``FileNotFoundError` if the file no longer exists
        """
        updated_epoch_time = os.path.getmtime(self.file_path)

        return datetime.utcfromtimestamp(updated_epoch_time).strftime(
            '%Y-%m-%d %H:%M:%S'
        )

    @property
    def file_accessed(self) -> str:
        """
        Property - returns the last access time string of the underlying plist
        file, if it exists.

        Returns
        -------
        The last access time string of the underlying plist file, if it exists.

        Raises
        ------
        ``FileNotFoundError` if the file no longer exists
        """
        accessed_epoch_time = os.path.getatime(self.file_path)

        return datetime.utcfromtimestamp(accessed_epoch_time).strftime(
            '%Y-%m-%d %H:%M:%S'
        )

    @property
    def file_owner(self) -> str:
        """
        Property - returns the user/owner name of the underlying plist file, if
        it exists.

        Returns
        -------
        The user/owner name of the underlying plist file, if it exists.

        Raises
        ------
        ``FileNotFoundError` if the file no longer exists
        """
        return self.file_path.owner()

    @property
    def file_group(self) -> str:
        """
        Property - returns the user/owner group name of the underlying plist
        file, if it exists.

        Returns
        -------
        The user/owner group name of the underlying plist file, if it exists.

        Raises
        ------
        ``FileNotFoundError` if the file no longer exists
        """
        return self.file_path.group()
