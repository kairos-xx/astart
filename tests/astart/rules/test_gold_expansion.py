"""Expanded gold set: evidence-ladder expectations over 500 typed cases.

Each case carries a ``family`` naming the failure class it exercises
(``default_literal``, ``call_sites``, ``tainted``…). Expectations are
written from typed ground truth -- the annotation a type checker would
accept -- not from whatever the tool happens to emit today. A ``None``
expectation encodes a required refusal under the evidence ladder.

"""

from __future__ import annotations

from ast import (
    AsyncFunctionDef,
    FunctionDef,
    arg,
    unparse,
    walk,
)
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final, final

import pytest
from astart import parse
from astart.rules import FixResult, default_registries
from astart.rules.catalog import load_default_catalog
from astart.rules.hints import Hint, HintIndex
from astart.rules.runner import FixSettings, fix_source
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal, expect_true

type DictStrOrNone = dict[str, str | None]

if TYPE_CHECKING:
    from astart.rules.checker import Checker
    from astart.rules.model import Catalog
    from astart.rules.registry import Registries
    from astart.source.ast import CommentedModule


@final
class Constants:
    """Group module-level constants.

    Attributes:
        minimum_cases (Final[int]): How many gold cases the expanded set must
            hold.
        cases (Final[list[Case]]): Grouped module constant.
        scalars (Final[tuple[tuple[str, str], ...]]): Grouped module constant.
        sites (Final[tuple[tuple[str, str], ...]]): Grouped module constant.
        disagree_pairs (Final[tuple[tuple[str, str], ...]]): Grouped module
            constant.
        union_spellings (Final[dict[tuple[str, str], str]]): Grouped module
            constant.
        annotation_fixes (Final[frozenset[str]]): Grouped module constant.
        fix_registries (Final[Registries]): Grouped module constant.
        fix_expected (Final[dict[str, dict[str, str | None]]]): Grouped module
            constant.
        negotiated_adds (Final[dict[tuple[str, str], str]]): Grouped module
            constant.

    """

    minimum_cases: Final[int] = 500

    cases: Final[list[Case]] = []

    # -------------------------------------------------------------------------
    # Typed ground truth literals.
    # -------------------------------------------------------------------------

    # Scalar literals the engine accepts as default evidence.
    scalars: Final[tuple[tuple[str, str], ...]] = (
        ("0", "int"),
        ("1", "int"),
        ("0x10", "int"),
        ("1_000", "int"),
        ("1.5", "float"),
        ("0.0", "float"),
        ("1e3", "float"),
        ("'a'", "str"),
        ("'hello'", "str"),
        ("''", "str"),
        ("True", "bool"),
        ("False", "bool"),
    )

    # Literal call-site arguments with their proven types.
    sites: Final[tuple[tuple[str, str], ...]] = (
        ("1", "int"),
        ("-2", "int"),
        ("0x10", "int"),
        ("1.5", "float"),
        ("2e9", "float"),
        ("'a'", "str"),
        ("''", "str"),
        ("True", "bool"),
        ("False", "bool"),
        ("b'ab'", "bytes"),
        ("b''", "bytes"),
        ("[1, 2]", "list[int]"),
        ("[1.5, 2.5]", "list[float]"),
        ("['a', 'b']", "list[str]"),
        ("[True]", "list[bool]"),
        ("[[1]]", "list[list[int]]"),
        ("{'a': 1}", "dict[str, int]"),
        ("{'a': 1.5}", "dict[str, float]"),
        ("{1: 'a'}", "dict[int, str]"),
        ("{'a': 'b'}", "dict[str, str]"),
        ("{1, 2}", "set[int]"),
        ("{'a', 'b'}", "set[str]"),
        ("{True}", "set[bool]"),
        ("None", "None"),
    )

    # -------------------------------------------------------------------------
    # call_sites_disagree / call_sites_unknown / default_disagrees.
    # -------------------------------------------------------------------------

    disagree_pairs: Final[tuple[tuple[str, str], ...]] = (
        ("1", "'a'"),
        ("1", "1.5"),
        ("True", "1"),
        ("1", "None"),
        ("'a'", "[1]"),
        ("[1]", "{'a': 1}"),
        ("1.5", "b'x'"),
        ("{1}", "[1]"),
        ("None", "'a'"),
        ("0.0", "0"),
    )

    union_spellings: Final[dict[tuple[str, str], str]] = {
        ("1", "'a'"): "int | str",
        ("True", "1"): "int",
        ("'a'", "[1]"): "str | list[int]",
        ("[1]", "{'a': 1}"): "dict[str, int] | list[int]",
        ("1.5", "b'x'"): "float | bytes",
        ("{1}", "[1]"): "list[int] | set[int]",
    }

    # -------------------------------------------------------------------------
    # M1-17: the same cases asserted through ``fix_source``.
    # -------------------------------------------------------------------------

    # Only the fixes that write a hint's own source are kept: ``synthesize-*``
    # legitimately generalize beyond the hint (e.g. ``def f(p): return p``
    # becomes ``T``), ``calls.add-keywords`` rewrites call sites between
    # rounds, and ``add-final`` targets module constants -- none are what the
    # gold expectation measures. What remains exercises applier, import
    # insertion and write-back on exactly the hinted annotations.
    annotation_fixes: Final[frozenset[str]] = frozenset(
        {
            "typing.add-none-return",
            "typing.add-noreturn",
            "typing.add-inferred-annotation",
        },
    )

    fix_registries: Final[Registries] = default_registries()

    # ``fix_source`` iterates to a fixed point, so a parameter annotation can
    # unlock a return proof that the single-pass hint index must refuse.  These
    # overrides record the converged expectation; every other case reuses its
    # hint-level ``expected`` map unchanged.
    fix_expected: Final[dict[str, dict[str, str | None]]] = {
        "call_sites/repr-site": {"f": "str", "f.p": "str"},
        "call_sites_unknown/abs-site": {"f": "int", "f.p": "int"},
    }

    # Annotations the contract negotiator writes where the hint index writes
    # none. Each was reviewed; anything not listed here fails the superset test
    # below.
    negotiated_adds: Final[dict[tuple[str, str], str]] = {
        ("attribute_read/conflicting-writes", "get"): "int | str",
        ("call_sites/arith-bool", "f"): "int",
        ("call_sites_disagree/identity/1-None", "f.p"): "int | None",
        ("call_sites_disagree/identity/None-'a'", "f.p"): "str | None",
        ("call_sites_disagree/len/1-None", "f.p"): "int | None",
        ("call_sites_disagree/len/None-'a'", "f.p"): "str | None",
        ("control_flow/if-else-diff", "f"): "int | str",
        ("control_flow/try-diff", "f"): "int | str",
        ("default_literal/add-self/bool", "f"): "int",
        ("method_binding/self-call", "n"): "int",
        ("method_binding/self-chain", "n"): "int",
        ("typed_flow/annotated-chain", "g"): "int",
        ("typed_flow/callee-return", "g"): "int",
        ("typed_flow/deep-chain", "g"): "int",
        ("typed_flow/deep-chain", "h"): "int",
        ("typed_flow/hinted-chain", "g"): "int",
        ("typed_flow/none-ann", "f"): "int | None",
        ("unresolved/mutual", "f"): "int",
        ("unresolved/mutual", "f.n"): "int",
        ("unresolved/mutual", "g"): "int",
        ("unresolved/mutual", "g.n"): "int",
        ("unresolved/recursive", "f"): "int",
        ("unresolved/recursive", "f.n"): "int",
        ("variadic/star-unpacked-call", "run"): "int",
    }


@final
@dataclass(frozen=True, slots=True)
class Case:
    """One gold expectation: name, failure-class family, source, hints.

    Attributes:
        name (str): Unique case identifier.
        family (str): Failure class the case exercises.
        source (str): Module source under test.
        expected (DictStrOrNone): Expected hint per subject; ``None`` requires
            refusal.

    """

    name: str
    family: str
    source: str
    expected: DictStrOrNone


