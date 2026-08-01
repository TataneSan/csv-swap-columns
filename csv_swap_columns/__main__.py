"""Module entry point for ``python -m csv_swap_columns``."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
