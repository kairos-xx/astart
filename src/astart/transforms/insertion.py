"""Explicit native AST insertion with lexical binding and collision checks."""

from __future__ import annotations

from ast import (
    AnnAssign,
    Attribute,
    BinOp,
    BitOr,
    Call,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    If,
    Import,
    ImportFrom,
    Load,
    Name,
    Starred,
    Store,
    Subscript,
    Tuple,
    With,
    alias,
    arg,
    arguments,
    expr,
    keyword,
    stmt,
    walk,
    withitem,
)
from dataclasses import dataclass
from keyword import iskeyword
from typing import TYPE_CHECKING, final

from astart.transforms.constants import MagicChanges, MagicScope, extract_magic

if TYPE_CHECKING:
    from astart.semantic.scopes import ScopeGraph
    from astart.source.ast import CommentedModule


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InsertSettings:
    """Explicit insertion options; runtime rewrites are disabled by default.

    Attributes:
        replace_print (bool): Rewrite only lexically unbound builtin print
            calls.
        helper_name (str): Preferred name for the injected self-contained
            helper.
        magic_scope (MagicScope): Scope of extracted comparison literals; off
            by default.

    """

    replace_print: bool = False
    helper_name: str = "aprint"
    magic_scope: MagicScope = "off"


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InsertChanges:
    """Auditable changes to the caller's existing module.

    Attributes:
        print_calls_changed (int): Calls rewritten to the native injected
            helper.
        helper_name (str | None): Actual collision-free name, or None when none
            was added.
        skipped (tuple[str, ...]): Explicit reasons for preserving calls.
        numeric_values_changed (int): Numeric literal occurrences replaced.
        numeric_constants_added (int): Unique typed numeric definitions
            inserted.

    """

    print_calls_changed: int
    helper_name: str | None
    skipped: tuple[str, ...]
    numeric_values_changed: int = 0
    numeric_constants_added: int = 0


def _name(*, text: str) -> Name:
    """Construct a fresh load node instead of aliasing AST child identities.

    Args:
        text (str): Identifier spelling.

    Returns:
        Name: A fresh name expression.

    """
    return Name(id=text, ctx=Load())


def _member(*, owner: str, member: str) -> Attribute:
    """Construct one attribute expression with unique child identities.

    Args:
        owner (str): Bound module or receiver identifier.
        member (str): Attribute spelling.

    Returns:
        Attribute: A fresh attribute expression.

    """
    return Attribute(value=_name(text=owner), attr=member, ctx=Load())


def _print_call(*, bindings: _HelperNames, stream: str) -> Expr:
    """Delegate formatting and stream behavior to the actual builtin print.

    The cast expresses print's conditional flush protocol; it never checks
    or replaces the supplied stream. Builtin print retains runtime validation.

    Args:
        bindings (_HelperNames): Collision-free builtin, typing and protocol
            names.
        stream (str): Local stream parameter or context-manager binding.

    Returns:
        Expr: A print expression statement inside the injected helper.

    """
    file: expr = _name(text=stream)
    if stream == "file":
        file = Call(
            func=_member(owner=bindings.typing_name, member="cast"),
            args=[],
            keywords=[
                keyword(
                    arg="typ",
                    value=_union(
                        members=[
                            _name(text=bindings.flushing),
                            Constant(value=None),
                        ],
                    ),
                ),
                keyword(arg="val", value=file),
            ],
        )
    return Expr(
        value=Call(
            func=_member(owner=bindings.builtins, member="print"),
            args=[Starred(value=_name(text="values"), ctx=Load())],
            keywords=[
                keyword(
                    arg=name,
                    value=file if name == "file" else _name(text=name),
                )
                for name in ("sep", "end", "file", "flush")
            ],
        ),
    )


def _union(*, members: list[expr]) -> expr:
    """Build a fresh annotation union without parsing annotation strings.

    Args:
        members (list[expr]): Nonempty ordered alternatives.

    Returns:
        expr: Native union expression.

    """
    result: expr = members[0]
    for member in members[1:]:
        result = BinOp(left=result, op=BitOr(), right=member)
    return result


