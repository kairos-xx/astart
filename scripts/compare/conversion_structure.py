"""AST-based comparison of generated documentation and declarations."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    FunctionDef,
    Import,
    ImportFrom,
    Module,
    Name,
    ParamSpec,
    Subscript,
    TypeAlias,
    TypeVar,
    TypeVarTuple,
    dump,
    expr,
    get_docstring,
    iter_child_nodes,
    unparse,
)
from collections import Counter
from dataclasses import asdict, dataclass, field, replace
from typing import TYPE_CHECKING, Final, TypedDict, cast, final

from astart.rules.alias_declarations import AliasDeclarations
from astart.source.api import parse

type DictStr = dict[str, str]

if TYPE_CHECKING:
    from astart import CommentedModule
    from astart.docstrings import DocstringNode
    from astart.rules.alias_declarations import LegacyAlias
    from astart.semantic.identities import Symbol

    from scripts.compare.session import ComparisonSession


@final
class Constants:
    """Shared artifact report categories and preview bounds.

    Attributes:
        categories (Final[tuple[str, ...]]): Ordered declaration and
            documentation categories.
        preview_limit (Final[int]): Maximum characters shown in a Markdown
            evidence block.
        labels (Final[dict[str, str]]): Human-readable artifact category names.

    """

    categories: Final[tuple[str, ...]] = (
        "docstrings",
        "type_aliases",
        "protocols",
        "typevars",
        "paramspecs",
        "type_var_tuples",
        "classes",
        "declaration_uses",
    )
    preview_limit: Final[int] = 2000
    labels: Final[dict[str, str]] = {
        "docstrings": "Docstrings",
        "type_aliases": "Type aliases",
        "protocols": "Protocols",
        "typevars": "TypeVar",
        "paramspecs": "ParamSpec",
        "type_var_tuples": "TypeVarTuple",
        "classes": "Classes",
        "declaration_uses": "Declaration uses",
    }


@final
@dataclass(frozen=True, slots=True)
class Artifact:
    """One source-backed documentation or declaration contract.

    Attributes:
        kind (str): Documentation, alias, protocol or type parameter
            declaration.
        key (str): Qualified declaration identity, with overload occurrence
            suffixes.
        line (int): Source line containing the declaration.
        content (str): Full readable contract used as comparison evidence.
        shape (str): Location-free structural comparison key.
        fields (DictStr): Structured documentation fields for difference
            explanations.

    """

    kind: str
    key: str
    line: int
    content: str
    shape: str
    fields: DictStr = field(default_factory=dict)


@final
@dataclass(frozen=True, slots=True)
class Difference:
    """A current-run comparison with evidence from both source files.

    Attributes:
        kind (str): Artifact category.
        key (str): Reference identity, or output identity for extra artifacts.
        verdict (str): Exact, equivalent spelling, changed, missing or extra.
        expected (Artifact | None): Curated reference evidence.
        actual (Artifact | None): Generated output evidence.
        explanation (str): Meaning and limits of this comparison.

    """

    kind: str
    key: str
    verdict: str
    expected: Artifact | None
    actual: Artifact | None
    explanation: str


def _protocol_shape(*, node: ClassDef) -> str:
    """Describe protocol member contracts independently of class naming.

    Args:
        node (ClassDef): Protocol class.

    Returns:
        str: Ordered signatures, generic parameters and declared attributes.

    """
    members: list[str] = [
        *(dump(node=item) for item in node.type_params),
        *(dump(node=item) for item in node.bases),
        *(dump(node=item) for item in node.decorator_list),
    ]
    for member in node.body:
        if isinstance(member, (FunctionDef, AsyncFunctionDef)):
            members.append(
                repr(
                    (
                        type(member).__name__,
                        member.name,
                        dump(node=member.args),
                        dump(node=member.returns) if member.returns else None,
                        tuple(
                            dump(node=item) for item in member.decorator_list
                        ),
                        tuple(dump(node=item) for item in member.type_params),
                    ),
                ),
            )
        elif isinstance(member, (AnnAssign, Assign)):
            members.append(dump(node=member))
    return repr(members)


def _typing_name(*, node: expr, imports: DictStr) -> str:
    """Resolve typing constructor spelling directly from native syntax.

    Args:
        node (expr): Imported constructor or parameterized base expression.
        imports (DictStr): Typing import metadata.

    Returns:
        str: Canonical constructor name, or an empty unknown spelling.

    """
    if isinstance(node, Subscript):
        return _typing_name(node=node.value, imports=imports)
    if isinstance(node, Name):
        return imports.get(node.id, node.id)
    if (
        isinstance(node, Attribute)
        and isinstance(node.value, Name)
        and imports.get(node.value.id, node.value.id)
        in {"typing", "typing_extensions"}
    ):
        return node.attr
    return ""


def _declarations(
    *,
    node: AST,
    trail: tuple[str, ...],
    key: str,
    imports: DictStr,
) -> list[Artifact]:
    """Collect declarations at one native AST node.

    Args:
        node (AST): Current declaration candidate.
        trail (tuple[str, ...]): Lexical owner path.
        key (str): Qualified class identity.
        imports (DictStr): Known typing import aliases.

    Returns:
        list[Artifact]: Declaration evidence at this node.

    """
    found: list[Artifact] = []
    if isinstance(node, TypeAlias):
        found.append(
            Artifact(
                kind="type_aliases",
                key=".".join((*trail, node.name.id)),
                line=node.lineno,
                content=unparse(ast_obj=node),
                shape=repr(
                    (
                        tuple(dump(node=item) for item in node.type_params),
                        dump(node=node.value),
                    ),
                ),
            ),
        )
    if isinstance(node, AnnAssign) and isinstance(node.target, Name):
        annotation: str = _typing_name(node=node.annotation, imports=imports)
        if imports.get(annotation, annotation) == "TypeAlias" and node.value:
            found.append(
                Artifact(
                    kind="type_aliases",
                    key=".".join((*trail, node.target.id)),
                    line=node.lineno,
                    content=unparse(ast_obj=node),
                    shape=repr(((), dump(node=node.value))),
                ),
            )
    if isinstance(node, ClassDef) and any(
        _typing_name(node=base, imports=imports) == "Protocol"
        for base in node.bases
    ):
        found.append(
            Artifact(
                kind="protocols",
                key=key,
                line=node.lineno,
                content=unparse(ast_obj=node),
                shape=_protocol_shape(node=node),
            ),
        )
    if isinstance(node, ClassDef) and not found:
        found.append(
            Artifact(
                kind="classes",
                key=key,
                line=node.lineno,
                content=unparse(ast_obj=node),
                shape=_protocol_shape(node=node),
            ),
        )
    if isinstance(node, Assign) and isinstance(node.value, Call):
        maker: str = _typing_name(node=node.value.func, imports=imports)
        if maker in {
            "TypeVar",
            "ParamSpec",
            "TypeVarTuple",
        }:
            found.extend(
                Artifact(
                    kind={
                        "TypeVar": "typevars",
                        "ParamSpec": "paramspecs",
                        "TypeVarTuple": "type_var_tuples",
                    }[maker],
                    key=".".join((*trail, target.id)),
                    line=node.lineno,
                    content=unparse(ast_obj=node),
                    shape=dump(node=node.value),
                )
                for target in node.targets
                if isinstance(target, Name)
            )
    return found


def _legacy_alias(
    *,
    node: AST,
    tree: CommentedModule,
    legacy: AliasDeclarations,
    trail: tuple[str, ...],
) -> list[Artifact]:
    """Reuse native alias inference for implicit type-only assignments.

    Args:
        node (AST): Assignment candidate.
        tree (CommentedModule): Shared parsed module.
        legacy (AliasDeclarations): Cached alias declaration analysis.
        trail (tuple[str, ...]): Lexical owner identity.

    Returns:
        list[Artifact]: Proven implicit alias evidence, when present.

    """
    declared: list[Artifact] = []
    if isinstance(node, Assign):
        alias: LegacyAlias | None = legacy.get(module=tree, statement=node)
        if alias is not None:
            declared.append(
                Artifact(
                    kind="type_aliases",
                    key=".".join((*trail, alias.name.id)),
                    line=node.lineno,
                    content=unparse(ast_obj=node),
                    shape=repr(
                        (
                            tuple(
                                dump(node=item) for item in alias.parameters
                            ),
                            dump(node=alias.value),
                        ),
                    ),
                ),
            )
    return declared


def artifacts(
    *,
    source: str,
    tree: CommentedModule | None = None,
) -> list[Artifact]:
    """Index contracts from one AST without importing or executing source.

    Args:
        source (str): Reference or generated Python source.
        tree (CommentedModule | None): Shared module; parse only when absent.

    Returns:
        list[Artifact]: Source-ordered artifacts, including
            nested and repeated definitions.

    """
    if tree is None:
        tree = parse(source=source)
    imports: DictStr = {
        item.asname or item.name: item.name
        for statement in tree.body
        if isinstance(statement, ImportFrom)
        and statement.module in {"typing", "typing_extensions"}
        for item in statement.names
    }
    imports.update(
        (item.asname or item.name, item.name)
        for statement in tree.body
        if isinstance(statement, Import)
        for item in statement.names
        if item.name in {"typing", "typing_extensions"}
    )
    documents: dict[int, DocstringNode] = {
        id(doc.owner) if doc.owner else id(tree): doc
        for doc in tree.docstrings
    }
    legacy: AliasDeclarations = AliasDeclarations()
    found: list[Artifact] = []
    counts: Counter[tuple[str, str]] = Counter()
    declarations: dict[str, AST] = {}
    pending: list[tuple[AST, tuple[str, ...]]] = [(tree, ())]
    while pending:
        node, trail = pending.pop()
        nested: tuple[str, ...] = trail
        if isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
            nested = (*trail, node.name)
        key: str = ".".join(nested) or "<module>"
        if isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
            counts["owner", key] += 1
            occurrence: int = counts["owner", key]
            if occurrence > 1:
                key += f"#definition:{occurrence}"
        documentation: str | None = (
            get_docstring(node=node)
            if isinstance(
                node,
                (Module, FunctionDef, AsyncFunctionDef, ClassDef),
            )
            else None
        )
        if documentation is not None:
            found.append(
                Artifact(
                    kind="docstrings",
                    key=key,
                    line=getattr(node, "lineno", 1),
                    content=documentation,
                    shape=documentation,
                    fields=_doc_fields(document=documents.get(id(node))),
                ),
            )
        declared: list[Artifact] = _declarations(
            node=node,
            trail=trail,
            key=key,
            imports=imports,
        )
        declared.extend(
            _legacy_alias(
                node=node,
                tree=tree,
                legacy=legacy,
                trail=trail,
            ),
        )
        found.extend(declared)
        if isinstance(
            node,
            (FunctionDef, AsyncFunctionDef, ClassDef, TypeAlias),
        ):
            owner_key: str = (
                ".".join((*trail, node.name.id))
                if isinstance(node, TypeAlias)
                else key
            )
            found.extend(
                Artifact(
                    kind=(
                        "paramspecs"
                        if isinstance(parameter, ParamSpec)
                        else "type_var_tuples"
                        if isinstance(parameter, TypeVarTuple)
                        else "typevars"
                    ),
                    key=f"{owner_key}.{parameter.name}",
                    line=node.lineno,
                    content=unparse(ast_obj=parameter),
                    shape=dump(node=parameter),
                )
                for parameter in node.type_params
                if isinstance(parameter, (TypeVar, ParamSpec, TypeVarTuple))
            )
        declarations.update(
            (item.key, node)
            for item in declared
            if item.kind in {"type_aliases", "protocols"}
        )
        pending.extend(
            (child, nested)
            for child in reversed(list(iter_child_nodes(node=node)))
        )
    for item in tuple(found):
        if item.kind not in {"type_aliases", "protocols"}:
            continue
        symbol: Symbol | None = tree.semantic.resolve(
            name=item.key.split(sep=".")[-1],
            scope=declarations[item.key],
        )
        references: int | None = (
            len(tree.semantic.symbols.references(symbol_id=symbol.id))
            if symbol is not None
            else None
        )
        found.append(
            Artifact(
                kind="declaration_uses",
                key=item.key,
                line=item.line,
                content=f"{references} resolved AST read references. "
                "Dynamic access and string forward references are "
                "not counted.",
                shape=str(object=references),
            ),
        )
    return found


def _doc_fields(*, document: DocstringNode | None) -> DictStr:
    """Read comparison evidence from structured documentation nodes.

    Args:
        document (DocstringNode | None): Existing docstring tree, when
            available.

    Returns:
        DictStr: Summary, prose and named section-entry contracts.

    """
    if document is None:
        return {}
    fields: DictStr = {
        "summary": document.summary,
        "description": document.description,
    }
    for section in document.sections:
        for index, entry in enumerate(iterable=section.entries):
            key: str = f"{section.kind}.{entry.name or index}"
            fields[key] = repr((entry.type_name, entry.description))
    return fields


def _doc_explanation(*, expected: Artifact, actual: Artifact) -> str:
    """Describe field-level differences without interpreting prose meaning.

    Args:
        expected (Artifact): Curated structured fields.
        actual (Artifact): Generated structured fields.

    Returns:
        str: Missing, additional and changed field evidence.

    """
    missing: list[str] = sorted(expected.fields.keys() - actual.fields.keys())
    extra: list[str] = sorted(actual.fields.keys() - expected.fields.keys())
    changed: list[str] = sorted(
        key
        for key in expected.fields.keys() & actual.fields.keys()
        if expected.fields[key] != actual.fields[key]
    )
    return (
        f"Missing fields: {', '.join(missing) or 'none'}. "
        f"Additional fields: {', '.join(extra) or 'none'}. "
        f"Changed fields: {', '.join(changed) or 'none'}. "
        "Types and description text are compared structurally; "
        "prose meaning and inference causes are not assessed."
    )


def compare_artifacts(
    *,
    typed: str,
    converted: str,
    untyped: str | None = None,
    session: ComparisonSession | None = None,
) -> list[Difference]:
    """Compare current source artifacts without using saved graph verdicts.

    Args:
        typed (str): Curated reference source.
        converted (str): Actual tool output.
        untyped (str | None): Input baseline for candidate synthesized-class
            provenance.
        session (ComparisonSession | None): Shared comparison trees.

    Returns:
        list[Difference]: Aligned evidence, including additional generated
            declarations.

    """
    expected: list[Artifact] = artifacts(
        source=typed,
        tree=session.reference.tree if session else None,
    )
    remaining: list[Artifact] = artifacts(
        source=converted,
        tree=session.output.tree if session else None,
    )
    result: list[Difference] = []
    for reference in expected:
        actual: Artifact | None = next(
            (
                item
                for item in remaining
                if (item.kind, item.key) == (reference.kind, reference.key)
            ),
            None,
        )
        verdict: str = "missing"
        explanation: str = "No generated artifact has this qualified identity."
        if actual is None and reference.kind in {
            "type_aliases",
            "protocols",
            "classes",
        }:
            candidates: list[Artifact] = [
                item
                for item in remaining
                if item.kind == reference.kind
                and item.shape == reference.shape
            ]
            if len(candidates) == 1:
                actual = candidates[0]
                verdict = "equivalent"
                explanation = (
                    "Same declaration structure under a different name; "
                    "reference-use coverage and semantic equivalence "
                    "are not proven."
                )
        elif actual is not None:
            verdict = "exact" if actual.shape == reference.shape else "changed"
            if (
                reference.kind == "type_aliases"
                and verdict == "exact"
                and actual.content != reference.content
            ):
                verdict = "equivalent"
            explanation = (
                (
                    "Normalized documentation text matches; prose meaning "
                    "is not assessed."
                )
                if reference.kind == "docstrings" and verdict == "exact"
                else "Compare the expected and produced contracts below; "
                "this comparison does not establish inference causes."
            )
        if (
            actual is not None
            and reference.kind == "docstrings"
            and verdict == "changed"
        ):
            explanation = _doc_explanation(expected=reference, actual=actual)
        if actual is not None:
            remaining.remove(actual)
        result.append(
            Difference(
                kind=reference.kind,
                key=reference.key,
                verdict=verdict,
                expected=reference,
                actual=actual,
                explanation=explanation,
            ),
        )
    result.extend(
        Difference(
            kind=item.kind,
            key=item.key,
            verdict="extra",
            expected=None,
            actual=item,
            explanation="Generated artifact absent from the reference.",
        )
        for item in remaining
    )
    return _class_origins(
        differences=result,
        untyped=untyped,
        tree=session.input.tree if session else None,
    )


def _class_origins(
    *,
    differences: list[Difference],
    untyped: str | None,
    tree: CommentedModule | None = None,
) -> list[Difference]:
    """Label output-only classes using an explicit input baseline.

    Args:
        differences (list[Difference]): Current-run comparisons.
        untyped (str | None): Input source, or unknown provenance when absent.
        tree (CommentedModule | None): Shared parsed input module.

    Returns:
        list[Difference]: Class evidence with bounded synthesis-origin claims.

    """
    baseline: set[str] | None = (
        {
            item.key
            for item in artifacts(source=untyped, tree=tree)
            if item.kind in {"classes", "protocols"}
        }
        if untyped is not None
        else None
    )
    result: list[Difference] = []
    for item in differences:
        if item.kind not in {"classes", "protocols"} or item.actual is None:
            result.append(item)
            continue
        origin: str = (
            "unknown"
            if baseline is None
            else "input"
            if item.actual.key in baseline
            else "output_only"
        )
        actual: Artifact = replace(
            item.actual,
            fields={**item.actual.fields, "origin": origin},
        )
        result.append(
            replace(
                item,
                actual=actual,
                explanation=item.explanation
                + (
                    " Output-only class: candidate synthesized declaration; "
                    "source absence alone does not prove its creation history."
                    if origin == "output_only"
                    else ""
                ),
            ),
        )
    return result


class _ArtifactJson(TypedDict):
    """JSON shape of one serialized artifact.

    Attributes:
        kind (str): Artifact category, such as ``"docstrings"``.
        key (str): Stable identifier within the category.
        line (int): Source line of the artifact.
        content (str): Serialized artifact text.
        shape (str): Canonical structure dump used for comparison.
        fields (DictStr): Named documentation fields extracted from the
            content.

    """

    kind: str
    key: str
    line: int
    content: str
    shape: str
    fields: DictStr


class _DifferenceJson(TypedDict):
    """JSON shape of one serialized difference.

    Attributes:
        kind (str): Artifact category of the compared record.
        key (str): Stable identifier within the category.
        verdict (str): Comparison outcome, one of ``exact``, ``equivalent``,
            ``changed``, ``missing``, or ``extra``.
        expected (_ArtifactJson | None): Reference-side artifact, when present.
        actual (_ArtifactJson | None): Output-side artifact, when present.
        explanation (str): Human-readable reason for the verdict.

    """

    kind: str
    key: str
    verdict: str
    expected: _ArtifactJson | None
    actual: _ArtifactJson | None
    explanation: str


class StructureJson(TypedDict):
    """JSON payload returned by ``structure_json``.

    Attributes:
        schema_version (int): Payload layout version.
        categories (dict[str, dict[str, int]]): Per-category verdict counts.
        items (list[_DifferenceJson]): Serialized difference records.

    """

    schema_version: int
    categories: dict[str, dict[str, int]]
    items: list[_DifferenceJson]


def structure_json(*, differences: list[Difference]) -> StructureJson:
    """Serialize artifact evidence and per-category counts.

    Args:
        differences (list[Difference]): Current-run comparison.

    Returns:
        StructureJson:
            Versioned comparison data independent of annotation metrics.

    """
    categories: dict[str, dict[str, int]] = {
        kind: dict.fromkeys(
            ("exact", "equivalent", "changed", "missing", "extra"),
            0,
        )
        for kind in Constants.categories
    }
    for item in differences:
        counts: dict[str, int] = categories.setdefault(item.kind, {})
        counts[item.verdict] = counts.get(item.verdict, 0) + 1
    return {
        "schema_version": 2,
        "categories": categories,
        "items": [
            cast(typ="_DifferenceJson", val=asdict(obj=item))
            for item in differences
        ],
    }


def structure_markdown(
    *,
    differences: list[Difference],
    typed_link: str,
    converted_link: str,
    include_details: bool = True,
) -> list[str]:
    """Render separated, collapsible evidence for non-annotation contracts.

    Args:
        differences (list[Difference]): Current-run evidence.
        typed_link (str): Relative curated-source link.
        converted_link (str): Relative generated-source link.
        include_details (bool): Include full evidence after the summary.

    Returns:
        list[str]: Markdown lines, with full evidence available in JSON.

    """
    lines: list[str] = [
        "## Documentation and generated declarations",
        "",
        "These counts are separate from annotation accuracy. Documentation "
        "uses normalized text; declarations use AST structure. "
        "Changed prose does not prove incorrect behavior. Renamed structural "
        "matches do not prove that all references use the declaration.",
        "",
        (
            "| Category | Exact | Equivalent structure | Changed | Missing "
            "| Extra |"
        ),
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for kind in Constants.categories:
        counts: Counter[str] = Counter(
            item.verdict for item in differences if item.kind == kind
        )
        values: str = " | ".join(
            str(object=counts[key])
            for key in (
                "exact",
                "equivalent",
                "changed",
                "missing",
                "extra",
            )
        )
        lines.append(f"| {Constants.labels[kind]} | {values} |")
    lines.extend(
        (
            "",
            "Full contracts and source locations are retained in "
            "`conversion-report.json` under `artifacts`.",
            "",
        ),
    )
    if not include_details:
        return lines
    for kind in Constants.categories:
        gaps: list[Difference] = [
            item
            for item in differences
            if item.kind == kind and item.verdict != "exact"
        ]
        lines.extend((f"### {Constants.labels[kind]}", ""))
        for item in gaps:
            lines.extend(
                (
                    f"<details><summary>{item.key} — {item.verdict}</summary>",
                    "",
                    item.explanation,
                    "",
                ),
            )
            for label, evidence, target in (
                ("Reference", item.expected, typed_link),
                ("Produced", item.actual, converted_link),
            ):
                if evidence is not None:
                    lines.extend(
                        (
                            (
                                f"**[{label}: {evidence.key}]({target}#L"
                                f"{evidence.line})**"
                            ),
                            "",
                            "````python",
                            evidence.content[: Constants.preview_limit],
                            "````",
                            "",
                        ),
                    )
                    if len(evidence.content) > Constants.preview_limit:
                        lines.extend(
                            (
                                "Preview truncated; full content is in JSON.",
                                "",
                            ),
                        )
            lines.extend(("</details>", ""))
    return lines
