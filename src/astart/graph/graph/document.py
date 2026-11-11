"""Token-backed AST document graph."""

from __future__ import annotations

from ast import AST, Module, iter_fields, parse, walk
from dataclasses import dataclass, field
from enum import StrEnum
from io import StringIO
from tokenize import ENDMARKER, TokenInfo, generate_tokens, tok_name
from typing import Self, cast

from astart.graph.graph.positions import (
    LineIndex,
    SourcePosition,
    SourceSpan,
)

type AstScalar = str | int | float | complex | bool | bytes | None
type AstListItem = AST | AstScalar
type AstFieldValue = AST | list[AstListItem] | tuple[AST, ...] | AstScalar


class TraversalOrder(StrEnum):
    """Supported document traversal orders.

    Attributes:
        AST_WALK: Ast walk associated with this instance.
        PREORDER: Preorder associated with this instance.

    """

    PREORDER = "preorder"
    AST_WALK = "ast_walk"


@dataclass(frozen=True, slots=True)
class AstToken:
    """A source token with concrete positions.

    Attributes:
        exact_kind (int): Exact kind retained as int by this instance.
        index (int): Index retained as int by this instance.
        kind (int): Kind retained as int by this instance.
        line_text (str): Line text retained as str by this instance.
        name (str): Identifier used to refer to the name.
        span (SourceSpan): Span retained as SourceSpan by this instance.
        text (str): Original source text retained for parsing and
            reconstruction.

    """

    index: int
    kind: int
    exact_kind: int
    name: str
    text: str
    span: SourceSpan
    line_text: str


@dataclass(frozen=True, slots=True)
class AstGraphNode:
    """Wrapper metadata for one raw AST node.

    Attributes:
        child_ids (tuple[int, ...]): Child ids retained as tuple[int, ...] by
            this instance.
        depth (int): Depth retained as int by this instance.
        field_index (int | None): Field index retained as int | None by this
            instance.
        field_name (str | None): Identifier used to refer to the field.
        kind (str): Kind retained as str by this instance.
        node (AST): AST node associated with this record.
        node_id (int): Node id retained as int by this instance.
        parent_id (int | None): Parent id retained as int | None by this
            instance.
        span (SourceSpan | None): Span retained as SourceSpan | None by this
            instance.

    """

    node: AST
    node_id: int
    kind: str
    span: SourceSpan | None
    parent_id: int | None
    field_name: str | None
    field_index: int | None
    depth: int
    child_ids: tuple[int, ...]

    def has_parent(self) -> bool:
        """Return whether this node has a parent wrapper.

        Returns:
            bool: Whether the requested condition holds.

        """
        return self.parent_id is not None


