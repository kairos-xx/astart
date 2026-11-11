"""Convert an untyped module with astart and report how it differs, in meaning.

Usage (from the repository root)::

    python scripts/compare
    python scripts/compare --min-confidence 0.5         --ledger "after G-02"
    python scripts/compare --checker --no-opacity

Runs ``astart fix`` in conversion mode on ``fixtures/untyped.py`` in memory
(the file is never modified), compares every annotation of the result with
``fixtures/typed.py`` by meaning, not by text, and writes:

* ``scripts/compare/artifacts/results/conversion-report.md``   the full report,
* ``scripts/compare/artifacts/results/conversion-report.json``
  the same data for tools,
* the ``conversion`` block of ``docs/planning/TODO.md`` (summary and gap
  by family).

The default reference graph,
``fixtures/artifacts/typed_graph.json``, supplies
declared annotations and contextual source evidence. Saved comparison verdicts
in the graph are never substituted for scoring the current conversion.

"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    BinOp,
    Call,
    ClassDef,
    Constant,
    Expression,
    FunctionDef,
    Module,
    Name,
    TypeAlias,
    arg,
    expr,
    parse,
    walk,
)
from collections import Counter
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from hashlib import sha256
from importlib import import_module
from json import dumps, loads
from os.path import relpath
from pathlib import Path
from subprocess import run
from sys import executable, path, stdout
from time import perf_counter
from typing import TYPE_CHECKING, Final, Protocol, TypedDict, cast, final

from scripts.compare.session import ComparisonSession

type ListStr = list[str]
type DictInt = dict[str, int]
type DictStr = dict[str, str]
type DictDictInt = dict[str, DictInt]

if TYPE_CHECKING:
    from collections.abc import Iterable
    from subprocess import CompletedProcess
    from types import ModuleType

    from astart import CommentedModule
    from astart.rules.checker import Checker
    from astart.rules.recovery import Context
    from astart.rules.registry import Registries

    from scripts.compare.conversion_structure import Difference, StructureJson
    from scripts.compare.evidence import Evidence, Index
    from scripts.compare.opacity_report import Row, Section


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root (Final[Path]): Repository root.
        scopes (Final[tuple[tuple[str, str], ...]]): Result scope key and its
            label.
        verdicts (Final[tuple[str, ...]]): Outcome names in display order.
        compatible (Final[frozenset[str]]): Outcomes with an equal or
            assignable type.
        gap (Final[frozenset[str]]): Outcomes that count as the remaining gap.
        scalars (Final[frozenset[str]]): Scalar type names.
        containers (Final[frozenset[str]]): Builtin container names.
        iterators (Final[frozenset[str]]): Generator and iterator names.
        abstract (Final[frozenset[str]]): Abstract collection names.
        typevar_makers (Final[frozenset[str]]): Calls that create type
            variables.
        families (Final[tuple[str, ...]]): Annotation families in display
            order.
        hard (Final[frozenset[str]]): Families that are partly author choices.
        tasks (Final[dict[str, str]]): TODO tasks that close the gap of each
            family.
        bar_width (Final[int]): Width of a bar in characters.
        owner_rows (Final[int]): Owners listed in the report.
        list_limit (Final[int]): Missing keys listed per family in the full
            report.
        opacity_lines (Final[int]): Lines of the opacity report embedded in the
            report.
        max_typevar_len (Final[int]): Longest uppercase name treated as an
            inline TypeVar.
        wrong_listed (Final[int]): Wrong annotations listed in the TODO block.
        snippet_len (Final[int]): Characters of a source line kept in a diff
            snippet.

    """

    root: Final[Path] = Path(__file__).resolve().parents[2]
    scopes: Final[tuple[tuple[str, str], ...]] = (
        ("parameters_and_returns", "Parameters and returns"),
        ("variables", "Variables"),
    )
    verdicts: Final[tuple[str, ...]] = (
        "exact",
        "narrower",
        "looser",
        "compatible",
        "unresolved",
        "wrong",
        "missing",
        "reference_only",
    )
    compatible: Final[frozenset[str]] = frozenset(
        {"narrower", "looser", "compatible"},
    )
    gap: Final[frozenset[str]] = frozenset({"missing", "wrong", "unresolved"})
    scalars: Final[frozenset[str]] = frozenset(
        {"int", "str", "float", "bool", "bytes", "complex"},
    )
    containers: Final[frozenset[str]] = frozenset(
        {"list", "dict", "set", "tuple", "frozenset"},
    )
    iterators: Final[frozenset[str]] = frozenset(
        {
            "Generator",
            "AsyncGenerator",
            "Iterator",
            "AsyncIterator",
            "Iterable",
            "AsyncIterable",
        },
    )
    abstract: Final[frozenset[str]] = frozenset(
        {
            "Sequence",
            "Mapping",
            "MutableMapping",
            "MutableSequence",
            "MutableSet",
            "AbstractSet",
            "Collection",
            "Set",
        },
    )
    typevar_makers: Final[frozenset[str]] = frozenset(
        {"TypeVar", "ParamSpec", "TypeVarTuple"},
    )
    families: Final[tuple[str, ...]] = (
        "Scalar",
        "Builtin container",
        "Optional",
        "Union",
        "Module class",
        "Library class",
        "Type alias",
        "Abstract collection",
        "Generator/Iterator",
        "Callable",
        "TypeVar",
        "Self",
        "ClassVar/Final",
        "Top type (object)",
        "Other",
    )
    hard: Final[frozenset[str]] = frozenset(
        {
            "Abstract collection",
            "Generator/Iterator",
            "Callable",
            "TypeVar",
            "Self",
            "ClassVar/Final",
            "Top type (object)",
            "Type alias",
        },
    )
    tasks: Final[dict[str, str]] = {
        "Scalar": "W-06, W-08, I-10, F-37",
        "Builtin container": "I-05, I-09, I-17, F-40, AL-07",
        "Optional": "I-01, I-08, AL-01",
        "Union": "AL-05, I-19",
        "Module class": "M2-02, W-12, I-11, W-14",
        "Library class": "I-21, I-08, T-08",
        "Type alias": "S-03, AL-14 (author-defined names)",
        "Abstract collection": "M4-16, AL-13, G-02",
        "Generator/Iterator": "W-13, G-05",
        "Callable": "M4-17, M5-19",
        "TypeVar": "M5-16, I-18, M5-19",
        "Self": "W-11, AF-02, F-43",
        "ClassVar/Final": "AF-05, G-06",
        "Top type (object)": (
            "policy: astart never writes object; G-02 scores narrower"
        ),
        "Other": "G-04",
    }
    bar_width: Final[int] = 20
    owner_rows: Final[int] = 15
    list_limit: Final[int] = 30
    opacity_lines: Final[int] = 60
    max_typevar_len: Final[int] = 2
    wrong_listed: Final[int] = 10
    snippet_len: Final[int] = 200


@final
@dataclass(frozen=True, slots=True)
class Item:
    """One annotation of the typed file and what happened to it.

    Attributes:
        scope (str): ``parameters_and_returns`` or ``variables``.
        key (str): Node path such as ``Class.method.param`` or ``function->``.
        verdict (str): Outcome name.
        written (str | None): What astart wrote, or ``None`` when nothing was
            written.
        author (str): What the typed file has.
        family (str): Shape of the author's annotation.
        typed_line (int | None): Line of the annotation in the typed file.
        converted_line (int | None): Line of the node in the converted output.
        untyped_line (int | None): Line of the node in the untyped input.

    """

    scope: str
    key: str
    verdict: str
    written: str | None
    author: str
    family: str
    typed_line: int | None = None
    converted_line: int | None = None
    untyped_line: int | None = None


class _Structure(Protocol):
    """Source artifact comparison supplied by the reporting module."""

    def compare_artifacts(
        self,
        *,
        typed: str,
        converted: str,
        untyped: str | None = None,
        session: ComparisonSession | None = None,
    ) -> list[Difference]:
        """Compare current documentation and declarations.

        Args:
            typed (str): Curated reference source.
            converted (str): Actual tool output.
            untyped (str | None): Input baseline for candidate
                synthesized-class provenance.
            session (ComparisonSession | None): Shared comparison trees.

        Returns:
            Aligned evidence, including additional generated declarations.

        """
        ...

    def structure_json(
        self,
        *,
        differences: list[Difference],
    ) -> StructureJson:
        """Serialize complete artifact evidence.

        Args:
            differences (list[Difference]): Current-run comparison.

        Returns:
            Versioned comparison data independent of annotation metrics.

        """
        ...

    def structure_markdown(
        self,
        *,
        differences: list[Difference],
        typed_link: str,
        converted_link: str,
        include_details: bool = True,
    ) -> ListStr:
        """Render separated source-backed artifact evidence.

        Args:
            differences (list[Difference]): Current-run evidence.
            typed_link (str): Relative curated-source link.
            converted_link (str): Relative generated-source link.
            include_details (bool): Include full evidence after the summary.

        Returns:
            Markdown lines, with full evidence available in JSON.

        """
        ...


def bar(*, value: int, total: int) -> str:
    """Draw a progress bar.

    Args:
        value (int): Amount done.
        total (int): Amount that means 100 %.

    Returns:
        str: A bar of ``Constants.bar_width`` characters.

    """
    width: int = Constants.bar_width
    if total <= 0:
        return "░" * width
    filled: int = max(0, min(width, round(number=width * value / total)))
    return "█" * filled + "░" * (width - filled)


def percent(*, value: int, total: int) -> str:
    """Format a share as a percentage.

    Args:
        value (int): Part.
        total (int): Whole.

    Returns:
        str: For example ``"45.9 %"``.

    """
    return "n/a" if total <= 0 else f"{100 * value / total:.1f} %"


class _Digest(Protocol):
    """The slice of a hash object ``tree_hash`` uses."""

    def update(self, data: bytes, /) -> None:
        """Add bytes to the hash.

        Args:
            data (bytes): Bytes to add.

        """
        ...

    def hexdigest(self) -> str:
        """Render the hash as hexadecimal text.

        Returns:
            The lowercase hex digest.

        """
        ...


def tree_hash(*, root: Path) -> str:
    """Hash the astart source tree, to stamp the report.

    Args:
        root (Path): Repository root.

    Returns:
        str: The first 12 hex digits of a SHA-256 over all source files.

    """
    digest: _Digest = sha256()
    for file in sorted((root / "src" / "astart").rglob(pattern="*.py")):
        if "__pycache__" in file.parts:
            continue
        digest.update(file.relative_to(root).as_posix().encode())
        digest.update(file.read_bytes())
    return digest.hexdigest()[:12]


