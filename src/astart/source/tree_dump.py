"""Export the complete comment-aware AST as deterministic JSON."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from ast import AST, iter_fields, walk
from dataclasses import fields, is_dataclass
from json import dumps
from pathlib import Path
from typing import TYPE_CHECKING, cast, final

from astart.source.api import parse
from astart.source.node_attributes import read_attribute

if TYPE_CHECKING:
    from collections.abc import Iterable

    from astart.source.ast import CommentedModule
    from astart.source.tokens import TokenSnapshot


@final
class TreeDumper:
    """Serialize AST fields, lexical snapshots, and semantic references."""

    def __init__(self, *, tree: CommentedModule) -> None:
        """Index nodes and retrieve lexical metadata once.

        Args:
            tree (CommentedModule): Parsed, comment-aware source tree.

        """
        self._tree: CommentedModule = tree
        self._nodes: list[AST] = list(walk(node=tree))
        self._ids: dict[int, int] = {
            id(node): index for index, node in enumerate(iterable=self._nodes)
        }
        self._snapshots: dict[int, TokenSnapshot] = dict(
            zip(
                (id(node) for node in self._nodes),
                tree.token_snapshots(nodes=self._nodes),
                strict=True,
            ),
        )

    def _value(self, *, value: object) -> object:
        """Convert a value into JSON-compatible structured data.

        Args:
            value (object): AST field or lexical metadata value.

        Returns:
            object: JSON-compatible representation.

        """
        if isinstance(value, AST):
            return self._node(node=value)
        if isinstance(value, (list, tuple)):
            return [
                self._value(value=item)
                for item in cast(typ="Iterable[object]", val=value)
            ]
        if isinstance(value, dict):
            mapping: dict[object, object] = cast(
                typ="dict[object, object]",
                val=value,
            )
            return {
                str(object=key): self._value(value=item)
                for key, item in mapping.items()
            }
        if is_dataclass(obj=value) and not isinstance(value, type):
            return {
                field.name: self._value(
                    value=getattr(value, field.name),
                )
                for field in fields(class_or_instance=value)
            }
        result: object
        if value is Ellipsis:
            result = {"kind": "ellipsis"}
        elif isinstance(value, (str, int, float, bool)) or value is None:
            result = value
        else:
            result = {"kind": "repr", "value": repr(value)}
        return result

    def _node(self, *, node: AST) -> dict[str, object]:
        """Serialize a node without following semantic back-references.

        Args:
            node (AST): Node owned by the indexed tree.

        Returns:
            dict[str, object]: Node fields, attributes, and token metadata.

        """
        result: dict[str, object] = {
            "id": self._ids[id(node)],
            "type": type(node).__name__,
            "module": type(node).__module__,
            "fields": {
                name: self._value(value=value)
                for name, value in iter_fields(node=node)
            },
            "attributes": {
                name: self._value(value=getattr(node, name))
                for name in getattr(node, "_attributes", ())
                if hasattr(node, name)
            },
        }
        if (snapshot := self._snapshots.get(id(node))) is not None:
            result["token_info"] = self._value(value=snapshot)
        references: dict[str, object] = {}
        for name in ("owner", "expression", "target"):
            linked: object = getattr(node, name, None)
            if isinstance(linked, AST):
                references[name] = self._ids.get(id(linked))
        if references:
            result["references"] = references
        if hasattr(node, "link_role"):
            result["link_role"] = self._value(
                value=read_attribute(node=node, name="link_role", kind=str),
            )
        return result

    def dump(self) -> dict[str, object]:
        """Produce a JSON-compatible snapshot of the indexed module.

        Returns:
            dict[str, object]: Tree, tokenizer stream, and source metadata.

        """
        return {
            "format": "astart-custom-ast-v1",
            "tree": self._node(node=self._tree),
            "token_stream": self._value(value=self._tree.token_stream),
            "token_source": self._tree.token_source,
        }


def dump_file(*, source: Path, output: Path) -> None:
    """Parse a Python file and write its structured AST as UTF-8 JSON.

    Args:
        source (Path): Input Python source file.
        output (Path): Destination JSON file.

    Raises:
        OSError: If reading or writing fails.
        SyntaxError: If the Python source cannot be parsed.
        ValueError: If token snapshots cannot be reconstructed safely.

    """
    tree: CommentedModule = parse(
        source=source.read_text(encoding="utf-8"),
        filename=str(object=source),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        data=dumps(
            obj=TreeDumper(tree=tree).dump(),
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    """Run the custom AST JSON exporter from the command line."""
    parser: ArgumentParser = ArgumentParser(
        description="Export astart's complete custom AST to JSON.",
    )
    parser.add_argument("source", type=Path, help="Input Python file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Destination JSON file",
    )
    arguments: Namespace = parser.parse_args()
    source: Path = arguments.source
    output: Path | None = arguments.output
    dump_file(
        source=source,
        output=output
        if output is not None
        else source.with_suffix(suffix=".ast.json"),
    )


if __name__ == "__main__":
    main()
