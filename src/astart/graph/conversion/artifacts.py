"""Output artifact models and writers for conversion runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from shutil import which
from subprocess import run
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from subprocess import CompletedProcess

    from astart.graph.conversion.engine import ConversionResult


def format_source(*, source: str) -> str:
    """Normalize source through ``ruff format`` (double quotes, layout).

    ``ast.unparse`` always emits single-quoted strings, which violates the
    ``ruff`` double-quote preference (Q000). Running the canonical formatter
    over the generated text resolves quote style and line layout uniformly
    without keying on any source-specific identifier. If ``ruff`` is not
    available the original text is returned unchanged.

    Args:
        source (str): The source examined while normalize source through ``ruff
            format`` (double quotes, layout).

    Returns:
        str: Rendered source text produced by this operation.

    """
    executable: str | None = which(cmd="ruff")
    if executable is None:
        return source
    completed: CompletedProcess[str] = run(
        args=[executable, "format", "-"],
        input=source,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout:
        return source
    return completed.stdout


@dataclass(frozen=True, slots=True)
class ConversionArtifactPaths:
    """Filesystem destinations for one conversion run.

    Attributes:
        explanation_path (Path | None): Path to the explanation used by this
            instance.
        output_path (Path): Path to the output used by this instance.

    """

    output_path: Path
    explanation_path: Path | None = None

    @classmethod
    def from_strings(
        cls,
        *,
        output: str,
        explanation: str | None = None,
    ) -> Self:
        """Create artifact paths from CLI string arguments.

        Args:
            explanation (str | None): Explanation supplied as str | None for
                this operation.
            output (str): Output supplied as str for this operation.

        Returns:
            Self: Self produced by this operation.

        """
        explanation_path: Path | None = (
            None if explanation is None else Path(explanation)
        )
        return cls(
            output_path=Path(output),
            explanation_path=explanation_path,
        )


@dataclass(frozen=True, slots=True)
class ConversionRunSummary:
    """Small human-readable summary for a completed conversion run.

    Attributes:
        annotation_plans (int): Annotation plans retained as int by this
            instance.
        explanations (int): Explanations retained as int by this instance.
        hypotheses (int): Hypotheses retained as int by this instance.
        output (str): Output retained as str by this instance.
        source (str): Original source text retained for parsing and
            reconstruction.
        stages (tuple[str, ...]): Stages retained as tuple[str, ...] by this
            instance.

    """

    source: str
    output: str
    annotation_plans: int
    hypotheses: int
    explanations: int
    stages: tuple[str, ...]

    @classmethod
    def from_result(
        cls,
        *,
        result: ConversionResult,
        output_path: Path,
    ) -> Self:
        """Build a run summary from a conversion result.

        Args:
            output_path (Path): Filesystem path identifying the output.
            result (ConversionResult): The result examined while build a run
                summary from a conversion result.

        Returns:
            Self: Self produced by this operation.

        """
        source: str = (
            "<memory>"
            if result.source_path is None
            else str(object=result.source_path)
        )
        return cls(
            source=source,
            output=str(object=output_path),
            annotation_plans=len(result.inference.annotation_plans),
            hypotheses=len(result.inference.hypotheses),
            explanations=result.explanation.summary.annotation_count,
            stages=result.stage_names,
        )

    def to_console_text(self) -> str:
        """Render the summary as CLI output.

        Returns:
            str: Rendered source text produced by this operation.

        """
        return f"""\
converted {self.source} -> {self.output}
annotation_plans: {self.annotation_plans}
hypotheses: {self.hypotheses}
explanations: {self.explanations}
stages: {", ".join(self.stages)}
"""


@dataclass(frozen=True, slots=True)
class ConversionArtifactWriter:
    """Write conversion artifacts to disk.

    Attributes:
        paths (ConversionArtifactPaths): Paths retained as
            ConversionArtifactPaths by this instance.

    """

    paths: ConversionArtifactPaths

    def write(self, *, result: ConversionResult) -> ConversionRunSummary:
        """Write configured artifacts and return a CLI summary.

        Args:
            result (ConversionResult): The result examined while write
                configured
                artifacts and return a CLI summary.

        Returns:
            ConversionRunSummary:
                ConversionRunSummary produced by this operation.

        """
        self._write_output(source=result.output_source)
        self._write_explanation(markdown=result.explanation.to_markdown())
        return ConversionRunSummary.from_result(
            result=result,
            output_path=self.paths.output_path,
        )

    def _write_output(self, *, source: str) -> None:
        """Write the inferred source file.

        Args:
            source (str): The source examined while write the inferred source
                file.

        """
        self.paths.output_path.parent.mkdir(parents=True, exist_ok=True)
        init_path: Path = self.paths.output_path.parent / "__init__.py"
        if not init_path.exists():
            init_path.write_text(data="", encoding="utf-8")
        formatted: str = format_source(source=source)
        self.paths.output_path.write_text(data=formatted, encoding="utf-8")

    def _write_explanation(self, *, markdown: str) -> None:
        """Write the optional explanation report.

        Args:
            markdown (str): Markdown supplied as str for this operation.

        """
        if self.paths.explanation_path is None:
            return
        self.paths.explanation_path.parent.mkdir(parents=True, exist_ok=True)
        self.paths.explanation_path.write_text(data=markdown, encoding="utf-8")
