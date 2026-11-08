"""Read typeshed-style stubs: locate, parse and resolve names.

The ideas come from ``typeshed_client`` (stub lookup, version and platform
conditions, overload groups, ``__all__``, re-exports and name resolution
across files), re-implemented here so astart needs no such dependency.
"""

from __future__ import annotations

from astart.stubs.conditions import Target, evaluate
from astart.stubs.locate import find_typeshed
from astart.stubs.parser import ImportedName, StubModule, StubName, parse_stub
from astart.stubs.resolver import (
    Resolved,
    Resolver,
    default_resolver,
    host_resolver,
)
from astart.stubs.returns import function_return
from astart.stubs.versions import module_available, parse_versions

__all__: list[str] = [
    "ImportedName",
    "Resolved",
    "Resolver",
    "StubModule",
    "StubName",
    "Target",
    "default_resolver",
    "evaluate",
    "find_typeshed",
    "function_return",
    "host_resolver",
    "module_available",
    "parse_stub",
    "parse_versions",
]
