"""Python AST extensions that preserve tokenizer comments across edits."""

from __future__ import annotations

from ast import (
    AST,
    Assign,
    AsyncFor,
    AsyncFunctionDef,
    AsyncWith,
    ClassDef,
    Constant,
    Expr,
    For,
    FunctionDef,
    If,
    Match,
    Module,
    Try,
    TryStar,
    TypeIgnore,
    While,
    With,
    dump,
    fix_missing_locations,
    iter_child_nodes,
    parse,
    stmt,
    unparse,
    walk,
)
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from io import StringIO
from itertools import pairwise
from pathlib import PurePosixPath
from shlex import quote as quote_shell
from shlex import split as split_shell
from tokenize import COMMENT, generate_tokens
from typing import TYPE_CHECKING, ClassVar, Self, cast, final
from weakref import ref

from astart.docstrings import (
    DocEntry,
    DocstringNode,
    DocStyle,
    ModuleDocstringNode,
    collect_docstrings,
    parse_docstring,
)
from astart.docstrings.layout import preserve_docstring_content
from astart.semantic.analyzer import SemanticAnalyzer
from astart.source.comment_directives import (
    DirectiveParser,
    SuppressionRule,
    SuppressionSpec,
    control_kind,
)
from astart.source.delta import ChangeSet, IncrementalSourceGraph
from astart.source.formatting import (
    EmissionPlan,
    FormatPreservationError,
    FormatPreserver,
)
from astart.source.node_attributes import (
    initialize_node,
    list_items,
    write_attribute,
)
from astart.source.tokens import (
    LexicalToken,
    SourceSpan,
    SourceTokenizer,
    TokenAwareMixin,
    TokenSnapshot,
    isolate_shared_ast_nodes,
)
from astart.source.transactions import AnnotationTransaction
from astart.transforms.typeuniondict import TypeUnionDict, TypeUnionDictType

type ListStr = list[str]
type TupleIntInt = tuple[int, int]

if TYPE_CHECKING:
    from ast import Call
    from collections.abc import Iterable
    from pathlib import Path
    from types import GenericAlias, UnionType

    from astart.graph.graph.document import AstDocument
    from astart.semantic.graph_conversion import GraphConversion
    from astart.semantic.type_inference import (
        TypeConstraintSolver,
        TypeInference,
    )
    from astart.semantic.typing_contracts import (
        BoundCall,
        CallableContract,
        ContractDiagnostic,
    )
    from astart.semantic.values import AbstractValue
type UnionMember = type | GenericAlias | UnionType


class Comment(AST):
    """Comment node exposed by ``ast.walk`` without changing executable suites.

    Attributes:
        text (str): Comment including its initial hash character.
        inline (bool): Whether code precedes the comment on its original source
            line.
        lineno (int): Original one-based line number.
        col_offset (int): Original zero-based UTF-8 byte column.
        end_lineno (int): Last source line occupied by the comment.
        end_col_offset (int): UTF-8 byte column after the comment.
        _field_types (ClassVar[TypeUnionDictType]): TODO.
        _fields (ClassVar[tuple[str, ...]]): TODO.
        _attributes (ClassVar[tuple[str, ...]]): TODO.

    Raises:
        ValueError: If the comment is not a single valid comment token.

    """

    text: str
    inline: bool
    lineno: int
    col_offset: int
    end_lineno: int
    end_col_offset: int
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "text": str,
            "inline": bool,
        },
    )
    _fields: ClassVar[tuple[str, ...]] = ("text", "inline")
    _attributes: ClassVar[tuple[str, ...]] = (
        "lineno",
        "col_offset",
        "end_lineno",
        "end_col_offset",
    )

    def __init__(
        self,
        *,
        text: str,
        inline: bool,
        lineno: int,
        col_offset: int,
    ) -> None:
        """Build a comment with AST-compatible source coordinates.

        Args:
            text (str): Text of exactly one comment token.
            inline (bool): True when source code precedes this token on its
                line.
            lineno (int): One-based line location.
            col_offset (int): Zero-based UTF-8 byte column.

        Raises:
            ValueError: If the text or position is invalid.

        """
        if not text.startswith("#") or "\n" in text or "\r" in text:
            msg: str = "A comment must begin with # and occupy one line."
            raise ValueError(msg)
        if lineno < 1 or col_offset < 0:
            msg = "Comment locations must be nonnegative and lines one-based."
            raise ValueError(msg)
        initialize_node(
            node=self,
            text=text,
            inline=inline,
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=lineno,
            end_col_offset=col_offset + len(text.encode(encoding="utf-8")),
        )


@final
class CommentControl(AST):
    """Native encoding, region or launcher semantics owned by one comment.

    Attributes:
        kind (str): Recognized control family.
        _fields (ClassVar[tuple[str, ...]]): TODO.
        _field_types (ClassVar[TypeUnionDictType]): TODO.

    """

    kind: str
    _fields: ClassVar[tuple[str, ...]] = ("kind",)
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "kind": str,
        },
    )

    def __init__(self, *, kind: str) -> None:
        """Create control metadata for the existing comment token.

        Args:
            kind (str): Parsed encoding, region or launcher family.

        """
        initialize_node(node=self, kind=kind)


def union(*types: UnionMember | None) -> UnionMember:
    """Construct a union type from the supplied types.

    Args:
        *types (UnionMember | None): Types to combine, including None.

    Returns:
        UnionMember: The resulting union or individual type.

    Raises:
        TypeError: If no types are provided.

    """
    if not types:
        msg: str = "At least one type is required."
        raise TypeError(msg)

    members: tuple[UnionMember, ...] = tuple(
        type(None) if member is None else member for member in types
    )
    result: UnionMember = members[0]
    for member in members[1:]:
        result = result | member
    return result


@final
class SingleLineComment(Comment):
    """A non-suppression comment, optionally owning source-control metadata.

    Attributes:
        control (CommentControl | None): Native control child, or None for
            ordinary prose.
        _fields (ClassVar[tuple[str, ...]]): TODO.
        _field_types (ClassVar[TypeUnionDictType]): TODO.

    """

    control: CommentControl | None
    _fields: ClassVar[tuple[str, ...]] = ("text", "inline", "control")
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "text": str,
            "inline": bool,
            "control": (CommentControl, None),
        },
    )

    def __init__(
        self,
        *,
        text: str,
        inline: bool,
        lineno: int,
        col_offset: int,
        control: CommentControl | None = None,
    ) -> None:
        """Construct a comment token and its optional parsed control child.

        Args:
            text (str): Exact comment token including its hash.
            inline (bool): Whether executable code precedes the token.
            lineno (int): One-based source line.
            col_offset (int): UTF-8 byte column.
            control (CommentControl | None): Parsed encoding/region/launcher
                semantics.

        Raises:
            ValueError: Text is not one comment or its location is invalid.

        """
        if (
            not text.startswith("#")
            or "\n" in text
            or "\r" in text
            or lineno < 1
            or col_offset < 0
        ):
            msg: str = (
                "A comment requires one # token and a valid source location."
            )
            raise ValueError(msg)
        initialize_node(
            node=self,
            text=text,
            inline=inline,
            control=control,
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=lineno,
            end_col_offset=col_offset + len(text.encode(encoding="utf-8")),
        )


@final
class SuppressionComment(Comment):
    """Comment containing a recognized lint, type or formatter directive.

    Attributes:
        tool (str): Checker or formatter that understands the directive.
        action (str): Suppression action: ignore, disable, enable, off, on or
            skip.
        scope (str): Recognized lexical scope, e.g. line, block or file.
        rules (list[SuppressionRule]): AST nodes for rule identifiers,
            excluding wildcard suppressions.
        all_rules (bool): True for directives without an explicit rule list.
        trailing (str): Trailing retained as str by this instance.
        form (str): Parsed directive family used for semantic rendering.
        _field_types (ClassVar[TypeUnionDictType]): TODO.
        _fields (ClassVar[tuple[str, ...]]): TODO.

    """

    tool: str
    action: str
    scope: str
    rules: list[SuppressionRule]
    all_rules: bool
    trailing: str
    form: str
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "text": str,
            "inline": bool,
            "tool": str,
            "action": str,
            "scope": str,
            "rules": list[SuppressionRule],
            "all_rules": bool,
            "trailing": str,
            "form": str,
        },
    )
    _fields: ClassVar[tuple[str, ...]] = (
        "text",
        "inline",
        "tool",
        "action",
        "scope",
        "rules",
        "all_rules",
        "trailing",
        "form",
    )

    def __init__(
        self,
        *,
        text: str,
        inline: bool,
        lineno: int,
        col_offset: int,
        spec: SuppressionSpec,
    ) -> None:
        """Create a semantic suppression comment.

        Args:
            text (str): Original token including hash.
            inline (bool): Whether code precedes the comment.
            lineno (int): Source line.
            col_offset (int): Byte column.
            spec (SuppressionSpec): Normalized directive semantics.

        Raises:
            ValueError: If the text or position is invalid.

        """
        if not text.startswith("#") or "\n" in text or "\r" in text:
            msg: str = "A suppression must be a single # comment token."
            raise ValueError(msg)
        if lineno < 1 or col_offset < 0:
            msg = "Comment locations must be nonnegative and lines one-based."
            raise ValueError(msg)
        initialize_node(
            node=self,
            text=text,
            inline=inline,
            tool=spec.tool,
            action=spec.action,
            scope=spec.scope,
            rules=spec.rules,
            all_rules=spec.all_rules,
            trailing=spec.trailing,
            form=spec.form,
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=lineno,
            end_col_offset=col_offset + len(text.encode(encoding="utf-8")),
        )

    def render(self) -> str:
        """Generate a directive from normalized checker, scope and rule nodes.

        Returns:
            str: Validated suppression comment text
                containing updated rule codes.

        Raises:
            ValueError: If the directive tool is unsupported or invalid.

        """
        return f"# {self._render_body()}{self.trailing}"

    def _render_body(self) -> str:
        """Render the checker-specific suppression directive body.

        Returns:
            str: Directive text without its comment prefix or trailing suffix.

        Raises:
            ValueError: If the suppression tool is unsupported.

        """
        codes: str = ", ".join(rule.code for rule in self.rules)
        if self.tool == "flake8/ruff":
            return f"noqa: {codes}" if codes else "noqa"
        if self.tool == "ruff":
            return f"ruff: noqa: {codes}" if codes else "ruff: noqa"
        if self.tool in ("pylint", "local-checker"):
            return (
                (f"{self.tool}: {self.action}={codes}")
                if codes
                else (f"{self.tool}: {self.action}")
            )
        if self.tool in ("type", "pyright", "basedpyright"):
            return (
                (f"{self.tool}: ignore[{codes}]")
                if codes
                else (f"{self.tool}: ignore")
            )
        return self._render_tool_body(codes=codes)

    def _render_tool_body(self, *, codes: str) -> str:
        """Render directives for formatters, coverage and niche checkers.

        Args:
            codes (str): Comma-separated rule identifiers for this directive.

        Returns:
            str: Tool-specific directive body text.

        Raises:
            ValueError: If the suppression tool is unsupported.

        """
        if self.tool in ("fmt", "autopep8", "isort"):
            body: str = f"{self.tool}: {self.action}"
            if self.tool == "isort" and self.scope == "file":
                body = "isort: skip_file"
            return body
        if self.tool == "coverage":
            return (
                "coverswitch: skip"
                if self.form == "coverswitch"
                else "pragma: nomutate"
                if self.action == "skip"
                else "pragma: no cover"
            )
        if self.tool == "bandit":
            return f"nosec: {codes}" if codes else "nosec"
        if self.tool == "sourcery":
            return f"sourcery skip: {codes}"
        if self.tool == "xenon":
            return "xenon: ignore"
        msg: str = f"Unsupported suppression tool: {self.tool}"
        raise ValueError(msg)


@final
class ShebangArgument(AST):
    """A parsed launcher or interpreter command-line argument.

    Attributes:
        value (str): Argument spelling without shell quotation.
        role (str): An option or positional argument.
        _field_types (ClassVar[TypeUnionDictType]): TODO.
        _fields (ClassVar[tuple[str, ...]]): TODO.

    """

    value: str
    role: str
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "value": str,
            "role": str,
        },
    )
    _fields: ClassVar[tuple[str, ...]] = ("value", "role")

    def __init__(self, *, value: str, role: str = "argument") -> None:
        """Initialize an editable interpreter argument.

        Args:
            value (str): Parsed argument spelling.
            role (str): Semantic argument category.

        """
        initialize_node(node=self, value=value, role=role)


