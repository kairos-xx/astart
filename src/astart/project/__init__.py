"""Whole-project analysis: imports, call graph, libraries and versions.

The rules layer analyses one module at a time. This package coordinates a
set of files as a project: :func:`scan_module` extracts each file's
definitions, imports and exports; :class:`SymbolTable` resolves names
across modules including ``__init__`` re-exports and ``__all__``;
:class:`ProjectIndex` keeps per-module records keyed by content hash so
unchanged files are never reparsed, and answers cross-module call sites;
:class:`LibraryIndex` loads typeshed, ``py.typed`` and stub-package
signatures; :class:`PythonTarget` gates emitted syntax on the project's
``requires-python`` floor.
:class:`TypeshedClientIndex` optionally answers lookups through the
third-party ``typeshed_client`` package when it is installed; it is off
by default and the hand-written readers remain the fallback.

"""

from __future__ import annotations

from astart.project.builder import BuildResult, build_index
from astart.project.index import CallRecord, ProjectConfig, ProjectIndex
from astart.project.libraries import (
    LibraryIndex,
    PackageRoot,
    find_library_roots,
)
from astart.project.naming import module_name, package_of
from astart.project.scan import (
    ImportKind,
    ImportRecord,
    ModuleScan,
    scan_module,
)
from astart.project.table import (
    ResolvedSymbol,
    SymbolKind,
    SymbolTable,
)
from astart.project.typeshed_client import (
    ClientConfig,
    TypeshedClientIndex,
)
from astart.project.versions import (
    PythonTarget,
    find_pyproject,
    parse_version,
    requires_python_floor,
    resolve_target,
)

__all__: list[str] = [
    "BuildResult",
    "CallRecord",
    "ClientConfig",
    "ImportKind",
    "ImportRecord",
    "LibraryIndex",
    "ModuleScan",
    "PackageRoot",
    "ProjectConfig",
    "ProjectIndex",
    "PythonTarget",
    "ResolvedSymbol",
    "SymbolKind",
    "SymbolTable",
    "TypeshedClientIndex",
    "build_index",
    "find_library_roots",
    "find_pyproject",
    "module_name",
    "package_of",
    "parse_version",
    "requires_python_floor",
    "resolve_target",
    "scan_module",
]
