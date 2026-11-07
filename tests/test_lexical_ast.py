"""Regression tests for semantic shebangs and immutable synchronized tokens."""

from __future__ import annotations

from ast import (
    AST,
    Assign,
    FunctionDef,
    Load,
    Module,
    Name,
    Store,
    TypeIgnore,
    dump,
    parse,
    walk,
)
from dataclasses import FrozenInstanceError
from io import StringIO
from textwrap import dedent
from tokenize import COMMENT, STRING, TokenInfo, generate_tokens
from typing import TYPE_CHECKING, Final, cast, final

import pytest
from astart.ast import (
    CommentedModule,
    ShebangArgument,
    ShebangInterpreter,
    ShebangNode,
    ShebangVariable,
    SingleLineComment,
    SuppressionComment,
)
from astart.docstrings import DocDescription, DocSummary, ModuleDocstringNode
from astart.node_attributes import read_attribute
from astart.tokens import LexicalToken, SourceSpan, TokenSnapshot

from tests.expectations import (
    expect_constant_expr,
    expect_equal,
    expect_false,
    expect_in,
    expect_instance,
    expect_is,
    expect_is_not,
    expect_name_expr,
    expect_named_node,
    expect_not_none,
    expect_true,
    expression_of_stmt,
)

if TYPE_CHECKING:
    from astart.docstrings import DocstringNode


@final
class Constants:
    """Group module-level constants.

    Attributes:
        min_node_count: Grouped module constant.

    """

    min_node_count: Final[int] = 20


@final
class Samples:
    """Shared source fixtures for structural and lexical tests.

    Attributes:
        source: Source containing comments, documentation and unicode.

    """

    source: str = dedent(
        text="""\
    #!/usr/bin/env -S python3 -I
    \"""Module summary.

    Module description with café.
    \"""

    # ordinary comment

    counter = 2

    def helper(value: int) -> int:
        \"""Produce a result.

        Extended detail.

        Args:
            value (int): Original value.

        Returns:
            int: Original result.
        \"""
        return value  # keep: E501
    """,
    )


def test_module_docstring_is_distinct_with_mutable_children() -> None:
    """A top-level string becomes a linked module-specific AST node."""
    tree: CommentedModule = CommentedModule.parse(source=Samples.source)
    module_doc: ModuleDocstringNode | None = tree.module_docstring
    if module_doc := expect_instance(
        value=module_doc,
        kind=ModuleDocstringNode,
    ):
        expect_instance(value=module_doc.summary_node, kind=DocSummary)
        expect_instance(value=module_doc.description_node, kind=DocDescription)
        expect_equal(
            actual=module_doc.summary_node.text,
            expected="Module summary.",
        )
        expect_equal(
            actual=module_doc.description_node.text,
            expected="Module description with café.",
        )
        expect_is(actual=module_doc.expression, expected=tree.body[0])
        expect_in(item=module_doc, container=tree.docstrings)
        expect_in(
            item=module_doc.summary_node,
            container=list(walk(node=tree)),
        )
        expect_in(
            item=module_doc.description_node,
            container=list(walk(node=tree)),
        )
        expect_equal(actual=tree.unparse(), expected=Samples.source)


def test_semantic_module_docstrings_are_both_editable_and_synchronized() -> (
    None
):
    """Changing a semantic child edits the real executable string constant."""
    tree: CommentedModule = CommentedModule.parse(source=Samples.source)
    doc: ModuleDocstringNode = expect_not_none(value=tree.module_docstring)
    doc.summary_node.text = "New module summary."
    doc.description_node.text = "A different explanation."
    result: str = tree.unparse()
    expect_in(item="New module summary.", container=result)
    expect_in(item="A different explanation.", container=result)
    expect_equal(actual=doc.summary, expected=doc.summary_node.text)
    expect_equal(actual=doc.description, expected=doc.description_node.text)
    expect_true(
        condition=str(
            object=expect_constant_expr(
                value=expression_of_stmt(
                    value=parse(source=result).body[0],
                ),
            ).value,
        ).startswith("New module summary."),
    )
    expect_equal(actual=tree.unparse(), expected=result)


