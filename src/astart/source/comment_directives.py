"""Parse comment-token directives into native suppression rule nodes."""

from __future__ import annotations

from ast import AST
from dataclasses import dataclass
from typing import ClassVar, final

from astart.source.node_attributes import initialize_node
from astart.transforms.typeuniondict import TypeUnionDict, TypeUnionDictType


@final
class SuppressionRule(AST):
    """One parsed diagnostic code, prefix or named rule in a suppression.

    Attributes:
        code (str): Exact source rule identifier.
        _field_types (ClassVar[TypeUnionDictType]): TODO.
        _fields (ClassVar[tuple[str, ...]]): TODO.

    """

    code: str
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={"code": str},
    )
    _fields: ClassVar[tuple[str, ...]] = ("code",)

    def __init__(self, *, code: str) -> None:
        """Create a rule identifier.

        Args:
            code (str): Identifier, optionally with a rule-family prefix.

        Raises:
            ValueError: If no identifier was supplied.

        """
        if not code.strip():
            msg: str = "Suppressed rule identifiers cannot be empty."
            raise ValueError(msg)
        initialize_node(node=self, code=code)


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SuppressionSpec:
    """Normalized directive semantics for one suppression comment.

    Attributes:
        tool (str): Checker or formatter that understands the directive.
        action (str): Suppression action: ignore, disable, enable, off, on or
            skip.
        scope (str): Recognized lexical scope, e.g. line, block or file.
        rules (list[SuppressionRule]): AST nodes for rule identifiers,
            excluding wildcard suppressions.
        all_rules (bool): True for directives without an explicit rule list.
        trailing (str): Optional trailing explanation, preserved when edited.
        form (str): Original directive family for lossless semantic rendering.

    """

    tool: str
    action: str
    scope: str
    rules: list[SuppressionRule]
    all_rules: bool
    trailing: str = ""
    form: str = ""