def _case(
    name: str,
    family: str,
    source: str,
    expected: DictStrOrNone,
) -> None:
    """Register one gold case.

    Args:
        name (str): Unique case identifier.
        family (str): Failure class the case exercises.
        source (str): Module source under test.
        expected (DictStrOrNone): Expected hint per subject; ``None`` requires
            refusal.

    """
    Constants.cases.append(
        Case(name=name, family=family, source=source, expected=expected),
    )


def _hints(source: str) -> DictStrOrNone:
    """Collect ``hint_for`` outputs for unannotated subjects.

    Args:
        source (str): Module source to inspect.

    Returns:
        DictStrOrNone: Hint source per unannotated subject name.

    """
    module: CommentedModule = parse(source=source, filename="gold.py")
    index: HintIndex = HintIndex.create(module=module, stubs_path=None)
    resolved: DictStrOrNone = {}
    for node in walk(node=module):
        if not isinstance(node, (FunctionDef, AsyncFunctionDef)):
            continue
        if node.returns is None:
            hint: Hint | None = index.hint_for(node=node)
            resolved[node.name] = None if hint is None else hint.source
        parameters: tuple[arg, ...] = (
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
            *(
                item
                for item in (node.args.vararg, node.args.kwarg)
                if item is not None
            ),
        )
        for parameter in parameters:
            if parameter.arg in {"self", "cls"}:
                continue
            if parameter.annotation is not None:
                continue
            hint = index.hint_for(node=parameter)
            key: str = f"{node.name}.{parameter.arg}"
            resolved[key] = None if hint is None else hint.source
    return resolved


def _def(
    name: str,
    params: str,
    body: str,
    calls: str = "",
) -> str:
    """Assemble a module source.

    Args:
        name (str): Function name.
        params (str): Parameter list text.
        body (str): Function body text.
        calls (str): Optional trailing call-site text.

    Returns:
        str: The assembled module source.

    """
    tail: str = f"\n\n\n{calls}" if calls else ""
    return f"def {name}({params}):\n    {body}\n{tail}"


def _src(*lines: str) -> str:
    """Join line fragments into one source text.

    Args:
        lines (str): Source fragments, concatenated verbatim.

    Returns:
        str: The joined source text.

    """
    return "".join(lines)


# ---------------------------------------------------------------------------
# default_literal: scalar defaults pin the type (ladder step 2).
# ---------------------------------------------------------------------------


def _default_literal_cases() -> None:
    """Register default-literal evidence cases.."""
    family: str = "default_literal"
    for literal, type_name in Constants.scalars:
        both: DictStrOrNone = {
            "f": type_name,
            "f.p": type_name,
        }
        _case(
            name=f"{family}/positional/{literal}",
            family=family,
            source=_def(name="f", params=f"p={literal}", body="return p"),
            expected=both,
        )
        _case(
            name=f"{family}/kwonly/{literal}",
            family=family,
            source=_def(name="f", params=f"*, p={literal}", body="return p"),
            expected=both,
        )
        _case(
            name=f"{family}/posonly/{literal}",
            family=family,
            source=_def(name="f", params=f"p={literal}, /", body="return p"),
            expected=both,
        )
        _case(
            name=f"{family}/async/{literal}",
            family=family,
            source=_src(
                f"async def f(p={literal}):\n",
                """\
    return p
""",
            ),
            expected=both,
        )
        _case(
            name=f"{family}/method/{literal}",
            family=family,
            source=_src(
                """\
class K:
""",
                f"    def m(self, p={literal}):\n",
                """\
        return p
""",
            ),
            expected={"m": type_name, "m.p": type_name},
        )
        _case(
            name=f"{family}/procedure/{literal}",
            family=family,
            source=_def(name="f", params=f"p={literal}", body="print(p)"),
            expected={"f": "None", "f.p": type_name},
        )
        _case(
            name=f"{family}/call-agrees/{literal}",
            family=family,
            source=_def(
                name="f",
                params=f"p={literal}",
                body="return p",
                calls=f"f({literal})\n",
            ),
            expected=both,
        )
        _case(
            name=f"{family}/return-const/{literal}",
            family=family,
            source=_def(
                name="f",
                params=f"p={literal}",
                body=f"return {literal}",
            ),
            expected=both,
        )
    pairs: tuple[tuple[tuple[str, str], tuple[str, str]], ...] = (
        (("1", "int"), ("'a'", "str")),
        (("1.5", "float"), ("True", "bool")),
        (("'a'", "str"), ("1", "int")),
        (("True", "bool"), ("1.5", "float")),
        (("0", "int"), ("''", "str")),
        (("False", "bool"), ("0.0", "float")),
    )
    for (lit_a, ta), (lit_b, tb) in pairs:
        _case(
            name=f"{family}/two-params/{ta}-{tb}",
            family=family,
            source=_def(
                name="f",
                params=f"a={lit_a}, b={lit_b}",
                body="return a",
            ),
            expected={"f": ta, "f.a": ta, "f.b": tb},
        )
    refused: tuple[tuple[str, str], ...] = (
        ("b'ab'", "bytes"),
        ("[]", "empty-list"),
        ("()", "empty-tuple"),
        ("{}", "empty-dict"),
        ("list", "name"),
        ("None", "none"),
    )
    for literal, tag in (("-1", "negated"), ("len([])", "call")):
        _case(
            name=f"default_expression/{tag}",
            family="default_expression",
            source=_def(name="f", params=f"p={literal}", body="return p"),
            expected={"f": "int", "f.p": "int"},
        )
    for literal, tag in refused:
        _case(
            name=f"default_refused/{tag}",
            family="default_refused",
            source=_def(name="f", params=f"p={literal}", body="return p"),
            expected={"f": None, "f.p": None},
        )


# ---------------------------------------------------------------------------
# call_sites: definite, agreeing call-site evidence pins the type.
# ---------------------------------------------------------------------------


