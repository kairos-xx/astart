from importlib import metadata
from typing import Any
from warnings import deprecated

@deprecated("""
    `setuptools.installer` and `fetch_build_eggs` are deprecated.
    Requirements should be satisfied by a PEP 517 installer.
    If you are using pip, you can try `pip install --use-pep517`.
    """)
def fetch_build_egg(
    dist,
    req,
) -> metadata.Distribution | metadata.PathDistribution: ...
def strip_marker(req) -> Any: ...
