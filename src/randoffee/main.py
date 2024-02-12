"""
main.py
-------

Classes for 'Groupings' (which represent one group in a random coffee round)
and 'Permutations' (which represent all groups in a random coffee round).

Also provides a mechanism for serialising both classes as JSON. The schema is
roughly defined as follows. The strings involved are people's emails, as given
in the `include` file. The rationale for using emails is that these are less
likely to change than names are.

{
    "date": date,
    "groups": [
        {
            "leader": str,
            "others": list[str],
        },
        ...
    ]
}
"""

import json
import datetime
import itertools
from collections import Counter
from pathlib import Path


class Grouping:
    def __init__(self, leader: str, others: list[str]):
        self.leader = leader
        self.others = set(others)

    def participants(self) -> set[str]:
        return {self.leader} | self.others

    ## TODO: Typing of dictionary values is not specific enough here
    def _asdict(self) -> dict[str, str | list[str]]:
        return {
            "leader": self.leader,
            "others": list(self.others)
        }


    def to_json(self) -> str:
        return json.dumps(self._asdict(), indent=4)

    @classmethod
    def from_dict(cls, d: dict):
        return cls(leader=d["leader"],
                   others=d["others"])

    def similarity_to(self, other: 'Grouping', excluding=None) -> int:
        """
        Returns the number of people in common between this grouping and
        another.

        The 'excluding' keyword argument can be used to exclude a person from
        the calculation. This is useful when you want to know how similar two
        groupings containing a particular person are, but you don't want to
        count that person.
        """
        if excluding is not None:
            excluding = set(excluding)
        else:
            excluding = set()
        return len((self.participants() - excluding)
                   & (other.participants() - excluding))


class Permutation:
    def __init__(self, date: datetime.date, groups: list[Grouping]):
        self.date = date
        self.groups = groups

    ## TODO: Typing of dictionary values is not specific enough here
    def _asdict(self) -> dict[str, str | list[dict[str, str | list[str]]]]:
        return {
            # YYYY-MM-DD
            "date": self.date.strftime("%Y-%m-%d"),
            "groups": [g._asdict() for g in self.groups]
        }

    def participants(self) -> set[str]:
        return set().union(*[g.participants() for g in self.groups])

    def to_json(self):
        return json.dumps(self._asdict(), indent=4)

    def to_json_file(self, filename: str | Path):
        with open(filename, "w") as f:
            f.write(self.to_json())

    @classmethod
    def from_json(cls, json_string: str):
        d = json.loads(json_string)
        return cls(date=datetime.date.fromisoformat(d["date"]),
                   groups=[Grouping.from_dict(g)
                           for g in d["groups"]])

    @classmethod
    def from_json_file(cls, filename: str | Path):
        with open(filename, "r") as f:
            return cls.from_json(f.read())

    def __str__(self):
        s = []
        for i, grp in enumerate(self.groups):
            s.append(f"Group {i+1}: {' | '.join(grp.participants())}")
        return "\n".join(s)


    def similarity_to(self,
                      other: 'Permutation',
                      weighting='linear') -> 'PermutationSimilarityStats':
        """
        Calculates the similarity between this permutation and another.

        The 'weighting' keyword argument can be set to 'linear' or 'quadratic'.
        This determines how the similarity scores in each group are combined.
        If 'linear', then the scores are added together. If 'quadratic', then
        the scores are squared and then added together. 'quadratic' effectively
        strongly penalises groups which are very similar.

        Returns a PermutationSimilarityStats object.
        """
        all_participants = self.participants() | other.participants()
        score_total = 0
        persons_with_repeats = {}

        for p in all_participants:
            # Find groups that P was in
            this_groups = [g for g in self.groups if p in g.participants()]
            other_groups = [g for g in other.groups if p in g.participants()]
            # Person didn't take part in one round. Assign a score of 0.
            if len(this_groups) == 0 or len(other_groups) == 0:
                continue
            elif len(this_groups) > 1:
                raise ValueError(f"Person {p} was in more than one group"
                                 f" in permutation dated {self.date}")
            elif len(other_groups) > 1:
                raise ValueError(f"Person {p} was in more than one group"
                                 f" in permutation dated {other.date}")
            else:
                sim = this_groups[0].similarity_to(other_groups[0],
                                                   excluding=[p])
                if sim > 0:
                    persons_with_repeats[p] = sim
                
                if weighting == 'linear':
                    score_total += sim
                elif weighting == 'quadratic':
                    score_total += sim ** 2

        return PermutationSimilarityStats(
            per_person_score=score_total / len(all_participants),
            persons_with_repeats=persons_with_repeats
        )


class PermutationSimilarityStats:
    """
    A class for storing the results of a similarity calculation between two
    permutations. The attributes are as follows:

    per_person_score
        First assign a score S to each person, where S is the number of
        repeated people you chatted with in both permutations. For example,
        if in the first permutation you (Y) were in a group {Y, A, B} and
        in the second permutation you were in a group {Y, B, C}, then your
        score S would be 1, because you chatted with B in both groups. This
        metric returns the mean of these scores across all people who
        participated in either permutation.

    persons_with_repeats
        A dictionary mapping each participant to their score as defined
        above. Only entries with a score greater than 0 are included.
    """

    def __init__(self, per_person_score: float, persons_with_repeats: dict[str, int]):
        self.per_person_score = per_person_score
        self.persons_with_repeats = persons_with_repeats

    def __str__(self):
        if len(self.persons_with_repeats) == 0:
            persons_with_repeats_str = '    none'
        else:
            sorted_persons = sorted(self.persons_with_repeats.items(),
                                    key=lambda x: [x[1], x[0]])
            persons_with_repeats_str = '\n'.join([f'    {v} for {k}'
                                                  for k, v in sorted_persons])
        return (f"per_person_score\n    {self.per_person_score:.4f}\n"
                f"persons_with_repeats\n{persons_with_repeats_str}")