def test_legacy_summary_fields_remain_editable() -> None:
    """Old summary/description string fields sync with new AST children."""
    tree: CommentedModule = CommentedModule.parse(source=Samples.source)
    doc: ModuleDocstringNode = expect_not_none(value=tree.module_docstring)
    doc.summary = "Backward compatible summary."
    doc.description = "Legacy detail."
    text: str = tree.unparse()
    expect_in(item="Backward compatible summary.", container=text)
    expect_in(item="Legacy detail.", container=text)
    expect_equal(
        actual=doc.summary_node.text,
        expected="Backward compatible summary.",
    )
    expect_equal(actual=doc.description_node.text, expected="Legacy detail.")


def test_conflicting_summary_changes_are_rejected() -> None:
    """Two disagreeing edits cannot silently overwrite one another."""
    tree: CommentedModule = CommentedModule.parse(source=Samples.source)
    doc: ModuleDocstringNode = expect_not_none(value=tree.module_docstring)
    doc.summary = "From legacy field."
    doc.summary_node.text = "From AST child."
    with pytest.raises(
        expected_exception=ValueError,
        match="Conflicting changes",
    ):
        tree.unparse()


@pytest.mark.parametrize(
    ("source", "expected_interpreter", "via_env", "options", "args"),
    [
        (
            """\
#!/usr/bin/python3
""",
            "/usr/bin/python3",
            False,
            [],
            [],
        ),
        (
            """\
#!/bin/bash -e
""",
            "/bin/bash",
            False,
            [],
            ["-e"],
        ),
        (
            """\
#!/usr/bin/env python3
""",
            "python3",
            True,
            [],
            [],
        ),
        (
            """\
#!/usr/bin/env -S python3 -I -X dev
""",
            "python3",
            True,
            ["-S"],
            ["-I", "-X", "dev"],
        ),
        (
            """\
#!/usr/bin/env -i -S python3 -O
""",
            "python3",
            True,
            ["-i", "-S"],
            ["-O"],
        ),
        (
            """\
#! /usr/bin/env -S python3 -B
""",
            "python3",
            True,
            ["-S"],
            ["-B"],
        ),
        (
            """\
#!
""",
            "",
            False,
            [],
            [],
        ),
        (
            """\
#!/usr/bin/env -u NAME python3 -O
""",
            "python3",
            True,
            ["-u", "NAME"],
            ["-O"],
        ),
    ],
)
def test_parse_shebang_components(
    *,
    source: str,
    expected_interpreter: str,
    via_env: bool,
    options: list[str],
    args: list[str],
) -> None:
    """Shebang lexer models direct executables and env-based launchers.

    Args:
        args: Collection of args supplied for this operation.
        expected_interpreter: Expected interpreter supplied as str for this
            operation.
        options: Options supplied as list[str] for this operation.
        source: The source examined while shebang lexer models direct
            executables and env-based launchers.
        via_env: Via env supplied as bool for this operation.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    shebang: ShebangNode | None = tree.shebang
    if shebang := expect_instance(value=shebang, kind=ShebangNode):
        expect_instance(value=shebang.interpreter, kind=ShebangInterpreter)
        expect_equal(
            actual=shebang.interpreter.path,
            expected=expected_interpreter,
        )
        expect_equal(
            actual=shebang.interpreter.name,
            expected=expected_interpreter.rsplit(sep="/", maxsplit=1)[-1],
        )
        expect_is(actual=shebang.interpreter.via_env, expected=via_env)
        expect_equal(
            actual=[part.value for part in shebang.launcher_options],
            expected=options,
        )
        expect_equal(
            actual=[part.value for part in shebang.arguments],
            expected=args,
        )
        expect_equal(actual=tree.unparse(), expected=source)
        expect_in(item=shebang, container=list(walk(node=tree)))
        expect_in(item=shebang.interpreter, container=list(walk(node=tree)))


def test_shebang_parses_environment_and_quoted_values() -> None:
    """Environment assignments are structured independent AST children."""
    source: str = """\
