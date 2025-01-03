"""
run.py
------
Script to generate a new permutation for coffee chats. To use, first install
the randoffee library. Then `cd` to the `Coffee` folder in the REG SharePoint,
and run:

    randoffee

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

        randoffee -e flast@turing.ac.uk

3. `template`
   A text file containing the email template. The template should contain a
   line with the text `{GROUPS}`, which indicates where the groups will be
   inserted.

The script will generate random groups of 4 or 5 people, along with the
complete text for an email. This text is automatically copied to the clipboard
in RTF format, and can then be pasted into the desktop version of Outlook (or
the macOS Mail.app).

Alternatively, this also provides a way of printing the RTF email for a set of
groups which have already been generated. To do this, you need to be in the
same folder as before, and run:

    randoffee-load FILENAME.json
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from math import inf
from pathlib import Path
from textwrap import wrap

from tqdm import tqdm

from .file import get_all_previous_permutations
from .leader import adjust_leaders
from .main import Permutation
from .randomise import randomise


def announce(s):
    lines = wrap(s, width=70)
    for i, line in enumerate(lines):
        if i == 0:
            print(f"✨☕️✨ \033[1m{line}")
        else:
            print(f"       {line}")
    print("\033[0m", end="")


def error(message, suggestion):
    message_lines = wrap(message, width=70)
    for i, line in enumerate(message_lines):
        if i == 0:
            print(f"❌ \033[1m{line}")
        else:
            print(f"   {line}")
    print("\033[0m", end="")
    for line in wrap(suggestion, width=70):
        print(f"   {line}")
    sys.exit(1)


def weighted_similarity(perm, most_recent_perms):
    weights = [1.0, 0.8, 0.5, 0.2]
    return sum(
        weight * perm.similarity_to(p).per_person_score
        for weight, p in zip(weights, most_recent_perms)
    ) / sum(weights)


class Person:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return f"{self.name} <{self.email}>"


def determine_participants(
    include_file, exclude_file, args_excluded_emails=None
) -> list[Person]:
    include_file_obj = Path(include_file)
    if not include_file_obj.exists():
        error(
            message=f"File '{include_file}' not found.",
            suggestion="Please make sure the file is in the current working directory. It should have a list of all the people participating in the random coffees, one per line, with a comma separating their name from their email.",
        )
    with include_file_obj.open(encoding="UTF-8") as f:
        lines = f.read().splitlines()
    try:
        # Check that include file has the right format
        assert all(len(line.split(",")) == 2 for line in lines)
        # Add people to include
        include_splits = [line.split(",") for line in lines]
        include_people = [Person(split[0], split[1]) for split in include_splits]
    except IndexError:
        error(
            message=(f"Error reading the file '{include_file}'."),
            suggestion="Each line should have a comma that separates the name of the person from their email.",
        )
    except AssertionError:
        error(
            message=(f"Error reading the file '{include_file}'."),
            suggestion="Not all lines had two columns. Check for stray or missing commas.",
        )

    if not include_people:
        error(
            message=f"No participants found in '{include_file}'.",
            suggestion="Please make sure the file is not empty and has the correct format: One person per line, with a comma separating their name from their email.",
        )

    exclude_file_obj = Path(exclude_file)
    if exclude_file_obj.exists():
        with exclude_file_obj.open(encoding="UTF-8") as f:
            lines = f.read().splitlines()
    else:
        lines = []
    try:
        # Check that exclude file has the right format
        assert all(len(line.split(",")) == 2 for line in lines)
        # Assume that the email is the second column and add them to exclude
        exclude_file_emails = {line.split(",")[1] for line in lines}
    except IndexError:
        error(
            message=(f"Error reading the file '{exclude_file}'."),
            suggestion="Each line should have a comma that separates the name of the person from their email.",
        )
    except AssertionError:
        error(
            message=(f"Error reading the file '{exclude_file}'."),
            suggestion="Not all lines had two columns. Check for stray or missing commas.",
        )


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


def get_persons_from_emails(
    emails: list[str], include_file, exclude_file
) -> set[Person]:
    """Returns all Persons corresponding to the list of emails. Searches in
    both the include and exclude files."""
    potential_participants = set()

    for file in [include_file, exclude_file]:
        file_obj = Path(file)

        if not file_obj.exists():
            error(
                message=f"File '{file}' not found.",
                suggestion="Please make sure the file is in the current working directory. It should have a list of all the people participating in the random coffees, one per line, with a comma separating their name from their email.",
            )
        with file_obj.open(encoding="UTF-8") as f:
            lines = f.read().splitlines()
        splits = [line.split(",") for line in lines]
        try:
            people = {Person(split[0], split[1]) for split in splits}
            potential_participants = potential_participants | people
        except IndexError:
            error(
                message=(f"Error reading the file '{file}'."),
                suggestion="Each line should have a comma that separates the name of the person from their email.",
            )

    return {p for p in potential_participants if p.email in emails}


def get_name_from_email(email: str, participants: list[Person]):
    for p in participants:
        if p.email == email:
            return p.name
    msg = f"Email {email} not found in participants"
    raise ValueError(msg)


def parse_main_args():
    parser = argparse.ArgumentParser(
        prog="randoffee", description="Generate random groups for coffee chats"
    )
    parser.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        default=[],
        help="Emails to exclude (can be space or semicolon separated)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-n",
        "--number",
        default=100000,
        help="Number of random permutations to generate (default: 100000)",
        type=int,
    )
    group.add_argument(
        "-t",
        "--target",
        help=(
            "Maximum tolerable weighted similarity score to the previous four"
            " permutations. You can use either this flag or -n, but not"
            " both; the default is to use -n."
        ),
        type=float,
    )
    parser.add_argument(
        "--allow-imperfect",
        action="store_true",
        help="Allow imperfect permutations (i.e. those with repeated people from the last round)",
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
        msg = "Error: textutil or pbcopy not found. For automatic copying to clipboard, please run this on macOS."
        raise FileNotFoundError(msg) from None


def choose_best_of(
    n_attempts, allow_imperfect, most_recent_perms, participants, group_size
):
    """
    1. Perform full randomisation `n_attempts` times.
    2. Filter for those which have 0 similarity to the immediately
       preceding permutation (i.e. no repeated people from the last
       round).
    3. Pick the one with the lowest weighted similarity to the preceding
       4 permutations. The weighted similarity is defined as

          weighted_similarity = (  1.0 * similarity_1
                                 + 0.8 * similarity_2
                                 + 0.5 * similarity_3
                                 + 0.2 * similarity_4) / 2.5

       where similarity_1 is the similarity to the most recent permutation,
       similarity_2 is the similarity to the second most recent, etc.
       Note that by virtue of the filtering in step 2, similarity_1 will
       always be 0.
    """
    perfect_perms = []
    best_perm = None
    best_similarity = inf

    announce(f"Generating {n_attempts} random permutations and picking the best.")
    print()

    for _ in tqdm(range(n_attempts)):
        trial_permutation = randomise(
            [p.email for p in participants],
            algorithm="full_random",
            group_size=group_size,
        )
        if most_recent_perms:
            trial_similarity = trial_permutation.similarity_to(
                most_recent_perms[0]
            ).per_person_score
        else:
            trial_similarity = 0
        # Check if it's perfect
        if trial_similarity == 0:
            perfect_perms.append(trial_permutation)
        # Check if it's the best so far
        if trial_similarity < best_similarity:
            best_similarity = trial_similarity
            best_perm = trial_permutation
    print()

    # Choose the best permutation
    if len(perfect_perms) == 0:
        if allow_imperfect:
            # OK to not have a perfect permutation, just choose the best one
            permutation = best_perm
        else:
            error(
                message=(
                    f"No permutations with no similarity to previous"
                    f" round ({most_recent_perms[0].datetime.date()}) found"
                ),
                suggestion=(
                    "Try increasing the number of attempts with the -n"
                    " flag, or suppressing this error with"
                    " --allow-imperfect."
                ),
            )
    else:
        # Calculate weighted similarity for each of the perfect permutations,
        # and select the lowest from these
        perfect_perms.sort(key=lambda p: weighted_similarity(p, most_recent_perms))
        permutation = perfect_perms[0]

    return permutation


def randomise_until_target(
    target_similarity, allow_imperfect, most_recent_perms, participants, group_size
):
    """
    Generate permutations until one below the target similarity score is found.
    """
    count = 0
    best_similarity = inf
    while True:
        count += 1
        permutation = randomise(
            [p.email for p in participants],
            algorithm="full_random",
            group_size=group_size,
        )
        # Similarity to most recent permutation
        similarity_latest = permutation.similarity_to(
            most_recent_perms[0]
        ).per_person_score
        # Weighted similarity to all previous permutations
        similarity_all = weighted_similarity(permutation, most_recent_perms)

        if similarity_all < best_similarity:
            best_similarity = similarity_all

        if count % 1000 == 0:
            print(f"Attempt {count}: best similarity so far = {best_similarity}")

        if (
            allow_imperfect or similarity_latest == 0
        ) and similarity_all < target_similarity:
            return permutation


def parse_load_args():
    parser = argparse.ArgumentParser(
        prog="randoffee-load", description="Generate email text from a JSON file."
    )
    # Just one positional argument
    parser.add_argument(
        "filename",
        metavar="FILENAME",
        type=str,
        help="JSON file containing the groupings.",
    )
    return parser.parse_args()


def load():
    args = parse_load_args()

    # Print the permutation and some stats
    permutation = Permutation.from_json_file(args.filename)
    announce("Loaded permutation")
    print(permutation)
    print()

    # Determine participants from permutation
    participants = get_persons_from_emails(
        emails=permutation.participants(),
        include_file="include",
        exclude_file="exclude",
    )

    # Generate email text
    groups_text = ""
    for i, group in enumerate(permutation.groups, start=1):
        if i > 1:
            groups_text += "\n"
        groups_text += (
            f"Group {i}:"
            f" <b>{get_name_from_email(group.leader, participants)}</b>"
            f" | "
            f"{' | '.join(get_name_from_email(o, participants) for o in group.others)}"
        )
    with Path("template").open() as f:
        email_template = f.read()
    email_text = email_template.format(GROUPS=groups_text)
    email_text = email_text.replace("\n", "<br />")

    # Copy email text to clipboard
    copy_html_to_clipboard(email_text)

    # Print emails to send to
    announce(
        "The email text has been copied to your system clipboard."
        " You should be able to paste it into any desktop email"
        " client (browser doesn't work)."
    )
    print()
    announce("Send the email to the following people:")
    print("; ".join(sorted(p.email for p in participants)))
    print()


def main():
    args = parse_main_args()
    prev_dir = "previous"
    group_size = 4

    participants = determine_participants(
        include_file="include",
        exclude_file="exclude",
        args_excluded_emails=args.exclude,
    )
    if not participants:
        announce(
            "There are no participants in this round, and thus nothing to do. Are you perhaps excluding everyone?",
        )
        sys.exit(0)

    most_recent_perms = get_all_previous_permutations(prev_dir)
    if not most_recent_perms:
        announce(
            f"Could not find any previous permutations in '{prev_dir}'. If this is the first time you're running randoffee, that's fine. Otherwise make sure '{prev_dir}' is in the current working directory."
        )
        print()

    # Generate the permutation
    if args.target is not None:
        permutation = randomise_until_target(
            args.target,
            args.allow_imperfect,
            most_recent_perms,
            participants,
            group_size,
        )
    else:
        permutation = choose_best_of(
            args.number,
            args.allow_imperfect,
            most_recent_perms,
            participants,
            group_size,
        )

    # Print the permutation and some stats
    permutation = adjust_leaders(permutation)
    announce("Proposed permutation")
    print(permutation)
    print()

    for prev_perm in most_recent_perms[:4]:
        announce(f"Similarity to previous coffee on {prev_perm.datetime.date()}")
        print(permutation.similarity_to(prev_perm))
        print()

    announce("Weighted similarity to previous 4 permutations")
    print(weighted_similarity(permutation, most_recent_perms))
    print()

    # Generate email text
    groups_text = ""
    for i, group in enumerate(permutation.groups, start=1):
        if i > 1:
            groups_text += "\n"
        groups_text += (
            f"Group {i}:"
            f" <b>{get_name_from_email(group.leader, participants)}</b>"
            f" | "
            f"{' | '.join(get_name_from_email(o, participants) for o in group.others)}"
        )
    with Path("template").open() as f:
        email_template = f.read()
    email_text = email_template.format(GROUPS=groups_text)
    email_text = email_text.replace("\n", "<br />")

    # Copy email text to clipboard
    copy_html_to_clipboard(email_text)

    # Print emails to send to
    announce(
        "The email text has been copied to your system clipboard."
        " You should be able to paste it into any desktop email"
        " client (browser doesn't work)."
    )
    print()
    announce("Send the email to the following people:")
    print("; ".join(sorted(p.email for p in participants)))
    print()

    # Prompt user to save permutation to disk
    announce("Are these your final groupings (to be sent out via email)?")
    save_perm = ""
    while save_perm.strip().lower() not in ["y", "n"]:
        save_perm = input("(y/n) > ")
    print()

    # Always save it to .latest.json, but if user said yes, then additionally
    # save it to a file with the date as the name
    save_perm_dir = Path("previous")
    save_perm_dir.mkdir(exist_ok=True)
    save_perm_file = save_perm_dir / ".latest.json"
    permutation.to_json_file(save_perm_file)
    if save_perm.strip().lower() == "y":
        permutation_date = permutation.datetime.date()
        save_perm_file = save_perm_dir / f"{permutation_date}.json"
        counter = 0
        while save_perm_file.exists():
            counter += 1
            save_perm_file = save_perm_dir / f"{permutation_date}_{counter}.json"
        permutation.to_json_file(save_perm_file)
        announce(f"Permutation saved to '{save_perm_file}'.")
    else:
        announce(
            f"Permutation not saved. (You can still find it at"
            f" '{save_perm_file}' should you need it.)"
        )


if __name__ == "__main__":
    main()
