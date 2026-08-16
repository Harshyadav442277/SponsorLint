"""`python -m sponsorlint`.

Module scope stays on the demo dependency set — see the import discipline note
in `cli.py`.
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
