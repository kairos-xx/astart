"""Lazy, nonexecuting Python stub lookup adapted from Astart.

This index accepts a path to a folder containing ``stdlib/`` or a ZIP whose
members include ``typeshed/stdlib/``. It never imports target modules.
"""

from __future__ import annotations

from ast import (
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Call,
    ClassDef,
    FunctionDef,
    Name,
    parse,
    stmt,
)
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final, final
from zipfile import ZipFile

from astart.semantic.type_expressions import (
    TypeExpression,
    TypeExpressionCodec,
)
from astart.semantic.typing_contracts import (
    CallableContract,
    function_contract,
)

if TYPE_CHECKING:
    from ast import Module
    from pathlib import Path
    from zipfile import ZipInfo


@final
class Constants:
    """Group module-level constants.

    Attributes:
        max_stub_bytes: Grouped module constant.

    """

    max_stub_bytes: Final[int] = 1000000


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StubSignature:
    """An imported declaration with a structured return annotation.

    Attributes:
        contract: Contract retained as CallableContract | None by this
            instance.
        qualified_name: Identifier used to refer to the qualified.
        returns: Returns retained as TypeExpression by this instance.
        source_path: Path to the source used by this instance.

    """

    qualified_name: str
    source_path: str
    returns: TypeExpression
    contract: CallableContract | None = None


@final
class StubIndex:
    """Cache minimal external annotations without executing imported code."""

    def __init__(self, *, root: Path) -> None:
        """Construct an optional stub index rooted at a trusted path.

        Args:
            root: Filesystem path identifying the root.

        """
        self.root: Path = root
        self._cache: dict[str, tuple[StubSignature, ...]] = {}
        self._archive_names: frozenset[str] | None = None

    def lookup(self, *, qualified_name: str) -> tuple[StubSignature, ...]:
        """Resolve a dotted import against at most one relevant stub file.

        Args:
            qualified_name: Identifier of the qualified being resolved.

        Returns:
            tuple[StubSignature, ...] produced by this operation.

        """
        pieces: tuple[str, ...] = tuple(qualified_name.split(sep="."))
        for length in range(len(pieces) - 1, 0, -1):
            module_name: str = ".".join(pieces[:length])
            if module_name not in self._cache:
                self._cache[module_name] = self._load(module_name=module_name)
            matched: tuple[StubSignature, ...] = tuple(
                item
                for item in self._cache[module_name]
                if item.qualified_name == qualified_name
            )
            if matched:
                return matched
        return ()

    def _read_directory_stub(
        self,
        *,
        names: tuple[str, ...],
    ) -> tuple[bytes, str] | None:
        """Read the first acceptable stub below a directory root.

        Args:
            names: Names supplied as tuple[str, ...] for this operation.

        Returns:
            tuple[bytes, str] | None produced by this operation.

        """
        for candidate in names:
            path: Path = self.root / candidate
            if not path.is_file():
                path = self.root / candidate.removeprefix("stdlib/")
            if (
                path.is_file()
                and path.stat().st_size <= Constants.max_stub_bytes
            ):
                return (path.read_bytes(), str(object=path))
        return None

    def _read_archive_stub(
        self,
        *,
        names: tuple[str, ...],
    ) -> tuple[bytes, str] | None:
        """Read the first acceptable stub from a zip archive root.

        Args:
            names: Names supplied as tuple[str, ...] for this operation.

        Returns:
            tuple[bytes, str] | None produced by this operation.

        """
        with ZipFile(file=self.root) as archive:
            if self._archive_names is None:
                self._archive_names = frozenset(archive.namelist())
            for candidate in names:
                for entry in ("typeshed/" + candidate, candidate):
                    if entry not in self._archive_names:
                        continue
                    info: ZipInfo = archive.getinfo(name=entry)
                    if info.file_size <= Constants.max_stub_bytes:
                        return (archive.read(entry), entry)
                    break
        return None

    def _load(self, *, module_name: str) -> tuple[StubSignature, ...]:
        """Read a bounded `.pyi` file and extract declared return shapes.

        Args:
            module_name: Identifier of the module being resolved.

        Returns:
            tuple[StubSignature, ...] produced by this operation.

        """
        relative: str = module_name.replace(".", "/")
        names: tuple[str, ...] = (
            (f"stdlib/{relative}.pyi"),
            (f"stdlib/{relative}/__init__.pyi"),
        )
        found: tuple[bytes, str] | None = None
        if self.root.is_dir():
            found = self._read_directory_stub(names=names)
        elif self.root.is_file():
            found = self._read_archive_stub(names=names)
        if found is None:
            return ()
        source, chosen = found
        try:
            module: Module = parse(
                source=source.decode(encoding="utf-8-sig"),
                filename=chosen,
            )
        except (SyntaxError, UnicodeDecodeError):
            return ()
        return _stub_signatures(
            module=module,
            module_name=module_name,
            chosen=chosen,
        )