#!/usr/bin/env -S CONFIG="hello world" python3 -O
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    shebang: ShebangNode = expect_not_none(value=tree.shebang)
    assignment: ShebangVariable = shebang.environment[0]
    expect_equal(actual=assignment.name, expected="CONFIG")
    expect_equal(actual=assignment.value, expected="hello world")
    expect_in(item=assignment, container=list(walk(node=tree)))
    expect_equal(actual=tree.unparse(), expected=source)
    assignment.value = "changed value"
    current: str = tree.unparse()
    expect_in(item="CONFIG='changed value'", container=current)
    expect_in(item="python3 -O", container=current)
    expect_equal(actual=tree.unparse(), expected=current)


def test_shebang_interpreter_and_argument_editing() -> None:
    """Changing structured command segments edits the emitted shebang."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
#!/usr/bin/env -S python3 -O
print('ok')
""",
    )
    shebang: ShebangNode = expect_not_none(value=tree.shebang)
    shebang.interpreter.path = "python3.13"
    expect_equal(actual=shebang.interpreter.name, expected="python3.13")
    shebang.arguments[0].value = "-I"
    shebang.arguments.append(ShebangArgument(value="-B", role="option"))
    output: str = tree.unparse()
    expect_true(
        condition=output.startswith("""\
#!/usr/bin/env -S python3.13 -I -B
"""),
    )
    expect_equal(actual=tree.unparse(), expected=output)
    compile(source=tree, filename="<test>", mode="exec")


def test_raw_shebang_edit_reparses_semantics() -> None:
    """The raw comment can be edited when structured children are untouched."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
#!/bin/bash
pass
""",
    )
    shebang: ShebangNode = expect_not_none(value=tree.shebang)
    shebang.text = "#!/usr/bin/python3 -u"
    expect_true(condition=tree.unparse().startswith("#!/usr/bin/python3 -u"))
    expect_equal(actual=shebang.interpreter.path, expected="/usr/bin/python3")
    expect_equal(actual=shebang.arguments[0].value, expected="-u")
    expect_true(condition=tree.unparse().startswith("#!/usr/bin/python3 -u"))


def test_conflicting_shebang_edits_are_rejected() -> None:
    """Raw and structured shebang edits conflict rather than silently merge."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
#!/bin/bash
""",
    )
    shebang: ShebangNode = expect_not_none(value=tree.shebang)
    shebang.text = "#!/usr/bin/python3"
    shebang.interpreter.path = "/bin/sh"
    with pytest.raises(
        expected_exception=ValueError,
        match="Conflicting shebang",
    ):
        tree.unparse()


def test_shebang_components_cannot_introduce_newlines() -> None:
    """Semantically invalid shebang arguments fail closed."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
#!/bin/bash
""",
    )
    expect_not_none(value=tree.shebang).interpreter.path = """\
/bin/bash
malicious"""
    with pytest.raises(expected_exception=ValueError, match="newline"):
        tree.unparse()


def test_non_first_line_hashbang_is_ordinary_comment() -> None:
    """The #! prefix only acquires shebang semantics on physical line one."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
# ordinary
#!/bin/bash
x=1
""",
    )
    expect_is(actual=tree.shebang, expected=None)
    expect_instance(value=tree.comments[1], kind=SingleLineComment)


def test_original_source_token_stream_equals_python_tokenizer() -> None:
    """Public tokens retain every token's type, spelling, and positions."""
    tree: CommentedModule = CommentedModule.parse(source=Samples.source)
    stream: tuple[LexicalToken, ...] = tree.token_stream
    reference: tuple[TokenInfo, ...] = tuple(
        generate_tokens(
            readline=StringIO(initial_value=Samples.source).readline,
        ),
    )
    expect_equal(actual=len(stream), expected=len(reference))
    for semantic, original in zip(stream, reference, strict=True):
        expect_equal(actual=semantic.type, expected=original.type)
        expect_equal(actual=semantic.exact_type, expected=original.exact_type)
        expect_equal(actual=semantic.string, expected=original.string)
        expect_equal(actual=semantic.start, expected=original.start)
        expect_equal(actual=semantic.end, expected=original.end)
        expect_equal(actual=semantic.line, expected=original.line)
    expect_true(condition=any(token.type == COMMENT for token in stream))
    expect_true(condition=any(token.type == STRING for token in stream))
    expect_equal(actual=tree.token_source, expected=Samples.source)


