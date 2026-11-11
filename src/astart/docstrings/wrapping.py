"""Opt-in wrapping through native comment and documentation AST mutations."""

from __future__ import annotations

from ast import (
    AsyncFunctionDef,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    Module,
    Pass,
    copy_location,
    dump,
    get_docstring,
    walk,
)
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Literal, final

from astart.docstrings.missing_returns import result_kinds
from astart.docstrings.prose import reflow_text
from astart.rules.provable import never_returns
from astart.source.ast import CommentedModule, SingleLineComment

if TYPE_CHECKING:
    from astart.docstrings import DocstringNode

type WrapStyle = Literal["preserve", "google", "numpy", "rest", "epytext"]


@final
class Constants:
    """Preservation boundaries for explicit wrapping.

    Attributes:
        minimum_width (Final[int]): Minimum useful configured source width.
        doc_pass_arity (Final[int]): Docstring followed by one redundant pass.
        code_markers (Final[tuple[str, ...]]): Conservative code indicators in
            ordinary comments.
        protected_sections (Final[frozenset[str]]): Sections containing
            literal/example syntax.

    """

    minimum_width: Final[int] = 20
    doc_pass_arity: Final[int] = 2
    code_markers: Final[tuple[str, ...]] = (
        "=",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        "::",
        ">>>",
    )
    protected_sections: Final[frozenset[str]] = frozenset(
        {"example", "examples", "references"},
    )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class WrapSettings:
    """Explicit choices for the native AST wrapping pass.

    Attributes:
        line_length (int): Source column budget for breakable prose.
        docstrings (bool): Reflow documentation nodes.
        comments (bool): Reflow ordinary standalone comment nodes.
        style (WrapStyle): Preserve detected syntax or explicitly select a
            style.
        boilerplate (bool): Insert TODO documentation constants where absent.
        strip_sections (bool): Explicitly remove documentation sections.
        remove_pass (bool): Remove a pass following a sole docstring.
        add_return_none (bool): Annotate functions proven to return nothing.
        normalize_lists (bool): Normalize numbered list closing separators.

    """

    line_length: int = 79
    docstrings: bool = True
    comments: bool = True
    style: WrapStyle = "preserve"
    boilerplate: bool = False
    strip_sections: bool = False
    remove_pass: bool = False
    add_return_none: bool = False
    normalize_lists: bool = True


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class WrapChanges:
    """Mutation counts and explicit preservation decisions.

    Attributes:
        docstrings_scanned (int): Existing documentation nodes inspected.
        docstrings_changed (int): Documents with actual semantic/layout edits.
        comment_blocks_changed (int): Ordinary comment blocks reflowed.
        structural_changes (int): Inserted docs, removed passes and return
            hints.
        skipped (tuple[str, ...]): Locations intentionally preserved.

    """

    docstrings_scanned: int
    docstrings_changed: int
    comment_blocks_changed: int
    structural_changes: int
    skipped: tuple[str, ...]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class WrapResult:
    """Convenience source result; core transformations use ``wrap_tree``.

    Attributes:
        source (str): Source emitted by the existing native AST infrastructure.
        docstrings_scanned (int): Existing documentation nodes inspected.
        docstrings_changed (int): Documents changed.
        comment_blocks_changed (int): Ordinary comment blocks changed.
        skipped (tuple[str, ...]): Explicit preservation decisions.

    """

    source: str
    docstrings_scanned: int
    docstrings_changed: int
    comment_blocks_changed: int
    skipped: tuple[str, ...]


