__all__ = [
    'find_plist_files',
]


import os
import plistlib

from pathlib import Path

from .plist import Plist


def find_plist_files(target_dir, recursive=False):
    """
    Find and generate all valid plist files in the target directory, if it
    exists. The valid plist files are generated as``core.plist.Plist``
    objects, and the invalid plist files are ignored.

    If ``recursive`` is ``True`` then the search for plist files in the
    target directory is recursive (look in the entire directory tree).

    Parameters
    ----------
    ``target_dir`` : ``str``, ``pathlib.Path``
        The target directory to search in

    ``recursive`` : ``bool``
        Whether the search should be recursive (top-down)

    Yields
    ------
    ``pyplist.core.plist.Plist``
        plist objects for plist files in the target directory, if the directory
        exists

    Raises
    ------
    ``FileNotFoundError``
        If the target directory doesn't exist
    """
    _target_dir = Path(target_dir).resolve()

    if not _target_dir.exists():
        raise FileNotFoundError(f'"{target_dir}" does not exist')

    if not recursive:
        plist_file_paths = (
            _target_dir.joinpath(file_name)
            for file_name in os.listdir(_target_dir)
            if file_name.endswith('.plist')
        )
        for path in plist_file_paths:
            try:
                yield Plist(path)
            except plistlib.InvalidFileException:
                pass

    else:
        plist_file_paths = (
            Path(root).resolve().joinpath(file_name)
            for root, _, file_names in os.walk(_target_dir)
            for file_name in file_names
            if file_name.endswith('.plist')
        )

        for path in plist_file_paths:
            try:
                yield Plist(path)
            except plistlib.InvalidFileException:
                pass
