"""
file.py
-------
Auxiliary functions for reading / writing permutations.
"""
from __future__ import annotations

from pathlib import Path

from . import Permutation


def get_all_previous_permutations(
    prev_dir: str | Path = "previous",
) -> list[Permutation]:
    """
    Get all previous permutations from a directory of previous permutations.
    Makes sure to ignore .latest.json files.

    If the directory does not exist, an empty list is returned.

    Parameters
    ----------
    prev_dir : str | Path
        The directory where the previous permutations are stored. Defaults to
        "previous".

    Returns
    -------
    list[Permutation]
        A list of all previous permutations, sorted by date in descending order
        (i.e. most recent first).
    """
    ALL_PERMS = []
    prev_dir = Path(prev_dir)
    if prev_dir.is_dir():
        for file in prev_dir.iterdir():
            if (
                file.is_file()
                and file.suffix == ".json"
                and file.name != ".latest.json"
            ):
                ALL_PERMS.append(Permutation.from_json_file(file))
    return sorted(ALL_PERMS, key=lambda p: p.datetime, reverse=True)
