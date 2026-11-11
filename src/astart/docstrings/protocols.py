"""Describe synthesized structural contracts without inventing behavior."""

from __future__ import annotations

from ast import (
    AnnAssign,
    AsyncFunctionDef,
    Attribute,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    Name,
    arg,
    get_docstring,
    unparse,
)
from typing import Final, final


@final
class Constants:
    """Describe operations whose language-level behavior is known.

    Attributes:
        summaries (Final[dict[str, str]]): Method summaries derived from
            Python's operation contract.

    """

    summaries: Final[dict[str, str]] = {
        "__call__": "Call the object with the declared arguments.",
        "__add__": "Return the addition result for the declared operands.",
        "__matmul__": "Return the matrix product for the declared operands.",
        "__mul__": "Return the product for the declared operands.",
        "__len__": "Return the number of available items.",
        "__iter__": "Return an iterator over the available items.",
        "__next__": "Return the next available item.",
        "__getitem__": "Return the item at the requested key.",
        "__setitem__": "Store the value at the requested key.",
        "__contains__": "Report whether the requested item is present.",
        "__enter__": "Enter the context and return its managed value.",
        "__exit__": "Leave the context with the supplied exception state.",
    }


def _put(
    *,
    owner: ClassDef | FunctionDef | AsyncFunctionDef,
    text: str,
) -> None:
    """Attach a docstring while retaining an existing literal's identity.

    Args:
        owner (ClassDef | FunctionDef | AsyncFunctionDef): New or explicitly
            selected structural declaration.
        text (str): Complete documentation contract.

    """
    if (
        owner.body
        and isinstance(owner.body[0], Expr)
        and isinstance(
            owner.body[0].value,
            Constant,
        )
        and isinstance(owner.body[0].value.value, str)
    ):
        owner.body[0].value.value = text
    else:
        owner.body.insert(0, Expr(value=Constant(value=text)))


def _method_text(*, method: FunctionDef | AsyncFunctionDef) -> str:
    """Describe required inputs and outputs, retaining TODO descriptions.

    Args:
        method (FunctionDef | AsyncFunctionDef): Typed method or property
            declaration.

    Returns:
        str: Google-style method documentation with no unobserved Raises
            claims.

    """
    setter: bool = any(
        isinstance(item, Attribute) and item.attr == "setter"
        for item in method.decorator_list
    )
    getter: bool = any(
        isinstance(item, Name) and item.id == "property"
        for item in method.decorator_list
    )
    summary: str = (
        f"Write the required ``{method.name}`` attribute."
        if setter
        else f"Read the required ``{method.name}`` attribute."
        if getter
        else Constants.summaries.get(
            method.name,
            f"Provide the required ``{method.name}`` operation.",
        )
    )
    positional: list[arg] = [*method.args.posonlyargs, *method.args.args]
    names: list[str] = [
        item.arg
        for item in [*positional, *method.args.kwonlyargs]
        if item.arg not in {"self", "cls"}
    ]
    if method.args.vararg is not None:
        names.append(f"*{method.args.vararg.arg}")
    if method.args.kwarg is not None:
        names.append(f"**{method.args.kwarg.arg}")
    parts: list[str] = [summary]
    if names:
        parts.extend(("", "Args:", *(f"    {name}: TODO." for name in names)))
    if (
        method.returns is not None
        and unparse(ast_obj=method.returns) != "None"
    ):
        parts.extend(("", "Returns:", "    TODO."))
    return "\n".join(parts)


def document_protocol(*, node: ClassDef, overwrite: bool = False) -> None:
    """Document structural members directly on the existing native nodes.

    Class and method summaries name the required operations. Argument,
    result and attribute prose remains TODO where source usage cannot prove
    a domain-specific explanation. No method behavior, exception, import or
    executable statement is synthesized by this documentation pass.

    Args:
        node (ClassDef): Protocol class whose signatures are already
            established.
        overwrite (bool): Replace generated prose; otherwise retain authored
            docs.

    """
    method_names: set[str] = {
        item.name
        for item in node.body
        if isinstance(item, (FunctionDef, AsyncFunctionDef))
    }
    attribute_names: set[str] = {
        item.target.id
        for item in node.body
        if isinstance(item, AnnAssign) and isinstance(item.target, Name)
    }
    members: tuple[str, ...] = tuple(sorted(method_names | attribute_names))
    attributes: tuple[str, ...] = tuple(sorted(attribute_names))
    if overwrite or get_docstring(node=node) is None:
        required: str = ", ".join(f"``{name}``" for name in members)
        parts: list[str] = [f"{protocol_marker()}{required}."]
        if attributes:
            parts.extend(
                (
                    "",
                    "Attributes:",
                    *(f"    {name}: TODO." for name in attributes),
                ),
            )
        _put(
            owner=node,
            text="\n".join(parts),
        )
    for member in node.body:
        if isinstance(member, (FunctionDef, AsyncFunctionDef)) and (
            overwrite or get_docstring(node=member) is None
        ):
            _put(owner=member, text=_method_text(method=member))


def protocol_marker() -> str:
    """Identify generated structural documentation across fix rounds.

    Returns:
        str: Stable marker used by synthesis and generated-member detection.

    """
    return "Structural contract requiring "