def test_lexical_information_is_available_on_every_ast_child() -> None:
    """No Python or semantic AST child loses its lexical metadata accessor."""
    tree: CommentedModule = CommentedModule.parse(source=Samples.source)
    nodes: list[AST] = list(walk(node=tree))
    expect_true(condition=len(nodes) > Constants.min_node_count)
    for node in nodes:
        info: TokenSnapshot = tree.token_snapshot(node=node)
        info = expect_instance(value=info, kind=TokenSnapshot)
        expect_instance(value=info.span, kind=SourceSpan)
        expect_instance(value=info.tokens, kind=tuple)
        expect_is(
            actual=cast(
                typ="tuple[LexicalToken, ...] | None",
                val=read_attribute(node=node, name="tokens", kind=tuple),
            ),
            expected=info.tokens,
        )
        expect_equal(
            actual=tree.token_snapshot(node=node).source_text,
            expected=info.source_text,
        )
        expect_instance(value=info.source_revision, kind=int)
        expect_instance(value=info.provenance, kind=str)
    expect_true(condition=any(isinstance(node, Load) for node in nodes))
    expect_true(condition=any(isinstance(node, Store) for node in nodes))
    expect_instance(value=tree.body[-1], kind=FunctionDef)
    compile(source=tree, filename="<test>", mode="exec")


def test_lexical_snapshots_are_frozen_and_versioned() -> None:
    """Old immutable snapshots stay consistent after live AST mutations."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
value = 10
""",
    )
    assignment: Assign = expect_instance(value=tree.body[0], kind=Assign)
    value: Name = expect_instance(value=assignment.targets[0], kind=Name)
    before: TokenSnapshot = tree.token_snapshot(node=value)
    expect_equal(actual=before.source_text, expected="value")
    value.id = "renamed"
    after: TokenSnapshot = tree.token_snapshot(node=value)
    expect_equal(actual=after.source_text, expected="renamed")
    expect_true(condition=after.source_revision > before.source_revision)
    expect_equal(actual=before.source_text, expected="value")
    expect_equal(actual=before.tokens[0].string, expected="value")
    snapshot_field: str = "source_text"
    with pytest.raises(expected_exception=FrozenInstanceError):
        setattr(after, snapshot_field, "mutable")
    t_field: str = "string"
    with pytest.raises(expected_exception=FrozenInstanceError):
        setattr(after.tokens[0], t_field, "mutable")


def test_no_op_access_keeps_same_token_version() -> None:
    """Repeated access without an AST mutation must not rebuild snapshots."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
value = 10
""",
    )
    old: TokenSnapshot = tree.token_snapshot(node=tree.body[0])
    expect_is(actual=tree.token_snapshot(node=tree.body[0]), expected=old)
    expect_equal(
        actual=tree.token_snapshot(node=tree.body[0]).source_revision,
        expected=old.source_revision,
    )


def test_all_node_positions_track_reformatted_utf8_source() -> None:
    """UTF-8 byte offsets match AST fields even after regenerated edits."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
name = "café"
print(name)
""",
    )
    statement: Assign = expect_instance(value=tree.body[0], kind=Assign)
    expect_name_expr(value=statement.targets[0]).id = "école"
    snapshot: TokenSnapshot = tree.token_snapshot(node=statement.targets[0])
    expect_equal(actual=snapshot.source_text, expected="école")
    expect_equal(
        actual=snapshot.span.end_column,
        expected=len("école".encode()),
    )
    expect_equal(actual=snapshot.tokens[0].start_byte_column, expected=0)
    expect_equal(
        actual=snapshot.tokens[0].end_byte_column,
        expected=len("école".encode()),
    )


