"""Exercise the graph command-line application and conversion artifacts."""

from __future__ import annotations

from io import StringIO
from json import dumps
from textwrap import dedent
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.graph import GraphOnlyConverter
from astart.graph.application import cli
from astart.graph.application.cli import (
    ApplicationCommand,
    CommandLineApplication,
    CommandLineParser,
    ConvertCommand,
    SmokeCommand,
)
from astart.graph.conversion import artifacts
from astart.graph.conversion.artifacts import (
    ConversionArtifactPaths,
    ConversionArtifactWriter,
    ConversionRunSummary,
    format_source,
)
from astart.graph.inference.explanations import (
    ExplanationSummary,
    InferenceExplanationReport,
)

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_instance,
    expect_is,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from astart.graph.conversion.engine import ConversionResult
    from astart.graph.inference.explanations import JsonObject


@final
class Constants:
    """Group module-level constants.

    Attributes:
        source (Final[str]): Grouped module constant.

    """

    source: Final[str] = dedent(
        text="""\
    def add(x, y):
        return x + y

    def first(items):
        return items[0]

    class Box:
        def __init__(self, value):
            self.value = value

    total = add(1, 2)
    head = first([1, 2, 3])
    """,
    )


def _convert(*, tmp_path: Path) -> ConversionResult:
    """Convert the sample source in a temporary directory.

    Args:
        tmp_path (Path): Directory holding the sample source file.

    Returns:
        ConversionResult: Complete conversion result for the sample.

    """
    path: Path = tmp_path / "sample.py"
    path.write_text(data=Constants.source, encoding="utf-8")
    return GraphOnlyConverter.create(stubs_path=tmp_path).convert_file(
        source_path=path,
    )


def test_protocol_command_stub_raises() -> None:
    """Keep the abstract protocol entry point explicit."""
    run: Callable[[], int] = vars(ApplicationCommand)["run"].__func__
    with pytest.raises(expected_exception=NotImplementedError):
        run()


def test_parser_selects_commands() -> None:
    """Choose a convert or smoke command from parsed arguments."""
    parser: CommandLineParser = CommandLineParser.create()
    convert: ApplicationCommand = parser.parse(
        arguments=[
            "convert",
            "--source",
            "a.py",
            "--stubs",
            "stubs",
            "--output",
            "out.py",
            "--explain",
            "why.md",
        ],
    )
    smoke: ApplicationCommand = parser.parse(arguments=[])
    command: ConvertCommand = expect_instance(
        value=convert,
        kind=ConvertCommand,
    )
    expect_equal(actual=command.artifacts.output_path.name, expected="out.py")
    expect_instance(value=smoke, kind=SmokeCommand)


