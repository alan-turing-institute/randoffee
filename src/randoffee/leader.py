"""
leader.py
---------
Contains functions for tallying the number of times a given person has been
tasked with leading a coffee group, and for adjusting permutations to account
for this.
"""
from __future__ import annotations

import random
from math import inf
from typing import Callable

from .file import get_all_previous_permutations
from .main import Grouping, Permutation


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
            # Backfill any participants not already in the dictionary
            for person in group.participants():
                if person not in lead_occasions:
                    lead_occasions[person] = 0
            # Add lead count for group leaders
            lead_occasions[group.leader] += 1

    return lead_occasions


def count_lead_fraction() -> dict[str, int]:
    """
    Counts the fraction of times a person has led a coffee group they
    participated in.

    Returns
    -------
    dict[str, int]
        A dictionary with people's emails as keys and the number of times they
        have led a coffee group as values.
    """
    prev_perms = get_all_previous_permutations()
    lead_occasions = {}
    total_occasions = {}

    for perm in prev_perms:
        for group in perm.groups:
            # Add lead count for group leaders
            lead_occasions[group.leader] = lead_occasions.get(group.leader, 0) + 1
            # Add total count for all group participants
            for person in group.participants():
                total_occasions[person] = total_occasions.get(person, 0) + 1

    return {
        person: (lead_occasions.get(person, 0) / tot)
        for person, tot in total_occasions.items()
    }


def adjust_leaders(
    perm: Permutation,
    metric: str = "lead_fraction",
    score_for_first_timers: Callable[[str], float] = lambda _: inf,
) -> Permutation:
    """
    Adjusts each group within a given permutation so that the leader is
    selected randomly from the people within each group who have had the fewest
    leading responsibilities (as determined by some metric).

    Parameters
    ----------
    perm : Permutation
        The permutation to adjust.
    metric : str, optional
        The metric to use for determining the leader. Can be either "lead_occasions"
        or "lead_fraction". Defaults to "lead_fraction".
    score_for_first_timers : Callable[[str], float], optional
        A function used for calculating the score for people who have never
        participated in a coffee group before. The function should take a
        string, which is the name / email of the person, and return a float
        which represents their score. A higher score means that they are less
        likely to be selected as the new leader.
        By default, this is a function which always returns math.inf, which
        effectively means that first-timers will never be selected to lead a
        group.

    Returns
    -------
    Permutation
        The adjusted permutation.
    """
    if metric == "lead_fraction":
        lead_scores = count_lead_fraction()
    elif metric == "lead_occasions":
        lead_scores = count_lead_occasions()
    else:
        msg = f"Invalid metric: {metric}"
        raise ValueError(msg)

    def get_lead_score(person: str) -> float:
        try:
            return lead_scores[person]
        except KeyError:
            return score_for_first_timers(person)

    new_groups = []

    for group in perm.groups:
        participants = group.participants()
        min_score = min(get_lead_score(p) for p in participants)
        min_score_participants = [
            p for p in participants if get_lead_score(p) == min_score
        ]
        new_leader = random.choice(min_score_participants)
        new_others = [p for p in participants if p != new_leader]

        new_groups.append(Grouping(leader=new_leader, others=new_others))

    return Permutation(date=perm.date, groups=new_groups)
