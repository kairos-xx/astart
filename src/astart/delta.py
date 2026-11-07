"""Identity-aware incremental source-map reconciliation for Python ASTs.

The graph records stable AST identities and sibling ordering independently of
original AST location attributes. Revisions are validated against the fully
parsed output; deltas classify the minimum lexical and structural change set.
"""

from __future__ import annotations

from ast import AST, iter_fields
from bisect import bisect_left
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import TYPE_CHECKING, Final, Literal, cast, final

from astart.node_attributes import list_items

if TYPE_CHECKING:
    from astart.tokens import TokenSnapshot


@final
class Constants:
    """Group module-level constants.

    Attributes:
        max_diff_window: Grouped module constant.

    """

    max_diff_window: Final[int] = 12000


type ChangeKind = Literal[
    "inserted",
    "removed",
    "moved",
    "shifted",
    "modified",
    "unchanged",
]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SourceChange:
    """A changed physical-line interval in two consecutive source revisions.

    Attributes:
        old_start: One-based first affected line in the previous revision.
        old_end: One-based exclusive last affected line, previous revision.
        new_start: One-based first affected line in the current revision.
        new_end: One-based exclusive last affected line, current revision.

    """

    old_start: int
    old_end: int
    new_start: int
    new_end: int

    @property
    def line_delta(self) -> int:
        """Net physical-line displacement introduced by the edit.

        Returns:
            int produced by this operation.

        """
        return self.new_end - self.new_start - (self.old_end - self.old_start)


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NodeChange:
    """One AST node's identity-stable transition between source revisions.

    Attributes:
        node_id: Process-local identity of the original mutable AST object.
        kind: Classification of the edit or coordinate displacement.
        before: Previous immutable snapshot, or None for inserted nodes.
        after: Current immutable snapshot, or None for removed nodes.
        parent_id: Current parent identity, or None when removed or root.
        nested: True when an ancestor's source range changed as well.

    """

    node_id: int
    kind: ChangeKind
    before: TokenSnapshot | None
    after: TokenSnapshot | None
    parent_id: int | None
    nested: bool

    @property
    def line_shift(self) -> int:
        """Signed start-line change, or zero when a revision is missing.

        Returns:
            int produced by this operation.

        """
        return (
            self.after.span.start_line - self.before.span.start_line
            if self.before is not None and self.after is not None
            else 0
        )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ChangeSet:
    """Immutable list of affected AST identities and edited source regions.

    Attributes:
        revision: Current token-source revision number.
        source_changes: Minimal line-based edit blocks.
        nodes: Changed, moved, inserted, removed, or shifted AST nodes.
        unchanged: Number of AST nodes retaining their exact prior snapshots.
        moved: Identities identified as moved rather than merely reindexed.
        semantic_links: Changed AST identities and their dependent semantic
            documentation-entry identities.

    """

    revision: int
    source_changes: tuple[SourceChange, ...]
    nodes: tuple[NodeChange, ...]
    unchanged: int
    moved: tuple[int, ...]
    semantic_links: tuple[tuple[int, int], ...] = ()

    def for_node(self, *, node: AST) -> NodeChange | None:
        """Find a node's transition, excluding unchanged identities.

        Args:
            node: A current or recently removed AST node.

        Returns:
            Its transition, if the node was affected by this revision.

        """
        return next(
            (change for change in self.nodes if change.node_id == id(node)),
            None,
        )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NodePath:
    """An AST object's parent and its position in the parent's AST field.

    Attributes:
        field: Field retained as str by this instance.
        index: Index retained as int by this instance.
        parent: Parent retained as int | None by this instance.

    """

    parent: int | None
    field: str
    index: int


def node_paths(*, root: AST) -> dict[int, NodePath]:
    """Capture nested AST ownership without touching locations.

    Args:
        root: Filesystem path identifying the root.

    Returns:
        dict[int, NodePath] produced by this operation.

    """
    result: dict[int, NodePath] = {
        id(root): NodePath(parent=None, field="", index=0),
    }
    pending: list[AST] = [root]
    while pending:
        owner: AST = pending.pop()
        for field, value in iter_fields(node=owner):
            if isinstance(value, AST):
                children: tuple[AST, ...] = (value,)
            elif isinstance(value, list):
                children = tuple(
                    item
                    for item in list_items(
                        value=cast(typ="list[object]", val=value),
                    )
                    if isinstance(item, AST)
                )
            else:
                continue
            for index, child in enumerate(iterable=children):
                if id(child) not in result:
                    result[id(child)] = NodePath(
                        parent=id(owner),
                        field=field,
                        index=index,
                    )
                    pending.append(child)
    return result


