__all__ = [
    'Plist'
]


import os
import plistlib

from datetime import datetime
from pathlib import Path

from types import MappingProxyType
from typing import (
    Any,
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
        self._path = None
        self._name = name

        try:
            plist_from_path(plist_input)
        except (TypeError, FileNotFoundError, plistlib.InvalidFileException):
            raise plistlib.InvalidFileException(INVALID_PLIST_FILE_MSG)
        else:
            self._path = Path(plist_input)

    @property
    def name(self):
        return self._name

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
            plist_dict = plist_from_path(self.path)
        except plistlib.InvalidFileException as e:
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
        Property - returns an integer hash of the plist data; wrapper attribute for
        ``self.__hash__()``.

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
        other_plist_values = pd.Series(other_plist.data).sort_index().transform(str)

        return this_plist_values.equals(other_plist_values)

    @property
    def keys(self) -> Tuple[str]:
        """
        Property - returns a tuple of the plist keys.

        Returns
        -------
        Tuple of plist keys
        """
        return tuple(self.data.keys())

    @property
    def values(self) -> Tuple[Any]:
        return tuple(self.data.values())

    @property
    def exists(self) -> bool:
        """
        Property - returns a bool of whether there is an underlying plist
        file existing on the filesystem.

        Returns
        -------
        ``bool`` of whether the underlying plist file exists
        """
        try:
            return self.path.exists()
        except (AttributeError, FileNotFoundError):
            raise ValueError(
                f'Plist file "{str(self.path)}" does not exist or has been deleted'
            )

    @property
    def created(self) -> str:
        """
        Property - returns the creation time string of the underlying plist
        file, if it exists.

        Returns
        -------
        The creation time string of the underlying plist file, if it exists.
        """
        try:
            created_epoch_time = os.path.getctime(self.path)
        except (TypeError, FileNotFoundError):
            raise ValueError(
                f'Plist file "{str(self.path)}" does not exist or has been deleted'
            )
        else:
            return datetime.utcfromtimestamp(created_epoch_time).strftime(
                '%Y-%m-%d %H:%M:%S'
            )

    @property
    def updated(self) -> str:
        """
        Property - returns the last updated time string of the underlying plist
        file, if it exists.

        Returns
        -------
        The last updated time string of the underlying plist file, if it exists.
        """
        try:
            updated_epoch_time = os.path.getmtime(self.path)
        except (TypeError, FileNotFoundError):
            raise ValueError(
                f'Plist file "{str(self.path)}" does not exist or has been deleted'
            )
        else:
            return datetime.utcfromtimestamp(updated_epoch_time).strftime(
                '%Y-%m-%d %H:%M:%S'
            )

    @property
    def accessed(self) -> str:
        """
        Property - returns the last access time string of the underlying plist
        file, if it exists.

        Returns
        -------
        The last access time string of the underlying plist file, if it exists.
        """
        try:
            accessed_epoch_time = os.path.getatime(self.path)
        except (TypeError, FileNotFoundError):
            raise ValueError(
                f'Plist file "{str(self.path)}" does not exist or has been deleted'
            )
        else:
            return datetime.utcfromtimestamp(accessed_epoch_time).strftime(
                '%Y-%m-%d %H:%M:%S'
            )

    @property
    def owner(self) -> str:
        """
        Property - returns the user/owner name of the underlying plist file, if it exists.

        Returns
        -------
        The user/owner name of the underlying plist file, if it exists.
        """
        try:
            return self.path.owner()
        except (AttributeError, FileNotFoundError):
            raise ValueError(
                f'Plist file "{str(self.path)}" does not exist or has been deleted'
            )

    @property
    def group(self) -> str:
        """
        Property - returns the user group name of the underlying plist file, if it exists.

        Returns
        -------
        The user group name of the underlying plist file, if it exists.
        """
        try:
            return self.path.group()
        except (AttributeError, FileNotFoundError):
            raise ValueError(
                f'Plist file "{str(self.path)}" does not exist or has been deleted'
            )