def _call_site_cases() -> None:
    """Register call-site evidence cases.."""
    family: str = "call_sites"
    for literal, type_name in Constants.sites:
        _case(
            name=f"{family}/identity/{literal}",
            family=family,
            source=_def(
                name="f",
                params="p",
                body="return p",
                calls=f"f({literal})\n",
            ),
            expected={"f": type_name, "f.p": type_name},
        )
        _case(
            name=f"{family}/len/{literal}",
            family=family,
            source=_def(
                name="f",
                params="p",
                body="return len(p)",
                calls=f"f({literal})\n",
            ),
            expected={"f": "int", "f.p": type_name},
        )
        _case(
            name=f"{family}/compare/{literal}",
            family=family,
            source=_def(
                name="f",
                params="p",
                body="return p > 0",
                calls=f"f({literal})\n",
            ),
            expected={"f": "bool", "f.p": type_name},
        )
        _case(
            name=f"{family}/keyword/{literal}",
            family=family,
            source=_def(
                name="f",
                params="p, q='d'",
                body="return p",
                calls=f"f(p={literal})\n",
            ),
            expected={"f": type_name, "f.p": type_name, "f.q": "str"},
        )
        _case(
            name=f"{family}/procedure/{literal}",
            family=family,
            source=_def(
                name="f",
                params="p",
                body="print(p)",
                calls=f"f({literal})\n",
            ),
            expected={"f": "None", "f.p": type_name},
        )
        _case(
            name=f"{family}/multi-site/{literal}",
            family=family,
            source=_def(
                name="f",
                params="p",
                body="return p",
                calls=f"f({literal})\nf({literal})\n",
            ),
            expected={"f": type_name, "f.p": type_name},
        )
    _case(
        name=f"{family}/two-args",
        family=family,
        source=_def(
            name="f",
            params="a, b",
            body="return a",
            calls="""\
f(1, 'x')
""",
        ),
        expected={"f": "int", "f.a": "int", "f.b": "str"},
    )
    _case(
        name=f"{family}/kw-and-pos",
        family=family,
        source=_def(
            name="f",
            params="a, b",
            body="return a",
            calls="""\
f(b='x', a=1)
""",
        ),
        expected={"f": "int", "f.a": "int", "f.b": "str"},
    )
    _case(
        name=f"{family}/three-args",
        family=family,
        source=_def(
            name="f",
            params="a, b, c",
            body="return a",
            calls="""\
f(1, 'x', 2.5)
""",
        ),
        expected={"f": "int", "f.a": "int", "f.b": "str", "f.c": "float"},
    )
    _case(
        name=f"{family}/method-attr",
        family=family,
        source=_src(
            """\
class K:
""",
            """\
    def m(self, a):
""",
            """\
        return a


""",
            """\
k = K()
k.m(1)
""",
        ),
        expected={"m": "int", "m.a": "int"},
    )
    _case(
        name=f"{family}/method-temp",
        family=family,
        source=_src(
            """\
class K:
""",
            """\
    def m(self, a):
""",
            """\
        return a


""",
            """\
K().m(1)
""",
        ),
        expected={"m": "int", "m.a": "int"},
    )
    _case(
        name=f"{family}/staticmethod",
        family=family,
        source=_src(
            """\
class K:
""",
            """\
    @staticmethod
""",
            """\
    def m(a):
""",
            """\
        return a


""",
            """\
K.m(1)
""",
        ),
        expected={"m": "int", "m.a": "int"},
    )
    _case(
        name=f"{family}/list-display",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return [p]",
            calls="""\
f(1)
""",
        ),
        expected={"f": "list[int]", "f.p": "int"},
    )
    _case(
        name=f"{family}/dict-display",
        family=family,
        source=_def(
            name="f",
            params="k, v",
            body="return {k: v}",
            calls="""\
f('a', 1)
""",
        ),
        expected={"f": "dict[str, int]", "f.k": "str", "f.v": "int"},
    )
    _case(
        name=f"{family}/tuple-display",
        family=family,
        source=_def(
            name="f",
            params="a, b",
            body="return (a, b)",
            calls="""\
f(1, 'x')
""",
        ),
        expected={"f": "tuple[int, str]", "f.a": "int", "f.b": "str"},
    )
    _case(
        name=f"{family}/convert-str",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return str(p)",
            calls="""\
f(1)
""",
        ),
        expected={"f": "str", "f.p": "int"},
    )
    _case(
        name=f"{family}/convert-int",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return int(p)",
            calls="""\
f('3')
""",
        ),
        expected={"f": "int", "f.p": "str"},
    )
    _case(
        name=f"{family}/arith-int",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p + 1",
            calls="""\
f(1)
""",
        ),
        expected={"f": "int", "f.p": "int"},
    )
    _case(
        name=f"{family}/arith-float",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p + 1",
            calls="""\
f(1.5)
""",
        ),
        expected={"f": "float", "f.p": "float"},
    )
    _case(
        name=f"{family}/arith-bool",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p + 1",
            calls="""\
f(True)
""",
        ),
        expected={"f": None, "f.p": "bool"},
    )
    _case(
        name=f"{family}/unary",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return -p",
            calls="""\
f(1)
""",
        ),
        expected={"f": "int", "f.p": "int"},
    )
    _case(
        name=f"{family}/not",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return not p",
            calls="""\
f(1)
""",
        ),
        expected={"f": "bool", "f.p": "int"},
    )
    _case(
        name=f"{family}/equality",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p == 0",
            calls="""\
f(1)
""",
        ),
        expected={"f": "bool", "f.p": "int"},
    )
    _case(
        name=f"{family}/is-none",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p is None",
            calls="""\
f(1)
""",
        ),
        expected={"f": "bool", "f.p": None},
    )
    _case(
        name=f"{family}/augassign",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="""\
p += 1
    return p""",
            calls="""\
f(1)
""",
        ),
        expected={"f": "int", "f.p": "int"},
    )
    _case(
        name=f"{family}/chained",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="""\
y = p
    return y""",
            calls="""\
f(1)
""",
        ),
        expected={"f": "int", "f.p": "int"},
    )
    for call, site_type in (
        ("int('1')", "int"),
        ("str(1)", "str"),
        ("len([1])", "int"),
        ("bool(0)", "bool"),
        ("float(1)", "float"),
        ("1 + 2", "int"),
        ("'a' 'b'", "str"),
        ("(1)", "int"),
    ):
        _case(
            name=f"{family}/site-expr/{call}",
            family=family,
            source=_def(
                name="f",
                params="p",
                body="return p",
                calls=f"f({call})\n",
            ),
            expected={"f": site_type, "f.p": site_type},
        )
    _case(
        name=f"{family}/repr-site",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p",
            calls="""\
f(repr(1))
""",
        ),
        expected={"f": None, "f.p": "str"},
    )
    _case(
        name=f"{family}/default-and-site",
        family=family,
        source=_def(
            name="f",
            params="q, p=1",
            body="return p",
            calls="""\
f('x', 2)
""",
        ),
        expected={"f": "int", "f.q": "str", "f.p": "int"},
    )


"""Pairs whose engine candidate is exactly the union of both sites."""


def _disagree_cases() -> None:
    """Register disagreeing-evidence cases: refusal unless a union is shown."""
    family: str = "call_sites_disagree"
    for left, right in Constants.disagree_pairs:
        tag: str = f"{left}-{right}"
        union: str | None = Constants.union_spellings.get((left, right))
        _case(
            name=f"{family}/identity/{tag}",
            family=family,
            source=_def(
                name="f",
                params="p",
                body="return p",
                calls=f"f({left})\nf({right})\n",
            ),
            expected={
                "f": None if tag == "True-1" else union,
                "f.p": union,
            },
        )
        _case(
            name=f"{family}/len/{tag}",
            family=family,
            source=_def(
                name="f",
                params="p",
                body="return len(p)",
                calls=f"f({left})\nf({right})\n",
            ),
            expected={"f": "int", "f.p": union},
        )
    _case(
        name=f"{family}/three-sites",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p",
            calls="""\
f(1)
f(2)
f('a')
""",
        ),
        expected={"f": "int | str", "f.p": "int | str"},
    )
    family = "call_sites_unknown"
    _case(
        name=f"{family}/tuple-site",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return len(p)",
            calls="""\
f((1, 2))
""",
        ),
        expected={"f": "int", "f.p": None},
    )
    _case(
        name=f"{family}/empty-list",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p",
            calls="""\
f([])
""",
        ),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/empty-dict",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p",
            calls="""\
f({})
""",
        ),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/empty-set",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p",
            calls="""\
f(set())
""",
        ),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/complex-site",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p",
            calls="""\
f(1j)
""",
        ),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/unknown-callee",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p",
            calls="""\
f(g())
""",
        ),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/attr-site",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p",
            calls="""\
f(obj.x)
""",
        ),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/name-site",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p",
            calls="""\
f(other)
""",
        ),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/abs-site",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p",
            calls="""\
f(abs(1))
""",
        ),
        expected={"f": None, "f.p": "int"},
    )
    _case(
        name=f"{family}/list-call-site",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p",
            calls="""\
f(list([1]))
""",
        ),
        expected={"f": "list[int]", "f.p": "list[int]"},
    )
    _case(
        name=f"{family}/sorted-site",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p",
            calls="""\
f(sorted([1]))
""",
        ),
        expected={"f": "list[int]", "f.p": "list[int]"},
    )
    _case(
        name=f"{family}/method-site",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return p",
            calls="""\
f('a'.upper())
""",
        ),
        expected={"f": "str", "f.p": "str"},
    )
    _case(
        name=f"{family}/subscript-site",
        family=family,
        source=_src(
            """\
def f(p):
    return p


""",
            """\
xs = [1]
f(xs[0])
""",
        ),
        expected={"f": None, "f.p": None},
    )
    family = "default_disagrees"
    for default, call in (
        ("1", "2.5"),
        ("1", "'a'"),
        ("'a'", "1"),
        ("1.5", "True"),
        ("True", "2.5"),
        ("'x'", "b'y'"),
        ("0", "None"),
        ("1.5", "'x'"),
    ):
        _case(
            name=f"{family}/{default}-vs-{call}",
            family=family,
            source=_def(
                name="f",
                params=f"p={default}",
                body="return p",
                calls=f"f({call})\n",
            ),
            expected={"f": None, "f.p": None},
        )


