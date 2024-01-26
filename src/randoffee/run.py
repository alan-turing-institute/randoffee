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

from .randomise import randomise
from .main import Permutation


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

 - What you're working on
 - What you're struggling with
 - What you're excited about
 - What you're reading
 - What you're watching
 - What you're listening to
 - What you're eating
 - What you're drinking
 - What you're doing for fun
 - What you're doing for work
 - What you're doing for exercise
 - What you're doing for relaxation
 - What you're doing for education
 - What you're doing for entertainment
 - What you're doing for self-improvement
 - What you're doing for self-care
 - What you're doing for others
 - What you're doing for the world
 - What you're doing for the environment
 - What you're doing for the community
 - What you're doing for your family
 - What you're doing for your friends
 - What you're doing for your colleagues
 - What you're doing for your neighbours
 - What you're doing for your country
 - What you're doing for your planet
 - What you're doing for your universe
 - What you're doing for your multiverse
 - What you're doing for your metaverse
 - What you're doing for your megaverse
 - What you're doing for your xenoverse
 - What you're doing for your omniverse
 - What you're doing for your hyperverse
 - What you're doing for your ultraverse
 - What you're doing for your archverse
 - What you're doing for your universe cluster
 - What you're doing for your universe cluster complex
 - What you're doing for your universe cluster complex supercluster
 - What you're doing for your universe cluster complex supercluster
 - What you're doing for your universe cluster complex supercluster
 - What you're doing for your universe cluster complex supercluster

(At this point, Copilot went into a loop, so we stopped it.)

The opt-out form is still here: https://forms.office.com/e/mN3hHns3Qf and you are welcome to let one of us know if you'd like to take a temporary break (zero judgment).

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


def get_most_recent_permutation(prev_dir: str | Path = "previous") -> Permutation:
    """Get the most recent permutation from a directory of previous permutations"""
    ALL_PERMS = []
    prev_dir = Path(prev_dir)
    for file in prev_dir.iterdir():
        if file.is_file() and file.suffix == '.json':
            ALL_PERMS.append(Permutation.from_json_file(file))
    if len(ALL_PERMS) == 0:
        raise FileNotFoundError(f"No previous permutations found"
                                f" in '{prev_dir.resolve()}'")
    return max(ALL_PERMS, key=lambda p: p.date)


if __name__ == "__main__":
    args = parse_args()
    participants = determine_participants(include_file="include",
                                          exclude_file="exclude",
                                          args_excluded_emails=args.exclude)

    most_recent_perm = get_most_recent_permutation(prev_dir="previous")
    permutation = randomise([p.email for p in participants],
                            algorithm="full_random_until_no_match",
                            previous_permutation=most_recent_perm,
                            max_tries=100000)

    # Print similarity to previous coffee
    # print(f"\n--------- SIMILARITY TO PREVIOUS COFFEE ON {most_recent_perm.date} ---------")
    # print(permutation.similarity_to(most_recent_perm))
    # print()

    # Generate email text
    email_text = HEADER
    email_text += "<br />"
    for i, group in enumerate(permutation.groups, start=1):
        email_text += f"Group {i}: <b>{group.leader}</b> | {' | '.join(group.others)}<br />"
    email_text += FOOTER

    # Copy email text to clipboard
    copy_html_to_clipboard(email_text)

    # Print emails to send to
    print(
        "Email text copied to clipboard. You should be able to paste"
        " it into any desktop email client (browser doesn't work).\nSend"
        " the email to the following people:"
    )
    print()
    print("; ".join(sorted(p.email for p in participants)))