def module_names(
    *,
    source: str,
    tree: Module | None = None,
) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
    """Collect class, type-variable and type-alias names of the typed module.

    Args:
        source (str): Source of the typed module.
        tree (Module | None): Shared module, when supplied.

    Returns:
        tuple[frozenset[str], frozenset[str], frozenset[str]]: The class names,
            the type-variable names and the type-alias names.

    """
    classes: set[str] = set()
    typevars: set[str] = set()
    aliases: set[str] = set()
    for node in walk(node=(parse(source=source) if tree is None else tree)):
        if isinstance(node, ClassDef):
            classes.add(node.name)
        if isinstance(node, TypeAlias):
            aliases.add(node.name.id)
        if isinstance(node, Assign) and isinstance(node.value, Call):
            func: expr = node.value.func
            if isinstance(func, Name) and func.id in Constants.typevar_makers:
                typevars.update(
                    target.id
                    for target in node.targets
                    if isinstance(target, Name)
                )
        typevars.update(
            param.name for param in getattr(node, "type_params", ())
        )
    return frozenset(classes), frozenset(typevars), frozenset(aliases)


def family_of(
    *,
    text: str,
    classes: frozenset[str],
    typevars: frozenset[str],
    aliases: frozenset[str],
) -> str:
    """Classify an annotation by its shape.

    Args:
        text (str): Annotation source.
        classes (frozenset[str]): Class names defined in the typed module.
        typevars (frozenset[str]): Type-variable names defined in the typed
            module.
        aliases (frozenset[str]): Type-alias names defined in the typed module.

    Returns:
        str: One of ``Constants.families``.

    """
    try:
        tree: Expression = parse(source=text, mode="eval")
    except SyntaxError:
        return "Other"
    if isinstance(tree.body, Constant) and tree.body.value is None:
        return "Scalar"
    names: set[str] = set()
    has_union: bool = False
    has_none: bool = False
    for node in walk(node=tree):
        if isinstance(node, Name):
            names.add(node.id)
        elif isinstance(node, Attribute):
            names.add(node.attr)
        elif isinstance(node, BinOp):
            has_union = True
            has_none = has_none or any(
                isinstance(side, Constant) and side.value is None
                for side in (node.left, node.right)
            )
    short_upper: bool = any(
        len(n) <= Constants.max_typevar_len and n.isupper() for n in names
    )
    known: set[str] = (
        set(Constants.scalars)
        | set(Constants.containers)
        | classes
        | aliases
        | typevars
        | {"None", "type", "object", "Any"}
    )
    ordered: tuple[tuple[str, bool], ...] = (
        ("Self", "Self" in names),
        ("ClassVar/Final", bool(names & {"ClassVar", "Final"})),
        ("Callable", "Callable" in names),
        ("Generator/Iterator", bool(names & Constants.iterators)),
        ("Abstract collection", bool(names & Constants.abstract)),
        (
            "TypeVar",
            bool(names & typevars)
            or short_upper
            or bool(names & {"args", "kwargs"}),
        ),
        ("Top type (object)", bool(names & {"object", "Any"})),
        ("Optional", has_none or "Optional" in names),
        ("Union", has_union or "Union" in names),
        ("Type alias", bool(names & aliases)),
        ("Module class", bool(names & classes)),
        ("Library class", bool(names - known)),
        ("Builtin container", bool(names & Constants.containers)),
        ("Scalar", bool(names & Constants.scalars)),
    )
    for family, matched in ordered:
        if matched:
            return family
    return "Other"


class _Recovery(Protocol):
    """The slice of ``astart.rules.recovery`` the comparison calls."""

    def annotation_map(
        self,
        *,
        source: str,
        tree: Module | None = None,
    ) -> DictStr:
        """Map annotation keys to their source text.

        Args:
            source (str): Module source.
            tree (Module | None): Shared parsed module, when available.

        Returns:
            Annotation key to annotation text.

        """
        ...

    def variable_map(
        self,
        *,
        source: str,
        tree: Module | None = None,
    ) -> DictStr:
        """Map variable keys to their annotation text.

        Args:
            source (str): Module source.
            tree (Module | None): Shared parsed module, when available.

        Returns:
            Variable key to annotation text.

        """
        ...

    def module_context(
        self,
        *,
        source: str,
        tree: Module | None = None,
    ) -> Context:
        """Collect the aliases and classes a module defines.

        Args:
            source (str): Module source.
            tree (Module | None): Shared parsed module, when available.

        Returns:
            Its: class:`Context`.

        """
        ...

    def normalize_annotation(self, *, text: str) -> str:
        """Reduce an annotation to a canonical form.

        Args:
            text (str): Annotation source.

        Returns:
            The canonical text.

        """
        ...

    def relation(
        self,
        *,
        written: str,
        truth: str,
        context: Context | None = None,
    ) -> str | None:
        """Say how a written annotation relates to the original one.

        Args:
            written (str): What the fixer wrote.
            truth (str): The original annotation.
            context (Context | None): Aliases and classes of the original
                module.

        Returns:
            The relation name, or ``None`` when they mean the same.

        """
        ...


class _ReferenceTarget(TypedDict):
    """An authored annotation and its explicitly scoped evidence links.

    Attributes:
        id (str): Stable annotation target identity.
        path (str): Qualified annotation path, including overload
            discriminator.
        annotation_source (str): Exact authored annotation text.
        expected_type_id (str): Normalized type record in the source graph.
        evidence_ids (ListStr): Evidence for the declared contract.
        supporting_evidence_ids (ListStr): Lexical source observations.
        supporting_evidence_role (str): Limits on interpreting contextual
            facts.
        constraint_ids (ListStr): Related constraints in the source graph.

    """

    id: str
    path: str
    annotation_source: str
    expected_type_id: str
    evidence_ids: ListStr
    supporting_evidence_ids: ListStr
    supporting_evidence_role: str
    constraint_ids: ListStr


class _ReferenceEvidence(TypedDict):
    """One source observation, with its trust and source location.

    Attributes:
        id (str): Stable evidence identity.
        expression (str): Source expression producing the observation.
        explanation (str): Interpretation of the observed syntax.
        kind (str): Declared annotation or source operation category.
        soundness (str): Qualification on the observation's validity.
        source_span (dict[str, int | None]): Source line and column boundaries.

    """

    id: str
    expression: str
    explanation: str
    kind: str
    soundness: str
    source_span: dict[str, int | None]


class _ReferenceType(TypedDict):
    """Normalized contract information used in human explanations.

    Attributes:
        kind (str): Type category such as UNION, CALLABLE or PROTOCOL.
        display (str): Normalized spelling of the type.
        qualified_name (str | None): Resolved name, where available.
        argument_type_ids (ListStr): Generic arguments in declaration order.
        union_member_type_ids (ListStr): Alternatives accepted by a union.
        declaration_id (str | None): Owning class or protocol declaration.

    """

    kind: str
    display: str
    qualified_name: str | None
    argument_type_ids: ListStr
    union_member_type_ids: ListStr
    declaration_id: str | None


class _ReferenceRequirement(TypedDict):
    """A declared protocol member or observed structural requirement.

    Attributes:
        subject_type_id (str): Receiver type constrained by the member.
        member_name (str): Required member name.
        status (str): DECLARED for authored protocol members.

    """

    subject_type_id: str
    member_name: str
    status: str


class _ReferenceDocument(TypedDict):
    """The graph tables consumed by the conversion report.

    Attributes:
        schema_version (str): Semantic graph schema version.
        revision (DictStr): Authored source digest and revision identity.
        annotation_targets (dict[str, _ReferenceTarget]): Every explicit
            annotation source site.
        evidence (dict[str, _ReferenceEvidence]): Source observations indexed
            by stable identity.
        type_expressions (dict[str, _ReferenceType]): Normalized reference
            contracts.
        protocol_requirements (dict[str, _ReferenceRequirement]): Declared and
            observed member requirements.

    """

    schema_version: str
    revision: DictStr
    annotation_targets: dict[str, _ReferenceTarget]
    evidence: dict[str, _ReferenceEvidence]
    type_expressions: dict[str, _ReferenceType]
    protocol_requirements: dict[str, _ReferenceRequirement]


@final
@dataclass(frozen=True, slots=True)
class ReferenceGraph:
    """Validated reference annotations, independent of saved tool output.

    Attributes:
        path (Path): Semantic graph location.
        document (_ReferenceDocument): Graph records used for explanation.

    """

    path: Path
    document: _ReferenceDocument

    def targets(self, *, key: str) -> list[_ReferenceTarget]:
        """Find all source sites, including overloads, at a scored path.

        Args:
            key (str): Scorer's qualified annotation path.

        Returns:
            list[_ReferenceTarget]: Matching authored annotation records.

        """
        return [
            target
            for target in self.document["annotation_targets"].values()
            if target["path"].split(sep="#overload:", maxsplit=1)[0] == key
        ]

    def facts(self, *, key: str) -> list[_ReferenceEvidence]:
        """Resolve declared and contextual observations without duplication.

        Args:
            key (str): Scorer's qualified annotation path.

        Returns:
            list[_ReferenceEvidence]: Source evidence; lexical context is not
                an assignability proof.

        """
        ids: dict[str, None] = dict.fromkeys(
            evidence_id
            for target in self.targets(key=key)
            for evidence_id in (
                *target["evidence_ids"],
                *target["supporting_evidence_ids"],
            )
        )
        return [self.document["evidence"][key] for key in ids]


def contract_meaning(*, graph: ReferenceGraph, type_id: str) -> str:
    """Translate a graph type into the capability or relation it preserves.

    Args:
        graph (ReferenceGraph): Authored contracts and declared protocol
            requirements.
        type_id (str): Normalized type identity.

    Returns:
        str: An explanation of this contract,
            without claiming an inference proof.

    """
    types: dict[str, _ReferenceType] = graph.document["type_expressions"]
    contract: _ReferenceType = types[type_id]
    name: str = (contract["qualified_name"] or "").rpartition(".")[2]
    arguments: ListStr = [
        types[key]["display"] for key in contract["argument_type_ids"]
    ]
    shown: str = ", ".join(arguments)
    meaning: str = "The authored contract selects this type."
    if contract["kind"] == "PROTOCOL":
        members: ListStr = sorted(
            {
                requirement["member_name"]
                for requirement in graph.document[
                    "protocol_requirements"
                ].values()
                if requirement["status"] == "DECLARED"
                and types[requirement["subject_type_id"]]["declaration_id"]
                == contract["declaration_id"]
            },
        )
        meaning = (
            "Requires the declared protocol members "
            + ", ".join(f"`{member}`" for member in members)
            + ". Matching an unrelated method name does not establish "
            "these structural requirements."
        )
    elif contract["kind"] == "CALLABLE":
        meaning = (
            f"Preserves the callable's parameter/result relation ({shown}). "
            "A bare Callable omits that relationship."
        )
    elif contract["kind"] in {"TYPEVAR", "PARAMSPEC", "TYPEVARTUPLE"}:
        meaning = (
            "Preserves a shared generic parameter across the signature; "
            "a concrete example type does not preserve that relationship."
        )
    elif name in {"Sequence", "MutableSequence"}:
        meaning = (
            f"Requires sequence access with element type `{shown}`. "
            "Iteration alone establishes less; an example list is one "
            "implementation, not the entire accepted input contract."
        )
    elif name in {"Mapping", "MutableMapping", "dict"}:
        meaning = (
            f"Preserves key/value types ({shown}). Mapping operations and "
            "the types flowing through keys and values must agree."
        )
    elif name in {"Iterable", "Iterator", "Generator"}:
        meaning = (
            f"Preserves iteration/yield types ({shown}); iteration does "
            "not by itself establish sequence indexing."
        )
    elif contract["kind"] == "SELF":
        meaning = "Preserves the receiver's concrete subclass in the result."
    return meaning