def test_token_metadata_reflects_comment_directive_edit() -> None:
    """A semantic suppression-rule change updates frozen COMMENT tokens."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            (
                """\
value = 1  __ASTART_FIXTURE_DIRECTIVE_4__: E501
"""
            ).replace(
                "__ASTART_FIXTURE_DIRECTIVE_4__",
                "# n" + "oqa",
            )
        ),
    )
    comment: SuppressionComment = expect_instance(
        value=tree.comments[0],
        kind=SuppressionComment,
    )
    old: TokenSnapshot = tree.token_snapshot(node=comment)
    comment.rules[0].code = "F841"
    latest: TokenSnapshot = tree.token_snapshot(node=comment)
    expect_equal(
        actual=old.tokens[0].string,
        expected=(
            ("__ASTART_FIXTURE_DIRECTIVE_4__: E501").replace(
                "__ASTART_FIXTURE_DIRECTIVE_4__",
                "# n" + "oqa",
            )
        ),
    )
    expect_equal(
        actual=latest.tokens[0].string,
        expected=(
            ("__ASTART_FIXTURE_DIRECTIVE_4__: F841").replace(
                "__ASTART_FIXTURE_DIRECTIVE_4__",
                "# n" + "oqa",
            )
        ),
    )
    expect_true(condition=latest.source_revision > old.source_revision)


def test_token_metadata_reflects_module_docstring_changes() -> None:
    """Summary children inherit updated physical STRING token information."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
\"""Old summary.\"""
""",
    )
    doc: ModuleDocstringNode = expect_not_none(value=tree.module_docstring)
    before: TokenSnapshot = tree.token_snapshot(node=doc.summary_node)
    doc.summary_node.text = "New summary."
    after: TokenSnapshot = tree.token_snapshot(node=doc.summary_node)
    expect_in(item="New summary.", container=after.source_text)
    expect_in(item="New summary.", container=after.tokens[0].string)
    expect_true(condition=before.source_revision < after.source_revision)
    expect_equal(actual=after.provenance, expected="inherited")


def test_append_statement_rebuilds_token_stream_in_place() -> None:
    """An in-place body-list append is detected without any setter hooks."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
#!/usr/bin/env python3
# keep header
value=1
""",
    )
    old: TokenSnapshot = tree.token_snapshot(node=tree)
    extra: Assign = expect_instance(
        value=parse(source="additional = 2").body[0],
        kind=Assign,
    )
    tree.body.append(extra)
    current: str = tree.token_source
    expect_true(
        condition=current.startswith("""\
#!/usr/bin/env python3
# keep header
"""),
    )
    expect_in(item="additional = 2", container=current)
    expect_equal(
        actual=tree.token_snapshot(node=extra).source_text,
        expected="additional = 2",
    )
    expect_true(
        condition=tree.token_snapshot(node=tree).source_revision
        > old.source_revision,
    )
    compile(source=tree, filename="<test>", mode="exec")


def test_detached_nodes_reject_stale_token_access() -> None:
    """Detached nodes retain no silently misleading source metadata."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1
y = 2
""",
    )
    detached: Assign = expect_instance(value=tree.body.pop(0), kind=Assign)
    with pytest.raises(
        expected_exception=ReferenceError,
        match="no longer part",
    ):
        _ = read_attribute(node=detached, name="token_info", kind=object)


def test_shebang_moved_never_displaces_first_physical_line() -> None:
    """New statements with colliding source numbers keep shebang on top."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
#!/bin/sh
value = 1
""",
    )
    extra: Assign = expect_instance(
        value=parse(source="other = 3").body[0],
        kind=Assign,
    )
    tree.body.insert(0, extra)
    result: str = tree.token_source
    expect_true(
        condition=result.startswith("""\
#!/bin/sh
"""),
    )
    expect_in(item="other = 3", container=result)


