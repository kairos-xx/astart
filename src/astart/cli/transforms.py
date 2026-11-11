"""Expose explicit native AST wrapping and insertion as a separate command."""

from __future__ import annotations

from argparse import BooleanOptionalAction
from difflib import unified_diff
from hashlib import sha256
from io import BytesIO
from json import dumps
from pathlib import Path
from tokenize import detect_encoding
from typing import TYPE_CHECKING, Protocol

from astart.cli.commands import write_atomic
from astart.docstrings.wrapping import WrapChanges, WrapSettings, wrap_tree
from astart.source.ast import CommentedModule
from astart.transforms.aliases import (
    AliasChanges,
    AliasOptimizer,
    AliasSettings,
)
from astart.transforms.insertion import (
    InsertChanges,
    InsertSettings,
    insert_tree,
)

if TYPE_CHECKING:
    from argparse import Action, ArgumentParser
    from typing import TextIO

    from astart.docstrings.wrapping import WrapStyle
    from astart.transforms.constants import MagicScope


class TransformArguments(Protocol):
    """Typed arguments accepted only by the explicit transform command.

    Attributes:
        transform_source (str): Source filename.
        transform_output (str | None): Output filename, absent for standard
            output.
        transform_report (str | None): Optional machine-readable audit
            destination.
        wrap (bool): Whether to reflow documentation and comment AST nodes.
        replace_print (bool): Whether to replace lexically builtin print calls.
        optimize_aliases (bool): Whether to extract repeated type-only
            patterns.
        alias_min_savings (int): Minimum canonical characters saved by new
            aliases.
        alias_max_plans (int): Hard bound on alias plan evaluations.
        magic_scope (MagicScope): Explicit numeric extraction scope.
        wrap_style (WrapStyle): Preserve or convert documentation syntax.
        line_length (int): Available source columns for prose.
        boilerplate (bool): Insert TODO documentation nodes.
        remove_pass (bool): Remove redundant docstring-following pass nodes.
        add_return_none (bool): Add proven None return annotations.
        strip_sections (bool): Explicitly remove documentation sections.
        diff (bool): Show changes without writing the source.
        check (bool): Exit one when changes would be made, without writing
            source.

    """

    transform_source: str
    transform_output: str | None
    transform_report: str | None
    wrap: bool
    replace_print: bool
    optimize_aliases: bool
    alias_min_savings: int
    alias_max_plans: int
    magic_scope: MagicScope
    wrap_style: WrapStyle
    line_length: int
    boilerplate: bool
    remove_pass: bool
    add_return_none: bool
    strip_sections: bool
    diff: bool
    check: bool


class _OutputModes(Protocol):
    """Project only the mutually exclusive output options used here."""

    def add_argument(
        self,
        *names: str,
        action: str = "store",
        dest: str | None = None,
    ) -> Action:
        """Register an output option on the standard argparse group.

        Args:
            *names (str): Positional option spellings required by argparse.
            action (str): Standard store or store_true behavior.
            dest (str | None): Explicit namespace destination when needed.

        Returns:
            Registered argparse action.

        """
        ...


def configure_transform(*, command: ArgumentParser) -> None:
    """Configure the isolated opt-in transformation command.

    Args:
        command (ArgumentParser): Subcommand parser owned by the existing CLI
            entry point.

    """
    command.add_argument("transform_source", metavar="SOURCE")
    modes: _OutputModes = command.add_mutually_exclusive_group()
    modes.add_argument(
        "-o",
        "--output",
        dest="transform_output",
    )
    modes.add_argument("--diff", action="store_true")
    modes.add_argument("--check", action="store_true")
    command.add_argument("--report", dest="transform_report")
    command.add_argument(
        "--wrap",
        action="store_true",
        help="Reflow native documentation and comment nodes",
    )
    command.add_argument(
        "--replace-print",
        action="store_true",
        help="Inject a native helper for builtin print calls",
    )
    command.add_argument(
        "--optimize-aliases",
        action=BooleanOptionalAction,
        default=True,
        help="Extract repeated type patterns as native PEP 695 aliases "
        "(default: enabled)",
    )
    command.add_argument("--alias-min-savings", type=int, default=8)
    command.add_argument("--alias-max-plans", type=int, default=512)
    command.add_argument(
        "--magic-scope",
        default="off",
        choices=("off", "module", "function", "class"),
    )
    command.add_argument(
        "--doc-style",
        dest="wrap_style",
        default="preserve",
        choices=("preserve", "google", "numpy", "rest", "epytext"),
    )
    command.add_argument("--line-length", type=int, default=79)
    command.add_argument("--boilerplate", action="store_true")
    command.add_argument("--remove-pass", action="store_true")
    command.add_argument("--add-return-none", action="store_true")
    command.add_argument("--strip-sections", action="store_true")


