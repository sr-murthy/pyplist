__all__ = [
    'Plist',
    'ProgramPlist',
]


import os
import plistlib
import stat

from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from xml.etree import ElementTree as XmlElementTree

import pandas as pd

from ..utils import (
    blake2b_hash_iterable,
    INVALID_PLIST_FILE_MSG,
    json_normalized_plist_dict,
    plist_dict_from_path,
    process_instances_by_exec_path,
)


class Plist:
    """
    Basic Plist class - exposes the given plist file properties via a property
    that retrieves the latest stored version of the plist file properties.

    .. note:: Only XML and binary versions of XML plists are supported.

    Implements ``__hash__`` to allow hashing of the plist properties, and
    ``__eq__`` to allow two plist objects to be compared for equality.
    """
    def __init__(self, plist_input):
        """
        Class initialiser - accepts either a plist file path string or a
        ``pathlib.Path`` object.

        Parameters
        ----------
        ``str``, ``pathlib.Path``: plist path string or object

        """
        try:
            plist_dict_from_path(plist_input)
        except (TypeError, FileNotFoundError, plistlib.InvalidFileException):
            raise plistlib.InvalidFileException(INVALID_PLIST_FILE_MSG)
        else:
            self._fp = Path(plist_input).absolute()

    @property
    def file_path(self):
        """
        Property - returns plist file path, if one was provided.

        Returns
        -------
        ``None``, ``pathlib.Path`` :
            Null if no file path was provided in initialisation, or a
            ``Pathlib.Path`` object containing the file path.
        """
        return self._fp

    @property
    def name(self):
        """
        Property - returns the plist name. This is just the plist file name
        stripped of the ``'.plist'`` extension.

        Returns
        -------
        ``str`` : the plist name

        """
        return self.file_path.name.rstrip('.plist')

    @property
    def xml(self):
        """
        Returns the XML source string of the plist file, if it is an XML
        file, otherwise this will be null if it is a valid binary plist
        file, or will raise an appropriate error if there is a problem
        with the file.

        Returns
        -------
        ``None``, ``str`` :
            Null if the plist file is a non-XML file, otherwise the source
            XML string

        Raises
        ------
        ``TypeError``, ``FileNotFoundError``, `plistlib.InvalidFileException``
        """
        _, file_type = plist_dict_from_path(self.file_path)

        if file_type == 'binary':
            return None

        with open(self.file_path, 'r') as f:
            return f.read()

    @property
    def plist_version(self):
        """
        Returns the plist (XML) version - applicable only to XML plists.

        Returns
        -------
        ``str``, ``None`` :
            The plist (XML) version string, if the plist file is XML. Could
            be null also
        """
        if self.file_type != 'xml':
            return

        plist_root = XmlElementTree.parse(self.file_path).getroot()

        return plist_root.attrib.get('version')

    def __repr__(self):
        """
        ``__repr__`` implementation - the string produced should, if executed,
        in Python, reproduce a ``Plist`` object which has the same properties
        as this object (``self``), if the file still exists, and additionally
        the same or similar file attributes, depending on any intermediate
        changes to the file.
        """
        return (
            f'{self.__module__}.{self.__class__.__name__}('
            f'"{self.file_path}"'
            f')'
        )

    @property
    def properties(self):
        """
        Property - returns the read-only, JSON-normalized plist dict from
        reading the latest content of the underling plist file.

        Returns
        -------
        The read-only, JSON-normalized plist dict (if the underlying file
        exists, and is a valid plist file).

        Raises
        ------
        ``FileNotFoundError``, ``plistlib.InvalidFileException``
        """
        try:
            plist_dict, _ = plist_dict_from_path(self.file_path)
        except (FileNotFoundError, plistlib.InvalidFileException) as e:
            raise e
        else:
            return MappingProxyType(
                json_normalized_plist_dict(plist_dict)
            )

    def __hash__(self):
        """
        Returns the integer hash of the BLAKE2b hash of the plist properties -
        this is computed by taking the BLAKE2b hash of the sorted Pandas
        series of property values, and then taking the hash of the BLAKE2b
        hash value.

        Returns
        -------

        The integer hash of the BLAKE2b hash value of the plist values
        """
        plist_series = pd.Series(self.properties).sort_index().transform(str)

        return hash(blake2b_hash_iterable(plist_series))

    @property
    def hash(self):
        """
        Property - returns an integer hash of the plist properties; wrapper
        attribute for ``self.__hash__()``.

        Returns
        -------
        An integer hash of the plist properties using ``self.__hash__()``
        """
        return self.__hash__()

    def __eq__(self, other_plist):
        """
        ``Plist`` object equality comparator - equality is based on equality of
        the Pandas series of property values for the two plists. The file
        attributes are ignored.

        Parameters
        ----------
        other_plist : ``pyplist.core.plist.Plist``
            The other plist object

        Returns
        -------
        Whether the two plists are equal (in terms of their properties dicts)
        """
        this_plist_values = pd.Series(self.properties).sort_index().transform(str)
        other_plist_values = pd.Series(
            other_plist.properties
        ).sort_index().transform(str)

        return this_plist_values.equals(other_plist_values)

    @property
    def keys(self):
        """
        Property - returns a tuple of the JSON-normalized plist keys.

        Returns
        -------
        Tuple of plist keys
        """
        return tuple(self.properties.keys())

    @property
    def values(self):
        """
        Property - returns a tuple of the JSON-normalized plist values.
        The allowable Python types are ``bool``, ``int``, ``float``, ``str``,
        ``bytes``, and ``list``, and thse correspond to the allowable
        types in the plist source XML data.

        Returns
        -------
        ``tuple`` of plist values
        """
        return tuple(self.properties.values())

    @property
    def file_exists(self):
        """
        Property - returns a bool of whether the plist file path currently
        exists.

        Returns
        -------
        ``bool`` of whether the plist file exists
        """
        return self.file_path.exists()

    @property
    def file_type(self):
        """
        Property - returns the plist file type: ``'xml'`` or ``'binary'``.

        Returns
        -------
        ``str`` of whether the plist file type: ``'xml'`` or ``'binary'``
        """
        _, file_type = plist_dict_from_path(self.file_path)

        return file_type

    @property
    def file_mode(self):
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
    def file_size(self):
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
    def file_created(self):
        """
        Property - returns a ``datetime.datetime`` object of the file creation
        UTC time. If it does not exist a ``FileNotFoundError`` is raised.

        Returns
        -------
        ``datetime.datetime`` object of the file creation UTC time, if if
        exists.

        Raises
        ------
        ``FileNotFoundError` if the file no longer exists
        """
        created_epoch_time = os.path.getctime(self.file_path)

        return datetime.utcfromtimestamp(created_epoch_time)

    @property
    def file_updated(self):
        """
        Property - returns a ``datetime.datetime`` object of the UTC time
        the file was updated. If it does exist a ``FileNotFoundError`` is
        raised.

        Returns
        -------
        ``datetime.datetime`` object of the UTC time the file was last updated,
        if
        it exists

        Raises
        ------
        ``FileNotFoundError` if the file no longer exists
        """
        updated_epoch_time = os.path.getmtime(self.file_path)

        return datetime.utcfromtimestamp(updated_epoch_time)

    @property
    def file_accessed(self):
        """
        Property - returns a ``datetime.datetime`` object of the UTC time
        the file was accessed. If it does exist a ``FileNotFoundError`` is
        raised.

        Returns
        -------
        ``datetime.datetime`` object of the UTC time the file was last
        accessed, if it exists

        Raises
        ------
        ``FileNotFoundError` if the file no longer exists
        """
        accessed_epoch_time = os.path.getatime(self.file_path)

        return datetime.utcfromtimestamp(accessed_epoch_time)

    @property
    def file_owner(self):
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
    def file_group(self):
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

    @property
    def file_summary(self):
        """
        Property - returns a read-only dict summarising the key file
        properties:
        ::
            * file name
            * directory path
            * whether the file currently exists on the filesystem
            * the file type - ``'xml'``, or ``'binary'``
            * the plist XML version string
            * the user/owner,
            * the user group
            * size in bytes
            * file mode string
            * created time
            * last updated time
            * last accessed time

        Returns
        -------
        Returns a read-only dict summarising the key file properties listed
        above.

        Raises
        ------
        ``FileNotFoundError` if the file no longer exists
        """
        datetime_fmt = '%Y-%m-%d %H:%M:%S.%f'

        return MappingProxyType({
            'name': self.file_path.name,
            'dir': str(self.file_path.parent.absolute()),
            'exists': self.file_exists,
            'type': self.file_type,
            'plist_version': self.plist_version,
            'user': self.file_owner,
            'group': self.file_group,
            'size': self.file_size,
            'mode': self.file_mode,
            'created': self.file_created.strftime(datetime_fmt),
            'updated': self.file_updated.strftime(datetime_fmt),
            'accessed': self.file_accessed.strftime(datetime_fmt)
        })


