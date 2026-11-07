"""Object-oriented command-line application."""

from __future__ import annotations

from argparse import (
    ArgumentParser,
    Namespace,
)
from dataclasses import dataclass
from pathlib import Path
from sys import stdout
from typing import Protocol, Self

from astart._graph.conversion.artifacts import (
    ConversionArtifactPaths,
    ConversionArtifactWriter,
    ConversionRunSummary,
)
from astart._graph.conversion.engine import (
    ConversionResult,
    GraphOnlyConverter,
)


class ApplicationCommand(Protocol):
    """Executable command produced by the CLI parser."""

    @staticmethod
    def run() -> int:
        """Run the command and return a process exit code.

        Returns:
            Process exit status; zero indicates successful completion.

        Raises:
            NotImplementedError: If this operation cannot satisfy its
                documented contract.

        """
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class ConvertCommand:
    """Convert a Python file through the graph inference pipeline.

    Attributes:
        artifacts: Artifacts retained as ConversionArtifactPaths
            by this instance.
        source_path: Path to the source used by this instance.
        stubs_path: Path to the stubs used by this instance.

    """

    source_path: Path
    stubs_path: Path
    artifacts: ConversionArtifactPaths

    @classmethod
    def from_namespace(cls, *, namespace: Namespace) -> Self:
        """Create a convert command from parsed CLI arguments.

        Args:
            namespace: Namespace supplied as Namespace for this operation.

        Returns:
            Self produced by this operation.

        """
        return cls(
            source_path=Path(namespace.source),
            stubs_path=Path(namespace.stubs),
            artifacts=ConversionArtifactPaths.from_strings(
                output=namespace.output,
                explanation=namespace.explain,
            ),
        )

    def run(self) -> int:
        """Run conversion and write requested artifacts.

        Returns:
            Process exit status; zero indicates successful completion.

        """
        converter: GraphOnlyConverter = GraphOnlyConverter.create(
            stubs_path=self.stubs_path,
        )
        result: ConversionResult = converter.convert_file(
            source_path=self.source_path,
        )
        writer: ConversionArtifactWriter = ConversionArtifactWriter(
            paths=self.artifacts,
        )
        summary: ConversionRunSummary = writer.write(result=result)
        stdout.write(summary.to_console_text())
        return 0


@dataclass(frozen=True, slots=True)
class SmokeCommand:
    """Print a package smoke-test message.

    Attributes:
        package_version: Package version retained as str by this instance.

    """

    package_version: str = "v33"

    def run(self) -> int:
        """Run the smoke command.

        Returns:
            Process exit status; zero indicates successful completion.

        """
        stdout.write(
            f"""\
astart inference API {self.package_version}
Full staged API pipeline modules are importable.
""",
        )
        return 0


@dataclass(frozen=True, slots=True)
class CommandLineParser:
    """Parse command-line arguments into command objects.

    Attributes:
        parser: Parser retained as ArgumentParser by this instance.

    """

    parser: ArgumentParser

    @classmethod
    def create(cls) -> Self:
        """Create the standard parser.

        Returns:
            Self produced by this operation.

        """
        parser: ArgumentParser = ArgumentParser(prog="astart")
        convert_parser: ArgumentParser = (
            parser.add_subparsers(dest="command")
        ).add_parser(name="convert")
        convert_parser.add_argument("--source", required=True)
        convert_parser.add_argument("--stubs", required=True)
        convert_parser.add_argument("--output", required=True)
        convert_parser.add_argument("--explain", required=False)
        return cls(parser=parser)

    def parse(self, *, arguments: list[str]) -> ApplicationCommand:
        """Parse arguments into a command object.

        Args:
            arguments: Collection of arguments supplied for this operation.

        Returns:
            ApplicationCommand produced by this operation.

        """
        namespace: Namespace = self.parser.parse_args(args=arguments)
        if namespace.command == "convert":
            return ConvertCommand.from_namespace(namespace=namespace)
        return SmokeCommand()


@dataclass(frozen=True, slots=True)
class CommandLineApplication:
    """Application object used by ``python -m astart``.

    Attributes:
        parser: Parser retained as CommandLineParser by this instance.

    """

    parser: CommandLineParser

    @classmethod
    def create(cls) -> Self:
        """Create the default command-line application.

        Returns:
            Self produced by this operation.

        """
        return cls(parser=CommandLineParser.create())

    def run(self, *, arguments: list[str]) -> int:
        """Parse and run a command.

        Args:
            arguments: Collection of arguments supplied for this operation.

        Returns:
            Process exit status; zero indicates successful completion.

        """
        command: ApplicationCommand = self.parser.parse(arguments=arguments)
        return command.run()
