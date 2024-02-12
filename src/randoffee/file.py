"""
file.py
-------
Auxiliary functions for reading / writing permutations.
"""

from pathlib import Path
from . import Permutation

def get_all_previous_permutations(prev_dir: str | Path = "previous") -> list[Permutation]:
    """
    Get all previous permutations from a directory of previous permutations.
    Makes sure to ignore .latest.json files.

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
    for file in prev_dir.iterdir():
        if file.is_file() and file.suffix == '.json' and file.name != '.latest.json':
            ALL_PERMS.append(Permutation.from_json_file(file))
    if len(ALL_PERMS) == 0:
        raise FileNotFoundError(f"No previous permutations found"
                                f" in '{prev_dir.resolve()}'")
    return sorted(ALL_PERMS, key=lambda p: p.date, reverse=True)