@final
class ShebangVariable(AST):
    """An editable environment variable assignment in an env shebang.

    Attributes:
        name (str): POSIX environment variable name.
        value (str): Assignment value, without quoting.
        _field_types (ClassVar[TypeUnionDictType]): TODO.
        _fields (ClassVar[tuple[str, ...]]): TODO.

    """

    name: str
    value: str
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "name": str,
            "value": str,
        },
    )
    _fields: ClassVar[tuple[str, ...]] = ("name", "value")

    def __init__(self, *, name: str, value: str) -> None:
        """Create an environment assignment.

        Args:
            name (str): Variable name.
            value (str): Its value.

        """
        initialize_node(node=self, name=name, value=value)


@final
class ShebangInterpreter(AST):
    """The interpreter command executed by the kernel or env launcher.

    Attributes:
        path (str): Interpreter path or env-resolved command name.
        via_env (bool): Whether env resolves the interpreter through PATH.
        _field_types (ClassVar[TypeUnionDictType]): TODO.
        _fields (ClassVar[tuple[str, ...]]): TODO.

    """

    path: str
    via_env: bool
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "path": str,
            "via_env": bool,
        },
    )
    _fields: ClassVar[tuple[str, ...]] = ("path", "via_env")

    def __init__(self, *, path: str, via_env: bool) -> None:
        """Initialize a semantic interpreter node.

        Args:
            path (str): Original interpreter path or command.
            via_env (bool): Whether ``env`` is the launcher.

        """
        initialize_node(node=self, path=path, via_env=via_env)

    @property
    def name(self) -> str:
        """Return the basename of the current interpreter path.

        Returns:
            str: str produced by this operation.

        """
        return PurePosixPath(self.path).name


@final
class ShebangNode(Comment):
    """Special first-line shebang with traversable interpreter components.

    Args and POSIX quoting are parsed as far as possible. This is a lexical
    model, not an emulation of every kernel's shebang argument rules.

    Attributes:
        launcher (ShebangInterpreter | None): The optional ``/usr/bin/env``
            executable.
        interpreter (ShebangInterpreter): Interpreted executable or
            env-resolved command.
        launcher_options (list[ShebangArgument]): Options passed to the env
            launcher.
        environment (list[ShebangVariable]): Environment variable assignments
            for env.
        arguments (list[ShebangArgument]): Interpreter arguments.
        _field_types (ClassVar[TypeUnionDictType]): TODO.
        _fields (ClassVar[tuple[str, ...]]): TODO.

    """

    launcher: ShebangInterpreter | None
    interpreter: ShebangInterpreter
    launcher_options: list[ShebangArgument]
    environment: list[ShebangVariable]
    arguments: list[ShebangArgument]
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "text": str,
            "inline": bool,
            "launcher": (ShebangInterpreter, None),
            "interpreter": ShebangInterpreter,
            "launcher_options": list[ShebangArgument],
            "environment": list[ShebangVariable],
            "arguments": list[ShebangArgument],
        },
    )
    _fields: ClassVar[tuple[str, ...]] = (
        "text",
        "inline",
        "launcher",
        "interpreter",
        "launcher_options",
        "environment",
        "arguments",
    )

    def __init__(self, *, text: str, lineno: int, col_offset: int) -> None:
        """Parse the special comment on physical line one.

        Args:
            text (str): Complete source shebang comment.
            lineno (int): Source line (always 1).
            col_offset (int): UTF-8 column (always zero).

        Raises:
            ValueError: If this operation cannot satisfy its documented
                contract.

        """
        if (
            not text.startswith("#!")
            or "\n" in text
            or "\r" in text
            or (lineno != 1)
            or (col_offset != 0)
        ):
            msg: str = "A shebang must be a first-line, unbroken #! comment."
            raise ValueError(msg)
        initialize_node(
            node=self,
            text=text,
            inline=False,
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=lineno,
            end_col_offset=len(text.encode(encoding="utf-8")),
            launcher=None,
            interpreter=ShebangInterpreter(path="", via_env=False),
            launcher_options=list[ShebangArgument](),
            environment=list[ShebangVariable](),
            arguments=list[ShebangArgument](),
        )
        try:
            parts: ListStr = split_shell(s=text[2:].strip())
        except ValueError:
            parts = text[2:].split()
        first: str = parts[0] if parts else ""
        via_env: bool = PurePosixPath(first).name == "env"
        self.launcher = (
            ShebangInterpreter(path=first, via_env=False) if via_env else None
        )
        self.launcher_options = []
        self.environment = []
        remainder: ListStr = parts[1:]
        if via_env:
            index: int = 0
            while index < len(remainder):
                part: str = remainder[index]
                if part in (
                    "-S",
                    "--split-string",
                    "-i",
                    "--ignore-environment",
                ):
                    self.launcher_options.append(
                        ShebangArgument(value=part, role="env_option"),
                    )
                elif part in ("-u", "--unset") and index + 1 < len(remainder):
                    self.launcher_options.extend(
                        (
                            ShebangArgument(value=part, role="env_option"),
                            ShebangArgument(
                                value=remainder[index + 1],
                                role="env_operand",
                            ),
                        ),
                    )
                    index += 1
                elif part.startswith("-") and part != "--":
                    self.launcher_options.append(
                        ShebangArgument(value=part, role="env_option"),
                    )
                elif part == "--":
                    self.launcher_options.append(
                        ShebangArgument(value=part, role="env_option"),
                    )
                    index += 1
                    break
                elif (
                    "=" in part
                    and part.split(sep="=", maxsplit=1)[0].isidentifier()
                ):
                    name, value = part.split(sep="=", maxsplit=1)
                    self.environment.append(
                        ShebangVariable(name=name, value=value),
                    )
                else:
                    break
                index += 1
            remainder = remainder[index:]
        self.interpreter = ShebangInterpreter(
            path=remainder[0] if via_env and remainder else first,
            via_env=via_env,
        )
        self.arguments = [
            ShebangArgument(
                value=part,
                role="option" if part.startswith("-") else "argument",
            )
            for part in (remainder[1:] if via_env else remainder)
        ]

    def render(self) -> str:
        """Serialize edited components into a canonical POSIX shebang.

        Returns:
            str: Single-line, shell-quoted shebang comment.

        Raises:
            ValueError: If edited arguments introduce a newline.

        """
        parts: ListStr = (
            [self.launcher.path] if self.launcher is not None else []
        )
        parts.extend(option.value for option in self.launcher_options)
        parts.extend(
            (f"{variable.name}={variable.value}")
            for variable in self.environment
        )
        parts.append(self.interpreter.path)
        parts.extend(argument.value for argument in self.arguments)
        if any("\n" in part or "\r" in part for part in parts):
            msg: str = "Shebang components must not contain a newline."
            raise ValueError(msg)
        if not self.interpreter.path:
            msg = "An edited shebang requires an interpreter executable."
            raise ValueError(msg)
        if any(not var.name.isidentifier() for var in self.environment):
            msg = "An env shebang assignment requires a valid variable name."
            raise ValueError(msg)
        encoded: ListStr = (
            [quote_shell(s=self.launcher.path)]
            if self.launcher is not None
            else []
        )
        encoded.extend(
            quote_shell(s=part.value) for part in self.launcher_options
        )
        encoded.extend(
            (f"{var.name}={quote_shell(s=var.value)}")
            for var in self.environment
        )
        encoded.append(quote_shell(s=self.interpreter.path))
        encoded.extend(quote_shell(s=part.value) for part in self.arguments)
        return "#!" + " ".join(encoded)


class CommentGroup(AST):
    """A logical comment cluster with at most one blank line inside.

    Its members are the same objects contained in the module's ``comments``
    list. AST traversal visits each real comment once through
    ``comment_blocks``.

    Attributes:
        comments (list[Comment]): Source-order comments in this cluster.
        blank_lines (list[int]): Count of blank source lines between
            consecutive comments.
        col_offset (int): Col offset retained as int by this instance.
        end_col_offset (int): End col offset retained as int by this instance.
        end_lineno (int): End lineno retained as int by this instance.
        lineno (int): Lineno retained as int by this instance.
        _field_types (ClassVar[TypeUnionDictType]): TODO.
        _fields (ClassVar[tuple[str, ...]]): TODO.
        _attributes (ClassVar[tuple[str, ...]]): TODO.

    """

    comments: list[Comment]
    blank_lines: list[int]
    lineno: int
    col_offset: int
    end_lineno: int
    end_col_offset: int
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "comments": list[Comment],
            "blank_lines": list[int],
        },
    )
    _fields: ClassVar[tuple[str, ...]] = ("comments", "blank_lines")
    _attributes: ClassVar[tuple[str, ...]] = (
        "lineno",
        "col_offset",
        "end_lineno",
        "end_col_offset",
    )

    def __init__(
        self,
        *,
        comments: list[Comment],
        blank_lines: list[int],
    ) -> None:
        """Create a grouping without duplicating comment nodes.

        Args:
            comments (list[Comment]): Consecutive comments belonging to one
                cluster.
            blank_lines (list[int]): Separators between each consecutive pair.

        Raises:
            ValueError: If separators and members are inconsistent.

        """
        if not comments or len(blank_lines) != len(comments) - 1:
            msg: str = "A comment group needs members and matching separators."
            raise ValueError(msg)
        initialize_node(
            node=self,
            comments=comments,
            blank_lines=blank_lines,
            lineno=comments[0].lineno,
            col_offset=comments[0].col_offset,
            end_lineno=comments[-1].end_lineno,
            end_col_offset=comments[-1].end_col_offset,
        )

    @property
    def text(self) -> str:
        """Reconstruct the cluster text, including intentional empty lines.

        Returns:
            str: str produced by this operation.

        """
        return "".join(
            (
                ("\n" * (1 + self.blank_lines[index - 1]) if index else "")
                + comment.text
                for index, comment in enumerate(iterable=self.comments)
            ),
        )


@final
class MultilineComment(CommentGroup):
    """Physically contiguous standalone comment lines, without blank gaps."""


def _classify_comment(
    *,
    text: str,
    inline: bool,
    lineno: int,
    col_offset: int,
    is_file_header: bool,
) -> Comment:
    """Build semantic comment nodes once at the COMMENT token boundary.

    Args:
        text (str): Tokenizer-owned comment token.
        inline (bool): Whether executable source precedes the token.
        lineno (int): One-based physical line.
        col_offset (int): UTF-8 byte column.
        is_file_header (bool): Whether this precedes executable source.

    Returns:
        Comment: Ordinary, control, launcher or suppression AST node.

    """
    if lineno == 1 and col_offset == 0 and text.startswith("#!"):
        return ShebangNode(text=text, lineno=lineno, col_offset=col_offset)
    body: str = text[1:].lstrip()
    spec: SuppressionSpec | None = DirectiveParser(
        body=body,
        inline=inline,
        file_header=is_file_header,
    ).parse()
    if spec is not None:
        return SuppressionComment(
            text=text,
            inline=inline,
            lineno=lineno,
            col_offset=col_offset,
            spec=spec,
        )
    kind: str | None = control_kind(body=body)
    return SingleLineComment(
        text=text,
        inline=inline,
        lineno=lineno,
        col_offset=col_offset,
        control=CommentControl(kind=kind) if kind is not None else None,
    )


def docstring_constant(*, doc: DocstringNode) -> Constant:
    """Return the string constant that holds an executable docstring.

    Args:
        doc (DocstringNode): Structured docstring node wrapping a real
            expression.

    Returns:
        Constant: The string ``Constant`` node inside the docstring expression.

    Raises:
        ValueError: If the node does not wrap a string constant.

    """
    expression: Expr | None = doc.expression
    if expression is None or not isinstance(expression.value, Constant):
        msg: str = "A docstring node must wrap a string constant."
        raise ValueError(msg)
    return expression.value


def docstring_text(*, doc: DocstringNode) -> str:
    """Return the text of an executable docstring.

    Args:
        doc (DocstringNode): Structured docstring node wrapping a real
            expression.

    Returns:
        str: The string value stored in the docstring constant.

    Raises:
        TypeError: If the constant does not hold a string.

    """
    value: object = docstring_constant(doc=doc).value
    if not isinstance(value, str):
        msg: str = "A docstring constant must hold a string."
        raise TypeError(msg)
    return value