def _print_protocols(
    *,
    builtins: str,
    typing_name: str,
    printable: str,
    writable: str,
    flushing: str,
) -> list[stmt]:
    """Construct precise structural contracts for values and output streams.

    Args:
        builtins (str): Builtin module alias.
        typing_name (str): Typing module alias.
        printable (str): Name for the string-conversion protocol.
        writable (str): Name for the stream write protocol.
        flushing (str): Name for the conditional flushing protocol.

    Returns:
        list[stmt]: Fresh protocol class definitions.

    """
    result: list[stmt] = []
    for name, method, parameters, returns in (
        (
            printable,
            "__str__",
            [arg(arg="self")],
            _member(owner=builtins, member="str"),
        ),
        (
            writable,
            "write",
            [
                arg(arg="self"),
                arg(
                    arg="text",
                    annotation=_member(owner=builtins, member="str"),
                ),
            ],
            _name(text=printable),
        ),
    ):
        result.append(
            ClassDef(
                name=name,
                bases=[_member(owner=typing_name, member="Protocol")],
                keywords=[],
                decorator_list=[],
                type_params=[],
                body=[
                    FunctionDef(
                        name=method,
                        args=arguments(
                            posonlyargs=parameters,
                            args=[],
                            vararg=None,
                            kwonlyargs=[],
                            kw_defaults=[],
                            kwarg=None,
                            defaults=[],
                        ),
                        body=[Expr(value=Constant(value=Ellipsis))],
                        decorator_list=[],
                        returns=returns,
                        type_comment=None,
                        type_params=[],
                    ),
                ],
            ),
        )
    result.append(
        ClassDef(
            name=flushing,
            bases=[
                _name(text=writable),
                _member(owner=typing_name, member="Protocol"),
            ],
            keywords=[],
            decorator_list=[],
            type_params=[],
            body=[
                FunctionDef(
                    name="flush",
                    args=arguments(
                        posonlyargs=[arg(arg="self")],
                        args=[],
                        vararg=None,
                        kwonlyargs=[],
                        kw_defaults=[],
                        kwarg=None,
                        defaults=[],
                    ),
                    body=[Expr(value=Constant(value=Ellipsis))],
                    decorator_list=[],
                    returns=Constant(value=None),
                    type_comment=None,
                    type_params=[],
                ),
            ],
        ),
    )
    return result


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _HelperNames:
    """Collision-free bindings used by one generated print helper.

    Attributes:
        builtins (str): Builtin module alias.
        path (str): Pathlib module alias.
        typing_name (str): Typing module alias.
        printable (str): String conversion protocol.
        writable (str): Stream protocol.
        flushing (str): Conditional stream flush protocol.

    """

    builtins: str
    path: str
    typing_name: str
    printable: str
    writable: str
    flushing: str


