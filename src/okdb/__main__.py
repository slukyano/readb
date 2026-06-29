"""Enable ``python -m okdb`` as an entry point equivalent to the ``okdb`` console script."""

from okdb.cli import main

if __name__ == "__main__":
    main()
