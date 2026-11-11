"""Read one stub file into the names it defines.

Branches that test the Python version or platform are evaluated against a
target, ``@overload`` definitions are grouped, ``__all__`` is followed, and
the typeshed export rules decide which names are public: no leading
underscore, and an import only when it is a re-export (``import x as x``,
``from m import n as n`` or ``from m import *``).

"""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    AugAssign,
    Call,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    If,
    Import,
    ImportFrom,
    List,
    Name,
    Tuple,
    expr,
    parse,
    stmt,
    unparse,
)
from dataclasses import dataclass, field
from typing import Final, final

from astart.stubs.conditions import Target, evaluate

type DictStubName = dict[str, StubName]


@final
class Constants:
    """Group module-level constants.

    Attributes:
        overload (Final[frozenset[str]]): Decorator names that start an
            overload group.
        type_variables (Final[frozenset[str]]): Callees that declare a type
            variable.
        dunder_all (Final[str]): Name of the export list.

    """

    overload: Final[frozenset[str]] = frozenset(
        {"overload", "typing.overload"},
    )
    type_variables: Final[frozenset[str]] = frozenset(
        {"TypeVar", "ParamSpec", "TypeVarTuple"},
    )
    dunder_all: Final[str] = "__all__"


@final
@dataclass(frozen=True, slots=True)
class ImportedName:
    """A name that stands for something defined in another module.

    Attributes:
        module (str): Absolute module the name comes from.
        name (str | None): The name inside that module, or ``None`` when the
            bound
            name is the module itself (``import os.path as p``).

    """

    module: str
    name: str | None


@final
@dataclass(slots=True)
class StubName:
    """One name a stub defines.

    Attributes:
        name (str): The name.
        kind (str): ``function``, ``class``, ``variable``, ``typevar`` or
            ``import``.
        exported (bool): Whether the name is public.
        nodes (list[AST]): The definitions in order (several for an overload
            group).
        children (DictStubName): For a class, the names defined in its body.
        imported (ImportedName | None): Where an ``import`` name comes from.
        alias_of (str | None): The dotted name a plain ``X = Y`` assignment
            refers to.
        ambiguous (bool): Whether a branch the evaluator could not decide
            may have defined it differently or not at all.
        decorators (tuple[str, ...]): Decorator names of a function.
        bases (tuple[str, ...]): Base-class expressions of a class, as text.
        overloaded (bool): Whether the definitions are an ``@overload`` group.

    """

    name: str
    kind: str
    exported: bool = True
    nodes: list[AST] = field(default_factory=list)
    children: DictStubName = field(default_factory=dict)
    imported: ImportedName | None = None
    alias_of: str | None = None
    ambiguous: bool = False
    decorators: tuple[str, ...] = ()
    bases: tuple[str, ...] = ()
    overloaded: bool = False


@final
@dataclass(slots=True)
class StubModule:
    """The public shape of one stub file.

    Attributes:
        name (str): Dotted module name.
        names (DictStubName): Every name the file defines.
        stars (list[str]): Modules star-imported (``from m import *``).
        dunder_all (list[str] | None): The literal ``__all__`` , or ``None``
            when absent.
        typevars (set[str]): Names declared as type variables.

    """

    name: str
    names: DictStubName = field(default_factory=dict)
    stars: list[str] = field(default_factory=list)
    dunder_all: list[str] | None = None
    typevars: set[str] = field(default_factory=set)


def _decorators(*, node: FunctionDef | AsyncFunctionDef) -> tuple[str, ...]:
    """Name the decorators of a function.

    Args:
        node (FunctionDef | AsyncFunctionDef): Function definition.

    Returns:
        tuple[str, ...]: Their source text, call arguments dropped.

    """
    return tuple(
        unparse(ast_obj=item.func if isinstance(item, Call) else item)
        for item in node.decorator_list
    )


def _strings(*, node: expr) -> list[str] | None:
    """Read a literal list or tuple of strings.

    Args:
        node (expr): An expression.

    Returns:
        list[str] | None:
            The strings, or ``None`` when it is not such a literal.

    """
    if not isinstance(node, (List, Tuple)):
        return None
    items: list[str] = []
    for element in node.elts:
        if not (
            isinstance(element, Constant) and isinstance(element.value, str)
        ):
            return None
        items.append(element.value)
    return items