def contract_parts(*, item: Item, graph: ReferenceGraph) -> ListStr:
    """Explain normalized union arms and generic relations from the graph.

    Args:
        item (Item): Scored annotation path.
        graph (ReferenceGraph): Validated authored reference.

    Returns:
        ListStr:
            Concise contract requirements for the selected annotation site.

    """
    targets: list[_ReferenceTarget] = graph.targets(key=item.key)
    if not targets:
        return []
    expected: str = targets[-1]["expected_type_id"]
    contract: _ReferenceType = graph.document["type_expressions"][expected]
    parts: ListStr = contract["union_member_type_ids"] or [expected]
    return [
        "- `"
        + plain(text=graph.document["type_expressions"][key]["display"])
        + "`: "
        + contract_meaning(graph=graph, type_id=key)
        for key in parts
    ]


def load_reference(*, path: Path, source: str) -> ReferenceGraph:
    """Load the annotation reference and reject stale or broken evidence.

    Args:
        path (Path): Version-four semantic graph.
        source (str): Exact authored source being scored.

    Returns:
        ReferenceGraph:
            The reference with verified source identity and evidence links.

    Raises:
        ValueError: The schema, source digest or evidence links disagree.

    """
    document: _ReferenceDocument = cast(
        typ="_ReferenceDocument",
        val=loads(s=path.read_text(encoding="utf-8")),
    )
    if document["schema_version"] != "4.0.0":
        msg: str = "Expected semantic graph schema 4.0.0"
        raise ValueError(msg)
    if (
        document["revision"]["source_digest"]
        != sha256(
            string=source.encode(encoding="utf-8"),
        ).hexdigest()
    ):
        msg = "Reference graph is stale for the selected typed source"
        raise ValueError(msg)
    for target in document["annotation_targets"].values():
        for evidence_id in (
            *target["evidence_ids"],
            *target["supporting_evidence_ids"],
        ):
            if evidence_id not in document["evidence"]:
                msg = f"Unresolved reference evidence: {evidence_id}"
                raise ValueError(msg)
    return ReferenceGraph(path=path, document=document)


def selected_reference(
    *,
    namespace: Namespace,
    source: str,
) -> ReferenceGraph | None:
    """Select the default fixture graph or an explicitly requested graph.

    Args:
        namespace (Namespace): CLI paths, including an optional reference
            graph.
        source (str): Authored source whose digest must match.

    Returns:
        ReferenceGraph | None:
            Validated evidence, or no graph for a custom typed reference.

    """
    graph_path: Path | None = namespace.reference_graph
    if graph_path is None and namespace.typed.resolve() == (
        Constants.root / "fixtures" / "typed.py"
    ):
        graph_path = (
            Constants.root / "fixtures" / "artifacts" / "typed_graph.json"
        )
    return (
        load_reference(path=graph_path, source=source)
        if graph_path is not None
        else None
    )


@final
@dataclass(frozen=True, slots=True)
class Sources:
    """Source lines, line maps and link targets, for snippets and links.

    Attributes:
        untyped (ListStr): Lines of the untyped input.
        typed (ListStr): Lines of the typed answer key.
        converted (ListStr): Lines of the converted output.
        links (DictStr): Link target per source (``untyped``, ``typed`` ,
            ``converted``).
        untyped_params (DictInt): Lines of the input's parameters and returns.
        untyped_vars (DictInt): Lines of the input's variables.
        anchors (DictStr): TODO entry anchor by task ID.
        evidence (Index | None): Evidence index of the untyped module.
        reasons (dict[str, tuple[str, str]]): Opacity reason and evidence by
            node path.
        reference (ReferenceGraph | None): Authored annotation graph, when
            selected.

    """

    untyped: ListStr
    typed: ListStr
    converted: ListStr
    links: DictStr
    untyped_params: DictInt
    untyped_vars: DictInt
    anchors: DictStr
    evidence: Index | None
    reasons: dict[str, tuple[str, str]]
    reference: ReferenceGraph | None = None


@final
@dataclass(frozen=True, slots=True)
class Extras:
    """Optional report content beyond the scored items.

    Attributes:
        sections (list[Section]): Opacity sections (may be empty).
        sources (Sources): Source lines, line maps and link targets.
        examples (int): Code examples shown per family of missing annotations.

    """

    sections: list[Section]
    sources: Sources
    examples: int


def todo_anchors(*, todo: Path) -> DictStr:
    """Compute the GitHub anchor of every task heading of the TODO file.

    Args:
        todo (Path): Path of the TODO file.

    Returns:
        DictStr: Anchor by task ID; empty when the file does not exist.

    """
    if not todo.exists():
        return {}
    anchors: DictStr = {}
    seen: Counter[str] = Counter()
    fenced: bool = False
    for line in todo.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            fenced = not fenced
        if fenced or not line.startswith("#"):
            continue
        heading: str = line.lstrip("#").strip()
        base: str = "".join(
            char for char in heading.lower() if char.isalnum() or char in " -_"
        ).replace(" ", "-")
        anchor: str = base if seen[base] == 0 else f"{base}-{seen[base]}"
        seen[base] += 1
        if line.startswith("### ") and " — " in line:
            anchors.setdefault(heading.partition(" — ")[0], anchor)
    return anchors


def task_links(
    *,
    text: str,
    anchors: DictStr,
    target: str = "TODO.md",
) -> str:
    """Turn task IDs in a text into links to their TODO entries.

    Args:
        text (str): Text such as ``"W-06, W-08 (author names)"``.
        anchors (DictStr): Anchor by task ID.
        target (str): Relative path to the TODO document.

    Returns:
        str: The text with each known ID linked.

    """
    words: ListStr = []
    for word in text.split(sep=" "):
        core: str = word.strip(",;()")
        if core in anchors:
            words.append(
                word.replace(core, f"[{core}]({target}#{anchors[core]})"),
            )
        else:
            words.append(word)
    return " ".join(words)


def cell(*, text: str) -> str:
    """Make text safe inside a Markdown table cell.

    Args:
        text (str): Any text.

    Returns:
        str: The text with pipes escaped and backticks replaced.

    """
    return text.replace("|", "\\|").replace("`", "'")


def node_line(*, key: str, sources: Sources) -> int | None:
    """Find the line of a node in the untyped input.

    Args:
        key (str): Node path such as ``Class.method.param`` or ``function->``.
        sources (Sources): Source lines and line maps.

    Returns:
        int | None: The line number, or ``None``.

    """
    return sources.untyped_params.get(key) or sources.untyped_vars.get(key)


def _functions(
    *,
    node: AST,
    trail: tuple[str, ...],
    out: DictInt,
) -> None:
    """Record the line of every parameter and return, like the scorer's keys.

    Args:
        node (AST): Node whose body is scanned.
        trail (tuple[str, ...]): Qualified-name prefix.
        out (DictInt): Destination mapping, extended in place.

    """
    for child in getattr(node, "body", []):
        if isinstance(child, (FunctionDef, AsyncFunctionDef)):
            name: str = ".".join((*trail, child.name))
            out[f"{name}->"] = (child.returns or child).lineno
            for parameter in walk(node=child.args):
                if isinstance(parameter, arg):
                    out[f"{name}.{parameter.arg}"] = parameter.lineno
            _functions(node=child, trail=(*trail, child.name), out=out)
        elif isinstance(child, ClassDef):
            _functions(node=child, trail=(*trail, child.name), out=out)


def param_lines(*, source: str, tree: Module | None = None) -> DictInt:
    """Locate parameters and returns by the scorer's keys.

    Args:
        source (str): Python source.
        tree (Module | None): Shared module, when supplied.

    Returns:
        DictInt: Line number by ``function.parameter`` or ``function->`` ;
            a return without annotation points at its ``def`` line.

    """
    out: DictInt = {}
    _functions(
        node=(parse(source=source) if tree is None else tree),
        trail=(),
        out=out,
    )
    return out


def _variables(
    *,
    body: Iterable[AST],
    trail: tuple[str, ...],
    annotated: DictInt,
    plain: DictInt,
) -> None:
    """Record the line of every annotated or plainly assigned variable.

    Args:
        body (Iterable[AST]): Statements of one scope.
        trail (tuple[str, ...]): Qualified-name prefix.
        annotated (DictInt): Lines of annotated assignments (last one wins).
        plain (DictInt): Lines of the first plain assignment.

    """
    for node in body:
        if isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
            _variables(
                body=node.body,
                trail=(*trail, node.name),
                annotated=annotated,
                plain=plain,
            )
            continue
        if isinstance(node, AnnAssign) and isinstance(node.target, Name):
            annotated[".".join((*trail, node.target.id))] = node.lineno
        if isinstance(node, Assign):
            for target in node.targets:
                if isinstance(target, Name):
                    plain.setdefault(
                        ".".join((*trail, target.id)),
                        node.lineno,
                    )
        for branch in ("body", "orelse", "finalbody"):
            inner: list[AST] | None = cast(
                typ="list[AST] | None",
                val=getattr(node, branch, None),
            )
            if inner is not None:
                _variables(
                    body=inner,
                    trail=trail,
                    annotated=annotated,
                    plain=plain,
                )


def variable_lines(
    *,
    source: str,
    tree: Module | None = None,
) -> DictInt:
    """Locate variables by the scorer's keys.

    Args:
        source (str): Python source.
        tree (Module | None): Shared module, when supplied.

    Returns:
        DictInt: Line number by ``scope.name`` : the annotated statement
            when there is one, else the first plain assignment.

    """
    annotated: DictInt = {}
    plain: DictInt = {}
    _variables(
        body=list((parse(source=source) if tree is None else tree).body),
        trail=(),
        annotated=annotated,
        plain=plain,
    )
    return {**plain, **annotated}


def line_text(*, lines: ListStr, number: int | None) -> str | None:
    """Read one source line for a snippet.

    Args:
        lines (ListStr): Source lines.
        number (int | None): 1-based line number.

    Returns:
        str | None:
            The line without trailing blanks, shortened to 200 characters,
            with code-fence marks defused; ``None`` when the line is unknown.

    """
    if number is None or not 1 <= number <= len(lines):
        return None
    text: str = lines[number - 1].rstrip().replace("```", "'''")
    if len(text) <= Constants.snippet_len:
        return text
    return text[: Constants.snippet_len] + "…"


