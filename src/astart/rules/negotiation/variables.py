"""Annotations for local variables, settled by negotiation."""

from __future__ import annotations

from ast import (
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    FunctionDef,
    Global,
    Name,
    Nonlocal,
    walk,
)
from typing import TYPE_CHECKING, final

from astart.rules.engine_hints import engine_variables
from astart.rules.hints import (
    Hint,
    HintBasis,
    allowed_names,
    escaped_function_names,
    is_allowed_source,
    node_key,
)
from astart.rules.negotiation.builders import build_contracts, walk_functions
from astart.rules.negotiation.negotiator import Negotiation, Negotiator
from astart.rules.negotiation.policy import accept, blocked_nodes
from astart.rules.provable import own_nodes
from astart.stubs import host_resolver

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Mapping

    from astart import CommentedModule
    from astart.rules.engine_hints import LazyConversion
    from astart.rules.hints import Key
    from astart.rules.negotiation.beliefs import Belief
    from astart.rules.negotiation.builders import Built


def _first_assignments(*, module: CommentedModule) -> dict[str, Assign]:
    """Find the first plain assignment of every local, by variable path.

    Args:
        module: Parsed module.

    Returns:
        The first single-target, unannotated ``name = value`` statement of
        each local, skipping names declared ``global`` or ``nonlocal``.

    """
    found: dict[str, Assign] = {}
    for qual, function, _in_class in walk_functions(
        node=module,
        trail=(),
        in_class=False,
    ):
        nodes: list[AST] = list(own_nodes(function=function))
        declared: set[str] = {
            name
            for node in nodes
            if isinstance(node, (Global, Nonlocal))
            for name in node.names
        }
        for node in nodes:
            if (
                isinstance(node, Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], Name)
                and node.targets[0].id not in declared
            ):
                found.setdefault(f"{qual}.{node.targets[0].id}", node)
    return found


def variable_hints(
    *,
    module: CommentedModule,
    engine: Mapping[str, str] | None = None,
) -> dict[Key, Hint]:
    """Find the local variables whose type the evidence proves.

    Args:
        module: Parsed module.
        engine: The inference engine's local annotations by variable path,
            taken only for variables the evidence leaves undecided
            (conversion mode).

    Returns:
        A hint for each assignment statement that can carry an annotation,
        by the statement's node identity.

    """
    built: Built = build_contracts(
        module=module,
        escaped=escaped_function_names(module=module),
        library=host_resolver(),
    )
    result: Negotiation = Negotiator().solve(graph=built.graph)
    blocked: frozenset[str] = blocked_nodes(built=built, result=result)
    known: frozenset[str] = allowed_names(module=module)
    found: dict[Key, Hint] = {}
    for path in sorted(built.variables):
        belief: Belief | None = result.beliefs.get(path)
        if belief is None:
            continue
        verdict: str | None = accept(
            belief=belief,
            kind="variable",
            opaque=blocked,
            corroboration={},
        )
        if verdict is not None and is_allowed_source(
            source=verdict,
            known_names=known,
        ):
            found[node_key(node=built.variables[path])] = Hint(
                source=verdict,
                basis=HintBasis.negotiated,
            )
    candidates: dict[str, AST] = {
        **_first_assignments(module=module),
        **built.variables,
    }
    for path, statement in sorted(candidates.items()):
        key: Key = node_key(node=statement)
        guess: str | None = None if engine is None else engine.get(path)
        if (
            key not in found
            and guess is not None
            and is_allowed_source(source=guess, known_names=known)
        ):
            found[key] = Hint(source=guess, basis=HintBasis.engine)
    return found


@final
class LazyVariables:
    """Negotiate the variable annotations of a module on first use."""

    def __init__(
        self,
        *,
        module: CommentedModule,
        forced: bool,
        conversion: LazyConversion | None = None,
    ) -> None:
        """Remember the module.

        Args:
            module: Parsed module.
            forced: Whether the user asked for variable annotations.
            conversion: The inference engine's output, in conversion mode.

        """
        self._module: CommentedModule = module
        self._forced: bool = forced
        self._conversion: LazyConversion | None = conversion
        self._hints: dict[Key, Hint] | None = None
        self._style: bool | None = None

    @property
    def enabled(self) -> bool:
        """Tell whether variables should be annotated in this module.

        Returns:
            ``True`` when asked for, or when the module already annotates
            some function-local variable (its author's style).

        """
        if self._forced:
            return True
        if self._style is None:
            self._style = any(
                isinstance(inner, AnnAssign) and isinstance(inner.target, Name)
                for function in walk(node=self._module)
                if isinstance(function, (FunctionDef, AsyncFunctionDef))
                for inner in walk(node=function)
            )
        return self._style

    def hint_for(self, *, node: AST) -> Hint | None:
        """Give the annotation justified for an assignment statement.

        Args:
            node: An assignment statement.

        Returns:
            The hint, or ``None``.

        """
        if not self.enabled:
            return None
        if self._hints is None:
            self._hints = variable_hints(
                module=self._module,
                engine=(
                    None
                    if self._conversion is None
                    or self._conversion.text is None
                    else engine_variables(converted=self._conversion.text)
                ),
            )
        return self._hints.get(node_key(node=node))
