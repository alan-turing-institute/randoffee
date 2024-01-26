import random
import datetime


from .main import Grouping, Permutation


def randomise(participants: list[str],
              group_size: int = 4,
              algorithm: str = 'full_random'
              ) -> "Permutation":
    """Divide participants into groups.

    Parameters
    ----------
    participants : list[Person]
        List of participants to be grouped. The entries should be their full
        names.

    group_size : int, optional
        The size of each group. As many groups are made with size `group_size`
        as possible, but if `group_size` does not cleanly divide
        `len(participants)`, then there will be some groups with size one
        larger than `group_size`. Defaults to 4.

    algorithm : str, optional
        The algorithm to use for randomising the groups. The default is
        'full_random', which uses a full randomisation. There are no other
        valid values for this at the moment.
    """
    if algorithm == 'full_random':
        random.shuffle(list(participants))   # make a copy

        # Let N = qn + r, where N = number of participants, n = group size, q =
        # number of groups, and r = number of participants left over.

        # Calculate q and r
        q, r = divmod(len(participants), group_size)

        # Generate the first groups from the first qn people
        groupings = [
            Grouping(leader=participants[group_size * i],
                     others=participants[(group_size * i) + 1 : group_size * (i + 1)])
            for i in range(q)
        ]

        # Add the last r people to r randomly chosen groups
        if r > 0:
            excess_participants = participants[q * group_size :]
            oversize_group_inds = random.sample(range(q), r)
            for ind, element in zip(oversize_group_inds, excess_participants):
                groupings[ind].others.add(element)

        return Permutation(date=datetime.date.today(), groups=groupings)

    else:
        raise ValueError(f"Invalid algorithm '{algorithm}'")