def link(*, label: str, target: str, number: int | None) -> str:
    """Build a Markdown link to a line.

    Args:
        label (str): File label.
        target (str): Relative path of the file.
        number (int | None): 1-based line number.

    Returns:
        str: ``[label:number](target#Lnumber)``, or ``n/a`` without a line.

    """
    if number is None:
        return "n/a"
    return f"[{label}:{number}]({target}#L{number})"


def snippet(*, item: Item, sources: Sources) -> ListStr:
    """Show an annotation as a diff: how it is against how it should be.

    Args:
        item (Item): A scored annotation.
        sources (Sources): Source lines and link targets.

    Returns:
        ListStr:
            Markdown lines: a line of links and a ``diff`` block whose ``-``
            line is the converted code and whose ``+`` line is the typed code.

    """
    how: str | None = line_text(
        lines=sources.converted,
        number=item.converted_line,
    )
    should: str | None = line_text(lines=sources.typed, number=item.typed_line)
    out_link: str = link(
        label="result.py",
        target=sources.links["converted"],
        number=item.converted_line,
    )
    typed_link: str = link(
        label=Path(sources.links["typed"]).name,
        target=sources.links["typed"],
        number=item.typed_line,
    )
    input_link: str = link(
        label="untyped.py",
        target=sources.links["untyped"],
        number=item.untyped_line,
    )
    lines: ListStr = [
        f"Output: {out_link} · Reference: {typed_link} · Input: {input_link}",
        "",
        "```diff",
        f"@@ {item.key} · {item.verdict} · {item.family} @@",
    ]
    if how is not None:
        lines.append(f"-{how}")
    if should is not None:
        lines.append(f"+{should}")
    lines.append("```")
    return lines


def _typed_link(*, item: Item, sources: Sources) -> str:
    """Link an item to its line in the typed file.

    Args:
        item (Item): Scored annotation.
        sources (Sources): Source lines and link targets.

    Returns:
        str: A Markdown link labelled with the typed file's name.

    """
    return link(
        label=Path(sources.links["typed"]).name,
        target=sources.links["typed"],
        number=item.typed_line,
    )


def compare(
    *,
    untyped: str,
    typed: str,
    converted: str,
    recovery: _Recovery,
    session: ComparisonSession | None = None,
) -> tuple[list[Item], DictInt]:
    """Score every annotation of the typed file against the converted module.

    Args:
        untyped (str): Source without annotations.
        typed (str): Source with the author's annotations.
        converted (str): What astart produced from the untyped source.
        recovery (_Recovery): The ``astart.rules.recovery`` module.
        session (ComparisonSession | None): Shared comparison trees, when
            supplied.

    Returns:
        tuple[list[Item], DictInt]: One item per annotation to recover, and the
            count of
            annotations written that the typed file does not have, by scope.

    """
    session = session or ComparisonSession.create(
        untyped=untyped,
        typed=typed,
        converted=converted,
    )
    truth: DictStr = recovery.annotation_map(
        source=typed,
        tree=session.reference.tree,
    )
    start: DictStr = recovery.annotation_map(
        source=untyped,
        tree=session.input.tree,
    )
    written: DictStr = recovery.annotation_map(
        source=converted,
        tree=session.output.tree,
    )
    truth_vars: DictStr = recovery.variable_map(
        source=typed,
        tree=session.reference.tree,
    )
    done_vars: DictStr = recovery.variable_map(
        source=converted,
        tree=session.output.tree,
    )
    context: Context = recovery.module_context(
        source=typed,
        tree=session.reference.tree,
    )
    classes, typevars, aliases = module_names(
        source=typed,
        tree=session.reference.tree,
    )
    typed_params: DictInt = param_lines(
        source=typed,
        tree=session.reference.tree,
    )
    converted_params: DictInt = param_lines(
        source=converted,
        tree=session.output.tree,
    )
    untyped_params: DictInt = param_lines(
        source=untyped,
        tree=session.input.tree,
    )
    typed_vars: DictInt = variable_lines(
        source=typed,
        tree=session.reference.tree,
    )
    converted_vars: DictInt = variable_lines(
        source=converted,
        tree=session.output.tree,
    )
    untyped_vars: DictInt = variable_lines(
        source=untyped,
        tree=session.input.tree,
    )
    items: list[Item] = []
    extra: DictInt = {scope: 0 for scope, _label in Constants.scopes}

    def judge(*, mine: str | None, author: str, normalise: bool) -> str:
        """Score the converted annotation against the author's.

        Args:
            mine (str | None): The annotation astart wrote, or ``None``.
            author (str): The author's annotation.
            normalise (bool): Whether to normalise ``mine`` before comparing.

        Returns:
            str: ``missing``, ``exact``, ``wrong``, a relation kind, or
                ``unresolved``.

        """
        if mine is None:
            return "missing"
        shown: str = (
            recovery.normalize_annotation(text=mine) if normalise else mine
        )
        if shown == recovery.normalize_annotation(text=author):
            return "exact"
        kind: str | None = recovery.relation(
            written=shown,
            truth=author,
            context=context,
        )
        if kind == "contradiction":
            return "wrong"
        return kind or "compatible"

    for key, author in truth.items():
        if key in start:
            continue
        mine: str | None = written.get(key)
        items.append(
            Item(
                scope="parameters_and_returns",
                key=key,
                verdict=(
                    judge(mine=mine, author=author, normalise=True)
                    if key in untyped_params
                    else "reference_only"
                ),
                written=mine,
                author=author,
                family=family_of(
                    text=author,
                    classes=classes,
                    typevars=typevars,
                    aliases=aliases,
                ),
                typed_line=typed_params.get(key),
                converted_line=converted_params.get(key),
                untyped_line=untyped_params.get(key),
            ),
        )
    for key, author in truth_vars.items():
        mine = done_vars.get(key)
        items.append(
            Item(
                scope="variables",
                key=key,
                verdict=(
                    judge(mine=mine, author=author, normalise=True)
                    if key in untyped_vars
                    else "reference_only"
                ),
                written=mine,
                author=author,
                family=family_of(
                    text=author,
                    classes=classes,
                    typevars=typevars,
                    aliases=aliases,
                ),
                typed_line=typed_vars.get(key),
                converted_line=converted_vars.get(key),
                untyped_line=untyped_vars.get(key),
            ),
        )
    extra["parameters_and_returns"] = sum(
        1 for key in written if key not in truth and key not in start
    )
    extra["variables"] = sum(1 for key in done_vars if key not in truth_vars)
    return items, extra


def tally(*, items: list[Item]) -> dict[str, Counter[str]]:
    """Count outcomes per scope.

    Args:
        items (list[Item]): Scored annotations.

    Returns:
        dict[str, Counter[str]]: A counter of outcomes for each scope.

    """
    counts: dict[str, Counter[str]] = {
        scope: Counter() for scope, _label in Constants.scopes
    }
    for item in items:
        counts[item.scope][item.verdict] += 1
    return counts


def pair_json(
    *,
    counts: dict[str, Counter[str]],
    extra: DictInt,
) -> DictDictInt:
    """Shape the counts like the output of ``scripts.compare.pair``.

    Args:
        counts (dict[str, Counter[str]]): Outcomes per scope.
        extra (DictInt): Annotations written that the typed file lacks, per
            scope.

    Returns:
        DictDictInt: ``correct`` , ``wrong`` , ``to_recover``
            and the other outcomes per scope.

    """
    shaped: DictDictInt = {}
    for scope, _label in Constants.scopes:
        found: Counter[str] = counts[scope]
        shaped[scope] = {
            "to_recover": sum(found.values()) - found["reference_only"],
            "reference_only": found["reference_only"],
            "correct": found["exact"],
            "equivalent": found["compatible"],
            "semantic_exact": found["exact"] + found["compatible"],
            "narrower": found["narrower"],
            "looser": found["looser"],
            "unresolved": found["unresolved"],
            "wrong": found["wrong"],
            "missing": found["missing"],
            "not_in_typed": extra[scope],
        }
    return shaped


def summary_table(*, shaped: DictDictInt) -> ListStr:
    """Render the summary table.

    Args:
        shaped (DictDictInt): Counts per scope in the ``scripts.compare.pair``
            shape.

    Returns:
        ListStr: Markdown lines.

    """
    lines: ListStr = [
        "| Scope | To recover | Exact spelling | Equivalent | Narrower | "
        "Looser | Unresolved | "
        "Wrong | Missing | Extra |",
        (
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | "
            "---: | ---: |"
        ),
    ]
    for scope, label in Constants.scopes:
        row: DictInt = shaped[scope]
        total: int = row["to_recover"]
        lines.append(
            f"| {label} | {total} | {row['correct']} "
            f"({percent(value=row['correct'], total=total)}) | "
            f"{row['equivalent']} | {row['narrower']} | {row['looser']} | "
            f"{row['unresolved']} | "
            f"{row['wrong']} | {row['missing']} | {row['not_in_typed']} |",
        )
    lines.extend(("", "```text"))
    for scope, label in Constants.scopes:
        row = shaped[scope]
        total = row["to_recover"]
        lines.append(
            f"{label:<24} same type "
            f"{bar(value=row['semantic_exact'], total=total)} "
            f"{percent(value=row['semantic_exact'], total=total):>7}   "
            f"wrong {bar(value=row['wrong'], total=total)} "
            f"{percent(value=row['wrong'], total=total):>7}",
        )
    lines.append("```")
    lines.extend(
        (
            "",
            "**Exact spelling** compares normalized annotation text. "
            "**Equivalent** is the scorer's semantic equivalence result "
            "after expanding aliases or comparing protocol structure. "
            "**Same type** adds these two counts. Narrower and looser types "
            "remain separate; changing "
            "a fixed tuple to a variadic tuple changes its length contract.",
        ),
    )
    return lines


def family_rows(*, items: list[Item]) -> list[dict[str, int | str]]:
    """Group outcomes by the family of the author's annotation.

    Args:
        items (list[Item]): Scored annotations.

    Returns:
        list[dict[str, int | str]]: One row per family, largest gap first.

    """
    by_family: dict[str, Counter[str]] = {
        name: Counter() for name in Constants.families
    }
    for item in items:
        by_family[item.family][item.verdict] += 1
    total_gap: int = sum(1 for item in items if item.verdict in Constants.gap)
    rows: list[dict[str, int | str]] = []
    for name, found in by_family.items():
        total: int = sum(found.values())
        if total == 0:
            continue
        gap: int = sum(found[v] for v in Constants.gap)
        rows.append(
            {
                "family": name,
                "total": total,
                "exact": found["exact"],
                "compatible": sum(found[v] for v in Constants.compatible),
                "unresolved": found["unresolved"],
                "wrong": found["wrong"],
                "missing": found["missing"],
                "gap": gap,
                "share": round(number=100 * gap / total_gap)
                if total_gap
                else 0,
            },
        )
    return sorted(rows, key=lambda row: -int(row["gap"]))


