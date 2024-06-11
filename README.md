# randoffee

Library to handle REG random coffees.

--------

## Workflow for generating random coffees

(_Note_: This assumes you are not actively developing the codebase.
If you are, skip ahead.)

1. Install the executable.
   If you don't have `pipx`, you can do `brew install pipx` on macOS, or [follow the instructions for your system](https://github.com/pypa/pipx).

       pipx install git+https://github.com/alan-turing-institute/randoffee.git

2. `cd` to the `Coffee` folder in the REG SharePoint.

3. Run

       randoffee

4. The script will print the groupings, some statistics about them, and ask you whether these are your final groupings.

   Before answering yes or no, you should double-check the groups to make sure that they are sensible.
   (In practice, we have never interfered with any of the groups.)

   If you are satisfied with these groupings, then you can enter `y` to save the permutation to disk.
   It will be saved in `previous/YYYY-MM-DD.json`.
   This file will be used for future coffee rounds (the script will make sure to generate groups that are sufficiently different from it).

   If you enter `n`, the permutation will still be saved as `previous/.latest.json`.
   You can just `mv` this to the desired date if you realise that you do want those groups.

6. Change the random topics in the email to anything you like.

7. Send the email to the list of email addresses the script gives you.

-------

## Developing

The usage is the same as above, but when setting up the codebase you probably want to:

1. Clone the repository:

       git clone git@github.com:alan-turing-institute/randoffee.git

2. Set up a virtual environment:

       cd randoffee
       python -m venv venv
       source venv/bin/activate

3. Install the library in editable mode:

       pip install --editable .

You should then have access to `randoffee` as a command as long as you are in the virtual environment.
When run, it will use the code in the local repository.

-------

## Usage as library

More functionality to follow.

Example usage (to investigate how similar previous coffees have been) follows.
The `COFFEE_DIR` variable must point to the `Coffee` folder in the REG SharePoint folder (in my case, I've symlinked it to `~/coffee`).


```python
from pathlib import Path

from randoffee import Permutation


## Read in all previous permutations

ALL_PERMS = []
COFFEE_DIR = Path.home() / 'coffee'

for file in (COFFEE_DIR / 'previous').iterdir():
    if file.is_file() and file.suffix == '.json':
        ALL_PERMS.append(Permutation.from_json_file(file))

ALL_PERMS = sorted(ALL_PERMS, key=lambda x: x.date)


## Calculate similarity between all consecutive permutations

for (perm1, perm2) in zip(ALL_PERMS, ALL_PERMS[1:]):
    print(f'-------- {perm1.date} x {perm2.date} --------')
    print(perm1.similarity_to(perm2))
    print('\n\n')
```