def _print_helper(*, name: str, bindings: _HelperNames) -> FunctionDef:
    """Construct helper syntax directly; no Python template is parsed.

    Args:
        name (str): Collision-free helper identifier.
        bindings (_HelperNames): Collision-free helper/import/protocol
            identifiers.

    Returns:
        FunctionDef:
            Self-contained typed print helper with optional path output.

    """
    builtins: str = bindings.builtins
    path: str = bindings.path
    typing_name: str = bindings.typing_name
    printable: str = bindings.printable
    writable: str = bindings.writable
    return FunctionDef(
        name=name,
        args=arguments(
            posonlyargs=[],
            args=[],
            vararg=arg(arg="values", annotation=_name(text=printable)),
            kwonlyargs=[
                arg(
                    arg="sep",
                    annotation=_union(
                        members=[
                            _member(owner=builtins, member="str"),
                            Constant(value=None),
                        ],
                    ),
                ),
                arg(
                    arg="end",
                    annotation=_union(
                        members=[
                            _member(owner=builtins, member="str"),
                            Constant(value=None),
                        ],
                    ),
                ),
                arg(
                    arg="file",
                    annotation=_union(
                        members=[
                            _member(owner=builtins, member="str"),
                            _member(owner=path, member="Path"),
                            _name(text=writable),
                            Constant(value=None),
                        ],
                    ),
                ),
                arg(
                    arg="mode",
                    annotation=Subscript(
                        value=_member(owner=typing_name, member="Literal"),
                        slice=Tuple(
                            elts=[
                                Constant(value=value)
                                for value in (
                                    "a",
                                    "w",
                                    "x",
                                    "r",
                                    "a+",
                                    "w+",
                                    "x+",
                                    "r+",
                                )
                            ],
                            ctx=Load(),
                        ),
                        ctx=Load(),
                    ),
                ),
                arg(
                    arg="flush",
                    annotation=_member(
                        owner=builtins,
                        member="bool",
                    ),
                ),
            ],
            kw_defaults=[
                Constant(value=None),
                Constant(value=None),
                Constant(value=None),
                Constant(value="a"),
                Constant(value=False),
            ],
            kwarg=None,
            defaults=[],
        ),
        body=[
            Expr(
                value=Constant(
                    value=(
                        "Print values to a stream or a UTF-8 path.\n\n"
                        "Args:\n    *values: Values passed to builtin print.\n"
                        "    sep: Separator, with print's default for None.\n"
                        "    end: Terminator, with print's default for None.\n"
                        "    file: Output stream, path, or current stdout.\n"
                        "    mode: Text path open mode.\n"
                        "    flush: Whether to flush after writing."
                    ),
                ),
            ),
            If(
                test=Call(
                    func=_member(owner=builtins, member="isinstance"),
                    args=[
                        _name(text="file"),
                        Tuple(
                            elts=[
                                _member(owner=builtins, member="str"),
                                _member(owner=path, member="Path"),
                            ],
                            ctx=Load(),
                        ),
                    ],
                    keywords=[],
                ),
                body=[
                    AnnAssign(
                        target=Name(id="stream", ctx=Store()),
                        annotation=_member(owner=typing_name, member="TextIO"),
                        value=None,
                        simple=1,
                    ),
                    With(
                        items=[
                            withitem(
                                context_expr=Call(
                                    func=Attribute(
                                        value=Call(
                                            func=_member(
                                                owner=path,
                                                member="Path",
                                            ),
                                            args=[_name(text="file")],
                                            keywords=[],
                                        ),
                                        attr="open",
                                        ctx=Load(),
                                    ),
                                    args=[],
                                    keywords=[
                                        keyword(
                                            arg="mode",
                                            value=_name(text="mode"),
                                        ),
                                        keyword(
                                            arg="encoding",
                                            value=Constant(
                                                value="utf-8",
                                            ),
                                        ),
                                    ],
                                ),
                                optional_vars=Name(id="stream", ctx=Store()),
                            ),
                        ],
                        body=[_print_call(bindings=bindings, stream="stream")],
                        type_comment=None,
                    ),
                ],
                orelse=[_print_call(bindings=bindings, stream="file")],
            ),
        ],
        decorator_list=[],
        returns=Constant(value=None),
        type_comment=None,
        type_params=[],
    )