def _unstable_siblings(
    *,
    before: tuple[int, ...],
    after: tuple[int, ...],
) -> set[int]:
    """Identify reordered common siblings in O(n log n) time.

    Args:
        after: After supplied as tuple[int, ...] for this operation.
        before: Before supplied as tuple[int, ...] for this operation.

    Returns:
        set[int] produced by this operation.

    """
    ranks: dict[int, int] = {
        identity: index for index, identity in enumerate(iterable=before)
    }
    common: list[int] = [identity for identity in after if identity in ranks]
    tails: list[int] = []
    indexes: list[int] = []
    predecessors: list[int] = [-1] * len(common)
    for index, identity in enumerate(iterable=common):
        rank: int = ranks[identity]
        slot: int = bisect_left(a=tails, x=rank)
        if slot > 0:
            predecessors[index] = indexes[slot - 1]
        if slot == len(tails):
            tails.append(rank)
            indexes.append(index)
        else:
            tails[slot] = rank
            indexes[slot] = index
    stable: set[int] = set()
    if indexes:
        cursor: int = indexes[-1]
        while cursor != -1:
            stable.add(common[cursor])
            cursor = predecessors[cursor]
    return set(common) - stable


def moved_identities(
    *,
    old: dict[int, NodePath],
    new: dict[int, NodePath],
) -> set[int]:
    """Distinguish moves from shifts using stable LCS sibling identities.

    Args:
        new: New supplied as dict[int, NodePath] for this operation.
        old: Old supplied as dict[int, NodePath] for this operation.

    Returns:
        set[int] produced by this operation.

    """
    shifted: set[int] = set()
    old_groups: dict[tuple[int | None, str], list[tuple[int, int]]] = {}
    new_groups: dict[tuple[int | None, str], list[tuple[int, int]]] = {}
    for identity, path in old.items():
        old_groups.setdefault((path.parent, path.field), []).append(
            (path.index, identity),
        )
    for identity, path in new.items():
        new_groups.setdefault((path.parent, path.field), []).append(
            (path.index, identity),
        )
        previous: NodePath | None = old.get(identity)
        if previous is not None and (previous.parent, previous.field) != (
            path.parent,
            path.field,
        ):
            shifted.add(identity)
    for key, new_members in new_groups.items():
        if key not in old_groups:
            continue
        before: tuple[int, ...] = tuple(
            (identity for _, identity in sorted(old_groups[key])),
        )
        after: tuple[int, ...] = tuple(
            (identity for _, identity in sorted(new_members)),
        )
        shifted.update(_unstable_siblings(before=before, after=after))
    return shifted


def _source_changes(*, before: str, after: str) -> tuple[SourceChange, ...]:
    """Compute edit blocks at physical-line granularity, not changed nodes.

    Args:
        after: After supplied as str for this operation.
        before: Before supplied as str for this operation.

    Returns:
        tuple[SourceChange, ...] produced by this operation.

    """
    previous: list[str] = before.splitlines(keepends=True)
    current: list[str] = after.splitlines(keepends=True)
    first: int = 0
    while (
        first < len(previous)
        and first < len(current)
        and (previous[first] == current[first])
    ):
        first += 1
    old_end: int = len(previous)
    new_end: int = len(current)
    while (
        old_end > first
        and new_end > first
        and (previous[old_end - 1] == current[new_end - 1])
    ):
        old_end -= 1
        new_end -= 1
    if first == old_end and first == new_end:
        return ()
    if old_end - first + new_end - first > Constants.max_diff_window:
        return (
            SourceChange(
                old_start=first + 1,
                old_end=old_end + 1,
                new_start=first + 1,
                new_end=new_end + 1,
            ),
        )
    matcher: SequenceMatcher[str] = SequenceMatcher(
        isjunk=None,
        a=previous[first:old_end],
        b=current[first:new_end],
        autojunk=False,
    )
    return tuple(
        (
            SourceChange(
                old_start=first + i + 1,
                old_end=first + j + 1,
                new_start=first + k + 1,
                new_end=first + stop + 1,
            )
            for tag, i, j, k, stop in matcher.get_opcodes()
            if tag != "equal"
        ),
    )


def _classify_snapshot(
    *,
    previous: TokenSnapshot | None,
    snapshot: TokenSnapshot,
    relocated: bool,
) -> ChangeKind:
    """Classify a node's lexical and structural transition.

    Args:
        previous: Previous supplied as TokenSnapshot | None for this operation.
        relocated: Relocated supplied as bool for this operation.
        snapshot: Snapshot supplied as TokenSnapshot for this operation.

    Returns:
        ChangeKind produced by this operation.

    """
    if previous is None:
        return "inserted"
    if relocated:
        return "moved"
    if previous.span != snapshot.span:
        return (
            "shifted"
            if previous.source_text == snapshot.source_text
            else "modified"
        )
    if previous.source_text != snapshot.source_text or (
        len(previous.tokens) != len(snapshot.tokens)
        or any(
            (
                before.type != after.type or before.string != after.string
                for before, after in zip(
                    previous.tokens,
                    snapshot.tokens,
                    strict=True,
                )
            ),
        )
    ):
        return "modified"
    return "unchanged"