def _validate_destinations(*, args: TransformArguments) -> None:
    """Reject report aliases before any source or report can be written.

    Args:
        args (TransformArguments): Explicit input/output/report selections.

    Raises:
        ValueError: The report would overwrite source or transformed output.
        OSError: A filesystem alias cannot be inspected.

    """
    if args.transform_report is None:
        return
    report: Path = Path(args.transform_report)
    destinations: list[Path] = [Path(args.transform_source)]
    if args.transform_output is not None:
        destinations.append(Path(args.transform_output))
    for destination in destinations:
        if report.resolve() == destination.resolve() or (
            report.exists()
            and destination.exists()
            and report.samefile(other_path=destination)
        ):
            msg: str = "The JSON report must not alias source or output."
            raise ValueError(msg)


def run_transform(*, args: TransformArguments, out: TextIO) -> int:
    """Apply chosen passes to one AST, then use the shared source emitter.

    Args:
        args (TransformArguments): Explicit subcommand arguments.
        out (TextIO): Caller-owned output stream, never closed here.

    Returns:
        int: One for check mode with pending changes, otherwise zero.

    Raises:
        OSError: An input/output/report path cannot be accessed.
        SyntaxError: Input syntax or shared emitted validation fails.
        UnicodeError: The source encoding cannot be decoded or encoded.
        ValueError: A transformation cannot preserve its documented contract.

    """
    _validate_destinations(args=args)
    path: Path = Path(args.transform_source)
    data: bytes = path.read_bytes()
    encoding: str = detect_encoding(
        readline=BytesIO(initial_bytes=data).readline,
    )[0]
    source: str = data.decode(encoding=encoding)
    tree: CommentedModule = CommentedModule.parse(
        source=source,
        filename=str(object=path),
    )
    aliases: AliasChanges | None = (
        AliasOptimizer(
            tree=tree,
            settings=AliasSettings(
                min_source_savings=args.alias_min_savings,
                max_plan_evaluations=args.alias_max_plans,
            ),
            module_id=str(object=path),
        ).optimize()
        if args.optimize_aliases
        else None
    )
    inserted: InsertChanges = insert_tree(
        tree=tree,
        settings=InsertSettings(
            replace_print=args.replace_print,
            magic_scope=args.magic_scope,
        ),
    )
    wrapped: WrapChanges = WrapChanges(
        docstrings_scanned=0,
        docstrings_changed=0,
        comment_blocks_changed=0,
        structural_changes=0,
        skipped=(),
    )
    doc_options: bool = (
        args.wrap or args.wrap_style != "preserve" or args.strip_sections
    )
    if (
        doc_options
        or args.boilerplate
        or args.remove_pass
        or args.add_return_none
    ):
        wrapped = wrap_tree(
            tree=tree,
            settings=WrapSettings(
                line_length=args.line_length,
                docstrings=doc_options,
                comments=args.wrap,
                style=args.wrap_style,
                boilerplate=args.boilerplate,
                remove_pass=args.remove_pass,
                add_return_none=args.add_return_none,
                strip_sections=args.strip_sections,
            ),
        )
    output: str = tree.unparse(preserve_formatting=True)
    changed: bool = output != source
    if args.transform_report:
        report: dict[str, str | int | bool | list[str] | None] = {
            "source_sha256": sha256(string=data).hexdigest(),
            "output_sha256": sha256(
                string=output.encode(
                    encoding=encoding,
                ),
            ).hexdigest(),
            "changed": changed,
            "aliases_added": len(aliases.declarations) if aliases else 0,
            "alias_annotations_changed": (
                aliases.annotations_changed if aliases else 0
            ),
            "alias_source_savings": aliases.source_savings if aliases else 0,
            "alias_plans_evaluated": aliases.plans_evaluated if aliases else 0,
            "alias_optimality_proven": (
                aliases.optimality_proven if aliases else False
            ),
            "alias_declaration_ids": (
                list(aliases.declaration_ids) if aliases else []
            ),
            "print_calls_changed": inserted.print_calls_changed,
            "numeric_values_changed": inserted.numeric_values_changed,
            "numeric_constants_added": inserted.numeric_constants_added,
            "helper_name": inserted.helper_name,
            "docstrings_scanned": wrapped.docstrings_scanned,
            "docstrings_changed": wrapped.docstrings_changed,
            "comment_blocks_changed": wrapped.comment_blocks_changed,
            "structural_changes": wrapped.structural_changes,
            "skipped": [
                *inserted.skipped,
                *wrapped.skipped,
                *(aliases.skipped if aliases else ()),
            ],
        }
        write_atomic(
            path=Path(args.transform_report),
            encoding="utf-8",
            text=dumps(obj=report, indent=2) + "\n",
        )
    if args.check:
        return int(changed)
    if args.diff:
        out.write(
            "".join(
                unified_diff(
                    a=source.splitlines(keepends=True),
                    b=output.splitlines(keepends=True),
                    fromfile=str(object=path),
                    tofile=str(object=path) + " (transformed)",
                ),
            ),
        )
    elif args.transform_output:
        write_atomic(
            path=Path(args.transform_output),
            text=output,
            encoding=encoding,
        )
    else:
        out.write(output)
    return 0
