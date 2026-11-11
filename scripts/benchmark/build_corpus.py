"""Build the external annotation-recovery corpus from pinned wheels.

The stdlib corpus is mostly untyped code. This corpus complements it with real
library and application code that is already fully annotated, so stripping the
annotations leaves an unambiguous ground truth. Every package is pinned by
version and wheel hash; every selected module is copied unchanged next to a
manifest that records where it came from, and the package's license text is
kept alongside.

Usage::

    python -m scripts.benchmark.build_corpus pin   # resolve latest, write pins
    python -m scripts.benchmark.build_corpus build # fetch, verify, extract

"""

from __future__ import annotations

from argparse import ArgumentParser
from ast import AsyncFunctionDef, FunctionDef, arg, arguments, parse, walk
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from subprocess import run
from sys import executable
from tempfile import TemporaryDirectory
from typing import Final, final
from zipfile import ZipFile


@final
class Constants:
    """Group module-level constants.

    Attributes:
        packages (Final[tuple[str, ...]]): Distributions to draw modules from.
        pins (Final[Path]): Pin file: version and wheel hash per distribution.
        output (Final[Path]): Directory receiving the corpus.
        min_lines (Final[int]): Fewest lines a module may have.
        max_lines (Final[int]): Most lines a module may have.
        min_functions (Final[int]): Fewest functions a module must define.
        min_density (Final[float]): Least fraction of parameters and returns
            annotated.
        per_package (Final[int]): Most modules taken from one distribution.
        skipped (Final[frozenset[str]]): Path parts that mark tests, vendored
            or generated code.
        licenses (Final[tuple[str, ...]]): Wheel metadata file names that hold
            license text.

    """

    packages: Final[tuple[str, ...]] = (
        "rich",
        "httpx",
        "httpcore",
        "h11",
        "anyio",
        "starlette",
        "click",
        "cattrs",
        "packaging",
        "tomli",
        "tomlkit",
        "markdown-it-py",
        "pluggy",
        "platformdirs",
        "filelock",
        "jinja2",
        "werkzeug",
        "flask",
        "itsdangerous",
        "structlog",
        "tenacity",
        "humanize",
        "arrow",
        "fastapi",
        "pytest",
    )
    pins: Final[Path] = Path(
        "scripts/benchmark/artifacts/resources/external_corpus.json",
    )
    output: Final[Path] = Path("tests/corpus/extended")
    min_lines: Final[int] = 60
    max_lines: Final[int] = 1500
    min_functions: Final[int] = 6
    min_density: Final[float] = 0.9
    per_package: Final[int] = 8
    skipped: Final[frozenset[str]] = frozenset(
        {"tests", "test", "testing", "_vendor", "vendored", "__pycache__"},
    )
    licenses: Final[tuple[str, ...]] = (
        "LICENSE",
        "LICENCE",
        "COPYING",
        "NOTICE",
    )


def _download(*, spec: str, into: Path) -> Path:
    """Download one pure-Python wheel without dependencies.

    Args:
        spec (str): Requirement such as ``rich`` or ``rich==13.9.4``.
        into (Path): Directory receiving the wheel.

    Returns:
        Path: The wheel's path.

    Raises:
        RuntimeError: If pip could not fetch exactly one wheel.

    """
    _ = run(
        args=[
            executable,
            "-m",
            "pip",
            "download",
            "--no-deps",
            "--only-binary",
            ":all:",
            "--dest",
            str(object=into),
            "-q",
            spec,
        ],
        check=False,
        capture_output=True,
    )
    wheels: list[Path] = sorted(into.glob(pattern="*.whl"))
    if len(wheels) != 1:
        msg: str = f"{spec}: expected one wheel, found {len(wheels)}"
        raise RuntimeError(msg)
    return wheels[0]


def _density(*, source: str) -> tuple[int, float]:
    """Measure how completely a module is annotated.

    Args:
        source (str): Module text.

    Returns:
        tuple[int, float]: The number of functions and the fraction of their
            parameters
            (receivers excluded) and returns that carry an annotation.

    """
    functions: int = 0
    annotated: int = 0
    total: int = 0
    for node in walk(node=parse(source=source)):
        if not isinstance(node, (FunctionDef, AsyncFunctionDef)):
            continue
        functions += 1
        arguments: arguments = node.args
        parameters: list[arg] = [
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
        ]
        parameters = [
            item
            for position, item in enumerate(iterable=parameters)
            if not (position == 0 and item.arg in {"self", "cls"})
        ]
        total += len(parameters) + 1
        annotated += sum(item.annotation is not None for item in parameters)
        annotated += node.returns is not None
    return functions, (annotated / total if total else 0.0)