@final
class DirectiveParser:
    """Consume one COMMENT token once, constructing its semantic AST fields."""

    def __init__(self, *, body: str, inline: bool, file_header: bool) -> None:
        """Bind the comment-content boundary and its lexical context.

        Args:
            body (str): Comment content after its hash prefix.
            inline (bool): Whether executable code precedes this comment.
            file_header (bool): Whether it precedes the first executable
                statement.

        """
        self._body: str = body
        self._position: int = 0
        self._inline: bool = inline
        self._header: bool = file_header
        self._head: str = ""

    def _word(self) -> str:
        """Consume one directive keyword at the current cursor.

        Returns:
            str: Lowercase keyword, excluding
                punctuation and trailing whitespace.

        """
        while (
            self._position < len(self._body)
            and self._body[self._position].isspace()
        ):
            self._position += 1
        start: int = self._position
        while self._position < len(self._body) and (
            self._body[self._position].isalnum()
            or self._body[self._position] in "_-"
        ):
            self._position += 1
        return self._body[start : self._position].casefold()

    def _take(self, *, delimiter: str) -> bool:
        """Consume an optional delimiter without losing unmatched trivia.

        Args:
            delimiter (str): Exact delimiter to consume.

        Returns:
            bool: Whether the delimiter was present.

        """
        previous: int = self._position
        while (
            self._position < len(self._body)
            and self._body[self._position].isspace()
        ):
            self._position += 1
        if self._body.startswith(delimiter, self._position):
            self._position += len(delimiter)
            return True
        self._position = previous
        return False

    @staticmethod
    def _code(*, code: str, bandit: bool) -> bool:
        """Validate an ASCII diagnostic code without matching source text.

        Args:
            code (str): One selector in a noqa or nosec directive.
            bandit (bool): Require the Bandit B prefix.

        Returns:
            bool: Whether letters followed by digits form the required
                selector.

        """
        index: int = 0
        while (
            index < len(code)
            and code[index].isalpha()
            and code[index].isascii()
        ):
            index += 1
        return (
            index > 0
            and code[index:].isascii()
            and code[index:].isdigit()
            and (not bandit or code[:index].casefold() == "b")
        )

    def _rules(
        self,
        *,
        bracket: bool = False,
        strict: bool = False,
    ) -> list[SuppressionRule] | None:
        """Construct rule nodes from the directive's selector payload only.

        Args:
            bracket (bool): Require a closing square bracket.
            strict (bool): Enforce noqa/nosec diagnostic code syntax.

        Returns:
            list[SuppressionRule] | None:
                Owned selector nodes, or None for malformed syntax.

        """
        end: int = self._body.find(
            "]" if bracket else "#",
            self._position,
        )
        if bracket and end < 0:
            return None
        stop: int = len(self._body) if end < 0 else end
        raw: str = self._body[self._position : stop]
        values: list[str] = [part.strip() for part in raw.split(sep=",")]
        if not all(values) or (
            strict
            and not all(
                self._code(code=value, bandit=self._head == "nosec")
                for value in values
            )
        ):
            return None
        self._position = (
            stop + 1 if bracket else self._position + len(raw.rstrip())
        )
        return [SuppressionRule(code=value) for value in values]

    def _finish(
        self,
        *,
        tool: str,
        action: str,
        rules: list[SuppressionRule],
    ) -> SuppressionSpec | None:
        """Attach exact suffix trivia to already parsed directive fields.

        Args:
            tool (str): Canonical checker/formatter identifier.
            action (str): Parsed directive operation.
            rules (list[SuppressionRule]): Native selector children created by
                this parse.

        Returns:
            SuppressionSpec | None: Structured comment specification,
                or None at an invalid boundary.

        """
        tail: str = self._body[self._position :]
        if tail and not (tail[0].isspace() or tail[0] == "#"):
            return None
        scope: str = (
            "file"
            if self._head == "ruff" or action == "skip_file"
            else "line"
            if self._inline
            or self._head
            in {
                "noqa",
                "nosec",
                "type",
                "pyright",
                "basedpyright",
                "pragma",
                "coverswitch",
                "sourcery",
            }
            or (self._head == "isort" and action == "skip")
            else "file"
            if self._header and self._head in {"pylint", "local-checker"}
            else "block"
        )
        return SuppressionSpec(
            tool=tool,
            action="skip" if action == "skip_file" else action,
            scope=scope,
            rules=rules,
            all_rules=not rules,
            trailing=tail,
            form=self._head,
        )

    def parse(self) -> SuppressionSpec | None:
        """Parse supported suppression grammar, without scanning Python code.

        Returns:
            SuppressionSpec | None: Directive semantics ready to attach
                to the existing comment tree.

        """
        self._head = self._word()
        if self._head in {"noqa", "nosec"}:
            return self._code_directive()
        if not self._take(delimiter=":"):
            return self._sourcery() if self._head == "sourcery" else None
        action: str = self._word()
        if self._head == "ruff" and action == "noqa":
            return self._code_directive()
        if (
            self._head in {"type", "pyright", "basedpyright"}
            and action == "ignore"
        ):
            rules: list[SuppressionRule] | None = (
                self._rules(bracket=True) if self._take(delimiter="[") else []
            )
            return (
                self._finish(tool=self._head, action=action, rules=rules)
                if rules is not None
                else None
            )
        if self._head in {"pylint", "local-checker"} and action in {
            "disable",
            "enable",
        }:
            rules = self._rules() if self._take(delimiter="=") else []
            return (
                self._finish(tool=self._head, action=action, rules=rules)
                if rules is not None
                else None
            )
        return self._simple(action=action)

    def _code_directive(self) -> SuppressionSpec | None:
        """Parse noqa/nosec selectors after their recognized keyword.

        Returns:
            SuppressionSpec | None: Canonical directive fields, or
                None for an invalid selector list.

        """
        explicit: bool = self._take(delimiter=":")
        if not explicit:
            suffix: str = self._body[self._position :].lstrip()
            if suffix and not suffix.startswith("#"):
                return None
        rules: list[SuppressionRule] | None = (
            self._rules(strict=True) if explicit else []
        )
        tool: str = (
            "bandit"
            if self._head == "nosec"
            else "ruff"
            if self._head == "ruff"
            else "flake8/ruff"
        )
        return (
            self._finish(tool=tool, action="ignore", rules=rules)
            if rules is not None
            else None
        )

    def _sourcery(self) -> SuppressionSpec | None:
        """Parse the two-word Sourcery directive prefix.

        Returns:
            SuppressionSpec | None:
                Its structured rule selector list, or None for ordinary prose.

        """
        if self._word() != "skip" or not self._take(delimiter=":"):
            return None
        rules: list[SuppressionRule] | None = self._rules()
        return (
            self._finish(tool="sourcery", action="skip", rules=rules)
            if rules is not None
            else None
        )

    def _simple(self, *, action: str) -> SuppressionSpec | None:
        """Parse formatter, coverage and single-action checker directives.

        Args:
            action (str): Already consumed directive keyword.

        Returns:
            SuppressionSpec | None:
                Recognized fields, or None for unsupported syntax.

        """
        if self._head in {"fmt", "autopep8", "isort"} and (
            action in {"off", "on", "skip"}
            or (self._head == "isort" and action == "skip_file")
        ):
            return self._finish(tool=self._head, action=action, rules=[])
        if self._head == "coverswitch" and action == "skip":
            return self._finish(tool="coverage", action="skip", rules=[])
        if self._head == "pragma":
            if action == "no" and self._word() == "cover":
                return self._finish(tool="coverage", action="ignore", rules=[])
            if action == "nomutate":
                return self._finish(tool="coverage", action="skip", rules=[])
        if self._head == "xenon" and action == "ignore":
            return self._finish(tool="xenon", action=action, rules=[])
        return None


def control_kind(*, body: str) -> str | None:
    """Recognize non-suppression controls at the comment-token boundary.

    Args:
        body (str): One comment's content after its hash marker.

    Returns:
        str | None: Encoding, region or launcher control kind; otherwise None.

    """
    stripped: str = body.strip().casefold()
    if stripped.startswith("!"):
        return "launcher"
    words: list[str] = stripped.partition(":")[0].split(maxsplit=1)
    if words and words[0] in {"region", "endregion"}:
        return "region"
    encoding: str = stripped.removeprefix("-*-").lstrip()
    if encoding.startswith("coding") and encoding[
        len("coding") :
    ].lstrip().startswith((":", "=")):
        return "encoding"
    return None