# ---------------------------------------------------------------------------
# none_default / uncorroborated / tainted.
# ---------------------------------------------------------------------------


def _evidence_gap_cases() -> None:
    """Register cases where evidence is missing.."""
    family: str = "none_default"
    _case(
        name=f"{family}/positional",
        family=family,
        source=_def(name="f", params="p=None", body="return p"),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/with-site",
        family=family,
        source=_def(
            name="f",
            params="p=None",
            body="return p",
            calls="""\
f(1)
""",
        ),
        expected={"f": None, "f.p": "int | None"},
    )
    _case(
        name=f"{family}/kwonly",
        family=family,
        source=_def(name="f", params="*, p=None", body="return p"),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/sibling",
        family=family,
        source=_def(name="f", params="p=None, q=1", body="return q"),
        expected={"f": "int", "f.p": None, "f.q": "int"},
    )
    _case(
        name=f"{family}/procedure",
        family=family,
        source=_def(name="f", params="p=None", body="print(p)"),
        expected={"f": "None", "f.p": None},
    )
    _case(
        name=f"{family}/method",
        family=family,
        source=_src(
            """\
class K:
""",
            """\
    def m(self, a=None):
""",
            """\
        return a
""",
        ),
        expected={"m": None, "m.a": None},
    )
    family = "uncorroborated"
    bodies: tuple[tuple[str, str, str | None], ...] = (
        ("return-len", "return len(p)", "int"),
        ("return-compare", "return p > 0", "bool"),
        ("return-not", "return not p", "bool"),
        ("return-self", "return p", None),
        ("return-str", "return str(p)", "str"),
        ("return-abs", "return abs(p)", None),
        ("procedure-print", "print(p)", "None"),
        ("unused", "return 0", "int"),
    )
    for tag, body, ret in bodies:
        _case(
            name=f"{family}/{tag}",
            family=family,
            source=_def(name="f", params="p", body=body),
            expected={"f": ret, "f.p": None},
        )
    _case(
        name=f"{family}/two-params",
        family=family,
        source=_def(name="f", params="a, b", body="return a"),
        expected={"f": None, "f.a": None, "f.b": None},
    )
    _case(
        name=f"{family}/kwonly",
        family=family,
        source=_def(name="f", params="*, p", body="return p"),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/method",
        family=family,
        source=_src(
            """\
class K:
""",
            """\
    def m(self, a):
""",
            """\
        return a
""",
        ),
        expected={"m": None, "m.a": None},
    )
    _case(
        name=f"{family}/posonly",
        family=family,
        source=_def(name="f", params="p, /", body="return p"),
        expected={"f": None, "f.p": None},
    )
    family = "tainted"
    _case(
        name=f"{family}/assign",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="""\
y = p * 2
    return y""",
        ),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/fstring",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return f'{p}'",
            calls="""\
f(1)
""",
        ),
        expected={"f": "str", "f.p": "int"},
    )
    _case(
        name=f"{family}/nested",
        family=family,
        source=_src(
            """\
def f(p):
""",
            """\
    def g(q):
""",
            """\
        return q
""",
            """\
    return g(p)


f(1)
""",
        ),
        expected={"f": None, "f.p": "int", "g": None, "g.q": None},
    )
    _case(
        name=f"{family}/comprehension",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="return [x for x in p]",
            calls="""\
f([1])
""",
        ),
        expected={"f": "list[int]", "f.p": "list[int]"},
    )


# ---------------------------------------------------------------------------
# proven_return / proven_none: provable returns on typed ground truth.
# ---------------------------------------------------------------------------


def _proven_return_cases() -> None:
    """Register proven-return-type cases.."""
    family: str = "proven_return"
    int_exprs: tuple[tuple[str, str, str], ...] = (
        ("add", "a + 1", "int"),
        ("sub", "a - 1", "int"),
        ("mul", "a * 2", "int"),
        ("truediv", "a / 2", "float"),
        ("floordiv", "a // 2", "int"),
        ("mod", "a % 2", "int"),
        ("compare", "a > 0", "bool"),
        ("eq", "a == 0", "bool"),
        ("not", "not a", "bool"),
        ("str", "str(a)", "str"),
        ("int", "int(a)", "int"),
        ("float", "float(a)", "float"),
        ("bool", "bool(a)", "bool"),
        ("len-list", "len([a])", "int"),
        ("list", "[a]", "list[int]"),
        ("list-2", "[a, a]", "list[int]"),
        ("tuple", "(a, a)", "tuple[int, int]"),
        ("tuple-1", "(a,)", "tuple[int]"),
        ("dict", "{a: a}", "dict[int, int]"),
        ("dict-lit", "{a: 1}", "dict[int, int]"),
        ("set", "{a}", "set[int]"),
        ("neg", "-a", "int"),
        ("pos", "+a", "int"),
        ("invert", "~a", "int"),
        ("boolop-and", "a and a", "int"),
        ("boolop-or", "a or a", "int"),
        ("ifexp", "a if a else 0", "int"),
        ("paren", "(a)", "int"),
        ("const", "7", "int"),
        ("const-float", "7.5", "float"),
        ("const-str", "'x'", "str"),
        ("const-none", "None", "None"),
        ("nested-list", "[[a]]", "list[list[int]]"),
    )
    for tag, expr, ret in int_exprs:
        _case(
            name=f"{family}/int/{tag}",
            family=family,
            source=f"def f(a: int):\n    return {expr}\n",
            expected={"f": ret},
        )
    str_exprs: tuple[tuple[str, str, str], ...] = (
        ("concat", "a + 'x'", "str"),
        ("mul", "a * 2", "str"),
        ("len", "len(a)", "int"),
        ("eq", "a == 'x'", "bool"),
        ("boolop", "a or 'x'", "str"),
        ("identity", "a", "str"),
        ("convert", "str(a)", "str"),
        ("in", "'x' in a", "bool"),
    )
    for tag, expr, ret in str_exprs:
        _case(
            name=f"{family}/str/{tag}",
            family=family,
            source=f"def f(a: str):\n    return {expr}\n",
            expected={"f": ret},
        )
    _case(
        name=f"{family}/two-params",
        family=family,
        source="""\
def f(a: int, b: str):
    return (a, b)
""",
        expected={"f": "tuple[int, str]"},
    )
    _case(
        name=f"{family}/conditional",
        family=family,
        source=_src(
            """\
def f(a: int):
""",
            """\
    if a:
""",
            """\
        return 1
""",
            """\
    return 2
""",
        ),
        expected={"f": "int"},
    )
    _case(
        name=f"{family}/mixed-annotated",
        family=family,
        source=_src(
            """\
def f(a: int, b):
""",
            """\
    return a


f(1, 'x')
""",
        ),
        expected={"f": "int", "f.b": "str"},
    )
    family = "proven_none"
    for tag, body in (
        ("print", "print(p)"),
        ("assign", "y = p"),
        (
            "for-loop",
            """\
for x in p:
        print(x)""",
        ),
        (
            "while",
            """\
while p:
        break""",
        ),
        ("expr", "p"),
        ("append", "p.append(1)"),
        (
            "if-print",
            """\
if p:
        print(p)""",
        ),
    ):
        _case(
            name=f"{family}/{tag}",
            family=family,
            source=_def(name="f", params="p", body=body),
            expected={"f": "None", "f.p": None},
        )
    _case(
        name=f"{family}/try",
        family=family,
        source=_src(
            """\
def f(p):
""",
            """\
    try:
""",
            """\
        print(p)
""",
            """\
    except ValueError:
""",
            """\
        pass
""",
        ),
        expected={"f": "None", "f.p": None},
    )
    for tag, body in (
        ("print", "print(p)"),
        ("assign", "y = p"),
        (
            "for-loop",
            """\
for x in p:
        print(x)""",
        ),
    ):
        _case(
            name=f"{family}/sited-{tag}",
            family=family,
            source=_def(
                name="f",
                params="p",
                body=body,
                calls="""\
f(1)
""",
            ),
            expected={"f": "None", "f.p": "int"},
        )


