"""Docstring facts and fixes: parameters, generator results and whitespace.

Docstring fixes edit a function's or class's documentation in place:

* ``docs.add-parameter-entries`` writes a stub entry for each parameter the
  docstring does not mention (DOC002);
* ``docs.remove-stale-entries`` drops entries for parameters the function no
  longer takes (DOC003);
* ``docs.add-generator-results`` repairs yielded and terminal-result entries
  with TODO placeholders (DOC004), preserving the detected style;
* ``docs.tidy-docstring`` strips trailing space, collapses blank runs and
  aligns the body (DOC007).

Parameter and whitespace fixes require editable Google-style docstrings.
Generator result fixes use the structured parser and preserve Google, NumPy,
reStructuredText and Epytext styles. Mixed styles are left intact.

"""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    Attribute,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    Module,
    Name,
    arguments,
    expr,
    parse,
    stmt,
    unparse,
    walk,
)
from typing import TYPE_CHECKING, Final, cast, final

from astart.docstrings import (
    Constants as DocstringConstants,
)
from astart.docstrings import (
    DocEntry,
    DocSection,
    generator_result_annotation,
    parse_docstring,
)
from astart.docstrings.edit import (
    add_parameter_entries,
    entry_names,
    parameter_entry_names,
    remove_parameter_entries,
    rename_parameter_entry,
    tidy_docstring,
)
from astart.docstrings.missing_returns import result_kinds
from astart.docstrings.shared import documented_names
from astart.docstrings.types import add_types

if TYPE_CHECKING:
    from astart import CommentedModule
    from astart.docstrings import DocKind, DocstringNode
    from astart.rules.facts import ModuleFacts, Subject
    from astart.rules.jsonvalue import JsonValue
    from astart.rules.predicate import FactValue

    type Function = FunctionDef | AsyncFunctionDef


@final
class Constants:
    """Group module-level constants.

    Attributes:
        triple_quotes (Final[tuple[str, ...]]): Delimiters a rewritable
            docstring may use.
        string_prefixes (Final[str]): Characters that may precede the opening
            quotes.
        receivers (Final[frozenset[str]]): Parameter names that never need
            documenting.
        rule_dashes (Final[int]): Length of a dashed underline that marks NumPy
            style.
        rest_marker (Final[str]): Text that marks reStructuredText field lists.
        overload (Final[str]): Decorator name whose definitions are never
            stubbed.
        stub_summary (Final[str]): Summary line written into a stub docstring.

    """

    triple_quotes: Final[tuple[str, ...]] = ('"""', "'''")
    string_prefixes: Final[str] = "rRuU"
    receivers: Final[frozenset[str]] = frozenset({"self", "cls"})
    rule_dashes: Final[int] = 3
    rest_marker: Final[str] = ":param"
    overload: Final[str] = "overload"
    stub_summary: Final[str] = "Describe {name}."


def _docstring(*, node: AST) -> tuple[Expr, Constant] | None:
    """Find the docstring statement of a definition.

    Args:
        node (AST): Any node.

    Returns:
        tuple[Expr, Constant] | None:
            The statement and its string constant, or ``None``.

    """
    if not isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef, Module)):
        return None
    first: stmt | None = node.body[0] if node.body else None
    if (
        isinstance(first, Expr)
        and isinstance(first.value, Constant)
        and isinstance(first.value.value, str)
    ):
        return first, first.value
    return None


def _dashed(*, text: str) -> bool:
    """Tell whether any line is a NumPy-style dashed underline.

    Args:
        text (str): Docstring value.

    Returns:
        bool: ``True`` when a line is only dashes, at least three of them.

    """
    return any(
        len(line.strip()) >= Constants.rule_dashes
        and set(line.strip()) == {"-"}
        for line in text.split(
            sep="\n",
        )
    )


def triple_quoted_owners(*, module: CommentedModule) -> frozenset[int]:
    """Collect the definitions whose docstring literal uses triple quotes.

    Called while the module is still as parsed, so source positions are
    valid. The text is read once: asking each docstring node for its own
    text would make the module rebuild its token index every time.

    Args:
        module (CommentedModule): Freshly parsed module.

    Returns:
        frozenset[int]: Identities of the owners with a triple-quoted
            docstring.

    """
    lines: list[str] = module.token_text.splitlines()
    found: set[int] = set()
    for docstring in module.docstrings:
        if not 0 < docstring.lineno <= len(lines):
            continue
        start: str = lines[docstring.lineno - 1][docstring.col_offset :]
        if start.lstrip(Constants.string_prefixes).startswith(
            Constants.triple_quotes,
        ):
            found.add(
                id(module) if docstring.owner is None else id(docstring.owner),
            )
    return frozenset(found)


