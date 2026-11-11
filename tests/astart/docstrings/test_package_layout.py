"""Package ownership, public facade identity and documentation resources."""

from __future__ import annotations

from ast import Assign, Constant, Name, Store, TypeAlias
from importlib.resources import files
from json import loads
from typing import TYPE_CHECKING, TypedDict

from astart import DocstringNode, parse
from astart.docstrings.core import DocstringNode as CoreDocstringNode
from astart.rules import default_registries, load_default_catalog
from astart.source.node_attributes import (
    read_attribute,
    reclassify_node,
    write_attribute,
)

from tests.support.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from importlib.abc import Traversable

    from astart import CommentedModule
    from astart.rules import Catalog
    from astart.rules.registry import Registries


class _CatalogDocument(TypedDict):
    """Catalog document fields read by the layout tests.

    Attributes:
        rules (list[dict[str, object]]): Rule entries carrying a ``key`` field.

    """

    rules: list[dict[str, object]]


def test_documentation_facade_preserves_class_identity() -> None:
    """The public facade and native source tree use one documentation model."""
    module: CommentedModule = parse(source='"""Example."""\n')
    expect_true(condition=DocstringNode is CoreDocstringNode)
    expect_true(condition=DocstringNode in type(module.docstrings[0]).__mro__)


def test_documentation_catalog_is_canonical_and_registered() -> None:
    """Domain-owned data remains accessible through package resources."""
    resource: Traversable = files(anchor="astart.docstrings").joinpath(
        "artifacts",
        "catalog.json",
    )
    document: _CatalogDocument = loads(
        s=resource.read_text(encoding="utf-8"),
    )
    registries: Registries = default_registries()
    catalog: Catalog = load_default_catalog(registries=registries)
    expect_true(
        condition={item["key"] for item in document["rules"]}
        <= {item.key for item in catalog.rules},
    )
    expect_true(
        condition=not files(anchor="astart.rules")
        .joinpath("artifacts", "catalog", "docs.json")
        .is_file(),
    )


def test_native_reclassification_preserves_identity_and_metadata() -> None:
    """A generic source edit retains metadata outside replaced fields."""
    name: Name = Name(id="Alias", ctx=Store())
    value: Constant = Constant(value=1)
    node: Assign = Assign(targets=[name], value=value)
    _ = write_attribute(node=node, name="custom_metadata", value="retained")
    original_identity: int = id(node)
    reclassify_node(
        node=node,
        kind=TypeAlias,
        removed=("targets",),
        fields={"name": name, "type_params": []},
    )
    expect_equal(actual=id(node), expected=original_identity)
    expect_true(condition=isinstance(node, TypeAlias))
    expect_equal(
        actual=read_attribute(node=node, name="custom_metadata", kind=str),
        expected="retained",
    )
    expect_true(condition=node.value is value)