# ---------------------------------------------------------------------------
# Refusal families: generator, declaration, escapes, redefinition.
# ---------------------------------------------------------------------------


def _refusal_cases() -> None:
    """Register cases that must refuse a hint.."""
    family: str = "generator"
    for tag, body in (
        ("bare", "yield p"),
        (
            "loop",
            """\
for x in p:
        yield x""",
        ),
        ("yield-from", "yield from p"),
        (
            "gen-return",
            """\
yield p
    return""",
        ),
    ):
        _case(
            name=f"{family}/{tag}",
            family=family,
            source=_def(name="f", params="p", body=body),
            expected={"f": None, "f.p": None},
        )
    family = "declaration"
    for tag, body in (
        ("ellipsis", "..."),
        ("pass", "pass"),
        ("docstring", '"""Doc."""\n    ...'),
        ("raise-ni", "raise NotImplementedError"),
        ("raise-ni-call", "raise NotImplementedError('x')"),
    ):
        _case(
            name=f"{family}/{tag}",
            family=family,
            source=_def(name="f", params="p", body=body),
            expected={"f": None, "f.p": None},
        )
    _case(
        name=f"{family}/overload",
        family=family,
        source=_src(
            """\
from typing import overload


""",
            """\
@overload
def f(p):
    ...
""",
        ),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/abstractmethod",
        family=family,
        source=_src(
            """\
import abc


""",
            """\
class K(abc.ABC):
""",
            """\
    @abc.abstractmethod
""",
            """\
    def m(self, a):
        ...
""",
        ),
        expected={"m": None, "m.a": None},
    )
    family = "escape"
    escapes: tuple[tuple[str, str], ...] = (
        ("alias", "g = f"),
        ("map", "list(map(f, [1]))"),
        ("list", "handlers = [f]"),
        ("dict", "handlers = {'go': f}"),
        ("tuple", "handlers = (f,)"),
        ("set", "handlers = {f}"),
        ("del", "del f"),
    )
    for tag, tail in escapes:
        _case(
            name=f"{family}/{tag}",
            family=family,
            source=_def(
                name="f",
                params="p",
                body="return p",
                calls=f"f(1)\n{tail}\n",
            ),
            expected={"f": None, "f.p": None},
        )
    _case(
        name=f"{family}/partial",
        family=family,
        source=_src(
            """\
import functools


""",
            """\
def f(p):
    return p


""",
            """\
q = functools.partial(f)
f(1)
""",
        ),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/callback",
        family=family,
        source=_src(
            """\
def other(fn):
    fn(1)


""",
            """\
def f(p):
    return p


""",
            """\
f(1)
other(f)
""",
        ),
        expected={
            "f": None,
            "f.p": None,
            "other": "None",
            "other.fn": None,
        },
    )
    _case(
        name=f"{family}/returned",
        family=family,
        source=_src(
            """\
def f(p):
    return p


""",
            """\
def g():
    return f


f(1)
""",
        ),
        expected={"f": None, "f.p": None, "g": None},
    )
    _case(
        name=f"{family}/decorated",
        family=family,
        source=_src(
            """\
def deco(fn):
    return fn


""",
            """\
@deco
def f(p):
    return p


f(1)
""",
        ),
        expected={
            "deco": None,
            "deco.fn": None,
            "f": None,
            "f.p": None,
        },
    )
    family = "unresolved"
    _case(
        name=f"{family}/shadowed",
        family=family,
        source=_src(
            """\
def f(p):
    return p


""",
            """\
def f(p):
    return p + 1


f(1)
""",
        ),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/conditional-def",
        family=family,
        source=_src(
            """\
if True:
""",
            """\
    def f(p):
        return p
""",
            """\
else:
""",
            """\
    def f(p):
        return p + 1


f(1)
""",
        ),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/recursive",
        family=family,
        source=_src(
            """\
def f(n):
""",
            """\
    if n:
        return f(n - 1)
""",
            """\
    return 0


f(3)
""",
        ),
        expected={"f": None, "f.n": None},
    )
    _case(
        name=f"{family}/mutual",
        family=family,
        source=_src(
            """\
def f(n):
""",
            """\
    if n:
        return g(n - 1)
""",
            """\
    return 0


""",
            """\
def g(n):
""",
            """\
    if n:
        return f(n - 1)
""",
            """\
    return 1


f(3)
""",
        ),
        expected={"f": None, "f.n": None, "g": None, "g.n": None},
    )
    _case(
        name=f"{family}/lambda-ref",
        family=family,
        source=_src(
            """\
def f(p):
    return p


""",
            """\
apply = lambda fn: fn(1)
apply(f)
""",
        ),
        expected={"f": None, "f.p": None},
    )


# ---------------------------------------------------------------------------
# imports / typed_flow / control_flow / method_binding families.
# ---------------------------------------------------------------------------