@final
class AstInserter:
    """Insert native nodes into one authoritative module, without parsing."""

    def __init__(
        self,
        *,
        tree: CommentedModule,
        settings: InsertSettings,
    ) -> None:
        """Bind the existing module and explicit insertion policy.

        Args:
            tree (CommentedModule): The caller's mutable comment-aware AST.
            settings (InsertSettings): Explicit runtime transformation choices.

        Raises:
            ValueError: The preferred helper name is not a Python identifier.

        """
        if (
            not settings.helper_name.isidentifier()
            or iskeyword(settings.helper_name)
            or settings.helper_name.startswith("__")
        ):
            msg: str = "The print helper name must be a Python identifier."
            raise ValueError(msg)
        self._tree: CommentedModule = tree
        self._settings: InsertSettings = settings

    def run(self) -> InsertChanges:
        """Rewrite proven builtin print names and inject native helper nodes.

        Returns:
            InsertChanges:
                Actual mutations and explicit binding-related refusals.

        """
        numeric: MagicChanges = extract_magic(
            tree=self._tree,
            scope=self._settings.magic_scope,
        )
        if not self._settings.replace_print:
            return InsertChanges(
                print_calls_changed=0,
                helper_name=None,
                skipped=numeric.skipped,
                numeric_values_changed=numeric.values_changed,
                numeric_constants_added=numeric.constants_added,
            )
        scopes: ScopeGraph = self._tree.semantic.scopes
        targets: list[Name] = []
        skipped: list[str] = list(numeric.skipped)
        wildcard: bool = any(
            isinstance(node, ImportFrom)
            and any(item.name == "*" for item in node.names)
            for node in walk(node=self._tree)
        )
        for node in walk(node=self._tree):
            if not isinstance(node, Call) or not isinstance(node.func, Name):
                continue
            function: Name = node.func
            if function.id != "print":
                continue
            identity: int = scopes.identities.node_id(node=function)
            scope_id: int | None = scopes.node_scopes.get(identity)
            if (
                wildcard
                or scope_id is None
                or scopes.resolve(
                    name="print",
                    scope_id=scope_id,
                )
                is not None
            ):
                skipped.append(
                    f"line {node.lineno}: print binding not builtin",
                )
                continue
            targets.append(function)
        if not targets:
            return InsertChanges(
                print_calls_changed=0,
                helper_name=None,
                skipped=tuple(skipped),
                numeric_values_changed=numeric.values_changed,
                numeric_constants_added=numeric.constants_added,
            )
        names: set[str] = {symbol.name for symbol in scopes.symbols.values()}
        names.update(
            node.id for node in walk(node=self._tree) if isinstance(node, Name)
        )
        helper: str = self._fresh(
            preferred=self._settings.helper_name,
            names=names,
        )
        builtins: str = self._fresh(preferred="_astart_builtins", names=names)
        path: str = self._fresh(preferred="_astart_pathlib", names=names)
        typing_name: str = self._fresh(
            preferred="_astart_typing",
            names=names,
        )
        printable: str = self._fresh(
            preferred="_astart_Printable",
            names=names,
        )
        writable: str = self._fresh(preferred="_astart_Writable", names=names)
        flushing: str = self._fresh(
            preferred="_astart_FlushingWritable",
            names=names,
        )
        added: list[stmt] = [
            Import(names=[alias(name="builtins", asname=builtins)]),
            Import(names=[alias(name="pathlib", asname=path)]),
            Import(names=[alias(name="typing", asname=typing_name)]),
            *_print_protocols(
                builtins=builtins,
                typing_name=typing_name,
                printable=printable,
                writable=writable,
                flushing=flushing,
            ),
            _print_helper(
                name=helper,
                bindings=_HelperNames(
                    builtins=builtins,
                    path=path,
                    typing_name=typing_name,
                    printable=printable,
                    writable=writable,
                    flushing=flushing,
                ),
            ),
        ]
        position: int = 0
        for statement in self._tree.body:
            if isinstance(statement, (Import, ImportFrom)) or (
                position == 0
                and isinstance(statement, Expr)
                and isinstance(statement.value, Constant)
                and isinstance(statement.value.value, str)
            ):
                position += 1
            else:
                break
        self._tree.body[position:position] = added
        for target in targets:
            target.id = helper
        return InsertChanges(
            print_calls_changed=len(targets),
            helper_name=helper,
            skipped=tuple(skipped),
            numeric_values_changed=numeric.values_changed,
            numeric_constants_added=numeric.constants_added,
        )

    @staticmethod
    def _fresh(*, preferred: str, names: set[str]) -> str:
        """Allocate a deterministic name unused in any lexical scope.

        Args:
            preferred (str): Base identifier.
            names (set[str]): Existing bindings/reads, updated with the chosen
                spelling.

        Returns:
            str: Collision-free identifier.

        """
        candidate: str = preferred
        ordinal: int = 1
        while candidate in names:
            ordinal += 1
            candidate = f"{preferred}_{ordinal}"
        names.add(candidate)
        return candidate


def insert_tree(
    *,
    tree: CommentedModule,
    settings: InsertSettings,
) -> InsertChanges:
    """Apply explicit insertion choices to existing native AST nodes.

    Args:
        tree (CommentedModule): Authoritative mutable module.
        settings (InsertSettings): Runtime rewrites selected by the caller.

    Returns:
        InsertChanges: Mutation counts and refusal reasons.

    """
    return AstInserter(tree=tree, settings=settings).run()