def is_editable(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether a definition's docstring can be rewritten safely.

    Args:
        subject (Subject): Function or class subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        FactValue:
            ``True`` for a Google-style, triple-quoted docstring with no tabs.

    """
    found: tuple[Expr, Constant] | None = _docstring(node=subject.node)
    if found is None:
        return False
    text: str = cast(typ="str", val=found[1].value)
    return not (
        "\t" in text
        or Constants.rest_marker in text
        or _dashed(text=text)
        or id(subject.node) not in facts.triple_quoted
    )


def _signature(*, function: Function) -> list[str]:
    """List the parameters a docstring should cover, with their stars.

    Args:
        function (Function): Function definition.

    Returns:
        list[str]: Display names in signature order, receivers excluded.

    """
    arguments: arguments = function.args
    names: list[str] = [
        item.arg for item in (*arguments.posonlyargs, *arguments.args)
    ]
    if arguments.vararg is not None:
        names.append(f"*{arguments.vararg.arg}")
    names.extend(item.arg for item in arguments.kwonlyargs)
    if arguments.kwarg is not None:
        names.append(f"**{arguments.kwarg.arg}")
    return [name for name in names if name not in Constants.receivers]


def _documented(*, function: Function, facts: ModuleFacts) -> set[str]:
    """Collect the bare names the docstring documents as parameters.

    Args:
        function (Function): Function definition.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        set[str]: Documented names without stars.

    """
    return {
        name.lstrip("*")
        for name in documented_names(
            module=facts.module,
            owner=function,
            kind="parameters",
        )
        if name is not None
    }


def stale_parameters(subject: Subject, facts: ModuleFacts) -> list[str]:
    """List documented parameters that the signature does not have.

    Args:
        subject (Subject): Function subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        list[str]: The stale names, in documentation order.

    """
    function: AST = subject.node
    if not isinstance(function, (FunctionDef, AsyncFunctionDef)):
        return []
    if _docstring(node=function) is None:
        return []
    declared: set[str] = {
        name.lstrip("*") for name in _signature(function=function)
    }
    return [
        name.lstrip("*")
        for name in documented_names(
            module=facts.module,
            owner=function,
            kind="parameters",
        )
        if name is not None
        and name.lstrip("*") not in declared
        and name not in Constants.receivers
    ]


def stale_count(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Count documented parameters that the signature lacks.

    Args:
        subject (Subject): Function subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        FactValue: The number of stale entries.

    """
    return len(stale_parameters(subject=subject, facts=facts))


def stale_evidence(subject: Subject, facts: ModuleFacts) -> JsonValue:
    """Provide the ``stale`` evidence slot.

    Args:
        subject (Subject): Function subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        JsonValue: The stale parameter names.

    """
    return cast(
        typ="JsonValue",
        val=list(stale_parameters(subject=subject, facts=facts)),
    )


def is_untidy(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether tidying would change a docstring.

    Args:
        subject (Subject): Function or class subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        FactValue:
            ``True`` when the docstring is editable and not already tidy.

    """
    found: tuple[Expr, Constant] | None = _docstring(node=subject.node)
    if found is None or not is_editable(subject=subject, facts=facts):
        return False
    statement, constant = found
    text: str = cast(typ="str", val=constant.value)
    return tidy_docstring(doc=text, indent=" " * statement.col_offset) != text


def generator_needs_results(
    subject: Subject,
    _facts: ModuleFacts,
) -> FactValue:
    """Find generator documentation whose result sections need repair.

    Args:
        subject (Subject): Function subject.
        _facts (ModuleFacts): Unused module facts.

    Returns:
        FactValue:
            Whether a documented generator lacks a yield or terminal result.

    """
    function: AST = subject.node
    found: tuple[Expr, Constant] | None = _docstring(node=function)
    if (
        not isinstance(function, (FunctionDef, AsyncFunctionDef))
        or found is None
    ):
        return False
    kinds: tuple[DocKind, ...] = result_kinds(node=function)
    if "yields" not in kinds:
        return False
    document: DocstringNode = parse_docstring(
        source=cast(typ="str", val=found[1].value),
    )
    return any(not document.entries(kind=kind) for kind in kinds)


def add_generator_results(subject: Subject, facts: ModuleFacts) -> None:
    """Repair generator result sections while retaining style and prose.

    Args:
        subject (Subject): Function subject.
        facts (ModuleFacts): Module facts and documentation preferences.

    """
    if facts.docstring_types:
        add_types(subject=subject, facts=facts)
        return
    _add_legacy_generator_results(subject=subject)


def _add_legacy_generator_results(*, subject: Subject) -> None:
    """Repair untyped legacy generator documentation.

    Args:
        subject (Subject): Function subject.

    """
    function: AST = subject.node
    found: tuple[Expr, Constant] | None = _docstring(node=function)
    if (
        not isinstance(function, (FunctionDef, AsyncFunctionDef))
        or found is None
    ):
        return
    statement, constant = found
    document: DocstringNode = parse_docstring(
        source=cast(typ="str", val=constant.value),
    )
    kinds: tuple[DocKind, ...] = result_kinds(node=function)
    if "yields" not in kinds or document.style == "mixed":
        return
    if kinds == ("yields",) and not document.entries(kind="yields"):
        for section in document.sections:
            if section.kind == "returns":
                section.kind = "yields"
                for entry in section.entries:
                    entry.kind = "yields"
                    component: expr | None = generator_result_annotation(
                        owner=function,
                        kind="yields",
                    )
                    if entry.type_name and component is not None:
                        entry.type_name = unparse(ast_obj=component)
    for kind in kinds:
        if not document.entries(kind=kind):
            position: int = next(
                (
                    index
                    for index, section in enumerate(iterable=document.sections)
                    if section.kind
                    in {
                        "raises",
                        "examples",
                        "notes",
                        "warnings",
                        "see_also",
                    }
                    or (kind == "yields" and section.kind == "returns")
                ),
                len(document.sections),
            )
            document.sections.insert(
                position,
                DocSection(
                    kind=kind,
                    title=kind.capitalize(),
                    entries=[
                        DocEntry(
                            kind=kind,
                            description=DocstringConstants.todo_placeholder,
                        ),
                    ],
                ),
            )
    lines: list[str] = document.render().splitlines()
    indent: str = " " * statement.col_offset
    constant.value = (
        lines[0]
        + "\n"
        + "\n".join(indent + line if line else "" for line in lines[1:])
        + "\n\n"
        + indent
    )


def add_entries(subject: Subject, facts: ModuleFacts) -> None:
    """Write a stub entry for every undocumented parameter.

    Args:
        subject (Subject): Function subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    """
    if facts.docstring_types:
        add_types(subject=subject, facts=facts)
        return
    function: AST = subject.node
    found: tuple[Expr, Constant] | None = _docstring(node=function)
    if (
        not isinstance(function, (FunctionDef, AsyncFunctionDef))
        or found is None
        or not is_editable(subject=subject, facts=facts)
    ):
        return
    statement, constant = found
    present: set[str] = _documented(function=function, facts=facts) | set(
        entry_names(doc=cast(typ="str", val=constant.value)),
    )
    signature: list[str] = _signature(function=function)
    missing: list[str] = [
        name for name in signature if name.lstrip("*") not in present
    ]
    if missing:
        indent: str = " " * statement.col_offset
        constant.value = tidy_docstring(
            doc=add_parameter_entries(
                doc=cast(typ="str", val=constant.value),
                names=missing,
                order=[name.lstrip("*") for name in signature],
                indent=indent,
            ),
            indent=indent,
        )


def heal_rename(subject: Subject, facts: ModuleFacts) -> None:
    """Rename a stale entry that is the renamed form of a missing parameter.

    Applies only when the function has exactly one stale entry and one
    undocumented parameter sitting at the same position, so the user's
    description survives the rename.

    Args:
        subject (Subject): Function subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    """
    function: AST = subject.node
    found: tuple[Expr, Constant] | None = _docstring(node=function)
    if (
        not isinstance(function, (FunctionDef, AsyncFunctionDef))
        or found is None
        or not is_editable(subject=subject, facts=facts)
    ):
        return
    stale: list[str] = stale_parameters(subject=subject, facts=facts)
    if len(stale) != 1:
        return
    constant: Constant = found[1]
    doc: str = cast(typ="str", val=constant.value)
    present: set[str] = _documented(function=function, facts=facts) | set(
        entry_names(doc=doc),
    )
    signature: list[str] = _signature(function=function)
    missing: list[str] = [
        name for name in signature if name.lstrip("*") not in present
    ]
    if len(missing) != 1:
        return
    old: str = stale[0]
    new: str = missing[0]
    doc_order: tuple[str, ...] = parameter_entry_names(doc=doc)
    sig_order: list[str] = [name.lstrip("*") for name in signature]
    if (
        old not in doc_order
        or new.lstrip("*") not in sig_order
        or doc_order.index(old) != sig_order.index(new.lstrip("*"))
    ):
        return
    indent: str = " " * found[0].col_offset
    constant.value = tidy_docstring(
        doc=rename_parameter_entry(doc=doc, old=old, new=new),
        indent=indent,
    )


def remove_entries(subject: Subject, facts: ModuleFacts) -> None:
    """Drop the entries of parameters the function no longer takes.

    Args:
        subject (Subject): Function subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    """
    found: tuple[Expr, Constant] | None = _docstring(node=subject.node)
    stale: list[str] = stale_parameters(subject=subject, facts=facts)
    if (
        found is None
        or not stale
        or not is_editable(subject=subject, facts=facts)
    ):
        return
    constant: Constant = found[1]
    indent: str = " " * found[0].col_offset
    constant.value = tidy_docstring(
        doc=remove_parameter_entries(
            doc=cast(typ="str", val=constant.value),
            names=stale,
        ),
        indent=indent,
    )


def tidy(subject: Subject, facts: ModuleFacts) -> None:
    """Strip trailing space, collapse blank runs and align the body.

    Args:
        subject (Subject): Function or class subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    """
    if any(
        document.owner is subject.node
        and not document.layout.preserve_original
        for document in facts.module.docstrings
    ):
        return
    found: tuple[Expr, Constant] | None = _docstring(node=subject.node)
    if found is None or not is_editable(subject=subject, facts=facts):
        return
    statement, constant = found
    constant.value = tidy_docstring(
        doc=cast(typ="str", val=constant.value),
        indent=" " * statement.col_offset,
    )


def stubs_wanted(_subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether missing docstrings should be flagged in this module.

    They are flagged when stubbing was requested, or when the module already
    documents something: a module that has docstrings is expected to have
    them everywhere, while a docstring-free script is left alone.

    Args:
        _subject (Subject): Unused subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        FactValue: Whether the requirement applies.

    """
    return facts.stub_docstrings or bool(facts.module.docstrings)


def _overloaded(*, node: Function | ClassDef) -> bool:
    """Tell whether a definition carries an ``overload`` decorator.

    Args:
        node (Function | ClassDef): Definition.

    Returns:
        bool: ``True`` for ``@overload`` and ``@typing.overload``.

    """
    return any(
        (isinstance(item, Name) and item.id == Constants.overload)
        or (isinstance(item, Attribute) and item.attr == Constants.overload)
        for item in node.decorator_list
    )


def _declaration_only(*, body: list[stmt]) -> bool:
    """Tell whether a body is only ``...`` (a protocol or stub declaration).

    Args:
        body (list[stmt]): Statements of a definition.

    Returns:
        bool: ``True`` when every statement is a bare ``...``.

    """
    return all(
        isinstance(item, Expr)
        and isinstance(item.value, Constant)
        and item.value.value is Ellipsis
        for item in body
    )


def _missing_public(*, node: AST) -> bool:
    """Tell whether a public definition has no docstring to stub.

    Args:
        node (AST): Any node.

    Returns:
        bool: ``True`` for a public, non-overload definition without
            a docstring whose body starts on its own line.

    """
    if not isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
        return False
    return bool(
        node.body
        and not _declaration_only(body=node.body)
        and not node.name.startswith("_")
        and _docstring(node=node) is None
        and not _overloaded(node=node)
        and node.body[0].lineno > node.lineno,
    )


def is_missing_public(subject: Subject, _facts: ModuleFacts) -> FactValue:
    """Report whether a public definition has no docstring to stub.

    Args:
        subject (Subject): Function or class subject.
        _facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        FactValue: func:`_missing_public` holds for the subject's node.

    """
    return _missing_public(node=subject.node)


def stub_missing_docstrings(*, source: str) -> str:
    """Insert a one-line stub docstring into every undocumented definition.

    This is a text edit, made before parsing, so the stub is real source with
    triple quotes; the parameter-entry fix then expands it where the function
    has parameters. Definitions whose body starts on the header line are left
    alone.

    Args:
        source (str): Module text.

    Returns:
        str: The text with stubs added; unchanged when it does not parse.

    """
    try:
        tree: Module = parse(source=source)
    except SyntaxError:
        return source
    lines: list[str] = source.splitlines(keepends=True)
    inserts: list[tuple[int, str]] = []
    for node in walk(node=tree):
        if not _missing_public(node=node):
            continue
        first: stmt = cast(
            typ="FunctionDef | AsyncFunctionDef | ClassDef",
            val=node,
        ).body[0]
        line: str = lines[first.lineno - 1]
        indent: str = line[: first.col_offset]
        if indent.strip():
            continue
        name: str = cast(
            typ="FunctionDef | AsyncFunctionDef | ClassDef",
            val=node,
        ).name
        inserts.append(
            (
                first.lineno - 1,
                f'{indent}"""{Constants.stub_summary.format(name=name)}"""\n',
            ),
        )
    for index, text in sorted(inserts, reverse=True):
        lines.insert(index, text)
    return "".join(lines)