@dataclass(frozen=True, slots=True)
class AstDocument:
    """Parsed source, tokens, and indexed AST graph nodes.

    Attributes:
        filename (str): Filename retained as str by this instance.
        line_index (LineIndex): Line index retained as LineIndex by this
            instance.
        nodes (tuple[AstGraphNode, ...]): Nodes retained as tuple[AstGraphNode,
            ...] by this instance.
        source (str): Original source text retained for parsing and
            reconstruction.
        tokens (tuple[AstToken, ...]): Tokens retained as tuple[AstToken, ...]
            by this instance.
        tree (Module): Tree retained as Module by this instance.
        _nodes_by_id (dict[int, AstGraphNode]): TODO.
        _nodes_by_kind (dict[str, tuple[AstGraphNode, ...]]): TODO.

    """

    source: str
    filename: str
    tree: Module
    line_index: LineIndex
    tokens: tuple[AstToken, ...]
    nodes: tuple[AstGraphNode, ...]
    _nodes_by_id: dict[int, AstGraphNode] = field(repr=False)
    _nodes_by_kind: dict[str, tuple[AstGraphNode, ...]] = field(repr=False)

    @classmethod
    def from_source(cls, *, source: str, filename: str) -> Self:
        """Parse and tokenize source exactly once.

        Args:
            filename (str): Filename supplied as str for this operation.
            source (str): The source examined while parse
                and tokenize source exactly once.

        Returns:
            Self: Self produced by this operation.

        """
        tree: Module = parse(source=source, filename=filename, mode="exec")
        line_index: LineIndex = LineIndex.from_source(source=source)
        tokens: tuple[AstToken, ...] = _tokenize_source(
            source=source,
            line_index=line_index,
        )
        nodes: tuple[AstGraphNode, ...] = _index_tree(tree=tree)
        return cls(
            source=source,
            filename=filename,
            tree=tree,
            line_index=line_index,
            tokens=tokens,
            nodes=nodes,
            _nodes_by_id={node.node_id: node for node in nodes},
            _nodes_by_kind=_build_kind_index(nodes=nodes),
        )

    @classmethod
    def from_module(
        cls,
        *,
        tree: Module,
        source: str,
        filename: str,
    ) -> Self:
        """Build document from pre-parsed module and source (no re-parsing).

        Args:
            filename (str): Filename supplied as str for this operation.
            source (str): The source examined while build document from
                pre-parsed module and source (no re-parsing).
            tree (Module): Tree supplied as Module for this operation.

        Returns:
            Self: Self produced by this operation.

        """
        line_index: LineIndex = LineIndex.from_source(source=source)
        tokens: tuple[AstToken, ...] = _tokenize_source(
            source=source,
            line_index=line_index,
        )
        nodes: tuple[AstGraphNode, ...] = _index_tree(tree=tree)
        return cls(
            source=source,
            filename=filename,
            tree=tree,
            line_index=line_index,
            tokens=tokens,
            nodes=nodes,
            _nodes_by_id={node.node_id: node for node in nodes},
            _nodes_by_kind=_build_kind_index(nodes=nodes),
        )

    def nodes_of_kind(self, *, kind: str) -> tuple[AstGraphNode, ...]:
        """Return all indexed nodes with the requested AST kind.

        Args:
            kind (str): Kind supplied as str for this operation.

        Returns:
            tuple[AstGraphNode, ...]: tuple[AstGraphNode, ...] produced by this
                operation.

        """
        return self._nodes_by_kind.get(kind, ())

    def node_by_id(self, *, node_id: int) -> AstGraphNode | None:
        """Return one graph node by raw AST node identity.

        Args:
            node_id (int): Node id supplied as int for this operation.

        Returns:
            AstGraphNode | None:
                AstGraphNode | None produced by this operation.

        """
        return self._nodes_by_id.get(node_id)

    def parent_of(self, *, node: AstGraphNode) -> AstGraphNode | None:
        """Return the parent wrapper for ``node`` when available.

        Args:
            node (AstGraphNode): The node examined while return the parent
                wrapper for ``node`` when available.

        Returns:
            AstGraphNode | None:
                AstGraphNode | None produced by this operation.

        """
        if node.parent_id is None:
            return None
        return self.node_by_id(node_id=node.parent_id)

    def children_of(self, *, node: AstGraphNode) -> tuple[AstGraphNode, ...]:
        """Return direct child wrappers for ``node``.

        Args:
            node (AstGraphNode): The node examined while return
                direct child wrappers for ``node``.

        Returns:
            tuple[AstGraphNode, ...]: tuple[AstGraphNode, ...] produced by this
                operation.

        """
        children: list[AstGraphNode] = []
        child_id: int
        for child_id in node.child_ids:
            child: AstGraphNode | None = self.node_by_id(node_id=child_id)
            if child is not None:
                children.append(child)
        return tuple(children)

    def ancestors_of(self, *, node: AstGraphNode) -> tuple[AstGraphNode, ...]:
        """Return ancestors from parent to root.

        Args:
            node (AstGraphNode): The node examined while return ancestors from
                parent to root.

        Returns:
            tuple[AstGraphNode, ...]: tuple[AstGraphNode, ...] produced by this
                operation.

        """
        ancestors: list[AstGraphNode] = []
        current: AstGraphNode | None = self.parent_of(node=node)
        while current is not None:
            ancestors.append(current)
            current = self.parent_of(node=current)
        return tuple(ancestors)

    def tokens_for_span(self, *, span: SourceSpan) -> tuple[AstToken, ...]:
        """Return tokens intersecting ``span``.

        Args:
            span (SourceSpan): Span supplied as SourceSpan for this operation.

        Returns:
            tuple[AstToken, ...]: tuple[AstToken, ...] produced by this
                operation.

        """
        return tuple(
            token for token in self.tokens if token.span.intersects(other=span)
        )

    def source_for_node(self, *, node: AstGraphNode) -> str | None:
        """Return exact original source for ``node`` when it has a span.

        Args:
            node (AstGraphNode): The node examined while return exact original
                source for ``node`` when it has a span.

        Returns:
            str | None: str | None produced by this operation.

        """
        if node.span is None:
            return None
        return self.line_index.span_text(span=node.span)

    def walk_nodes(
        self,
        *,
        order: TraversalOrder = TraversalOrder.PREORDER,
    ) -> tuple[AstGraphNode, ...]:
        """Return document nodes in a stable traversal order.

        Args:
            order (TraversalOrder): Order supplied as TraversalOrder for this
                operation.

        Returns:
            tuple[AstGraphNode, ...]: tuple[AstGraphNode, ...] produced by this
                operation.

        """
        if order is TraversalOrder.AST_WALK:
            return tuple(
                self._nodes_by_id[id(node)]
                for node in walk(node=self.tree)
                if id(node) in self._nodes_by_id
            )
        return self.nodes