def family_table(
    *,
    rows: list[dict[str, int | str]],
    limit: int,
    anchors: DictStr,
    todo_target: str = "TODO.md",
) -> ListStr:
    """Render the gap-by-family table.

    Args:
        rows (list[dict[str, int | str]]): Output of ``family_rows``.
        limit (int): Maximum number of families shown.
        anchors (DictStr): TODO anchor by task ID, to link the tasks.
        todo_target (str): Relative path to the TODO document.

    Returns:
        ListStr: Markdown lines.

    """
    lines: ListStr = [
        "| Author's annotation | Total | Exact | Compatible | Wrong | "
        "Missing | Share of gap | Hard | Tasks |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | --- |",
    ]
    for row in rows[:limit]:
        name: str = str(object=row["family"])
        hard: str = "yes" if name in Constants.hard else ""
        tasks: str = task_links(
            text=Constants.tasks[name],
            anchors=anchors,
            target=todo_target,
        )
        lines.append(
            f"| {name} | {row['total']} | {row['exact']} | "
            f"{row['compatible']} | {row['wrong']} | {row['missing']} | "
            f"{row['share']} % | {hard} | {tasks} |",
        )
    return lines


def owner_of(*, key: str) -> str:
    """Name the function or class an annotation belongs to.

    Args:
        key (str): Node path such as ``Class.method.param`` or ``function->``.

    Returns:
        str: The path without its last part.

    """
    if key.endswith("->"):
        return key[:-2]
    return key.rpartition(".")[0] or key


@final
class Reasons:
    """Plain-language meaning and TODO tasks for each opacity reason.

    Attributes:
        known (Final[dict[str, tuple[str, str]]]): Reason label to
            ``(meaning, tasks)``.
        unknown (Final[tuple[str, str]]): Fallback for a reason that is not
            described yet.

    """

    known: Final[dict[str, tuple[str, str]]] = {
        "settled": (
            "Typed by negotiation: these are the nodes astart can write",
            "",
        ),
        "declared": (
            "Already annotated in the input, or guaranteed by the language",
            "",
        ),
        "unsettled (no evidence)": (
            "Nothing proves a type and no evidence reaches the node",
            "P-05, AL-05, AL-18",
        ),
        "downstream of a blocked node": (
            "Opacity spreads: the node depends on a blocked one. "
            "Fix the direct reasons first",
            "AL-03, AL-04",
        ),
        "lost a contribution": (
            (
                "A contract could not be transferred, so the result "
                "would be incomplete"
            ),
            "F-07",
        ),
        "direct: unprovable Name": (
            "Returns a name the prover cannot type (a wrapper, a decorated "
            "function, a class)",
            "M5-19, AL-03, M4-03",
        ),
        "direct: unprovable Call": (
            "Returns a call result the prover cannot type "
            "(`super()`, `getattr`, constructors, `list(...)`)",
            "W-06, I-08, I-21, F-41",
        ),
        "direct: function escapes as a value": (
            (
                "The function is passed around as a value, so its "
                "callers are unknown"
            ),
            "W-07, AL-04",
        ),
        "direct: no evidence reaches it": (
            "A parameter with no call site, default or use that proves a type",
            "W-08, P-05, AL-05, AL-09",
        ),
        "direct: stub, abstract or never returns": (
            "Protocol stubs, abstract methods and functions that never return",
            "AF-03, I-16, M5-04",
        ),
        "direct: a call to it cannot be bound": (
            "Some call to the function cannot be matched to its parameters",
            "W-07, M2-02, M2-11",
        ),
        "direct: unprovable Tuple": (
            "Returns a tuple whose members are not all typed",
            "I-17, F-40",
        ),
        "direct: unprovable Dict": (
            "Returns a dict display with unpacking or untyped members",
            "I-17, F-40",
        ),
        "direct: unprovable BinOp": (
            "Arithmetic over operands that are not typed",
            "I-10, W-06",
        ),
        "direct: generator": (
            "Generator functions: the return type needs the yield types",
            "W-13, M4-06",
        ),
        "direct: unprovable Attribute": (
            "Returns an attribute the class table does not type",
            "I-11, W-12, M2-06",
        ),
    }
    unknown: Final[tuple[str, str]] = (
        "Not described yet: add it to the table in "
        "scripts/compare/conversion_report.py",
        "G-03",
    )


def describe(*, label: str) -> tuple[str, str]:
    """Look up the meaning and tasks of an opacity reason.

    Args:
        label (str): Reason label from the opacity report.

    Returns:
        tuple[str, str]: The meaning and the tasks.

    """
    if label in Reasons.known:
        return Reasons.known[label]
    if label.startswith("direct: unprovable "):
        kind: str = label.removeprefix("direct: unprovable ")
        return f"Returns a {kind} expression the prover cannot type", "G-03"
    return Reasons.unknown


def opacity_sections(
    *,
    source: str,
    samples: int,
    tree: CommentedModule | None = None,
) -> list[Section]:
    """Run the opacity analysis of the untyped module.

    Args:
        source (str): Untyped source.
        tree (CommentedModule | None): Shared parsed input module.
        samples (int): Examples kept per direct reason.

    Returns:
        list[Section]: The sections of ``scripts/opacity_report.collect``,
            or an empty list when that script cannot be imported.

    """
    for name in ("scripts.compare.opacity_report",):
        try:
            module: ModuleType = import_module(name=name)
        except ImportError:
            continue
        return cast(
            typ="list[Section]",
            val=list(
                module.collect(source=source, samples=samples, module=tree),
            ),
        )
    return []


def owner_cell(*, owner: str, sources: Sources) -> str:
    """Show an owner with a link to its definition in the input.

    Args:
        owner (str): Function or class path.
        sources (Sources): Source lines and line maps.

    Returns:
        str: The owner in code style, with a link when its line is known.

    """
    number: int | None = sources.untyped_params.get(
        f"{owner}->",
    ) or sources.untyped_vars.get(owner)
    if number is None:
        return f"`{owner}`"
    where: str = link(
        label="untyped.py",
        target=sources.links["untyped"],
        number=number,
    )
    return f"`{owner}` ({where})"


def opacity_markdown(
    *,
    sections: list[Section],
    sources: Sources,
) -> ListStr:
    """Render the opacity analysis as tables with linked examples.

    Args:
        sections (list[Section]): Sections from ``opacity_sections``.
        sources (Sources): Source lines, line maps and link targets.

    Returns:
        ListStr: Markdown lines.

    """
    lines: ListStr = []
    todo_target: str = sources.links.get("todo", "TODO.md")
    anchors: DictStr = sources.anchors
    for section in sections:
        lines.extend(
            (
                f"### {section.title.capitalize()}: {section.total} nodes",
                "",
                "| Reason | Nodes | Share | | What it means | Tasks |",
                "| --- | ---: | ---: | --- | --- | --- |",
            ),
        )
        for row in section.rows:
            meaning, tasks = describe(label=row.label)
            linked_tasks: str = task_links(
                text=tasks,
                anchors=anchors,
                target=todo_target,
            )
            lines.append(
                f"| {row.label} | {row.count} | "
                f"{percent(value=row.count, total=section.total)} | "
                f"`{bar(value=row.count, total=section.total)}` | "
                f"{meaning} | "
                f"{linked_tasks} |",
            )
        for row in section.rows:
            if not row.samples:
                continue
            lines.extend(
                (
                    "",
                    f"<details><summary>Examples: {row.label} "
                    f"({row.count} nodes)</summary>",
                    "",
                    "| Node | Line | Code | Evidence |",
                    "| --- | ---: | --- | --- |",
                ),
            )
            for node, why in row.samples:
                number: int | None = node_line(
                    key=node,
                    sources=sources,
                )
                code: str | None = line_text(
                    lines=sources.untyped,
                    number=number,
                )
                shown: str = (
                    "n/a" if code is None else f"`{cell(text=code.strip())}`"
                )
                where: str = link(
                    label="untyped.py",
                    target=sources.links["untyped"],
                    number=number,
                )
                lines.append(
                    f"| `{node}` | {where} | {shown} | `{cell(text=why)}` |",
                )
            lines.extend(("", "</details>"))
        lines.append("")
    return lines


def plain(*, text: str) -> str:
    """Make text safe inside inline code.

    Args:
        text (str): Any text.

    Returns:
        str: The text with backticks replaced.

    """
    return text.replace("`", "'")


class _EvidenceModule(Protocol):
    """The slice of ``scripts.compare.evidence`` the report uses."""

    def build_index(self, *, source: str, tree: Module | None = None) -> Index:
        """Index a module for evidence lookup.

        Args:
            source (str): Module source.
            tree (Module | None): Shared parsed module, when available.

        Returns:
            The evidence index.

        """
        ...

    def evidence_for(
        self,
        *,
        index: Index,
        key: str,
        scope: str,
    ) -> list[Evidence] | None:
        """Collect the evidence for one scored node.

        Args:
            index (Index): The module index.
            key (str): Node path.
            scope (str): Result scope.

        Returns:
            The facts, or ``None`` when the node is unknown.

        """
        ...

    def conclusion(self, *, author: str, evidence: list[Evidence]) -> str:
        """Say in words why the evidence does not give the author's type.

        Args:
            author (str): The author's annotation.
            evidence (list[Evidence]): The collected facts.

        Returns:
            One paragraph of reading.

        """
        ...

    def short(self, *, node: AST | str) -> str:
        """Render an expression for display, shortened.

        Args:
            node (AST | str): An AST node or text.

        Returns:
            The shortened rendering.

        """
        ...


def evidence_module() -> _EvidenceModule | None:
    """Import the evidence collector next to this script.

    Returns:
        _EvidenceModule | None:
            The module, or ``None`` when it cannot be imported.

    """
    for name in ("scripts.compare.evidence",):
        try:
            return cast(typ="_EvidenceModule", val=import_module(name=name))
        except ImportError:
            continue
    return None


type _Collected = tuple[_EvidenceModule, list[Evidence]]


def _collect_evidence(
    *,
    module: _EvidenceModule | None,
    sources: Sources,
    item: Item,
) -> _Collected | None:
    """Pair the evidence module with the facts for one scored node.

    Args:
        module (_EvidenceModule | None): The imported evidence module.
        sources (Sources): Source lines and the evidence index.
        item (Item): The scored node.

    Returns:
        _Collected | None:
            The module and its facts, or ``None`` when either is missing.

    """
    index: Index | None = sources.evidence
    if module is None or index is None:
        return None
    found: list[Evidence] | None = module.evidence_for(
        index=index,
        key=item.key,
        scope=item.scope,
    )
    if not found:
        return None
    return module, found