@final
class _Reader:
    """Walk a stub's statements into a :class:`StubModule`."""

    def __init__(self, *, module: str, package: bool, target: Target) -> None:
        """Prepare an empty result.

        Args:
            module (str): Dotted module name.
            package (bool): Whether the file is a package's ``__init__.pyi``.
            target (Target): The environment the branches are decided for.

        """
        self._package: bool = package
        self._target: Target = target
        self.module: StubModule = StubModule(name=module)

    def read(self, *, body: list[stmt]) -> StubModule:
        """Read the top-level statements.

        Args:
            body (list[stmt]): Statements of the module.

        Returns:
            StubModule: The finished module, exports decided.

        """
        self._block(body=body, scope=self.module.names, undecided=False)
        self._exports()
        return self.module

    def _block(
        self,
        *,
        body: list[stmt],
        scope: DictStubName,
        undecided: bool,
    ) -> None:
        """Read statements into a scope.

        Args:
            body (list[stmt]): Statements.
            scope (DictStubName): Names being defined (module or class body).
            undecided (bool): Whether an undecidable branch encloses the block.

        """
        for item in body:
            if isinstance(item, If):
                self._if(item=item, scope=scope, undecided=undecided)
            elif isinstance(item, (FunctionDef, AsyncFunctionDef)):
                self._function(item=item, scope=scope, undecided=undecided)
            elif isinstance(item, ClassDef):
                self._class(item=item, scope=scope, undecided=undecided)
            elif isinstance(item, (Assign, AnnAssign)):
                self._assign(item=item, scope=scope, undecided=undecided)
            elif isinstance(item, (Import, ImportFrom)):
                self._import(item=item, scope=scope, undecided=undecided)
            else:
                self._effect(item=item)

    def _if(
        self,
        *,
        item: If,
        scope: DictStubName,
        undecided: bool,
    ) -> None:
        """Read the branch an ``if`` selects, or both when undecidable.

        Args:
            item (If): The ``if`` statement.
            scope (DictStubName): Names being defined.
            undecided (bool): Whether an undecidable branch encloses it.

        """
        verdict: bool | None = evaluate(test=item.test, target=self._target)
        if verdict is None:
            self._block(body=item.body, scope=scope, undecided=True)
            self._block(body=item.orelse, scope=scope, undecided=True)
        else:
            self._block(
                body=item.body if verdict else item.orelse,
                scope=scope,
                undecided=undecided,
            )

    @staticmethod
    def _define(
        *,
        scope: DictStubName,
        entry: StubName,
        undecided: bool,
    ) -> StubName:
        """Add or replace a name, noting undecided definitions.

        Args:
            scope (DictStubName): Names being defined.
            entry (StubName): The new definition.
            undecided (bool): Whether it sits in an undecidable branch.

        Returns:
            StubName: The entry now stored.

        """
        entry.ambiguous = undecided
        scope[entry.name] = entry
        return entry

    def _function(
        self,
        *,
        item: FunctionDef | AsyncFunctionDef,
        scope: DictStubName,
        undecided: bool,
    ) -> None:
        """Read a function, grouping ``@overload`` definitions.

        Args:
            item (FunctionDef | AsyncFunctionDef): The definition.
            scope (DictStubName): Names being defined.
            undecided (bool): Whether an undecidable branch encloses it.

        """
        names: tuple[str, ...] = _decorators(node=item)
        existing: StubName | None = scope.get(item.name)
        if (
            Constants.overload & set(names)
            and existing is not None
            and existing.kind == "function"
        ):
            existing.nodes.append(item)
            existing.overloaded = True
            return
        entry: StubName = StubName(
            name=item.name,
            kind="function",
            nodes=[item],
            decorators=names,
            overloaded=bool(Constants.overload & set(names)),
        )
        _ = self._define(scope=scope, entry=entry, undecided=undecided)

    def _class(
        self,
        *,
        item: ClassDef,
        scope: DictStubName,
        undecided: bool,
    ) -> None:
        """Read a class and the names in its body.

        Args:
            item (ClassDef): The definition.
            scope (DictStubName): Names being defined.
            undecided (bool): Whether an undecidable branch encloses it.

        """
        entry: StubName = StubName(
            name=item.name,
            kind="class",
            nodes=[item],
            bases=tuple(unparse(ast_obj=base) for base in item.bases),
        )
        _ = self._define(scope=scope, entry=entry, undecided=undecided)
        self._block(body=item.body, scope=entry.children, undecided=undecided)

    def _assign(
        self,
        *,
        item: Assign | AnnAssign,
        scope: DictStubName,
        undecided: bool,
    ) -> None:
        """Read an assignment: a variable, alias, type variable or ``__all__``.

        Args:
            item (Assign | AnnAssign): The statement.
            scope (DictStubName): Names being defined.
            undecided (bool): Whether an undecidable branch encloses it.

        """
        targets: list[expr] = (
            item.targets if isinstance(item, Assign) else [item.target]
        )
        value: expr | None = item.value
        for target in targets:
            if not isinstance(target, Name):
                continue
            if target.id == Constants.dunder_all and value is not None:
                self.module.dunder_all = _strings(node=value)
                continue
            entry: StubName = StubName(
                name=target.id,
                kind="variable",
                nodes=[item],
            )
            callee: str | None = None
            if isinstance(value, Call):
                func: expr = value.func
                if isinstance(func, Attribute):
                    callee = func.attr
                elif isinstance(func, Name):
                    callee = func.id
            if callee in Constants.type_variables:
                entry.kind = "typevar"
                self.module.typevars.add(target.id)
            elif isinstance(value, (Name, Attribute)):
                entry.alias_of = unparse(ast_obj=value)
            _ = self._define(scope=scope, entry=entry, undecided=undecided)

    def _effect(self, *, item: stmt) -> None:
        """Read statements that only edit ``__all__``.

        Args:
            item (stmt): The statement.

        """
        if (
            isinstance(item, AugAssign)
            and isinstance(item.target, Name)
            and item.target.id == Constants.dunder_all
        ):
            more: list[str] | None = _strings(node=item.value)
            if more is not None and self.module.dunder_all is not None:
                self.module.dunder_all.extend(more)
        elif (
            isinstance(item, Expr)
            and isinstance(item.value, Call)
            and isinstance(item.value.func, Attribute)
            and unparse(ast_obj=item.value.func.value) == Constants.dunder_all
            and self.module.dunder_all is not None
        ):
            self._edit_all(call=item.value)

    def _edit_all(self, *, call: Call) -> None:
        """Apply ``__all__.extend([...])`` and ``__all__.append("x")``.

        Args:
            call (Call): The method call on ``__all__``.

        """
        if not isinstance(call.func, Attribute) or not call.args:
            return
        names: list[str] | None = (
            _strings(node=call.args[0])
            if call.func.attr == "extend"
            else [call.args[0].value]
            if call.func.attr == "append"
            and isinstance(call.args[0], Constant)
            and isinstance(call.args[0].value, str)
            else None
        )
        if names is not None and self.module.dunder_all is not None:
            self.module.dunder_all.extend(names)

    def _absolute(self, *, node: ImportFrom) -> str:
        """Turn a possibly relative ``from`` import into a module name.

        Args:
            node (ImportFrom): The statement.

        Returns:
            str: The absolute dotted module name.

        """
        if node.level == 0:
            return node.module or ""
        base: list[str] = self.module.name.split(sep=".")
        if not self._package:
            base = base[:-1]
        base = base[: len(base) - (node.level - 1)] if node.level > 1 else base
        return ".".join([*base, *([node.module] if node.module else [])])

    def _import(
        self,
        *,
        item: Import | ImportFrom,
        scope: DictStubName,
        undecided: bool,
    ) -> None:
        """Read an import into names that point at their origin.

        Args:
            item (Import | ImportFrom): The statement.
            scope (DictStubName): Names being defined.
            undecided (bool): Whether an undecidable branch encloses it.

        """
        if isinstance(item, Import):
            for alias in item.names:
                bound: str = alias.asname or alias.name.partition(".")[0]
                origin: str = alias.name if alias.asname else bound
                self._bind(
                    scope=scope,
                    bound=bound,
                    imported=ImportedName(module=origin, name=None),
                    exported=alias.asname == alias.name,
                    undecided=undecided,
                )
            return
        module: str = self._absolute(node=item)
        for alias in item.names:
            if alias.name == "*":
                self.module.stars.append(module)
                continue
            self._bind(
                scope=scope,
                bound=alias.asname or alias.name,
                imported=ImportedName(module=module, name=alias.name),
                exported=alias.asname == alias.name,
                undecided=undecided,
            )

    def _bind(
        self,
        *,
        scope: DictStubName,
        bound: str,
        imported: ImportedName,
        exported: bool,
        undecided: bool,
    ) -> None:
        """Record one imported name.

        Args:
            scope (DictStubName): Names being defined.
            bound (str): The local name.
            imported (ImportedName): Where it comes from.
            exported (bool): Whether the import is written as a re-export.
            undecided (bool): Whether an undecidable branch encloses it.

        """
        entry: StubName = StubName(
            name=bound,
            kind="import",
            exported=exported,
            imported=imported,
        )
        _ = self._define(scope=scope, entry=entry, undecided=undecided)

    def _exports(self) -> None:
        """Decide which module-level names are public."""
        listed: list[str] | None = self.module.dunder_all
        for name, entry in self.module.names.items():
            if listed is not None:
                entry.exported = name in listed
            elif entry.kind == "import":
                continue
            else:
                entry.exported = not name.startswith("_")


def parse_stub(
    *,
    source: str,
    module: str,
    package: bool,
    target: Target,
) -> StubModule:
    """Read a stub file.

    Args:
        source (str): The ``.pyi`` text.
        module (str): Dotted module name the file defines.
        package (bool): Whether the file is a package's ``__init__.pyi``.
        target (Target): The Python version, platform and implementation to
            read for.

    Returns:
        StubModule: The module's names, grouped overloads and export decisions.

    """
    return _Reader(module=module, package=package, target=target).read(
        body=parse(source=source).body,
    )