def read_node_span(*, node: AST) -> SourceSpan | None:
    """Read a node source span when the AST provides one.

    Args:
        node (AST): The node examined while read a node
            source span when the AST provides one.

    Returns:
        SourceSpan | None: SourceSpan | None produced by this operation.

    """
    line: int | None = _read_int_attribute(node=node, name="lineno")
    column: int | None = _read_int_attribute(node=node, name="col_offset")
    end_line: int | None = _read_int_attribute(node=node, name="end_lineno")
    end_column: int | None = _read_int_attribute(
        node=node,
        name="end_col_offset",
    )
    if (
        line is None
        or column is None
        or end_line is None
        or end_column is None
    ):
        return None
    return SourceSpan(
        start=SourcePosition(line=line, column=column),
        end=SourcePosition(line=end_line, column=end_column),
    )


@dataclass(frozen=True, slots=True)
class _NodeRecordRequest:
    """Recursive AST node indexing request.

    Attributes:
        depth (int): Depth retained as int by this instance.
        field_index (int | None): Field index retained as int | None by this
            instance.
        field_name (str | None): Identifier used to refer to the field.
        node (AST): AST node associated with this record.
        parent_id (int | None): Parent id retained as int | None by this
            instance.

    """

    node: AST
    parent_id: int | None
    field_name: str | None
    field_index: int | None
    depth: int


def _read_int_attribute(*, node: AST, name: str) -> int | None:
    """Read an integer attribute from an AST node.

    Args:
        name (str): Identifier of the name being resolved.
        node (AST): The node examined while read an integer attribute from an
            AST node.

    Returns:
        int | None: int | None produced by this operation.

    """
    value: AstScalar = cast(typ="AstScalar", val=getattr(node, name, None))
    if isinstance(value, int):
        return value
    return None


def _tokenize_source(
    *,
    source: str,
    line_index: LineIndex,
) -> tuple[AstToken, ...]:
    """Tokenize source into position-aware tokens.

    Args:
        line_index (LineIndex): Line index supplied as LineIndex for this
            operation.
        source (str): The source examined while tokenize
            source into position-aware tokens.

    Returns:
        tuple[AstToken, ...]: tuple[AstToken, ...] produced by this operation.

    """
    buffer: StringIO = StringIO(initial_value=source)
    raw_tokens: tuple[TokenInfo, ...] = tuple(
        generate_tokens(readline=buffer.readline),
    )
    tokens: list[AstToken] = []
    raw_index: int
    token: TokenInfo
    for raw_index, token in enumerate(iterable=raw_tokens):
        if token.type == ENDMARKER:
            continue
        span: SourceSpan = SourceSpan(
            start=SourcePosition(
                line=token.start[0],
                column=token.start[1],
            ),
            end=SourcePosition(
                line=token.end[0],
                column=token.end[1],
            ),
        )
        tokens.append(
            AstToken(
                index=raw_index,
                kind=token.type,
                exact_kind=token.exact_type,
                name=tok_name.get(token.type, str(object=token.type)),
                text=line_index.span_text(span=span),
                span=span,
                line_text=token.line,
            ),
        )
    return tuple(tokens)