def _group_comments(
    *,
    comments: list[Comment],
    lines: ListStr,
    positions: dict[int, TupleIntInt] | None = None,
    previous: list[Comment | CommentGroup] | None = None,
) -> list[Comment | CommentGroup]:
    """Partition comments into singleton, multiline and separated clusters.

    Args:
        comments (list[Comment]): Source-ordered individual comment nodes.
        lines (ListStr): Current source lines, including newline endings.
        positions (dict[int, TupleIntInt] | None): Optional emitted (line,
            UTF-8 column) for moved comments.
        previous (list[Comment | CommentGroup] | None): Existing groups whose
            identities may be retained.

    Returns:
        list[Comment | CommentGroup]: AST nodes that traverse every individual
            comment exactly once.

    """
    blocks: list[Comment | CommentGroup] = []
    current: list[Comment] = []
    gaps: list[int] = []
    retained: dict[
        tuple[type[CommentGroup], tuple[int, ...], tuple[int, ...]],
        CommentGroup,
    ] = {
        (
            MultilineComment
            if isinstance(block, MultilineComment)
            else CommentGroup,
            tuple(id(item) for item in block.comments),
            tuple(block.blank_lines),
        ): block
        for block in previous or []
        if isinstance(block, CommentGroup)
    }

    def locate(comment: Comment) -> TupleIntInt:
        """Read an emitted position or the original lexical coordinate.

        Args:
            comment (Comment): Comment supplied as Comment for this operation.

        Returns:
            TupleIntInt: tuple[int, int] produced by this operation.

        """
        return (
            positions.get(id(comment), (comment.lineno, comment.col_offset))
            if positions is not None
            else (comment.lineno, comment.col_offset)
        )

    def flush() -> None:
        """Commit the current contiguous logical cluster."""
        if len(current) == 1:
            blocks.append(current[0])
        elif current:
            block_type: type[CommentGroup] = (
                MultilineComment if not any(gaps) else CommentGroup
            )
            key: tuple[
                type[CommentGroup],
                tuple[int, ...],
                tuple[int, ...],
            ] = (block_type, tuple(id(item) for item in current), tuple(gaps))
            block: CommentGroup = retained.get(key) or block_type(
                comments=list(current),
                blank_lines=list(gaps),
            )
            if positions is not None:
                block.lineno, block.col_offset = locate(comment=current[0])
                block.end_lineno, _ = locate(comment=current[-1])
            blocks.append(block)
        current.clear()
        gaps.clear()

    for comment in comments:
        if current:
            last_comment: Comment = current[-1]
            previous_line, previous_column = locate(comment=last_comment)
            current_line, current_column = locate(comment=comment)
            gap: int = current_line - previous_line - 1
            separate: bool = (
                last_comment.inline
                or comment.inline
                or current_column != previous_column
                or (gap < 0)
                or (gap > 1)
                or any(
                    lines[number].strip()
                    for number in range(previous_line, current_line - 1)
                )
            )
            if separate:
                flush()
            else:
                gaps.append(gap)
        current.append(comment)
    flush()
    return blocks


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _Suite:
    """A mutable statement sequence and its original lexical range.

    Attributes:
        statements (list[stmt]): Mutable AST statement suite.
        start (int): First original source line belonging to this suite.
        end (int): Exclusive final source line belonging to this suite.
        indent (int): Expected indentation in original source.
        depth (int): Structural nesting depth.
        header_line (int | None): Original line of this suite's compound or
            clause header.

    """

    statements: list[stmt]
    start: int
    end: int
    indent: int
    depth: int
    header_line: int | None


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _Insertion:
    """Pending marker placement inside a statement suite.

    Attributes:
        index (int): Insertion index in the original unmodified suite.
        comment_index (int): Index within the public comment collection.
        inline (bool): Whether to try to attach to the preceding statement
            line.
        header (bool): Whether the anchor is a compound-statement header.

    """

    index: int
    comment_index: int
    inline: bool
    header: bool


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _FieldContext:
    """Position of one child node inside its parent's AST field.

    Attributes:
        parent (AST): Parsed AST node owning the field.
        field_name (str): Name of the AST field holding the node.
        index (int): Position inside a list-valued field, if applicable.

    """

    parent: AST
    field_name: str
    index: int = 0


@final
class _TokenIndexer:
    """Assign validated parser spans to mutable AST node identities.

    Attributes:
        tokenizer: Tokenizer for the re-emitted current source.
        previous: Previous immutable snapshots by node identity.
        mapped: Current snapshots collected during this traversal.

    """

    def __init__(
        self,
        *,
        tokenizer: SourceTokenizer,
        previous: dict[int, TokenSnapshot],
    ) -> None:
        """Prepare a fresh mapping pass for one source revision.

        Args:
            tokenizer (SourceTokenizer): Tokenizer bound to the emitted source
                revision.
            previous (dict[int, TokenSnapshot]): Snapshot index from the
                preceding refresh.

        """
        self.tokenizer: SourceTokenizer = tokenizer
        self.previous: dict[int, TokenSnapshot] = previous
        self.mapped: dict[int, TokenSnapshot] = {}

    def map_code(
        self,
        *,
        original: AST,
        parsed_node: AST,
        inherited: TokenSnapshot,
        context: _FieldContext | None = None,
    ) -> None:
        """Map token locations by structural AST position.

        Args:
            original (AST): Mutable user-facing executable node.
            parsed_node (AST): Corresponding current parser-produced AST node.
            inherited (TokenSnapshot): Nearest parent snapshot when no own span
                exists.
            context (_FieldContext | None): Parsed parent field position, for
                operator lookup.

        """
        found: SourceSpan | None = self.tokenizer.span_of(node=parsed_node)
        if (
            found is None
            and context is not None
            and (context.field_name in ("op", "ops"))
        ):
            found = self.tokenizer.operator_span(
                parent=context.parent,
                field=context.field_name,
                index=context.index,
            )
        info: TokenSnapshot = (
            self.tokenizer.snapshot_cached(
                span=found,
                previous=self.previous.get(id(original)),
            )
            if found is not None
            else self.tokenizer.snapshot_cached(
                span=inherited.span,
                provenance="inherited",
                previous=self.previous.get(id(original)),
            )
        )
        self.mapped[id(original)] = info
        for field in original._fields:
            old: object = getattr(original, field, None)
            new: object = getattr(parsed_node, field, None)
            if isinstance(old, AST) and isinstance(new, AST):
                self.map_code(
                    original=old,
                    parsed_node=new,
                    inherited=info,
                    context=_FieldContext(
                        parent=parsed_node,
                        field_name=field,
                    ),
                )
            else:
                for ordinal, (old_item, new_item) in enumerate(
                    iterable=zip(
                        list_items(value=old),
                        list_items(value=new),
                        strict=False,
                    ),
                ):
                    if isinstance(old_item, AST) and isinstance(new_item, AST):
                        self.map_code(
                            original=old_item,
                            parsed_node=new_item,
                            inherited=info,
                            context=_FieldContext(
                                parent=parsed_node,
                                field_name=field,
                                index=ordinal,
                            ),
                        )

    def map_children(self, *, node: AST, inherited: TokenSnapshot) -> None:
        """Assign host-owned string/comment tokens to semantic subnodes.

        Args:
            node (AST): AST node to map and traverse.
            inherited (TokenSnapshot): Fallback parent tokens for nonlexical
                AST fields.

        """
        info: TokenSnapshot | None = self.mapped.get(id(node))
        if info is None:
            info = self.tokenizer.snapshot_cached(
                span=inherited.span,
                provenance="inherited",
                previous=self.previous.get(id(node)),
            )
            self.mapped[id(node)] = info
        for child in iter_child_nodes(node=node):
            self.map_children(node=child, inherited=info)


type _CompoundStatement = (
    FunctionDef
    | AsyncFunctionDef
    | ClassDef
    | If
    | While
    | For
    | AsyncFor
    | With
    | AsyncWith
    | Try
    | TryStar
    | Match
)


def _clause_start(
    *,
    keyword: str,
    first_statement: stmt,
    parent: stmt,
    lines: ListStr,
) -> int:
    """Find the actual clause header before its first body statement.

    Args:
        keyword (str): Clause token, such as ``else`` or ``finally``.
        first_statement (stmt): First executable statement of the clause.
        parent (stmt): Enclosing control-flow statement.
        lines (ListStr): Original source lines, including their newlines.

    Returns:
        int: One-based line number of the matching clause header.

    """
    for number in range(first_statement.lineno - 1, parent.lineno, -1):
        line: str = lines[number - 1]
        if len(line) - len(
            line.lstrip(" \t"),
        ) == parent.col_offset and line.strip().startswith(f"{keyword}:"):
            return number
    return first_statement.lineno


def _orelse_start(
    *,
    statement: If | While | For | AsyncFor,
    lines: ListStr,
) -> int:
    """Locate an ``else`` or ``elif`` clause header above its body.

    Args:
        statement (If | While | For | AsyncFor): Control-flow statement owning
            the clause.
        lines (ListStr): Original source lines, including their newlines.

    Returns:
        int: Header line of the else or elif clause.

    """
    first: stmt = statement.orelse[0]
    return (
        first.lineno
        if isinstance(first, If) and first.col_offset == statement.col_offset
        else _clause_start(
            keyword="else",
            first_statement=first,
            parent=statement,
            lines=lines,
        )
    )


def _nested_bodies(
    *,
    statement: _CompoundStatement,
    lower: int,
    lines: ListStr,
) -> list[tuple[list[stmt], int]]:
    """Enumerate direct child suites with their header start lines.

    Args:
        statement (_CompoundStatement): Compound statement whose clauses
            produce suites.
        lower (int): Header line of the compound statement itself.
        lines (ListStr): Original source lines, including their newlines.

    Returns:
        list[tuple[list[stmt], int]]: (body, start line) pairs, in clause
            order.

    """
    nested: list[tuple[list[stmt], int]] = []
    if isinstance(statement, (Try, TryStar)):
        nested.append((statement.body, lower))
        nested.extend(
            (handler.body, handler.lineno) for handler in statement.handlers
        )
        if statement.orelse:
            nested.append(
                (
                    statement.orelse,
                    _clause_start(
                        keyword="else",
                        first_statement=statement.orelse[0],
                        parent=statement,
                        lines=lines,
                    ),
                ),
            )
        if statement.finalbody:
            nested.append(
                (
                    statement.finalbody,
                    _clause_start(
                        keyword="finally",
                        first_statement=statement.finalbody[0],
                        parent=statement,
                        lines=lines,
                    ),
                ),
            )
    elif isinstance(statement, Match):
        nested.extend(
            (case.body, case.pattern.lineno) for case in statement.cases
        )
    else:
        nested.append((statement.body, lower))
        if (
            isinstance(statement, (If, While, For, AsyncFor))
            and statement.orelse
        ):
            nested.append(
                (
                    statement.orelse,
                    _orelse_start(statement=statement, lines=lines),
                ),
            )
    return nested