def _flow_cases() -> None:
    """Register control-flow and scope cases.."""
    family: str = "imported_site"
    _case(
        name=f"{family}/path",
        family=family,
        source=_src(
            """\
from pathlib import Path

""",
            """\
def f(p):
    return p


f(Path('a'))
""",
        ),
        expected={"f": "Path", "f.p": "Path"},
    )
    _case(
        name=f"{family}/deque",
        family=family,
        source=_src(
            """\
from collections import deque

""",
            """\
def f(p):
    return p


f(deque([1]))
""",
        ),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/namedtuple",
        family=family,
        source=_src(
            """\
from collections import namedtuple
""",
            """\
P = namedtuple('P', 'x')


""",
            """\
def f(p):
    return p


f(P(1))
""",
        ),
        expected={"f": None, "f.p": None},
    )
    _case(
        name=f"{family}/unimported",
        family=family,
        source=_src(
            """\
def f(p):
    return p


f(Path('a'))
""",
        ),
        expected={"f": None, "f.p": None},
    )
    family = "typed_flow"
    _case(
        name=f"{family}/annotated-param",
        family=family,
        source="""\
def f(a: int):
    return a
""",
        expected={"f": "int"},
    )
    _case(
        name=f"{family}/annotated-str",
        family=family,
        source="""\
def f(a: str):
    return a
""",
        expected={"f": "str"},
    )
    _case(
        name=f"{family}/annotated-chain",
        family=family,
        source=_src(
            """\
def f(a: int):
    return a


""",
            """\
def g(b: int):
    return f(b)
""",
        ),
        expected={"f": "int", "g": None},
    )
    _case(
        name=f"{family}/hinted-chain",
        family=family,
        source=_src(
            """\
def f(a: int):
    return a


""",
            """\
def g(b):
    return f(b)


g(1)
""",
        ),
        expected={"f": "int", "g": None, "g.b": "int"},
    )
    _case(
        name=f"{family}/callee-return",
        family=family,
        source=_src(
            """\
def f():
    return 1


""",
            """\
def g():
    return f()
""",
        ),
        expected={"f": "int", "g": None},
    )
    _case(
        name=f"{family}/deep-chain",
        family=family,
        source=_src(
            """\
def f(a: int):
    return a


""",
            """\
def g(b: int):
    return f(b)


""",
            """\
def h(c: int):
    return g(c)
""",
        ),
        expected={"f": "int", "g": None, "h": None},
    )
    _case(
        name=f"{family}/forward-ref",
        family=family,
        source="""\
def f(a: 'int'):
    return a
""",
        expected={"f": None},
    )
    _case(
        name=f"{family}/optional-ann",
        family=family,
        source=_src(
            """\
from typing import Optional

""",
            """\
def f(a: Optional[int]):
    return a
""",
        ),
        expected={"f": "Optional[int]"},
    )
    _case(
        name=f"{family}/union-ann",
        family=family,
        source="""\
def f(a: int | str):
    return a
""",
        expected={"f": "int | str"},
    )
    _case(
        name=f"{family}/none-ann",
        family=family,
        source="""\
def f(a: int | None):
    return a
""",
        expected={"f": None},
    )
    _case(
        name=f"{family}/param-default-ann",
        family=family,
        source="""\
def f(a: int = 0):
    return a
""",
        expected={"f": "int"},
    )
    for annotation in (
        "list",
        "list[int]",
        "dict[str, int]",
        "tuple[int, str]",
        "set[int]",
        "bytes",
        "float",
    ):
        _case(
            name=f"{family}/ann-{annotation}",
            family=family,
            source=f"def f(a: {annotation}):\n    return a\n",
            expected={"f": annotation},
        )
    family = "control_flow"
    _case(
        name=f"{family}/if-else-same",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="""\
if p:
        return 1
    return 2""",
            calls="""\
f(True)
""",
        ),
        expected={"f": "int", "f.p": "bool"},
    )
    _case(
        name=f"{family}/if-else-diff",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="""\
if p:
        return 1
    return 'a'""",
            calls="""\
f(True)
""",
        ),
        expected={"f": None, "f.p": "bool"},
    )
    _case(
        name=f"{family}/falls-off",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="""\
if p:
        return 1""",
            calls="""\
f(True)
""",
        ),
        expected={"f": "int | None", "f.p": "bool"},
    )
    _case(
        name=f"{family}/try-except",
        family=family,
        source=_src(
            """\
def f(p):
""",
            """\
    try:
        return 1
""",
            """\
    except ValueError:
        return 2


f(True)
""",
        ),
        expected={"f": "int", "f.p": "bool"},
    )
    _case(
        name=f"{family}/try-diff",
        family=family,
        source=_src(
            """\
def f(p):
""",
            """\
    try:
        return 1
""",
            """\
    except ValueError:
        return 'a'


f(True)
""",
        ),
        expected={"f": None, "f.p": "bool"},
    )
    _case(
        name=f"{family}/while-else",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="""\
while p:
        return 1
    return 0""",
            calls="""\
f(True)
""",
        ),
        expected={"f": "int", "f.p": "bool"},
    )
    _case(
        name=f"{family}/early-raise",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="""\
if p is None:
        raise ValueError
    return 1""",
            calls="""\
f(True)
""",
        ),
        expected={"f": "int", "f.p": None},
    )
    _case(
        name=f"{family}/elif",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="""\
if p:
        return 1
    elif p:
        return 2
    return 3""",
            calls="""\
f(True)
""",
        ),
        expected={"f": "int", "f.p": "bool"},
    )
    _case(
        name=f"{family}/nested-if",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="""\
if p:
        if p:
            return 1
        return 2
    return 3""",
            calls="""\
f(True)
""",
        ),
        expected={"f": "int", "f.p": "bool"},
    )
    _case(
        name=f"{family}/for-return",
        family=family,
        source=_def(
            name="f",
            params="p",
            body="""\
for x in p:
        return 1
    return 0""",
            calls="""\
f([1])
""",
        ),
        expected={"f": "int", "f.p": "list[int]"},
    )
    family = "method_binding"
    _case(
        name=f"{family}/self-call",
        family=family,
        source=_src(
            """\
class K:
""",
            """\
    def m(self, a):
        return a

""",
            """\
    def n(self):
        return self.m(1)
""",
        ),
        expected={"m": "int", "m.a": "int", "n": None},
    )
    _case(
        name=f"{family}/self-chain",
        family=family,
        source=_src(
            """\
class K:
""",
            """\
    def m(self, a):
        return a

""",
            """\
    def n(self):
        return self.m(1)


K().n()
""",
        ),
        expected={"m": "int", "m.a": "int", "n": None},
    )
    _case(
        name=f"{family}/super-call",
        family=family,
        source=_src(
            """\
class B:
""",
            """\
    def m(self, a):
        return a


""",
            """\
class K(B):
""",
            """\
    def m(self, a):
""",
            """\
        return super().m(a)
""",
        ),
        expected={"m": None, "m.a": None},
    )
    _case(
        name=f"{family}/classmethod",
        family=family,
        source=_src(
            """\
class K:
""",
            """\
    @classmethod
""",
            """\
    def m(cls, a):
        return a


K.m(1)
""",
        ),
        expected={"m": "int", "m.a": "int"},
    )
    _case(
        name=f"{family}/instance-attr",
        family=family,
        source=_src(
            """\
class K:
""",
            """\
    def m(self, a):
        return a


K().m('x')
""",
        ),
        expected={"m": "str", "m.a": "str"},
    )
    family = "nested_scope"
    _case(
        name=f"{family}/inner-typed",
        family=family,
        source=_src(
            """\
def f(p: int):
""",
            """\
    def g():
        return 1
""",
            """\
    return g()
""",
        ),
        expected={"f": None, "g": "int"},
    )
    _case(
        name=f"{family}/closure",
        family=family,
        source=_src(
            """\
def f(p: int):
""",
            """\
    def g():
        return p
""",
            """\
    return g()
""",
        ),
        expected={"f": None, "g": None},
    )
    _case(
        name=f"{family}/inner-call",
        family=family,
        source=_src(
            """\
def f():
""",
            """\
    def g(q):
        return q
""",
            """\
    return g(1)
""",
        ),
        expected={"f": None, "g": None, "g.q": None},
    )


# ---------------------------------------------------------------------------
# Multiplier: sweep literals through common bodies to reach 500+ cases.
# ---------------------------------------------------------------------------


def _sweep_cases() -> None:
    """Cartesian sweeps that make the gold set broad, not just deep."""
    family: str = "call_sites"
    numeric_ops: tuple[
        tuple[str, str, dict[str, str]],
        ...,
    ] = (
        ("add", "return p + 1", {"int": "int", "float": "float"}),
        ("sub", "return p - 1", {"int": "int", "float": "float"}),
        (
            "mul",
            "return p * 2",
            {"int": "int", "float": "float", "str": "str"},
        ),
        ("div", "return p / 2", {"int": "float", "float": "float"}),
        (
            "floordiv",
            "return p // 2",
            {"int": "int", "float": "float"},
        ),
        ("mod", "return p % 2", {"int": "int", "float": "float"}),
    )
    comparisons: tuple[str, ...] = ("<", "<=", ">=", "!=")
    numeric_sites: tuple[tuple[str, str], ...] = (
        ("1", "int"),
        ("0", "int"),
        ("1.5", "float"),
        ("0.0", "float"),
        ("'a'", "str"),
    )
    for op_name, body, ret_by_param in numeric_ops:
        for literal, type_name in numeric_sites:
            if type_name == "str" and op_name != "mul":
                continue
            ret_hint: str | None = ret_by_param.get(type_name)
            if ret_hint is None:
                continue
            _case(
                name=f"{family}/{op_name}/{literal}",
                family=family,
                source=_def(
                    name="f",
                    params="p",
                    body=body,
                    calls=f"f({literal})\n",
                ),
                expected={"f": ret_hint, "f.p": type_name},
            )
    for op in comparisons:
        for literal, type_name in numeric_sites:
            _case(
                name=f"{family}/cmp{op}/{literal}",
                family=family,
                source=_def(
                    name="f",
                    params="p",
                    body=f"return p {op} 0",
                    calls=f"f({literal})\n",
                ),
                expected={"f": "bool", "f.p": type_name},
            )
    # Default-literal sweep across arithmetic bodies.
    family = "default_literal"
    literals: tuple[tuple[str, str], ...] = (
        ("1", "int"),
        ("1.5", "float"),
        ("'a'", "str"),
        ("True", "bool"),
    )
    for literal, type_name in literals:
        shapes: tuple[tuple[str, str, str | None], ...] = (
            (
                "add-self",
                "return p + p",
                type_name if type_name in {"int", "float", "str"} else None,
            ),
            ("identity-expr", "return (p)", type_name),
            ("eq-self", "return p == p", "bool"),
        )
        for tag, body, ret in shapes:
            _case(
                name=f"{family}/{tag}/{type_name}",
                family=family,
                source=_def(name="f", params=f"p={literal}", body=body),
                expected={"f": ret, "f.p": type_name},
            )
    # Two-literal site combinations for pair coverage.
    family = "call_sites"
    site_pairs: tuple[tuple[str, str, str, str], ...] = (
        ("1", "'a'", "int", "str"),
        ("1.5", "1", "float", "int"),
        ("True", "''", "bool", "str"),
        ("'x'", "1.5", "str", "float"),
        ("[1]", "1", "list[int]", "int"),
        ("{'a': 1}", "'x'", "dict[str, int]", "str"),
        ("{1}", "2.5", "set[int]", "float"),
        ("b'x'", "1", "bytes", "int"),
    )
    for lit_a, lit_b, ta, tb in site_pairs:
        _case(
            name=f"{family}/pair/{ta}-{tb}",
            family=family,
            source=_def(
                name="f",
                params="a, b",
                body="return a",
                calls=f"f({lit_a}, {lit_b})\n",
            ),
            expected={"f": ta, "f.a": ta, "f.b": tb},
        )


