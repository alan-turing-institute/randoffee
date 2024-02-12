"""
leader.py
---------
Contains functions for tallying the number of times a given person has been
tasked with leading a coffee group, and for adjusting permutations to account
for this.
"""

from .file import get_all_previous_permutations
from .main import Permutation, Grouping

import random 


def count_lead_occasions() -> dict[str, int]:
    """
    Counts the number of times each person has led a coffee group.

    Returns
    -------
    dict[str, int]
        A dictionary with people's emails as keys and the number of times they
        have led a coffee group as values.
    """
    prev_perms = get_all_previous_permutations()
    lead_occasions = {}

    for perm in prev_perms:
        for group in perm.groups:
            lead_occasions[group.leader] = lead_occasions.get(group.leader, 0) + 1

    return lead_occasions


def adjust_leaders(perm: Permutation) -> Permutation:
    """
    Adjusts each group within a given permutation so that the leader is
    selected randomly from the people within each group who have led the fewest
    coffee groups.

    Parameters
    ----------
    perm : Permutation
        The permutation to adjust.

    Returns
    -------
    Permutation
        The adjusted permutation.
    """
    lead_occasions = count_lead_occasions()

    new_groups = []

    for group in perm.groups:
        participants = group.participants()
        min_hosted = min(lead_occasions.get(p, 0) for p in participants)
        min_hosts = [p for p in participants
                     if lead_occasions.get(p, 0) == min_hosted]
        new_leader = random.choice(min_hosts)
        new_others = [p for p in participants if p != new_leader]

        new_groups.append(Grouping(leader=new_leader, others=new_others))

    return Permutation(date=perm.date, groups=new_groups)
