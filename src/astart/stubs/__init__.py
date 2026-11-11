# Stub-file reading re-implements ideas from the third-party
# ``typeshed_client`` package; see LICENSES.md for attribution.
"""Read typeshed-style stubs: locate, parse and resolve names.

The ideas come from ``typeshed_client`` (stub lookup, version and platform
conditions, overload groups, ``__all__``, re-exports and name resolution
across files), re-implemented here so astart needs no such dependency.

"""

from __future__ import annotations

from astart.stubs.conditions import Target, evaluate
from astart.stubs.locate import bundled_typeshed, find_typeshed
from astart.stubs.parser import ImportedName, StubModule, StubName, parse_stub
from astart.stubs.resolver import (
    Resolved,
    Resolver,
    default_resolver,
    host_resolver,
)
from astart.stubs.returns import (
    CallArguments,
    class_typevars,
    function_return,
    method_return,
    receiver_parts,
    select_overload,
    variable_type,
)
from astart.stubs.versions import module_available, parse_versions

__all__: list[str] = [
    "CallArguments",
    "ImportedName",
    "Resolved",
    "Resolver",
    "StubModule",
    "StubName",
    "Target",
    "bundled_typeshed",
    "class_typevars",
    "default_resolver",
    "evaluate",
    "find_typeshed",
    "function_return",
    "host_resolver",
    "method_return",
    "module_available",
    "parse_stub",
    "parse_versions",
    "receiver_parts",
    "select_overload",
    "variable_type",
]