# ---------------------------------------------------------------------------
# Feature families: variadic, attribute reads, comprehensions, rebinds.
# ---------------------------------------------------------------------------


def _variadic_cases() -> None:
    """Register ``*args``/``**kwargs`` evidence cases."""
    family: str = "variadic"
    _case(
        name=f"{family}/star-ints",
        family=family,
        source=_def(
            name="f",
            params="*a",
            body="return len(a)",
            calls="""\
f(1, 2)
f(3)
""",
        ),
        expected={"f": "int", "f.a": "int"},
    )
    _case(
        name=f"{family}/double-star-strs",
        family=family,
        source=_def(
            name="f",
            params="**k",
            body="return len(k)",
            calls="""\
f(x="s", y="t")
""",
        ),
        expected={"f": "int", "f.k": "str"},
    )
    _case(
        name=f"{family}/star-after-positional",
        family=family,
        source=_def(
            name="f",
            params="x, *a",
            body="return x",
            calls="""\
f("s", 1, 2)
""",
        ),
        expected={"f": "str", "f.x": "str", "f.a": "int"},
    )
    _case(
        name=f"{family}/kwargs-same-type",
        family=family,
        source=_def(
            name="f",
            params="**k",
            body="return k",
            calls="""\
f(a=1, b=2)
""",
        ),
        expected={"f": None, "f.k": "int"},
    )
    _case(
        name=f"{family}/star-mixed",
        family=family,
        source=_def(
            name="f",
            params="*a",
            body="return len(a)",
            calls="""\
f(1, "a")
""",
        ),
        expected={"f": "int", "f.a": None},
    )
    _case(
        name=f"{family}/star-unpacked-call",
        family=family,
        source=_src(
            """\
def f(*a):
    return len(a)


""",
            """\
def run(xs):
    return f(*xs)


""",
            """\
f(1, 2)
""",
        ),
        expected={"f": "int", "f.a": None, "run": None, "run.xs": None},
    )
    _case(
        name=f"{family}/star-no-extras",
        family=family,
        source=_def(
            name="f",
            params="first, *rest",
            body="return first",
            calls="""\
f(1)
""",
        ),
        expected={"f": "int", "f.first": "int", "f.rest": None},
    )
    _case(
        name=f"{family}/star-escaped",
        family=family,
        source=_src(
            """\
def f(*a):
    return len(a)


""",
            """\
g = f
g(1, 2)
""",
        ),
        expected={"f": "int", "f.a": None},
    )


def _attribute_read_cases() -> None:
    """Register ``return self.x`` attribute-table cases."""
    family: str = "attribute_read"
    _case(
        name=f"{family}/agreed-int",
        family=family,
        source=_src(
            """\
class Box:
""",
            """\
    def __init__(self):
        self.size = 3

""",
            """\
    def get(self):
        return self.size
""",
        ),
        expected={"__init__": "None", "get": "int"},
    )
    _case(
        name=f"{family}/arithmetic",
        family=family,
        source=_src(
            """\
class Box:
""",
            """\
    def __init__(self):
        self.a = 1

""",
            """\
    def nxt(self):
        return self.a + 1
""",
        ),
        expected={"__init__": "None", "nxt": "int"},
    )
    _case(
        name=f"{family}/optional-writes",
        family=family,
        source=_src(
            """\
class Box:
""",
            """\
    def __init__(self):
        self.size = None

""",
            """\
    def grow(self) -> None:
        self.size = 2

""",
            """\
    def get(self):
        return self.size
""",
        ),
        expected={"__init__": "None", "get": "int | None"},
    )
    _case(
        name=f"{family}/conflicting-writes",
        family=family,
        source=_src(
            """\
class Box:
""",
            """\
    def __init__(self):
        self.size = 3

""",
            """\
    def rename(self) -> None:
        self.size = 'big'

""",
            """\
    def get(self):
        return self.size
""",
        ),
        expected={"__init__": "None", "get": None},
    )
    _case(
        name=f"{family}/rebound-self",
        family=family,
        source=_src(
            """\
class Box:
""",
            """\
    def __init__(self):
        self.size = 3

""",
            """\
    def get(self, other):
        self = other
        """,
            """\
return self.size
""",
        ),
        expected={"__init__": "None", "get": None, "get.other": None},
    )
    _case(
        name=f"{family}/two-classes",
        family=family,
        source=_src(
            """\
class A:
""",
            """\
    def __init__(self):
        self.v = 1

""",
            """\
    def get(self):
        return self.v


""",
            """\
class B:
""",
            """\
    def __init__(self):
        self.w = 'x'

""",
            """\
    def fetch(self):
        return self.w
""",
        ),
        expected={
            "__init__": "None",
            "get": "int",
            "fetch": "str",
        },
    )


def _comprehension_cases() -> None:
    """Register comprehension display cases."""
    family: str = "comprehension"
    _case(
        name=f"{family}/list-range",
        family=family,
        source=_def(
            name="f",
            params="n",
            body="return [i * 2 for i in range(n)]",
        ),
        expected={"f": "list[int]", "f.n": None},
    )
    _case(
        name=f"{family}/dict-comp",
        family=family,
        source=_def(
            name="g",
            params="",
            body='return {c: 0 for c in "ab"}',
        ),
        expected={"g": "dict[str, int]"},
    )
    _case(
        name=f"{family}/set-comp",
        family=family,
        source=_def(
            name="h",
            params="",
            body="return {str(i) for i in range(3)}",
        ),
        expected={"h": "set[str]"},
    )
    _case(
        name=f"{family}/target-shadows",
        family=family,
        source=_src(
            """\
i = "s"


""",
            """\
def f():
    return [i for i in range(3)]
""",
        ),
        expected={"f": "list[int]"},
    )
    _case(
        name=f"{family}/async-comp",
        family=family,
        source=_src(
            """\
async def f(src):
    return [i async for i in src]
""",
        ),
        expected={"f": None, "f.src": None},
    )
    _case(
        name=f"{family}/unknown-iterable",
        family=family,
        source=_def(
            name="f",
            params="xs",
            body="return [x for x in xs]",
        ),
        expected={"f": None, "f.xs": None},
    )