@final
class CommentedModule(TokenAwareMixin, Module):
    """An ``ast.Module`` with traversable comments and safe re-emission.

    The normal ``body`` contains only Python statements, so the instance
    remains compatible with compilers, transformers and ordinary AST visitors.
    Comment children are traversable through ``comment_blocks``; the flat
    ``comments`` list references those same nodes without duplicating visits.

    A structurally unchanged tree unparses byte-for-byte as the supplied source
    string. After edits, code is regenerated and comments are reconstructed at
    their nearest statement-suite anchors, with validation of the code AST.

    Attributes:
        comments: Flat lexical index of the traversable comment nodes.
        comment_blocks: Comment nodes and group nodes, in source order.
        docstrings: Normalized documentation nodes from Python definitions.
        _field_types (ClassVar[TypeUnionDictType]): TODO.
        _fields (ClassVar[tuple[str, ...]]): TODO.

    """

    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "body": list[stmt],
            "type_ignores": list[TypeIgnore],
            "comment_blocks": list[Comment | CommentGroup],
            "docstrings": list[DocstringNode],
        },
    )
    _fields: ClassVar[tuple[str, ...]] = (
        "body",
        "type_ignores",
        "comment_blocks",
        "docstrings",
    )

    def __init__(
        self,
        *,
        body: list[stmt],
        type_ignores: list[TypeIgnore],
        comments: list[Comment],
        source: str,
        docstrings: list[DocstringNode] | None = None,
    ) -> None:
        """Initialize an annotated module and capture its pristine state.

        Args:
            body (list[stmt]): Executable statements returned by Python's
                parser.
            type_ignores (list[TypeIgnore]): Type-ignore records from Python's
                parser.
            comments (list[Comment]): Tokenized comments in their original
                order.
            source (str): Exact original source string.
            docstrings (list[DocstringNode] | None): Optional externally
                prepared structured documentation.

        """
        super().__init__(body=body, type_ignores=type_ignores)
        self.comments: list[Comment] = comments
        self.comment_blocks: list[Comment | CommentGroup] = _group_comments(
            comments=comments,
            lines=source.splitlines(keepends=True),
        )
        self.docstrings: list[DocstringNode] = (
            docstrings
            if docstrings is not None
            else collect_docstrings(body=body)
        )
        isolate_shared_ast_nodes(root=self)
        self._doc_snapshots: dict[int, str] = {
            id(node): dump(node=node, include_attributes=True)
            for node in self.docstrings
        }
        self._supp_snapshots: dict[int, tuple[str, ...]] = {
            id(comment): self._suppression_signature(comment=comment)
            for comment in self.comments
            if isinstance(comment, SuppressionComment)
        }
        self._supp_texts: dict[int, str] = {
            id(comment): comment.text
            for comment in self.comments
            if isinstance(comment, SuppressionComment)
        }
        self._doc_rendered: dict[int, str] = {}
        self._source: str = source
        self._snapshot: str = dump(node=self, include_attributes=True)
        self._last_emission_plan: EmissionPlan | None = None
        self._token_version: int = 0
        self._token_fingerprint: str = ""
        self._current_source: str = ""
        self._source_tokenizer: SourceTokenizer | None = None
        self._token_snapshots: dict[int, TokenSnapshot] = {}
        self.source_graph: IncrementalSourceGraph = IncrementalSourceGraph(
            root=self,
        )
        self._token_classes: dict[type[AST], type[AST]] = {}
        self.token_provider = ref(self)
        self._shebang_snapshots: dict[int, tuple[str, ...]] = {
            id(comment): self._shebang_signature(shebang=comment)
            for comment in comments
            if isinstance(comment, ShebangNode)
        }
        self._shebang_texts: dict[int, str] = {
            id(comment): comment.text
            for comment in comments
            if isinstance(comment, ShebangNode)
        }
        self._original_statement_ids: set[int] = {
            id(node) for node in walk(node=self) if isinstance(node, stmt)
        }
        for node in walk(node=self):
            if id(node) in self._original_statement_ids:
                write_attribute(node=node, name="comment_original", value=True)
        self._bind_token_nodes()
        self._format_preserver: FormatPreserver = FormatPreserver(
            source=source,
            body=body,
        )
        self._format_doc_baseline: dict[int, tuple[str, str, str, str]] = {
            id(doc): (
                doc.summary,
                doc.description,
                doc.style,
                repr(tuple(dump(node=section) for section in doc.sections)),
            )
            for doc in self.docstrings
        }
        self._format_orig_comments: dict[int, TupleIntInt] = {}
        original_lines: ListStr = source.splitlines(keepends=True)
        original_offsets: list[int] = [0]
        for line in original_lines:
            original_offsets.append(original_offsets[-1] + len(line))
        for comment in comments:
            raw: str = original_lines[comment.lineno - 1]
            column: int = len(
                raw.encode(encoding="utf-8")[: comment.col_offset].decode(
                    encoding="utf-8",
                ),
            )
            begin: int = original_offsets[comment.lineno - 1] + column
            self._format_orig_comments[id(comment)] = (
                begin,
                begin + len(comment.text),
            )
        self._token_formatting: bool = False
        self._formatted_comment_positions: dict[int, TupleIntInt] = {}
        self._format_conflicts: str = "raise"
        self._semantic_model: SemanticAnalyzer | None = None

    @classmethod
    def parse(cls, source: str, *, filename: str = "<unknown>") -> Self:
        """Parse Python source including all genuine tokenizer comment tokens.

        Args:
            source (str): Python source string, preserving its original
                newlines.
            filename (str): Filename used for Python's syntax errors.

        Returns:
            Self: Traversable comment-aware AST module.

        Raises:
            SyntaxError: If the original Python source cannot be parsed.
            TokenError: If tokenization encounters an incomplete token.

        """
        module: Module = parse(
            source=source,
            filename=filename,
            mode="exec",
            type_comments=True,
        )
        lines: ListStr = source.splitlines(keepends=True)
        comments: list[Comment] = []
        first_code_line: int = min(
            (statement.lineno for statement in module.body),
            default=len(lines) + 1,
        )
        for token in generate_tokens(
            readline=StringIO(initial_value=source).readline,
        ):
            if token.type == COMMENT:
                line: str = lines[token.start[0] - 1]
                prefix: str = line[: token.start[1]]
                comments.append(
                    _classify_comment(
                        text=token.string,
                        inline=bool(prefix.strip()),
                        lineno=token.start[0],
                        col_offset=len(prefix.encode(encoding="utf-8")),
                        is_file_header=token.start[0] < first_code_line,
                    ),
                )
        tree: Self = cls(
            body=module.body,
            type_ignores=module.type_ignores,
            comments=comments,
            source=source,
        )
        tree.refresh_token_index()
        tree.source_graph.mark_baseline()
        return tree

    @property
    def semantic(self) -> SemanticAnalyzer:
        """Return a persistent lazy semantic graph for this mutable module.

        Semantic identities survive supported edits; value caches are
        invalidated when the AST's executable semantic structure changes.

        Returns:
            SemanticAnalyzer: SemanticAnalyzer produced by this operation.

        """
        if self._semantic_model is None:
            self._semantic_model = SemanticAnalyzer(root=self)
        else:
            self._semantic_model.refresh()
        return self._semantic_model

    @property
    def types(self) -> TypeConstraintSolver:
        """Return the shared type solver for the current AST revision.

        Returns:
            TypeConstraintSolver:
                TypeConstraintSolver produced by this operation.

        """
        return self.semantic.types

    @property
    def typing_diagnostics(self) -> tuple[ContractDiagnostic, ...]:
        """Return type contract violations for the current revision.

        Returns:
            tuple[ContractDiagnostic, ...]: tuple[ContractDiagnostic, ...]
                produced by this operation.

        """
        return self.semantic.typing_diagnostics

    @property
    def shebang(self) -> ShebangNode | None:
        """Return the structured first-line shebang, when one exists.

        Returns:
            ShebangNode | None: ShebangNode | None produced by this operation.

        """
        return next(
            (
                comment
                for comment in self.comments
                if isinstance(comment, ShebangNode)
            ),
            None,
        )

    @property
    def module_docstring(self) -> ModuleDocstringNode | None:
        """Return the special top-level module docstring, when present.

        Returns:
            ModuleDocstringNode | None:
                ModuleDocstringNode | None produced by this operation.

        """
        self._ensure_docstring_index()
        return next(
            (
                doc
                for doc in self.docstrings
                if isinstance(doc, ModuleDocstringNode)
            ),
            None,
        )

    @property
    def token_changes(self) -> ChangeSet:
        """Return the last verified identity-aware incremental change set.

        Returns:
            ChangeSet: ChangeSet produced by this operation.

        """
        self.refresh_token_index()
        return self.source_graph.last_change

    @property
    def token_stream(self) -> tuple[LexicalToken, ...]:
        """Expose the immutable, complete tokenizer output.

        Returns:
            tuple[LexicalToken, ...]: tuple[LexicalToken, ...] produced by this
                operation.

        Raises:
            RuntimeError: If this operation cannot satisfy its documented
                contract.

        """
        self.refresh_token_index()
        if self._source_tokenizer is None:
            msg: str = "The source tokenizer has not been initialized."
            raise RuntimeError(msg)
        return self._source_tokenizer.tokens

    @property
    def token_source(self) -> str:
        """Return the exact source text associated with current snapshots.

        Returns:
            str: Rendered source text produced by this operation.

        """
        self.refresh_token_index()
        return self._current_source

    @staticmethod
    def render_markers(
        source: str,
        *,
        markers: dict[str, tuple[Comment, bool, bool]],
        blank_lines_before: dict[str, int] | None = None,
    ) -> str:
        """Replace unparser placeholders with comments at valid indentation.

        Args:
            source (str): Unparser result containing standalone string markers.
            markers (dict[str, tuple[Comment, bool, bool]]): Marker lookup with
                desired comments and inline hints.
            blank_lines_before (dict[str, int] | None): Gaps to restore between
                original comments.

        Returns:
            str: Regenerated source with comments
                instead of placeholder statements.

        Raises:
            ValueError: If a marker cannot be accounted for exactly once.

        """
        rendered: ListStr = []
        seen: set[str] = set()
        for line in source.split(
            sep="\n",
        ):
            marker: str = line.strip().strip("'\"")
            if marker not in markers or line.strip() not in (
                repr(marker),
                (f'"{marker}"'),
                (f'"""{marker}"""'),
                (f"'''{marker}'''"),
            ):
                rendered.append(line)
                continue
            comment: Comment
            inline: bool
            header: bool
            comment, inline, header = markers[marker]
            if marker in seen:
                msg: str = "The unparser duplicated a comment marker."
                raise ValueError(msg)
            seen.add(marker)
            indentation: str = line[: len(line) - len(line.lstrip(" \t"))]
            if (
                inline
                and rendered
                and rendered[-1].strip()
                and (not rendered[-1].lstrip().startswith("#"))
                and (
                    (
                        header
                        and rendered[-1].rstrip().endswith(":")
                        and (
                            len(rendered[-1]) - len(rendered[-1].lstrip(" \t"))
                            < len(indentation)
                        )
                    )
                    or (
                        not header
                        and len(rendered[-1]) - len(rendered[-1].lstrip(" \t"))
                        == len(indentation)
                    )
                )
            ):
                rendered[-1] = f"{rendered[-1].rstrip()}  {comment.text}"
            else:
                needed: int = (
                    blank_lines_before.get(marker, 0)
                    if blank_lines_before is not None
                    else 0
                )
                existing: int = 0
                for previous_line in reversed(rendered):
                    if previous_line.strip():
                        break
                    existing += 1
                rendered.extend("" for _ in range(max(0, needed - existing)))
                rendered.append(f"{indentation}{comment.text}")
        if seen != markers.keys():
            msg = "The unparser lost or duplicated a comment marker."
            raise ValueError(msg)
        return "\n".join(rendered)

    def configure_stubs(self, *, root: Path | None) -> None:
        """Use an optional folder or ZIP of `.pyi` files for type evidence.

        Args:
            root (Path | None): Filesystem path identifying the root.

        """
        self.semantic.configure_stubs(root=root)

    def configure_graph(self, *, stubs_path: Path | None) -> None:
        """Enable automatic Astart graph inference on every AST revision.

        Args:
            stubs_path (Path | None): Filesystem path identifying the stubs.

        """
        self.semantic.configure_graph(stubs_path=stubs_path)

    def convert(
        self,
        *,
        stubs_path: Path | None = None,
        filename: str = "<memory>",
        apply: bool = False,
    ) -> GraphConversion:
        """Merge the integrated graph inference into this AST.

        The graph conversion is non-destructive unless ``apply`` is enabled.

        Args:
            apply (bool): Apply supplied as bool for this operation.
            filename (str): Filename supplied as str for this operation.
            stubs_path (Path | None): Typeshed root for stub lookups, or
                ``None`` for the
                ``ASTART_TYPESHED`` override and then the bundled snapshot.

        Returns:
            GraphConversion: GraphConversion produced by this operation.

        """
        return self.semantic.convert(
            stubs_path=stubs_path,
            filename=filename,
            apply=apply,
        )

    def signature(self, *, name: str) -> tuple[CallableContract, ...]:
        """Return resolved callable contracts with all parameter kinds.

        Args:
            name (str): Identifier of the name being resolved.

        Returns:
            tuple[CallableContract, ...]: tuple[CallableContract, ...] produced
                by this operation.

        """
        return self.semantic.signature(name=name)

    def bind_call(self, *, node: Call) -> BoundCall | None:
        """Bind supplied and omitted call arguments to their parameters.

        Args:
            node (Call): The node examined while bind supplied and omitted call
                arguments to their parameters.

        Returns:
            BoundCall | None: BoundCall | None produced by this operation.

        """
        return self.semantic.bind_call(node=node)

    def bind_calls(self, *, nodes: Iterable[Call]) -> list[BoundCall | None]:
        """Bind many calls with a single revision check.

        Prefer this over calling :meth:`bind_call` in a loop; each single
        lookup reconciles the whole tree first.

        Args:
            nodes (Iterable[Call]): Calls to bind, in the order results are
                wanted.

        Returns:
            list[BoundCall | None]: One binding, or ``None``, per call.

        """
        return self.semantic.bind_calls(nodes=nodes)

    def graph_document(self, *, filename: str = "<memory>") -> AstDocument:
        """Return the current source's detailed internal inference graph.

        Args:
            filename (str): Filename supplied as str for this operation.

        Returns:
            AstDocument: AstDocument produced by this operation.

        """
        return self.semantic.graph_document(filename=filename)

    def infer_type(self, *, node: AST | str) -> TypeInference:
        """Return a provenance-carrying type inference for a node or symbol.

        Args:
            node (AST | str): The node examined while return a
                provenance-carrying
                type inference for a node or symbol.

        Returns:
            TypeInference: TypeInference produced by this operation.

        """
        return self.semantic.infer_type(node=node)

    def infer(self, *, node: AST | str) -> AbstractValue:
        """Infer a known immutable value or return a conservative abstraction.

        Args:
            node (AST | str): Expression AST node or module-level lexical name.

        Returns:
            AbstractValue: Abstract value, never a runtime execution result.

        """
        return self.semantic.infer(node=node).value

    def refresh_token_index(self) -> None:
        """Retokenize the current source and reconcile mutable AST structure.

        A full fingerprint check catches edits made to mutable node lists,
        which cannot be detected reliably by ``__setattr__`` hooks alone.

        Raises:
            ValueError: If the edited AST cannot round-trip safely.

        """
        self._bind_token_nodes()
        state: str = self._token_state()
        if (
            self._source_tokenizer is not None
            and state == self._token_fingerprint
        ):
            return
        emitted: str = self.unparse(
            preserve_formatting=self._token_formatting,
            on_format_conflict=self._format_conflicts,
        )
        self._bind_token_nodes()
        current: str = self._token_state()
        self._token_version += 1
        indexer: _TokenIndexer = _TokenIndexer(
            tokenizer=SourceTokenizer(
                source=emitted,
                revision=self._token_version,
            ),
            previous=self._token_snapshots,
        )
        parsed: Module = (
            self
            if self._source_tokenizer is None and emitted == self._source
            else parse(source=emitted, type_comments=True)
        )
        full: TokenSnapshot = indexer.tokenizer.snapshot(
            span=indexer.tokenizer.full_span,
        )
        indexer.mapped[id(self)] = full
        indexer.map_code(
            original=Module(body=self.body, type_ignores=self.type_ignores),
            parsed_node=parsed,
            inherited=full,
        )
        self._map_comment_snapshots(indexer=indexer, parsed=parsed)
        self._map_semantic_snapshots(indexer=indexer)
        indexer.map_children(node=self, inherited=full)
        self._relink_detached_docs()
        self._reconcile_index(
            indexer=indexer,
            emitted=emitted,
            fingerprint=current,
        )

    def annotation_transaction(self) -> AnnotationTransaction:
        """Stage checked annotation edits on this same native module.

        Returns:
            AnnotationTransaction:
                Single-writer transaction with no changes until commit.

        """
        return AnnotationTransaction(tree=self)

    @property
    def emission_plan(self) -> EmissionPlan | None:
        """Return the last successful lexical plan without refreshing indexes.

        Returns:
            EmissionPlan | None: Validated native emission plan,
                or None for nonlexical emission.

        """
        return self._last_emission_plan

    def token_snapshot(self, *, node: AST) -> TokenSnapshot:
        """Get immutable, up-to-date lexical metadata for an owned AST node.

        Args:
            node (AST): Existing traversable AST child or this module.

        Returns:
            TokenSnapshot:
                Frozen tokenize records and current source coordinates.

        Raises:
            ReferenceError: If the requested node was detached from this tree.

        """
        self.refresh_token_index()
        found: TokenSnapshot | None = self._token_snapshots.get(id(node))
        if found is None:
            msg: str = "The AST node is no longer part of this module."
            raise ReferenceError(msg)
        return found

    def token_snapshots(
        self,
        *,
        nodes: Iterable[AST],
    ) -> tuple[TokenSnapshot, ...]:
        """Read a batch after one compatibility reconciliation of the tree.

        Use this for graph traversals instead of requesting each node's
        lazy token property separately. Frozen results remain valid records
        of this revision even after later mutations.

        Args:
            nodes (Iterable[AST]): Owned nodes in the desired result order.

        Returns:
            tuple[TokenSnapshot, ...]: Immutable snapshots, including repeated
                requested nodes.

        Raises:
            ReferenceError: A requested node is detached from this module.
            ValueError: The edited tree cannot be emitted safely.

        """
        self.refresh_token_index()
        result: list[TokenSnapshot] = []
        for node in nodes:
            found: TokenSnapshot | None = self._token_snapshots.get(id(node))
            if found is None:
                msg: str = "The AST node is no longer part of this module."
                raise ReferenceError(msg)
            result.append(found)
        return tuple(result)

    def replace_comment_lines(
        self,
        *,
        comments: tuple[SingleLineComment, ...],
        lines: tuple[str, ...],
    ) -> tuple[SingleLineComment, ...]:
        """Replace standalone comment AST nodes at their original anchor.

        Existing nodes are retained in order where possible; extra lines
        become real traversable comment nodes. Their shared original span
        lets the format preserver emit the group as one lexical replacement.

        Args:
            comments (tuple[SingleLineComment, ...]): Contiguous owned ordinary
                standalone comments.
            lines (tuple[str, ...]): Replacement lines including their hash
                characters.

        Returns:
            tuple[SingleLineComment, ...]: Current AST nodes representing the
                replacement block.

        Raises:
            ValueError: Ownership, contiguity or comment text is invalid.

        """
        if not comments or not lines:
            msg: str = "A comment replacement needs original and new lines."
            raise ValueError(msg)
        positions: dict[int, int] = {
            id(comment): index
            for index, comment in enumerate(iterable=self.comments)
        }
        start: int | None = positions.get(id(comments[0]))
        if start is None or any(
            positions.get(id(comment)) != start + index
            or comment.inline
            or comment.col_offset != comments[0].col_offset
            or id(comment) not in self._format_orig_comments
            for index, comment in enumerate(iterable=comments)
        ):
            msg = "Comment replacements require contiguous owned nodes."
            raise ValueError(msg)
        spans: list[TupleIntInt] = [
            self._format_orig_comments[id(comment)] for comment in comments
        ]
        selected: set[int] = {id(comment) for comment in comments}
        selected_spans: set[TupleIntInt] = set(spans)
        if any(
            id(comment) not in selected
            and self._format_orig_comments.get(id(comment)) in selected_spans
            for comment in self.comments
        ):
            msg = "Replace every member of a shared comment anchor together."
            raise ValueError(msg)
        if any(
            before != after
            and (
                before[1] > after[0]
                or self._source[before[1] : after[0]].strip()
            )
            for before, after in pairwise(spans)
        ):
            msg = "A comment replacement cannot include intervening code."
            raise ValueError(msg)
        span: TupleIntInt = (spans[0][0], spans[-1][1])
        # Construct all new nodes before mutating any existing node.
        prepared: list[SingleLineComment] = [
            SingleLineComment(
                text=text,
                inline=False,
                lineno=comments[min(index, len(comments) - 1)].lineno,
                col_offset=comments[0].col_offset,
            )
            for index, text in enumerate(iterable=lines)
        ]
        result: list[SingleLineComment] = []
        for index, node in enumerate(iterable=prepared):
            current: SingleLineComment = (
                comments[index] if index < len(comments) else node
            )
            current.text = node.text
            self._format_orig_comments[id(current)] = span
            result.append(current)
        self.comments[start : start + len(comments)] = result
        return tuple(result)

    def index_docstrings(self) -> None:
        """Index inserted documentation while retaining existing edited nodes.

        Raises:
            ValueError: A removed document contains pending structured edits.

        """
        self._ensure_docstring_index()

    def _formatted_comment_edits(self) -> list[tuple[int, int, str]]:
        """Collect original-coordinate replacements for comment AST blocks.

        Returns:
            list[tuple[int, int, str]]: One lexical edit per original comment
                or reflowed block.

        """
        grouped: dict[TupleIntInt, ListStr] = {}
        for comment in self.comments:
            span: TupleIntInt = self._format_orig_comments[id(comment)]
            grouped.setdefault(span, []).append(comment.text)
        newline: str = (
            """\
\r
"""
            if """\
\r
"""
            in self._source
            else "\n"
        )
        result: list[tuple[int, int, str]] = []
        for (start, end), lines in grouped.items():
            indent: str = self._source[
                self._source.rfind(
                    "\n",
                    0,
                    start,
                )
                + 1 : start
            ]
            separator: str = newline + indent
            result.append((start, end, separator.join(lines)))
        return result

    def semantic_dependents(self, *, node: AST) -> tuple[DocEntry, ...]:
        """Find documentation entries linked to an executable AST node.

        Args:
            node (AST): Parameter, attribute, return, or exception AST node.

        Returns:
            tuple[DocEntry, ...]: Identity-linked entries, after reconciling
                structural edits.

        """
        self.refresh_token_index()
        return tuple(
            entry
            for doc in self.docstrings
            for entry in doc.entries()
            if entry.target is node
        )

    def refresh_docstrings(self) -> None:
        """Re-index docstrings after structural AST changes.

        Discards the existing semantic view only when it contains no
        unapplied edits. Call this after inserting or removing definitions
        or when editing string constants directly.

        Raises:
            ValueError: If semantic documentation edits are still pending.

        """
        if any(
            dump(node=doc, include_attributes=True)
            != self._doc_snapshots.get(id(doc))
            and doc.expression is not None
            and isinstance(doc.expression.value, Constant)
            and (docstring_text(doc=doc) == doc.raw)
            for doc in self.docstrings
        ):
            msg: str = "Apply structured docstring edits before refreshing."
            raise ValueError(msg)
        self.docstrings = collect_docstrings(body=self.body)
        self._bind_token_nodes()
        self._doc_snapshots = {
            id(doc): dump(node=doc, include_attributes=True)
            for doc in self.docstrings
        }
        self._doc_rendered.clear()

    def unparse(
        self,
        *,
        doc_style: DocStyle | None = None,
        preserve_formatting: bool = False,
        on_format_conflict: str = "raise",
    ) -> str:
        """Recover source, including comments, while validating code semantics.

        For an unmodified tree, returns the exact input string. After an AST
        edit, source formatting follows ``ast.unparse``; comments are kept in
        their closest lexical suite, though intra-expression layout may move.

        Args:
            doc_style (DocStyle | None): Optional target documentation syntax,
                or None to keep each
                document's detected style when regeneration is needed.
            preserve_formatting (bool): Reuse original lexical slices and local
                edits.
            on_format_conflict (str): ``raise`` to reject ambiguous edits, or
                ``fallback`` to use the traditional full AST unparser.

        Returns:
            str: A Python source string containing
                every comment node exactly once.

        Raises:
            ValueError: If comments cannot be safely reconstructed with the
                exact executable AST and type-comment meaning preserved.
            SyntaxError: If a caller has mutated the tree to invalid syntax.

        """
        if on_format_conflict not in ("raise", "fallback"):
            msg: str = "on_format_conflict must be 'raise' or 'fallback'."
            raise ValueError(msg)
        self._last_emission_plan = None
        self._sync_suppressions()
        self._sync_shebangs()
        self._ensure_docstring_index()
        self.comment_blocks = _group_comments(
            comments=self.comments,
            lines=self._source.splitlines(keepends=True),
            previous=self.comment_blocks,
        )
        if (
            doc_style is None
            and dump(node=self, include_attributes=True) == self._snapshot
        ):
            self._adopt_unparse_settings(
                preserve_formatting=preserve_formatting,
                on_format_conflict=on_format_conflict,
            )
            return self._source
        self._sync_docstrings(style=doc_style)
        if preserve_formatting and doc_style is None:
            preserve_formatting = self._try_preserve_layouts(
                on_format_conflict=on_format_conflict,
            )
        self._bind_token_nodes()
        code: Module = Module(body=self.body, type_ignores=self.type_ignores)
        if preserve_formatting:
            formatted: str | None = self._try_formatted_unparse(
                code=code,
                on_format_conflict=on_format_conflict,
            )
            if formatted is not None:
                return formatted
        return self._unparse_generated(code=code)

    @staticmethod
    def _shebang_signature(*, shebang: ShebangNode) -> tuple[str, ...]:
        """Fingerprint semantic shebang children independently of raw text.

        Args:
            shebang (ShebangNode): Parsed first-line interpreter comment.

        Returns:
            tuple[str, ...]: Immutable summary of every semantic shebang
                component.

        """
        return (
            shebang.launcher.path if shebang.launcher else "",
            shebang.interpreter.path,
            str(object=shebang.interpreter.via_env),
            *(
                (f"option:{part.role}:{part.value}")
                for part in shebang.launcher_options
            ),
            *(
                (f"variable:{var.name}={var.value}")
                for var in shebang.environment
            ),
            *(
                (f"argument:{part.role}:{part.value}")
                for part in shebang.arguments
            ),
        )

    @staticmethod
    def _token_span(token: LexicalToken) -> SourceSpan:
        """Convert a lexical comment token into a source span.

        Args:
            token (LexicalToken): Comment token from the emitted-source
                tokenizer.

        Returns:
            SourceSpan: UTF-8 byte-column span covering the token.

        """
        return SourceSpan(
            start_line=token.start[0],
            start_column=token.start_byte_column,
            end_line=token.end[0],
            end_column=token.end_byte_column,
        )

    @staticmethod
    def _collect_suites(body: list[stmt], *, lines: ListStr) -> list[_Suite]:
        """Index statement suites with lexical ranges, including nested blocks.

        Args:
            body (list[stmt]): Mutable root statement list of the cloned AST.
            lines (ListStr): Original source lines, including their newlines.

        Returns:
            list[_Suite]: Suites ordered by recursive discovery.

        """
        suites: list[_Suite] = []

        def visit(suite: _Suite) -> None:
            """Recursively register one statement suite and its children.

            Args:
                suite (_Suite): Suite's statements and admissible lexical
                    range.

            """
            suites.append(suite)
            for index, statement in enumerate(iterable=suite.statements):
                if not isinstance(
                    statement,
                    (
                        FunctionDef,
                        AsyncFunctionDef,
                        ClassDef,
                        If,
                        While,
                        For,
                        AsyncFor,
                        With,
                        AsyncWith,
                        Try,
                        TryStar,
                        Match,
                    ),
                ):
                    continue
                lower: int = statement.lineno
                upper: int = (
                    suite.statements[index + 1].lineno
                    if index + 1 < len(suite.statements)
                    and hasattr(suite.statements[index + 1], "lineno")
                    and (suite.statements[index + 1].lineno > lower)
                    else suite.end
                )
                active: list[tuple[list[stmt], int]] = [
                    (sub_body, sub_start)
                    for sub_body, sub_start in _nested_bodies(
                        statement=statement,
                        lower=lower,
                        lines=lines,
                    )
                    if sub_body
                ]
                for sub_index, (sub_body, sub_start) in enumerate(
                    iterable=active,
                ):
                    next_start: int = (
                        active[sub_index + 1][1]
                        if sub_index + 1 < len(active)
                        else upper
                    )
                    visit(
                        suite=_Suite(
                            statements=sub_body,
                            start=sub_start,
                            end=max(sub_start + 1, next_start),
                            indent=sub_body[0].col_offset,
                            depth=suite.depth + 1,
                            header_line=sub_start,
                        ),
                    )

        visit(
            suite=_Suite(
                statements=body,
                start=1,
                end=len(lines) + 2,
                indent=0,
                depth=0,
                header_line=None,
            ),
        )
        return suites

    @staticmethod
    def _validate_marker_comment(comment: Comment) -> None:
        """Validate that a comment can be encoded in a marker expression.

        Args:
            comment (Comment): Comment about to be encoded.

        Raises:
            ValueError: If the comment is multi-line or misplaced.

        """
        if (
            not comment.text.startswith("#")
            or "\n" in comment.text
            or "\r" in comment.text
        ):
            msg: str = "Comment text must be a single # comment."
            raise ValueError(msg)
        if comment.lineno < 1:
            msg = "Comment line numbers must start at one."
            raise ValueError(msg)

    @staticmethod
    def _preceding_statements(
        *,
        chosen: _Suite,
        comment: Comment,
    ) -> list[tuple[int, AST]]:
        """Collect executable statements ending before an inline comment.

        Args:
            chosen (_Suite): Suite whose statements are scanned.
            comment (Comment): Inline comment to anchor.

        Returns:
            list[tuple[int, AST]]: (index, statement) pairs that precede the
                comment column.

        """
        return [
            (index, statement)
            for index, statement in enumerate(iterable=chosen.statements)
            if getattr(statement, "comment_original", False)
            and statement.end_col_offset is not None
            and (statement.end_col_offset > 0)
            and (statement.end_lineno == comment.lineno)
            and (
                statement.end_col_offset <= comment.col_offset
                or (
                    isinstance(statement, Assign)
                    and statement.type_comment is not None
                    and comment.text.startswith("# type:")
                )
            )
        ]

    @staticmethod
    def _marker_position(
        *,
        chosen: _Suite,
        comment: Comment,
        header: bool,
        inline: bool,
        preceding: list[tuple[int, AST]],
    ) -> int:
        """Compute the insertion index of a marker within a suite.

        Args:
            chosen (_Suite): Suite selected to hold the marker.
            comment (Comment): Comment being anchored.
            header (bool): Whether the comment attaches to a compound header.
            inline (bool): Whether the comment follows code on its line.
            preceding (list[tuple[int, AST]]): Statements ending before the
                comment.

        Returns:
            int: Statement index where the marker expression belongs.

        """
        if header:
            return 0
        if inline:
            return preceding[-1][0] + 1
        return next(
            (
                index
                for index, statement in enumerate(iterable=chosen.statements)
                if getattr(statement, "comment_original", False)
                and getattr(statement, "lineno", -1)
                <= comment.lineno
                <= getattr(statement, "end_lineno", -1)
            ),
            sum(
                getattr(statement, "lineno", 10**9) < comment.lineno
                for statement in chosen.statements
                if getattr(statement, "comment_original", False)
            ),
        )

    @staticmethod
    def _strip_unparser_comments(source: str) -> str:
        """Remove unparser-emitted type comments before reintroducing tokens.

        Args:
            source (str): Result of the standard AST unparser.

        Returns:
            str: Source without comments, preserving its line structure.

        """
        lines: ListStr = source.splitlines(keepends=True)
        for token in generate_tokens(
            readline=StringIO(initial_value=source).readline,
        ):
            if token.type == COMMENT:
                line_index: int = token.start[0] - 1
                line: str = lines[line_index]
                lines[line_index] = (
                    line[: token.start[1]].rstrip(" \t") + line[token.end[1] :]
                )
        return "".join(lines)

    @staticmethod
    def _suppression_signature(
        *,
        comment: SuppressionComment,
    ) -> tuple[str, ...]:
        """Record semantic suppression state independent of its original text.

        Args:
            comment (SuppressionComment): Structured suppression to
                fingerprint.

        Returns:
            tuple[str, ...]: Tuple of directive semantics including individual
                rule codes.

        """
        return (
            comment.tool,
            comment.action,
            comment.scope,
            str(object=comment.all_rules),
            comment.trailing,
            comment.form,
            *(rule.code for rule in comment.rules),
        )

    @staticmethod
    def _doc_owner_expression(
        *,
        owner: Module | FunctionDef | AsyncFunctionDef | ClassDef,
    ) -> Expr | None:
        """Return an owner's leading docstring expression when present.

        Args:
            owner (Module|FunctionDef|AsyncFunctionDef|ClassDef): Candidate
                docstring owner.

        Returns:
            Expr | None: The string expression node, or ``None`` when absent.

        """
        if (
            owner.body
            and isinstance(owner.body[0], Expr)
            and isinstance(owner.body[0].value, Constant)
            and isinstance(owner.body[0].value.value, str)
        ):
            return owner.body[0]
        return None

    @staticmethod
    def _comment_tokens(*, text: str) -> ListStr:
        """List comment token strings in lexically patched source.

        Args:
            text (str): Candidate regenerated source.

        Returns:
            ListStr: Comment strings in encounter order.

        """
        return [
            token.string
            for token in generate_tokens(
                readline=StringIO(initial_value=text).readline,
            )
            if token.type == COMMENT
        ]

    @staticmethod
    def _marker_prefix(*, source: str, generated: str) -> str:
        """Choose a marker prefix absent from both old and new source.

        Args:
            source (str): Original document text.
            generated (str): Freshly unparsed executable text.

        Returns:
            str: A collision-free marker prefix.

        """
        prefix: str = "__ASTART_SOURCE_MARKER_"
        while prefix in source or prefix in generated:
            prefix += "_"
        return prefix

    def _sync_shebangs(self) -> None:
        """Synchronize edited shebang structures and their source comment.

        Raises:
            ValueError: If the raw string and semantic children conflict.

        """
        for comment in self.comments:
            if not isinstance(comment, ShebangNode):
                continue
            signature: tuple[str, ...] = self._shebang_signature(
                shebang=comment,
            )
            previous: tuple[str, ...] | None = self._shebang_snapshots.get(
                id(comment),
            )
            previous_text: str = self._shebang_texts.get(
                id(comment),
                comment.text,
            )
            if (
                comment.launcher is None
                and (
                    comment.launcher_options
                    or comment.environment
                    or comment.interpreter.via_env
                )
            ) or (
                comment.launcher is not None
                and (not comment.interpreter.via_env)
            ):
                msg: str = (
                    "Inconsistent shebang launcher and interpreter semantics."
                )
                raise ValueError(msg)
            if signature != previous and comment.text != previous_text:
                msg = "Conflicting shebang text and semantic edits."
                raise ValueError(msg)
            if signature != previous:
                comment.text = comment.render()
                self._shebang_texts[id(comment)] = comment.text
            elif comment.text != previous_text:
                updated: ShebangNode = ShebangNode(
                    text=comment.text,
                    lineno=comment.lineno,
                    col_offset=comment.col_offset,
                )
                comment.launcher = updated.launcher
                comment.interpreter = updated.interpreter
                comment.launcher_options = updated.launcher_options
                comment.environment = updated.environment
                comment.arguments = updated.arguments
                self._shebang_texts[id(comment)] = comment.text
            self._shebang_snapshots[id(comment)] = self._shebang_signature(
                shebang=comment,
            )

    def _bind_token_nodes(self) -> None:
        """Give every existing AST node a lazy token provider property.

        Standard Python nodes are upgraded *in place* to same-named AST
        subclasses. All ordinary ``isinstance`` relationships, AST fields,
        and compile() compatibility are preserved.

        """
        isolate_shared_ast_nodes(root=self)
        for node in walk(node=self):
            if node is not self and (not isinstance(node, TokenAwareMixin)):
                original: type[AST] = type(node)
                adapted: type[AST] | None = self._token_classes.get(original)
                if adapted is None:
                    adapted = type(
                        original.__name__,
                        (TokenAwareMixin, original),
                        {"__module__": original.__module__},
                    )
                    self._token_classes[original] = adapted
                node.__class__ = adapted
            cast(typ="TokenAwareMixin", val=node).token_provider = ref(self)

    def _token_state(self) -> str:
        """Fingerprint edits to the flat comment list that AST walks skip.

        Returns:
            str: str produced by this operation.

        """
        return dump(node=self, include_attributes=True) + repr(
            tuple((id(comment), comment.text) for comment in self.comments),
        )

    def _map_comment_snapshots(
        self,
        *,
        indexer: _TokenIndexer,
        parsed: Module,
    ) -> None:
        """Map comments and type-ignore markers to re-emitted token spans.

        Args:
            indexer (_TokenIndexer): Mapping pass for the current revision.
            parsed (Module): Freshly parsed module for the emitted source.

        Raises:
            ValueError: If emitted comments no longer match the index.

        """
        source_comments: list[LexicalToken] = [
            token
            for token in indexer.tokenizer.tokens
            if token.type == COMMENT
        ]
        if len(source_comments) != len(self.comments):
            msg: str = "Re-emitted comments do not match the semantic index."
            raise ValueError(msg)
        for comment, token in zip(self.comments, source_comments, strict=True):
            if comment.text != token.string:
                msg = (
                    "The emitted comment order or "
                    "contents changed unexpectedly."
                )
                raise ValueError(msg)
            indexer.mapped[id(comment)] = indexer.tokenizer.snapshot(
                span=self._token_span(token=token),
            )
        for original_ignore, emitted_ignore in zip(
            self.type_ignores,
            parsed.type_ignores,
            strict=True,
        ):
            for token in source_comments:
                if (
                    token.start[0] == emitted_ignore.lineno
                    and "type: ignore" in token.string
                ):
                    indexer.mapped[id(original_ignore)] = (
                        indexer.tokenizer.snapshot(
                            span=self._token_span(token=token),
                        )
                    )
                    break

    def _map_semantic_snapshots(self, *, indexer: _TokenIndexer) -> None:
        """Inherit host spans for docstrings and grouped comments.

        Args:
            indexer (_TokenIndexer): Mapping pass for the current revision.

        """
        for doc in self.docstrings:
            if doc.expression is not None:
                origin: TokenSnapshot | None = indexer.mapped.get(
                    id(doc.expression.value),
                )
                if origin is not None:
                    indexer.mapped[id(doc)] = indexer.tokenizer.snapshot(
                        span=origin.span,
                        provenance="inherited",
                    )
        for block in self.comment_blocks:
            if not isinstance(block, CommentGroup):
                continue
            start: TokenSnapshot | None = indexer.mapped.get(
                id(block.comments[0]),
            )
            end: TokenSnapshot | None = indexer.mapped.get(
                id(block.comments[-1]),
            )
            if start is not None and end is not None:
                indexer.mapped[id(block)] = indexer.tokenizer.snapshot(
                    span=SourceSpan(
                        start_line=start.span.start_line,
                        start_column=start.span.start_column,
                        end_line=end.span.end_line,
                        end_column=end.span.end_column,
                    ),
                )

    def _relink_detached_docs(self) -> None:
        """Rebind semantic entries whose targets left the live tree."""
        live: set[int] = {
            id(item)
            for item in walk(
                node=Module(body=self.body, type_ignores=self.type_ignores),
            )
        }
        for doc in self.docstrings:
            if any(
                entry.target is not None and id(entry.target) not in live
                for entry in doc.entries()
            ):
                doc.link()

    def _reconcile_index(
        self,
        *,
        indexer: _TokenIndexer,
        emitted: str,
        fingerprint: str,
    ) -> None:
        """Commit reconciled snapshots and record the verified fingerprint.

        Args:
            indexer (_TokenIndexer): Completed mapping pass for the current
                revision.
            emitted (str): Validated emitted source for this revision.
            fingerprint (str): Post-emission structural fingerprint.

        """
        dependencies: dict[int, list[int]] = {}
        for doc in self.docstrings:
            for entry in doc.entries():
                if entry.target is not None:
                    dependencies.setdefault(id(entry.target), []).append(
                        id(entry),
                    )
        reconciled, _ = self.source_graph.reconcile(
            root=self,
            source=emitted,
            snapshots=indexer.mapped,
            revision=self._token_version,
            semantic_dependencies={
                identity: tuple(entries)
                for identity, entries in dependencies.items()
            },
        )
        self._source_tokenizer = indexer.tokenizer
        self._current_source = emitted
        self._token_snapshots = reconciled
        self._token_fingerprint = fingerprint

    def _inject_markers(
        self,
        module: Module,
        *,
        prefix: str,
    ) -> dict[str, tuple[Comment, bool, bool]]:
        """Insert temporary expression markers in appropriate cloned suites.

        Args:
            module (Module): Deep-cloned executable AST, safe to mutate.
            prefix (str): Unique per-document marker prefix.

        Returns:
            dict[str, tuple[Comment, bool, bool]]: Marker text associated with
                its comment and placement hint.

        """
        lines: ListStr = self._source.splitlines(keepends=True)
        suites: list[_Suite] = self._collect_suites(
            body=module.body,
            lines=lines,
        )
        pending: dict[int, list[_Insertion]] = {}
        for comment_index, comment in enumerate(iterable=self.comments):
            self._validate_marker_comment(comment=comment)
            chosen, position, inline, header = self._comment_placement(
                comment=comment,
                suites=suites,
                lines=lines,
            )
            pending.setdefault(id(chosen.statements), []).append(
                _Insertion(
                    index=position,
                    comment_index=comment_index,
                    inline=inline,
                    header=header,
                ),
            )
        return self._apply_markers(
            suites=suites,
            pending=pending,
            prefix=prefix,
        )

    def _comment_placement(
        self,
        *,
        comment: Comment,
        suites: list[_Suite],
        lines: ListStr,
    ) -> tuple[_Suite, int, bool, bool]:
        """Choose the suite and insertion index for one comment.

        Args:
            comment (Comment): Comment to place within a suite.
            suites (list[_Suite]): Indexed suites covering the cloned module.
            lines (ListStr): Original source lines, including their newlines.

        Returns:
            tuple[_Suite, int, bool, bool]: (suite, position, inline, header)
                placement for its marker.

        """
        if isinstance(comment, ShebangNode):
            return (suites[0], 0, False, False)
        source_line: str = (
            lines[comment.lineno - 1] if comment.lineno <= len(lines) else ""
        )
        source_indent: int = len(source_line) - len(source_line.lstrip(" \t"))
        eligible: list[_Suite] = [
            suite
            for suite in suites
            if suite.start <= comment.lineno < suite.end
            and suite.indent <= source_indent
        ]
        chosen: _Suite = max(
            eligible,
            key=lambda suite: (suite.depth, suite.start),
            default=suites[0],
        )
        code_prefix: str = source_line.encode(encoding="utf-8")[
            : comment.col_offset
        ].decode(encoding="utf-8")
        header: bool = comment.inline and code_prefix.rstrip().endswith(":")
        header_suites: list[_Suite] = []
        if header:
            header_suites = [
                suite
                for suite in suites
                if suite.header_line == comment.lineno
                and suite.indent > source_indent
                and (suite.start <= comment.lineno < suite.end)
            ]
            if header_suites:
                chosen = max(
                    header_suites,
                    key=lambda suite: (suite.depth, suite.start),
                )
        preceding: list[tuple[int, AST]] = self._preceding_statements(
            chosen=chosen,
            comment=comment,
        )
        inline: bool = bool(
            comment.inline and (preceding or (header and header_suites)),
        )
        header = bool(header and header_suites)
        position: int = self._marker_position(
            chosen=chosen,
            comment=comment,
            header=header,
            inline=inline,
            preceding=preceding,
        )
        return (chosen, position, inline, header)

    def _apply_markers(
        self,
        *,
        suites: list[_Suite],
        pending: dict[int, list[_Insertion]],
        prefix: str,
    ) -> dict[str, tuple[Comment, bool, bool]]:
        """Splice scheduled marker expressions into each suite.

        Args:
            suites (list[_Suite]): Cloned suites receiving marker statements.
            pending (dict[int, list[_Insertion]]): Scheduled insertions keyed
                by statement-list identity.
            prefix (str): Unique per-document marker prefix.

        Returns:
            dict[str, tuple[Comment, bool, bool]]: Marker text associated with
                its comment and placement hint.

        """
        markers: dict[str, tuple[Comment, bool, bool]] = {}
        for suite in suites:
            inserts: list[_Insertion] = pending.get(id(suite.statements), [])
            if not inserts:
                continue
            by_position: dict[int, list[_Insertion]] = {}
            for insertion in inserts:
                by_position.setdefault(insertion.index, []).append(insertion)
            original: list[stmt] = list(suite.statements)
            suite.statements.clear()
            for position in range(len(original) + 1):
                for insertion in sorted(
                    by_position.get(position, []),
                    key=lambda item: item.comment_index,
                ):
                    marker: str = f"{prefix}{insertion.comment_index}__"
                    markers[marker] = (
                        self.comments[insertion.comment_index],
                        insertion.inline,
                        insertion.header,
                    )
                    suite.statements.append(Expr(value=Constant(value=marker)))
                if position < len(original):
                    suite.statements.append(original[position])
        return markers

    def _sync_suppressions(self) -> None:
        """Reconcile edited rule nodes and tokenizer comments before emitting.

        Raises:
            ValueError: If both semantic and raw comment forms disagree.

        """
        for comment in self.comments:
            if not isinstance(comment, SuppressionComment):
                continue
            signature: tuple[str, ...] = self._suppression_signature(
                comment=comment,
            )
            if signature == self._supp_snapshots.get(id(comment)):
                if comment.text != self._supp_texts.get(id(comment)):
                    self._resync_suppression_text(comment=comment)
                continue
            expected: str = comment.render()
            if comment.text not in (self._supp_texts[id(comment)], expected):
                msg: str = "Suppression text and semantic rules conflict."
                raise ValueError(msg)
            comment.text = expected
            self._supp_texts[id(comment)] = expected
            if comment.tool == "type":
                self._update_type_ignore(comment=comment)

    def _resync_suppression_text(self, *, comment: SuppressionComment) -> None:
        """Reparse edited suppression text into its semantic fields.

        Args:
            comment (SuppressionComment): Structured suppression whose raw text
                was edited.

        Raises:
            TypeError: If the new text is no longer a directive.

        """
        refreshed: Comment = _classify_comment(
            text=comment.text,
            inline=comment.inline,
            lineno=comment.lineno,
            col_offset=comment.col_offset,
            is_file_header=comment.lineno
            < min(
                (statement.lineno for statement in self.body),
                default=comment.lineno + 1,
            ),
        )
        if not isinstance(refreshed, SuppressionComment):
            msg: str = "Edited suppression text is no longer a directive."
            raise TypeError(msg)
        comment.tool = refreshed.tool
        comment.action = refreshed.action
        comment.scope = refreshed.scope
        comment.rules = refreshed.rules
        comment.all_rules = refreshed.all_rules
        comment.trailing = refreshed.trailing
        comment.form = refreshed.form
        self._supp_texts[id(comment)] = comment.text
        if comment.tool == "type":
            self._update_type_ignore(comment=comment)

    def _update_type_ignore(self, *, comment: SuppressionComment) -> None:
        """Propagate semantic rule edits to matching type ignore entries.

        Args:
            comment (SuppressionComment): Suppression whose ``type`` tool rules
                changed.

        """
        for item in self.type_ignores:
            if item.lineno == comment.lineno:
                item.tag = (
                    "[" + ", ".join(rule.code for rule in comment.rules) + "]"
                    if comment.rules
                    else ""
                )

    def _ensure_docstring_index(self) -> None:
        """Reconcile newly inserted or removed documentation owner expressions.

        This retains the existing semantic node identities and pending edits
        for unchanged docstrings while discovering new definitions inserted
        into mutable statement lists.

        Raises:
            ValueError: If a document with unapplied semantic edits vanished.

        """
        owners: list[Module | FunctionDef | AsyncFunctionDef | ClassDef] = (
            self._documented_owners()
        )
        expected: set[int] = set()
        owners_by_expression: dict[
            int,
            Module | FunctionDef | AsyncFunctionDef | ClassDef,
        ] = {}
        for owner in owners:
            expression: Expr | None = self._doc_owner_expression(owner=owner)
            if expression is not None:
                expected.add(id(expression))
                owners_by_expression[id(expression)] = owner
        known: set[int] = {
            id(doc.expression)
            for doc in self.docstrings
            if doc.expression is not None
        }
        for doc in self.docstrings:
            current_owner: (
                Module | FunctionDef | AsyncFunctionDef | ClassDef | None
            ) = owners_by_expression.get(id(doc.expression))
            new_owner: FunctionDef | AsyncFunctionDef | ClassDef | None = (
                None if isinstance(current_owner, Module) else current_owner
            )
            if current_owner is not None and new_owner is not doc.owner:
                doc.owner = new_owner
                doc.__class__ = (
                    ModuleDocstringNode if new_owner is None else DocstringNode
                )
                doc.link()
        if known == expected:
            return
        existing: dict[int, DocstringNode] = {
            id(doc.expression): doc
            for doc in self.docstrings
            if doc.expression is not None
        }
        self._check_removed_docstrings(expected=expected)
        new_docs: list[DocstringNode] = self._collect_new_docstrings(
            existing=existing,
        )
        for old in self.docstrings:
            if old not in new_docs:
                self._doc_snapshots.pop(id(old), None)
                self._doc_rendered.pop(id(old), None)
        self.docstrings = new_docs
        self._bind_token_nodes()

    def _documented_owners(
        self,
    ) -> list[Module | FunctionDef | AsyncFunctionDef | ClassDef]:
        """Enumerate every node that may own a docstring.

        Returns:
            list[Module | FunctionDef | AsyncFunctionDef | ClassDef]: The
                module plus all nested definitions, in walk order.

        """
        owners: list[Module | FunctionDef | AsyncFunctionDef | ClassDef] = [
            Module(body=self.body, type_ignores=[]),
        ]
        owners.extend(
            node
            for node in walk(node=owners[0])
            if isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef))
        )
        return owners

    def _check_removed_docstrings(self, *, expected: set[int]) -> None:
        """Reject removal of docstrings that still hold pending edits.

        Args:
            expected (set[int]): Identities of expressions still present in the
                AST.

        Raises:
            ValueError: If a document with unapplied semantic edits vanished.

        """
        for old in self.docstrings:
            if old.expression is None or id(old.expression) in expected:
                continue
            if dump(
                node=old,
                include_attributes=True,
            ) != self._doc_snapshots.get(id(old)):
                msg: str = (
                    "A docstring with pending structured edits was removed."
                )
                raise ValueError(msg)

    def _collect_new_docstrings(
        self,
        *,
        existing: dict[int, DocstringNode],
    ) -> list[DocstringNode]:
        """Collect current docstrings, preserving existing node identities.

        Args:
            existing (dict[int, DocstringNode]): Known documents keyed by
                expression identity.

        Returns:
            list[DocstringNode]: Documents in source order, reusing preserved
                nodes.

        """
        new_docs: list[DocstringNode] = []
        for parsed_doc in collect_docstrings(body=self.body):
            if parsed_doc.expression is None:
                continue
            preserved: DocstringNode | None = existing.get(
                id(parsed_doc.expression),
            )
            node: DocstringNode = (
                preserved if preserved is not None else parsed_doc
            )
            new_docs.append(node)
            if preserved is None:
                self._doc_snapshots[id(node)] = dump(
                    node=node,
                    include_attributes=True,
                )
        return new_docs

    def _sync_docstrings(self, *, style: DocStyle | None = None) -> None:
        """Apply edits to structured documentation to executable constants.

        Args:
            style (DocStyle | None): Optional output format conversion for
                every docstring.

        Raises:
            FormatPreservationError: When both the source string and
                structured node changed, or an edited docstring no
                longer has a string constant.

        """
        for index, original in enumerate(iterable=list(self.docstrings)):
            doc: DocstringNode = original
            is_edited: bool = dump(
                node=doc,
                include_attributes=True,
            ) != self._doc_snapshots.get(id(doc))
            if (
                doc.expression is None
                or not isinstance(doc.expression.value, Constant)
                or (not isinstance(doc.expression.value.value, str))
            ):
                if is_edited:
                    msg: str = (
                        "An edited docstring no longer has a string constant."
                    )
                    raise FormatPreservationError(msg)
                self.docstrings.remove(doc)
                self._doc_snapshots.pop(id(doc), None)
                self._doc_rendered.pop(id(doc), None)
                continue
            if not is_edited and docstring_text(doc=doc) not in (
                doc.raw,
                self._doc_rendered.get(id(doc)),
            ):
                current: DocstringNode = parse_docstring(
                    source=docstring_text(doc=doc),
                    owner=doc.owner,
                    expression=doc.expression,
                )
                self.docstrings[index] = current
                self._doc_snapshots.pop(id(doc), None)
                self._doc_rendered.pop(id(doc), None)
                self._doc_snapshots[id(current)] = dump(
                    node=current,
                    include_attributes=True,
                )
                doc = current
            if not is_edited and style is None:
                continue
            if (
                docstring_text(doc=doc)
                not in (doc.raw, self._doc_rendered.get(id(doc)))
                and is_edited
            ):
                msg = "Executable and structured docstrings were both changed."
                raise FormatPreservationError(msg)
            docstring_constant(doc=doc).value = doc.render(
                style=style
                if style is not None
                else "google"
                if doc.style == "mixed"
                else doc.style,
            )
            if (
                not doc.layout.preserve_original
                and doc.layout.is_trailing_blank
                and doc.sections
            ):
                lines: ListStr = docstring_text(doc=doc).splitlines()
                indent: str = self._docstring_indent(document=doc)
                docstring_constant(doc=doc).value = (
                    lines[0]
                    + "\n"
                    + "\n".join(
                        indent + line if line else "" for line in lines[1:]
                    )
                    + "\n\n"
                    + indent
                )
            self._doc_rendered[id(doc)] = docstring_text(doc=doc)

    def _docstring_indent(self, *, document: DocstringNode) -> str:
        """Find lexical indentation for existing or synthesized documentation.

        Args:
            document (DocstringNode): Native documentation to emit.

        Returns:
            str: Source indentation, or structural
                indentation for inserted nodes.

        """
        if document.expression is not None and document.expression.col_offset:
            return " " * document.expression.col_offset
        pending: list[tuple[AST, int]] = [(self, 0)]
        while pending:
            node, depth = pending.pop()
            if node is document.expression:
                return " " * (4 * depth)
            pending.extend(
                (child, depth + int(isinstance(node, stmt)))
                for child in iter_child_nodes(node=node)
                if not isinstance(child, DocstringNode)
            )
        return ""

    def _preserve_docstring_layouts(self) -> None:
        """Keep exact PEP 257 prose whitespace after semantic field edits.

        Raises:
            FormatPreservationError: If edited structured data cannot be
                placed into the original documentation without reformatting.

        """
        for doc in self.docstrings:
            if not doc.layout.preserve_original:
                continue
            baseline: tuple[str, str, str, str] | None = (
                self._format_doc_baseline.get(id(doc))
            )
            if baseline is None or doc.expression is None:
                continue
            initial_summary: str
            initial_description: str
            style: str
            sections: str
            initial_summary, initial_description, style, sections = baseline
            if (
                doc.summary == initial_summary
                and doc.description == initial_description
                and (docstring_text(doc=doc) == doc.raw)
            ):
                continue
            if (
                doc.style != style
                or repr(tuple(dump(node=section) for section in doc.sections))
                != sections
            ):
                msg: str = (
                    "Structural docstring changes cannot preserve exact prose "
                    "layout; use on_format_conflict='fallback'."
                )
                raise FormatPreservationError(msg)
            if docstring_text(doc=doc) != doc.raw:
                updated: str = preserve_docstring_content(
                    original=doc.raw,
                    old_summary=initial_summary,
                    new_summary=doc.summary,
                    old_description=initial_description,
                    new_description=doc.description,
                )
                docstring_constant(doc=doc).value = updated
                self._doc_rendered[id(doc)] = updated

    def _unparse_formatted(self, *, code: Module) -> str:
        """Generate a lexically patched source and validate AST equivalence.

        Args:
            code (Module): Current executable syntax tree for semantic
                verification.

        Returns:
            str: Regenerated source with unmodified original source
                fragments.

        Raises:
            FormatPreservationError: When regeneration could lose syntax or
                trivia.

        """
        self._check_formatted_guards()
        plan: EmissionPlan = self._format_preserver.plan(
            body=self.body,
            comments=self._formatted_comment_edits(),
            revision=self._token_version,
        )
        text: str = plan.render(
            source=self._source,
            revision=self._token_version,
        )
        parsed, found = self._validate_formatted_text(text=text, code=code)
        self._adopt_formatted_comments(text=text, parsed=parsed, found=found)
        self._last_emission_plan = plan
        return text

    def _check_formatted_guards(self) -> None:
        """Reject format-preserving output that could change semantics.

        Raises:
            FormatPreservationError: When suppression scope or comment
                identity cannot be guaranteed to survive lexical patching.

        """
        if any(
            isinstance(comment, SuppressionComment)
            and comment.scope in ("block", "file")
            for comment in self.comments
        ) and self._format_preserver.has_structural_mutations(body=self.body):
            msg: str = (
                "A structural edit may change block/file suppression scope. "
                "Use on_format_conflict='fallback' only if acceptable."
            )
            raise FormatPreservationError(msg)
        if any(
            id(comment) not in self._format_orig_comments
            for comment in self.comments
        ):
            msg = "New comments require the full-source formatting fallback."
            raise FormatPreservationError(msg)

    def _validate_formatted_text(
        self,
        *,
        text: str,
        code: Module,
    ) -> tuple[Module, ListStr]:
        """Check comment survival and AST equivalence of patched source.

        Args:
            text (str): Lexically patched candidate source.
            code (Module): Current executable syntax tree for semantic
                verification.

        Returns:
            tuple[Module, ListStr]: Reparsed module and the comment tokens
                found in order.

        Raises:
            FormatPreservationError: If comments or semantics diverged.

        """
        found: ListStr = self._comment_tokens(text=text)
        expected: ListStr = [comment.text for comment in self.comments]
        if Counter(found) != Counter(expected):
            msg: str = (
                "Format-preserving changes would lose or duplicate comments."
            )
            raise FormatPreservationError(msg)
        try:
            parsed: Module = parse(
                source=text,
                mode="exec",
                type_comments=True,
            )
        except (SyntaxError, IndentationError) as exc:
            msg = "Format-preserving reconstruction produced invalid Python."
            raise FormatPreservationError(msg) from exc
        if dump(node=Module(body=parsed.body, type_ignores=[])) != dump(
            node=Module(body=code.body, type_ignores=[]),
        ):
            msg = "Format-preserving reconstruction changed AST semantics."
            raise FormatPreservationError(msg)
        if [item.tag for item in parsed.type_ignores] != [
            item.tag for item in code.type_ignores
        ]:
            msg = "Format-preserving edits changed type-ignore semantics."
            raise FormatPreservationError(msg)
        return (parsed, found)

    def _adopt_formatted_comments(
        self,
        *,
        text: str,
        parsed: Module,
        found: ListStr,
    ) -> None:
        """Reorder comments and refresh positions after relocation.

        Args:
            text (str): Lexically patched source that survived validation.
            parsed (Module): Reparsed module for position reconciliation.
            found (ListStr): Comment token strings in encounter order.

        """
        pending: list[Comment] = list(self.comments)
        ordered: list[Comment] = []
        for token_text in found:
            for index, comment in enumerate(iterable=pending):
                if comment.text == token_text:
                    ordered.append(pending.pop(index))
                    break
        self.comments = ordered
        positions: dict[int, TupleIntInt] = {}
        for comment, token in zip(
            ordered,
            (
                token
                for token in generate_tokens(
                    readline=StringIO(initial_value=text).readline,
                )
                if token.type == COMMENT
            ),
            strict=True,
        ):
            positions[id(comment)] = (
                token.start[0],
                len(token.line[: token.start[1]].encode(encoding="utf-8")),
            )
        self._formatted_comment_positions = positions
        self.comment_blocks = _group_comments(
            comments=self.comments,
            lines=text.splitlines(keepends=True),
            positions=positions,
            previous=self.comment_blocks,
        )
        for item, parsed_ignore in zip(
            self.type_ignores,
            parsed.type_ignores,
            strict=True,
        ):
            item.lineno = parsed_ignore.lineno

    def _adopt_unparse_settings(
        self,
        *,
        preserve_formatting: bool,
        on_format_conflict: str,
    ) -> None:
        """Record the resolved unparse mode and refresh token bindings.

        Args:
            preserve_formatting (bool): Whether lexical preservation is active.
            on_format_conflict (str): The validated conflict policy.

        """
        self._token_formatting = preserve_formatting
        self._format_conflicts = on_format_conflict
        self._bind_token_nodes()

    def _try_preserve_layouts(self, *, on_format_conflict: str) -> bool:
        """Keep docstring prose layout or report that fallback is needed.

        Args:
            on_format_conflict (str): ``raise`` to reject ambiguous edits, or
                ``fallback`` to allow full-source regeneration.

        Returns:
            bool: True when format preservation remains possible.

        Raises:
            FormatPreservationError: When the policy is ``raise``.

        """
        try:
            self._preserve_docstring_layouts()
        except FormatPreservationError:
            if on_format_conflict == "raise":
                raise
            return False
        return True

    def _try_formatted_unparse(
        self,
        *,
        code: Module,
        on_format_conflict: str,
    ) -> str | None:
        """Attempt the lexically patched unparse path.

        Args:
            code (Module): Current executable syntax tree for semantic
                verification.
            on_format_conflict (str): ``raise`` to reject ambiguous edits, or
                ``fallback`` to allow full-source regeneration.

        Returns:
            str | None:
                The patched source, or ``None`` when fallback is required.

        Raises:
            FormatPreservationError: When the policy is ``raise``.

        """
        try:
            formatted: str = self._unparse_formatted(code=code)
        except FormatPreservationError:
            if on_format_conflict == "raise":
                raise
            return None
        self._adopt_unparse_settings(
            preserve_formatting=True,
            on_format_conflict=on_format_conflict,
        )
        return formatted

    def _comment_gaps(self, *, prefix: str) -> dict[str, int]:
        """Count fully blank gaps preceding each standalone comment.

        Args:
            prefix (str): The marker prefix in use.

        Returns:
            dict[str, int]: Marker text mapped to the blank lines to restore
                before it.

        """
        lines: ListStr = self._source.splitlines(keepends=True)
        gaps: dict[str, int] = {}
        for index, comment in enumerate(iterable=self.comments):
            if index == 0 or comment.inline:
                continue
            previous: Comment = self.comments[index - 1]
            count: int = comment.lineno - previous.lineno - 1
            if count > 0 and all(
                not lines[number].strip()
                for number in range(previous.lineno, comment.lineno - 1)
                if number < len(lines)
            ):
                gaps[f"{prefix}{index}__"] = count
        return gaps

    def _unparse_generated(self, *, code: Module) -> str:
        """Regenerate full source through markers and validate semantics.

        Args:
            code (Module): Current executable syntax tree for semantic
                verification.

        Returns:
            str: Regenerated source containing every comment exactly once.

        Raises:
            ValueError: If re-emitting comments altered the executable AST.

        """
        self._token_formatting = False
        generated: Module = deepcopy(x=code)
        fix_missing_locations(node=generated)
        unmodified_code: str = unparse(ast_obj=generated)
        prefix: str = self._marker_prefix(
            source=self._source,
            generated=unmodified_code,
        )
        markers: dict[str, tuple[Comment, bool, bool]] = self._inject_markers(
            module=generated,
            prefix=prefix,
        )
        text: str = self.render_markers(
            source=self._strip_unparser_comments(
                source=unparse(ast_obj=fix_missing_locations(node=generated)),
            ),
            markers=markers,
            blank_lines_before=self._comment_gaps(prefix=prefix),
        )
        if self._source.endswith("\n"):
            text += "\n"
        if dump(
            node=parse(source=text, mode="exec", type_comments=True),
        ) != dump(node=code):
            msg: str = (
                "Re-emitting comments changed the executable Python AST."
            )
            raise ValueError(msg)
        self._bind_token_nodes()
        return text