@final
class IncrementalSourceGraph:
    """Track stable node identities and reconcile lexical revisions.

    The host validates and tokenizes a new complete source.
    This graph then computes localized movement and nested change propagation
    without invalidating unaffected immutable per-node snapshots.
    """

    def __init__(self, *, root: AST) -> None:
        """Capture the initial object ownership graph.

        Args:
            root: Mutable root AST node.

        """
        self._paths: dict[int, NodePath] = node_paths(root=root)
        self._source: str = ""
        self._snapshots: dict[int, TokenSnapshot] = {}
        self._last: ChangeSet = ChangeSet(
            revision=0,
            source_changes=(),
            nodes=(),
            unchanged=0,
            moved=(),
        )

    @property
    def last_change(self) -> ChangeSet:
        """Return the last immutable source and node change set.

        Returns:
            ChangeSet produced by this operation.

        """
        return self._last

    def mark_baseline(self) -> None:
        """Mark an initial parsed tree as a starting state, not a user edit."""
        self._last = ChangeSet(
            revision=self._last.revision,
            source_changes=(),
            nodes=(),
            unchanged=len(self._snapshots),
            moved=(),
        )

    def reconcile(
        self,
        *,
        root: AST,
        source: str,
        snapshots: dict[int, TokenSnapshot],
        revision: int,
        semantic_dependencies: dict[int, tuple[int, ...]] | None = None,
    ) -> tuple[dict[int, TokenSnapshot], ChangeSet]:
        """Update only affected identities; keep valid unchanged snapshots.

        Args:
            root: Current mutable tree after transformations.
            source: Fully validated current source text.
            snapshots: Correct, newly mapped source snapshots.
            revision: Current source generation.
            semantic_dependencies: AST identity to externally linked
                documentation-entry identities, when available.

        Returns:
            Reconciled snapshots and immutable affected-node description.

        """
        paths: dict[int, NodePath] = node_paths(root=root)
        relocated: set[int] = moved_identities(old=self._paths, new=paths)
        reconciled: dict[int, TokenSnapshot] = {}
        transitions: list[NodeChange] = []
        unchanged: int = 0
        dirty: set[int] = set()
        for identity, snapshot in snapshots.items():
            previous: TokenSnapshot | None = self._snapshots.get(identity)
            current_path: NodePath | None = paths.get(identity)
            kind: ChangeKind = _classify_snapshot(
                previous=previous,
                snapshot=snapshot,
                relocated=identity in relocated,
            )
            if (
                kind == "unchanged"
                and previous is not None
                and (previous.tokens == snapshot.tokens)
            ):
                reconciled[identity] = previous
                unchanged += 1
            else:
                reconciled[identity] = snapshot
                if kind == "unchanged":
                    kind = "shifted"
                dirty.add(identity)
                transitions.append(
                    NodeChange(
                        node_id=identity,
                        kind=kind,
                        before=previous,
                        after=snapshot,
                        parent_id=current_path.parent
                        if current_path is not None
                        else None,
                        nested=False,
                    ),
                )
        for identity, previous in self._snapshots.items():
            if identity not in reconciled:
                dirty.add(identity)
                transitions.append(
                    NodeChange(
                        node_id=identity,
                        kind="removed",
                        before=previous,
                        after=None,
                        parent_id=None,
                        nested=False,
                    ),
                )
        parents: set[int] = set()
        for identity in dirty:
            path: NodePath | None = paths.get(identity)
            while path is not None and path.parent is not None:
                parents.add(path.parent)
                path = paths.get(path.parent)
        transitions = [
            NodeChange(
                node_id=item.node_id,
                kind=item.kind,
                before=item.before,
                after=item.after,
                parent_id=item.parent_id,
                nested=item.parent_id in parents,
            )
            for item in transitions
        ]
        result: ChangeSet = ChangeSet(
            revision=revision,
            source_changes=_source_changes(before=self._source, after=source),
            nodes=tuple(transitions),
            unchanged=unchanged,
            moved=tuple(sorted(relocated)),
            semantic_links=tuple(
                (change.node_id, dependent)
                for change in transitions
                for dependent in (semantic_dependencies or {}).get(
                    change.node_id,
                    (),
                )
            ),
        )
        self._paths = paths
        self._source = source
        self._snapshots = reconciled
        self._last = result
        return (reconciled, result)