def astart_part(*, item: Item, sources: Sources) -> str:
    """Explain why astart missed or changed the author's type.

    Args:
        item (Item): A scored annotation that is missing or differs.
        sources (Sources): Source lines, line maps and the opacity reasons.

    Returns:
        str: One paragraph, specific to the node.

    """
    found: tuple[str, str] | None = sources.reasons.get(item.key)
    observed: str = (
        "No annotation was written."
        if item.written is None
        else f"The tool wrote `{plain(text=item.written)}`."
    )
    if found is None:
        return (
            f"{observed} The scorer labels this **{item.verdict}**. "
            "No candidate-selection trace was recorded for this target, "
            "so the report cannot identify which inference rule or guard "
            "produced that result. Absence of a diagnostic does not show "
            "that no rule examined the target."
        )
    label, why = found
    detail: str = f" Observation: `{plain(text=why)}`." if why else ""
    tasks: str = task_links(
        text=describe(label=label)[1],
        anchors=sources.anchors,
        target=sources.links.get("todo", "TODO.md"),
    )
    return (
        f"{observed} A separate negotiator analysis reports **{label}**."
        f"{detail} {describe(label=label)[0]}. "
        "This observation is a debugging lead; it does not identify the "
        "conversion's selected candidate or prove why it was accepted or "
        f"refused. Related work: {tasks}."
    )


def evidence_implication(*, fact: Evidence) -> str:
    """Describe what an observation can establish without overclaiming.

    Args:
        fact (Evidence): An input-source observation from the evidence
            collector.

    Returns:
        str: The observation's scope and its inference limitation.

    """
    if not fact.certain:
        return "Name-only match; binding to this target is unverified."
    meanings: tuple[tuple[bool, str], ...] = (
        (
            "call site" in fact.kind or "default" in fact.kind,
            "Shows one argument/default, not every accepted input.",
        ),
        (
            "iterat" in fact.kind,
            "Requires iteration; indexing and element types need evidence.",
        ),
        (
            "index" in fact.kind,
            "Requires subscription; this alone does not identify a class.",
        ),
        (
            "method" in fact.kind,
            "Requires this member; its name alone does not prove a class.",
        ),
        (
            "return" in fact.kind or "yield" in fact.kind,
            "Contributes a result; all paths and operands must be resolved.",
        ),
        (
            fact.kind in {"assignment", "adds elements", "updated in place"},
            "Constrains stored values; later writes and aliases also matter.",
        ),
    )
    return next(
        (meaning for matches, meaning in meanings if matches),
        "A constraint to combine with other operations and bindings.",
    )


def input_evidence(*, item: Item, sources: Sources) -> ListStr:
    """Render a compact, qualified chain of input-source observations.

    Args:
        item (Item): The annotation being explained.
        sources (Sources): Source links and evidence index.

    Returns:
        ListStr:
            A table separating source observations from their implications.

    """
    collected: _Collected | None = _collect_evidence(
        module=evidence_module(),
        sources=sources,
        item=item,
    )
    if collected is None:
        return [
            "The collector did not resolve direct evidence for this target. "
            "This is a limit of the collector, not proof that the type "
            "cannot be inferred from the source.",
        ]
    _module, found = collected
    lines: ListStr = [
        "| Source | Observation | What it establishes |",
        "| --- | --- | --- |",
    ]
    for fact in found[:8]:
        where: str = link(
            label="input",
            target=sources.links["untyped"],
            number=fact.line,
        )
        shown: str = (
            f" Observed type: `{cell(text=fact.type)}`." if fact.type else ""
        )
        lines.append(
            f"| {where} | {cell(text=fact.kind)}: "
            f"`{cell(text=fact.text)}`{shown} | "
            f"{evidence_implication(fact=fact)} |",
        )
    lines.extend(
        (
            "",
            "These observations constrain the annotation. Examples of values "
            "passed by current callers do not establish the full public input "
            "contract, and an unresolved name match is not type evidence.",
        ),
    )
    return lines


def reference_evidence(*, item: Item, sources: Sources) -> ListStr:
    """Explain the authored contract separately from lexical context.

    Args:
        item (Item): Annotation being explained.
        sources (Sources): Source links and optional reference graph.

    Returns:
        ListStr: The source contract and concise contextual observations.

    """
    where: str = _typed_link(item=item, sources=sources)
    lines: ListStr = [
        f"The reference declares `{plain(text=item.author)}` at {where}. "
        "That declaration defines the comparison target; it is not an "
        "independent proof that the type is uniquely inferable.",
    ]
    if sources.reference is None:
        return lines
    lines.extend(("", *contract_parts(item=item, graph=sources.reference)))
    json_link: str = sources.links.get("report_json", "conversion-report.json")
    facts: list[_ReferenceEvidence] = sources.reference.facts(key=item.key)
    name: str = item.key.rpartition(".")[2]
    relevant: list[_ReferenceEvidence] = [
        fact
        for fact in facts
        if fact["kind"] == "AST_OPERATION"
        and (
            (item.key.endswith("->") and "return/yield" in fact["explanation"])
            or name in fact["expression"]
        )
    ]
    if relevant:
        lines.extend(("", "Related operations in the reference:", ""))
    for fact in relevant[:3]:
        location: str = link(
            label="reference",
            target=sources.links["typed"],
            number=fact["source_span"].get("lineno"),
        )
        expression: str = " ".join(fact["expression"].split())
        lines.append(
            (
                f"- {location}: `{plain(text=expression[:160])}`. "
                f"{fact['explanation']}"
            ),
        )
    lines.extend(
        (
            "",
            "<details><summary>Graph evidence and limitations</summary>",
            "",
            f"{len(facts)} linked records are retained in "
            "[conversion-report.json]("
            f"{json_link}"
            "). "
            "Non-declaration records are lexical context, not proofs of the "
            "expected type. Constraint and type IDs resolve in the source ",
            "graph.",
            "</details>",
        ),
    )
    return lines


def explain(*, item: Item, sources: Sources) -> ListStr:
    """Explain, for one case, why the author's type is what it is.

    Args:
        item (Item): A scored annotation.
        sources (Sources): Source lines, line maps, evidence index and reasons.

    Returns:
        ListStr: Markdown lines: the numbered path of evidence
            in the untyped source, a reading of it, and
            why astart did not reach the author's type.

    """
    return [
        "**1. Expected contract**",
        "",
        *reference_evidence(item=item, sources=sources),
        "",
        "**2. Evidence in the untyped input**",
        "",
        *input_evidence(item=item, sources=sources),
        "",
        "**3. Tool diagnosis**",
        "",
        astart_part(item=item, sources=sources),
    ]


def case(
    *,
    item: Item,
    sources: Sources,
    level: int = 3,
) -> ListStr:
    """Show a separated case with a contract comparison and evidence chain.

    Args:
        item (Item): A scored annotation.
        sources (Sources): Source lines, line maps, evidence index and reasons.
        level (int): Heading depth under the surrounding issue group.

    Returns:
        ListStr: Markdown lines.

    """
    written: str = (
        "Not annotated"
        if item.written is None
        else f"`{cell(text=item.written)}`"
    )
    return [
        "---",
        "",
        f"{'#' * level} {item.verdict.capitalize()} annotation: `{item.key}`",
        "",
        f"**{item.verdict.capitalize()}** · {item.family}",
        "",
        "| Current tool output | Expected reference |",
        "| --- | --- |",
        f"| {written} | `{cell(text=item.author)}` |",
        "",
        "<details><summary>Source locations and code comparison</summary>",
        "",
        *snippet(item=item, sources=sources),
        "",
        "</details>",
        "",
        *explain(item=item, sources=sources),
    ]


def astart_short(*, item: Item, sources: Sources) -> str:
    """Say in a few words why astart missed or changed the author's type.

    Args:
        item (Item): A scored annotation that is not exact.
        sources (Sources): Source lines, line maps and the opacity reasons.

    Returns:
        str: A short phrase for a code comment.

    """
    if item.verdict == "missing":
        found: tuple[str, str] | None = sources.reasons.get(item.key)
        if found is None:
            return "astart: no graph node for this path"
        label, why = found
        detail: str = f" ({plain(text=why)})" if why else ""
        return f"astart: {label}{detail}"
    written: str = item.written or "?"
    return f"astart wrote {plain(text=written)}"


def fix_comment(*, item: Item, sources: Sources) -> str:
    """Build the bespoke ``[FIX]`` comment for one case.

    Args:
        item (Item): A scored annotation that is not exact.
        sources (Sources): Source lines, line maps, evidence index and reasons.

    Returns:
        str: One line: the author's type, the evidence that
            leads to it, and why astart did not reach it.

    """
    collected: _Collected | None = _collect_evidence(
        module=evidence_module(),
        sources=sources,
        item=item,
    )
    target: str = (
        "->" if item.key.endswith("->") else item.key.rpartition(".")[2]
    )
    parts: ListStr = []
    if collected is None:
        parts.append("no evidence for this node in the untyped source")
    else:
        module, found = collected
        typed_first: list[Evidence] = [fact for fact in found if fact.type][
            :2
        ] or found[:2]
        for fact in typed_first:
            shown: str = f" -> {fact.type}" if fact.type else ""
            parts.append(
                f"untyped.py:{fact.line} {fact.kind} "
                f"{module.short(node=plain(text=fact.text))}{shown}",
            )
        parts.append(
            "observations constrain the type; see report for their limits",
        )
    parts.append(astart_short(item=item, sources=sources))
    text: str = (
        f"[FIX] {target}: {item.author} ({item.verdict}) - " + "; ".join(parts)
    )
    limit: int = 320
    return text if len(text) <= limit else text[: limit - 1] + "…"


