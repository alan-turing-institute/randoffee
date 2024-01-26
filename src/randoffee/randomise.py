import random
import datetime


from .main import Grouping, Permutation


def randomise(participants: list[str],
              group_size: int = 4,
              algorithm: str = 'full_random',
              previous_permutation: Permutation | None = None,
              max_tries: int = 100000,
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
        The algorithm to use for randomising the groups.

        'full_random' : Completely randomly permute participants.

        'full_random_until_no_match' : Run 'full_random' until the similarity
            score with a previous permutation is 0. The 'previous_permutation'
            and 'max_tries' parameters must be given.

    previous_permutation : Permutation, optional
        The previous permutation. Only used if `algorithm` is
        'full_random_until_no_match'. Defaults to None.

    max_tries : int, optional
        The maximum number of times to try 'full_random_until_no_match' before
        giving up. Defaults to 100000.
    """
    if algorithm == 'full_random':
        participants = list(participants)   # make a copy
        random.shuffle(participants)

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

    elif algorithm == 'full_random_until_no_match':
        if previous_permutation is None:
            raise ValueError("No previous permutation given")
        if max_tries < 1:
            raise ValueError(f"Invalid max_tries '{max_tries}'")

        count = 0
        while count < max_tries:
            count += 1
            perm = randomise(participants, group_size, algorithm='full_random')
            if perm.similarity_to(previous_permutation) == 0:
                print(f"Found permutation with similarity 0 after {count} tries")
                return perm
        raise ValueError(f"Could not find permutation with similarity"
                         f" 0 after {count} tries")

    else:
        raise ValueError(f"Invalid algorithm '{algorithm}'")