def _multi_binding_cases() -> None:
    """Register multi-binding local cases."""
    family: str = "multi_binding"
    _case(
        name=f"{family}/branch-agree",
        family=family,
        source=_src(
            """\
def f(flag):
""",
            """\
    n = 0
""",
            """\
    if flag:
        n = 1
""",
            """\
    return n
""",
        ),
        expected={"f": "int", "f.flag": None},
    )
    _case(
        name=f"{family}/augmented-counter",
        family=family,
        source=_src(
            """\
def count(items):
""",
            """\
    total = 0
""",
            """\
    for _ in items:
        total += 1
""",
            """\
    return total
""",
        ),
        expected={"count": "int", "count.items": None},
    )
    _case(
        name=f"{family}/self-referential",
        family=family,
        source=_src(
            """\
def grow(steps):
""",
            """\
    x = 1
""",
            """\
    for _ in steps:
        x = x * 2
""",
            """\
    return x
""",
        ),
        expected={"grow": "int", "grow.steps": None},
    )
    _case(
        name=f"{family}/disagreeing",
        family=family,
        source=_src(
            """\
def f(flag):
""",
            """\
    v = 1
""",
            """\
    if flag:
        v = 'a'
""",
            """\
    return v
""",
        ),
        expected={"f": None, "f.flag": None},
    )
    _case(
        name=f"{family}/widening-augassign",
        family=family,
        source=_src(
            """\
def f(items):
""",
            """\
    v = 0
""",
            """\
    for _ in items:
        v += 0.5
""",
            """\
    return v
""",
        ),
        expected={"f": None, "f.items": None},
    )
    _case(
        name=f"{family}/loop-target-collision",
        family=family,
        source=_src(
            """\
def f(xs):
""",
            """\
    x = 0
""",
            """\
    for x in xs:
        pass
""",
            """\
    return x
""",
        ),
        expected={"f": None, "f.xs": None},
    )


_default_literal_cases()
_call_site_cases()
_disagree_cases()
_evidence_gap_cases()
_proven_return_cases()
_refusal_cases()
_flow_cases()
_sweep_cases()
_variadic_cases()
_attribute_read_cases()
_comprehension_cases()
_multi_binding_cases()


@pytest.mark.parametrize(
    "case",
    Constants.cases,
    ids=lambda c: f"{c.family}:{c.name}",
)
def test_gold(case: Case) -> None:
    """Each case's hint map matches the typed ground truth.

    Args:
        case (Case): Gold case to verify.

    """
    expect_equal(
        actual=_hints(source=case.source),
        expected=case.expected,
    )


def test_gold_covers_every_rejection_family() -> None:
    """The gold set spans the ladder's named refusal classes."""
    families: set[str] = {case.family for case in Constants.cases}
    expected: set[str] = {
        "attribute_read",
        "call_sites",
        "call_sites_disagree",
        "call_sites_unknown",
        "comprehension",
        "control_flow",
        "declaration",
        "default_disagrees",
        "default_literal",
        "default_refused",
        "escape",
        "generator",
        "imported_site",
        "method_binding",
        "multi_binding",
        "nested_scope",
        "none_default",
        "proven_none",
        "proven_return",
        "tainted",
        "typed_flow",
        "uncorroborated",
        "unresolved",
        "variadic",
    }
    expect_equal(actual=families & expected, expected=expected)


def test_gold_case_count() -> None:
    """The expanded gold set has at least 500 cases."""
    expect_true(
        condition=len(Constants.cases) >= Constants.minimum_cases,
        message="gold set should have at least 500 cases",
    )


_FIX_BASE: Final[Catalog] = load_default_catalog(
    registries=Constants.fix_registries,
)
_FIX_CATALOG: Final[Catalog] = replace(
    _FIX_BASE,
    rules=tuple(
        replace(
            rule,
            fixes=tuple(
                key for key in rule.fixes if key in Constants.annotation_fixes
            ),
        )
        for rule in _FIX_BASE.rules
    ),
    fixes=tuple(
        fix for fix in _FIX_BASE.fixes if fix.key in Constants.annotation_fixes
    ),
)


@final
class _AcceptAll:
    """A checker that never objects to a change."""

    @staticmethod
    def regresses(*, filename: str, before: str, after: str) -> bool:
        """Accept every change.

        Args:
            filename (str): Unused file name.
            before (str): Unused original text.
            after (str): Unused changed text.

        Returns:
            bool: Always ``False``.

        """
        return not (filename or before or after) and False


def _written(source: str) -> DictStrOrNone:
    """Collect the annotations ``fix_source`` actually wrote.

    Args:
        source (str): Fixed module source.

    Returns:
        DictStrOrNone: Annotation source per subject, ``None`` where absent.

    """
    module: CommentedModule = parse(source=source, filename="gold-fixed.py")
    resolved: DictStrOrNone = {}
    for node in walk(node=module):
        if not isinstance(node, (FunctionDef, AsyncFunctionDef)):
            continue
        resolved[node.name] = (
            None if node.returns is None else unparse(ast_obj=node.returns)
        )
        parameters: tuple[arg, ...] = (
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
            *(
                item
                for item in (node.args.vararg, node.args.kwarg)
                if item is not None
            ),
        )
        for parameter in parameters:
            if parameter.arg in {"self", "cls"}:
                continue
            resolved[f"{node.name}.{parameter.arg}"] = (
                None
                if parameter.annotation is None
                else unparse(ast_obj=parameter.annotation)
            )
    return resolved


def _fix_expected(case: Case) -> DictStrOrNone:
    """Return the fix-level expectation for a gold case.

    Args:
        case (Case): Gold case under test.

    Returns:
        DictStrOrNone: Expected annotations after ``fix_source`` converges.

    """
    return Constants.fix_expected.get(case.name, case.expected)


@pytest.mark.parametrize("with_checker", [False, True], ids=["off", "stub"])
@pytest.mark.parametrize(
    "case",
    Constants.cases,
    ids=lambda c: f"{c.family}:{c.name}",
)
def test_gold_fix_level(case: Case, *, with_checker: bool) -> None:
    """``fix_source`` writes exactly the expected annotations.

    Args:
        case (Case): Gold case to verify through the full fixer.
        with_checker (bool): Whether to gate guarded fixes on an accepting
            stub.

    """
    checker: Checker | None = _AcceptAll() if with_checker else None
    result: FixResult = fix_source(
        source=case.source,
        filename="gold.py",
        catalog=_FIX_CATALOG,
        registries=Constants.fix_registries,
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            checker=checker,
            negotiate=False,
        ),
    )
    expect_true(
        condition=result.parse_error is None,
        message=f"{case.name}: {result.parse_error}",
    )
    expected: DictStrOrNone = _fix_expected(case=case)
    written: DictStrOrNone = _written(source=result.source)
    expect_equal(
        actual={key: written.get(key) for key in expected},
        expected=expected,
    )


def _fixed_annotations(
    case: Case,
    *,
    negotiate: bool,
) -> DictStrOrNone:
    """Run the fixer on a gold case and list the annotations of interest.

    Args:
        case (Case): Gold case.
        negotiate (bool): Whether negotiated hints supplement the hint index.

    Returns:
        DictStrOrNone: The written annotation for each key the case expects.

    """
    result: FixResult = fix_source(
        source=case.source,
        filename="gold.py",
        catalog=_FIX_CATALOG,
        registries=Constants.fix_registries,
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            negotiate=negotiate,
        ),
    )
    written: DictStrOrNone = _written(source=result.source)
    return {key: written.get(key) for key in _fix_expected(case=case)}


@pytest.mark.parametrize(
    "case",
    Constants.cases,
    ids=lambda c: f"{c.family}:{c.name}",
)
def test_gold_negotiation_is_a_reviewed_superset(case: Case) -> None:
    """Negotiation never changes a written annotation and adds only reviewed.

    Args:
        case (Case): Gold case to run with and without negotiation.

    """
    plain: DictStrOrNone = _fixed_annotations(
        case=case,
        negotiate=False,
    )
    negotiated: DictStrOrNone = _fixed_annotations(
        case=case,
        negotiate=True,
    )
    for key, before in plain.items():
        after: str | None = negotiated[key]
        if before is not None:
            expect_equal(actual=after, expected=before)
        elif after is not None:
            expect_equal(
                actual=after,
                expected=Constants.negotiated_adds.get((case.name, key)),
                message=f"{case.name}: unreviewed addition for {key}",
            )
