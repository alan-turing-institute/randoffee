"""
main.py
-------

Classes for 'Groupings' (which represent one group in a random coffee round)
and 'Permutations' (which represent all groups in a random coffee round).

Also provides a mechanism for serialising both classes as JSON. The schema is
roughly defined as follows. The strings involved are people's full names, as
given in the `include` file.

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


class Grouping:
    def __init__(self, leader: str, others: list[str]):
        self.leader = leader
        self.others = set(others)

    def participants(self) -> set[str]:
        return {self.leader} | self.others

    def to_json(self) -> str:
        return json.dumps({
            "leader": self.leader,
            "others": list(self.others)
        })

    @classmethod
    def from_json(cls, json_string: str):
        d = json.loads(json_string);
        return cls(leader=d["leader"],
                   others=d["others"])


class Permutation:
    def __init__(self, date: ..., groups: list[Grouping]):
        self.date = date
        self.groups = groups


    def to_json(self):
        return json.dumps({
            "date": self.date,
            "groups": [g.to_json() for g in self.groups]
        })

    @classmethod
    def from_json(cls, json_string: str):
        d = json.loads(json_string)
        return cls(date=d["date"],
                   groups=[Grouping.from_json(g)
                           for g in d["groups"]])