def full_report(
    *,
    meta: DictStr,
    shaped: DictDictInt,
    items: list[Item],
    extras: Extras,
) -> str:
    """Render the full Markdown report.

    Args:
        meta (DictStr): Header fields (time, tree, duration, settings,
            command).
        shaped (DictDictInt): Counts per scope.
        items (list[Item]): Scored annotations.
        extras (Extras): Optional report content (sections, sources, examples).

    Returns:
        str: The report text.

    """
    sections: list[Section] = extras.sections
    sources: Sources = extras.sources
    generator_link: str = sources.links.get("generator", "../__main__.py")
    opacity_link = sources.links.get("opacity_script", "../opacity_report.py")
    examples: int = extras.examples
    files: str = (
        f"[fixtures/untyped.py]({sources.links['untyped']}) · "
        f"[{Path(sources.links['typed']).name}]({sources.links['typed']}) · "
        f"[result.py]({sources.links['converted']})"
    )
    lines: ListStr = [
        f"# Conversion report: [`fixtures/untyped.py`]"
        f"({sources.links['untyped']}) "
        f"to [`{Path(sources.links['typed']).name}`]"
        f"({sources.links['typed']})",
        "",
        f"*Generated {meta['when']} by "
        "[`scripts/compare`]("
        f"{generator_link}"
        "). "
        "Do not edit; run the script again.*",
        "",
        "In every code example `-` is how the converted code is "
        "([result.py](result.py)) and `+` is "
        "the reference contract; the links go "
        "to the exact lines.",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| files | {files} |",
    ]
    lines.extend(
        f"| {key} | {value} |" for key, value in meta.items() if key != "when"
    )
    lines.extend(("", "## Summary", ""))
    lines.extend(summary_table(shaped=shaped))
    lines.extend(
        (
            "",
            "## Where the gap is, by the author's annotation",
            "",
            "Compatible includes equivalent, narrower and looser types. "
            "Hard families are partly author choices or policy and bound the "
            "90 % target.",
            "",
        ),
    )
    rows: list[dict[str, int | str]] = family_rows(items=items)
    lines.extend(
        family_table(
            rows=rows,
            limit=len(rows),
            anchors=sources.anchors,
            todo_target=sources.links.get("todo", "TODO.md"),
        ),
    )
    wrong: list[Item] = sorted(
        (item for item in items if item.verdict == "wrong"),
        key=lambda item: (item.scope, item.key),
    )
    lines.extend(
        (
            "",
            f"## Wrong annotations ({len(wrong)}), with code",
            "",
            "The scorer found incompatible annotations. Each case separates "
            "the reference contract, observed input constraints, and the "
            "limits of the recorded tool diagnosis.",
            "",
        ),
    )
    for item in wrong:
        lines.extend((*case(item=item, sources=sources), ""))
    owners: Counter[str] = Counter(
        owner_of(key=item.key)
        for item in items
        if item.verdict in Constants.gap
    )
    lines.extend(
        (
            "## Gap by owner (most missing or wrong first)",
            "",
            "| Owner | Gap |",
            "| --- | ---: |",
        ),
    )
    lines.extend(
        f"| {owner_cell(owner=owner, sources=sources)} | {count} |"
        for owner, count in owners.most_common(n=Constants.owner_rows)
    )
    lines.extend(("", "## Missing annotations by family, with code", ""))
    for row in rows:
        name: str = str(object=row["family"])
        missing: list[Item] = [
            item
            for item in items
            if item.family == name and item.verdict == "missing"
        ]
        if not missing:
            continue
        lines.extend(
            (
                f"### {name}: {len(missing)} missing",
                "",
                (
                    "Tasks: "
                    + task_links(
                        text=Constants.tasks[name],
                        anchors=sources.anchors,
                        target=sources.links.get("todo", "TODO.md"),
                    )
                ),
                "",
            ),
        )
        for item in missing[:examples]:
            lines.extend((*case(item=item, sources=sources, level=4), ""))
        lines.extend(
            (
                f"<details><summary>All {len(missing)} (first "
                f"{Constants.list_limit}, with links to the author's line)"
                "</summary>",
                "",
            ),
        )
        lines.extend(
            f"- `{item.key}` "
            f"({_typed_link(item=item, sources=sources)})"
            f": `{item.author}`"
            for item in missing[: Constants.list_limit]
        )
        lines.extend(("", "</details>", ""))
    opacity_link: str = sources.links.get(
        "opacity_script",
        "../scripts/compare/opacity_report.py",
    )
    lines.extend(
        (
            "## Why nodes stay unannotated",
            "",
            f"From [`opacity_report.py`]({opacity_link}) "
            "on the untyped input. A node is something that has a type: a "
            "parameter, a return value or a local variable. A *direct* reason "
            "blocks a node by itself; the other labels describe nodes that "
            "are typed, declared, or blocked only because of another node.",
            "",
        ),
    )
    lines.extend(
        opacity_markdown(sections=sections, sources=sources)
        if sections
        else ["The opacity analysis was skipped or could not run.", ""],
    )
    lines.extend(("## Reproduce", "", f"`{meta['command']}`"))
    return "\n".join(lines) + "\n"


def todo_block(
    *,
    meta: DictStr,
    shaped: DictDictInt,
    items: list[Item],
    sections: list[Section],
    sources: Sources,
) -> str:
    """Render the compact block that is embedded in the TODO file.

    Args:
        meta (DictStr): Header fields.
        shaped (DictDictInt): Counts per scope.
        items (list[Item]): Scored annotations.
        sections (list[Section]): Opacity sections (may be empty).
        sources (Sources): Source lines, line maps and link targets.

    Returns:
        str: Markdown for the block between the conversion markers.

    """
    report_link: str = sources.links.get("report", "conversion-report.md")
    lines: ListStr = [
        f"Run {meta['when']} · tree `{meta['tree']}` · converted in "
        f"{meta['converted in']} · files: "
        f"[fixtures/untyped.py]({sources.links['untyped']}), "
        f"[{Path(sources.links['typed']).name}]({sources.links['typed']}), "
        f"[result.py]({sources.links['converted']}) · "
        "[full report]("
        f"{report_link})",
        "",
    ]
    todo_target: str = sources.links.get("todo", "TODO.md")
    anchors: DictStr = sources.anchors
    lines.extend(summary_table(shaped=shaped))
    rows: list[dict[str, int | str]] = family_rows(items=items)
    lines.extend(("", "Where the gap is, by the author's annotation:", ""))
    lines.extend(
        family_table(
            rows=rows,
            limit=8,
            anchors=anchors,
            todo_target=sources.links.get("todo", "TODO.md"),
        ),
    )
    if sections:
        lines.extend(
            (
                "",
                "Why nodes stay unannotated (biggest direct reasons; "
                "examples with links are in the full report):",
                "",
                (
                    "| Nodes | Reason | Nodes of that kind | What it "
                    "means | Tasks |"
                ),
                "| --- | --- | ---: | --- | --- |",
            ),
        )
        for section in sections:
            direct: list[Row] = [
                r for r in section.rows if r.label.startswith("direct")
            ]
            for row in direct[:4]:
                meaning, tasks = describe(label=row.label)
                linked_tasks: str = task_links(
                    text=tasks,
                    anchors=anchors,
                    target=todo_target,
                )
                lines.append(
                    f"| {section.title} | {row.label} | {row.count} "
                    f"({percent(value=row.count, total=section.total)}) | "
                    f"{meaning} | "
                    f"{linked_tasks} |",
                )
    wrong: list[Item] = sorted(
        (item for item in items if item.verdict == "wrong"),
        key=lambda item: (item.scope, item.key),
    )
    lines.extend(
        (
            "",
            "In the examples `-` is how the converted code is and `+` is how "
            "it should be (the author's `fixtures/typed.py`); "
            "the links go to the exact lines.",
            "",
            f"<details><summary>Wrong annotations with code "
            f"(first 6 of {len(wrong)})</summary>",
            "",
        ),
    )
    for item in wrong[:6]:
        lines.extend((*case(item=item, sources=sources), ""))
    lines.extend(("</details>", ""))
    lines.extend(
        (
            "<details><summary>Examples of missing annotations "
            "(1 per family, largest gaps first)</summary>",
            "",
        ),
    )
    for row in rows[:6]:
        name: str = str(object=row["family"])
        missing: list[Item] = [
            item
            for item in items
            if item.family == name and item.verdict == "missing"
        ]
        if not missing:
            continue
        tasks: str = task_links(
            text=Constants.tasks[name],
            anchors=anchors,
        )
        lines.extend(
            (
                f"**{name}** ({len(missing)} missing; tasks: {tasks})",
                "",
            ),
        )
        for item in missing[:1]:
            lines.extend((*case(item=item, sources=sources), ""))
    lines.append("</details>")
    return "\n".join(lines)


def write_block(*, todo: Path, name: str, block: str) -> bool:
    """Replace one generated block in the TODO file.

    Args:
        todo (Path): Path of the TODO file.
        name (str): Marker name of the block.
        block (str): New block text.

    Returns:
        bool: Whether the markers were found and the block written.

    """
    start: str = f"<!-- {name}:start -->"
    end: str = f"<!-- {name}:end -->"
    text: str = todo.read_text(encoding="utf-8")
    head, found_start, rest = text.partition(start)
    _, found_end, tail = rest.partition(end)
    if not found_start or not found_end:
        return False
    _ = todo.write_text(
        data=f"{head}{start}\n{block}\n{end}{tail}",
        encoding="utf-8",
    )
    return True


def convert(*, source: str, settings: Namespace) -> str:
    """Run astart in conversion mode on a source text.

    Args:
        source (str): Untyped source.
        settings (Namespace): Parsed options (``min_confidence``, ``checker``).

    Returns:
        str: The converted source.

    """
    rules: ModuleType = import_module(name="astart.rules")
    vocabulary: ModuleType = import_module(name="astart.rules.vocabulary")
    registries: Registries = rules.default_registries()
    checker: Checker | None = None
    if settings.checker:
        checker = import_module(name="astart.rules.checker").build_checker(
            root=Path.cwd(),
        )
    return rules.fix_source(
        source=source,
        filename="untyped.py",
        catalog=rules.load_default_catalog(registries=registries),
        registries=registries,
        settings=rules.FixSettings(
            ceiling=vocabulary.FixSafety.guarded,
            min_confidence=settings.min_confidence,
            annotate_variables=True,
            negotiate=True,
            engine=True,
            checker=checker,
        ),
    ).source


def build_evidence_index(
    *,
    source: str,
    tree: Module | None = None,
) -> Index | None:
    """Index the untyped source for evidence lookup.

    Args:
        source (str): Untyped source.
        tree (Module | None): Shared parsed input module.

    Returns:
        Index | None:
            The index, or ``None`` when the collector cannot be imported.

    """
    module: _EvidenceModule | None = evidence_module()
    return (
        None
        if module is None
        else module.build_index(source=source, tree=tree)
    )


def _report_meta(
    *,
    namespace: Namespace,
    reused: bool,
    seconds: float,
    untyped: str,
    typed: str,
) -> tuple[DictStr, datetime]:
    """Build the report metadata and its timestamp.

    Args:
        namespace (Namespace): Parsed command-line arguments.
        reused (bool): Whether the saved conversion output was reused.
        seconds (float): Wall-clock seconds the conversion took.
        untyped (str): Untyped source.
        typed (str): Typed source.

    Returns:
        tuple[DictStr, datetime]: The metadata mapping and the generation time.

    """
    now: datetime = datetime.now().astimezone()
    command: str = "python scripts/compare" + (
        f" --min-confidence {namespace.min_confidence}"
        + (" --checker" if namespace.checker else "")
        + (" --reuse" if reused else "")
    )
    meta: DictStr = {
        "when": now.strftime(format="%a %d %b %Y, %H:%M %Z").strip(),
        "tree": tree_hash(root=Constants.root),
        "reference SHA-256": sha256(string=typed.encode()).hexdigest(),
        "converted in": (
            "saved output reused" if reused else f"{seconds:.0f} s"
        ),
        "untyped / typed": (
            f"{len(untyped.splitlines())} / {len(typed.splitlines())} lines"
        ),
        "settings": (
            "conversion mode (engine), negotiation on, variables on, "
            f"minimum confidence {namespace.min_confidence}, "
            f"checker {'on' if namespace.checker else 'off'}"
        ),
        "command": command,
        "reference-only targets": (
            "Reported separately; excluded from recovery totals"
        ),
    }
    return meta, now


