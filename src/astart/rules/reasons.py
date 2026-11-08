"""Closed vocabulary of the reasons a fix or hint is not applied."""

from __future__ import annotations

from enum import StrEnum
from typing import final


@final
class SkipCode(StrEnum):
    """Why the runner did not apply a selected fix.

    Attributes:
        subject_missing: The subject could not be located in the final tree.
        conflict: Another fix already edited the same node.
        preconditions_changed: The fix's preconditions no longer held.
        applier_failed: The applier raised.
        write_back: The tree could not be written without reformatting.
        checker_rejected: The external type checker reported a new error.

    """

    subject_missing = "subject-missing"
    conflict = "conflict"
    preconditions_changed = "preconditions-changed"
    applier_failed = "applier-failed"
    write_back = "write-back"
    checker_rejected = "checker-rejected"


@final
class Rejection(StrEnum):
    """Why a type hint was refused.

    The values are the texts reported to users.

    Attributes:
        contains_object: The candidate mentions ``object`` or ``Any``.
        none_default: The parameter defaults to ``None``.
        call_sites_disagree: Call sites pass different types.
        call_sites_unknown: A call site's argument type is unknown.
        declaration_body: The function is a declaration, not an implementation.
        default_disagrees: The default's type differs from the candidate.
        engine_disagrees: The inference differs from the syntax proof.
        escapes: The function is used as a value, so callers are unknown.
        generator: The function is a generator.
        needs_import: The annotation needs an import that cannot be added.
        no_candidate: Nothing proposed a type.
        protocol_mismatch: A protocol dunder's body contradicts the type the
            protocol declares.
        not_provable: The return type is not provable from the syntax.
        uncorroborated: No call site corroborates the candidate.
        tainted: A returned value depends on an unannotated parameter.

    """

    contains_object = "contains object"
    none_default = "None default"
    call_sites_disagree = "call sites disagree"
    call_sites_unknown = "call sites unknown"
    declaration_body = "declaration body"
    default_disagrees = "default disagrees"
    engine_disagrees = "engine disagrees"
    escapes = "escapes as a value"
    generator = "generator"
    needs_import = "needs import or unknown name"
    no_candidate = "no candidate"
    protocol_mismatch = "protocol result differs"
    not_provable = "return type not provable"
    uncorroborated = "uncorroborated"
    tainted = "tainted by parameter"
