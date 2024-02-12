"""
run.py
------
Script to generate a new permutation for coffee chats. To use, first install
the randoffee library. Then `cd` to the `Coffee` folder in the REG SharePoint,
and run:

    python -m randoffee.run

This script requires the following files to be present in the working directory
(the `Coffee` folder should already have all of these).

1. `include`
   A CSV file containing names and emails of people who are participating in
   the coffee. Each line should have the format {name},{email}.

2. `exclude`
   Same format as above. The exclude file overrides the include file, so if
   somebody is in both, they will be excluded.

   For a more temporary exclusion (e.g. for people on leave), you can pass the
   email address as an argument to the script, e.g.

        python randomise.py -e flast@turing.ac.uk

The script will generate random groups of 4 or 5 people, along with the
complete text for an email. This text is automatically copied to the clipboard
in RTF format, and can then be pasted into the desktop version of Outlook (or
the macOS Mail.app).
"""

import argparse
import subprocess
from pathlib import Path

from tqdm import tqdm

from .randomise import randomise
from .main import Permutation

def announce(s):
    print(f"✨ \033[1m{s}\033[0m")


HEADER = "<br />".join(
    """
Hello REG and ARC,

Here are the groups for our next randomised coffee chats.
""".split(
        "\n"
    )
)

FOOTER = "<br />".join(
    """
The first person in the group is responsible for making sure the meeting gets
scheduled, but anyone in the group is free to take initiative to schedule it.
Please schedule a 30 minute call, and feel free to fill it with chatter about
absolutely anything, including, but not limited to, the following topics:

 - Birds in classic literature
 - Which type of cheese the Moon is made of
 - Renters' rights in the United Kingdom
 - The most unusual pasta shape you've seen

The opt-out form is still here: https://forms.office.com/e/mN3hHns3Qf and you
are welcome to let one of us know if you'd like to take a temporary break (zero
judgment). Just drop us a Slack message or an email.

Kind regards,
Jon and Markus

""".split("\n"))


class Person:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return f"{self.name} <{self.email}>"


def determine_participants(include_file,
                           exclude_file,
                           args_excluded_emails=None
                           ) -> list[Person]:
    with open(include_file, "r", encoding="UTF-8") as f:
        lines = f.read().splitlines()
        include_splits = [line.split(",") for line in lines]
        include_people = [Person(split[0], split[1]) for split in include_splits]

    with open(exclude_file, "r", encoding="UTF-8") as f:
        lines = f.read().splitlines()
        exclude_file_emails = set(line.split(",")[1] for line in lines)

    if args_excluded_emails is None:
        args_excluded_emails = set()
    else:
        args_excluded_emails = set(args_excluded_emails)

    participants = []
    for person in include_people:
        if person.email in (exclude_file_emails | args_excluded_emails):
            print(f"Excluding {person.name} <{person.email}> from this round")
        else:
            participants.append(person)

    return participants


def get_name_from_email(email: str, participants: list[Person]):
    for p in participants:
        if p.email == email:
            return p.name
    raise ValueError(f"Email {email} not found in participants")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate random groups for coffee chats"
    )
    parser.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        default=[],
        help="Emails to exclude (can be space or semicolon separated)",
    )

    args = parser.parse_args()
    # Split on semicolons (if any)
    exclude = []
    for em in args.exclude:
        exclude.extend(em.split(";"))
    args.exclude = [em.strip() for em in exclude]
    return args