def test_no_module_docstring_when_module_does_not_begin_with_string() -> None:
    """Arbitrary later string expressions do not become module docs."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1
'not a module docstring'
""",
    )
    expect_is(actual=tree.module_docstring, expected=None)
    expect_false(condition=bool(tree.docstrings))


def test_docstring_render_conversion_preserves_semantic_children() -> None:
    """Independent summary/description children survive style conversion."""
    tree: CommentedModule = CommentedModule.parse(source=Samples.source)
    doc: ModuleDocstringNode | None = tree.module_docstring
    rendered: str = expect_not_none(value=doc).render(style="numpy")
    expect_true(condition=rendered.startswith("Module summary."))
    expect_in(item="Module description with café.", container=rendered)
    expect_equal(
        actual=expect_not_none(value=doc).summary_node.text,
        expected="Module summary.",
    )
    result: str = tree.unparse(doc_style="rest")
    expect_in(item="Module summary.", container=result)


def test_token_class_adaptation_does_not_change_ast_dump_semantics() -> None:
    """Ordinary AST serializers still recognize every standard class name."""
    source: str = """\
def f(x: int) -> int:
    return x
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    expected: Module = expect_instance(
        value=parse(source=source, type_comments=True),
        kind=Module,
    )
    expect_equal(
        actual=dump(
            node=type(expected)(
                body=tree.body,
                type_ignores=tree.type_ignores,
            ),
        ),
        expected=dump(node=expected),
    )
    expect_equal(actual=tree.unparse(), expected=source)


def test_direct_executable_constant_edit_refreshes_documentation() -> None:
    """Raw string edits update the module docstring's semantic index too."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
\"""Original summary.\"""
x = 3
""",
    )
    old: ModuleDocstringNode = expect_not_none(value=tree.module_docstring)
    expect_constant_expr(
        value=expression_of_stmt(value=tree.body[0]),
    ).value = """\
Changed summary.

New description."""
    expect_in(item="Changed summary.", container=tree.token_source)
    updated: ModuleDocstringNode = expect_not_none(value=tree.module_docstring)
    expect_is_not(actual=updated, unexpected=old)
    expect_equal(actual=updated.summary_node.text, expected="Changed summary.")
    expect_equal(
        actual=updated.description_node.text,
        expected="New description.",
    )
    expect_in(
        item="Changed summary.",
        container=tree.token_snapshot(node=updated.summary_node).source_text,
    )
    with pytest.raises(expected_exception=ReferenceError):
        _ = read_attribute(node=old, name="token_info", kind=object)


def test_removing_executable_docstring_removes_semantic_module_doc() -> None:
    """A changed leading non-string constant is no longer documentation."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
\"""Summary.\"""
""",
    )
    expect_constant_expr(
        value=expression_of_stmt(value=tree.body[0]),
    ).value = 42
    expect_equal(
        actual=tree.token_source,
        expected="""\
42
""",
    )
    expect_is(actual=tree.module_docstring, expected=None)
    expect_false(condition=bool(tree.docstrings))


def test_shebang_new_components_are_token_bound_after_unparse() -> None:
    """Raw shebang parsing attaches token providers to new children."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
#!/bin/sh
pass
""",
    )
    expect_not_none(value=tree.shebang).text = "#!/usr/bin/env -S python3 -I"
    tree.unparse()
    expect_in(
        item="python3",
        container=tree.token_snapshot(
            node=expect_not_none(value=tree.shebang).interpreter,
        ).source_text,
    )
    expect_in(
        item="-S",
        container=tree.token_snapshot(
            node=expect_not_none(value=tree.shebang).launcher_options[0],
        ).source_text,
    )


def test_inconsistent_shebang_launcher_metadata_rejected() -> None:
    """A user cannot claim env-based semantics without an env launcher."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
#!/bin/sh
""",
    )
    expect_not_none(value=tree.shebang).interpreter.via_env = True
    with pytest.raises(expected_exception=ValueError, match="Inconsistent"):
        tree.unparse()