def _index_tree(*, tree: Module) -> tuple[AstGraphNode, ...]:
    """Create parent-aware graph wrappers for every AST node.

    Args:
        tree (Module): Tree supplied as Module for this operation.

    Returns:
        tuple[AstGraphNode, ...]: tuple[AstGraphNode, ...] produced by this
            operation.

    """
    records: list[AstGraphNode] = []
    _: int = _append_node_record(
        records=records,
        request=_NodeRecordRequest(
            node=tree,
            parent_id=None,
            field_name=None,
            field_index=None,
            depth=0,
        ),
    )
    return tuple(records)


def _append_node_record(
    *,
    records: list[AstGraphNode],
    request: _NodeRecordRequest,
) -> int:
    """Append one wrapper record and recurse into children.

    Args:
        records (list[AstGraphNode]): Records supplied as list[AstGraphNode]
            for this operation.
        request (_NodeRecordRequest): Request supplied as _NodeRecordRequest
            for this operation.

    Returns:
        int: int produced by this operation.

    """
    node_id: int = id(request.node)
    child_ids: list[int] = []
    field: str
    value: AstFieldValue
    for field, raw_value in iter_fields(node=request.node):
        value = cast(typ="AstFieldValue", val=raw_value)
        if isinstance(value, AST):
            child_ids.append(id(value))
            _append_node_record(
                records=records,
                request=_NodeRecordRequest(
                    node=value,
                    parent_id=node_id,
                    field_name=field,
                    field_index=None,
                    depth=request.depth + 1,
                ),
            )
        elif isinstance(value, list):
            child_ids.extend(
                _append_list_children(
                    records=records,
                    values=value,
                    parent_id=node_id,
                    field_name=field,
                    depth=request.depth + 1,
                ),
            )
    records.append(
        AstGraphNode(
            node=request.node,
            node_id=node_id,
            kind=type(request.node).__name__,
            span=read_node_span(node=request.node),
            parent_id=request.parent_id,
            field_name=request.field_name,
            field_index=request.field_index,
            depth=request.depth,
            child_ids=tuple(child_ids),
        ),
    )
    return node_id


def _append_list_children(
    *,
    records: list[AstGraphNode],
    values: list[AstListItem],
    parent_id: int,
    field_name: str,
    depth: int,
) -> list[int]:
    """Append list-valued child nodes and return their identities.

    Args:
        depth (int): Depth supplied as int for this operation.
        field_name (str): Identifier of the field being resolved.
        parent_id (int): Parent id supplied as int for this operation.
        records (list[AstGraphNode]): Records supplied as list[AstGraphNode]
            for this operation.
        values (list[AstListItem]): Values supplied as list[AstListItem] for
            this operation.

    Returns:
        list[int]: list[int] produced by this operation.

    """
    child_ids: list[int] = []
    index: int
    item: AstListItem
    for index, item in enumerate(iterable=values):
        if not isinstance(item, AST):
            continue
        child_ids.append(id(item))
        _append_node_record(
            records=records,
            request=_NodeRecordRequest(
                node=item,
                parent_id=parent_id,
                field_name=field_name,
                field_index=index,
                depth=depth,
            ),
        )
    return child_ids


def _build_kind_index(
    *,
    nodes: tuple[AstGraphNode, ...],
) -> dict[str, tuple[AstGraphNode, ...]]:
    """Build an immutable kind index.

    Args:
        nodes (tuple[AstGraphNode, ...]): Collection of nodes supplied for this
            operation.

    Returns:
        dict[str, tuple[AstGraphNode, ...]]: dict[str, tuple[AstGraphNode,
            ...]] produced by this operation.

    """
    buckets: dict[str, list[AstGraphNode]] = {}
    node: AstGraphNode
    for node in nodes:
        buckets.setdefault(node.kind, []).append(node)
    return {kind: tuple(bucket) for kind, bucket in buckets.items()}