class ProgramPlist(Plist):

    def __init__(self, plist_input):
        """
        Class initialiser - accepts either a plist file path string or a
        ``pathlib.Path`` object. Represents plists for executables, e.g.
        programs, processes, including daemons.

        Parameters
        ----------
        ``str``, ``pathlib.Path`` :
            plist path string or object

        """
        super(self.__class__, self).__init__(plist_input)

    @property
    def program_path(self):
        """
        Returns the plist program path object, if available via properties.

        Returns
        -------
        ``pathlib.Path``, ``None``:
            The plist program path object, or null if unavailable via
            properties.
        """
        try:
            return Path(self.properties['Program'])
        except KeyError:
            try:
                return Path(self.properties.get('ProgramArguments')[0])
            except TypeError:
                return

    @property
    def program_name(self):
        """
        Returns the plist program name, if available via properties.

        Returns
        -------
        ``str``, ``None`` :
            The plist program name, or null if unavailable via
            properties.
        """
        try:
            return self.program_path.name
        except AttributeError:
            return

    @property
    def process_instances(self):
        """
        Returns a read-only dict of the process instances of the plist program,
        keyed by the process ID. If there are no active processes for the program
        an empty dict is returned.

        Returns
        -------
        ``types.MappingProxyType`` :
            A read-only dict of the process instances of the plist program,
            keyed by the process ID. If there are no active processes for the
            program an empty dict is returned.
        """
        program_path = self.program_path

        if not program_path:
            return

        return MappingProxyType({
            proc_instance['pid']: proc_instance
            for proc_instance in process_instances_by_exec_path(program_path)
        })

    @property
    def is_running(self):
        """
        Returns whether there is a running process associated with the plist
        program. If the program path is undefined or invalid this will return
        null, as the call on the ``process_instances`` property will return
        null in that case.

        Returns
        -------
        ``bool``, ``None`` :
            Whether there is a running process associated with the plist
            program. If the program path is undefined or invalid this will
            return null, as the call on the ``process_instances`` property
            will return null in that case.
        """
        try:
            return len(self.process_instances) > 0
        except TypeError:
            return