def test_late_attached_comments_force_token_index_rebuild() -> None:
    """A mutable flat comment-list append is not missed by fingerprinting."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1
""",
    )
    old_version: int = tree.token_snapshot(node=tree).source_revision
    tree.comments.append(
        SingleLineComment(
            text="# late comment",
            inline=False,
            lineno=2,
            col_offset=0,
        ),
    )
    expect_in(item="# late comment", container=tree.token_source)
    expect_true(
        condition=tree.token_snapshot(node=tree.comments[-1]).source_revision
        > old_version,
    )


def test_native_type_ignore_node_maps_to_its_actual_comment_token() -> None:
    """ast.TypeIgnore gets specific source token metadata, not a fallback."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            (
                """\
x = something  __ASTART_FIXTURE_DIRECTIVE_3__[assignment]
"""
            ).replace("__ASTART_FIXTURE_DIRECTIVE_3__", "# t" + "ype: ignore")
        ),
    )
    ignore: TypeIgnore = tree.type_ignores[0]
    before: TokenSnapshot = tree.token_snapshot(node=ignore)
    expect_equal(
        actual=before.tokens[0].string,
        expected=(
            ("__ASTART_FIXTURE_DIRECTIVE_3__[assignment]").replace(
                "__ASTART_FIXTURE_DIRECTIVE_3__",
                "# t" + "ype: ignore",
            )
        ),
    )
    expect_equal(actual=before.provenance, expected="own")
    typed_comment: SuppressionComment = expect_instance(
        value=tree.comments[0],
        kind=SuppressionComment,
    )
    typed_comment.rules[0].code = "attr-defined"
    updated: TokenSnapshot = tree.token_snapshot(node=ignore)
    expect_equal(
        actual=updated.tokens[0].string,
        expected=(
            ("__ASTART_FIXTURE_DIRECTIVE_3__[attr-defined]").replace(
                "__ASTART_FIXTURE_DIRECTIVE_3__",
                "# t" + "ype: ignore",
            )
        ),
    )
    expect_true(condition=updated.source_revision > before.source_revision)


@pytest.mark.parametrize(
    "source",
    [
        """\
class Value:
    def f(self):
        return 3
""",
        """\
def f(a, /, b: int = 2, *, c: str = 'x'):
    return a + b
""",
        """\
async def f(xs):
    async for x in xs:
        yield x
""",
        (
            """\
try:
    risky()
except ValueError as exc:
    raise
finally:
    pass
"""
        ),
        (
            """\
match value:
    case [x, y]:
        return_value = x + y
    case _:
        pass
"""
        ),
        """\
result = [x ** 2 for x in range(3) if x % 2 == 0]
""",
        """\
from typing import Final
CONSTANT: Final[int] = 5
""",
        (
            dedent(
                text="""\
    def f():
        with open('x') as stream:
            return stream.read()
    """,
            )
        ),
        """\
def f(n):
    return f'{n!r:>10}'
""",
        """\
def f():
    '''Summary.'''
    # inside
    pass
""",
        (
            (
                dedent(
                    text="""\
    __ASTART_FIXTURE_DIRECTIVE_3__[unused-ignore]
    # pragma: no cover
    x = 1
    """,
                )
            ).replace("__ASTART_FIXTURE_DIRECTIVE_3__", "# t" + "ype: ignore")
        ),
        """\
def f[T](value: T) -> T:
    return value
""",
    ],
)
def test_token_index_walks_advanced_python_syntax(source: str) -> None:
    """All ordinary AST node kinds retain lexical metadata and compilation.

    Args:
        source: The source examined while all ordinary AST node kinds
            retain lexical metadata and compilation.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(actual=tree.token_source, expected=source)
    expect_true(
        condition=all(
            expect_instance(
                value=tree.token_snapshot(node=node),
                kind=TokenSnapshot,
            )
            for node in walk(node=tree)
        ),
    )
    expect_equal(
        actual=dump(node=parse(source=tree.unparse(), type_comments=True)),
        expected=dump(node=parse(source=source, type_comments=True)),
    )
    compile(source=tree, filename="<test>", mode="exec")