def _type_parameter_names(*, module: Module) -> tuple[str, ...]:
    """Names bound to ``TypeVar``, ``ParamSpec`` or ``TypeVarTuple``.

    Args:
        module: The module examined while names bound to ``TypeVar``,
            ``ParamSpec`` or ``TypeVarTuple``.

    Returns:
        tuple[str, ...] produced by this operation.

    """
    return tuple(
        target.id
        for member in module.body
        if isinstance(member, Assign)
        and isinstance(member.value, Call)
        and isinstance(member.value.func, Name)
        and (member.value.func.id in ("TypeVar", "ParamSpec", "TypeVarTuple"))
        for target in member.targets
        if isinstance(target, Name)
    )


def _member_signature(
    *,
    member: stmt,
    parent: str,
    module_name: str,
    chosen: str,
    type_parameters: tuple[str, ...],
) -> StubSignature | None:
    """Describe one function or annotated attribute of a stub, if any.

    Args:
        chosen: Chosen supplied as str for this operation.
        member: Member supplied as stmt for this operation.
        module_name: Identifier of the module being resolved.
        parent: Parent supplied as str for this operation.
        type_parameters: Type parameters supplied as tuple[str, ...] for this
            operation.

    Returns:
        StubSignature | None produced by this operation.

    """
    if (
        isinstance(member, (FunctionDef, AsyncFunctionDef))
        and member.returns is not None
    ):
        return StubSignature(
            qualified_name=(f"{parent}.{member.name}"),
            source_path=chosen,
            returns=TypeExpressionCodec.from_ast(node=member.returns),
            contract=replace(
                function_contract(
                    node=member,
                    qualified_name=(f"{parent}.{member.name}"),
                    method_kind="instance"
                    if parent != module_name
                    else "function",
                ),
                type_parameters=type_parameters,
                source_path=chosen,
            ),
        )
    if isinstance(member, AnnAssign) and isinstance(member.target, Name):
        return StubSignature(
            qualified_name=(f"{parent}.{member.target.id}"),
            source_path=chosen,
            returns=TypeExpressionCodec.from_ast(node=member.annotation),
        )
    return None


def stub_signatures(
    *,
    source: str,
    module_name: str,
    chosen: str,
) -> tuple[StubSignature, ...]:
    """Extract declared signatures from parsed stub source.

    Args:
        source: Text of a ``.pyi`` file or of a ``.py`` file from a
            ``py.typed`` package.
        module_name: Dotted name the source provides.
        chosen: Path recorded on each signature for provenance.

    Returns:
        The signatures the source declares.

    """
    try:
        module: Module = parse(source=source, filename=chosen)
    except SyntaxError:
        return ()
    return _stub_signatures(
        module=module,
        module_name=module_name,
        chosen=chosen,
    )


def _stub_signatures(
    *,
    module: Module,
    module_name: str,
    chosen: str,
) -> tuple[StubSignature, ...]:
    """Collect every declared signature of a parsed stub module.

    Args:
        chosen: Chosen supplied as str for this operation.
        module: The module examined while collect every declared signature of a
            parsed stub module.
        module_name: Identifier of the module being resolved.

    Returns:
        tuple[StubSignature, ...] produced by this operation.

    """
    result: list[StubSignature] = []
    type_parameters: tuple[str, ...] = _type_parameter_names(module=module)
    statements: list[tuple[str, list[stmt]]] = [
        (module_name, list(module.body)),
    ]
    while statements:
        parent, members = statements.pop()
        for member in members:
            if isinstance(member, ClassDef):
                statements.append(
                    ((f"{parent}.{member.name}"), list(member.body)),
                )
                continue
            signature: StubSignature | None = _member_signature(
                member=member,
                parent=parent,
                module_name=module_name,
                chosen=chosen,
                type_parameters=type_parameters,
            )
            if signature is not None:
                result.append(signature)
    return tuple(result)