@final
class AstWrapper:
    """Mutate one existing module without parsing or emitting Python source."""

    def __init__(
        self,
        *,
        tree: CommentedModule,
        settings: WrapSettings,
    ) -> None:
        """Bind the caller's authoritative AST and explicit options.

        Args:
            tree (CommentedModule): Existing mutable module; no clone or second
                AST is created.
            settings (WrapSettings): Independent wrapping options.

        Raises:
            ValueError: Configured source width is too small.

        """
        if settings.line_length < Constants.minimum_width:
            msg: str = "Source wrapping width must be at least 20 columns"
            raise ValueError(msg)
        self._tree: CommentedModule = tree
        self._settings: WrapSettings = settings
        self._skipped: list[str] = []

    def run(self) -> WrapChanges:
        """Apply structured mutations, retaining unaffected node identities.

        Returns:
            WrapChanges: Counts of actual changes and preservation decisions.

        Raises:
            ValueError: Existing doc edits conflict or comment ownership fails.

        """
        structural: int = self._structure()
        self._tree.index_docstrings()
        changed: int = 0
        scanned: int = 0
        if self._settings.docstrings:
            for document in self._tree.docstrings:
                scanned += 1
                changed += self._document(document=document)
        comments: int = self._comments() if self._settings.comments else 0
        return WrapChanges(
            docstrings_scanned=scanned,
            docstrings_changed=changed,
            comment_blocks_changed=comments,
            structural_changes=structural,
            skipped=tuple(self._skipped),
        )

    def _reflow(self, *, text: str, width: int) -> str:
        """Reflow one semantic prose field.

        Args:
            text (str): Text from an existing documentation/comment AST node.
            width (int): Available prose columns.

        Returns:
            str: Reflowed content with protected regions unchanged.

        """
        return reflow_text(
            text=text,
            width=max(1, width),
            normalize_lists=self._settings.normalize_lists,
        )

    def _document(self, *, document: DocstringNode) -> int:
        """Edit semantic text children, never replace the documentation node.

        Args:
            document (DocstringNode): Existing owner-linked structured
                document.

        Returns:
            int: One when its content or layout policy changed, otherwise zero.

        """
        if document.style == "mixed":
            self._skipped.append(
                f"line {document.lineno}: mixed documentation preserved",
            )
            return 0
        document.synchronize_text_parts()
        before: str = dump(node=document)
        width: int = self._settings.line_length - document.col_offset
        document.summary_node.text = self._reflow(
            text=document.summary,
            width=width,
        )
        document.description_node.text = self._reflow(
            text=document.description,
            width=width,
        )
        if self._settings.strip_sections:
            document.sections.clear()
        if self._settings.style != "preserve":
            document.style = self._settings.style
        for section in document.sections:
            if (
                section.title.rstrip(":").lower()
                in Constants.protected_sections
            ):
                continue
            if section.kind == "unknown":
                continue
            section.description = self._reflow(
                text=section.description,
                width=width - 4,
            )
            for entry in section.entries:
                label: str = entry.name or entry.type_name or ""
                entry.description = self._reflow(
                    text=entry.description,
                    width=width - max(8, len(label) + 6),
                )
                entry.sync_todo()
        document.synchronize_text_parts()
        changed: bool = dump(node=document) != before
        if changed:
            document.layout.preserve_original = False
            document.layout.is_trailing_blank = True
        return int(changed)

    def _comment_groups(self) -> list[tuple[SingleLineComment, ...]]:
        """Select contiguous ordinary standalone comments from AST nodes.

        Returns:
            list[tuple[SingleLineComment, ...]]: Groups with matching
                indentation and no directive/inline nodes.

        """
        groups: list[list[SingleLineComment]] = []
        active: list[SingleLineComment] = []
        for comment in self._tree.comments:
            if (
                not isinstance(comment, SingleLineComment)
                or comment.inline
                or comment.control is not None
            ):
                active = []
                continue
            if (
                not active
                or comment.col_offset != active[-1].col_offset
                or not active[-1].lineno
                <= comment.lineno
                <= active[-1].lineno + 1
            ):
                active = []
                groups.append(active)
            active.append(comment)
        return [tuple(group) for group in groups]

    def _comments(self) -> int:
        """Reflow AST comments through the module's shared lexical anchors.

        Returns:
            int: Number of changed comment blocks.

        """
        changed: int = 0
        for group in self._comment_groups():
            text: str = "\n".join(
                comment.text.removeprefix("#").removeprefix(" ")
                for comment in group
            )
            if any(marker in text for marker in Constants.code_markers):
                continue
            wrapped: str = self._reflow(
                text=text,
                width=self._settings.line_length - group[0].col_offset - 2,
            )
            lines: tuple[str, ...] = tuple(
                "# " + line if line else "#" for line in wrapped.splitlines()
            )
            if lines and lines != tuple(comment.text for comment in group):
                self._tree.replace_comment_lines(comments=group, lines=lines)
                changed += 1
        return changed

    def _structure(self) -> int:
        """Apply explicitly enabled changes to real statement/return nodes.

        Returns:
            int: Number of structural changes made.

        """
        changed: int = 0
        for node in walk(node=Module(body=self._tree.body, type_ignores=[])):
            if not isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
                continue
            if self._settings.boilerplate and get_docstring(node=node) is None:
                node.body.insert(
                    0,
                    copy_location(
                        new_node=Expr(value=Constant(value="TODO.")),
                        old_node=node.body[0],
                    ),
                )
                changed += 1
            if (
                self._settings.remove_pass
                and len(node.body) == Constants.doc_pass_arity
                and get_docstring(node=node) is not None
                and isinstance(node.body[-1], Pass)
            ):
                node.body.pop()
                changed += 1
            if (
                self._settings.add_return_none
                and isinstance(node, (FunctionDef, AsyncFunctionDef))
                and node.returns is None
                and not result_kinds(node=node)
                and not never_returns(function=node)
            ):
                node.returns = Constant(value=None)
                changed += 1
        return changed


def wrap_tree(
    *,
    tree: CommentedModule,
    settings: WrapSettings,
) -> WrapChanges:
    """Wrap the caller's AST nodes without parsing or emitting source.

    Args:
        tree (CommentedModule): The authoritative native module, mutated in
            place.
        settings (WrapSettings): Explicit formatting/structural options.

    Returns:
        WrapChanges: Actual mutation counts and preservation reasons.

    """
    return AstWrapper(tree=tree, settings=settings).run()


def wrap_source(*, source: str, settings: WrapSettings) -> WrapResult:
    """Adapt source text to the native AST manipulation pass.

    Args:
        source (str): Original Python module text.
        settings (WrapSettings): Explicit wrapping choices.

    Returns:
        WrapResult: Source emitted by the existing
            format-preserving AST infrastructure.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    changes: WrapChanges = wrap_tree(tree=tree, settings=settings)
    return WrapResult(
        source=tree.unparse(preserve_formatting=True),
        docstrings_scanned=changes.docstrings_scanned,
        docstrings_changed=changes.docstrings_changed,
        comment_blocks_changed=changes.comment_blocks_changed,
        skipped=changes.skipped,
    )
