"""
randomise.py
------------
To use:
    python randomise.py

This script requires a list of names and emails in the file "include". Each
line of this file should be a comma-separated list of name and email, e.g.

    Grace Hopper,ghopper@turing.ac.uk

To explicitly remove somebody from the list, add them to the file "exclude",
which has the same format. The exclude file overrides the include file, so if
somebody is in both, they will be excluded.

For a more temporary exclusion (e.g. for people on leave), you can pass the
email address as an argument to the script, e.g.

    python randomise.py -e ghopper@turing.ac.uk

The script will generate random groups of 4 or 5 people, along with the
complete text for an email. This text is automatically copied to the clipboard
in RTF format, and can then be pasted into the desktop version of Outlook (or
the macOS Mail.app).
"""

import argparse
import random
import subprocess
import sys

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
The first person in the group is responsible for making sure the meeting gets scheduled, but anyone in the group is free to take initiative to schedule it. The meeting should take place this week or next, after that we'll start a new round with new groups. Please schedule a 30 minute call, and feel free to fill it with chatter about absolutely anything, including, but not limited to, snakes, shades of pink, brick architecture, or 17th century wars.

For more information about the random coffees, including how to opt out, see Evelina's original email, which we paste below. If you've already opted out, please ignore this email.

Kind regards,
Jon and Markus

Description of the scheme:

> As part of our long-term hybrid working strategy, we would like to trial new Hut23 randomised coffees. 
> 
> The goal is to create a space for conversations across the team, not limited to people who already work together or who come to the office regularly. The Hut23 randomised coffees will differ from the Turing-wide scheme:
> 
> - The scheme will be limited to REG and ARC.
> - We will be randomly split into groups of 4. This is a group size that still enables a reasonable conversation over Zoom. It also enables the meeting to happen even if someone is not available.
> - Every 2 weeks, you will receive an email with your group assignment. 
> - A designated person within each group will be responsible for scheduling the coffee. They can also delegate the responsibility to someone else in the group. 
> - The recommended process is to create a slack conversation with your group and coordinate there. 
> - When scheduling, be mindful of the team members that come to the office and book a meeting room if necessary.
> 
> Thank you to Markus and Jon who will be running the scheme, ie. generating the groups and sending out emails. After several rounds, we will follow up with a survey to assess how the randomised coffees are working in practice.
> 
> If you would prefer to opt out, please fill in this form: https://forms.office.com/e/mN3hHns3Qf.
""".split(
        "\n"
    )
)


def random_groups(elements, group_size):
    """Divide the elements into random groups of size N."""
    random.shuffle(elements)
    groups = [elements[i : i + group_size] for i in range(0, len(elements), group_size)]
    last_group = groups[-1]
    last_group_size = len(last_group)
    if last_group_size < group_size:
        oversize_group_inds = random.sample(range(len(groups) - 1), last_group_size)
        for ind, element in zip(oversize_group_inds, last_group):
            groups[ind].append(element)
        groups = groups[:-1]
    return groups


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


if __name__ == "__main__":
    args = parse_args()
    GROUP_SIZE = 4

    # Generate groups
    with open("include", "r", encoding="UTF-8") as f:
        lines = f.read().splitlines()
        include_splits = [line.split(",") for line in lines]

    with open("exclude", "r", encoding="UTF-8") as f:
        lines = f.read().splitlines()
        exclude_emails = [line.split(",")[1] for line in lines]

    def is_email_included(email):
        return email not in args.exclude and email not in exclude_emails

    names_and_emails = {
        split[0]: split[1] for split in include_splits if is_email_included(split[1])
    }
    excluded_names_and_emails = {
        split[0]: split[1]
        for split in include_splits
        if not is_email_included(split[1])
    }
    groups = random_groups(list(names_and_emails.keys()), GROUP_SIZE)

    # Generate email text
    email_text = HEADER
    email_text += "<br />"
    for i, group in enumerate(groups, start=1):
        group[0] = f"<b>{group[0]}</b>"
        email_text += f"Group {i}: {' | '.join(group)}<br />"
    email_text += FOOTER

    # Copy email text to system rich text clipboard
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
        proc1.communicate(input=email_text.encode("UTF-8"))
        proc2.wait()
    except FileNotFoundError:
        print(
            "Error: textutil or pbcopy not found. For automatic copying to"
            " clipboard, please run on Mac."
        )
        sys.exit(1)
    else:
        print(
            "Email text copied to clipboard. You should be able to paste"
            " it into any desktop email client (browser doesn't work).\nSend"
            " the email to the following people:"
        )
        print()

    # Print emails to send to
    print("; ".join(names_and_emails.values()))

    # Print excluded emails
    if excluded_names_and_emails:
        print()
        print(
            "The following people in the include list have been excluded"
            " from this round:"
        )
        for name, email in excluded_names_and_emails.items():
            print(f" - {name} <{email}>")
    else:
        print()
        print("Nobody on the include list was excluded from this round.")
