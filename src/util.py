from sys import stderr
from typing import Any


def eprint(*args, **kwargs):
    """
    print to stderr
    """
    merged_kwargs: Any = {"file": stderr} | kwargs
    print(*args, **merged_kwargs)
