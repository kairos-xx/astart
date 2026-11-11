"""Closed vocabulary of the rule ontology."""

from __future__ import annotations

from enum import StrEnum
from typing import Final, final


class Domain(StrEnum):
    """Subject area a rule belongs to.

    Attributes:
        parsing: Source that cannot be parsed.
        suppression: Lint or type-check suppression markers.
        typing: Annotations and typing escape hatches.
        calls: Call-site conventions.
        imports: Import conventions.
        docs: Docstring contracts.
        oop: Method binding and class structure.
        naming: Naming conventions.
        simplification: Behaviour-preserving rewrites.
        whitespace: Blank lines and spacing.
        structure: Module layout.
        config: Project configuration.

    """

    parsing = "parsing"
    suppression = "suppression"
    typing = "typing"
    calls = "calls"
    imports = "imports"
    docs = "docs"
    oop = "oop"
    naming = "naming"
    simplification = "simplification"
    whitespace = "whitespace"
    structure = "structure"
    config = "config"


class Severity(StrEnum):
    """Importance of a finding.

    Attributes:
        error: Blocks a clean run.
        warning: Should be reviewed.
        info: Informational.

    """

    error = "error"
    warning = "warning"
    info = "info"


class Phase(StrEnum):
    """Stage of a run, in execution order.

    Attributes:
        facts: Compute shared facts.
        check: Evaluate rules.
        fix: Apply edits.
        formatting: Hand the result to the formatter (value ``format``).

    """

    facts = "facts"
    check = "check"
    fix = "fix"
    formatting = "format"


class FixSafety(StrEnum):
    """How far a fix may be applied without review.

    Attributes:
        proven: Semantics preserved by construction.
        guarded: Applied only above an inference confidence threshold.
        suggest: Shown but never applied automatically.
        none: No fix exists.

    """

    proven = "proven"
    guarded = "guarded"
    suggest = "suggest"
    none = "none"


class Owner(StrEnum):
    """Tool responsible for a rule.

    Attributes:
        astart: Implemented by astart.
        ruff: Delegated to ruff.

    """

    astart = "astart"
    ruff = "ruff"


class Maturity(StrEnum):
    """Lifecycle stage of a rule.

    Attributes:
        experimental: May change without notice.
        stable: Covered by compatibility promises.
        deprecated: Scheduled for removal.

    """

    experimental = "experimental"
    stable = "stable"
    deprecated = "deprecated"


class Cost(StrEnum):
    """What a fact or rule needs in order to be evaluated.

    Attributes:
        syntactic: A single node.
        scope: Lexical scope resolution.
        semantic: Inference over the module.
        project: Several modules.

    """

    syntactic = "syntactic"
    scope = "scope"
    semantic = "semantic"
    project = "project"

    def rank(self) -> int:
        """Return the position of this cost in the ordering.

        Returns:
            int: Zero for syntactic up to three for project.

        """
        return Constants.cost_order.index(self)


class Expressible(StrEnum):
    """How a rule trigger is expressed.

    Attributes:
        declarative: A predicate stored as data.
        procedural: A registered procedure.

    """

    declarative = "declarative"
    procedural = "procedural"


@final
class Constants:
    """Group module-level constants.

    Attributes:
        cost_order (Final[tuple[Cost, ...]]): Grouped module constant.

    """

    cost_order: Final[tuple[Cost, ...]] = (
        Cost.syntactic,
        Cost.scope,
        Cost.semantic,
        Cost.project,
    )