def _candidates(*, wheel: ZipFile) -> list[tuple[str, str, int, float]]:
    """Pick the modules of a wheel worth keeping, best first.

    Args:
        wheel (ZipFile): Opened wheel.

    Returns:
        list[tuple[str, str, int, float]]:
            ``(path, source, functions, density)`` for
            each acceptable module, most functions first.

    """
    found: list[tuple[str, str, int, float]] = []
    for name in wheel.namelist():
        parts: tuple[str, ...] = Path(name).parts
        if (
            not name.endswith(".py")
            or Constants.skipped & set(parts)
            or parts[0].endswith((".dist-info", ".data"))
            or Path(name).name == "__init__.py"
        ):
            continue
        source: str = wheel.read(name=name).decode(encoding="utf-8")
        lines: int = source.count("\n")
        if not Constants.min_lines <= lines <= Constants.max_lines:
            continue
        try:
            functions, density = _density(source=source)
        except SyntaxError:
            continue
        if (
            functions >= Constants.min_functions
            and density >= Constants.min_density
        ):
            found.append((name, source, functions, density))
    return sorted(found, key=lambda item: -item[2])[: Constants.per_package]


def _pin() -> int:
    """Resolve the newest wheel of every package and record the pins.

    Returns:
        int: Zero.

    """
    pins: list[dict[str, str]] = []
    for package in Constants.packages:
        with TemporaryDirectory() as scratch:
            try:
                wheel: Path = _download(spec=package, into=Path(scratch))
            except RuntimeError:
                continue
            digest: str = sha256(data=wheel.read_bytes()).hexdigest()
            version: str = wheel.name.split(sep="-")[1]
            pins.append(
                {"name": package, "version": version, "sha256": digest},
            )
    _ = Constants.pins.write_text(
        data=dumps(obj=pins, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


def _build() -> int:
    """Fetch the pinned wheels, verify them and extract the corpus.

    Returns:
        int: Zero on success, one when a hash does not match.

    """
    pins: list[dict[str, str]] = loads(
        s=Constants.pins.read_text(encoding="utf-8"),
    )
    Constants.output.mkdir(parents=True, exist_ok=True)
    (Constants.output / "LICENSES").mkdir(exist_ok=True)
    manifest: list[dict[str, str | int | float]] = []
    for pin in pins:
        with TemporaryDirectory() as scratch:
            wheel: Path = _download(
                spec=f"{pin['name']}=={pin['version']}",
                into=Path(scratch),
            )
            if sha256(data=wheel.read_bytes()).hexdigest() != pin["sha256"]:
                return 1
            with ZipFile(file=wheel) as archive:
                for name, source, functions, density in _candidates(
                    wheel=archive,
                ):
                    target: str = (
                        f"{pin['name']}__"
                        f"{name.removesuffix('.py').replace('/', '__')}.py"
                    )
                    _ = (Constants.output / target).write_text(
                        data=source,
                        encoding="utf-8",
                    )
                    manifest.append(
                        {
                            "file": target,
                            "distribution": pin["name"],
                            "version": pin["version"],
                            "origin": name,
                            "sha256": sha256(data=source.encode()).hexdigest(),
                            "lines": source.count("\n"),
                            "functions": functions,
                            "density": round(number=density, ndigits=3),
                        },
                    )
                for name in archive.namelist():
                    if Path(name).name.upper().startswith(Constants.licenses):
                        _ = (
                            Constants.output
                            / "LICENSES"
                            / f"{pin['name']}.txt"
                        ).write_bytes(data=archive.read(name=name))
                        break
    _ = (Constants.output / "MANIFEST.json").write_text(
        data=dumps(obj=manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


def main() -> int:
    """Run the requested step.

    Returns:
        int: The exit status.

    """
    parser: ArgumentParser = ArgumentParser(
        prog="python -m scripts.benchmark.build_corpus",
    )
    parser.add_argument("step", choices=("pin", "build"))
    return _pin() if parser.parse_args().step == "pin" else _build()


if __name__ == "__main__":
    raise SystemExit(main())