def _prepare_report(
    *,
    namespace: Namespace,
    session: ComparisonSession,
) -> tuple[list[Section], Sources]:
    """Build evidence and source links from the shared comparison session.

    Args:
        namespace (Namespace): Report command settings.
        session (ComparisonSession): The three authoritative source trees.

    Returns:
        tuple[list[Section], Sources]: Opacity evidence and the linked source
            bundle.

    """
    untyped_source: str = session.input.source
    typed_source: str = session.reference.source
    converted_source: str = session.output.source
    sections: list[Section] = (
        []
        if namespace.no_opacity
        else opacity_sections(
            source=untyped_source,
            samples=namespace.examples + 1,
            tree=session.input.tree,
        )
    )
    out_dir: Path = namespace.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path: Path = out_dir / "result.py"
    _ = output_path.write_text(data=converted_source, encoding="utf-8")
    sources: Sources = Sources(
        untyped=untyped_source.splitlines(),
        typed=typed_source.splitlines(),
        converted=converted_source.splitlines(),
        links={
            "typed": (
                relpath(path=namespace.typed, start=out_dir).replace("\\", "/")
            ),
            "untyped": relpath(
                path=namespace.untyped,
                start=out_dir,
            ).replace("\\", "/"),
            "converted": output_path.name,
            "generator": relpath(
                path=Constants.root / "scripts" / "compare" / "__main__.py",
                start=out_dir,
            ),
            "opacity_script": relpath(
                path=Constants.root
                / "scripts"
                / "compare"
                / "opacity_report.py",
                start=out_dir,
            ),
            "todo": relpath(path=namespace.todo, start=out_dir),
            "report": "conversion-report.md",
            "report_json": "conversion-report.json",
            "annotated": "conversion-annotated.py.txt",
        },
        untyped_params=param_lines(
            source=untyped_source,
            tree=session.input.tree,
        ),
        untyped_vars=variable_lines(
            source=untyped_source,
            tree=session.input.tree,
        ),
        anchors=todo_anchors(todo=namespace.todo),
        evidence=build_evidence_index(
            source=untyped_source,
            tree=session.input.tree,
        ),
        reasons={
            path: reason
            for section in sections
            for path, reason in section.nodes.items()
        },
        reference=selected_reference(namespace=namespace, source=typed_source),
    )
    return sections, sources


def _arguments() -> Namespace:
    """Parse conversion, reference and report settings.

    Returns:
        Namespace: The selected command-line settings.

    """
    parser: ArgumentParser = ArgumentParser(prog="conversion_report")
    parser.add_argument(
        "--untyped",
        type=Path,
        default=Constants.root / "fixtures" / "untyped.py",
    )
    parser.add_argument(
        "--typed",
        type=Path,
        default=Constants.root / "fixtures" / "typed.py",
    )
    parser.add_argument(
        "--reference-graph",
        type=Path,
        help=(
            "Annotation evidence graph; defaults to the typed reference graph"
        ),
    )
    parser.add_argument("--min-confidence", type=float, default=0.5)
    parser.add_argument("--examples", type=int, default=5)
    parser.add_argument("--checker", action="store_true")
    parser.add_argument("--no-opacity", action="store_true")
    parser.add_argument("--no-todo", action="store_true")
    parser.add_argument("--reuse", action="store_true")
    parser.add_argument("--ledger", default="")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Constants.root
        / "scripts"
        / "compare"
        / "artifacts"
        / "results",
    )
    parser.add_argument(
        "--todo",
        type=Path,
        default=Constants.root / "docs" / "planning" / "TODO.md",
    )
    return parser.parse_args()


def main() -> int:
    """Convert, score and write the report.

    Returns:
        int: Zero.

    """
    args: Namespace = _arguments()
    out_dir: Path = args.out_dir
    todo_path: Path = args.todo
    path.insert(0, str(object=Constants.root / "src"))
    path.insert(0, str(object=Constants.root))
    structural: _Structure = cast(
        typ="_Structure",
        val=import_module(name="scripts.compare.conversion_structure"),
    )
    untyped: str = args.untyped.read_text(encoding="utf-8")
    typed: str = args.typed.read_text(encoding="utf-8")
    _ = stdout.write(
        f"Converting {args.untyped} ({len(untyped.splitlines())} lines) "
        "in memory; this takes 1 to 2 minutes...\n",
    )
    saved: Path = out_dir / "result.py"
    reused: bool = bool(args.reuse and saved.exists())
    began: float = perf_counter()
    converted: str = (
        saved.read_text(encoding="utf-8")
        if reused
        else convert(source=untyped, settings=args)
    )
    seconds: float = perf_counter() - began
    _ = stdout.write(
        ("Reused the saved output" if reused else "Converted")
        + f" in {seconds:.0f} s; scoring...\n",
    )
    recovery: _Recovery = cast(
        typ="_Recovery",
        val=import_module(name="astart.rules.recovery"),
    )
    session: ComparisonSession = ComparisonSession.create(
        untyped=untyped,
        typed=typed,
        converted=converted,
    )
    items, extra = compare(
        untyped=untyped,
        typed=typed,
        converted=converted,
        recovery=recovery,
        session=session,
    )
    counts: dict[str, Counter[str]] = tally(items=items)
    shaped: DictDictInt = pair_json(
        counts=counts,
        extra=extra,
    )
    meta, now = _report_meta(
        namespace=args,
        reused=reused,
        seconds=seconds,
        untyped=untyped,
        typed=typed,
    )
    meta["converted SHA-256"] = sha256(string=converted.encode()).hexdigest()
    sections, sources = _prepare_report(namespace=args, session=session)
    reference: ReferenceGraph | None = sources.reference
    artifacts: list[Difference] = structural.compare_artifacts(
        typed=typed,
        converted=converted,
        untyped=untyped,
        session=session,
    )
    report_path: Path = out_dir / "conversion-report.md"
    report_text: str = full_report(
        meta=meta,
        shaped=shaped,
        items=items,
        extras=Extras(
            sections=sections,
            sources=sources,
            examples=args.examples,
        ),
    )
    report_text = report_text.replace(
        "## Where the gap is, by the author's annotation",
        "\n".join(
            structural.structure_markdown(
                differences=artifacts,
                typed_link=sources.links["typed"],
                converted_link=sources.links["converted"],
            ),
        )
        + """
## Where the gap is, by the author's annotation""",
        count=1,
    )
    _ = report_path.write_text(data=report_text, encoding="utf-8")
    artifact_data: StructureJson = structural.structure_json(
        differences=artifacts,
    )
    data: dict[str, object] = {
        "schema_version": 2,
        **shaped,
        "generated": now.isoformat(timespec="seconds"),
        "meta": meta,
        "items": [asdict(obj=item) for item in items],
        "artifacts": artifact_data,
        "agent_summary": {
            "annotation_counts": shaped,
            "artifact_counts": artifact_data["categories"],
            "comparison_module_parses": 3,
            "output_only_classes": [
                {
                    "kind": item.kind,
                    "key": item.actual.key,
                    "line": item.actual.line,
                    "verdict": item.verdict,
                }
                for item in artifacts
                if item.kind in {"classes", "protocols"}
                and item.actual is not None
                and item.actual.fields.get("origin") == "output_only"
            ],
            "report_command": "python scripts/compare",
            "reuse_command": "python scripts/compare --reuse",
            "todo_update": "Generated TODO counts use this same comparison.",
        },
        "opacity": [asdict(obj=section) for section in sections],
    }
    if reference is not None:
        data["reference_graph"] = {
            "path": str(object=reference.path),
            "source_digest": reference.document["revision"]["source_digest"],
            "comparison": "Scored against this run; saved verdicts unused",
            "evidence_role": "Authored contracts and lexical context",
            "annotation_targets": reference.document["annotation_targets"],
            "evidence": reference.document["evidence"],
            "items": {
                item.key: {
                    "target_ids": [
                        target["id"]
                        for target in reference.targets(key=item.key)
                    ],
                    "evidence_ids": [
                        fact["id"] for fact in reference.facts(key=item.key)
                    ],
                    "input_target_exists": item.untyped_line is not None,
                    "diagnostic": (
                        "Reference-only target; inspect structural alignment"
                        if item.untyped_line is None
                        else "Use current opacity evidence for tool diagnosis"
                    ),
                }
                for item in items
            },
        }
    json_path: Path = out_dir / "conversion-report.json"
    _ = json_path.write_text(
        data=dumps(obj=data, indent=2) + "\n",
        encoding="utf-8",
    )
    _ = stdout.write(
        f"Wrote {report_path}, {json_path} and {saved}\n",
    )
    if not args.no_todo:
        todo_sources: Sources = replace(
            sources,
            links={
                key: relpath(
                    path=(out_dir / value).resolve(),
                    start=todo_path.parent,
                ).replace("\\", "/")
                for key, value in sources.links.items()
            },
        )
        block: str = todo_block(
            meta=meta,
            shaped=shaped,
            items=items,
            sections=sections,
            sources=todo_sources,
        )
        block += "\n" + "\n".join(
            structural.structure_markdown(
                differences=artifacts,
                typed_link=todo_sources.links["typed"],
                converted_link=todo_sources.links["converted"],
                include_details=False,
            ),
        )
        wrote: bool = write_block(
            todo=args.todo,
            name="conversion",
            block=block,
        )
        _ = stdout.write(
            f"Updated the conversion block of {args.todo}\n"
            if wrote
            else f"No conversion markers in {args.todo}; block not written\n",
        )
    if args.ledger:
        done: CompletedProcess[str] = run(
            args=[
                executable,
                "-m",
                "scripts.todo_update",
                "status",
                "--quiet",
                "pair",
                "--label",
                args.ledger,
            ],
            input=dumps(obj=shaped),
            text=True,
            check=False,
        )
        _ = stdout.write(f"Ledger updated (exit {done.returncode})\n")
    located: int = sum(1 for item in items if item.typed_line is not None)
    _ = stdout.write(
        (
            f"Located the author's line for {located} of {len(items)}"
            f" annotations\n"
        ),
    )
    for scope, label in Constants.scopes:
        row: DictInt = shaped[scope]
        _ = stdout.write(
            f"{label}: {row['correct']} exact spelling + "
            f"{row['equivalent']} equivalent = {row['semantic_exact']} "
            f"same type of {row['to_recover']}, "
            f"{row['wrong']} wrong, {row['missing']} missing\n",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