def copy_html_to_clipboard(html_text: str) -> None:
    try:
        proc1 = subprocess.Popen(
            [
                "textutil",
                "-convert",
                "rtf",
                "-stdin",
                "-stdout",
                "-inputencoding",
                "UTF-8",
                "-format",
                "html",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        proc2 = subprocess.Popen(["pbcopy", "-Prefer", "rtf"], stdin=proc1.stdout)
        proc1.communicate(input=html_text.encode("UTF-8"))
        proc2.wait()
    except FileNotFoundError:
        raise FileNotFoundError(
            "Error: textutil or pbcopy not found. For automatic copying to"
            " clipboard, please run this on macOS."
        ) from None


def get_most_recent_permutations(prev_dir: str | Path = "previous") -> list[Permutation]:
    """Get the most recent permutation from a directory of previous
    permutations. Makes sure to ignore .latest.json files."""
    ALL_PERMS = []
    prev_dir = Path(prev_dir)
    for file in prev_dir.iterdir():
        if file.is_file() and file.suffix == '.json' and file.name != '.latest.json':
            ALL_PERMS.append(Permutation.from_json_file(file))
    if len(ALL_PERMS) == 0:
        raise FileNotFoundError(f"No previous permutations found"
                                f" in '{prev_dir.resolve()}'")
    return sorted(ALL_PERMS, key=lambda p: p.date, reverse=True)


if __name__ == "__main__":
    args = parse_args()
    participants = determine_participants(include_file="include",
                                          exclude_file="exclude",
                                          args_excluded_emails=args.exclude)

    most_recent_perms = get_most_recent_permutations(prev_dir="previous")

    ALGORITHM = 'random_pick_best'

    if ALGORITHM == 'random_once':
        announce("Generating a single random permutation.")

        # Perform full randomisation one time and check similarity to previous
        # permutation
        permutation = randomise([p.email for p in participants],
                                algorithm=ALGORITHM)
        most_recent_perm = most_recent_perms[0]
        announce(f"Similarity to previous coffee on {most_recent_perm.date}")
        print(permutation.similarity_to(most_recent_perm))

    elif ALGORITHM == 'random_pick_best':
        # 1. Perform full randomisation 100000 times.
        # 2. Filter for those which have 0 similarity to the immediately
        #    preceding permutation (i.e. no repeated people from the last
        #    round).
        # 3. Pick the one with the lowest weighted similarity to the preceding
        #    4 permutations. The weighted similarity is defined as
        #
        #       weighted_similarity = (  1.0 * similarity_1
        #                              + 0.8 * similarity_2
        #                              + 0.5 * similarity_3
        #                              + 0.2 * similarity_4) / 2.5
        #
        #    where similarity_1 is the similarity to the most recent permutation,
        #    similarity_2 is the similarity to the second most recent, etc.
        #    Note that by virtue of the filtering in step 2, similarity_1 will
        #    always be 0.
        n_attempts = 10000
        perfect_perms = []

        announce(f"Generating {n_attempts} random permutations and picking the best.")
        print()

        for _ in tqdm(range(n_attempts)):
            trial_permutation = randomise([p.email for p in participants],
                                          algorithm='full_random')
            trial_similarity = trial_permutation.similarity_to(most_recent_perms[0]).per_person_score
            if trial_similarity == 0:
                perfect_perms.append(trial_permutation)

        print()

        if len(perfect_perms) == 0:
            raise ValueError(f"No permutations with similarity to previous"
                             f" round ({most_recent_perms[0].date}) found")

        # Calculate weighted similarity for each permutation
        def weighted_similarity(perm):
            return (1.0 * perm.similarity_to(most_recent_perms[0]).per_person_score
                    + 0.8 * perm.similarity_to(most_recent_perms[1]).per_person_score
                    + 0.5 * perm.similarity_to(most_recent_perms[2]).per_person_score
                    + 0.2 * perm.similarity_to(most_recent_perms[3]).per_person_score) / 2.5

        perfect_perms.sort(key=weighted_similarity)
        permutation = perfect_perms[0]

        for prev_perm in most_recent_perms[:4]:
            announce(f"Similarity to previous coffee on {prev_perm.date}")
            print(permutation.similarity_to(prev_perm))
            print()

        announce(f"Weighted similarity to previous 4 permutations")
        print(weighted_similarity(permutation))
        print()

    else:
        raise ValueError(f"Algorithm '{ALGORITHM}' not recognised")

    # Generate email text
    email_text = HEADER
    email_text += "<br />"
    for i, group in enumerate(permutation.groups, start=1):
        email_text += (f"Group {i}:"
                       f" <b>{get_name_from_email(group.leader, participants)}</b>"
                       f" | "
                       f"{' | '.join(get_name_from_email(o, participants) for o in group.others)}<br />")
    email_text += FOOTER

    # Copy email text to clipboard
    copy_html_to_clipboard(email_text)

    # Print emails to send to
    announce("The email text has been copied to your system clipboard."
               " You should be able to paste it into\n   any desktop email"
               " client (browser doesn't work).")
    print()
    announce("Send the email to the following people:")
    print("; ".join(sorted(p.email for p in participants)))
    print()

    # Prompt user to save permutation to disk
    announce("Are these your final groupings (to be sent out via email)?")
    save_perm = input("   (y/n) > ")
    print()
    
    # Always save it to .latest.json, but if user said yes, then additionally
    # save it to a file with the date as the name
    save_perm_dir = Path("previous")
    save_perm_dir.mkdir(exist_ok=True)
    save_perm_file = save_perm_dir / ".latest.json"
    permutation.to_json_file(save_perm_file)
    if save_perm.lower() == 'y':
        save_perm_file = save_perm_dir / f"{permutation.date}.json"
        permutation.to_json_file(save_perm_file)
        announce(f"Permutation saved to '{save_perm_file}'.")
    else:
        announce(f"Permutation not saved. (You can still find it at"
                 f" '{save_perm_file}' should you need it.)")