def test_shebang_remains_first_during_docstring_and_code_changes() -> None:
    """Regenerating module docs never pushes the shebang below code."""
    tree: CommentedModule = CommentedModule.parse(source=Samples.source)
    expect_not_none(
        value=tree.module_docstring,
    ).summary_node.text = "Changed module summary."
    expect_named_node(value=tree.body[-1]).name = "updated_helper"
    result: str = tree.token_source
    expect_true(
        condition=result.startswith("""\
#!/usr/bin/env -S python3 -I
"""),
    )
    expect_in(item="Changed module summary.", container=result)
    expect_in(item="def updated_helper", container=result)
    expect_equal(
        actual=tree.token_snapshot(
            node=expect_not_none(value=tree.shebang),
        ).span.start_line,
        expected=1,
    )


@pytest.mark.parametrize(
    "text",
    [
        "# not a shebang",
        """\
#!/bin/sh
second line""",
        "#!/bin/sh\r",
    ],
)
def test_raw_shebang_edit_must_remain_first_line_directive(text: str) -> None:
    """Changing a shebang to arbitrary or multiline text fails closed.

    Args:
        text: Text supplied as str for this operation.

    """
    tree: CommentedModule = CommentedModule.parse(
        source="""\
#!/bin/sh
""",
    )
    expect_not_none(value=tree.shebang).text = text
    with pytest.raises(expected_exception=ValueError, match="first-line"):
        tree.unparse()


def test_invalid_new_env_variable_name_is_rejected() -> None:
    """Malformed edited environment assignments never change meaning."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
#!/usr/bin/env -S CONFIG=1 python3
""",
    )
    expect_not_none(value=tree.shebang).environment[0].name = "INVALID-NAME"
    with pytest.raises(expected_exception=ValueError, match="variable name"):
        tree.unparse()


def test_newly_inserted_module_docstring_is_discovered_automatically() -> None:
    """Adding a leading AST string expression updates the semantic index."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
value = 1
""",
    )
    tree.body.insert(0, parse(source='"""Added summary."""').body[0])
    doc: ModuleDocstringNode = expect_not_none(value=tree.module_docstring)
    doc = expect_instance(value=doc, kind=ModuleDocstringNode)
    expect_equal(actual=doc.summary_node.text, expected="Added summary.")
    expect_in(item="Added summary.", container=tree.token_source)
    expect_equal(
        actual=tree.token_snapshot(node=doc.summary_node).tokens[0].type,
        expected=STRING,
    )


def test_inserted_function_docstring_preserves_edited_docs() -> None:
    """Structural indexing keeps documentation edits and node identity."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def original():
    '''Old.'''
    return 1
""",
    )
    first: DocstringNode = tree.docstrings[0]
    first.summary_node.text = "Edited existing."
    tree.body.append(
        parse(
            source="""\
def added():
    '''Added function.'''
    return 2
""",
        ).body[0],
    )
    result: str = tree.token_source
    expect_equal(actual=len(tree.docstrings), expected=2)
    expect_is(actual=tree.docstrings[0], expected=first)
    expect_in(item="Edited existing.", container=result)
    expect_in(item="Added function.", container=result)


def test_removed_docstring_with_pending_edits_fails_closed() -> None:
    """Structural edits must not silently drop unapplied semantic doc edits."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f():
    '''Original.'''
    pass
""",
    )
    tree.docstrings[0].summary_node.text = "Modified."
    tree.body.pop(0)
    with pytest.raises(
        expected_exception=ValueError,
        match="pending structured edits",
    ):
        tree.unparse()


def test_removed_unchanged_docstring_owner_updates_index() -> None:
    """Deleting a function removes its detached documentation node."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f():
    '''Original.'''
    pass
x = 2
""",
    )
    old: DocstringNode = tree.docstrings[0]
    tree.body.pop(0)
    expect_equal(
        actual=tree.token_source,
        expected="""\
x = 2
""",
    )
    expect_false(condition=bool(tree.docstrings))
    with pytest.raises(expected_exception=ReferenceError):
        _ = tree.token_snapshot(node=old.summary_node)