def test_smoke_command_writes_banner(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Print the package banner for the default command.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture replacing the module's stdout
            handle.

    """
    buffer: StringIO = StringIO()
    monkeypatch.setattr(target=cli, name="stdout", value=buffer)
    expect_equal(
        actual=CommandLineApplication.create().run(arguments=[]),
        expected=0,
    )
    expect_in(item="astart inference API", container=buffer.getvalue())


def test_convert_command_writes_outputs(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run a conversion and write the source and explanation files.

    Args:
        tmp_path (Path): Directory for inputs and outputs.
        monkeypatch (pytest.MonkeyPatch): Fixture replacing the module's stdout
            handle.

    """
    buffer: StringIO = StringIO()
    monkeypatch.setattr(target=cli, name="stdout", value=buffer)
    source: Path = tmp_path / "in.py"
    source.write_text(data=Constants.source, encoding="utf-8")
    output: Path = tmp_path / "nested" / "out.py"
    explanation: Path = tmp_path / "docs" / "why.md"
    status: int = CommandLineApplication.create().run(
        arguments=[
            "convert",
            "--source",
            str(object=source),
            "--stubs",
            str(object=tmp_path),
            "--output",
            str(object=output),
            "--explain",
            str(object=explanation),
        ],
    )
    expect_equal(actual=status, expected=0)
    expect_true(condition=output.exists())
    expect_true(condition=(output.parent / "__init__.py").exists())
    expect_in(
        item="# Inference explanation report",
        container=explanation.read_text(encoding="utf-8"),
    )
    expect_in(item="converted", container=buffer.getvalue())


def test_artifact_paths_from_strings() -> None:
    """Build artifact paths with and without an explanation."""
    plain: ConversionArtifactPaths = ConversionArtifactPaths.from_strings(
        output="out.py",
    )
    full: ConversionArtifactPaths = ConversionArtifactPaths.from_strings(
        output="out.py",
        explanation="why.md",
    )
    expect_is(actual=plain.explanation_path, expected=None)
    explanation: Path = expect_not_none(value=full.explanation_path)
    expect_equal(actual=explanation.name, expected="why.md")


def test_writer_skips_optional_explanation(*, tmp_path: Path) -> None:
    """Write only the source when no explanation path is configured.

    Args:
        tmp_path (Path): Directory for the converted output.

    """
    result: ConversionResult = _convert(tmp_path=tmp_path)
    output: Path = tmp_path / "out" / "result.py"
    summary: ConversionRunSummary = ConversionArtifactWriter(
        paths=ConversionArtifactPaths(output_path=output),
    ).write(result=result)
    expect_true(condition=output.exists())
    expect_in(item="annotation_plans:", container=summary.to_console_text())
    expect_in(item="sample.py", container=summary.source)


def test_summary_marks_memory_sources(*, tmp_path: Path) -> None:
    """Describe in-memory conversions without a source path.

    Args:
        tmp_path (Path): Directory used for the output path.

    """
    converter: GraphOnlyConverter = GraphOnlyConverter.create(
        stubs_path=tmp_path,
    )
    result: ConversionResult = converter.convert_text(source=Constants.source)
    summary: ConversionRunSummary = ConversionRunSummary.from_result(
        result=result,
        output_path=tmp_path / "x.py",
    )
    expect_equal(actual=summary.source, expected="<memory>")
    expect_equal(
        actual=converter.convert_source(source=Constants.source),
        expected=result.output_source,
    )


class _Failed:
    """Completed process stand-in with a failing status.

    Attributes:
        returncode (int): Non-zero exit status.
        stdout (str): Empty standard output.

    """

    returncode: int = 1
    stdout: str = ""


class _Formatted:
    """Completed process stand-in with formatted output.

    Attributes:
        returncode (int): Zero exit status.
        stdout (str): Formatted source text.

    """

    returncode: int = 0
    stdout: str = """\
x = 2
"""


def _return_none(**kwargs: str | bool | list[str]) -> None:
    """Report that no executable exists.

    Args:
        kwargs (str | bool | list[str]): Ignored keyword arguments.

    """


def _return_shell(**kwargs: str | bool | list[str]) -> str:
    """Report a fake executable path.

    Args:
        kwargs (str | bool | list[str]): Ignored keyword arguments.

    Returns:
        str: Path of a fake formatter.

    """
    _ = kwargs
    return "/bin/sh"


def _return_failed(**kwargs: str | bool | list[str]) -> _Failed:
    """Return a failed process stand-in.

    Args:
        kwargs (str | bool | list[str]): Ignored keyword arguments.

    Returns:
        _Failed: Failing stand-in.

    """
    _ = kwargs
    return _Failed()


def _return_formatted(**kwargs: str | bool | list[str]) -> _Formatted:
    """Return a successful process stand-in.

    Args:
        kwargs (str | bool | list[str]): Ignored keyword arguments.

    Returns:
        _Formatted: Formatting stand-in.

    """
    _ = kwargs
    return _Formatted()


def test_format_source_variants(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fall back to the input when ruff is missing or rejects the text.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture controlling executable
            discovery.

    """
    monkeypatch.setattr(target=artifacts, name="which", value=_return_none)
    expect_equal(
        actual=format_source(
            source="""\
x = 'a'
""",
        ),
        expected="""\
x = 'a'
""",
    )
    monkeypatch.setattr(target=artifacts, name="which", value=_return_shell)
    monkeypatch.setattr(target=artifacts, name="run", value=_return_failed)
    expect_equal(
        actual=format_source(
            source="""\
x = 1
""",
        ),
        expected="""\
x = 1
""",
    )
    monkeypatch.setattr(target=artifacts, name="run", value=_return_formatted)
    expect_equal(
        actual=format_source(
            source="""\
x=1
""",
        ),
        expected="""\
x = 2
""",
    )


def test_explanation_report_serializes(*, tmp_path: Path) -> None:
    """Render the explanation as JSON data and markdown.

    Args:
        tmp_path (Path): Directory holding the converted sample.

    """
    result: ConversionResult = _convert(tmp_path=tmp_path)
    report: InferenceExplanationReport = result.explanation
    data: JsonObject = report.to_json_data()
    expect_true(condition=len(dumps(obj=data)) > 0)
    markdown: str = report.to_markdown()
    expect_in(item="## Pipeline stages", container=markdown)
    expect_in(item="## Annotation explanations", container=markdown)


def test_explanation_report_lists_warnings_and_messages() -> None:
    """Include warnings and validation messages in the markdown report."""
    report: InferenceExplanationReport = InferenceExplanationReport(
        summary=ExplanationSummary(
            annotation_count=0,
            evidence_count=0,
            average_confidence=0.0,
            warning_count=1,
            stage_count=1,
        ),
        annotations=(),
        warnings=("careful",),
        stage_names=("stage",),
        validation_messages=("fine",),
    )
    markdown: str = report.to_markdown()
    expect_in(item="## Warnings", container=markdown)
    expect_in(item="## Validation messages", container=markdown)
    expect_in(item="careful", container=markdown)
